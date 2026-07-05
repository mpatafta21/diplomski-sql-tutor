"""Integracijski testovi POST /run + GET /admin/agent-logs — Faza 4.0a-4.

/run: čisti sandbox exec (reuse SandboxRunner), ništa ne perzistira.
      Zahtijeva ŽIV sandbox (isti obrazac kao test_sandbox_runner.py — bez skip markera,
      sandbox_connection_string fixture ima fallback na localhost:5433).

/admin/agent-logs: read kroz to_thread. Logovi se ubacuju s JEDINSTVENIM correlation_id
      pa se filtrira po njemu (izbjegava sudar s tragovima drugih testova). Teardown briše.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import delete, func, select

from app.db.models import AgentMessageLog, Attempt, User
from app.db.session import SessionLocal
from app.main import create_app
from tests.conftest import auth_header


@asynccontextmanager
async def _client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as c:
        yield c


def _make_user_with_role(username: str, role: str) -> int:
    with SessionLocal() as s:
        u = User(
            username=username,
            email=f"{username}@test.example",
            password_hash="dummy_hash_402b2",
            role=role,
        )
        s.add(u)
        s.commit()
        return u.id


@pytest.fixture
def student_auth():
    """Committed student → auth header za gated /run."""
    uid = _make_user_with_role("run_student_402b2", "student")
    yield auth_header(uid, role="student")
    with SessionLocal() as s:
        s.execute(delete(User).where(User.id == uid))
        s.commit()


@pytest.fixture
def admin_auth():
    """Committed admin → auth header za admin-guarded /admin/agent-logs.

    role u tokenu se generira iz auth_header(role="admin"); require_admin gleda
    user.role iz DB-a, pa user MORA biti admin i u bazi."""
    uid = _make_user_with_role("admin_logs_402b2", "admin")
    yield {"header": auth_header(uid, role="admin"), "uid": uid}
    with SessionLocal() as s:
        s.execute(delete(User).where(User.id == uid))
        s.commit()


def _attempts_count() -> int:
    with SessionLocal() as s:
        return s.scalar(select(func.count()).select_from(Attempt))


# ===========================================================================
# POST /run
# ===========================================================================


@pytest.mark.asyncio
async def test_run_valid_select(student_auth):
    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/run",
            json={"query": "SELECT id FROM products LIMIT 3"},
            headers=student_auth,
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["error"] is None
    assert body["columns"] == ["id"]
    assert len(body["rows"]) == 3
    assert body["exec_ms"] >= 0


@pytest.mark.asyncio
async def test_run_syntax_error_is_200_with_error(student_auth):
    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/run", json={"query": "SELEC bogus FROM"}, headers=student_auth
        )

    assert resp.status_code == 200, resp.text  # NE 500
    body = resp.json()
    assert body["error"] is not None
    assert isinstance(body["error"], str)
    assert body["rows"] == []


@pytest.mark.asyncio
async def test_run_does_not_persist_attempt(student_auth):
    before = _attempts_count()
    app = create_app()
    async with _client(app) as client:
        await client.post(
            "/run",
            json={"query": "SELECT id FROM products LIMIT 1"},
            headers=student_auth,
        )
    after = _attempts_count()
    assert before == after, "/run NE smije kreirati attempt red"


@pytest.mark.asyncio
async def test_run_rejects_ddl_readonly(student_auth):
    """DDL pod readonly rolom + dml=False → error (permission denied), NE uspjeh."""
    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/run",
            json={"query": "CREATE TABLE zzz_run_test (x int)"},
            headers=student_auth,
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["error"] is not None, "DDL mora pasti (readonly rola)"

    # dokaz da tablica NIJE nastala: sljedeći upit na nju mora pasti isto
    async with _client(app) as client:
        check = await client.post(
            "/run", json={"query": "SELECT * FROM zzz_run_test"}, headers=student_auth
        )
    assert check.json()["error"] is not None


@pytest.mark.asyncio
async def test_run_task_id_optional_ignored(student_auth):
    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/run",
            json={"task_id": 12345, "query": "SELECT id FROM products LIMIT 1"},
            headers=student_auth,
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["error"] is None


# ===========================================================================
# GET /admin/agent-logs
# ===========================================================================


@pytest.fixture
def agent_logs():
    """Ubaci 3 AgentMessageLog reda s jedinstvenim correlation_id-em. Teardown briše."""
    cid = uuid.uuid4()
    other_cid = uuid.uuid4()
    base = datetime.now(timezone.utc) - timedelta(minutes=10)

    with SessionLocal() as s:
        # NE-kronološkim redom ubacivanja da dokažemo ORDER BY created_at DESC
        s.add(
            AgentMessageLog(
                sender="coordinator",
                receiver="evaluator",
                performative="request",
                content={"step": 2},
                correlation_id=cid,
                created_at=base + timedelta(minutes=2),
            )
        )
        s.add(
            AgentMessageLog(
                sender="evaluator",
                receiver="knowledge",
                performative="inform",
                content={"step": 1},
                correlation_id=cid,
                created_at=base + timedelta(minutes=1),
            )
        )
        s.add(
            AgentMessageLog(
                sender="coordinator",
                receiver="recommender",
                performative="request",
                content={"step": 3},
                correlation_id=cid,
                created_at=base + timedelta(minutes=3),
            )
        )
        # tuđi cid — ne smije se pojaviti pri filtru po cid
        s.add(
            AgentMessageLog(
                sender="gamification",
                receiver="coordinator",
                performative="inform",
                content=None,
                correlation_id=other_cid,
                created_at=base,
            )
        )
        s.commit()

    yield {"cid": cid, "other_cid": other_cid}

    with SessionLocal() as s:
        s.execute(
            delete(AgentMessageLog).where(
                AgentMessageLog.correlation_id.in_([cid, other_cid])
            )
        )
        s.commit()


@pytest.mark.asyncio
async def test_agent_logs_filter_by_correlation_id_desc(agent_logs, admin_auth):
    cid = str(agent_logs["cid"])
    app = create_app()
    async with _client(app) as client:
        resp = await client.get(
            "/admin/agent-logs",
            params={"correlation_id": cid},
            headers=admin_auth["header"],
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3  # samo naš cid
    items = body["items"]
    assert all(i["correlation_id"] == cid for i in items)
    # DESC → step 3, 2, 1
    assert [i["content"]["step"] for i in items] == [3, 2, 1]
    # oblik jednog reda
    assert set(items[0].keys()) == {
        "id",
        "sender",
        "receiver",
        "performative",
        "content",
        "correlation_id",
        "created_at",
    }


@pytest.mark.asyncio
async def test_agent_logs_filter_by_sender(agent_logs, admin_auth):
    cid = str(agent_logs["cid"])
    app = create_app()
    async with _client(app) as client:
        resp = await client.get(
            "/admin/agent-logs",
            params={"correlation_id": cid, "sender": "coordinator"},
            headers=admin_auth["header"],
        )
    body = resp.json()
    assert body["total"] == 2
    assert all(i["sender"] == "coordinator" for i in body["items"])


@pytest.mark.asyncio
async def test_agent_logs_invalid_uuid_422(admin_auth):
    app = create_app()
    async with _client(app) as client:
        resp = await client.get(
            "/admin/agent-logs",
            params={"correlation_id": "abc"},
            headers=admin_auth["header"],
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_agent_logs_limit_clamp_200(agent_logs, admin_auth):
    cid = str(agent_logs["cid"])
    app = create_app()
    async with _client(app) as client:
        resp = await client.get(
            "/admin/agent-logs",
            params={"correlation_id": cid, "limit": 999},
            headers=admin_auth["header"],
        )
    assert resp.json()["limit"] == 200  # clamp, ne 422
