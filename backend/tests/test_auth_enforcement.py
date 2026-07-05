"""Auth-enforcement testovi — Faza 4.0b.2 (dokaz da gate stvarno radi).

Tri invarijante:
  1. Bez tokena → 401 na SVIM zaštićenim rutama.
  2. /admin/agent-logs: student → 403, admin → 200.
  3. Spoof-proof: /attempt ide za usera IZ TOKENA — klijent ne može podvaliti drugi
     user_id (AttemptRequest ga više nema; čak i ubačeni body "user_id" se ignorira).

Test 3 koristi isti mock-agent stack kao test_api.py (kontrolirani Coordinator tok).
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest
from sqlalchemy import delete, select

from agents.coordinator import CoordinatorAgent
from app.db.models import (
    Attempt,
    Misconception,
    SkillMastery,
    Task,
    User,
    UserBadge,
    XpLog,
)
from app.db.session import SessionLocal
from app.main import create_app, start_gateway_stack, stop_gateway_stack
from tests.conftest import auth_header
from tests.test_coordinator import (  # noqa: E402
    _make_attempt,
    _MockEvaluator,
    _MockKnowledge,
    _MockRecommender,
)


@asynccontextmanager
async def _client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as c:
        yield c


# ===========================================================================
# 1. Bez tokena → 401 (za POST rute šaljemo VALJAN body da samo auth padne)
# ===========================================================================

_PROTECTED = [
    ("get", "/profile", None),
    ("get", "/next-task", None),
    ("get", "/attempts", None),
    ("get", "/mastery-history", None),
    ("get", "/modules", None),
    ("get", "/badges", None),
    ("get", "/leaderboard", None),
    ("get", "/task/1", None),
    ("get", "/me", None),
    ("get", "/admin/agent-logs", None),
    ("post", "/run", {"query": "SELECT 1"}),
    ("post", "/attempt", {"task_id": 1, "submitted_query": "SELECT 1"}),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path,body", _PROTECTED)
async def test_protected_route_without_token_401(method, path, body):
    app = create_app()
    async with _client(app) as client:
        if method == "post":
            resp = await client.post(path, json=body)
        else:
            resp = await client.get(path)
    assert resp.status_code == 401, f"{method.upper()} {path} bez tokena → {resp.status_code}"


# ===========================================================================
# 2. /admin/agent-logs — role guard
# ===========================================================================


@pytest.fixture
def role_users():
    """Committed student + admin. Teardown briše oba."""
    ids = {}
    with SessionLocal() as s:
        student = User(
            username="enf_student_402b2",
            email="enf_student_402b2@test.example",
            password_hash="dummy",
            role="student",
        )
        admin = User(
            username="enf_admin_402b2",
            email="enf_admin_402b2@test.example",
            password_hash="dummy",
            role="admin",
        )
        s.add_all([student, admin])
        s.commit()
        ids = {"student": student.id, "admin": admin.id}
    yield ids
    with SessionLocal() as s:
        s.execute(delete(User).where(User.id.in_(list(ids.values()))))
        s.commit()


@pytest.mark.asyncio
async def test_admin_logs_student_forbidden_403(role_users):
    app = create_app()
    async with _client(app) as client:
        resp = await client.get(
            "/admin/agent-logs", headers=auth_header(role_users["student"], "student")
        )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "admin_required"


@pytest.mark.asyncio
async def test_admin_logs_admin_ok_200(role_users):
    app = create_app()
    async with _client(app) as client:
        resp = await client.get(
            "/admin/agent-logs", headers=auth_header(role_users["admin"], "admin")
        )
    assert resp.status_code == 200


# ===========================================================================
# 3. Spoof-proof: attempt ide za TOKEN-usera, ne za body-podvaljeni user_id
# ===========================================================================


@pytest.fixture
def two_users():
    """User A (xp=111) i B (xp=999) + valjan task. Teardown briše sve vezano."""
    with SessionLocal() as s:
        a = User(
            username="enf_A_402b2",
            email="enf_A_402b2@test.example",
            password_hash="dummy",
            xp=111,
            level=2,
        )
        b = User(
            username="enf_B_402b2",
            email="enf_B_402b2@test.example",
            password_hash="dummy",
            xp=999,
            level=9,
        )
        s.add_all([a, b])
        s.commit()
        a_id, b_id = a.id, b.id
        task_id = s.scalar(select(Task.id).limit(1))
    assert task_id is not None, "tasks moraju biti seedani"

    yield {"a_id": a_id, "b_id": b_id, "task_id": task_id}

    with SessionLocal() as s:
        for uid in (a_id, b_id):
            s.execute(delete(XpLog).where(XpLog.user_id == uid))
            s.execute(delete(Attempt).where(Attempt.user_id == uid))
            s.execute(delete(SkillMastery).where(SkillMastery.user_id == uid))
            s.execute(delete(UserBadge).where(UserBadge.user_id == uid))
            s.execute(delete(Misconception).where(Misconception.user_id == uid))
        s.execute(delete(User).where(User.id.in_([a_id, b_id])))
        s.commit()


@asynccontextmanager
async def _stack(app, agents):
    await start_gateway_stack(app, agents=agents)
    await asyncio.sleep(0.6)
    try:
        yield
    finally:
        await stop_gateway_stack(app)
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_attempt_uses_token_user_not_body(two_users):
    """Token = user A; body podvaljuje "user_id": B. Attempt se bilježi za A, a odgovor
    (xp iz build_response_payload čita User[A]) pokazuje A.xp=111, ne B.xp=999.
    Dokaz: klijent NE bira user_id — dolazi iz tokena."""
    a_id, b_id, task_id = two_users["a_id"], two_users["b_id"], two_users["task_id"]
    # attempt se mora kreirati za A (mock evaluator vraća njegov attempt_id)
    attempt_id = _make_attempt(
        a_id, task_id, is_correct=True, error_type=None, attempt_number=1, xp_delta=0
    )

    app = create_app()
    ev = _MockEvaluator("evaluator")
    ev._attempt_id = attempt_id
    km = _MockKnowledge("knowledge")
    km._updated_concepts = ["agg_count"]
    rec = _MockRecommender("recommender")
    rec._reply_payload = {"task_id": task_id, "concept": "agg_count", "reason": "zpd"}
    coord = CoordinatorAgent("coordinator")

    async with _stack(app, [ev, km, rec, coord]), _client(app) as client:
        resp = await client.post(
            "/attempt",
            # "user_id": b_id je PODVALA — mora se ignorirati (schema ga nema)
            json={"user_id": b_id, "task_id": task_id, "submitted_query": "SELECT 1;"},
            headers=auth_header(a_id),
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    # gamification.xp dolazi iz User[token-usera=A] → 111, NE B (999)
    assert body["xp"] == 111, "attempt je otišao za krivog usera (spoof prošao!)"

    # i u DB: nijedan attempt/xp_log NIJE nastao za B
    with SessionLocal() as s:
        b_attempts = s.scalar(
            select(Attempt.id).where(Attempt.user_id == b_id).limit(1)
        )
    assert b_attempts is None, "B ne smije imati nijedan attempt"
