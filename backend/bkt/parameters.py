"""BKT default parametri po tier-u + factory funkcije."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from bkt.model import BKT

if TYPE_CHECKING:
    from app.prolog.prolog_engine import PrologEngine

Tier = Literal["easy", "medium", "hard"]

TIER_DEFAULTS: dict[str, dict[str, float]] = {
    "easy": {"p_l0": 0.30, "p_t": 0.30, "p_g": 0.25, "p_s": 0.08},
    "medium": {"p_l0": 0.15, "p_t": 0.20, "p_g": 0.20, "p_s": 0.10},
    "hard": {"p_l0": 0.05, "p_t": 0.10, "p_g": 0.10, "p_s": 0.15},
}


def create_bkt_for_tier(tier: Tier) -> BKT:
    """Vrati BKT instancu s default parametrima za zadani tier."""
    if tier not in TIER_DEFAULTS:
        raise ValueError(f"Nepoznat tier: {tier!r}")
    p = TIER_DEFAULTS[tier]
    return BKT(p_l0=p["p_l0"], p_t=p["p_t"], p_g=p["p_g"], p_s=p["p_s"])


def create_bkt_for_concept(concept: str, engine: "PrologEngine") -> BKT:
    """Vrati BKT instancu za zadani koncept — tier dohvaćen iz Prolog ontologije."""
    tier = engine.get_tier(concept)
    return create_bkt_for_tier(tier)  # type: ignore[arg-type]
