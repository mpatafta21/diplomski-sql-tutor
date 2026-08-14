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

  Kat. C — NEEVALUABILNI (agents.evaluation.UNSUPPORTED_CONCEPTS: explain_plan,
    index_usage). Evaluacijska jezgra ih ne zna ocijeniti (plan-presence put nije
    implementiran) → task tog koncepta NIKAD ne može postati is_correct → nikad
    "riješen" → recommender bi ga vraćao zauvijek, uz 0 XP i BKT kaznu po pokušaju
    (trajni ćorsokak, nalaz 4.4-0c B4). Tretman: ISTA maska kao Kat. B (0.99).
    NAPOMENA: subfloor ih NE hvata — explain_plan ima 2, index_usage 3 aktivna
    primary taska, a subfloor prag je < 2. Zato je potreban eksplicitan popis.

Redoslijed je bitan: prior → skill_mastery → subfloor → transverzalni (zadnji,
jer ovisi o mastery ostalih koncepata u snapshotu).

recommend() UVIJEK vraća dict (nikad goli None) jer reason ne smije biti izgubljen:
  - zdravo:           {"task_id": int,  "concept": str,  "reason": <prolog reason>}
  - iscrpljen:        {"task_id": None, "concept": str,  "reason": "exhausted"}
  - nema preporuke:   {"task_id": None, "concept": None, "reason": "no_recommendation"}
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agents.db_helpers import load_concept_code_map, load_concept_id_map
from agents.evaluation import UNSUPPORTED_CONCEPTS
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


def transversal_concepts(
    session: Session, stats: dict[str, tuple[int, int]] | None = None
) -> set[str]:
    """Kat. A: koncepti modula 0 BEZ ijednog aktivnog primary taska (strukturni glue).

    Npr. column_alias, join_condition. null_handling je modul 0 ALI ima taskove →
    NIJE ovdje (tretira se kao normalan koncept).

    `stats` je izlaz `_concept_task_stats` — proslijedi ga kad ista transakcija
    treba više kategorija, da se isti upit ne ponovi (v. `recommend`).
    """
    stats = _concept_task_stats(session) if stats is None else stats
    return {
        code
        for code, (module_number, count) in stats.items()
        if module_number == 0 and count == 0
    }


def concepts_with_tasks(
    session: Session,
    stats: dict[str, tuple[int, int]] | None = None,
    code_order: Iterable[str] | None = None,
) -> list[str]:
    """Koncepti s >= 1 aktivnim primary zadatkom — ulaz za `recommendable/1`.

    🔴 Definicija je „IMA zadatke", ne „ima NERIJEŠENE zadatke". Da je potonje,
    koncept čije je sve riješeno tiho bi nestao iz preporuka umjesto da vrati
    reason="exhausted" — a to je stanje koje sučelje mora moći prikazati
    (v. test_all_tasks_solved_gives_exhausted).

    🔴 Vraća LISTU u kanonskom poretku (`load_concept_code_map`), ne set. Poredak
    injektiranih fakata je ulaz u Prolog, ne detalj implementacije: set bi ovdje
    dao poredak ovisan o hashu, dakle promjenjiv između procesa — mehanizam
    ERRATE #60. `recommendable/1` je u rules.pl namjerno zadnji cilj pa ne
    nabraja, ali kanonski poredak je druga brana i ne košta ništa.

    Ne zamjenjuje maske Kat. B/C (0.99); te ostaju kakve jesu. Ovaj skup je
    obrana za Kat. A, koju maska po dizajnu ne pokriva.
    """
    stats = _concept_task_stats(session) if stats is None else stats
    order = load_concept_code_map(session) if code_order is None else code_order
    return [code for code in order if stats.get(code, (None, 0))[1] > 0]


def subfloor_concepts(
    session: Session, stats: dict[str, tuple[int, int]] | None = None
) -> set[str]:
    """Kat. B: koncepti modula != 0 s < 2 aktivna primary taska (pod-resursirani).

    Npr. insert, right_join. Maskiraju se kao mastered da ih Prolog ne preporuči.
    """
    stats = _concept_task_stats(session) if stats is None else stats
    return {
        code
        for code, (module_number, count) in stats.items()
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
    code_map: dict[str, int] | None = None,
) -> dict[str, float]:
    """Izgradi {concept_code: p_l} za SVIH 30 koncepata za injekciju u Prolog.

    Koraci (redoslijed bitan):
      1. tier-točan prior za svih 30 (create_bkt_for_concept → Prolog tier)
      2. overwrite diranima iz skill_mastery (stvarni p_l)
      3. subfloor (kat. B) → 0.99 (ravna maska)
      4. transverzalni (kat. A) → 0.99 ako su svi all_prereqs mastered, inače 0.0
    """
    # `code_map` se smije proslijediti kad ga pozivatelj već ima (recommend) —
    # isti upit inače ide dvaput po pozivu.
    if code_map is None:
        code_map = load_concept_code_map(session)  # code -> id, KANONSKI redoslijed
    id_map = load_concept_id_map(session)  # id -> code

    # 1. tier-točan prior za svih 30
    # 🔴 Redoslijed ovog dicta je ULAZ U PROLOG, ne detalj implementacije:
    # `inject_mastery` asertira činjenice ovim redom, a `recommend_next/2` reže
    # prvim rješenjem. Nasljeđuje se iz `load_concept_code_map` (kanonski
    # pedagoški slijed). Koraci 2–4 samo prepisuju VRIJEDNOSTI postojećih
    # ključeva, pa redoslijed ostaje netaknut. V. `docs/errata.md` #60.
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


def resolve_task_for_concept(
    session: Session, user_id: int, concept_code: str
) -> tuple[int | None, bool]:
    """Vrati `(task_id, repeat)` — zadatak koncepta za ovog korisnika.

    Tri ishoda koja pozivatelji moraju razlikovati:
      * `(id, False)` — najlakši NERIJEŠEN aktivan primary zadatak;
      * `(id, True)`  — svi su riješeni, vraćen najlakši **za ponavljanje**
        (Task ekran ga označava bedžom „Riješeno"; ponovna predaja ne nosi XP);
      * `(None, False)` — koncept nema nijedan aktivan primary zadatak.

    🔴 JEDINI izvor pravila „koncept → zadatak". `select_task_for_concept`
    delegira ovamo; dvije implementacije istog upita bile bi mehanizam N-8.
    """
    # Obrana u dubinu (Kat. C): neevaluabilan koncept NIKAD ne smije dati task —
    # ni ako ga netko zatraži izravno, zaobilazeći masku u recommend(). Takav
    # task ne može postati is_correct → nikad "riješen" → trajna petlja.
    if concept_code in UNSUPPORTED_CONCEPTS:
        return None, False

    concept_id = load_concept_code_map(session).get(concept_code)
    if concept_id is None:
        return None, False

    candidate_ids = list(
        session.execute(
            select(Task.id)
            .join(TaskConcept, TaskConcept.task_id == Task.id)
            .where(
                TaskConcept.concept_id == concept_id,
                TaskConcept.is_primary.is_(True),
                Task.is_active.is_(True),
            )
            .order_by(Task.difficulty.asc(), Task.id.asc())
        ).scalars()
    )
    if not candidate_ids:
        return None, False

    solved = solved_task_ids(session, user_id)
    for task_id in candidate_ids:
        if task_id not in solved:
            return task_id, False

    return candidate_ids[0], True


def select_task_for_concept(
    session: Session, user_id: int, concept_code: str
) -> int | None:
    """Najlakši aktivni primary task koncepta koji korisnik još NIJE riješio.

    Vraća None ako koncept nema (nerješenih) aktivnih primary taskova.

    🔴 „Sve riješeno" OSTAJE None — `recommend()` iz toga radi reason="exhausted",
    stanje koje sučelje mora moći prikazati. Zadatak za ponavljanje nudi samo
    izravni put kroz `resolve_task_for_concept` (klik na koncept), gdje ga je
    korisnik izrijekom zatražio.
    """
    task_id, repeat = resolve_task_for_concept(session, user_id, concept_code)
    return None if repeat else task_id


# ---------------------------------------------------------------------------
# Orkestracija
# ---------------------------------------------------------------------------


def recommend(session: Session, engine: "PrologEngine", user_id: int) -> dict:
    """Preporuči sljedeći task za korisnika (Prolog ZPD + BKT + task selekcija).

    Sinkroni Prolog dio (inject → recommend_next → clear) pozivatelj u 3C.2 omota
    u asyncio.to_thread + asyncio.Lock (pyswip je jedan globalni sync VM).
    """
    # Jedan upit za sve tri kategorije: bez ovoga se `_concept_task_stats` vrti
    # TRI puta po pozivu (izmjereno 1,43 ms svaki), a `load_concept_code_map`
    # dvaput. Zatečeno je bilo dvostruko; recommendable/1 bi bio treći.
    stats = _concept_task_stats(session)
    code_order = load_concept_code_map(session)
    transversal = transversal_concepts(session, stats)
    # Kat. B (subfloor) + Kat. C (NEEVALUABILNI) dijele ISTI tretman: maska 0.99
    # → Prolog ih ne preporučuje. Maskiranje je na razini KONCEPTA, ne taska:
    # filtriranje tek u select_task_for_concept dalo bi reason="exhausted"
    # (task_id=None) = tiši ćorsokak umjesto rješenja (4.4-0d KORAK 4).
    masked = subfloor_concepts(session, stats) | UNSUPPORTED_CONCEPTS
    snapshot = build_mastery_snapshot(
        session, engine, user_id, transversal, masked, code_order
    )

    # Kat. A se NE maskira nego se izbacuje iz KANDIDATA: p_l mora ostati 0.0 da
    # blokira nizvodne koncepte, a 0.0 ga ujedno čini `weak` pa je preticao prave
    # koncepte kroz klauzulu 1 i završavao kao "exhausted". recommendable/1 je
    # razdvajanje te dvije uloge — v. rules.pl.
    recommendable = concepts_with_tasks(session, stats, code_order)

    uid = str(user_id)
    engine.inject_recommendable(recommendable)
    engine.inject_mastery(uid, snapshot)
    try:
        rec = engine.recommend_next(uid)
    finally:
        # Počisti mastery fakte da ne cure u dijeljeni VM (cross-user leak).
        engine.clear_mastery(uid)
        # recommendable/1 je globalan; čisti se pod istom bravom pod kojom je i
        # ubačen (pozivatelj u 3C.2 drži prolog_lock preko cijelog recommend()).
        engine.clear_recommendable()

    if rec is None:
        return {"task_id": None, "concept": None, "reason": "no_recommendation"}

    concept, reason = rec
    task_id = select_task_for_concept(session, user_id, concept)
    if task_id is None:
        return {"task_id": None, "concept": concept, "reason": "exhausted"}

    return {"task_id": task_id, "concept": concept, "reason": reason}
