"""Testovi za BKT model — Marko scenario iz §5.5 + rubni slučajevi."""

from __future__ import annotations

import math

import pytest

from bkt.model import BKT
from bkt.parameters import TIER_DEFAULTS, create_bkt_for_tier


def test_marko_scenario_hard_tier():
    """§5.5: hard defaults, 3 pokušaja (incorrect, correct, correct)."""
    bkt = BKT(p_l0=0.05, p_t=0.10, p_g=0.10, p_s=0.15)
    p_l1 = bkt.update(is_correct=False)
    assert p_l1 == pytest.approx(0.107, abs=0.01)
    p_l2 = bkt.update(is_correct=True)
    assert p_l2 == pytest.approx(0.554, abs=0.01)
    p_l3 = bkt.update(is_correct=True)
    assert p_l3 == pytest.approx(0.922, abs=0.01)
    assert bkt.is_mastered is True


def test_tier_defaults_match_spec():
    assert TIER_DEFAULTS["easy"] == {"p_l0": 0.30, "p_t": 0.30, "p_g": 0.25, "p_s": 0.08}
    assert TIER_DEFAULTS["medium"] == {"p_l0": 0.15, "p_t": 0.20, "p_g": 0.20, "p_s": 0.10}
    assert TIER_DEFAULTS["hard"] == {"p_l0": 0.05, "p_t": 0.10, "p_g": 0.10, "p_s": 0.15}


def test_create_bkt_for_tier_factory():
    for tier, params in TIER_DEFAULTS.items():
        bkt = create_bkt_for_tier(tier)  # type: ignore[arg-type]
        assert bkt.p_l == pytest.approx(params["p_l0"])
        assert bkt.p_t == pytest.approx(params["p_t"])
        assert bkt.p_g == pytest.approx(params["p_g"])
        assert bkt.p_s == pytest.approx(params["p_s"])


def test_predict_on_mastered_user():
    bkt = BKT(p_l0=0.95, p_t=0.10, p_g=0.10, p_s=0.10)
    assert bkt.predict() > 0.80


def test_clamp_upper_bound():
    bkt = BKT(p_l0=0.999, p_t=0.30, p_g=0.10, p_s=0.05)
    for _ in range(5):
        p = bkt.update(is_correct=True)
        assert 0.0 <= p <= 1.0


def test_clamp_lower_bound():
    bkt = BKT(p_l0=0.05, p_t=0.10, p_g=0.10, p_s=0.15)
    for _ in range(10):
        p = bkt.update(is_correct=False)
        assert p >= 0.0


def test_mastery_reached_after_consecutive_correct():
    for tier in ("easy", "medium", "hard"):
        bkt = create_bkt_for_tier(tier)  # type: ignore[arg-type]
        for _ in range(10):
            bkt.update(is_correct=True)
        assert bkt.is_mastered, f"tier={tier} not mastered"


def test_repr_contains_all_params():
    bkt = BKT(p_l0=0.15, p_t=0.20, p_g=0.20, p_s=0.10)
    r = repr(bkt)
    for token in ("p_l", "p_t", "p_g", "p_s"):
        assert token in r


def test_create_bkt_for_concept_left_join_is_hard():
    """left_join je tier=hard → p_l0=0.05."""
    from app.prolog.prolog_engine import PrologEngine

    from bkt.parameters import create_bkt_for_concept

    with PrologEngine() as engine:
        bkt = create_bkt_for_concept("left_join", engine)
    assert bkt.p_l == pytest.approx(0.05)
    assert bkt.p_t == pytest.approx(0.10)
