"""Integracijski testovi `GET /task-for-concept/{code}` — fix „koncept → zadatak".

Ruta postoji jer je `entry_task_id` u `/modules` STATIČAN (bez korisničkog
konteksta), pa je klik na koncept vodio na već riješen zadatak. Ovdje se riješeni
preskaču kroz `resolve_task_for_concept` — jedini kod koji zna što je student
riješio.

Test-pristup po uzoru na test_api_read_endpoints.py: čisti DB read (bez agenata),
create_app() + ASGITransport. Attempti se seedaju i brišu u fixtureu jer ruta čita
kroz vlastitu SessionLocal i vidi samo COMMITANE podatke.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
import pytest
from sqlalchemy import delete, select

from agents.evaluation import UNSUPPORTED_CONCEPTS
from app.db.models import Attempt, Concept, Task, TaskConcept, User
from app.db.session import SessionLocal
from app.main import create_app
from tests.conftest import auth_header


@asynccontextmanager
async def _client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
def student():
    """Committed student; teardown briše attempte pa usera (FK red)."""
    with SessionLocal() as s:
        u = User(
            username="tfc_student",
            email="tfc_student@test.example",
            password_hash="dummy_hash_tfc",
        )
        s.add(u)
        s.commit()
        uid = u.id
    yield uid
    with SessionLocal() as s:
        s.execute(delete(Attempt).where(Attempt.user_id == uid))
        s.execute(delete(User).where(User.id == uid))
        s.commit()


def _primary_task_ids(code: str) -> list[int]:
    """Aktivni primary zadaci koncepta, poretkom koji ruta koristi."""
    with SessionLocal() as s:
        cid = s.scalar(select(Concept.id).where(Concept.code == code))
        return list(
            s.execute(
                select(Task.id)
                .join(TaskConcept, TaskConcept.task_id == Task.id)
                .where(
                    TaskConcept.concept_id == cid,
                    TaskConcept.is_primary.is_(True),
                    Task.is_active.is_(True),
                )
                .order_by(Task.difficulty, Task.id)
            ).scalars()
        )


def _concept_with_at_least(n: int) -> str:
    """Koncept s >= n aktivnih primary zadataka (ne hardkodira se ime)."""
    for code in ("select_basic", "where_filter", "inner_join", "order_by"):
        if len(_primary_task_ids(code)) >= n:
            return code
    pytest.skip(f"nema koncepta s >= {n} aktivnih primary zadataka")


def _mark_solved(user_id: int, task_ids: list[int]) -> None:
    with SessionLocal() as s:
        for i, tid in enumerate(task_ids, start=1):
            s.add(
                Attempt(
                    user_id=user_id,
                    task_id=tid,
                    submitted_query="SELECT 1",
                    is_correct=True,
                    attempt_number=i,
                )
            )
        s.commit()


# ---------------------------------------------------------------------------
# Sretan put + jezgra popravka
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_easiest_task_for_fresh_user(student):
    code = _concept_with_at_least(1)
    expected = _primary_task_ids(code)[0]

    async with _client(create_app()) as c:
        r = await c.get(f"/task-for-concept/{code}", headers=auth_header(student))

    assert r.status_code == 200, r.text
    assert r.json() == {"task_id": expected, "concept": code, "repeat": False}


@pytest.mark.asyncio
async def test_skips_solved_task(student):
    """🔴 JEZGRA: riješen najlakši → ruta vraća SLJEDEĆI, ne isti.

    Ovo je kvar zbog kojeg ruta postoji: `entry_task_id` je ovdje vraćao prvi.
    """
    code = _concept_with_at_least(2)
    ids = _primary_task_ids(code)
    _mark_solved(student, [ids[0]])

    async with _client(create_app()) as c:
        r = await c.get(f"/task-for-concept/{code}", headers=auth_header(student))

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["task_id"] == ids[1], f"vratio riješen zadatak: {body}"
    assert body["repeat"] is False


@pytest.mark.asyncio
async def test_all_solved_returns_easiest_with_repeat_flag(student):
    """Svi riješeni → najlakši uz `repeat: true` (odluka: „za ponavljanje, bez XP-a").

    Zadatak se NE uskraćuje — Task ekran ga označava bedžom „Riješeno", a ponovna
    predaja ionako ne nosi XP (`already_solved`).
    """
    code = _concept_with_at_least(2)
    ids = _primary_task_ids(code)
    _mark_solved(student, ids)

    async with _client(create_app()) as c:
        r = await c.get(f"/task-for-concept/{code}", headers=auth_header(student))

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["repeat"] is True, f"nedostaje oznaka ponavljanja: {body}"
    assert body["task_id"] == ids[0], "za ponavljanje se nudi najlakši"


# ---------------------------------------------------------------------------
# Rubni slučajevi i obrana u dubinu
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_concept_404(student):
    async with _client(create_app()) as c:
        r = await c.get("/task-for-concept/nema_me", headers=auth_header(student))

    assert r.status_code == 404
    assert r.json()["detail"] == "concept_not_found"


@pytest.mark.asyncio
async def test_transversal_concept_has_no_tasks_404(student):
    """Transverzalni koncept (Kat. A) po dizajnu nema zadatke → jasan 404.

    Razlikuje se od `concept_not_found`: koncept POSTOJI, samo nije vježbiv.
    """
    async with _client(create_app()) as c:
        r = await c.get("/task-for-concept/join_condition", headers=auth_header(student))

    assert r.status_code == 404
    assert r.json()["detail"] == "concept_has_no_tasks"


@pytest.mark.asyncio
async def test_unsupported_concept_never_yields_task(student):
    """🔴 Kat. C (neevaluabilni) ne smije dati zadatak ni izravnim pozivom rute.

    Takav zadatak nikad ne može postati `is_correct` → 0 XP + BKT kazna po
    pokušaju (nalaz 4.4-0c B4). Guard je u `resolve_task_for_concept`.
    """
    async with _client(create_app()) as c:
        for code in sorted(UNSUPPORTED_CONCEPTS):
            r = await c.get(
                f"/task-for-concept/{code}", headers=auth_header(student)
            )
            assert r.status_code == 404, f"{code} je ponudio zadatak: {r.text}"


@pytest.mark.asyncio
async def test_requires_auth():
    """Isti guard kao /modules — bez tokena nema odgovora."""
    code = _concept_with_at_least(1)
    async with _client(create_app()) as c:
        r = await c.get(f"/task-for-concept/{code}")

    assert r.status_code == 401


@pytest.mark.asyncio
async def test_is_per_user(student):
    """Dva korisnika, isti koncept, različito riješeno → različit zadatak.

    Dokazuje da je odgovor user-aware, a ne katalog kao `entry_task_id`.
    """
    code = _concept_with_at_least(2)
    ids = _primary_task_ids(code)
    _mark_solved(student, [ids[0]])

    with SessionLocal() as s:
        other = User(
            username="tfc_other",
            email="tfc_other@test.example",
            password_hash="dummy_hash_tfc2",
        )
        s.add(other)
        s.commit()
        other_id = other.id

    try:
        async with _client(create_app()) as c:
            mine = await c.get(
                f"/task-for-concept/{code}", headers=auth_header(student)
            )
            theirs = await c.get(
                f"/task-for-concept/{code}", headers=auth_header(other_id)
            )
        assert mine.json()["task_id"] == ids[1]
        assert theirs.json()["task_id"] == ids[0]
    finally:
        with SessionLocal() as s:
            s.execute(delete(Attempt).where(Attempt.user_id == other_id))
            s.execute(delete(User).where(User.id == other_id))
            s.commit()
