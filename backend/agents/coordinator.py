"""CoordinatorAgent — FSM orkestracija tutoring ciklusa (Faza 3E.2b; #62 popravak).

Srce orkestracije. Prima start-poruku (submit-attempt) od gatewaya (3E.3), vodi
FIPA-ACL razgovor s ostalim agentima i vraća agregirani attempt-response natrag
pošiljatelju. Čisti FIPA — Coordinator NE zna za HTTP/AgentBridge.

FSM tok, po JEDNOM razgovoru:
    EVALUATE → UPDATE → RECOMMEND → RESPOND → (kraj FSM-a)

Prijem je izdvojen iz FSM-a u `_Intake` (CyclicBehaviour): on prima svaku
`submit-attempt` i za nju OTVARA VLASTITI FSM. Prije #62 je prijem bio peto stanje
istog, jedinog FSM-a — v. „ŠTO JE PROMIJENIO #62" niže.

Korespondencija sa zaključanim odlukama (3E dizajn):
  - model-updated (od KM, 3E.1) je SPINE FSM-a: UPDATE čeka model-updated za svoj
    correlation_id (nosi attempt_id). Coordinator NE čeka Evaluatorov odgovor
    (Evaluator ne odgovara pošiljatelju na success-putu — odluka 7.1).
  - Coordinator čeka SAMO KM, ne Gamification. Gam teče paralelno; njegov rezultat
    se čita iz DB-a u RESPOND (best-effort, odluka 7.3).
  - DB-read agregacija: Coordinator NE prima rezultate porukama, čita ih iz DB po
    attempt_id (D6 garantira commit-before-inform). Nula retrofita Evaluator/Gam.
  - Stateless: start-poruka nosi user_id+task_id+submitted_query; nema session tablice.

🔴 ŠTO JE PROMIJENIO #62 (i zašto je prethodni tekst ovdje bio NETOČAN)
--------------------------------------------------------------------------------
Prije popravka stajalo je (GATE 2): „Sekvencijalna orkestracija, jedan tutoring-ciklus
po instanci … SVI studentski flowovi globalno serijaliziraju." Serijalizacija je bila
istinita, ali njezina POSLJEDICA nije bila opisana: višak se nije čekao nego
ODBACIVAO. Uz nju je stajao i ovaj invariant:

    „svaka ne-self.cid poruka je nužno MRTVA (od prethodnog timeoutanog flowa),
     nikad buduća — pa je drop siguran"

🔴 Ta je tvrdnja bila NEISTINITA od Faze 3E.3, tri mjeseca. Vrijedila bi samo da
zahtjevi stižu strogo jedan po jedan. Čim dva HTTP klijenta predaju istovremeno,
`submit-attempt` drugoga stigne dok je FSM u UPDATE/RECOMMEND, drain-loop ga odbaci
kao „stale", a to je BUDUĆI zahtjev — ne mrtav. Izmjereno: rafal od K istovremenih
predaja davao je TOČNO JEDAN redak u `attempts` za svaki K ∈ {2,3,4,8}; ostali su
studenti dobili 504 nakon 15 s, a njihov rad nije postojao nigdje. V. errata #62 i
`docs/fix-62-korak-0.md`.

KONKURENCIJA (od #62)
  Svaki razgovor ima VLASTITI `OrchestrationFSM` s VLASTITIM predloškom vezanim uz
  svoj `correlation_id`. SPADE `dispatch()` isporučuje poruku svakom behaviouru čiji
  predložak matcha, pa je predložak sam po sebi korelacijski router — nema ručnog
  registryja Future-a. Tokovi teku istovremeno; nizvodni Recommender i dalje
  serijalizira (`prolog_lock`), ali S REDOM, ne s gubitkom (dokazano na `/next-task`,
  koji je istu konkurentnost podnosio i prije #62).

  🔴 GATE 2 time PADA kao opis sustava i ovdje je zamijenjen. Ono što od njega ostaje
  istinito: Recommender je i dalje usko grlo, samo više ne gubi.

INVARIANT KORELACIJE (novi, i sada ISTINIT)
  Poruka koja ne matcha nijedan behaviour nužno je ZAKAŠNJELA — njezin je tok već
  završio (odgovorio ili istekao) i predložak mu je uklonjen. Živ tok UVIJEK ima
  registriran svoj predložak, pa se poruka živog toka ne može izgubiti. SPADE takvu
  poruku logira kao „No behaviour matched" i odbaci; to je jedini slučaj odbacivanja.
  Izvršava ga `tests/test_coordinator_concurrency.py`.

  Unutar jednog toka `_recv` i dalje ima drain-loop, ali samo za tuđu ONTOLOGIJU pod
  istim cid-om; timeout je UKUPNI (deadline) i ne resetira se po odbačenoj poruci.

GRANICA ISTOVREMENIH TOKOVA
  `MAX_CONCURRENT_FLOWS`. Na granici se predaja ODBIJA EKSPLICITNO (`refuse` +
  `coordinator_busy` → HTTP 503), nikad tiho — tiho odbijanje na granici bilo bi #62
  reproduciran na drugom mjestu.
"""

from __future__ import annotations

import asyncio
import logging

from spade.behaviour import CyclicBehaviour, FSMBehaviour, State
from spade.template import Template
from sqlalchemy import func, select

from agents.base import TutorAgent
from agents.gamification_persistence import (
    load_attempt,
    prior_correct_solve_exists,
)
from agents.messages import (
    ERROR_PLAN_UNAVAILABLE as _ERROR_PLAN_UNAVAILABLE,
    Ontology,
    Performative,
    body_to_payload,
)
from app.core import config
from app.db.models import Attempt, Badge, User, UserBadge, XpLog
from app.db.session import SessionLocal
from scripts.lib.sandbox_runner import DEFAULT_STATEMENT_TIMEOUT_S

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ontologije / konstante (gateway ↔ Coordinator; lokalne da ne diramo messages.py)
# ---------------------------------------------------------------------------

ONTOLOGY_SUBMIT_ATTEMPT = "submit-attempt"
ONTOLOGY_ATTEMPT_RESPONSE = "attempt-response"

ERROR_EVALUATION_TIMEOUT = "evaluation_timeout"
#: Granica istovremenih tokova dosegnuta — predaja odbijena EKSPLICITNO (#62).
ERROR_COORDINATOR_BUSY = "coordinator_busy"

#: Re-eksport iz protokolnog modula — `routes.py` uvozi cijelu ERROR_* obitelj
#: odavde, pa novi član ne mijenja oblik tog uvoza. Definicija je u
#: `messages.py` jer je to jedina riječ koju Evaluator i Coordinator dijele.
ERROR_PLAN_UNAVAILABLE = _ERROR_PLAN_UNAVAILABLE
REASON_RECOMMEND_TIMEOUT = "recommend_timeout"
#: #63: pokušaj je nađen u bazi nakon isteka UPDATE prozora, pa se preporuka NIJE ni
#: tražila. Razlikuje se od `recommend_timeout` (tražena, nije stigla) — student je u
#: oba slučaja bez preporuke, ali razlog nije isti i log to mora znati.
REASON_RECOMMEND_SKIPPED = "recommend_skipped"

# FSM stanja (RECEIVE je od #62 izdvojen u `_Intake` i više nije stanje)
STATE_EVALUATE = "EVALUATE"
STATE_UPDATE = "UPDATE"
STATE_RECOMMEND = "RECOMMEND"
STATE_RESPOND = "RESPOND"

# Default timeouti (sekunde).
#
# 🔴 #63: UPDATE prozor se IZVODI iz sandbox granice, ne postavlja kao vlastita
# konstanta. Prije popravka su `statement_timeout` i `DEFAULT_UPDATE_TIMEOUT` oba
# bili 5 — dvije nevezane petice — pa je SVAKI upit koji potroši sandbox timeout
# nužno prekoračio i UPDATE prozor: Coordinator bi odustao (504) dok bi Evaluator
# uredno commitao pokušaj. Izmjereno 3/3, uklj. TOČAN upit uz dodijeljenih 30 XP.
#
# 🔴 Produljenje je postalo SIGURNO tek nakon #62. Stari komentar je glasio: „UPDATE
# namjerno kratak: pod serijalizacijom UPDATE hang blokira SVE studente." To je bilo
# točno dok je FSM bio jedan; sada spor tok blokira samo sebe.
#
# Ukupni najgori put (UPDATE + RECOMMEND) mora ostati ispod `GATEWAY_TIMEOUT` (15):
# 7 + 5 = 12, uz 3 s rezerve.
UPDATE_TIMEOUT_MARGIN_S = 2.0
DEFAULT_UPDATE_TIMEOUT = DEFAULT_STATEMENT_TIMEOUT_S + UPDATE_TIMEOUT_MARGIN_S
DEFAULT_RECOMMEND_TIMEOUT = 5.0
DEFAULT_RECEIVE_TIMEOUT = 30.0

#: Koliko se nakon isteka UPDATE prozora još čeka da upis „slegne" prije nego se
#: odgovori greškom. Bez toga bi redak koji nastane milisekundu nakon provjere opet
#: proizveo nesklad — samo rjeđe.
SETTLE_WINDOW_S = 2.0
SETTLE_INTERVAL_S = 0.25

#: 🔴 Gornja granica istovremenih razgovora. Postoji da bi preopterećenje imalo
#: EKSPLICITAN ishod: bez nje bi svi tokovi čekali u Evaluatorovom serijalnom redu i
#: masovno padali u `evaluation_timeout` — što je za studenta nerazlučivo od kvara.
#: Brojka je namjerno visoko iznad realnog evala (20 sudionika): granica je zaštita
#: od bijega, ne mehanizam raspodjele.
MAX_CONCURRENT_FLOWS = 64


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


def max_attempt_id(user_id: int, task_id: int) -> int | None:
    """Najveći `attempts.id` tog korisnika i zadatka — polazna crta toka (#63).

    🔴 Zašto ID, a ne vrijeme: usporedba po `created_at` mjeri APLIKACIJSKI sat protiv
    sata BAZE. Skew je na istom stroju zanemariv, ali „zanemariv" nije isto što i
    „nula", a ovdje bi promašaj vratio točno onaj nesklad koji popravljamo. ID-evi
    dolaze iz istog sekvencijalnog izvora kao i redak, pa usporedba nema sata.

    Ide kroz `idx_attempts_user_task`; trošak ~1 ms po predaji.
    """
    with SessionLocal() as session:
        return session.scalar(
            select(func.max(Attempt.id)).where(
                Attempt.user_id == user_id, Attempt.task_id == task_id
            )
        )


def attempt_since(user_id: int, task_id: int, baseline_id: int | None) -> int | None:
    """Pokušaj nastao NAKON polazne crte, ili `None`. Odgovara na: „je li upisano?"."""
    with SessionLocal() as session:
        return session.scalar(
            select(Attempt.id)
            .where(
                Attempt.user_id == user_id,
                Attempt.task_id == task_id,
                Attempt.id > (baseline_id or 0),
            )
            .order_by(Attempt.id.desc())
            .limit(1)
        )


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
        "detail": None,
        "verdict": None,
    }
    gamification: dict = {
        "xp_delta": 0,
        "xp": None,
        "level": None,
        "current_streak": None,
        "new_badges": [],
        # True ako je task bio VEĆ točno riješen PRIJE ovog pokušaja → attempt-XP
        # se ne dodjeljuje (first-solve gate). UI to prikazuje kao „bez XP-a".
        "already_solved": False,
    }

    with SessionLocal() as session:
        created_at = None
        if attempt_id is not None:
            att = load_attempt(session, attempt_id)
            if att is not None:
                created_at = att.created_at
                feedback["is_correct"] = att.is_correct
                feedback["error_type"] = att.error_type
                # Stage 0b: pedagoški detail iz attempts reda (NULL za correct).
                feedback["detail"] = att.detail
                # ERRATA #8: partial se NE razlučuje — attempts nema verdict kolonu;
                # izvodimo correct/incorrect iz is_correct. attempts.verdict migracija
                # = Faza 4 (tada feedback može vratiti pravi partial).
                feedback["verdict"] = "correct" if att.is_correct else "incorrect"
                # already_solved: isti izvor istine kao gate u persist_gamification
                # (raniji točan pokušaj istog taska). Correct pokušaj koji je PRVO
                # rješavanje → False (XP je dodijeljen).
                gamification["already_solved"] = prior_correct_solve_exists(
                    session, user_id, att.task_id, att.attempt_number
                )

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
    """Bazno stanje JEDNOG razgovora. Nosi vlastiti `flow` — nema dijeljenog stanja.

    🔴 Prije #62 su sva stanja čitala `self.agent._flow`, JEDAN atribut na agentu. To
    je bio drugi, dublji razlog zašto zaustavljanje odbacivanja poruka ne bi bilo
    dovoljno: i da su poruke stizale, Coordinator ih ne bi imao gdje držati.
    """

    def __init__(self, flow: dict) -> None:
        super().__init__()
        self.flow = flow

    async def _recv(self, *, ontology: str, timeout: float):
        """Vrati prvu poruku tražene ontologije; ostale odbaci. `None` na istek.

        🔴 Filtriranje po `correlation_id` OVDJE VIŠE NE POSTOJI — radi ga SPADE
        predložak vezan uz ovaj FSM (v. `_flow_template`), pa u ovaj mailbox tuđi cid
        ne može ni ući. Ostaje drain samo za tuđu ontologiju pod ISTIM cid-om.

        Timeout je UKUPNI (deadline) i NE resetira se po odbačenoj poruci — inače bi
        poplava poruka produžila čekanje preko zadanog prozora.
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
            if msg_ont == ontology:
                return msg
            _log.debug(
                "Coordinator[%s]: drained poruka druge ontologije (%s; čekam %s)",
                self.flow.get("cid"),
                msg_ont,
                ontology,
            )


# ---------------------------------------------------------------------------
# FSM stanja
# ---------------------------------------------------------------------------


class EvaluateState(_FlowState):
    """Pošalji evaluate-query Evaluatoru (fire-and-forget); → UPDATE."""

    async def run(self) -> None:
        flow = self.flow
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
        flow = self.flow
        msg = await self._recv(
            ontology=Ontology.MODEL_UPDATED,
            timeout=self.agent.update_timeout,
        )
        if msg is None:
            # 🔴 #63: prije nego kažemo „nije prošlo", moramo PROVJERITI je li prošlo.
            # Coordinatorov istek ne zaustavlja Evaluatora — on commita neovisno
            # (D6), a Gamification i KM rade dalje. Odgovor „greška" uz postojeći
            # redak znači da je student kažnjen za predaju koju mu sustav niječe.
            found = await self._settle(flow)
            if found is not None:
                _log.warning(
                    "Coordinator UPDATE: model-updated istekao (cid=%s), ali pokušaj "
                    "%s POSTOJI → odgovaram stvarnim ishodom, ne greškom",
                    flow["cid"],
                    found,
                )
                flow["attempt_id"] = found
                # Preporuka se ne traži: prozor je već potrošen, a `RECOMMEND` bi
                # dodao još do 5 s na zahtjev koji je ionako spor.
                flow["recommendation"] = {
                    "task_id": None,
                    "concept": None,
                    "reason": REASON_RECOMMEND_SKIPPED,
                }
                self.set_next_state(STATE_RESPOND)
                return

            # Ništa nije upisano → greška je istinita.
            _log.warning(
                "Coordinator UPDATE: model-updated timeout (cid=%s) i nema retka → "
                "evaluation_timeout",
                flow["cid"],
            )
            flow["error"] = ERROR_EVALUATION_TIMEOUT
            self.set_next_state(STATE_RESPOND)
            return

        # 🔴 GRANA NA PERFORMATIV, NIKAD NA SADRŽAJ PAYLOADA (ERRATA #69).
        #
        # `refuse(model-updated)` = Evaluator odbija isporučiti model-updated jer
        # pokušaj NIJE NASTAO (plan izvedbe se nije mogao dohvatiti). Ontologija je
        # tema razgovora, performativ je govorni čin — isti obrazac kao
        # `_refuse_busy`, samo unutar toka umjesto na njegovoj granici.
        #
        # 🔴 Zašto NE `if payload.get("error")`: to bi bilo „novo ponašanje bez
        # novog imena" — obrazac koji je u ovom projektu već proizveo tri nalaza
        # (v. wrapup §G2). Legitiman `inform(model-updated)` koji sutra dobije
        # polje `error` tiho bi prekidao tok. Čuva `test_inform_s_error_kljucem_
        # NE_prekida_tok`.
        if msg.get_metadata("performative") == Performative.REFUSE:
            _log.warning(
                "Coordinator UPDATE: Evaluator odbio model-updated (cid=%s) → "
                "plan_unavailable; pokušaj nije nastao",
                flow["cid"],
            )
            flow["error"] = ERROR_PLAN_UNAVAILABLE
            self.set_next_state(STATE_RESPOND)
            return

        payload = body_to_payload(msg.body)
        flow["attempt_id"] = payload.get("attempt_id")
        self.set_next_state(STATE_RECOMMEND)

    async def _settle(self, flow: dict) -> int | None:
        """Kratko pričekaj da upis slegne, pa vrati `attempt_id` ako postoji.

        Jedna provjera ne bi bila dovoljna: redak koji nastane milisekundu nakon nje
        vratio bi isti nesklad, samo rjeđe. Zato se provjera ponavlja kroz
        `SETTLE_WINDOW_S` — ograničeno, jer i ovaj prozor troši `GATEWAY_TIMEOUT`.
        """
        loop = asyncio.get_event_loop()
        deadline = loop.time() + SETTLE_WINDOW_S
        while True:
            found = await asyncio.to_thread(
                attempt_since,
                flow["user_id"],
                flow["task_id"],
                flow["baseline_attempt_id"],
            )
            if found is not None or loop.time() >= deadline:
                return found
            await asyncio.sleep(SETTLE_INTERVAL_S)


class RecommendState(_FlowState):
    """Pošalji recommend-next Recommenderu, čekaj reply za ovaj cid. TIMEOUT → degradacija."""

    async def run(self) -> None:
        flow = self.flow
        req = self.agent.build_message(
            to=config.AGENT_RECOMMENDER_JID,
            performative=Performative.REQUEST,
            ontology=Ontology.RECOMMEND_NEXT,
            payload={"user_id": flow["user_id"]},
            correlation_id=flow["cid"],
        )
        await self.send(req)

        msg = await self._recv(
            ontology=Ontology.RECOMMEND_NEXT,
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
    """Agregiraj iz DB (osim na evaluation_timeout) i vrati attempt-response; KRAJ toka."""

    async def run(self) -> None:
        flow = self.flow
        cid = flow["cid"]

        if flow.get("error") in (ERROR_EVALUATION_TIMEOUT, ERROR_PLAN_UNAVAILABLE):
            # Definiran greška-odgovor — gateway (3E.3) mapira u 5xx. NIKAD ne visi.
            # 🔴 `plan_unavailable` NE ide kroz `build_response_payload`: taj gradi
            # odgovor IZ BAZE po `attempt_id`, a ovdje retka nema i ne smije ga biti.
            payload = {"error": flow["error"], "correlation_id": cid}
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
        # 🔴 NE postavlja se sljedeće stanje → SPADE zaključuje da je FSM u završnom
        # stanju i ubija ga. Čišćenje (uklanjanje behavioura + predloška, pop iz
        # `_flows`) ide u `OrchestrationFSM.on_end`, koji se izvodi i na urednom
        # kraju i na `kill()` — v. LEAK GUARD ondje.


# ---------------------------------------------------------------------------
# FSM behaviour + agent
# ---------------------------------------------------------------------------


class OrchestrationFSM(FSMBehaviour):
    """FSM JEDNOG razgovora: EVALUATE→UPDATE→RECOMMEND→RESPOND→(kraj).

    Instancira se po predaji i nosi vlastiti `flow`. Prijem (nekadašnje RECEIVE
    stanje) preuzeo je `_Intake`, jer prijem NIJE korak razgovora nego njegov okidač —
    dok je bio stanje istog FSM-a, jedan razgovor u tijeku značio je da se sljedeći
    ne može ni primiti.
    """

    def __init__(self, flow: dict) -> None:
        # 🔴 `FSMBehaviour.__init__` zove `setup()`, pa `_flow` MORA biti postavljen
        # prije poziva nadklase — inače `setup` nema što proslijediti stanjima.
        self._flow = flow
        super().__init__()

    def setup(self) -> None:
        flow = self._flow
        self.add_state(STATE_EVALUATE, EvaluateState(flow), initial=True)
        self.add_state(STATE_UPDATE, UpdateState(flow))
        self.add_state(STATE_RECOMMEND, RecommendState(flow))
        self.add_state(STATE_RESPOND, RespondState(flow))

        self.add_transition(STATE_EVALUATE, STATE_UPDATE)
        self.add_transition(STATE_UPDATE, STATE_RECOMMEND)
        self.add_transition(STATE_UPDATE, STATE_RESPOND)  # timeout put
        self.add_transition(STATE_RECOMMEND, STATE_RESPOND)
        # RESPOND nema izlaz → završno stanje, FSM se ugasi (v. `on_end`).

    async def on_end(self) -> None:
        """🔴 LEAK GUARD: tok se odjavljuje BEZUVJETNO, na svakom izlazu.

        Isti obrazac kao `AgentBridge.wait` (`finally: _pending.pop`). Bez ovoga bi
        svaki razgovor ostavio mrtav behaviour u `agent.behaviours` čiji predložak i
        dalje matcha — curenje koje se vidi tek nakon sati rada, dakle točno tijekom
        evala.
        """
        self.agent._release_flow(self._flow["cid"], self)


def _intake_template() -> Template:
    """Samo start-poruke. Odgovori idu per-flow predlošcima, ne ovamo."""
    t = Template()
    t.set_metadata("ontology", ONTOLOGY_SUBMIT_ATTEMPT)
    return t


def _flow_template(cid: str) -> Template:
    """🔴 KORELACIJSKI ROUTER: predložak vezan uz JEDAN `correlation_id`.

    Ovo je cijeli mehanizam korelacije — SPADE `dispatch()` isporučuje poruku svakom
    behaviouru čiji predložak matcha, pa tuđi cid u ovaj mailbox ne može ni ući.
    Nema ručnog registryja Future-a; posao koji u gatewayu radi `AgentBridge._pending`
    ovdje radi sam predložak.
    """
    t_model = Template()
    t_model.set_metadata("ontology", Ontology.MODEL_UPDATED)
    t_model.set_metadata("correlation_id", cid)
    t_recommend = Template()
    t_recommend.set_metadata("ontology", Ontology.RECOMMEND_NEXT)
    t_recommend.set_metadata("correlation_id", cid)
    return t_model | t_recommend


class _Intake(CyclicBehaviour):
    """Prima `submit-attempt` i otvara VLASTITI FSM za svaku predaju."""

    async def run(self) -> None:
        msg = await self.receive(timeout=self.agent.receive_timeout)
        if msg is None:
            return

        cid = msg.get_metadata("correlation_id")
        sender = str(msg.sender)
        try:
            payload = body_to_payload(msg.body)
            flow = {
                "cid": cid,
                "sender": sender,
                "user_id": payload["user_id"],
                "task_id": payload["task_id"],
                "submitted_query": payload["submitted_query"],
                "attempt_id": None,
                "recommendation": None,
                "error": None,
                # #63: polazna crta za pitanje „je li ovaj tok išta upisao?".
                # Postavlja se PRIJE nego išta krene, inače nije polazna crta.
                "baseline_attempt_id": None,
            }
        except Exception:
            _log.exception("Coordinator INTAKE: neispravna start-poruka — ignoriram")
            return

        flow["baseline_attempt_id"] = await asyncio.to_thread(
            max_attempt_id, flow["user_id"], flow["task_id"]
        )

        self.agent.log_message(
            sender=sender,
            receiver=str(self.agent.jid),
            performative=Performative.REQUEST,
            content=payload,
            correlation_id=cid,
        )

        if not self.agent._open_flow(cid, flow):
            await self._refuse_busy(sender, cid)
            return

        fsm = OrchestrationFSM(flow)
        self.agent._flows[cid]["fsm"] = fsm
        self.agent.add_behaviour(fsm, _flow_template(cid))

    async def _refuse_busy(self, to: str, cid: str) -> None:
        """🔴 Granica se objavljuje, ne prešućuje.

        Tiho odbacivanje na granici bilo bi #62 reproduciran na drugom mjestu:
        student bi opet čekao `GATEWAY_TIMEOUT` i dobio 504 bez ijednog objašnjenja.
        Ovako odgovor stiže odmah, nosi razlog, i vidljiv je u `agent_messages_log`.
        `refuse` je performativ definiran u `messages.py` koji dosad nije imao
        proizvođača — ovo mu je prvi.
        """
        _log.warning(
            "Coordinator: granica od %d istovremenih tokova dosegnuta — odbijam cid=%s",
            MAX_CONCURRENT_FLOWS,
            cid,
        )
        payload = {"error": ERROR_COORDINATOR_BUSY, "correlation_id": cid}
        msg = self.agent.build_message(
            to=to,
            performative=Performative.REFUSE,
            ontology=ONTOLOGY_ATTEMPT_RESPONSE,
            payload=payload,
            correlation_id=cid,
        )
        await self.send(msg)
        self.agent.log_message(
            sender=str(self.agent.jid),
            receiver=to,
            performative=Performative.REFUSE,
            content=payload,
            correlation_id=cid,
        )


class CoordinatorAgent(TutorAgent):
    """Orkestrira tutoring cikluse preko FSM-a PO RAZGOVORU; gateway-facing FIPA agent."""

    def __init__(
        self,
        agent_name: str = "coordinator",
        *,
        update_timeout: float = DEFAULT_UPDATE_TIMEOUT,
        recommend_timeout: float = DEFAULT_RECOMMEND_TIMEOUT,
        receive_timeout: float = DEFAULT_RECEIVE_TIMEOUT,
        max_concurrent_flows: int = MAX_CONCURRENT_FLOWS,
    ) -> None:
        super().__init__(agent_name)
        self.update_timeout = update_timeout
        self.recommend_timeout = recommend_timeout
        self.receive_timeout = receive_timeout
        self.max_concurrent_flows = max_concurrent_flows
        #: cid → {"flow": dict, "fsm": OrchestrationFSM|None}. Registry ŽIVIH tokova.
        self._flows: dict[str, dict] = {}

    def _open_flow(self, cid: str, flow: dict) -> bool:
        """Rezerviraj mjesto za tok. `False` ⟺ granica dosegnuta ili cid već postoji."""
        if cid in self._flows:
            _log.warning("Coordinator: cid %s već ima živ tok — odbijam duplikat", cid)
            return False
        if len(self._flows) >= self.max_concurrent_flows:
            return False
        self._flows[cid] = {"flow": flow, "fsm": None}
        return True

    def _release_flow(self, cid: str, fsm) -> None:
        """Odjavi tok i ukloni njegov behaviour. Idempotentno."""
        self._flows.pop(cid, None)
        try:
            if self.has_behaviour(fsm):
                self.remove_behaviour(fsm)
        except ValueError:  # pragma: no cover — utrka s vlastitim kill()om
            pass

    def flow_count(self) -> int:
        """Broj živih tokova — introspekcija za testove curenja (usp. `pending_count`)."""
        return len(self._flows)

    async def setup(self) -> None:
        self.add_behaviour(_Intake(), _intake_template())
