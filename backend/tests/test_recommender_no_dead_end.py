"""Falsifikacija: postoji li IKOJE stanje u kojem preporučivač nasuka studenta.

Grana `fix-koncept-do-zadatka` zatvorila je DVA oblika ćorsokaka, i drugi je nađen
tek nakon što je prvi bio proglašen riješenim (v. `docs/fix-koncept-zadatak-wrapup.md`
§A.6). Zato ovdje ne stoje samo primjeri, nego pokušaj **opovrgavanja** nad
nasumičnim stanjima.

🔴 Zove STVARNI `recommend()` nad stvarnim Prolog motorom — ne repliku njegove
logike. Da je pravila reimplementirao u Pythonu, test bi tvrdio da se replika slaže
sama sa sobom.

🔴 Svako stanje se upisuje u SAVEPOINT i rollbacka, pa u živu `tutor_main` ne ostaje
ništa (ERRATA #40 — suite dijeli bazu s aplikacijom).

Broj stanja je namjerno mali da suite ostane brz; dubinski prolaz:

    FALSIFY_TRIALS=1500 uv run pytest tests/test_recommender_no_dead_end.py

Sjeme je fiksno — pad mora biti reproducibilan, inače nalaz nije upotrebljiv.
"""

from __future__ import annotations

import os
import random

import pytest
from sqlalchemy import delete, select

from agents.db_helpers import load_concept_code_map
from agents.evaluation import UNSUPPORTED_CONCEPTS
from agents.recommender_logic import (
    _MASTERED_THRESHOLD,
    _concept_task_stats,
    build_mastery_snapshot,
    recommend,
    subfloor_concepts,
    transversal_concepts,
)
from app.db.models import Attempt, Concept, SkillMastery, Task, TaskConcept, User
from app.db.session import SessionLocal
from app.prolog.prolog_engine import PrologEngine

TRIALS = int(os.getenv("FALSIFY_TRIALS", "200"))
SEED = 20260814
_USERNAME = "_falsify_dead_end_tmp"


@pytest.fixture
def falsify_user():
    with SessionLocal() as s:
        s.execute(delete(User).where(User.username == _USERNAME))
        s.commit()
        u = User(
            username=_USERNAME,
            email="_falsify_dead_end@test.example",
            password_hash="dummy",
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


def _random_state(rng, codes, with_tasks, prim, all_tasks):
    """Nasumičan (mastery profil, skup riješenih). Rubovi su namjerno gusti."""
    mode = rng.random()
    if mode < 0.25:  # novak
        profile: dict[str, float] = {}
    elif mode < 0.5:  # sve visoko
        profile = {c: rng.uniform(0.85, 1.0) for c in codes}
    else:  # miješano, s vrijednostima točno oko pragova 0.30 i 0.85
        profile = {
            c: rng.choice([0.0, 0.05, 0.3, 0.5, 0.7, 0.84, 0.85, 0.9, 1.0])
            for c in codes
            if rng.random() < 0.8
        }

    solved: set[int] = set()
    # Patološki slučaj koji je i bio drugi oblik ćorsokaka: SVI zadaci nekog
    # koncepta riješeni. Bez ovoga bi nasumičan uzorak takvo stanje jedva pogodio.
    if rng.random() < 0.6 and with_tasks:
        for c in rng.sample(with_tasks, rng.randint(1, min(5, len(with_tasks)))):
            solved.update(prim[c])
    if rng.random() < 0.5:
        solved.update(rng.sample(all_tasks, rng.randint(0, len(all_tasks) // 2)))
    return profile, solved


def test_recommender_never_dead_ends(falsify_user):
    """Četiri tvrdnje nad nasumičnim stanjima; nijedna ne smije pasti.

    P1  nikad `exhausted` — task_id=None uz postavljen koncept je slijepa ulica
    P2  `no_recommendation` SAMO kad su svi koncepti sa zadacima savladani
        (inače je „Sve savladano" laž studentu koji ima što raditi)
    P3  `repeat_practice` nudi zadatak koji je student doista riješio
    P4  svaki vraćeni task_id je AKTIVAN i PRIMARAN za vraćeni koncept
    """
    uid = falsify_user
    rng = random.Random(SEED)
    violations: list[str] = []
    reasons: dict[str, int] = {}

    with SessionLocal() as s, PrologEngine() as engine:
        code_map = load_concept_code_map(s)
        codes = list(code_map)
        stats = _concept_task_stats(s)
        prim = {
            code: list(
                s.execute(
                    select(Task.id)
                    .join(TaskConcept, TaskConcept.task_id == Task.id)
                    .where(
                        TaskConcept.concept_id == cid,
                        TaskConcept.is_primary.is_(True),
                        Task.is_active.is_(True),
                    )
                ).scalars()
            )
            for code, cid in code_map.items()
        }
        all_tasks = sorted({t for ids in prim.values() for t in ids})
        with_tasks = [c for c in codes if prim[c]]
        assert with_tasks, "katalog nema nijedan koncept sa zadacima"

        for i in range(TRIALS):
            profile, solved = _random_state(rng, codes, with_tasks, prim, all_tasks)

            sp = s.begin_nested()
            try:
                if profile:
                    s.bulk_save_objects(
                        [
                            SkillMastery(user_id=uid, concept_id=code_map[c], p_l=v)
                            for c, v in profile.items()
                        ]
                    )
                if solved:
                    s.bulk_save_objects(
                        [
                            Attempt(
                                user_id=uid,
                                task_id=t,
                                submitted_query="SELECT 1",
                                is_correct=True,
                                attempt_number=1,
                            )
                            for t in solved
                        ]
                    )
                s.flush()

                res = recommend(s, engine, uid)
                reason = res["reason"]
                reasons[reason] = reasons.get(reason, 0) + 1

                if reason == "exhausted":
                    violations.append(f"[{i}] P1 ĆORSOKAK: {res}")

                if reason == "no_recommendation":
                    snap = build_mastery_snapshot(
                        s,
                        engine,
                        uid,
                        transversal_concepts(s, stats),
                        subfloor_concepts(s, stats) | UNSUPPORTED_CONCEPTS,
                        # `code_map`, ne `codes`: parametar je dict[str, int].
                        # Lista bi radila slucajno (tijelo samo iterira kljuceve)
                        # i pukla cim netko doda `code_map[code]`.
                        code_map,
                    )
                    nesavladani = [
                        c
                        for c in with_tasks
                        if snap.get(c, 0.0) < _MASTERED_THRESHOLD
                    ]
                    if nesavladani:
                        violations.append(
                            f"[{i}] P2 LAŽNO SLAVLJE uz nesavladane {nesavladani[:4]}"
                        )

                tid = res["task_id"]
                if tid is not None:
                    if reason == "repeat_practice" and tid not in solved:
                        violations.append(
                            f"[{i}] P3: repeat_practice nudi NEriješen {tid}"
                        )
                    if tid not in prim.get(res["concept"], []):
                        violations.append(
                            f"[{i}] P4: task {tid} nije aktivan primaran za "
                            f"{res['concept']}"
                        )
            finally:
                sp.rollback()

    assert not violations, (
        f"{len(violations)} povreda u {TRIALS} stanja "
        f"(seed={SEED}): {violations[:5]}"
    )
    # Rezerva mora biti ŽIVA grana, ne mrtav kod — da tvrdnje ne prolaze zato što
    # se taj put nikad ne izvrši. Uz TRIALS=200 pojavi se ~8 puta.
    assert reasons.get("repeat_practice"), (
        f"grana `repeat_practice` nije pogođena ni jednom — tvrdnja P3 ništa ne "
        f"čuva; viđeni reasoni: {reasons}"
    )
