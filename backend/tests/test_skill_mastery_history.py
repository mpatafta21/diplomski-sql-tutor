"""TDD testovi za skill_mastery_history — Faza 4.0a-3.1.

Dva sloja:
  HOOK  — agents/knowledge_logic.update_mastery_for_attempt piše snapshot atomarno s
          mastery upsertom (isti commit). Pokreće se ČISTIM Python pozivom (bez XMPP),
          u stilu test_knowledge_logic.py (knowledge_env + prolog_engine fixture).
  ENDPOINT — GET /mastery-history (read kroz to_thread; commit+cleanup obrazac).

Cleanup FK redoslijed: skill_mastery_history → attempts → skill_mastery → users.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import delete, func, select

from agents.knowledge_logic import update_mastery_for_attempt
from app.db.models import (
    Attempt,
    Concept,
    SkillMastery,
    SkillMasteryHistory,
    Task,
    User,
)
from app.db.session import SessionLocal
from app.main import create_app
from app.prolog.prolog_engine import PrologEngine
from tests.conftest import auth_header

# Reuse committed-attempt helper (za validan attempt_id FK)
from tests.test_coordinator import _make_attempt  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures / helperi
# ---------------------------------------------------------------------------


@pytest.fixture
def smh_env():
    """Committed test user. Teardown: smh → attempts → skill_mastery → user."""
    with SessionLocal() as s:
        u = User(
            username="smh_user_3a31",
            email="smh_3a31@test.example",
            password_hash="dummy_hash_3a31",
        )
        s.add(u)
        s.commit()
        uid = u.id

    yield uid

    with SessionLocal() as s:
        s.execute(delete(SkillMasteryHistory).where(SkillMasteryHistory.user_id == uid))
        s.execute(delete(Attempt).where(Attempt.user_id == uid))
        s.execute(delete(SkillMastery).where(SkillMastery.user_id == uid))
        s.execute(delete(User).where(User.id == uid))
        s.commit()


@pytest.fixture
def prolog_engine():
    with PrologEngine() as engine:
        yield engine


@asynccontextmanager
async def _client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as c:
        yield c


def _concept_id(code: str) -> int:
    with SessionLocal() as s:
        cid = s.scalar(select(Concept.id).where(Concept.code == code))
    assert cid is not None, f"Koncept {code!r} nije seedan"
    return cid


def _some_task_id() -> int:
    with SessionLocal() as s:
        tid = s.scalar(select(Task.id).limit(1))
    assert tid is not None, "tasks moraju biti seedani"
    return tid


def _history_rows(user_id: int) -> list[SkillMasteryHistory]:
    with SessionLocal() as s:
        return list(
            s.execute(
                select(SkillMasteryHistory)
                .where(SkillMasteryHistory.user_id == user_id)
                .order_by(
                    SkillMasteryHistory.created_at.asc(), SkillMasteryHistory.id.asc()
                )
            ).scalars()
        )


def _insert_history(
    user_id: int,
    code: str,
    p_l: float,
    created_at: datetime,
    attempt_id: int | None = None,
) -> None:
    with SessionLocal() as s:
        s.add(
            SkillMasteryHistory(
                user_id=user_id,
                concept_id=_concept_id(code),
                p_l=p_l,
                attempt_id=attempt_id,
                created_at=created_at,
            )
        )
        s.commit()


# ===========================================================================
# HOOK
# ===========================================================================


@pytest.mark.asyncio
async def test_hook_creates_one_history_row(smh_env, prolog_engine):
    uid = smh_env
    task_id = _some_task_id()
    attempt_id = _make_attempt(
        uid, task_id, is_correct=True, error_type=None, attempt_number=1
    )

    with SessionLocal() as sess:
        result = await update_mastery_for_attempt(
            sess,
            prolog_engine,
            uid,
            ["agg_count"],
            is_correct=True,
            attempt_id=attempt_id,
        )

    assert "agg_count" in result
    rows = _history_rows(uid)
    assert len(rows) == 1
    r = rows[0]
    assert r.user_id == uid
    assert r.concept_id == _concept_id("agg_count")
    assert r.p_l == pytest.approx(result["agg_count"])
    assert r.attempt_id == attempt_id


@pytest.mark.asyncio
async def test_hook_multiple_updates_progression(smh_env, prolog_engine):
    uid = smh_env
    for _ in range(3):
        with SessionLocal() as sess:
            await update_mastery_for_attempt(
                sess, prolog_engine, uid, ["agg_count"], is_correct=True
            )

    rows = _history_rows(uid)
    assert len(rows) == 3
    p_ls = [r.p_l for r in rows]
    # 3× correct → p_l monotono raste
    assert p_ls == sorted(p_ls)
    assert p_ls[0] < p_ls[-1]
    # created_at kronološki neopadajući
    cts = [r.created_at for r in rows]
    assert cts == sorted(cts)


@pytest.mark.asyncio
async def test_hook_multi_concept_one_row_each(smh_env, prolog_engine):
    uid = smh_env
    with SessionLocal() as sess:
        result = await update_mastery_for_attempt(
            sess, prolog_engine, uid, ["agg_count", "group_by"], is_correct=True
        )

    assert set(result.keys()) == {"agg_count", "group_by"}
    rows = _history_rows(uid)
    assert len(rows) == 2
    assert {r.concept_id for r in rows} == {
        _concept_id("agg_count"),
        _concept_id("group_by"),
    }


@pytest.mark.asyncio
async def test_hook_guard_no_upsert_no_history(smh_env, prolog_engine):
    """result == {} (nepoznat koncept) → NULA history redova."""
    uid = smh_env
    with SessionLocal() as sess:
        result = await update_mastery_for_attempt(
            sess, prolog_engine, uid, ["totally_unknown_concept_xyz"], is_correct=True
        )
    assert result == {}
    assert _history_rows(uid) == []


@pytest.mark.asyncio
async def test_hook_attempt_id_none_defaults(smh_env, prolog_engine):
    uid = smh_env
    with SessionLocal() as sess:
        await update_mastery_for_attempt(
            sess, prolog_engine, uid, ["agg_count"], is_correct=True
        )
    rows = _history_rows(uid)
    assert len(rows) == 1
    assert rows[0].attempt_id is None


# ===========================================================================
# ENDPOINT — GET /mastery-history
# ===========================================================================


@pytest.mark.asyncio
async def test_endpoint_chronological_and_fields(smh_env):
    uid = smh_env
    base = datetime.now(timezone.utc) - timedelta(hours=3)
    # ubaci NE-kronološkim redom da dokažemo ORDER BY created_at ASC
    _insert_history(uid, "agg_count", 0.30, base + timedelta(minutes=20))
    _insert_history(uid, "agg_count", 0.15, base)
    _insert_history(uid, "agg_count", 0.22, base + timedelta(minutes=10))

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/mastery-history", headers=auth_header(uid))

    assert resp.status_code == 200, resp.text
    points = resp.json()
    assert [p["p_l"] for p in points] == [0.15, 0.22, 0.30]  # kronološki asc
    assert all(p["concept"] == "agg_count" for p in points)
    assert all(
        set(p.keys()) == {"concept", "p_l", "attempt_id", "created_at"} for p in points
    )
    assert points[0]["attempt_id"] is None


@pytest.mark.asyncio
async def test_endpoint_concept_filter(smh_env):
    uid = smh_env
    now = datetime.now(timezone.utc)
    _insert_history(uid, "agg_count", 0.4, now)
    _insert_history(uid, "group_by", 0.6, now + timedelta(minutes=1))

    app = create_app()
    async with _client(app) as client:
        resp = await client.get(
            "/mastery-history",
            params={"concept": "group_by"},
            headers=auth_header(uid),
        )

    assert resp.status_code == 200, resp.text
    points = resp.json()
    assert len(points) == 1
    assert points[0]["concept"] == "group_by"
    assert points[0]["p_l"] == pytest.approx(0.6)


@pytest.mark.asyncio
async def test_endpoint_unknown_user_401():
    """Semantika 4.0b.2: user iz tokena. Token za nepostojećeg usera → 401
    invalid_token, NE 404 (helper više ne provjerava postojanje)."""
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/mastery-history", headers=auth_header(999999999))
    assert resp.status_code == 401
    assert resp.json()["detail"] == "invalid_token"


@pytest.mark.asyncio
async def test_endpoint_empty_history_is_200(smh_env):
    uid = smh_env
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/mastery-history", headers=auth_header(uid))
    assert resp.status_code == 200
    assert resp.json() == []


# Sanity: nema orphan history redova nakon suite (smh_env teardown radi)
def test_no_orphan_history_after_module():
    with SessionLocal() as s:
        # ne tvrdimo globalno 0 (drugi testovi mogu teći), samo da naš user prefix nestane
        leftover = s.scalar(
            select(func.count())
            .select_from(SkillMasteryHistory)
            .join(User, User.id == SkillMasteryHistory.user_id)
            .where(User.username == "smh_user_3a31")
        )
    assert leftover == 0
