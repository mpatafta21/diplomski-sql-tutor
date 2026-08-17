"""Simulacija savršenog studenta — je li M6 dosežan i otključava li se `group_by`?

🔴 **Zašto simulacija, a ne zaključivanje.** Ista pitanja su se u 4.4-0f
odgovarala računom („2 točna po konceptu ⇒ badge dostižan") i odgovor je bio
KRIV: `right_join` nikad nije bivao ponuđen jer ga je subfloor maskirao, pa
nijedan račun nad ishodima nije mogao biti točan (ERRATA #25). Poučak: dostižnost
se MJERI prolaskom kroz stvarni preporučivač, ne izvodi iz brojki.

**IZMJERENI ISHODI (savršen student, 46 zadataka, 2026-08-14):**

| pitanje | odgovor |
|---|---|
| posjećeni moduli | **0, 1, 2, 3, 4, 5, 6** |
| je li M6 dosežan | **DA** — oba koncepta ponuđena ⇒ bedž `explorer` ostaje dostižan |
| blokira li `column_alias` nizvodni `group_by` | **NE** (0.9356 ≥ 0.85; `group_by` 0.99999) |
| nudi li preporučivač `column_alias` | 🔴 **NE, nijednom** |

🔴 Zadnji redak je nalaz, ne propust izvedbe: `column_alias` **saturira iznad
praga prije nego dođe na red**, jer ima 4 sekundarna pojavljivanja a Prolog bira
samo koncepte ISPOD praga. To je ERRATA #35 (ZPD escape) po drugi put, sada na
konceptu koji je zadatke dobio namjerno. Zadaci ostaju dosežni klikom na koncept
u pregledu Modula, ali ne kroz „Sljedeći zadatak".

Pokretanje: uv run pytest tests/test_m6_reachability.py -v -s
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, select

from agents.recommender_logic import recommend, resolve_task_for_concept
from app.db.models import Attempt, Concept, Module, SkillMastery, Task, TaskConcept, User
from app.db.session import SessionLocal
from app.prolog.prolog_engine import PrologEngine
from bkt.parameters import create_bkt_for_concept

_SIM_USERNAME = "sim_m6_reach"
_SIM_EMAIL = "sim_m6_reach@example.test"

#: Gornja granica koraka — simulacija mora stati i kad recommender vrti u krug.
_MAX_KORAKA = 400


@pytest.fixture(scope="module")
def engine():
    with PrologEngine() as eng:
        yield eng


@pytest.fixture
def sim_user():
    with SessionLocal() as s:
        s.execute(delete(User).where(User.username == _SIM_USERNAME))
        s.commit()
        u = User(
            username=_SIM_USERNAME, email=_SIM_EMAIL, password_hash="dummy_sim_m6"
        )
        s.add(u)
        s.commit()
        uid = u.id
    yield uid
    with SessionLocal() as s:
        s.execute(delete(Attempt).where(Attempt.user_id == uid))
        s.execute(delete(SkillMastery).where(SkillMastery.user_id == uid))
        s.execute(delete(User).where(User.id == uid))
        s.commit()


def _concepts_of_task(sess, task_id: int) -> list[tuple[str, bool]]:
    return [
        (code, is_primary)
        for code, is_primary in sess.execute(
            select(Concept.code, TaskConcept.is_primary)
            .join(TaskConcept, TaskConcept.concept_id == Concept.id)
            .where(TaskConcept.task_id == task_id)
        ).all()
    ]


def _bkt_update(sess, uid: int, code: str, correct: bool, engine: PrologEngine) -> None:
    """Isti put kao KnowledgeModelAgent: BKT posterior po konceptu zadatka.

    🔴 Tier dolazi iz PROLOGA (`create_bkt_for_concept`), ne iz `concepts.tier` —
    Prolog je autoritativan i za 6/30 koncepata se ta dva razilaze (ERRATA #28).
    """
    concept = sess.execute(
        select(Concept).where(Concept.code == code)
    ).scalar_one_or_none()
    if concept is None:
        return
    row = sess.execute(
        select(SkillMastery).where(
            SkillMastery.user_id == uid, SkillMastery.concept_id == concept.id
        )
    ).scalar_one_or_none()
    bkt = create_bkt_for_concept(code, engine)
    if row is None:
        row = SkillMastery(user_id=uid, concept_id=concept.id, p_l=bkt.p_l0)
        sess.add(row)
        sess.flush()
    bkt.p_l = row.p_l
    row.p_l = bkt.update(correct)


def _simuliraj(uid: int, engine: PrologEngine) -> dict:
    """Savršen student: uvijek točno rješava ono što mu se ponudi."""
    vidjeni_koncepti: list[str] = []
    vidjeni_moduli: set[int] = set()
    rijeseni: set[int] = set()

    for _ in range(_MAX_KORAKA):
        with SessionLocal() as sess:
            rec = recommend(sess, engine, uid)
            task_id = rec.get("task_id")
            concept = rec.get("concept")
            if task_id is None:
                break
            if task_id in rijeseni:
                # Rezerva (ponavljanje riješenog) — dalje nema novog gradiva.
                break

            task = sess.get(Task, task_id)
            modul = sess.execute(
                select(Module.number).where(Module.id == task.module_id)
            ).scalar_one()
            vidjeni_moduli.add(modul)
            if concept:
                vidjeni_koncepti.append(concept)

            broj_pokusaja = (
                sess.execute(
                    select(Attempt.attempt_number)
                    .where(Attempt.user_id == uid, Attempt.task_id == task_id)
                    .order_by(Attempt.attempt_number.desc())
                    .limit(1)
                ).scalar()
                or 0
            )
            sess.add(
                Attempt(
                    user_id=uid,
                    task_id=task_id,
                    submitted_query=task.expected_query,
                    is_correct=True,
                    error_type=None,
                    execution_time_ms=1,
                    rows_returned=0,
                    attempt_number=broj_pokusaja + 1,
                )
            )
            for code, _is_primary in _concepts_of_task(sess, task_id):
                _bkt_update(sess, uid, code, True, engine)
            rijeseni.add(task_id)
            sess.commit()

    with SessionLocal() as sess:
        mastery = {
            code: p
            for code, p in sess.execute(
                select(Concept.code, SkillMastery.p_l)
                .join(SkillMastery, SkillMastery.concept_id == Concept.id)
                .where(SkillMastery.user_id == uid)
            ).all()
        }
    return {
        "koncepti": vidjeni_koncepti,
        "moduli": vidjeni_moduli,
        "rijeseno": len(rijeseni),
        "mastery": mastery,
    }


# ---------------------------------------------------------------------------
# Tvrdnje
# ---------------------------------------------------------------------------


def test_column_alias_ne_blokira_group_by(sim_user, engine):
    """Tvrdnja 1: bojazan iz plana se NIJE ostvarila — M2 nije zaključan.

    Plan je strahovao da će `column_alias`, izlaskom iz Kat. A, zapeti ispod
    praga 0.85 (modul 0 → subfloor ga ne štiti) i zaključati nizvodni
    `group_by`. Izmjereno: ne zapinje.
    """
    rezultat = _simuliraj(sim_user, engine)

    print(f"\n  riješeno zadataka : {rezultat['rijeseno']}")
    print(f"  posjećeni moduli  : {sorted(rezultat['moduli'])}")
    print(f"  column_alias p_l  : {rezultat['mastery'].get('column_alias')}")
    print(f"  group_by     p_l  : {rezultat['mastery'].get('group_by')}")

    assert "group_by" in rezultat["koncepti"], (
        f"group_by nikad nije otključan; column_alias je zapeo na "
        f"{rezultat['mastery'].get('column_alias')} < 0.85 i blokirao cijeli M2"
    )
    assert rezultat["mastery"]["column_alias"] >= 0.85


def test_column_alias_je_ZPD_ESCAPE_dosezan_navigacijom_ali_ne_preporukom(
    sim_user, engine
):
    """🔴 Tvrdnja 2: tri nova `column_alias` zadatka preporučivač NIKAD ne nudi.

    Izmjereno: p_l dosegne **0.9356 — iznad praga 0.85 — a da koncept nijednom
    nije bio ponuđen kao primarni**. Uzrok je ERRATA #35 (ZPD escape): koncept
    ima 4 sekundarna pojavljivanja, BKT ažurira i sekundarne koncepte zadatka, a
    Prolog bira samo koncepte ISPOD praga. Saturira se prije nego dođe na red.

    🔴 Zadaci ipak NISU mrtvi: `resolve_task_for_concept` ih vraća, pa su
    dosežni klikom na redak koncepta u pregledu Modula (put iz ERRATE #42/#43).
    Razlika „dosežno navigacijom" vs „nuđeno preporukom" je ono što ovaj test
    zaključava — bez njega bi se lako čitalo da je koncept pokriven.

    Ovo je DRUGA neovisna potvrda #35, sada na konceptu koji je zadatke dobio
    namjerno. Za rad: dodavanje zadataka konceptu s puno sekundarnih
    pojavljivanja NE čini ga podučavanim.
    """
    rezultat = _simuliraj(sim_user, engine)

    assert "column_alias" not in rezultat["koncepti"], (
        "column_alias JE ponuđen — #35 više ne vrijedi za njega; provjeri je li "
        "se promijenio broj sekundarnih pojavljivanja ili prag"
    )

    with SessionLocal() as sess:
        task_id, ponavljanje = resolve_task_for_concept(
            sess, sim_user, "column_alias"
        )

    assert task_id is not None, (
        "zadaci su i navigacijom nedosežni — tada su stvarno mrtvi (#27)"
    )
    assert ponavljanje is False


def test_je_li_M6_dosezan_savrsenom_studentu(sim_user, engine):
    """Tvrdnja 2: dosežnost M6 — odgovor se MJERI i zapisuje, kakav god bio.

    O njemu ovisi bedž `explorer`: kriterij je dinamičan (moduli koji imaju
    aktivne zadatke), pa aktivacijom M6 bedž traži i njega. Ako M6 nije dosežan,
    `explorer` je nedostižan — ista klasa kao ERRATA #22/#25.
    """
    rezultat = _simuliraj(sim_user, engine)
    m6_koncepti = {"explain_plan", "index_usage"} & set(rezultat["koncepti"])

    print(f"\n  posjećeni moduli : {sorted(rezultat['moduli'])}")
    print(f"  M6 koncepti      : {sorted(m6_koncepti) or '—'}")

    assert 6 in rezultat["moduli"], (
        "M6 NIJE dosežan ni savršenom studentu → bedž `explorer` je nedostižan "
        "(regresija ERRATE #22). Kriterij bedža mora se suziti na M1–M5 ILI se "
        "prereqs M6 moraju popustiti — odluka korisnika, v. wrapup."
    )
