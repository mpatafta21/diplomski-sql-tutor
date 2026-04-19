"""Sintetički korisnički profili za validaciju Prolog recommend_next.

Tri profila iz §4.5 dokumenta faza-1-domenski-model.md + dva dodatna unit
testa (tranzitivni prereqs i explain_recommendation reason string).

TDD crvena faza: ovi testovi padaju dok ne postoji PrologEngine wrapper
(vidi Task 5).
"""

from __future__ import annotations

import pytest

from app.prolog.prolog_engine import PrologEngine  # NAMJERNO padne prije Task 5


# --- Fixtures ------------------------------------------------------------

@pytest.fixture
def engine():
    """Svježa PrologEngine instanca s automatskim cleanup-om mastery fakata.

    __exit__ radi retractall(mastery/3) pa testovi ne cure state među sobom.
    """
    with PrologEngine() as eng:
        yield eng


# --- Profili iz §4.5 dokumenta -------------------------------------------

# M1 — Osnove SELECT-a (6)
M1_CONCEPTS = [
    "select_basic", "from_clause", "where_filter",
    "order_by", "limit_offset", "distinct",
]
# M2 — Agregacije (5)
M2_CONCEPTS = [
    "group_by", "having_filter", "agg_count",
    "agg_sum_avg", "agg_min_max",
]
# M3 — JOIN-ovi (7)
M3_CONCEPTS = [
    "inner_join", "left_join", "right_join",
    "full_outer_join", "cross_join", "self_join", "multi_table_join",
]
# M4 — DML (3)
M4_CONCEPTS = ["insert", "update", "delete"]
# M5 — Podupiti (4)
M5_CONCEPTS = [
    "scalar_subquery", "in_subquery",
    "exists_subquery", "correlated_subquery",
]
# Transverzalni (3)
TRANSVERSAL = ["null_handling", "column_alias", "join_condition"]

ALL_30 = (
    M1_CONCEPTS + M2_CONCEPTS + M3_CONCEPTS + M4_CONCEPTS
    + M5_CONCEPTS + TRANSVERSAL + ["explain_plan", "index_usage"]
)


# --- Test 1: user_novice — sve P_L = 0.1 → select_basic ------------------

def test_novice_recommends_select_basic(engine: PrologEngine) -> None:
    """Početnik bez ikakvog znanja: prva preporuka je korijen grafa (select_basic)."""
    snapshot = {c: 0.1 for c in ALL_30}
    engine.inject_mastery("user_novice", snapshot)

    result = engine.recommend_next("user_novice")

    assert result is not None, "recommend_next mora vratiti neku preporuku"
    concept, reason = result
    assert concept == "select_basic"
    assert reason == "weak_with_prereqs_met"


# --- Test 2: user_join_stuck — stuck na inner_join -----------------------

def test_join_stuck_recommends_inner_join(engine: PrologEngine) -> None:
    """M1/M2 mastered, inner_join weak s ispunjenim prereq-ima → inner_join.

    NAPOMENA: `join_condition` je 0.9 (ne 0.8 kao u §4.5 doc-a) — korisnik
    je odobrio 0.9 jer je inače `prereqs_met(inner_join)` pao i test bi
    vratio `join_condition` umjesto očekivanog `inner_join`.
    """
    snapshot: dict[str, float] = {}
    # M1 i M2 svi mastered (0.9 >= 0.85)
    for c in M1_CONCEPTS + M2_CONCEPTS:
        snapshot[c] = 0.9
    # column_alias je prereq group_by — mastered da group_by ima prereqs_met
    snapshot["column_alias"] = 0.9
    # inner_join weak (0.25 < 0.30)
    snapshot["inner_join"] = 0.25
    # join_condition mastered (0.9 — pogledaj napomenu iznad)
    snapshot["join_condition"] = 0.9
    # null_handling partial (0.7 ∈ [0.30, 0.85))
    snapshot["null_handling"] = 0.7

    engine.inject_mastery("user_join_stuck", snapshot)

    result = engine.recommend_next("user_join_stuck")

    assert result is not None
    concept, reason = result
    assert concept == "inner_join"
    assert reason == "weak_with_prereqs_met"


# --- Test 3: user_advanced — M1-M4 mastered, M5 0.1 → scalar_subquery ----

def test_advanced_recommends_scalar_subquery(engine: PrologEngine) -> None:
    """Svi M1-M4 + transverzalni mastered, M5 na 0.1 → scalar_subquery (prvi M5)."""
    snapshot: dict[str, float] = {}
    for c in M1_CONCEPTS + M2_CONCEPTS + M3_CONCEPTS + M4_CONCEPTS + TRANSVERSAL:
        snapshot[c] = 0.9
    for c in M5_CONCEPTS:
        snapshot[c] = 0.1
    # M6 namjerno NE injectam — ne smije utjecati na preporuku

    engine.inject_mastery("user_advanced", snapshot)

    result = engine.recommend_next("user_advanced")

    assert result is not None
    concept, reason = result
    assert concept == "scalar_subquery"
    # 0.1 < 0.3 → weak; prereqs (where_filter, select_basic) mastered → weak_with_prereqs_met
    assert reason == "weak_with_prereqs_met"


# --- Test 4 (unit): all_prereqs(left_join) --------------------------------

def test_all_prereqs_left_join(engine: PrologEngine) -> None:
    """Tranzitivni prereqs za left_join moraju biti točno 6 čvorova iz grafa."""
    result = engine.all_prereqs("left_join")

    expected = {
        "inner_join", "null_handling", "join_condition",
        "from_clause", "where_filter", "select_basic",
    }
    assert set(result) == expected
    assert len(result) == 6


# --- Test 5 (unit): explain_recommendation reason string -----------------

def test_explain_recommendation_reason_for_novice(engine: PrologEngine) -> None:
    """Za user_novice (svi P_L=0.1), reason preporuke je 'weak_with_prereqs_met'."""
    snapshot = {c: 0.1 for c in ALL_30}
    engine.inject_mastery("user_novice", snapshot)

    result = engine.recommend_next("user_novice")

    assert result is not None
    _, reason = result
    assert reason == "weak_with_prereqs_met"
