"""Dijeljene DB query pomoćne funkcije za SPADE agente.

Čiste read funkcije bez side-effecta — sigurno pozivati iz bilo kojeg agenta.
Dijele ih 3B (SkillMastery upsert), 3C (filtriranje taskova), 3D (po potrebi).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Concept, SkillMastery


def load_concept_code_map(session: Session) -> dict[str, int]:
    """Vrati {concept_code: concept_id} za sve koncepte u bazi."""
    rows = session.execute(select(Concept.code, Concept.id)).all()
    return {r.code: r.id for r in rows}


def load_concept_id_map(session: Session) -> dict[int, str]:
    """Vrati {concept_id: concept_code} za sve koncepte u bazi."""
    rows = session.execute(select(Concept.id, Concept.code)).all()
    return {r.id: r.code for r in rows}


def load_mastery_snapshot(session: Session, user_id: int) -> dict[str, float]:
    """Sirovi skill_mastery snapshot {concept_code: p_l} — SAMO dirani koncepti.

    NAMJERNO različito od recommender_logic.build_mastery_snapshot:
      - bez PrologEngine/tier-priora (badge-eval je Opcija A, izvan VM-a)
      - bez subfloor maske 0.99 (maska je ispravna za ZPD-preporuku, ali bi
        OVDJE lažno proglasila right_join/insert savladanima → lažni bedževi)

    Nedirani koncepti se izostavljaju: njihovi tier-priori (0.05–0.15) su < 0.85
    (MASTERY_THRESHOLD), pa ne mijenjaju mastered skup. Ako se tier-prior ikad
    digne >= 0.85, ovo treba revidirati.
    """
    rows = session.execute(
        select(Concept.code, SkillMastery.p_l)
        .join(SkillMastery, SkillMastery.concept_id == Concept.id)
        .where(SkillMastery.user_id == user_id)
    ).all()
    return {code: p_l for code, p_l in rows}
