"""Dijeljene DB query pomoćne funkcije za SPADE agente.

Čiste read funkcije bez side-effecta — sigurno pozivati iz bilo kojeg agenta.
Dijele ih 3B (SkillMastery upsert), 3C (filtriranje taskova), 3D (po potrebi).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Concept


def load_concept_code_map(session: Session) -> dict[str, int]:
    """Vrati {concept_code: concept_id} za sve koncepte u bazi."""
    rows = session.execute(select(Concept.code, Concept.id)).all()
    return {r.code: r.id for r in rows}


def load_concept_id_map(session: Session) -> dict[int, str]:
    """Vrati {concept_id: concept_code} za sve koncepte u bazi."""
    rows = session.execute(select(Concept.id, Concept.code)).all()
    return {r.id: r.code for r in rows}
