"""Integracijski testovi user read endpointa — Faza 4.0a-2.

Pokriva: GET /attempts, GET /leaderboard (global + weekly).

Test-pristup: endpointi čitaju kroz vlastitu SessionLocal (vide samo COMMITANO), pa se
podaci pripremaju committano + eksplicitno brišu u teardownu (obrazac api_user iz
test_api.py). Rollback-fixture db_session NIJE vidljiv endpointu.

Redoslijed brisanja zbog FK: xp_log → attempts → users.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest
from sqlalchemy import delete, select

from app.db.models import Attempt, Task, User, XpLog
from app.db.session import SessionLocal
from app.main import create_app

# Reuse committed-attempt helper (piše Attempt + opc. XpLog, commita)
from tests.test_coordinator import _make_attempt  # noqa: E402

_ZAGREB = ZoneInfo("Europe/Zagreb")


@asynccontextmanager
async def _client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as c:
        yield c


@pytest.fixture
def make_user():
    """Tvornica committanih usera s determinističkim cleanupom (xp_log→attempts→users)."""
    created: list[int] = []

    def _make(username: str, *, xp: int = 0, level: int = 1) -> int:
        with SessionLocal() as s:
            u = User(
                username=username,
                email=f"{username}@test.example",
                password_hash="dummy_hash_402a2",
                xp=xp,
                level=level,
            )
            s.add(u)
            s.commit()
            uid = u.id
        created.append(uid)
        return uid

    yield _make

    with SessionLocal() as s:
        s.execute(delete(XpLog).where(XpLog.user_id.in_(created)))
        s.execute(delete(Attempt).where(Attempt.user_id.in_(created)))
        s.execute(delete(User).where(User.id.in_(created)))
        s.commit()


def _some_task() -> tuple[int, str]:
    with SessionLocal() as s:
        row = s.execute(select(Task.id, Task.title).limit(1)).first()
        assert row is not None, "tasks moraju biti seedani"
        return row[0], row[1]


def _insert_xplog(user_id: int, delta: int, created_at: datetime) -> None:
    """Ubaci XpLog s KONTROLIRANIM created_at (attempt_id je nullable)."""
    with SessionLocal() as s:
        s.add(
            XpLog(
                user_id=user_id,
                attempt_id=None,
                delta=delta,
                reason="test",
                created_at=created_at,
            )
        )
        s.commit()


# ===========================================================================
# GET /attempts
# ===========================================================================


@pytest.mark.asyncio
async def test_attempts_pagination_and_order(make_user):
    uid = make_user("att_order_402a2")
    task_id, task_title = _some_task()
    for n in (1, 2, 3):
        _make_attempt(uid, task_id, is_correct=True, error_type=None, attempt_number=n)

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/attempts", params={"user_id": uid, "limit": 2})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert len(body["items"]) == 2
    # created_at DESC → najnoviji (attempt_number 3) prvi
    assert [i["attempt_number"] for i in body["items"]] == [3, 2]
    assert body["items"][0]["task_id"] == task_id
    assert body["items"][0]["task_title"] == task_title


@pytest.mark.asyncio
async def test_attempts_offset_and_limit_clamp(make_user):
    uid = make_user("att_clamp_402a2")
    task_id, _ = _some_task()
    for n in (1, 2, 3):
        _make_attempt(uid, task_id, is_correct=True, error_type=None, attempt_number=n)

    app = create_app()
    async with _client(app) as client:
        # offset preskače najnoviji
        r_off = await client.get("/attempts", params={"user_id": uid, "offset": 1})
        # limit=500 → clamp na 100
        r_clamp = await client.get("/attempts", params={"user_id": uid, "limit": 500})

    off = r_off.json()
    assert off["offset"] == 1
    assert [i["attempt_number"] for i in off["items"]] == [2, 1]

    clamp = r_clamp.json()
    assert clamp["limit"] == 100  # clamp, ne 422
    assert clamp["total"] == 3


@pytest.mark.asyncio
async def test_attempts_empty_user_is_200(make_user):
    uid = make_user("att_empty_402a2")
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/attempts", params={"user_id": uid})
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_attempts_unknown_user_404():
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/attempts", params={"user_id": 999999999})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "user_not_found"


# ===========================================================================
# GET /leaderboard — global
# ===========================================================================


@pytest.mark.asyncio
async def test_leaderboard_global_order_and_rank(make_user):
    uid_hi = make_user("lb_hi_402a2", xp=30000, level=9)
    uid_mid = make_user("lb_mid_402a2", xp=20000, level=6)
    uid_lo = make_user("lb_lo_402a2", xp=10000, level=3)

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/leaderboard", params={"scope": "global", "limit": 3})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    items = body["items"]
    assert [i["username"] for i in items] == [
        "lb_hi_402a2",
        "lb_mid_402a2",
        "lb_lo_402a2",
    ]
    assert [i["rank"] for i in items] == [1, 2, 3]
    assert items[0]["xp"] == 30000
    assert items[0]["level"] == 9
    # sanity: nema unused var upozorenja
    assert {uid_hi, uid_mid, uid_lo}


@pytest.mark.asyncio
async def test_leaderboard_invalid_scope_422():
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/leaderboard", params={"scope": "banana"})
    assert resp.status_code == 422


# ===========================================================================
# GET /leaderboard — weekly
# ===========================================================================


@pytest.mark.asyncio
async def test_leaderboard_weekly_sum(make_user):
    uid_a = make_user("lb_wk_a_402a2", xp=999, level=2)
    uid_b = make_user("lb_wk_b_402a2", xp=1, level=5)
    now = datetime.now(_ZAGREB)
    inside = now - timedelta(days=1)
    _insert_xplog(uid_a, 10, inside)
    _insert_xplog(uid_a, 5, inside)
    _insert_xplog(uid_b, 20, inside)

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/leaderboard", params={"scope": "weekly"})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    items = body["items"]
    # B (20) ispred A (15); xp = weekly score, ne User.xp
    assert [i["username"] for i in items] == ["lb_wk_b_402a2", "lb_wk_a_402a2"]
    assert [i["xp"] for i in items] == [20, 15]
    assert [i["rank"] for i in items] == [1, 2]
    # level je TRENUTNI User.level, ne izveden
    assert items[0]["level"] == 5


@pytest.mark.asyncio
async def test_leaderboard_weekly_boundary(make_user):
    uid = make_user("lb_wk_bnd_402a2")
    cutoff = datetime.now(_ZAGREB) - timedelta(days=7)
    _insert_xplog(uid, 7, cutoff + timedelta(minutes=1))  # UNUTRA
    _insert_xplog(uid, 100, cutoff - timedelta(minutes=1))  # VANI

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/leaderboard", params={"scope": "weekly"})

    body = resp.json()
    mine = [i for i in body["items"] if i["username"] == "lb_wk_bnd_402a2"]
    assert len(mine) == 1
    assert mine[0]["xp"] == 7  # samo UNUTRA red, VANI (100) se ne broji


@pytest.mark.asyncio
async def test_leaderboard_weekly_empty(make_user):
    # user postoji ali BEZ ijedne delte u prozoru → ne pojavljuje se
    uid = make_user("lb_wk_none_402a2", xp=5000)
    old = datetime.now(_ZAGREB) - timedelta(days=30)
    _insert_xplog(uid, 42, old)

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/leaderboard", params={"scope": "weekly"})

    body = resp.json()
    assert all(i["username"] != "lb_wk_none_402a2" for i in body["items"])
