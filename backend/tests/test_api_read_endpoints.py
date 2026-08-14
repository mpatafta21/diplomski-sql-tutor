"""Integracijski testovi statičkih read endpointa — Faza 4.0a-1.

Pokriva: GET /task/{id}, GET /modules, GET /badges.

Test-pristup: READ-ONLY protiv seedanog `tutor_main` (moduli/koncepti/bedževi su
statični seed — vidi app/db/seed.py + app/db/seed_data.py; taskovi su importirani u
fazi 3.0). Endpoint čita kroz vlastitu SessionLocal pa vidi samo COMMITANE podatke —
zato se oslanjamo na već committane seed podatke, bez commit/cleanup fixtura.

Ove rute su ČISTI DB read (bez agenata) → koristi se samo create_app() + ASGITransport,
stack agenata se NE diže (isto kao test_get_profile_pure_db_read u test_api.py).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
import pytest
from sqlalchemy import delete, select

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
def student_auth():
    """Committed student → auth header (rute su sad gated; sadržaj usera nebitan)."""
    with SessionLocal() as s:
        u = User(
            username="read_ep_student_402b2",
            email="read_ep_student_402b2@test.example",
            password_hash="dummy_hash_402b2",
        )
        s.add(u)
        s.commit()
        uid = u.id
    yield auth_header(uid)
    with SessionLocal() as s:
        s.execute(delete(User).where(User.id == uid))
        s.commit()


# ---------------------------------------------------------------------------
# GET /task/{task_id}
# ---------------------------------------------------------------------------


def _find_task_with_concepts() -> tuple[int, list[tuple[str, str, bool]]]:
    """Vrati (task_id, [(code, name, is_primary), ...]) za neki seedani task s konceptima.

    Ne hardkodiramo id — biramo dinamički prvi AKTIVAN task s bar jednim
    task_concepts redom. `is_active` filtar je OBAVEZAN od 4.4-0f: neaktivni
    (M6) taskovi sada vraćaju 404, pa bi slučajan odabir takvog taska srušio
    testove detalja.
    """
    with SessionLocal() as s:
        task_id = s.scalar(
            select(TaskConcept.task_id)
            .join(Task, Task.id == TaskConcept.task_id)
            .where(Task.is_active.is_(True))
            .limit(1)
        )
        assert task_id is not None, "task_concepts mora biti popunjen (faza 3.0 import)"
        concepts = s.execute(
            select(Concept.code, Concept.name, TaskConcept.is_primary)
            .join(TaskConcept, TaskConcept.concept_id == Concept.id)
            .where(TaskConcept.task_id == task_id)
        ).all()
        return task_id, [(c, n, p) for c, n, p in concepts]


@pytest.mark.asyncio
async def test_get_task_detail_returns_fields(student_auth):
    task_id, concepts = _find_task_with_concepts()
    expected_codes = {c for c, _, _ in concepts}

    app = create_app()  # bez agenata — čisti DB read
    async with _client(app) as client:
        resp = await client.get(f"/task/{task_id}", headers=student_auth)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == task_id
    assert isinstance(body["title"], str) and body["title"]
    assert isinstance(body["description"], str)
    assert isinstance(body["difficulty"], int)
    assert "estimated_time_sec" in body  # smije biti null
    assert isinstance(body["module_id"], int)
    # Svjež student bez pokušaja → task nije riješen.
    assert body["solved"] is False

    returned_codes = {c["code"] for c in body["concepts"]}
    assert returned_codes == expected_codes
    for c in body["concepts"]:
        assert set(c.keys()) == {"code", "name", "is_primary"}

    # sortiranje: primarni prvi, pa po code
    flags_then_codes = [(not c["is_primary"], c["code"]) for c in body["concepts"]]
    assert flags_then_codes == sorted(flags_then_codes)


@pytest.mark.asyncio
async def test_get_task_detail_solved_flag_true_after_correct():
    """`solved` je True kad korisnik ima raniji točan pokušaj ovog taska
    (indikator „Riješeno"). Izvedeno iz attempts, per-korisnik."""
    task_id, _ = _find_task_with_concepts()
    with SessionLocal() as s:
        u = User(
            username="solved_flag_user",
            email="solved_flag_user@test.example",
            password_hash="dummy_solved",
        )
        s.add(u)
        s.commit()
        uid = u.id
        s.add(
            Attempt(
                user_id=uid,
                task_id=task_id,
                submitted_query="SELECT 1",
                is_correct=True,
                error_type=None,
                execution_time_ms=5,
                rows_returned=1,
                attempt_number=1,
            )
        )
        s.commit()

    try:
        app = create_app()
        async with _client(app) as client:
            resp = await client.get(f"/task/{task_id}", headers=auth_header(uid))
        assert resp.status_code == 200, resp.text
        assert resp.json()["solved"] is True
    finally:
        with SessionLocal() as s:
            s.execute(delete(Attempt).where(Attempt.user_id == uid))
            s.execute(delete(User).where(User.id == uid))
            s.commit()


@pytest.mark.asyncio
async def test_get_task_detail_leaks_no_solution(student_auth):
    """KRITIČNO: /task/{id} NE SMIJE izložiti rješenje ni sandbox schemu."""
    task_id, _ = _find_task_with_concepts()

    app = create_app()
    async with _client(app) as client:
        resp = await client.get(f"/task/{task_id}", headers=student_auth)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    # ni u strukturi ni u sirovom tijelu
    for forbidden in ("expected_query", "expected_result", "sandbox_schema"):
        assert forbidden not in body
        assert forbidden not in resp.text


@pytest.mark.asyncio
async def test_get_task_detail_404(student_auth):
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/task/999999999", headers=student_auth)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "task_not_found"


# ---------------------------------------------------------------------------
# GET /modules
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_modules_structure_and_counts(student_auth):
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/modules", headers=student_auth)

    assert resp.status_code == 200, resp.text
    modules = resp.json()
    assert isinstance(modules, list) and len(modules) >= 1

    # order_index uzlazno na razini modula
    order_indices = [m["order_index"] for m in modules]
    assert order_indices == sorted(order_indices)

    # svaki modul: koncepti sortirani po order_index
    for m in modules:
        assert set(m.keys()) == {
            "id",
            "number",
            "name",
            "description",
            "difficulty",
            "order_index",
            "concepts",
        }
        c_order = [c["order_index"] for c in m["concepts"]]
        assert c_order == sorted(c_order)
        for c in m["concepts"]:
            assert set(c.keys()) == {
                "id",
                "code",
                "name",
                "tier",
                "order_index",
                "prerequisites",
                "primary_task_count",
            }

    # poznati prereq brid: from_clause ima select_basic kao preduvjet (po code-u)
    from_clause = next(
        (c for m in modules for c in m["concepts"] if c["code"] == "from_clause"), None
    )
    assert from_clause is not None, "koncept from_clause mora biti u seedu"
    assert "select_basic" in from_clause["prerequisites"]


@pytest.mark.asyncio
async def test_get_modules_matches_db_counts(student_auth):
    from app.db.models import Module

    with SessionLocal() as s:
        n_modules_db = len(s.execute(select(Module.id)).all())
        n_concepts_db = len(s.execute(select(Concept.id)).all())

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/modules", headers=student_auth)
    modules = resp.json()

    assert len(modules) == n_modules_db
    n_concepts_api = sum(len(m["concepts"]) for m in modules)
    assert n_concepts_api == n_concepts_db


@pytest.mark.asyncio
async def test_get_modules_primary_task_count(student_auth):
    """primary_task_count (Faza 4.3 Stage 0, NALAZ #10) — broj AKTIVNIH PRIMARY
    taskova po konceptu, ista semantika kao recommender_logic._concept_task_stats
    (UI unlock logika mora moći zrcaliti Recommenderove kategorije: 0 / <2 / >=2)."""
    from sqlalchemy import func

    from app.db.models import Task

    # Ground truth istim LEFT JOIN-om kao recommender_logic._concept_task_stats.
    with SessionLocal() as s:
        rows = s.execute(
            select(Concept.code, func.count(Task.id))
            .select_from(Concept)
            .outerjoin(
                TaskConcept,
                (TaskConcept.concept_id == Concept.id)
                & (TaskConcept.is_primary.is_(True)),
            )
            .outerjoin(
                Task,
                (Task.id == TaskConcept.task_id) & (Task.is_active.is_(True)),
            )
            .group_by(Concept.code)
        ).all()
    expected_counts = dict(rows)

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/modules", headers=student_auth)

    assert resp.status_code == 200, resp.text
    api_counts = {
        c["code"]: c["primary_task_count"]
        for m in resp.json()
        for c in m["concepts"]
    }

    # Svi koncepti nose count i on odgovara DB ground truthu (non-null int >= 0).
    assert api_counts == expected_counts
    for count in api_counts.values():
        assert isinstance(count, int) and count >= 0

    # Sidra iz živog inventara (KORAK 0): transverzalni glue bez primary taskova
    # vs null_handling koji JE modul 0 ali IMA primary taskove (nije prozirni).
    assert api_counts["join_condition"] == 0
    assert api_counts["column_alias"] == 0
    assert api_counts["null_handling"] > 0


@pytest.mark.asyncio
async def test_get_modules_has_no_static_entry_task(student_auth):
    """🔴 `/modules` NE SMIJE vraćati konkretan `task_id` po konceptu.

    Do 2026-08-14 je vraćao `entry_task_id` — najlakši aktivni primary zadatak,
    statičan i jednak za svakoga. Klijent je na njega linkao, pa je klik na koncept
    vodio na VEĆ RIJEŠEN zadatak. Odredište sada bira `/task-for-concept/{code}`.

    Gate je širi od imena polja namjerno: bilo koji `*task_id*` u čvoru koncepta
    vratio bi isti kvar pod drugim imenom.

    Klikabilnost nosi `primary_task_count > 0` — ista maska (is_primary +
    is_active), pa je signal nepromijenjen.
    """
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/modules", headers=student_auth)

    assert resp.status_code == 200, resp.text
    concepts = {c["code"]: c for m in resp.json() for c in m["concepts"]}

    for code, c in concepts.items():
        assert not [k for k in c if "task_id" in k], (
            f"{code}: čvor koncepta opet nosi task_id ({list(c)})"
        )

    # Sidra za signal koji je preuzeo klikabilnost: glue bez zadataka → 0.
    assert concepts["join_condition"]["primary_task_count"] == 0
    assert concepts["column_alias"]["primary_task_count"] == 0
    assert concepts["null_handling"]["primary_task_count"] > 0


# ---------------------------------------------------------------------------
# GET /badges
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_badges_catalog(student_auth):
    from app.db.models import Badge

    with SessionLocal() as s:
        n_badges = len(s.execute(select(Badge.id)).all())

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/badges", headers=student_auth)

    assert resp.status_code == 200, resp.text
    badges = resp.json()
    assert isinstance(badges, list)
    assert len(badges) == n_badges

    # order by code
    codes = [b["code"] for b in badges]
    assert codes == sorted(codes)

    # shema: bez `rule`
    for b in badges:
        assert set(b.keys()) == {"code", "name", "description", "icon", "xp_reward"}
        assert "rule" not in b
    assert "rule" not in resp.text

    # poznat bedž
    fc = next((b for b in badges if b["code"] == "first_correct"), None)
    assert fc is not None
    assert fc["name"] == "Prvi uspjeh"
    assert fc["icon"] == "star"


# ---------------------------------------------------------------------------
# NEAKTIVAN task → 404 (NALAZ #19 dopuna, Faza 4.4-0f)
#
# Recommender neevaluabilne koncepte više ne nudi (Kat. C maska, 4.4-0d), ali je
# izravan URL ostao zadnji put do M6 taska: student je mogao otvoriti zadatak,
# predati rješenje i dobiti unsupported_eval → 0 XP + BKT kaznu koja curi i na
# evaluabilne sekundarne koncepte. Ključ je source_id, ne numerički id
# (NALAZ #21: SERIAL se mijenja pri svakom reseedu).
# ---------------------------------------------------------------------------

_INACTIVE_SOURCE_ID = "explain_plan_d3_60b9eaee"  # M6, is_active=False od 4.4-0e


@pytest.mark.asyncio
async def test_get_task_detail_inactive_returns_404(student_auth):
    """Neaktivan (M6) task se tretira kao nepostojeći."""
    with SessionLocal() as s:
        row = s.execute(
            select(Task.id, Task.is_active).where(
                Task.source_id == _INACTIVE_SOURCE_ID
            )
        ).first()
    assert row is not None, f"{_INACTIVE_SOURCE_ID} mora postojati u datasetu"
    task_id, is_active = row
    assert is_active is False, (
        f"preduvjet: {_INACTIVE_SOURCE_ID} mora biti neaktivan (NALAZ #19)"
    )

    app = create_app()
    async with _client(app) as client:
        resp = await client.get(f"/task/{task_id}", headers=student_auth)

    assert resp.status_code == 404, (
        "neaktivan task MORA biti 404 — inače je izravan URL zaobilaznica do "
        "neevaluabilnog zadatka"
    )
    assert resp.json()["detail"] == "task_not_found"


@pytest.mark.asyncio
async def test_get_task_detail_active_still_200(student_auth):
    """Regresija: aktivan task i dalje vraća 200 (guard ne lovi previše)."""
    task_id, _ = _find_task_with_concepts()
    app = create_app()
    async with _client(app) as client:
        resp = await client.get(f"/task/{task_id}", headers=student_auth)
    assert resp.status_code == 200, resp.text
