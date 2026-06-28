"""CoordinatorAgent — FSM orkestracija tutoring ciklusa (Faza 3E.2b).

Srce orkestracije. Prima start-poruku (submit-attempt) od gatewaya (3E.3), vodi
FIPA-ACL razgovor s ostalim agentima i vraća agregirani attempt-response natrag
pošiljatelju. Čisti FIPA — Coordinator NE zna za HTTP/AgentBridge.

FSM tok:
    RECEIVE → EVALUATE → UPDATE → RECOMMEND → RESPOND → (natrag na RECEIVE)

Korespondencija sa zaključanim odlukama (3E dizajn):
  - model-updated (od KM, 3E.1) je SPINE FSM-a: UPDATE čeka model-updated za svoj
    correlation_id (nosi attempt_id). Coordinator NE čeka Evaluatorov odgovor
    (Evaluator ne odgovara pošiljatelju na success-putu — odluka 7.1).
  - Coordinator čeka SAMO KM, ne Gamification. Gam teče paralelno; njegov rezultat
    se čita iz DB-a u RESPOND (best-effort, odluka 7.3).
  - DB-read agregacija: Coordinator NE prima rezultate porukama, čita ih iz DB po
    attempt_id (D6 garantira commit-before-inform). Nula retrofita Evaluator/Gam.
  - Stateless: start-poruka nosi user_id+task_id+submitted_query; nema session tablice.

KONKURENCIJA (svjesna MVP odluka — GATE 2):
  Sekvencijalna orkestracija, jedan tutoring-ciklus po instanci. SPADE FSMBehaviour
  ima jedan mailbox queue i izvodi stanja strogo redom, pa se SVI studentski flowovi
  globalno serijaliziraju kroz jednu instancu. Opravdano: nizak-konkurentan eval
  workload + downstream Recommender je ionako serijaliziran (prolog_lock). Pravi
  paralelizam (dispatcher / per-request spawn) = future work, skalabilnost.

STALE-MESSAGE GUARD (obavezan, ispravnost):
  receive() u UPDATE/RECOMMEND je drain-loop koji odbacuje poruke s tuđim
  correlation_id-em. INVARIANT (vrijedi POD serijalizacijom): svaka ne-self.cid
  poruka je nužno MRTVA (od prethodnog timeoutanog flowa), nikad buduća — pa je
  drop siguran. Ako se ikad uvede dispatcher, ovaj invariant pada i guard mora
  postati pravi correlation-router. Timeout je UKUPNI (deadline), ne resetira se po
  odbačenoj poruci — inače stale-flood produžava hang.
"""

from __future__ import annotations

import asyncio
import logging

from spade.behaviour import FSMBehaviour, State
from spade.template import Template
from sqlalchemy import func, select

from agents.base import TutorAgent
from agents.gamification_persistence import load_attempt
from agents.messages import Ontology, Performative, body_to_payload
from app.core import config
from app.db.models import Badge, User, UserBadge, XpLog
from app.db.session import SessionLocal

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ontologije / konstante (gateway ↔ Coordinator; lokalne da ne diramo messages.py)
# ---------------------------------------------------------------------------

ONTOLOGY_SUBMIT_ATTEMPT = "submit-attempt"
ONTOLOGY_ATTEMPT_RESPONSE = "attempt-response"

ERROR_EVALUATION_TIMEOUT = "evaluation_timeout"
REASON_RECOMMEND_TIMEOUT = "recommend_timeout"

# FSM stanja
STATE_RECEIVE = "RECEIVE"
STATE_EVALUATE = "EVALUATE"
STATE_UPDATE = "UPDATE"
STATE_RECOMMEND = "RECOMMEND"
STATE_RESPOND = "RESPOND"

# Default timeouti (sekunde) — UPDATE namjerno kratak: pod serijalizacijom UPDATE
# hang blokira SVE studente, pa kratak timeout ograničava štetu.
DEFAULT_UPDATE_TIMEOUT = 5.0
DEFAULT_RECOMMEND_TIMEOUT = 5.0
DEFAULT_RECEIVE_TIMEOUT = 30.0


# ---------------------------------------------------------------------------
# RESPOND agregacija — čiste DB-read funkcije (sync; pozvane preko to_thread)
# ---------------------------------------------------------------------------


def _best_effort_new_badges(session, user_id: int, since) -> list[str]:
    """Bedževi zarađeni na/nakon `since` (created_at attempta) — BEST-EFFORT approx.

    user_badges nema attempt_id, pa "novi badge IZ OVOG attempta" nije pouzdano
    razlučiv; aproksimiramo po earned_at >= created_at. Uz to Gam teče paralelno i
    možda još nije commitao u trenutku RESPOND → lista može biti prazna iako će
    badge biti dodijeljen. /profile (3E.3) je autoritativan izvor bedževa.
    """
    if since is None:
        return []
    rows = session.execute(
        select(Badge.code)
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user_id, UserBadge.earned_at >= since)
    ).scalars()
    return list(rows)


def build_response_payload(user_id: int, attempt_id: int | None) -> dict:
    """Agregiraj attempt-response iz DB-a po attempt_id (feedback + gam + ostalo).

    Recommendation se NE čita ovdje (dolazi iz RECOMMEND stanja); pozivatelj je
    dodaje. xp_delta je pouzdan (SUM xp_log po attempt_id); badge-XP ima
    attempt_id=NULL pa NE ulazi u xp_delta (to je čisti delta solve-a).
    """
    feedback: dict = {
        "attempt_id": attempt_id,
        "is_correct": None,
        "error_type": None,
        "verdict": None,
    }
    gamification: dict = {
        "xp_delta": 0,
        "xp": None,
        "level": None,
        "current_streak": None,
        "new_badges": [],
    }

    with SessionLocal() as session:
        created_at = None
        if attempt_id is not None:
            att = load_attempt(session, attempt_id)
            if att is not None:
                created_at = att.created_at
                feedback["is_correct"] = att.is_correct
                feedback["error_type"] = att.error_type
                # ERRATA #8: partial se NE razlučuje — attempts nema verdict kolonu;
                # izvodimo correct/incorrect iz is_correct. attempts.verdict migracija
                # = Faza 4 (tada feedback može vratiti pravi partial).
                feedback["verdict"] = "correct" if att.is_correct else "incorrect"

            xp_delta = session.scalar(
                select(func.coalesce(func.sum(XpLog.delta), 0)).where(
                    XpLog.attempt_id == attempt_id
                )
            )
            gamification["xp_delta"] = int(xp_delta or 0)

        user = session.get(User, user_id)
        if user is not None:
            gamification["xp"] = user.xp
            gamification["level"] = user.level
            gamification["current_streak"] = user.current_streak
            gamification["new_badges"] = _best_effort_new_badges(
                session, user_id, created_at
            )

    return {"user_id": user_id, "feedback": feedback, "gamification": gamification}


# ---------------------------------------------------------------------------
# Bazno FSM stanje s drain-aware receive helperom
# ---------------------------------------------------------------------------


class _FlowState(State):
    """Bazno stanje: dijeli drain-loop receive koji matcha (ontology[, cid])."""

    async def _recv_matching(
        self,
        *,
        ontology: str,
        cid: str | None,
        timeout: float,
    ):
        """Vrati prvu poruku koja matcha ontology (i cid ako zadan); ostale odbaci.

        Stale-message guard: ukupni timeout (deadline) — NE resetira se po odbačenoj
        poruci. Vraća None na istek. cid=None → prihvati bilo koji cid (RECEIVE).
        """
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                return None
            msg = await self.receive(timeout=remaining)
            if msg is None:
                return None
            msg_ont = msg.get_metadata("ontology")
            msg_cid = msg.get_metadata("correlation_id")
            if msg_ont == ontology and (cid is None or msg_cid == cid):
                return msg
            _log.debug(
                "Coordinator: drained stale poruka (ont=%s cid=%s; čekam ont=%s cid=%s)",
                msg_ont,
                msg_cid,
                ontology,
                cid,
            )


# ---------------------------------------------------------------------------
# FSM stanja
# ---------------------------------------------------------------------------


class ReceiveState(_FlowState):
    """Čeka submit-attempt; sprema per-flow stanje na agent; → EVALUATE."""

    async def run(self) -> None:
        msg = await self._recv_matching(
            ontology=ONTOLOGY_SUBMIT_ATTEMPT,
            cid=None,
            timeout=self.agent.receive_timeout,
        )
        if msg is None:
            # Nema starta u ovom prozoru — ostani u RECEIVE (poll).
            self.set_next_state(STATE_RECEIVE)
            return

        try:
            payload = body_to_payload(msg.body)
            self.agent._flow = {
                "cid": msg.get_metadata("correlation_id"),
                "sender": str(msg.sender),
                "user_id": payload["user_id"],
                "task_id": payload["task_id"],
                "submitted_query": payload["submitted_query"],
                "attempt_id": None,
                "recommendation": None,
                "error": None,
            }
        except Exception:
            _log.exception("Coordinator RECEIVE: neispravna start-poruka — ignoriram")
            self.set_next_state(STATE_RECEIVE)
            return

        self.agent.log_message(
            sender=self.agent._flow["sender"],
            receiver=str(self.agent.jid),
            performative=Performative.REQUEST,
            content=payload,
            correlation_id=self.agent._flow["cid"],
        )
        self.set_next_state(STATE_EVALUATE)


class EvaluateState(_FlowState):
    """Pošalji evaluate-query Evaluatoru (fire-and-forget); → UPDATE."""

    async def run(self) -> None:
        flow = self.agent._flow
        req = self.agent.build_message(
            to=config.AGENT_EVALUATOR_JID,
            performative=Performative.REQUEST,
            ontology=Ontology.EVALUATE_QUERY,
            payload={
                "user_id": flow["user_id"],
                "task_id": flow["task_id"],
                "submitted_query": flow["submitted_query"],
            },
            correlation_id=flow["cid"],
        )
        await self.send(req)
        self.agent.log_message(
            sender=str(self.agent.jid),
            receiver=config.AGENT_EVALUATOR_JID,
            performative=Performative.REQUEST,
            content={"user_id": flow["user_id"], "task_id": flow["task_id"]},
            correlation_id=flow["cid"],
        )
        self.set_next_state(STATE_UPDATE)


class UpdateState(_FlowState):
    """Čekaj model-updated (od KM) za ovaj cid; izvuci attempt_id. TIMEOUT → RESPOND."""

    async def run(self) -> None:
        flow = self.agent._flow
        msg = await self._recv_matching(
            ontology=Ontology.MODEL_UPDATED,
            cid=flow["cid"],
            timeout=self.agent.update_timeout,
        )
        if msg is None:
            # Anti-hang: KM nikad nije javio (npr. payload exception). NE visi.
            _log.warning(
                "Coordinator UPDATE: model-updated timeout (cid=%s) → evaluation_timeout",
                flow["cid"],
            )
            flow["error"] = ERROR_EVALUATION_TIMEOUT
            self.set_next_state(STATE_RESPOND)
            return

        payload = body_to_payload(msg.body)
        flow["attempt_id"] = payload.get("attempt_id")
        self.set_next_state(STATE_RECOMMEND)


class RecommendState(_FlowState):
    """Pošalji recommend-next Recommenderu, čekaj reply za ovaj cid. TIMEOUT → degradacija."""

    async def run(self) -> None:
        flow = self.agent._flow
        req = self.agent.build_message(
            to=config.AGENT_RECOMMENDER_JID,
            performative=Performative.REQUEST,
            ontology=Ontology.RECOMMEND_NEXT,
            payload={"user_id": flow["user_id"]},
            correlation_id=flow["cid"],
        )
        await self.send(req)

        msg = await self._recv_matching(
            ontology=Ontology.RECOMMEND_NEXT,
            cid=flow["cid"],
            timeout=self.agent.recommend_timeout,
        )
        if msg is None:
            # Degradacija (NE hang): preporuka nedostupna.
            _log.warning(
                "Coordinator RECOMMEND: recommend-next timeout (cid=%s) → degradacija",
                flow["cid"],
            )
            flow["recommendation"] = {
                "task_id": None,
                "concept": None,
                "reason": REASON_RECOMMEND_TIMEOUT,
            }
        else:
            payload = body_to_payload(msg.body)
            flow["recommendation"] = {
                "task_id": payload.get("task_id"),
                "concept": payload.get("concept"),
                "reason": payload.get("reason"),
            }
        self.set_next_state(STATE_RESPOND)


class RespondState(_FlowState):
    """Agregiraj iz DB (osim na evaluation_timeout) i vrati attempt-response; → RECEIVE."""

    async def run(self) -> None:
        flow = self.agent._flow
        cid = flow["cid"]

        if flow.get("error") == ERROR_EVALUATION_TIMEOUT:
            # Definiran greška-odgovor — gateway (3E.3) mapira u 5xx. NIKAD ne visi.
            payload = {"error": ERROR_EVALUATION_TIMEOUT, "correlation_id": cid}
        else:
            payload = await asyncio.to_thread(
                build_response_payload, flow["user_id"], flow["attempt_id"]
            )
            payload["recommendation"] = flow["recommendation"]
            payload["correlation_id"] = cid

        resp = self.agent.build_message(
            to=flow["sender"],
            performative=Performative.INFORM,
            ontology=ONTOLOGY_ATTEMPT_RESPONSE,
            payload=payload,
            correlation_id=cid,
        )
        await self.send(resp)
        self.agent.log_message(
            sender=str(self.agent.jid),
            receiver=flow["sender"],
            performative=Performative.INFORM,
            content=payload,
            correlation_id=cid,
        )
        # Loop natrag — spreman za idući flow (FSM nikad ne dolazi u final state).
        self.set_next_state(STATE_RECEIVE)


# ---------------------------------------------------------------------------
# FSM behaviour + agent
# ---------------------------------------------------------------------------


class OrchestrationFSM(FSMBehaviour):
    """5-stanja FSM: RECEIVE→EVALUATE→UPDATE→RECOMMEND→RESPOND→(RECEIVE)."""

    def setup(self) -> None:
        self.add_state(STATE_RECEIVE, ReceiveState(), initial=True)
        self.add_state(STATE_EVALUATE, EvaluateState())
        self.add_state(STATE_UPDATE, UpdateState())
        self.add_state(STATE_RECOMMEND, RecommendState())
        self.add_state(STATE_RESPOND, RespondState())

        self.add_transition(STATE_RECEIVE, STATE_RECEIVE)  # poll
        self.add_transition(STATE_RECEIVE, STATE_EVALUATE)
        self.add_transition(STATE_EVALUATE, STATE_UPDATE)
        self.add_transition(STATE_UPDATE, STATE_RECOMMEND)
        self.add_transition(STATE_UPDATE, STATE_RESPOND)  # timeout put
        self.add_transition(STATE_RECOMMEND, STATE_RESPOND)
        self.add_transition(STATE_RESPOND, STATE_RECEIVE)  # loop


def _coordinator_template() -> Template:
    """Template koji u FSM queue propušta sve tri dolazne ontologije."""
    t_submit = Template()
    t_submit.set_metadata("ontology", ONTOLOGY_SUBMIT_ATTEMPT)
    t_model = Template()
    t_model.set_metadata("ontology", Ontology.MODEL_UPDATED)
    t_recommend = Template()
    t_recommend.set_metadata("ontology", Ontology.RECOMMEND_NEXT)
    return t_submit | t_model | t_recommend


class CoordinatorAgent(TutorAgent):
    """Orkestrira tutoring ciklus preko FSM-a; gateway-facing FIPA agent."""

    def __init__(
        self,
        agent_name: str = "coordinator",
        *,
        update_timeout: float = DEFAULT_UPDATE_TIMEOUT,
        recommend_timeout: float = DEFAULT_RECOMMEND_TIMEOUT,
        receive_timeout: float = DEFAULT_RECEIVE_TIMEOUT,
    ) -> None:
        super().__init__(agent_name)
        self.update_timeout = update_timeout
        self.recommend_timeout = recommend_timeout
        self.receive_timeout = receive_timeout

    async def setup(self) -> None:
        self._flow: dict | None = None  # per-flow stanje (sigurno: serijalizirano)
        self.add_behaviour(OrchestrationFSM(), _coordinator_template())
