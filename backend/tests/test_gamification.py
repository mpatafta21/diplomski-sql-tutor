"""TDD testovi za agents/gamification_logic.py — Faza 3D.1.

Čista logika GamificationAgenta: XP, leveli, mastery prag, streak, badge eval.
ZERO I/O — bez DB/SPADE/Prolog, sve funkcije su deterministične.

KLJUČNO za otpornost na mentor-pending brojeve (TODO(mentor F2x)):
asercije se grade kompozicijom preko konstanti, NE hardkodiranjem nepotvrđenih
XP vrijednosti. Iznimka su dva ANCHOR testa iz §3.4 (difficulty=1 fiksiran na 10)
i pin round-half-up ponašanja.
"""

from __future__ import annotations

import math
from datetime import date, timedelta

import pytest

from agents.gamification_logic import (
    EXPLORER_MODULES,
    FIRST_ATTEMPT_BONUS,
    FIRST_ATTEMPT_BONUS_FLOOR,
    JOIN_CONCEPTS,
    LEVEL_STEP,
    MASTERY_THRESHOLD,
    VERDICT_FACTOR,
    XP_BASE_BY_DIFFICULTY,
    BadgeFacts,
    compute_xp,
    eval_badges,
    level_for_xp,
    mastered_concepts,
    progress_to_next_level,
    streak_from_active_dates,
)

# ======================================================================
# XP
# ======================================================================


def test_compute_xp_anchor_first_attempt():
    # §3.4 worked example: difficulty=1, prvi pokušaj, ×2.0 → 20 XP.
    assert compute_xp(1, "correct", 1) == 20


def test_compute_xp_anchor_second_attempt():
    # §3.4 worked example (linija 442): difficulty=1, drugi pokušaj, ×1.5 → 15 XP.
    assert compute_xp(1, "correct", 2) == 15


def test_compute_xp_incorrect_is_zero():
    # verdict=incorrect → faktor 0.0 → 0 XP neovisno o difficulty/bonusu.
    assert compute_xp(5, "incorrect", 1) == 0


@pytest.mark.parametrize("difficulty", [1, 2, 3, 4, 5])
def test_compute_xp_composition_correct(difficulty):
    # Kompozicija preko konstanti — preživljava promjenu mentor-brojeva.
    base = XP_BASE_BY_DIFFICULTY[difficulty]
    for attempt, bonus in (
        (1, FIRST_ATTEMPT_BONUS[1]),
        (2, FIRST_ATTEMPT_BONUS[2]),
        (3, FIRST_ATTEMPT_BONUS_FLOOR),
        (7, FIRST_ATTEMPT_BONUS_FLOOR),
    ):
        expected = math.floor(base * VERDICT_FACTOR["correct"] * bonus + 0.5)
        assert compute_xp(difficulty, "correct", attempt) == expected


def test_compute_xp_bonus_decay_monotonic():
    # 1. pokušaj nosi >= XP od 2., a 2. >= 3.+ (za pozitivan faktor).
    xp1 = compute_xp(3, "correct", 1)
    xp2 = compute_xp(3, "correct", 2)
    xp3 = compute_xp(3, "correct", 3)
    xp9 = compute_xp(3, "correct", 9)
    assert xp1 >= xp2 >= xp3
    assert xp3 == xp9  # attempt_number >= 3 koristi isti floor


def test_compute_xp_partial_round_half_up():
    # Pin: .5 se zaokružuje GORE (round-half-up), ne banker's, ne dolje.
    base = XP_BASE_BY_DIFFICULTY[1]
    factor = VERDICT_FACTOR["partial"]
    bonus = FIRST_ATTEMPT_BONUS[2]
    raw = base * factor * bonus
    expected = math.floor(raw + 0.5)
    assert compute_xp(1, "partial", 2) == expected
    # Kad je raw točno N.5, mora ići na N+1 (a ne N kao banker's rounding).
    if raw - math.floor(raw) == 0.5:
        assert expected == math.floor(raw) + 1


def test_compute_xp_unknown_verdict_raises():
    with pytest.raises(ValueError):
        compute_xp(1, "bogus", 1)


def test_compute_xp_unknown_difficulty_raises():
    with pytest.raises(ValueError):
        compute_xp(6, "correct", 1)


# ======================================================================
# LEVEL
# ======================================================================


@pytest.mark.parametrize(
    "xp, expected_level",
    [(0, 1), (99, 1), (100, 2), (285, 3), (300, 4)],
)
def test_level_for_xp(xp, expected_level):
    assert level_for_xp(xp) == expected_level
    # Konzistentno s LEVEL_STEP formulom.
    assert level_for_xp(xp) == 1 + xp // LEVEL_STEP


def test_progress_to_next_level_mid():
    level, in_level, to_next = progress_to_next_level(285)
    assert (level, in_level, to_next) == (3, 85, 15)


def test_progress_to_next_level_boundary():
    # Točno na pragu levela: 0 u levelu, pun korak do iduceg.
    level, in_level, to_next = progress_to_next_level(300)
    assert (level, in_level, to_next) == (4, 0, LEVEL_STEP)
    assert in_level + to_next == LEVEL_STEP


# ======================================================================
# MASTERY
# ======================================================================


def test_mastered_concepts_threshold_boundary():
    snapshot = {
        "at_threshold": MASTERY_THRESHOLD,
        "above": MASTERY_THRESHOLD + 0.05,
        "below": MASTERY_THRESHOLD - 0.0001,
    }
    assert mastered_concepts(snapshot) == frozenset({"at_threshold", "above"})


def test_mastered_concepts_empty():
    assert mastered_concepts({}) == frozenset()


# ======================================================================
# STREAK
# ======================================================================


def test_streak_today_only():
    today = date(2026, 6, 27)
    assert streak_from_active_dates({today}, today) == (1, 1)


def test_streak_three_consecutive():
    today = date(2026, 6, 27)
    dates = {today, today - timedelta(days=1), today - timedelta(days=2)}
    assert streak_from_active_dates(dates, today) == (3, 3)


def test_streak_gap_resets_current():
    today = date(2026, 6, 27)
    # today, today-1 nepoprekidni, pa rupa na today-2, pa today-3.
    dates = {today, today - timedelta(days=1), today - timedelta(days=3)}
    current, longest = streak_from_active_dates(dates, today)
    assert current == 2
    assert longest == 2


def test_streak_longest_exceeds_current():
    today = date(2026, 6, 27)
    # 5 starih uzastopnih (završavaju na today-7..today-3), pa rupa, pa 2 nova.
    old = {today - timedelta(days=d) for d in (7, 6, 5, 4, 3)}
    new = {today, today - timedelta(days=1)}
    current, longest = streak_from_active_dates(old | new, today)
    assert current == 2
    assert longest == 5


def test_streak_asserts_today_present():
    today = date(2026, 6, 27)
    with pytest.raises(AssertionError):
        streak_from_active_dates({today - timedelta(days=1)}, today)


# ======================================================================
# BADGES
# ======================================================================


def _facts(**kw) -> BadgeFacts:
    base = dict(
        has_correct=False,
        mastered=frozenset(),
        current_streak=0,
        attempted_modules=frozenset(),
    )
    base.update(kw)
    return BadgeFacts(**base)


def test_badge_first_correct():
    assert eval_badges(_facts(has_correct=True)) == frozenset({"first_correct"})


def test_badge_join_master_full():
    assert eval_badges(_facts(mastered=JOIN_CONCEPTS)) == frozenset({"join_master"})


def test_badge_join_master_partial_no():
    # 2/3 join koncepata → NE dobiva join_master.
    two = frozenset(list(JOIN_CONCEPTS)[:2])
    assert "join_master" not in eval_badges(_facts(mastered=two))


def test_badge_null_ninja():
    assert eval_badges(_facts(mastered=frozenset({"null_handling"}))) == frozenset(
        {"null_ninja"}
    )


def test_badge_streak_7():
    assert eval_badges(_facts(current_streak=7)) == frozenset({"streak_7"})
    assert "streak_7" not in eval_badges(_facts(current_streak=6))


def test_badge_explorer_boundary():
    assert "explorer" not in eval_badges(_facts(attempted_modules=frozenset({1, 2, 3, 4, 5})))
    assert eval_badges(_facts(attempted_modules=EXPLORER_MODULES)) == frozenset(
        {"explorer"}
    )


def test_badge_empty_facts():
    assert eval_badges(_facts()) == frozenset()


def test_badge_multiple_simultaneous():
    facts = _facts(
        has_correct=True,
        mastered=JOIN_CONCEPTS | {"null_handling"},
        current_streak=7,
        attempted_modules=EXPLORER_MODULES,
    )
    assert eval_badges(facts) == frozenset(
        {"first_correct", "join_master", "null_ninja", "streak_7", "explorer"}
    )
