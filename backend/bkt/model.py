"""BKT model — Corbett & Anderson (1994) posterior update."""

from __future__ import annotations

from dataclasses import dataclass

MASTERY_THRESHOLD = 0.85


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class BKT:
    """Bayesian Knowledge Tracing model za jedan koncept i jednog korisnika.

    Parametri prema Corbett & Anderson (1994):
    - p_l0: P(L₀) — prior vjerojatnost znanja prije prvog pokušaja
    - p_t: P(T) — vjerojatnost prijelaza iz neznanja u znanje
    - p_g: P(G) — vjerojatnost pogađanja (correct | not learned)
    - p_s: P(S) — vjerojatnost slip-a (incorrect | learned)

    Atribut `p_l` je trenutna posteriorna vjerojatnost znanja P(Lₙ).
    """

    p_l0: float
    p_t: float
    p_g: float
    p_s: float

    def __post_init__(self) -> None:
        for name, val in (
            ("p_l0", self.p_l0),
            ("p_t", self.p_t),
            ("p_g", self.p_g),
            ("p_s", self.p_s),
        ):
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"{name}={val} izvan [0,1]")
        self.p_l: float = self.p_l0

    def predict(self) -> float:
        """P(correct na sljedećem pokušaju) = P(L)·(1−P(S)) + (1−P(L))·P(G)."""
        return self.p_l * (1.0 - self.p_s) + (1.0 - self.p_l) * self.p_g

    def update(self, is_correct: bool) -> float:
        """Posteriorni update P(L) nakon promatranog odgovora.

        Vraća novu vrijednost p_l.
        """
        if is_correct:
            num = self.p_l * (1.0 - self.p_s)
            den = num + (1.0 - self.p_l) * self.p_g
        else:
            num = self.p_l * self.p_s
            den = num + (1.0 - self.p_l) * (1.0 - self.p_g)

        p_l_given_obs = num / den if den > 0.0 else self.p_l
        self.p_l = _clamp(p_l_given_obs + (1.0 - p_l_given_obs) * self.p_t)
        return self.p_l

    @property
    def is_mastered(self) -> bool:
        return self.p_l >= MASTERY_THRESHOLD

    def __repr__(self) -> str:
        return (
            f"BKT(p_l={self.p_l:.3f}, p_t={self.p_t:.3f}, "
            f"p_g={self.p_g:.3f}, p_s={self.p_s:.3f})"
        )
