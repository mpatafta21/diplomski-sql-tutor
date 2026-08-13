"""`POST /admin/hint-credit/reset` — admin vraća SVOJ kredit za savjete (Faza 5.2).

🔴 ZAŠTO SMIJE BRISATI: adminovi `hint_requests` redci NISU telemetrija. Admin je
po dizajnu izvan analize (`/leaderboard` ga izrijekom isključuje, „admin nije
natjecatelj"), pa njegovi redci nikad ne ulaze u evaluaciju. Za studenta isto
brisanje bilo bi uništavanje jedinog izvora o potrošnji savjeta i rupama u
katalogu — zato ruta briše **isključivo retke pozivatelja** i ne prima `user_id`.

🔴 ZAŠTO RESET, A NE „ADMIN BEZ OGRANIČENJA": neograničen admin nikad ne može
vidjeti `hint_rate_limited`, a to je jedno od sedam stanja koja rad dokumentira i
demonstrira se upravo na adminu. S resetom se limit može iscrpiti, pokazati, pa
vratiti.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import delete, select

from app.core import config
from app.db.models import Attempt, HintRequest, Task, User
from app.db.session import SessionLocal
from app.main import create_app
from tests.conftest import auth_header


@pytest.fixture
def reset_users():
    """Admin + student, oba sa svojim potrošenim savjetima."""
    with SessionLocal() as s:
        task_id = int(s.scalar(select(Task.id).order_by(Task.id).limit(1)))
        admin = User(
            username="reset_admin_52",
            email="reset-admin-52@test.example",
            password_hash="dummy_hash_52a",
            role="admin",
        )
        student = User(
            username="reset_student_52",
            email="reset-student-52@test.example",
            password_hash="dummy_hash_52s",
            role="student",
        )
        s.add_all([admin, student])
        s.commit()
        ids = {"admin": admin.id, "student": student.id, "task": task_id}

    yield ids

    with SessionLocal() as s:
        uids = [ids["admin"], ids["student"]]
        s.execute(delete(HintRequest).where(HintRequest.user_id.in_(uids)))
        s.execute(delete(Attempt).where(Attempt.user_id.in_(uids)))
        s.execute(delete(User).where(User.id.in_(uids)))
        s.commit()


def _spend(
    uid: int, task_id: int, *, n: int, source: str = "fallback", attempt: int = 1
) -> None:
    now = datetime.now(timezone.utc)
    with SessionLocal() as s:
        a = Attempt(
            user_id=uid,
            task_id=task_id,
            submitted_query="SELECT 1;",
            is_correct=False,
            error_type="row_mismatch",
            attempt_number=attempt,
        )
        s.add(a)
        s.flush()
        for i in range(n):
            s.add(
                HintRequest(
                    user_id=uid,
                    task_id=task_id,
                    after_attempt_id=a.id,
                    error_type="row_mismatch",
                    source=source,
                    hint_text=None if source == "unavailable" else f"tekst {i}",
                    created_at=now - timedelta(minutes=i + 1),
                )
            )
        s.commit()


def _rows(uid: int) -> list[HintRequest]:
    with SessionLocal() as s:
        return list(
            s.scalars(select(HintRequest).where(HintRequest.user_id == uid)).all()
        )


async def _call(uid: int, role: str) -> httpx.Response:
    app = create_app()  # bez stacka — čisti DB write, nula agenata
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        return await c.post(
            "/admin/hint-credit/reset", headers=auth_header(uid, role)
        )


@pytest.mark.asyncio
async def test_admin_resets_own_credit(reset_users, monkeypatch) -> None:
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    uid = reset_users["admin"]
    _spend(uid, reset_users["task"], n=config.HINT_MAX)

    r = await _call(uid, "admin")

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["remaining"] == config.HINT_MAX
    assert body["next_refill_at"] is None, "pun bucket nema što puniti"
    assert body["deleted"] == config.HINT_MAX
    assert _rows(uid) == []


@pytest.mark.asyncio
async def test_student_gets_403(reset_users, monkeypatch) -> None:
    """🔴 Reset je admin-only. Student koji ostane bez savjeta čeka nadopunu."""
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    uid = reset_users["student"]
    _spend(uid, reset_users["task"], n=2)

    r = await _call(uid, "student")

    assert r.status_code == 403
    assert r.json()["detail"] == "admin_required"
    assert len(_rows(uid)) == 2, "odbijen zahtjev ne smije obrisati ništa"


@pytest.mark.asyncio
async def test_reset_touches_only_the_caller(reset_users, monkeypatch) -> None:
    """🔴 Ruta ne prima `user_id` i ne smije dirati tuđe retke.

    Ovo je test protiv budućeg „malog proširenja": čim bi reset primio ciljanog
    korisnika, jedna kriva vrijednost obrisala bi evaluacijske podatke sudionika.
    """
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    admin, student = reset_users["admin"], reset_users["student"]
    _spend(admin, reset_users["task"], n=3)
    _spend(student, reset_users["task"], n=3)

    r = await _call(admin, "admin")

    assert r.status_code == 200
    assert _rows(admin) == []
    assert len(_rows(student)) == 3, "studentovi redci su NETAKNUTI"


@pytest.mark.asyncio
async def test_unavailable_rows_survive(reset_users, monkeypatch) -> None:
    """🔴 Briše se SAMO ono što troši kredit.

    `source='unavailable'` ne troši kredit (odluka C.1 plana 5.0) — taj redak
    mjeri rupu u katalogu hintova. Reset kredita nema razloga to brisati, pa
    najmanji mogući doseg brisanja i ovdje vrijedi.
    """
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    uid = reset_users["admin"]
    _spend(uid, reset_users["task"], n=2, source="fallback")
    _spend(uid, reset_users["task"], n=1, source="unavailable", attempt=2)

    r = await _call(uid, "admin")

    assert r.status_code == 200
    assert r.json()["deleted"] == 2
    preostali = _rows(uid)
    assert [x.source for x in preostali] == ["unavailable"]


@pytest.mark.asyncio
async def test_reset_agrees_with_profile(reset_users, monkeypatch) -> None:
    """🔴 Ista disciplina kao §B.4: brojka iz resetа == brojka iz `/profile`.

    Odgovor se ne smije računati vlastitom formulom — zove `hint_credit`, istu
    funkciju koju zovu `/hint` i `/profile`.
    """
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    uid = reset_users["admin"]
    _spend(uid, reset_users["task"], n=4)

    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.post(
            "/admin/hint-credit/reset", headers=auth_header(uid, "admin")
        )
        p = await c.get("/profile", headers=auth_header(uid, "admin"))

    assert r.status_code == 200 and p.status_code == 200
    assert r.json()["remaining"] == p.json()["remaining"] == config.HINT_MAX
    assert r.json()["next_refill_at"] == p.json()["next_refill_at"] is None
