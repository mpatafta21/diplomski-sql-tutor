"""Dijeljene DB query pomoćne funkcije za SPADE agente.

Čiste read funkcije bez side-effecta — sigurno pozivati iz bilo kojeg agenta.
Dijele ih 3B (SkillMastery upsert), 3C (filtriranje taskova), 3D (po potrebi).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Concept, Module, SkillMastery

#: 🔴 KANONSKI REDOSLIJED KONCEPATA — pedagoški slijed: modul po modulu, unutar
#: modula po `order_index`, `concepts.id` kao obrambeni razrješitelj.
#:
#: NIJE kozmetika. `build_mastery_snapshot` gradi dict OVIM redoslijedom,
#: `PrologEngine.inject_mastery` asertira `mastery/3` činjenice redoslijedom tog
#: dicta, a `recommend_next/2` reže prvim rješenjem (`!`). Bez `ORDER BY` taj
#: redoslijed je FIZIČKI POREDAK REDAKA U HEAPU, koji `run_seed()` prepisuje pri
#: svakom bootu (`make db-seed` → `on_conflict_do_update`) — pa se preporuka
#: mijenja bez ijedne izmjene koda. V. `docs/errata.md` #60.
#:
#: Par `(modules.order_index, concepts.order_index)` je izmjereno JEDINSTVEN nad
#: svih 30 koncepata (0 sudara), pa `Concept.id` nikad ne odlučuje — stoji da
#: redoslijed ostane totalan i ako se doda koncept koji sudari.
_KANONSKI_POREDAK = (Module.order_index, Concept.order_index, Concept.id)


def load_concept_code_map(session: Session) -> dict[str, int]:
    """Vrati {concept_code: concept_id} za sve koncepte, u KANONSKOM redoslijedu.

    🔴 Redoslijed je dio ugovora, ne slučajnost — v. `_KANONSKI_POREDAK`.
    Pozivatelj koji ga ne treba ništa ne gubi; pozivatelj koji ga treba
    (`build_mastery_snapshot`) bez njega tiho postaje nedeterminističan.
    """
    rows = session.execute(
        select(Concept.code, Concept.id)
        .join(Module, Module.id == Concept.module_id)
        .order_by(*_KANONSKI_POREDAK)
    ).all()
    return {r.code: r.id for r in rows}


def load_concept_id_map(session: Session) -> dict[int, str]:
    """Vrati {concept_id: concept_code} za sve koncepte, u KANONSKOM redoslijedu."""
    rows = session.execute(
        select(Concept.id, Concept.code)
        .join(Module, Module.id == Concept.module_id)
        .order_by(*_KANONSKI_POREDAK)
    ).all()
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
