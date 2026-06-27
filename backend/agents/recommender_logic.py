"""Recommend logika za RecommenderAgent — čist modul bez SPADE ovisnosti (3C.1).

Kombinira Prolog ZPD preporuku (prereqs + mastery) s BKT mastery snapshotom i
selekcijom konkretnog zadatka. SPADE omotač, asyncio.Lock i inform Coordinatoru
dolaze u 3C.2; ova logika je sinkrona i jedinično testabilna.

Tok recommend():
  1. odredi kategorije sub-floora (DB-izvedeno)
  2. izgradi mastery snapshot svih 30 koncepata (tier-točan prior + skill_mastery)
  3. inject → recommend_next → clear  (pozivatelj u 3C.2 omota u to_thread + Lock)
  4. mapiraj preporučeni koncept u konkretan task (izbjegni već riješene)

Sub-floor strategija — DVIJE kategorije s RAZLIČITIM tretmanom:

  Kat. A — TRANSVERZALNI (modul 0, 0 aktivnih primary taskova; npr. column_alias,
    join_condition). To su strukturni prerequisite-čvorovi koji po dizajnu nemaju
    zadatke. Tretman: PROZIRAN — p_l = 0.99 SAMO ako su svi all_prereqs već
    mastered u snapshotu, inače 0.0. Tako readiness teče kroz njih tek kad su im
    vlastiti prereqs gotovi (sprječava lažno otključavanje nizvodnih koncepata
    novaku — npr. inner_join čiji je jedini prereq join_condition).

  Kat. B — SUBFLOOR (modul != 0, < 2 aktivna primary taska; npr. insert,
    right_join). Pod-resursirani realni koncepti. Tretman: MASK kao mastered
    (0.99) da ih Prolog preskoči kroz vlastite klauzule i ne preporuči ih (premalo
    zadataka za vježbu). Sigurno jer nisu kritični prereqs (provjereno testom).

Redoslijed je bitan: prior → skill_mastery → subfloor → transverzalni (zadnji,
jer ovisi o mastery ostalih koncepata u snapshotu).

recommend() UVIJEK vraća dict (nikad goli None) jer reason ne smije biti izgubljen:
  - zdravo:           {"task_id": int,  "concept": str,  "reason": <prolog reason>}
  - iscrpljen:        {"task_id": None, "concept": str,  "reason": "exhausted"}
  - nema preporuke:   {"task_id": None, "concept": None, "reason": "no_recommendation"}
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agents.db_helpers import load_concept_code_map, load_concept_id_map
from app.db.models import Attempt, Concept, Module, SkillMastery, Task, TaskConcept
from bkt.parameters import create_bkt_for_concept

if TYPE_CHECKING:
    from app.prolog.prolog_engine import PrologEngine

_log = logging.getLogger(__name__)

# Mora se poklapati s rules.pl mastery_threshold(0.85).
_MASTERED_THRESHOLD = 0.85
_MASK_VALUE = 0.99  # "mastered" — Prolog preskoči koncept kroz vlastite klauzule
_BLOCK_VALUE = 0.0  # transverzalni bez gotovih prereqs — blokira nizvodno


# ---------------------------------------------------------------------------
# Kategorizacija koncepata (DB-izvedeno, bez hardkodiranih imena)
# ---------------------------------------------------------------------------


def _concept_task_stats(session: Session) -> dict[str, tuple[int, int]]:
    """Vrati {code: (module_number, broj_aktivnih_primary_taskova)} za sve koncepte.

    LEFT JOIN s uvjetima u ON-klauzuli kako bi koncepti bez taskova dali count 0.
    """
    rows = session.execute(
        select(Concept.code, Module.number, func.count(Task.id))
        .select_from(Concept)
        .join(Module, Module.id == Concept.module_id)
        .outerjoin(
            TaskConcept,
            (TaskConcept.concept_id == Concept.id) & (TaskConcept.is_primary.is_(True)),
        )
        .outerjoin(
            Task,
            (Task.id == TaskConcept.task_id) & (Task.is_active.is_(True)),
        )
        .group_by(Concept.code, Module.number)
    ).all()
    return {code: (module_number, count) for code, module_number, count in rows}


def transversal_concepts(session: Session) -> set[str]:
    """Kat. A: koncepti modula 0 BEZ ijednog aktivnog primary taska (strukturni glue).

    Npr. column_alias, join_condition. null_handling je modul 0 ALI ima taskove →
    NIJE ovdje (tretira se kao normalan koncept).
    """
    return {
        code
        for code, (module_number, count) in _concept_task_stats(session).items()
        if module_number == 0 and count == 0
    }


def subfloor_concepts(session: Session) -> set[str]:
    """Kat. B: koncepti modula != 0 s < 2 aktivna primary taska (pod-resursirani).

    Npr. insert, right_join. Maskiraju se kao mastered da ih Prolog ne preporuči.
    """
    return {
        code
        for code, (module_number, count) in _concept_task_stats(session).items()
        if module_number != 0 and count < 2
    }


# ---------------------------------------------------------------------------
# Mastery snapshot
# ---------------------------------------------------------------------------


def build_mastery_snapshot(
    session: Session,
    engine: "PrologEngine",
    user_id: int,
    transversal: set[str],
    subfloor: set[str],
) -> dict[str, float]:
    """Izgradi {concept_code: p_l} za SVIH 30 koncepata za injekciju u Prolog.

    Koraci (redoslijed bitan):
      1. tier-točan prior za svih 30 (create_bkt_for_concept → Prolog tier)
      2. overwrite diranima iz skill_mastery (stvarni p_l)
      3. subfloor (kat. B) → 0.99 (ravna maska)
      4. transverzalni (kat. A) → 0.99 ako su svi all_prereqs mastered, inače 0.0
    """
    code_map = load_concept_code_map(session)  # code -> id
    id_map = load_concept_id_map(session)  # id -> code

    # 1. tier-točan prior za svih 30
    snapshot: dict[str, float] = {
        code: create_bkt_for_concept(code, engine).p_l for code in code_map
    }

    # 2. overwrite diranima iz skill_mastery
    rows = session.execute(
        select(SkillMastery).where(SkillMastery.user_id == user_id)
    ).scalars()
    for row in rows:
        code = id_map.get(row.concept_id)
        if code is not None:
            snapshot[code] = row.p_l

    # 3. subfloor → ravna maska (mastered, ne preporučuj)
    for code in subfloor:
        snapshot[code] = _MASK_VALUE

    # 4. transverzalni → prozirni (ovisi o mastery ostalih, zato zadnji)
    for code in transversal:
        prereqs = engine.all_prereqs(code)
        if all(snapshot.get(p, 0.0) >= _MASTERED_THRESHOLD for p in prereqs):
            snapshot[code] = _MASK_VALUE
        else:
            snapshot[code] = _BLOCK_VALUE

    return snapshot


# ---------------------------------------------------------------------------
# Task selekcija
# ---------------------------------------------------------------------------


def solved_task_ids(session: Session, user_id: int) -> set[int]:
    """Skup task_id-eva koje je korisnik točno riješio (is_correct=true)."""
    return set(
        session.execute(
            select(Attempt.task_id)
            .where(Attempt.user_id == user_id, Attempt.is_correct.is_(True))
            .distinct()
        ).scalars()
    )


def select_task_for_concept(
    session: Session, user_id: int, concept_code: str
) -> int | None:
    """Najlakši aktivni primary task koncepta koji korisnik još NIJE riješio.

    Vraća None ako koncept nema (nerješenih) aktivnih primary taskova.
    """
    concept_id = load_concept_code_map(session).get(concept_code)
    if concept_id is None:
        return None

    solved = solved_task_ids(session, user_id)
    candidate_ids = session.execute(
        select(Task.id)
        .join(TaskConcept, TaskConcept.task_id == Task.id)
        .where(
            TaskConcept.concept_id == concept_id,
            TaskConcept.is_primary.is_(True),
            Task.is_active.is_(True),
        )
        .order_by(Task.difficulty.asc(), Task.id.asc())
    ).scalars()

    for task_id in candidate_ids:
        if task_id not in solved:
            return task_id
    return None


# ---------------------------------------------------------------------------
# Orkestracija
# ---------------------------------------------------------------------------


def recommend(session: Session, engine: "PrologEngine", user_id: int) -> dict:
    """Preporuči sljedeći task za korisnika (Prolog ZPD + BKT + task selekcija).

    Sinkroni Prolog dio (inject → recommend_next → clear) pozivatelj u 3C.2 omota
    u asyncio.to_thread + asyncio.Lock (pyswip je jedan globalni sync VM).
    """
    transversal = transversal_concepts(session)
    subfloor = subfloor_concepts(session)
    snapshot = build_mastery_snapshot(session, engine, user_id, transversal, subfloor)

    uid = str(user_id)
    engine.inject_mastery(uid, snapshot)
    try:
        rec = engine.recommend_next(uid)
    finally:
        # Počisti mastery fakte da ne cure u dijeljeni VM (cross-user leak).
        engine.clear_mastery(uid)

    if rec is None:
        return {"task_id": None, "concept": None, "reason": "no_recommendation"}

    concept, reason = rec
    task_id = select_task_for_concept(session, user_id, concept)
    if task_id is None:
        return {"task_id": None, "concept": concept, "reason": "exhausted"}

    return {"task_id": task_id, "concept": concept, "reason": reason}
