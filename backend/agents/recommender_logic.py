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

    🔴 NAPOMENA (ispravljena 2026-08-14): raniji tekst je tvrdio da ih „subfloor NE
    hvata jer explain_plan ima 2, a index_usage 3 aktivna primary taska". Izmjereno:
    OBA imaju 0 aktivnih — svih 5 M6 zadataka je namjerno deaktivirano, pa ih
    subfloor (< 2) trenutno hvata. Eksplicitan popis svejedno mora ostati: čim se
    M6 vrati u igru i count naraste iznad praga, subfloor ih ispušta, a
    neevaluabilni su i dalje. Popis je time obrana koja ne ovisi o sadržaju
    kataloga; brojke iz njega se NE citiraju jer se mijenjaju s aktivacijom.

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


def concepts_with_available_tasks(
    session: Session,
    user_id: int,
    code_order: Iterable[str] | None = None,
) -> list[str]:
    """Koncepti koji OVOM korisniku mogu dati zadatak — ulaz za `recommendable/1`.

    Definicija je „ima barem jedan aktivan primary zadatak koji korisnik NIJE
    riješio". Slabija definicija („ima zadatke", bez obzira na riješeno) ostavlja
    ćorsokak: koncept kojemu je sve riješeno, a mastery ispod praga, ostaje
    kandidat zauvijek, `select_task_for_concept` vrati None i student dobije
    „Nema novih zadataka" uz neriješene zadatke drugdje.

    🔴 Izmjereno na `admin` računu 2026-08-14: `where_filter` (3/3 riješena,
    p_l 0.7728) i `insert` (2/2, p_l 0.7702) su ga trajno zaglavljivali uz **71
    neriješen zadatak**. Prva izvedba ovog popravka koristila je slabiju
    definiciju i zatvorila samo ćorsokak Kat. A (koncept BEZ zadataka).

    🔴 Zato je predikat PO KORISNIKU, ne globalan iz kataloga. Injektira se i
    briše unutar iste kritične sekcije kao `mastery/3` (`prolog_lock`).

    🔴 Vraća LISTU u kanonskom poretku (`load_concept_code_map`). Poredak
    injektiranih fakata je ulaz u Prolog, ne detalj implementacije: set bi dao
    poredak ovisan o hashu, dakle promjenjiv između procesa — mehanizam
    ERRATE #60.

    Ne zamjenjuje maske Kat. B/C (0.99); te ostaju kakve jesu.
    """
    order = load_concept_code_map(session) if code_order is None else code_order

    # JEDAN upit: `select_task_for_concept` po konceptu bio bi 30 upita po pozivu
    # i pojeo bi cijeli dobitak iz `perf` commita.
    solved = select(Attempt.task_id).where(
        Attempt.user_id == user_id, Attempt.is_correct.is_(True)
    )
    available = set(
        session.execute(
            select(Concept.code)
            .join(TaskConcept, TaskConcept.concept_id == Concept.id)
            .join(Task, Task.id == TaskConcept.task_id)
            .where(
                TaskConcept.is_primary.is_(True),
                Task.is_active.is_(True),
                Task.id.not_in(solved),
            )
            .distinct()
        ).scalars()
    )
    # Kat. C nikad ne smije proći — guard u dubinu uz masku 0.99 i onaj u
    # `resolve_task_for_concept`; ne oslanja se na to da M6 nema aktivnih zadataka.
    return [c for c in order if c in available and c not in UNSUPPORTED_CONCEPTS]


def concepts_with_tasks(
    session: Session,
    stats: dict[str, tuple[int, int]] | None = None,
    code_order: Iterable[str] | None = None,
) -> list[str]:
    """Koncepti s >= 1 aktivnim primary zadatkom, bez obzira na riješeno.

    Širi skup od `concepts_with_available_tasks` i koristi se SAMO kao rezerva u
    `recommend()`: kad nijedan koncept nema neriješen zadatak unutar ZPD-a,
    ponavljanje riješenog je jedini put naprijed (v. `recommend`).
    """
    stats = _concept_task_stats(session) if stats is None else stats
    order = load_concept_code_map(session) if code_order is None else code_order
    return [
        c
        for c in order
        if stats.get(c, (None, 0))[1] > 0 and c not in UNSUPPORTED_CONCEPTS
    ]


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
    """Najlakši aktivni primary zadatak koncepta koji korisnik NIJE riješio.

    Vraća None ako koncept nema NERIJEŠENIH aktivnih primary zadataka — dakle i
    kad ih ima, ali su svi riješeni. Zadatak za ponavljanje nudi samo
    `resolve_task_for_concept`, kroz `repeat=True`.

    🔴 NEMA produkcijskih pozivatelja — `recommend()` i ruta zovu
    `resolve_task_for_concept` izravno. Zadržano jer je čitljiv izraz pravila
    „preskoči riješeno" i koristi ga suita. Tko mijenja politiku odabira,
    mijenja `resolve_task_for_concept`; izmjena OVDJE ne mijenja ponašanje
    sustava.

    🔴 Raniji docstring tvrdio je da `recommend()` iz ovog `None` radi
    reason="exhausted". To više nije istina (v. `recommend`) i uklonjeno je
    2026-08-14 — ali `None` ostaje, jer bi bez njega funkcija tiho vraćala
    riješen zadatak onima koji je zovu kao „daj neriješen".
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

    # Kandidat je koncept koji OVOM korisniku može dati zadatak. Pokriva oba
    # oblika ćorsokaka: Kat. A (koncept bez zadataka; p_l 0.0 mora ostati radi
    # blokade nizvodnog, a 0.0 ga je činila `weak` pa je pretjecao prave koncepte)
    # i "sve riješeno, mastery ispod praga" (vječni kandidat bez zadatka).
    recommendable = concepts_with_available_tasks(session, user_id, code_order)

    uid = str(user_id)

    def _ask(candidates: list[str]) -> tuple[str, str] | None:
        """Jedan Prolog krug s danim skupom kandidata. Uvijek čisti za sobom."""
        try:
            # 🔴 Injekcije su UNUTAR try: da stoje iznad njega, iznimka u drugoj
            # (npr. neispravan kod koncepta) ostavila bi fakte prve u dijeljenom
            # VM-u, a `finally` se ne bi izvršio. RecommendBehaviour hvata
            # Exception i nastavlja, pa bi zaprljani VM preživio zahtjev.
            engine.inject_recommendable(candidates)
            engine.inject_mastery(uid, snapshot)
            return engine.recommend_next(uid)
        finally:
            # Počisti da fakti ne cure u dijeljeni VM (cross-user leak). Oboje je
            # pod istom bravom (pozivatelj u 3C.2 drži prolog_lock preko cijelog
            # recommend()), a `recommendable/1` se briše globalnim retractallom.
            engine.clear_mastery(uid)
            engine.clear_recommendable()

    rec = _ask(recommendable)

    # 🔴 REZERVA. Ako nijedan koncept nema NERIJEŠEN zadatak unutar ZPD-a, to još
    # ne znači „sve savladano": tipičan slučaj je da je korijenski koncept
    # (`select_basic`) iscrpljen a nije savladan, pa `prereqs_met` blokira sve
    # nizvodno. Ondje je PONAVLJANJE riješenog jedini put naprijed — bez ove
    # grane vratili bismo `no_recommendation`, koji sučelje prikazuje kao
    # slavljeničko „Sve savladano" iako student ima neriješenih zadataka.
    # Drugi Prolog krug plaća se samo u tom rijetkom stanju.
    if rec is None:
        rec = _ask(concepts_with_tasks(session, stats, code_order))

    if rec is None:
        return {"task_id": None, "concept": None, "reason": "no_recommendation"}

    concept, reason = rec
    task_id, repeat = resolve_task_for_concept(session, user_id, concept)
    if task_id is None:
        return {"task_id": None, "concept": concept, "reason": "exhausted"}
    if repeat:
        # Zadatak je već riješen: nosi bedž „Riješeno" i ne donosi XP, ali diže
        # mastery kroz BKT — a to je jedino što otključava ostatak grafa.
        return {"task_id": task_id, "concept": concept, "reason": "repeat_practice"}

    return {"task_id": task_id, "concept": concept, "reason": reason}
