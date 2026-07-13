"""E2E testovi za CoordinatorAgent FSM orkestraciju — Faza 3E.2b.

Coordinator se izolira KONTROLIRANIM mock agentima (Evaluator/KM/Recommender na
njihovim JID-evima) + gateway-probom (vlastiti JID, auto-register). Tako testovi
NE ovise o sandboxu/seedanim taskovima — testira se ORKESTRACIJA (sekvenca, cid
korelacija, timeout-handling, DB-read agregacija), ne stvarna SQL evaluacija.

Zahtijeva: živući Prosody (5222) + tutor_main DB s registriranim agentima.

Per-flow DB-read agregacija u RESPOND čita committed `attempts`/`xp_log` redove —
testovi ih pre-insertaju i prosljeđuju attempt_id kroz mock lanac (kao u produkciji
gdje Evaluator persistira, a KM-ov model-updated nosi attempt_id).

GATE 2 (serijalizacija): FSMBehaviour serijalizira flowove globalno → cid-korelacija
test je SEKVENCIJALAN (dva flowa zaredom), ne paralelan.
"""

from __future__ import annotations

import asyncio
import subprocess
import uuid
from contextlib import asynccontextmanager

import pytest
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.template import Template
from sqlalchemy import delete, select

from agents.base import TutorAgent
from agents.coordinator import (
    ERROR_EVALUATION_TIMEOUT,
    ONTOLOGY_ATTEMPT_RESPONSE,
    ONTOLOGY_SUBMIT_ATTEMPT,
    REASON_RECOMMEND_TIMEOUT,
    CoordinatorAgent,
)
from agents.messages import Ontology, Performative, body_to_payload
from app.core import config
from app.db.models import Attempt, Task, User, UserBadge, XpLog
from app.db.session import SessionLocal

_PROBE_JID = "gwprobe@localhost"
_PROBE_PW = "gwprobe_pw"
_PROSODY_CONTAINER = "sql-tutor-prosody"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _register_probe_account():
    """Registriraj gateway-probe JID u Prosody (idempotentno — postojeći račun OK)."""
    subprocess.run(
        ["docker", "exec", _PROSODY_CONTAINER, "prosodyctl", "register",
         "gwprobe", "localhost", _PROBE_PW],
        capture_output=True,
        text=True,
    )
    yield


@pytest.fixture
def coord_env():
    """Committed test user + valjan task_id. Teardown briše xp_log/attempts/badges/user."""
    with SessionLocal() as sess:
        user = User(
            username="coord_e2e_user_3e2b",
            email="coord_e2e_3e2b@test.example",
            password_hash="dummy_hash_3e2b",
        )
        sess.add(user)
        sess.commit()
        user_id = user.id
        task_id = sess.scalar(select(Task.id).limit(1))
    assert task_id is not None, "tasks moraju biti seedani (faza 3.0)"

    yield {"user_id": user_id, "task_id": task_id}

    with SessionLocal() as cleanup:
        cleanup.execute(delete(XpLog).where(XpLog.user_id == user_id))
        cleanup.execute(delete(Attempt).where(Attempt.user_id == user_id))
        cleanup.execute(delete(UserBadge).where(UserBadge.user_id == user_id))
        cleanup.execute(delete(User).where(User.id == user_id))
        cleanup.commit()


def _make_attempt(
    user_id: int,
    task_id: int,
    *,
    is_correct: bool,
    error_type: str | None,
    attempt_number: int,
    xp_delta: int = 0,
    detail: str | None = None,
) -> int:
    """Insertaj committed Attempt (+opc. XpLog) i vrati attempt_id."""
    with SessionLocal() as sess:
        att = Attempt(
            user_id=user_id,
            task_id=task_id,
            submitted_query="SELECT 1;",
            is_correct=is_correct,
            error_type=error_type,
            attempt_number=attempt_number,
            detail=detail,
        )
        sess.add(att)
        sess.commit()
        attempt_id = att.id
        if xp_delta:
            sess.add(XpLog(user_id=user_id, attempt_id=attempt_id, delta=xp_delta, reason="attempt"))
            sess.commit()
    return attempt_id


# ---------------------------------------------------------------------------
# Mock agenti (kontrolirani FIPA partneri Coordinatora)
# ---------------------------------------------------------------------------


class _MockEvaluator(TutorAgent):
    """JID 'evaluator': na evaluate-query prosljeđuje attempt-result KM-u (s cid+attempt_id)."""

    class _B(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return
            cid = msg.get_metadata("correlation_id")
            payload = body_to_payload(msg.body)
            fwd = self.agent.build_message(
                to=config.AGENT_KNOWLEDGE_JID,
                performative=Performative.INFORM,
                ontology=Ontology.ATTEMPT_RESULT,
                payload={"user_id": payload.get("user_id"), "attempt_id": getattr(self.agent, "_attempt_id", None)},
                correlation_id=cid,
            )
            await self.send(fwd)

    async def setup(self) -> None:
        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.EVALUATE_QUERY)
        self.add_behaviour(self._B(), tmpl)


class _MockKnowledge(TutorAgent):
    """JID 'knowledge': na attempt-result šalje model-updated Coordinatoru (s cid+attempt_id).

    Konfigurabilno:
      _silent          → ne šalje ništa (KM-timeout scenarij)
      _updated_concepts → sadržaj signala (mehanička greška = [])
      _stale_cid/_stale_attempt_id → prvo pošalje stale model-updated sa STRANIM cid
                                     (stale-message guard test)
    """

    class _B(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return
            if getattr(self.agent, "_silent", False):
                return
            cid = msg.get_metadata("correlation_id")
            payload = body_to_payload(msg.body)

            stale_cid = getattr(self.agent, "_stale_cid", None)
            if stale_cid:
                stale = self.agent.build_message(
                    to=config.AGENT_COORDINATOR_JID,
                    performative=Performative.INFORM,
                    ontology=Ontology.MODEL_UPDATED,
                    payload={"attempt_id": getattr(self.agent, "_stale_attempt_id", -1), "updated_concepts": []},
                    correlation_id=stale_cid,
                )
                await self.send(stale)

            mu = self.agent.build_message(
                to=config.AGENT_COORDINATOR_JID,
                performative=Performative.INFORM,
                ontology=Ontology.MODEL_UPDATED,
                payload={
                    "user_id": payload.get("user_id"),
                    "attempt_id": payload.get("attempt_id"),
                    "updated_concepts": getattr(self.agent, "_updated_concepts", []),
                },
                correlation_id=cid,
            )
            await self.send(mu)

    async def setup(self) -> None:
        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.ATTEMPT_RESULT)
        self.add_behaviour(self._B(), tmpl)


class _MockRecommender(TutorAgent):
    """JID 'recommender': na recommend-next odgovara pošiljatelju (osim ako _silent)."""

    class _B(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return
            if getattr(self.agent, "_silent", False):
                return
            cid = msg.get_metadata("correlation_id")
            reply = self.agent.build_message(
                to=str(msg.sender),
                performative=Performative.INFORM,
                ontology=Ontology.RECOMMEND_NEXT,
                payload=getattr(self.agent, "_reply_payload", {"task_id": None, "concept": None, "reason": "ok"}),
                correlation_id=cid,
            )
            await self.send(reply)

    async def setup(self) -> None:
        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.RECOMMEND_NEXT)
        self.add_behaviour(self._B(), tmpl)


class _GatewayProbe(TutorAgent):
    """Glumi 3E.3 gateway: šalje submit-attempt, hvata attempt-response. Vlastiti JID."""

    def __init__(self) -> None:
        # Zaobiđi jids.py registry (probe nije jedan od 5 agenata).
        Agent.__init__(self, jid=_PROBE_JID, password=_PROBE_PW, port=config.XMPP_PORT, verify_security=False)

    class _Listen(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return
            self.agent._responses.append({
                "cid": msg.get_metadata("correlation_id"),
                "payload": body_to_payload(msg.body),
            })

    async def setup(self) -> None:
        self._responses: list[dict] = []  # OUTPUT
        tmpl = Template()
        tmpl.set_metadata("ontology", ONTOLOGY_ATTEMPT_RESPONSE)
        self.add_behaviour(self._Listen(), tmpl)

    def send_submit(self, *, user_id: int, task_id: int, cid: str) -> None:
        probe = self

        class _Send(OneShotBehaviour):
            async def run(self) -> None:
                msg = probe.build_message(
                    to=config.AGENT_COORDINATOR_JID,
                    performative=Performative.REQUEST,
                    ontology=ONTOLOGY_SUBMIT_ATTEMPT,
                    payload={"user_id": user_id, "task_id": task_id, "submitted_query": "SELECT 1;"},
                    correlation_id=cid,
                )
                await self.send(msg)

        self.add_behaviour(_Send())


# ---------------------------------------------------------------------------
# Helperi
# ---------------------------------------------------------------------------


async def _poll(condition_fn, *, timeout: float = 15.0, interval: float = 0.2) -> None:
    end = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < end:
        if condition_fn():
            return
        await asyncio.sleep(interval)
    raise TimeoutError(f"Uvjet nije zadovoljen u {timeout}s")


def _find(probe: _GatewayProbe, cid: str) -> dict | None:
    return next((r for r in probe._responses if r["cid"] == cid), None)


async def _start(*agents) -> None:
    for a in agents:
        # gateway-probe nije pre-registriran kroz scripts/register_agents → auto_register
        auto = isinstance(a, _GatewayProbe)
        await a.start(auto_register=auto)
    await asyncio.sleep(0.6)


async def _stop(*agents) -> None:
    for a in agents:
        if a.is_alive():
            await a.stop()


@asynccontextmanager
async def _running(*agents):
    await _start(*agents)
    try:
        yield
    finally:
        await _stop(*agents)
        await asyncio.sleep(0.1)


# ---------------------------------------------------------------------------
# T1 — HAPPY PATH
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_full_flow(coord_env):
    """Točan attempt → attempt-response: feedback(correct) + xp_delta>0 + recommendation(task_id).
    cid propagiran kroz cijeli lanac (start.cid == response.cid)."""
    user_id, task_id = coord_env["user_id"], coord_env["task_id"]
    attempt_id = _make_attempt(user_id, task_id, is_correct=True, error_type=None, attempt_number=1, xp_delta=10)
    cid = str(uuid.uuid4())

    coordinator = CoordinatorAgent("coordinator")
    ev = _MockEvaluator("evaluator"); ev._attempt_id = attempt_id
    km = _MockKnowledge("knowledge"); km._updated_concepts = ["agg_count"]
    rec = _MockRecommender("recommender"); rec._reply_payload = {"task_id": task_id, "concept": "agg_count", "reason": "zpd"}
    probe = _GatewayProbe()

    async with _running(coordinator, ev, km, rec, probe):
        probe.send_submit(user_id=user_id, task_id=task_id, cid=cid)
        await _poll(lambda: _find(probe, cid) is not None)

    resp = _find(probe, cid)
    assert resp is not None, "gateway nije dobio attempt-response"
    assert resp["cid"] == cid, "cid mora biti propagiran kroz cijeli lanac"
    p = resp["payload"]
    assert p["feedback"]["is_correct"] is True
    assert p["feedback"]["verdict"] == "correct"
    assert p["gamification"]["xp_delta"] == 10
    assert p["recommendation"]["task_id"] == task_id


# ---------------------------------------------------------------------------
# T2 — 🔴 MEHANIČKA GREŠKA (syntax_error, updated_concepts:[])
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mechanical_error_does_not_hang(coord_env):
    """syntax_error → KM šalje model-updated s updated_concepts:[] → flow NE visi:
    feedback(syntax_error), xp_delta=0, recommendation prisutan."""
    user_id, task_id = coord_env["user_id"], coord_env["task_id"]
    attempt_id = _make_attempt(user_id, task_id, is_correct=False, error_type="syntax_error", attempt_number=1)
    cid = str(uuid.uuid4())

    coordinator = CoordinatorAgent("coordinator")
    ev = _MockEvaluator("evaluator"); ev._attempt_id = attempt_id
    km = _MockKnowledge("knowledge"); km._updated_concepts = []  # 3E.1 guard
    rec = _MockRecommender("recommender"); rec._reply_payload = {"task_id": task_id, "concept": "x", "reason": "review"}
    probe = _GatewayProbe()

    async with _running(coordinator, ev, km, rec, probe):
        probe.send_submit(user_id=user_id, task_id=task_id, cid=cid)
        await _poll(lambda: _find(probe, cid) is not None)

    p = _find(probe, cid)["payload"]
    assert p["feedback"]["error_type"] == "syntax_error"
    assert p["feedback"]["is_correct"] is False
    assert p["gamification"]["xp_delta"] == 0
    assert p["recommendation"]["task_id"] == task_id, "Recommender svejedno odgovara na grešci"


# ---------------------------------------------------------------------------
# T3 — 🔴 KM TIMEOUT (anti-hang guard)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_km_timeout_returns_error_and_recovers(coord_env):
    """model-updated NIKAD ne stigne → UPDATE timeout → attempt-response=evaluation_timeout,
    FSM NE visi i oporavi se (idući flow prolazi normalno)."""
    user_id, task_id = coord_env["user_id"], coord_env["task_id"]
    attempt_id = _make_attempt(user_id, task_id, is_correct=True, error_type=None, attempt_number=1, xp_delta=5)

    coordinator = CoordinatorAgent("coordinator", update_timeout=1.0)
    ev = _MockEvaluator("evaluator"); ev._attempt_id = attempt_id
    km = _MockKnowledge("knowledge"); km._silent = True  # KM ne javlja → timeout
    rec = _MockRecommender("recommender"); rec._reply_payload = {"task_id": task_id, "concept": "x", "reason": "zpd"}
    probe = _GatewayProbe()

    cid1, cid2 = str(uuid.uuid4()), str(uuid.uuid4())

    async with _running(coordinator, ev, km, rec, probe):
        # Flow 1 — KM šuti → evaluation_timeout
        probe.send_submit(user_id=user_id, task_id=task_id, cid=cid1)
        await _poll(lambda: _find(probe, cid1) is not None)
        r1 = _find(probe, cid1)["payload"]
        assert r1.get("error") == ERROR_EVALUATION_TIMEOUT, "KM timeout mora dati definiran error"
        assert r1["correlation_id"] == cid1

        # Flow 2 — KM proradi → dokaz da se FSM vratio na RECEIVE (nije zaglavio)
        km._silent = False
        probe.send_submit(user_id=user_id, task_id=task_id, cid=cid2)
        await _poll(lambda: _find(probe, cid2) is not None)

    r2 = _find(probe, cid2)["payload"]
    assert "error" not in r2, "FSM se mora oporaviti i normalno obraditi idući flow"
    assert r2["feedback"]["is_correct"] is True


# ---------------------------------------------------------------------------
# T4 — RECOMMEND timeout (degradacija, ne hang)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recommend_timeout_degrades(coord_env):
    """Recommender ne odgovori → recommendation=None reason=recommend_timeout, response svejedno stigne."""
    user_id, task_id = coord_env["user_id"], coord_env["task_id"]
    attempt_id = _make_attempt(user_id, task_id, is_correct=True, error_type=None, attempt_number=1, xp_delta=8)
    cid = str(uuid.uuid4())

    coordinator = CoordinatorAgent("coordinator", recommend_timeout=1.0)
    ev = _MockEvaluator("evaluator"); ev._attempt_id = attempt_id
    km = _MockKnowledge("knowledge"); km._updated_concepts = ["x"]
    rec = _MockRecommender("recommender"); rec._silent = True  # Recommender šuti
    probe = _GatewayProbe()

    async with _running(coordinator, ev, km, rec, probe):
        probe.send_submit(user_id=user_id, task_id=task_id, cid=cid)
        await _poll(lambda: _find(probe, cid) is not None)

    p = _find(probe, cid)["payload"]
    assert p["recommendation"]["task_id"] is None
    assert p["recommendation"]["reason"] == REASON_RECOMMEND_TIMEOUT
    assert p["feedback"]["is_correct"] is True, "feedback mora doći i kad preporuka degradira"


# ---------------------------------------------------------------------------
# T5 — cid korelacija (sekvencijalno — GATE 2 serijalizira)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cid_correlation_two_sequential_flows(coord_env):
    """Dva flowa zaredom (različiti cid + attempt) → svaki dobije SVOJ response, bez cross-talka.

    Sekvencijalno jer FSMBehaviour serijalizira (GATE 2, svjesna MVP odluka)."""
    user_id, task_id = coord_env["user_id"], coord_env["task_id"]
    a1 = _make_attempt(user_id, task_id, is_correct=True, error_type=None, attempt_number=1, xp_delta=3)
    a2 = _make_attempt(user_id, task_id, is_correct=False, error_type="row_mismatch", attempt_number=2)
    cid1, cid2 = str(uuid.uuid4()), str(uuid.uuid4())

    coordinator = CoordinatorAgent("coordinator")
    ev = _MockEvaluator("evaluator")
    km = _MockKnowledge("knowledge"); km._updated_concepts = ["x"]
    rec = _MockRecommender("recommender"); rec._reply_payload = {"task_id": task_id, "concept": "x", "reason": "zpd"}
    probe = _GatewayProbe()

    async with _running(coordinator, ev, km, rec, probe):
        ev._attempt_id = a1
        probe.send_submit(user_id=user_id, task_id=task_id, cid=cid1)
        await _poll(lambda: _find(probe, cid1) is not None)

        ev._attempt_id = a2
        probe.send_submit(user_id=user_id, task_id=task_id, cid=cid2)
        await _poll(lambda: _find(probe, cid2) is not None)

    r1, r2 = _find(probe, cid1)["payload"], _find(probe, cid2)["payload"]
    assert r1["feedback"]["attempt_id"] == a1 and r1["correlation_id"] == cid1
    assert r2["feedback"]["attempt_id"] == a2 and r2["correlation_id"] == cid2
    assert r1["feedback"]["is_correct"] is True
    assert r2["feedback"]["is_correct"] is False


# ---------------------------------------------------------------------------
# T6 — 🔴 STALE-MESSAGE GUARD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stale_message_guard_drops_foreign_cid(coord_env):
    """U queue stigne model-updated sa STRANIM cid (od timeoutanog flowa) PA pravi sa self.cid →
    UPDATE odbaci tuđi, uhvati svoj → ispravan attempt_id (ne stale)."""
    user_id, task_id = coord_env["user_id"], coord_env["task_id"]
    real_attempt = _make_attempt(user_id, task_id, is_correct=True, error_type=None, attempt_number=1, xp_delta=7)
    cid_b = str(uuid.uuid4())
    foreign_cid = str(uuid.uuid4())  # cid "prethodnog timeoutanog flowa A"

    coordinator = CoordinatorAgent("coordinator")
    ev = _MockEvaluator("evaluator"); ev._attempt_id = real_attempt
    km = _MockKnowledge("knowledge")
    km._updated_concepts = ["x"]
    km._stale_cid = foreign_cid          # podmetni stranu poruku prije prave
    km._stale_attempt_id = 999999        # nepostojeći attempt → dokaz da NIJE uzet
    rec = _MockRecommender("recommender"); rec._reply_payload = {"task_id": task_id, "concept": "x", "reason": "zpd"}
    probe = _GatewayProbe()

    async with _running(coordinator, ev, km, rec, probe):
        probe.send_submit(user_id=user_id, task_id=task_id, cid=cid_b)
        await _poll(lambda: _find(probe, cid_b) is not None)

    p = _find(probe, cid_b)["payload"]
    assert p["correlation_id"] == cid_b
    assert p["feedback"]["attempt_id"] == real_attempt, (
        "UPDATE je uzeo tuđu (stale) poruku — correlation guard ne radi"
    )
    assert p["feedback"]["is_correct"] is True
