"""Test: dvostruko pokretanje seed skripte ne mijenja broj redaka."""

from __future__ import annotations

from sqlalchemy import func, select

from app.db.models import Badge, Concept, ConceptPrerequisite, Module
from app.db.seed import run_seed
from app.db.session import SessionLocal


def _counts() -> dict[str, int]:
    with SessionLocal() as s:
        return {
            "modules": s.scalar(select(func.count()).select_from(Module)),
            "concepts": s.scalar(select(func.count()).select_from(Concept)),
            "prereqs": s.scalar(select(func.count()).select_from(ConceptPrerequisite)),
            "badges": s.scalar(select(func.count()).select_from(Badge)),
        }


def test_seed_is_idempotent() -> None:
    # Prvi run (može biti prvi put, ili restart nakon prethodnog seed-a).
    run_seed()
    first = _counts()

    # Drugi run — ne smije duplicirati ništa.
    run_seed()
    second = _counts()

    assert first == second, f"Seed nije idempotentan: {first} != {second}"
    assert second == {"modules": 7, "concepts": 30, "prereqs": 38, "badges": 5}


def test_concept_codes_are_canonical() -> None:
    """Verificira da seed upiše sve 30 očekivanih code-ova."""
    from app.db.seed_data import CONCEPTS

    expected = {c["code"] for c in CONCEPTS}
    with SessionLocal() as s:
        got = {row for row, in s.execute(select(Concept.code)).all()}
    assert got == expected
