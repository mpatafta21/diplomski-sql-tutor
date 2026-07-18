"""TDD testovi za agents/recommender_logic.py — 3C.1.

Čista recommend logika (bez SPADE): snapshot build (tier-točan prior),
2-kategorijski sub-floor (transverzalni prozirni + subfloor mask), task
selekcija, te recommend() orkestracija.

Strategija sub-floora (dvije kategorije, DB-izvedeno):
  Kat. A — TRANSVERZALNI (modul 0, 0 aktivnih primary taskova): {column_alias,
    join_condition}. PROZIRNI: p_l = 0.99 ako su SVI all_prereqs mastered u
    snapshotu, inače 0.0 (blokira nizvodno). Readiness teče kroz njih samo kad
    su im prereqs gotovi.
  Kat. B — SUBFLOOR (modul != 0, < 2 aktivna primary taska): {insert, right_join}.
    MASK kao mastered (0.99) da ih Prolog preskoči kroz vlastite klauzule.

Bug slučaj koji ova strategija popravlja: blanket maska p_l=0.99 na transverzalni
join_condition (JEDINI prereq od inner_join) prerano je otključavala inner_join
NOVAKU. Prozirnost to rješava: novak → join_condition=0.0 → inner_join blokiran
→ preporuka select_basic.

Reuse zlatnih profila/konstanti iz test_recommender_synthetic.py.

Cleanup: recommender_env kreira committed usera, briše attempts+skill_mastery+user
u teardown-u. PrologEngine je class-level singleton; recommend() sam čisti mastery
fakte (finally clear_mastery), a fixture __exit__ je dodatni safety net.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy import delete, select

from agents.db_helpers import load_concept_code_map
from agents.evaluation import UNSUPPORTED_CONCEPTS
from agents.recommender_logic import (
    build_mastery_snapshot,
    recommend,
    select_task_for_concept,
    subfloor_concepts,
    transversal_concepts,
)
from app.db.models import Attempt, SkillMastery, Task, TaskConcept, User
from app.db.session import SessionLocal
from app.prolog.prolog_engine import PrologEngine
from tests.test_recommender_synthetic import ALL_30, M1_CONCEPTS, M2_CONCEPTS

# ---------------------------------------------------------------------------
# Konstante
# ---------------------------------------------------------------------------

_RC_USERNAME = "rc_test_user_3c1"
_RC_EMAIL = "rc_3c1@test.example"

# Tier-točni p_l0 (iz bkt/parameters.py TIER_DEFAULTS) — NE flat 0.1
_PRIOR_EASY = 0.30  # npr. select_basic
_PRIOR_MEDIUM = 0.15  # npr. agg_count
_PRIOR_HARD = 0.05  # npr. left_join


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def recommender_env():
    """Committed test user. Teardown briše attempts + skill_mastery + user."""
    with SessionLocal() as sess:
        user = User(
            username=_RC_USERNAME,
            email=_RC_EMAIL,
            password_hash="dummy_hash_3c1",
        )
        sess.add(user)
        sess.commit()
        user_id = user.id

    yield {"user_id": user_id}

    with SessionLocal() as cleanup:
        cleanup.execute(delete(Attempt).where(Attempt.user_id == user_id))
        cleanup.execute(delete(SkillMastery).where(SkillMastery.user_id == user_id))
        cleanup.execute(delete(User).where(User.id == user_id))
        cleanup.commit()


@pytest.fixture
def prolog_engine():
    """PrologEngine s automatskim cleanup-om mastery fakata (singleton VM)."""
    with PrologEngine() as engine:
        yield engine


# ---------------------------------------------------------------------------
# Helperi
# ---------------------------------------------------------------------------


def _seed_mastery(user_id: int, profile: dict[str, float]) -> None:
    """Upsert SkillMastery redova s danim p_l vrijednostima."""
    with SessionLocal() as sess:
        code_map = load_concept_code_map(sess)
        for code, p_l in profile.items():
            cid = code_map[code]
            row = sess.get(SkillMastery, (user_id, cid))
            if row is None:
                sess.add(SkillMastery(user_id=user_id, concept_id=cid, p_l=p_l))
            else:
                row.p_l = p_l
        sess.commit()


def _primary_task_ids(code: str) -> list[int]:
    """Aktivni primary task id-evi koncepta, sortirani po difficulty pa id."""
    with SessionLocal() as sess:
        cid = load_concept_code_map(sess)[code]
        return list(
            sess.execute(
                select(Task.id)
                .join(TaskConcept, TaskConcept.task_id == Task.id)
                .where(
                    TaskConcept.concept_id == cid,
                    TaskConcept.is_primary.is_(True),
                    Task.is_active.is_(True),
                )
                .order_by(Task.difficulty, Task.id)
            ).scalars()
        )


def _seed_solved(user_id: int, task_ids: list[int]) -> None:
    """Označi taskove kao točno riješene (is_correct=True)."""
    with SessionLocal() as sess:
        for tid in task_ids:
            sess.add(
                Attempt(
                    user_id=user_id,
                    task_id=tid,
                    submitted_query="SELECT 1",
                    is_correct=True,
                    attempt_number=1,
                )
            )
        sess.commit()


def _all_mastered_profile() -> dict[str, float]:
    return {c: 0.9 for c in ALL_30}


# ---------------------------------------------------------------------------
# T1 — Kategorizacija (DB-izvedeno): transverzalni vs subfloor
# ---------------------------------------------------------------------------


def test_category_sets_are_db_derived():
    """transversal = {column_alias, join_condition}; subfloor = {insert, right_join};
    null_handling (modul 0 ALI ima taskove) NE smije biti transverzalan."""
    with SessionLocal() as sess:
        transversal = transversal_concepts(sess)
        subfloor = subfloor_concepts(sess)

    assert transversal == {"column_alias", "join_condition"}, (
        f"Transverzalni (modul 0, 0 taskova) krivi: {transversal}"
    )
    assert "null_handling" not in transversal, (
        "null_handling ima taskove → NIJE transverzalan"
    )
    assert subfloor == {"insert", "right_join"}, (
        f"Subfloor (modul != 0, < 2 taska) krivi: {subfloor}"
    )
    assert transversal.isdisjoint(subfloor), "Kategorije se ne smiju preklapati"


# ---------------------------------------------------------------------------
# T2 — Snapshot ima svih 30 s TIER-TOČNIM priorom (ne flat 0.1)
# ---------------------------------------------------------------------------


def test_snapshot_uses_tier_priors_not_flat(recommender_env, prolog_engine):
    """Novak (bez skill_mastery): snapshot ima svih 30, nedirane na TIER p_l0.

    Dokazuje tier-točan prior: left_join=0.05 (hard), NE 0.1; select_basic=0.30
    (easy); agg_count=0.15 (medium). Subfloor → 0.99; transverzalni (novak) → 0.0.
    """
    user_id = recommender_env["user_id"]

    with SessionLocal() as sess:
        transversal = transversal_concepts(sess)
        subfloor = subfloor_concepts(sess)
        snapshot = build_mastery_snapshot(
            sess, prolog_engine, user_id, transversal, subfloor
        )

    assert len(snapshot) == 30, f"Snapshot mora imati svih 30, ima {len(snapshot)}"
    # Tier-točni priori (razlikovni od flat 0.1)
    assert snapshot["left_join"] == pytest.approx(_PRIOR_HARD), "hard p_l0 = 0.05, NE 0.1"
    assert snapshot["select_basic"] == pytest.approx(_PRIOR_EASY), "easy p_l0 = 0.30"
    assert snapshot["agg_count"] == pytest.approx(_PRIOR_MEDIUM), "medium p_l0 = 0.15"
    # Subfloor maska
    assert snapshot["insert"] == pytest.approx(0.99)
    assert snapshot["right_join"] == pytest.approx(0.99)
    # Transverzalni za novaka → 0.0 (prereqs nisu mastered)
    assert snapshot["join_condition"] == pytest.approx(0.0)
    assert snapshot["column_alias"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# T3 — Dirani koncepti overwrite-aju prior iz skill_mastery
# ---------------------------------------------------------------------------


def test_seeded_mastery_overwrites_prior(recommender_env, prolog_engine):
    """skill_mastery red (inner_join=0.25) nadjačava tier prior (0.15) u snapshotu."""
    user_id = recommender_env["user_id"]
    _seed_mastery(user_id, {"inner_join": 0.25})

    with SessionLocal() as sess:
        transversal = transversal_concepts(sess)
        subfloor = subfloor_concepts(sess)
        snapshot = build_mastery_snapshot(
            sess, prolog_engine, user_id, transversal, subfloor
        )

    assert snapshot["inner_join"] == pytest.approx(0.25), (
        "skill_mastery p_l mora nadjačati tier prior 0.15"
    )


# ---------------------------------------------------------------------------
# T4 — BUG SLUČAJ: novak → select_basic, NE inner_join (prozirnost radi)
# ---------------------------------------------------------------------------


def test_novice_recommends_select_basic_not_inner_join(recommender_env, prolog_engine):
    """KLJUČNI test: novak (bez mastery) dobiva select_basic, NE inner_join.

    Blanket maska p_l=0.99 na join_condition (jedini prereq inner_join) je prije
    lažno otključavala inner_join novaku. Prozirnost: join_condition=0.0 →
    inner_join blokiran → select_basic.
    """
    user_id = recommender_env["user_id"]

    with SessionLocal() as sess:
        result = recommend(sess, prolog_engine, user_id)

    assert result["concept"] == "select_basic", (
        f"Novak mora dobiti select_basic, dobio {result['concept']} "
        "(ako je inner_join → prozirnost transverzalnih ne radi!)"
    )
    assert result["concept"] != "inner_join"
    assert result["reason"] == "partial_continuation", (
        "select_basic na tier prioru 0.30 je PARTIAL (ne weak kao flat 0.1)"
    )
    assert result["task_id"] is not None, "Mora vratiti konkretan task_id"


# ---------------------------------------------------------------------------
# T5 — Prozirnost u DRUGOM smjeru: M1 mastered → join_condition otključa inner_join
# ---------------------------------------------------------------------------


def test_advanced_transversal_unlocks_downstream(recommender_env, prolog_engine):
    """M1 mastered → join_condition prozirno postaje 0.99 (prereqs gotovi).

    Dokazuje da prozirnost radi u oba smjera: novak blokira (T4), napredni otključava.
    """
    user_id = recommender_env["user_id"]
    _seed_mastery(user_id, {c: 0.9 for c in M1_CONCEPTS})

    with SessionLocal() as sess:
        transversal = transversal_concepts(sess)
        subfloor = subfloor_concepts(sess)
        snapshot = build_mastery_snapshot(
            sess, prolog_engine, user_id, transversal, subfloor
        )

    assert snapshot["join_condition"] == pytest.approx(0.99), (
        "M1 mastered → join_condition prereqs (from_clause, select_basic) gotovi → 0.99"
    )


def test_advanced_recommends_inner_join(recommender_env, prolog_engine):
    """M1+M2 mastered → preporuka inner_join (prvi weak s ispunjenim prereq-ima)."""
    user_id = recommender_env["user_id"]
    _seed_mastery(user_id, {c: 0.9 for c in M1_CONCEPTS + M2_CONCEPTS + ["null_handling"]})

    with SessionLocal() as sess:
        result = recommend(sess, prolog_engine, user_id)

    assert result["concept"] == "inner_join", (
        f"M1+M2 mastered → inner_join, dobio {result['concept']}"
    )
    assert result["reason"] == "weak_with_prereqs_met"
    assert result["task_id"] is not None


# ---------------------------------------------------------------------------
# T6 — Solved task se izbjegava (sljedeći po difficulty)
# ---------------------------------------------------------------------------


def test_solved_task_excluded(recommender_env):
    """Riješen najlakši task koncepta → select_task vrati SLJEDEĆI po difficulty."""
    user_id = recommender_env["user_id"]
    task_ids = _primary_task_ids("select_basic")
    assert len(task_ids) >= 2, "Test pretpostavlja >= 2 taska za select_basic"
    easiest, next_one = task_ids[0], task_ids[1]

    _seed_solved(user_id, [easiest])

    with SessionLocal() as sess:
        chosen = select_task_for_concept(sess, user_id, "select_basic")

    assert chosen == next_one, f"Mora preskočiti riješen {easiest}, vratiti {next_one}"
    assert chosen != easiest


# ---------------------------------------------------------------------------
# T7 — Iscrpljen koncept (svi taskovi riješeni) → None + reason="exhausted"
# ---------------------------------------------------------------------------


def test_exhausted_concept_returns_exhausted(recommender_env, prolog_engine):
    """select_basic weak (0.1) ali SVI taskovi riješeni → exhausted, task_id=None."""
    user_id = recommender_env["user_id"]
    _seed_mastery(user_id, {"select_basic": 0.1})
    _seed_solved(user_id, _primary_task_ids("select_basic"))

    with SessionLocal() as sess:
        result = recommend(sess, prolog_engine, user_id)

    assert result["concept"] == "select_basic"
    assert result["task_id"] is None
    assert result["reason"] == "exhausted"


# ---------------------------------------------------------------------------
# T8 — Sve mastered → None + reason="no_recommendation"
# ---------------------------------------------------------------------------


def test_all_mastered_no_recommendation(recommender_env, prolog_engine):
    """Svih 30 na 0.9 → recommend_next None → reason no_recommendation."""
    user_id = recommender_env["user_id"]
    _seed_mastery(user_id, _all_mastered_profile())

    with SessionLocal() as sess:
        result = recommend(sess, prolog_engine, user_id)

    assert result["task_id"] is None
    assert result["concept"] is None
    assert result["reason"] == "no_recommendation"


# ---------------------------------------------------------------------------
# T9 — Subfloor masking je benigno: insert nije prereq ničemu
# ---------------------------------------------------------------------------


def test_insert_masking_is_benign(prolog_engine):
    """insert (subfloor) nije prereq nijednom konceptu → masking ga ne otključava ništa."""
    for concept in ALL_30:
        prereqs = prolog_engine.all_prereqs(concept)
        assert "insert" not in prereqs, (
            f"insert je prereq od {concept!r} — masking bi ga lažno otključao!"
        )


# ---------------------------------------------------------------------------
# T10 — Subfloor koncepti se NIKAD ne preporučuju kao meta
# ---------------------------------------------------------------------------


def test_subfloor_never_recommended(recommender_env, prolog_engine):
    """U novice i advanced profilu recommend nikad ne vraća insert/right_join."""
    user_id = recommender_env["user_id"]

    # Novice
    with SessionLocal() as sess:
        novice = recommend(sess, prolog_engine, user_id)
    assert novice["concept"] not in {"insert", "right_join"}

    # Advanced (sve M1-M4 + transverzalni mastered, M3 djelomično)
    _seed_mastery(
        user_id,
        {c: 0.9 for c in M1_CONCEPTS + M2_CONCEPTS + ["null_handling", "inner_join"]},
    )
    with SessionLocal() as sess:
        advanced = recommend(sess, prolog_engine, user_id)
    assert advanced["concept"] not in {"insert", "right_join"}, (
        f"Subfloor preporučen kao meta: {advanced['concept']}"
    )


# ---------------------------------------------------------------------------
# T11 — Cleanup: recommend čisti mastery fakte (nema cross-user leaka)
# ---------------------------------------------------------------------------


def test_recommend_clears_mastery_after(recommender_env, prolog_engine):
    """recommend() poziva clear_mastery(str(user_id)) u finally — dokaz spy-em."""
    user_id = recommender_env["user_id"]

    with patch.object(
        prolog_engine, "clear_mastery", wraps=prolog_engine.clear_mastery
    ) as spy:
        with SessionLocal() as sess:
            recommend(sess, prolog_engine, user_id)

    spy.assert_called_with(str(user_id))


# ---------------------------------------------------------------------------
# T-4.4-0d — NEEVALUABILNI koncepti (Kat. C) se NE preporučuju
#
# 🔴 Ćorsokak prije fixa: Prolog je vraćao ('explain_plan', 'weak_with_prereqs_met'),
# recommender je servirao task 90, evaluator ga NE zna ocijeniti (unsupported_eval)
# → nikad is_correct → nikad "riješen" → isti task zauvijek, uz 0 XP i BKT kaznu.
# ---------------------------------------------------------------------------


def test_unsupported_concepts_yield_no_task(recommender_env):
    """select_task_for_concept vraća None za neevaluabilne — iako taskovi POSTOJE."""
    user_id = recommender_env["user_id"]
    with SessionLocal() as sess:
        for code in UNSUPPORTED_CONCEPTS:
            assert _primary_task_ids(code), f"preduvjet: {code} ima aktivne taskove"
            assert select_task_for_concept(sess, user_id, code) is None, (
                f"{code} je neevaluabilan — NE smije dati task (trajni ćorsokak)"
            )


def test_evaluable_concepts_still_yield_tasks(recommender_env):
    """Regresija: ostali koncepti su NEDIRNUTI (uklj. DML koje sada znamo ocijeniti)."""
    user_id = recommender_env["user_id"]
    with SessionLocal() as sess:
        for code in ("select_basic", "group_by", "insert", "update", "delete"):
            assert select_task_for_concept(sess, user_id, code) is not None, (
                f"{code} je evaluabilan i mora davati task"
            )


def test_unsupported_concepts_masked_in_snapshot(recommender_env, prolog_engine):
    """Maska je na razini KONCEPTA (0.99) — Prolog ih preskače kroz vlastite klauzule."""
    user_id = recommender_env["user_id"]
    with SessionLocal() as sess:
        masked = subfloor_concepts(sess) | UNSUPPORTED_CONCEPTS
        snap = build_mastery_snapshot(
            sess, prolog_engine, user_id, transversal_concepts(sess), masked
        )
    for code in UNSUPPORTED_CONCEPTS:
        assert snap[code] >= 0.99, f"{code} mora biti maskiran kao mastered"


def test_unmasked_prolog_would_recommend_unevaluable(prolog_engine):
    """Preduvjet ćorsokaka: kad su SAMO neevaluabilni koncepti slabi, Prolog ih nudi.

    Deterministički jer su oni JEDINI slabi kandidati (ne ovisi o redoslijedu
    Prologovih rješenja).
    """
    snap = {c: 0.99 for c in ALL_30}
    for code in UNSUPPORTED_CONCEPTS:
        snap[code] = 0.10

    prolog_engine.inject_mastery("t_unmasked", snap)
    try:
        rec = prolog_engine.recommend_next("t_unmasked")
    finally:
        prolog_engine.clear_mastery("t_unmasked")

    assert rec is not None and rec[0] in UNSUPPORTED_CONCEPTS, (
        f"bez maske Prolog nudi neevaluabilan koncept (= ćorsokak), dobiveno {rec}"
    )


def test_masked_skips_to_evaluable_concept(prolog_engine):
    """🔴 S maskom: preskoči neevaluabilno i ponudi STVARAN zadatak — ne šutnju.

    Ovo je dokaz da fix ne stvara TIŠI ćorsokak (task_id=None / no_recommendation):
    self_join je jedini evaluabilan slab koncept pa je očekivanje jednoznačno.
    """
    snap = {c: 0.99 for c in ALL_30}
    snap["self_join"] = 0.10
    for code in UNSUPPORTED_CONCEPTS:
        snap[code] = 0.99  # maska koju recommend() primjenjuje

    prolog_engine.inject_mastery("t_masked", snap)
    try:
        rec = prolog_engine.recommend_next("t_masked")
    finally:
        prolog_engine.clear_mastery("t_masked")

    assert rec is not None, "maska je ušutkala preporuku — tiši ćorsokak"
    assert rec[0] not in UNSUPPORTED_CONCEPTS
    assert rec[0] == "self_join", f"mora ponuditi evaluabilan koncept, dobiveno {rec}"
