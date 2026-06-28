"""Integracijski testovi HTTP gatewaya — Faza 3E.3 (zatvara Fazu 3E).

End-to-end: HTTP (httpx ASGITransport) → AgentBridge → FIPA Coordinatoru → FSM →
FIPA reply → bridge → HTTP. Coordinator se izolira kontroliranim mock agentima
(reuse iz test_coordinator), pa testovi ne ovise o sandboxu.

🔴 SAME-LOOP: agenti se startaju na istom event loopu kao HTTP handleri (plain-bridge
invariant iz 3E.2a). test_same_loop_bridge_resolves to dokazuje i identitetom loopa
i funkcionalno (bridge.resolve iz Coordinatora → HTTP handler ga pokupi).

Zahtijeva živući Prosody (5222) + tutor_main DB s registriranim agentima.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest
from sqlalchemy import delete, select

from agents.coordinator import CoordinatorAgent
from app.core import config
from app.db.models import (
    Attempt,
    Badge,
    Concept,
    Misconception,
    SkillMastery,
    Task,
    User,
    UserBadge,
    XpLog,
)
from app.db.session import SessionLocal
from app.main import create_app, start_gateway_stack, stop_gateway_stack

# Reuse kontroliranih mock agenata + helpera iz 3E.2b
from tests.test_coordinator import (  # noqa: E402
    _make_attempt,
    _MockEvaluator,
    _MockKnowledge,
    _MockRecommender,
)


# ---------------------------------------------------------------------------
# Fixtures / helperi
# ---------------------------------------------------------------------------


@pytest.fixture
def api_user():
    """Committed test user + valjan task_id. Teardown briše sve vezane redove."""
    with SessionLocal() as sess:
        user = User(
            username="api_e2e_user_3e3",
            email="api_e2e_3e3@test.example",
            password_hash="dummy_hash_3e3",
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
        cleanup.execute(delete(SkillMastery).where(SkillMastery.user_id == user_id))
        cleanup.execute(delete(UserBadge).where(UserBadge.user_id == user_id))
        cleanup.execute(delete(Misconception).where(Misconception.user_id == user_id))
        cleanup.execute(delete(User).where(User.id == user_id))
        cleanup.commit()


@asynccontextmanager
async def _stack(app, agents):
    await start_gateway_stack(app, agents=agents)
    await asyncio.sleep(0.6)  # XMPP presence/connect settle
    try:
        yield
    finally:
        await stop_gateway_stack(app)
        await asyncio.sleep(0.1)


@asynccontextmanager
async def _client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


def _happy_mocks(*, attempt_id: int, task_id: int):
    ev = _MockEvaluator("evaluator"); ev._attempt_id = attempt_id
    km = _MockKnowledge("knowledge"); km._updated_concepts = ["agg_count"]
    rec = _MockRecommender("recommender")
    rec._reply_payload = {"task_id": task_id, "concept": "agg_count", "reason": "zpd"}
    coord = CoordinatorAgent("coordinator")
    return ev, km, rec, coord


# ---------------------------------------------------------------------------
# 🔴 T1 — SAME-LOOP (preduvjet: plain bridge radi samo na zajedničkom loopu)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_same_loop_bridge_resolves(api_user):
    """🔴 Plain-bridge preduvjet: bridge.resolve iz Coordinatorovog behavioura rezolvira
    Future koji HTTP handler čeka — što uspijeva SAMO ako oba teku na istom event loopu.

    FUNKCIONALNI dokaz (ne identitet `agent.loop` atributa): SPADE zakazuje behaviour
    preko asyncio.create_task na TEKUĆEM loopu (ne na agent.loop), a bridge Future se
    kreira/rezolvira na istom tekućem loopu. Ako bi se loopovi razlikovali, set_result
    bi bio na drugom loopu nego awaiter → bridge.wait bi istekao → HTTP 504. Dakle 200
    (a ne 504) je konkluzivan dokaz zajedničkog loopa.

    (Napomena: `coord.loop` atribut je nepouzdan u test-procesu — SPADE Container je
    proces-singleton i ne re-binda loop; izvršavanje ipak ide na running loop preko
    create_task. U produkciji je prva instancijacija u uvicorn loopu, pa je i atribut točan.)"""
    user_id, task_id = api_user["user_id"], api_user["task_id"]
    attempt_id = _make_attempt(user_id, task_id, is_correct=True, error_type=None, attempt_number=1, xp_delta=4)
    app = create_app()
    ev, km, rec, coord = _happy_mocks(attempt_id=attempt_id, task_id=task_id)

    async with _stack(app, [ev, km, rec, coord]), _client(app) as client:
        resp = await client.post(
            "/attempt",
            json={"user_id": user_id, "task_id": task_id, "submitted_query": "SELECT 1;"},
        )

    assert resp.status_code == 200, (
        f"bridge.wait nije rezolviran (status {resp.status_code}) — resolve i awaiter "
        "nisu na istom loopu → plain-bridge invariant prekršen"
    )
    assert resp.json()["feedback"]["is_correct"] is True


# ---------------------------------------------------------------------------
# T2 — POST /attempt happy path (end-to-end)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_attempt_happy(api_user):
    user_id, task_id = api_user["user_id"], api_user["task_id"]
    attempt_id = _make_attempt(user_id, task_id, is_correct=True, error_type=None, attempt_number=1, xp_delta=10)
    app = create_app()
    ev, km, rec, coord = _happy_mocks(attempt_id=attempt_id, task_id=task_id)

    async with _stack(app, [ev, km, rec, coord]), _client(app) as client:
        resp = await client.post(
            "/attempt",
            json={"user_id": user_id, "task_id": task_id, "submitted_query": "SELECT 1;"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["feedback"]["is_correct"] is True
    assert body["feedback"]["error_type"] is None
    assert body["xp_delta"] == 10
    assert body["recommendation"]["task_id"] == task_id


# ---------------------------------------------------------------------------
# T3 — POST /attempt mehanička greška (syntax_error)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_attempt_mechanical_error(api_user):
    user_id, task_id = api_user["user_id"], api_user["task_id"]
    attempt_id = _make_attempt(user_id, task_id, is_correct=False, error_type="syntax_error", attempt_number=1)
    app = create_app()
    ev = _MockEvaluator("evaluator"); ev._attempt_id = attempt_id
    km = _MockKnowledge("knowledge"); km._updated_concepts = []  # 3E.1 guard
    rec = _MockRecommender("recommender")
    rec._reply_payload = {"task_id": task_id, "concept": "x", "reason": "review"}
    coord = CoordinatorAgent("coordinator")

    async with _stack(app, [ev, km, rec, coord]), _client(app) as client:
        resp = await client.post(
            "/attempt",
            json={"user_id": user_id, "task_id": task_id, "submitted_query": "SELEC *;"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["feedback"]["error_type"] == "syntax_error"
    assert body["feedback"]["is_correct"] is False
    assert body["xp_delta"] == 0


# ---------------------------------------------------------------------------
# 🔴 T4 — POST /attempt orchestration timeout → 504 (NE hang)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_attempt_timeout_returns_504(api_user):
    user_id, task_id = api_user["user_id"], api_user["task_id"]
    _make_attempt(user_id, task_id, is_correct=True, error_type=None, attempt_number=1, xp_delta=5)
    app = create_app()
    ev = _MockEvaluator("evaluator")
    km = _MockKnowledge("knowledge"); km._silent = True  # KM šuti → Coordinator evaluation_timeout
    rec = _MockRecommender("recommender")
    coord = CoordinatorAgent("coordinator", update_timeout=1.0)

    async with _stack(app, [ev, km, rec, coord]), _client(app) as client:
        resp = await client.post(
            "/attempt",
            json={"user_id": user_id, "task_id": task_id, "submitted_query": "SELECT 1;"},
        )

    assert resp.status_code == 504, resp.text
    assert resp.json()["detail"] == "evaluation_timeout"


# ---------------------------------------------------------------------------
# T5 — GET /next-task (izravan recommend-next kroz bridge)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_next_task(api_user):
    user_id, task_id = api_user["user_id"], api_user["task_id"]
    app = create_app()
    rec = _MockRecommender("recommender")
    rec._reply_payload = {"task_id": task_id, "concept": "group_by", "reason": "zpd"}

    async with _stack(app, [rec]), _client(app) as client:
        resp = await client.get("/next-task", params={"user_id": user_id})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["task_id"] == task_id
    assert body["concept"] == "group_by"
    assert body["reason"] == "zpd"


# ---------------------------------------------------------------------------
# T6 — GET /profile (čisti DB read, nezavisan od agenata)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_profile_pure_db_read(api_user):
    """/profile radi BEZ ijednog pokrenutog agenta (čisti DB read)."""
    user_id = api_user["user_id"]
    with SessionLocal() as sess:
        user = sess.get(User, user_id)
        user.xp = 250
        user.level = 3
        user.current_streak = 4
        user.longest_streak = 9
        concept_id = sess.scalar(select(Concept.id).limit(1))
        sess.add(SkillMastery(user_id=user_id, concept_id=concept_id, p_l=0.72))
        sess.commit()

    app = create_app()  # NE pokrećemo stack — dokaz neovisnosti o agentima
    async with _client(app) as client:
        resp = await client.get("/profile", params={"user_id": user_id})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["xp"] == 250
    assert body["level"] == 3
    assert body["current_streak"] == 4
    assert body["longest_streak"] == 9
    assert len(body["mastery"]) == 1
    assert body["mastery"][0]["p_l"] == pytest.approx(0.72)


@pytest.mark.asyncio
async def test_get_profile_unknown_user_404():
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/profile", params={"user_id": 999999999})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# T7 — malformed body → 422 (Pydantic validacija)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_attempt_malformed_body_422():
    app = create_app()
    async with _client(app) as client:
        resp = await client.post("/attempt", json={"user_id": 1})  # fale task_id, submitted_query
    assert resp.status_code == 422
