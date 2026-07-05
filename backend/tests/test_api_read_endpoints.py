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
from sqlalchemy import select

from app.db.models import Concept, TaskConcept
from app.db.session import SessionLocal
from app.main import create_app


@asynccontextmanager
async def _client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


# ---------------------------------------------------------------------------
# GET /task/{task_id}
# ---------------------------------------------------------------------------


def _find_task_with_concepts() -> tuple[int, list[tuple[str, str, bool]]]:
    """Vrati (task_id, [(code, name, is_primary), ...]) za neki seedani task s konceptima.

    Ne hardkodiramo id — biramo dinamički prvi task koji ima bar jedan task_concepts red.
    """
    with SessionLocal() as s:
        task_id = s.scalar(select(TaskConcept.task_id).limit(1))
        assert task_id is not None, "task_concepts mora biti popunjen (faza 3.0 import)"
        concepts = s.execute(
            select(Concept.code, Concept.name, TaskConcept.is_primary)
            .join(TaskConcept, TaskConcept.concept_id == Concept.id)
            .where(TaskConcept.task_id == task_id)
        ).all()
        return task_id, [(c, n, p) for c, n, p in concepts]


@pytest.mark.asyncio
async def test_get_task_detail_returns_fields():
    task_id, concepts = _find_task_with_concepts()
    expected_codes = {c for c, _, _ in concepts}

    app = create_app()  # bez agenata — čisti DB read
    async with _client(app) as client:
        resp = await client.get(f"/task/{task_id}")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == task_id
    assert isinstance(body["title"], str) and body["title"]
    assert isinstance(body["description"], str)
    assert isinstance(body["difficulty"], int)
    assert "estimated_time_sec" in body  # smije biti null
    assert isinstance(body["module_id"], int)

    returned_codes = {c["code"] for c in body["concepts"]}
    assert returned_codes == expected_codes
    for c in body["concepts"]:
        assert set(c.keys()) == {"code", "name", "is_primary"}

    # sortiranje: primarni prvi, pa po code
    flags_then_codes = [(not c["is_primary"], c["code"]) for c in body["concepts"]]
    assert flags_then_codes == sorted(flags_then_codes)


@pytest.mark.asyncio
async def test_get_task_detail_leaks_no_solution():
    """KRITIČNO: /task/{id} NE SMIJE izložiti rješenje ni sandbox schemu."""
    task_id, _ = _find_task_with_concepts()

    app = create_app()
    async with _client(app) as client:
        resp = await client.get(f"/task/{task_id}")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    # ni u strukturi ni u sirovom tijelu
    for forbidden in ("expected_query", "expected_result", "sandbox_schema"):
        assert forbidden not in body
        assert forbidden not in resp.text


@pytest.mark.asyncio
async def test_get_task_detail_404():
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/task/999999999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "task_not_found"


# ---------------------------------------------------------------------------
# GET /modules
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_modules_structure_and_counts():
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/modules")

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
            }

    # poznati prereq brid: from_clause ima select_basic kao preduvjet (po code-u)
    from_clause = next(
        (c for m in modules for c in m["concepts"] if c["code"] == "from_clause"), None
    )
    assert from_clause is not None, "koncept from_clause mora biti u seedu"
    assert "select_basic" in from_clause["prerequisites"]


@pytest.mark.asyncio
async def test_get_modules_matches_db_counts():
    from app.db.models import Module

    with SessionLocal() as s:
        n_modules_db = len(s.execute(select(Module.id)).all())
        n_concepts_db = len(s.execute(select(Concept.id)).all())

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/modules")
    modules = resp.json()

    assert len(modules) == n_modules_db
    n_concepts_api = sum(len(m["concepts"]) for m in modules)
    assert n_concepts_api == n_concepts_db


# ---------------------------------------------------------------------------
# GET /badges
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_badges_catalog():
    from app.db.models import Badge

    with SessionLocal() as s:
        n_badges = len(s.execute(select(Badge.id)).all())

    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/badges")

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
