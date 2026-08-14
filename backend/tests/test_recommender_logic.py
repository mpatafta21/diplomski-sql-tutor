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
    concepts_with_available_tasks,
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
    """transversal = {column_alias, join_condition};
    subfloor = {insert, right_join} + neevaluabilni (vidi dolje);
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
    # 4.4-0h / NALAZ #27: `insert` i `right_join` imali su TOČNO 1 primarni task,
    # pa ih je subfloor pravilo (<2) tiho maskiralo kao savladane → recommender ih
    # NIKAD nije nudio (empirijski: p_l je ostajao na tier prioru). Svakom je
    # dodan po jedan ručno autorski zadatak → 2 taska → izlaze iz subfloora.
    # Preostaju SAMO M6 koncepti (0 aktivnih taskova, NALAZ #19) — očekivanje je
    # izraženo kroz UNSUPPORTED_CONCEPTS da ostane točno ako se M6 vrati u igru.
    assert subfloor == set(UNSUPPORTED_CONCEPTS), (
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
    # Subfloor maska — od 4.4-0h (NALAZ #27) `insert` i `right_join` VIŠE NISU
    # subfloor (svaki je dobio 2. primarni task), pa nose svoj pravi tier prior.
    # Maska ostaje samo na konceptima s 0 aktivnih taskova (M6, NALAZ #19).
    for code in UNSUPPORTED_CONCEPTS:
        assert snapshot[code] == pytest.approx(0.99), (
            f"{code} ima 0 aktivnih taskova → mora biti maskiran"
        )
    assert snapshot["right_join"] == pytest.approx(_PRIOR_HARD), (
        "right_join je od 4.4-0h normalan koncept — ne smije biti maskiran"
    )
    # NAPOMENA: prior dolazi iz PROLOG tiera (autoritativan), koji se za `insert`
    # razlikuje od DB stupca concepts.tier (Prolog easy vs DB medium) — vidi NALAZ #28.
    assert snapshot["insert"] == pytest.approx(_PRIOR_EASY), (
        "insert je od 4.4-0h normalan koncept — ne smije biti maskiran"
    )
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
# T7 — Koncept kojemu je SVE riješeno, a mastery nizak → preporuka ide DALJE
#
# 🔴 IZMIJENJENO 2026-08-14. Ovaj je test prije tvrdio suprotno: da isti slučaj
# daje `task_id=None, reason="exhausted"`. Bio je pisan prema PROMATRANOM
# ponašanju i time zaključao ćorsokak kao specifikaciju (klasa NALAZA #57).
#
# Posljedica u praksi, izmjerena na računu `admin`: `where_filter` (3/3 riješena,
# p_l 0.7728) i `insert` (2/2, p_l 0.7702) bili su vječni kandidati — Prolog ih
# preporuči, task selekcija nema što vratiti, student vidi „Nema novih zadataka"
# uz **71 neriješen zadatak** drugdje. Mastery im ne može narasti jer se do
# zadatka ne dolazi kroz preporuku.
#
# Odluka korisnika 2026-08-14: preporuka prelazi na drugi koncept. Put do
# ponavljanja ostaje kroz Module (klik na koncept → riješen zadatak uz oznaku).
# ---------------------------------------------------------------------------


def test_all_tasks_solved_moves_on_when_alternative_exists(
    recommender_env, prolog_engine
):
    """🔴 Stanje s računa `admin`: koncept iscrpljen, ALI drugdje ima zadataka.

    select_basic savladan (0.9) i sav riješen → nizvodni koncepti su otključani i
    imaju neriješene zadatke → preporuka mora otići NA DRUGI koncept, ne vratiti
    „Nema novih zadataka".
    """
    user_id = recommender_env["user_id"]
    _seed_mastery(user_id, {"select_basic": 0.9})
    _seed_solved(user_id, _primary_task_ids("select_basic"))

    with SessionLocal() as sess:
        result = recommend(sess, prolog_engine, user_id)

    assert result["reason"] != "exhausted", f"ćorsokak: {result}"
    assert result["concept"] != "select_basic", (
        f"koncept bez raspoloživog zadatka ostao je kandidat: {result}"
    )
    assert result["task_id"] is not None, f"nema izlaza kroz sučelje: {result}"


def test_dead_end_falls_back_to_repeat_instead_of_false_celebration(
    recommender_env, prolog_engine
):
    """🔴 Kad NEMA kamo dalje, ponavljanje je jedini put — ne „Sve savladano".

    select_basic je JEDINI korijen grafa. Ako mu je sve riješeno a nije savladan
    (0.1), `prereqs_met` blokira sve nizvodno, pa nijedan koncept nema neriješen
    zadatak unutar ZPD-a.

    Bez rezerve `recommend_next` ovdje padne → reason="no_recommendation", što
    sučelje prikazuje kao slavljeničko „Sve savladano" — laž, jer student ima
    neriješenih zadataka. Ponavljanje diže mastery kroz BKT i time otključava
    ostatak grafa.
    """
    user_id = recommender_env["user_id"]
    _seed_mastery(user_id, {"select_basic": 0.1})
    solved = _primary_task_ids("select_basic")
    _seed_solved(user_id, solved)

    with SessionLocal() as sess:
        result = recommend(sess, prolog_engine, user_id)

    assert result["reason"] != "no_recommendation", (
        f"lažno slavlje: {result} — student ima neriješenih zadataka"
    )
    assert result["task_id"] is not None, f"nema izlaza kroz sučelje: {result}"
    assert result["reason"] == "repeat_practice", f"neočekivan reason: {result}"
    assert result["task_id"] in solved, "ponavljanje mora ponuditi riješen zadatak"


def test_concept_with_all_solved_is_not_recommendable(recommender_env):
    """Skup kandidata je PO KORISNIKU: riješeno mijenja tko u njemu je."""
    user_id = recommender_env["user_id"]

    with SessionLocal() as sess:
        assert "select_basic" in concepts_with_available_tasks(sess, user_id)

    _seed_solved(user_id, _primary_task_ids("select_basic"))

    with SessionLocal() as sess:
        assert "select_basic" not in concepts_with_available_tasks(sess, user_id), (
            "koncept sa svim riješenim zadacima i dalje je kandidat"
        )


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
# recommender je servirao task `explain_plan_d3_60b9eaee` (source_id — NALAZ #21:
# numerički id se mijenja pri svakom reseedu), evaluator ga NE zna ocijeniti
# → nikad is_correct → nikad "riješen" → isti task zauvijek, uz 0 XP i BKT kaznu.
# ---------------------------------------------------------------------------


def test_unsupported_concepts_yield_no_task(recommender_env):
    """select_task_for_concept vraća None za neevaluabilne koncepte.

    DVA neovisna sloja obrane (oba se ovdje tvrde):
      1. kod: guard u select_task_for_concept (4.4-0d),
      2. podaci: M6 taskovi su is_active=False (4.4-0e, NALAZ #19) pa ih ni
         upit ne bi našao.
    Sloj 1 je bitan jer bi se sloj 2 mogao vratiti (plan-presence evaluacija).
    """
    user_id = recommender_env["user_id"]
    with SessionLocal() as sess:
        for code in UNSUPPORTED_CONCEPTS:
            assert not _primary_task_ids(code), (
                f"{code}: očekujem NULA aktivnih taskova (NALAZ #19)"
            )
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

    # Izolira pravilo pod testom (maska) od guarda po broju zadataka: ovdje se
    # tvrdi svijet u kojem SVI koncepti imaju zadatke, pa preporuku može
    # zaustaviti samo maska. Bez toga bi test prolazio iz drugog razloga —
    # explain_plan/index_usage danas imaju 0 aktivnih zadataka (izmjereno).
    prolog_engine.inject_recommendable(ALL_30)
    prolog_engine.inject_mastery("t_unmasked", snap)
    try:
        rec = prolog_engine.recommend_next("t_unmasked")
    finally:
        prolog_engine.clear_mastery("t_unmasked")
        prolog_engine.clear_recommendable()

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

    prolog_engine.inject_recommendable(ALL_30)  # v. napomenu u testu iznad
    prolog_engine.inject_mastery("t_masked", snap)
    try:
        rec = prolog_engine.recommend_next("t_masked")
    finally:
        prolog_engine.clear_mastery("t_masked")
        prolog_engine.clear_recommendable()

    assert rec is not None, "maska je ušutkala preporuku — tiši ćorsokak"
    assert rec[0] not in UNSUPPORTED_CONCEPTS
    assert rec[0] == "self_join", f"mora ponuditi evaluabilan koncept, dobiveno {rec}"


# ---------------------------------------------------------------------------
# T10 — Kat. A ćorsokak: transverzalni koncept POBIJEDI PRIORITETOM
#
# Zatečeni kvar (nije ga uveo Faza 5), izmjeren 2026-08-13 na računu s 6/80
# riješenih: /next-task vraća {"task_id": null, "concept": "join_condition",
# "reason": "exhausted"}, a UI to prikaže kao „Nema novih zadataka" — uz 74
# neriješena zadatka i BEZ izlaza kroz sučelje.
#
# 🔴 Mehanizam je PRIORITET, ne prazan skup kandidata. Izmjereno na stvarnom
# motoru: actionable skup ima TRI člana — {join_condition, select_basic,
# where_filter}. join_condition je 0.0 → weak (<0.30) → klauzula 1 `recommend_next`
# reže cutom prije nego se stigne do klauzule 2 (partial), gdje čekaju select_basic
# (0.8412) i where_filter. Transverzalni po dizajnu ima 0 zadataka →
# select_task_for_concept → None → reason="exhausted".
#
# Uvjet ulaska: from_clause SAVLADAN + select_basic < 0.85. Zato ga T4 (novak) ne
# hvata — novaku from_clause nije mastered, pa prereqs_met(join_condition) padne i
# klauzula 1 se ne upali. from_clause saturira brzo (sekundarni koncept gotovo
# svakog zadatka), pa je to stanje kroz koje realno prolazi svaki sudionik.
# ---------------------------------------------------------------------------

# Izmjereno na računu iz nalaza (2026-08-13), ne izmišljeno.
_DEADLOCK_PROFILE = {"from_clause": 0.99998, "select_basic": 0.8412}


def test_deadlock_profile_does_not_dead_end(recommender_env, prolog_engine):
    """🔴 REPRODUKCIJA: profil iz nalaza NE SMIJE dati ćorsokak.

    Tvrdi ISHOD vidljiv studentu (postoji zadatak), ne ime koncepta — ime je
    stvar pedagoškog poretka i smije se mijenjati, „nema izlaza" ne smije.
    """
    user_id = recommender_env["user_id"]
    _seed_mastery(user_id, _DEADLOCK_PROFILE)

    with SessionLocal() as sess:
        result = recommend(sess, prolog_engine, user_id)
        transversal = transversal_concepts(sess)

    assert result["reason"] != "exhausted", (
        f"ćorsokak: {result} — student vidi „Nema novih zadataka” uz neriješene zadatke"
    )
    assert result["task_id"] is not None, f"nema izlaza kroz sučelje: {result}"
    assert result["concept"] not in transversal, (
        f"preporučen transverzalni koncept {result['concept']!r}, koji po dizajnu "
        "nema zadataka"
    )


def test_deadlock_profile_falsifiable_control(recommender_env, prolog_engine):
    """Kontrola iz nalaza: podigni select_basic iznad praga → preporuka je zdrava.

    Bez ove kontrole test iznad ne bi razlikovao „popravljeno" od „profil nikad
    nije ni bio u ćorsokaku".
    """
    user_id = recommender_env["user_id"]
    _seed_mastery(user_id, {"from_clause": 0.99998, "select_basic": 0.90})

    with SessionLocal() as sess:
        result = recommend(sess, prolog_engine, user_id)
        transversal = transversal_concepts(sess)

    assert result["task_id"] is not None, f"kontrola: {result}"
    assert result["concept"] not in transversal


def test_transversal_loses_to_real_concept(prolog_engine):
    """🔴 JEZGRA: transverzalni 0.0 ne smije preteći koncept koji IMA zadatke.

    🔴 Determinizam NE SMIJE ovisiti o poretku injekcije fakata. Prva verzija ovog
    testa stavila je oba koncepta u `weak` i prolazila je i PRIJE popravka — ne
    zbog pravila nego zato što `self_join` (ALL_30 idx 16) dolazi prije
    `join_condition` (idx 27), pa ga je klauzula 1 zatekla prvog.

    Zato: join_condition je JEDINI weak (klauzula 1 nema konkurenciju), a self_join
    je partial (klauzula 2). Prije popravka klauzula 1 reže cutom na transverzalnom;
    poslije mora pasti na self_join. Ishod je jednoznačan u oba smjera bez obzira
    na poredak.

    Zrcali test_masked_skips_to_evaluable_concept (Kat. B/C), koji isto pravilo
    već čuva za maskirane koncepte.
    """
    snap = {c: 0.99 for c in ALL_30}
    snap["join_condition"] = 0.0  # jedini weak
    snap["self_join"] = 0.50  # jedini partial

    # Svijet u kojem svi OSIM transverzalnih imaju zadatke — to je stvarno stanje
    # kataloga i jedina stvar koju ovaj test ispituje.
    prolog_engine.inject_recommendable([c for c in ALL_30 if c != "join_condition"])
    prolog_engine.inject_mastery("t_transversal", snap)
    try:
        rec = prolog_engine.recommend_next("t_transversal")
    finally:
        prolog_engine.clear_mastery("t_transversal")
        prolog_engine.clear_recommendable()

    assert rec is not None, "preporuka ušutkana — tiši ćorsokak"
    assert rec[0] != "join_condition", (
        f"transverzalni koncept pobijedio prioritetom, dobiveno {rec}"
    )
    assert rec[0] == "self_join", f"mora ponuditi koncept sa zadacima, dobiveno {rec}"


def test_transversal_still_blocks_downstream(prolog_engine):
    """🔴 REGRESIJA: popravak NE SMIJE otključati nizvodne koncepte.

    join_condition = 0.0 je JEDINI izravni prereq od inner_join. Da popravak dira
    tu vrijednost (npr. poravnanjem tranzitivno→izravno u snapshotu), inner_join bi
    postao lažno dostupan novaku — kvar zbog kojeg Kat. A uopće postoji.
    """
    snap = {c: 0.10 for c in ALL_30}
    snap["join_condition"] = 0.0

    prolog_engine.inject_mastery("t_block", snap)
    try:
        met = list(prolog_engine._prolog.query("prereqs_met(t_block, inner_join)"))
    finally:
        prolog_engine.clear_mastery("t_block")

    assert not met, "inner_join je lažno otključan — blokada transverzalnim je pala"


# ---------------------------------------------------------------------------
# T11 — recommendable/1 NE SMIJE utjecati na poredak preporuke
#
# 🔴 Uhvaćeno tijekom implementacije: s `recommendable(Concept)` kao PRVIM ciljem
# u klauzuli i nevezanim Conceptom, predikat postaje GENERATOR — poredak rješenja
# prestaje ovisiti o `mastery/3` (kanonski pedagoški slijed) i počinje ovisiti o
# poretku `recommendable/1` fakata. Kako su se ti fakti tada injektirali iz Python
# seta, poredak je ovisio o hashu i mijenjao se između procesa: preporuka se
# mijenja bez ijedne izmjene koda = mehanizam ERRATE #60.
#
# Prvi simptom bio je pad zatečenog testa (M1+M2 mastered → dobio `update` umjesto
# `inner_join`). Ovi testovi pretvaraju taj slučajni pad u trajnu branu.
# ---------------------------------------------------------------------------


def test_recommendable_order_does_not_change_recommendation(prolog_engine):
    """🔴 Isti svijet, obrnut poredak recommendable fakata → ISTA preporuka.

    Pada ako `recommendable/1` ikad postane generator (npr. premještanjem na
    početak klauzule).
    """
    # 🔴 Profil mora dati VIŠE kandidata, inače test ne mjeri poredak. Prva verzija
    # stavila je sve na 0.10 i prolazila je i s namjerno vraćenom regresijom: kad
    # ništa nije mastered, `prereqs_met` vrijedi samo za `select_basic` (jedini
    # korijen grafa), pa je odgovor jedinstven bez obzira na poredak.
    # Ovdje su sve mastered osim dva weak koncepta čiji su prereqs zadovoljeni —
    # tada o pobjedniku odlučuje isključivo redoslijed nabrajanja.
    snap = {c: 0.99 for c in ALL_30}
    snap["self_join"] = 0.10
    snap["update"] = 0.10
    world = [c for c in ALL_30 if c != "join_condition"]

    results = []
    for order in (world, list(reversed(world))):
        prolog_engine.inject_recommendable(order)
        prolog_engine.inject_mastery("t_order", snap)
        try:
            results.append(prolog_engine.recommend_next("t_order"))
        finally:
            prolog_engine.clear_mastery("t_order")
            prolog_engine.clear_recommendable()

    assert results[0] == results[1], (
        f"poredak recommendable fakata promijenio preporuku: {results} — "
        "predikat je postao generator (ERRATA #60)"
    )


def test_candidate_set_is_canonically_ordered(recommender_env):
    """Skup za injekciju je LISTA u kanonskom poretku, ne set.

    Set bi dao poredak ovisan o hashu stringova, dakle promjenjiv između procesa.
    """
    user_id = recommender_env["user_id"]
    with SessionLocal() as sess:
        got = concepts_with_available_tasks(sess, user_id)
        canonical = list(load_concept_code_map(sess))

    assert isinstance(got, list), "set ne jamči poredak između procesa"
    assert got == [c for c in canonical if c in set(got)], (
        "poredak ne prati load_concept_code_map (kanonski pedagoški slijed)"
    )


def test_recommend_is_deterministic_across_calls(recommender_env, prolog_engine):
    """Isti profil, pet uzastopnih poziva → isti ishod (uklj. ćorsokak profil)."""
    user_id = recommender_env["user_id"]
    _seed_mastery(user_id, _DEADLOCK_PROFILE)

    with SessionLocal() as sess:
        results = [recommend(sess, prolog_engine, user_id) for _ in range(5)]

    assert all(r == results[0] for r in results), f"nedeterministično: {results}"


def test_recommend_injects_recommendable(recommender_env, prolog_engine):
    """🔴 recommend() MORA injektirati recommendable/1 — inače fail-closed ušutka sve.

    Brana protiv refaktora koji ispusti injekciju: bez fakata `recommend_next`
    ne vraća ništa, pa bi svaki korisnik dobio "no_recommendation".
    """
    user_id = recommender_env["user_id"]
    prolog_engine.clear_recommendable()  # zajamči prazno stanje prije poziva

    with SessionLocal() as sess:
        result = recommend(sess, prolog_engine, user_id)

    assert result["concept"] is not None, (
        f"recommend() nije injektirao recommendable/1 — dobiveno {result}"
    )


def test_recommendable_is_cleared_after_recommend(recommender_env, prolog_engine):
    """Globalni fakti se ne smiju zadržati nakon poziva (dijeljeni VM)."""
    user_id = recommender_env["user_id"]

    with SessionLocal() as sess:
        recommend(sess, prolog_engine, user_id)

    left = list(prolog_engine._prolog.query("recommendable(C)"))
    assert not left, f"recommendable/1 fakti procurili iz recommend(): {len(left)}"
