"""Idempotentna seed skripta.

Pokreni:
    cd backend && uv run python -m app.db.seed

Ponovno pokretanje ne mijenja broj redaka; UPDATE-a samo deskriptivna
polja (name, description, tier, order_index) ako su se promijenila u seed_data.py.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import Badge, Concept, ConceptPrerequisite, Module
from app.db.seed_data import BADGES, CONCEPTS, MODULES, PREREQUISITES
from app.db.session import SessionLocal

logger = logging.getLogger("seed")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def seed_modules(session: Session) -> dict[int, int]:
    """Upsert modula. Vraća mapu module_number -> module_id."""
    stmt = insert(Module).values(MODULES)
    stmt = stmt.on_conflict_do_update(
        index_elements=["number"],
        set_={
            "name": stmt.excluded.name,
            "description": stmt.excluded.description,
            "difficulty": stmt.excluded.difficulty,
            "order_index": stmt.excluded.order_index,
        },
    )
    session.execute(stmt)
    session.flush()

    rows = session.execute(select(Module.number, Module.id)).all()
    return {number: id_ for number, id_ in rows}


def seed_concepts(session: Session, module_map: dict[int, int]) -> dict[str, int]:
    """Upsert koncepata. Vraća mapu concept_code -> concept_id."""
    payload = [
        {
            "code": c["code"],
            "name": c["name"],
            "module_id": module_map[c["module_number"]],
            "tier": c["tier"],
            "description": c["description"],
            "order_index": c["order_index"],
        }
        for c in CONCEPTS
    ]
    stmt = insert(Concept).values(payload)
    stmt = stmt.on_conflict_do_update(
        index_elements=["code"],
        set_={
            "name": stmt.excluded.name,
            "module_id": stmt.excluded.module_id,
            "tier": stmt.excluded.tier,
            "description": stmt.excluded.description,
            "order_index": stmt.excluded.order_index,
        },
    )
    session.execute(stmt)
    session.flush()

    rows = session.execute(select(Concept.code, Concept.id)).all()
    return {code: id_ for code, id_ in rows}


def seed_prerequisites(session: Session, concept_map: dict[str, int]) -> None:
    """Upsert prerequisite rubova. ON CONFLICT DO NOTHING jer PK pokriva sve."""
    payload = [
        {
            "concept_id": concept_map[concept_code],
            "prerequisite_id": concept_map[prereq_code],
        }
        for concept_code, prereq_code in PREREQUISITES
    ]
    stmt = insert(ConceptPrerequisite).values(payload)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["concept_id", "prerequisite_id"]
    )
    session.execute(stmt)


def seed_badges(session: Session) -> None:
    stmt = insert(Badge).values(BADGES)
    stmt = stmt.on_conflict_do_update(
        index_elements=["code"],
        set_={
            "name": stmt.excluded.name,
            "description": stmt.excluded.description,
            "icon": stmt.excluded.icon,
            "rule": stmt.excluded.rule,
            "xp_reward": stmt.excluded.xp_reward,
        },
    )
    session.execute(stmt)


def run_seed() -> None:
    with SessionLocal() as session:
        module_map = seed_modules(session)
        logger.info("Modula u bazi: %d", len(module_map))

        concept_map = seed_concepts(session, module_map)
        logger.info("Koncepata u bazi: %d", len(concept_map))

        seed_prerequisites(session, concept_map)
        logger.info("Prerequisite rubova upisano: %d", len(PREREQUISITES))

        seed_badges(session)
        logger.info("Bedževa u bazi: %d", len(BADGES))

        session.commit()
    logger.info("Seed dovršen.")


if __name__ == "__main__":
    run_seed()
