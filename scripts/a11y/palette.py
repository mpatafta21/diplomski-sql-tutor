"""Konverzija oklch → sRGB + WCAG kontrast, uz ČITANJE tokena iz `frontend/src/index.css`.

🔴 Tokeni se NE hardkodiraju — čitaju se iz CSS-a pri svakom pokretanju. To je jedini
razlog zbog kojeg ova skripta preživi promjenu palete: kad se `index.css` promijeni,
mjerenje se mijenja s njim, bez ijedne izmjene ovdje.

Konvertor se pri svakom pokretanju VALIDIRA na brojkama koje su već objavljene u
dokumentaciji projekta (v. `SELF_TEST`). Ako validacija padne, skripta prekida —
neispravan konvertor koji tiho vraća brojke gori je od nikakvog (poučak #39).
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CSS = REPO / "frontend" / "src" / "index.css"

# ── oklch → sRGB ──────────────────────────────────────────────────────────


def _oklch_to_linear(L: float, C: float, h_deg: float) -> tuple[float, float, float]:
    h = math.radians(h_deg)
    a, b = C * math.cos(h), C * math.sin(h)
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_**3, m_**3, s_**3
    return (
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def _lin_to_srgb(c: float) -> float:
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def _srgb_to_lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


class Color:
    """sRGB boja u rasponu 0..1 + alpha."""

    __slots__ = ("rgb", "alpha", "name")

    def __init__(self, rgb, alpha: float = 1.0, name: str = ""):
        self.rgb, self.alpha, self.name = rgb, alpha, name

    @classmethod
    def oklch(cls, L: float, C: float = 0.0, h: float = 0.0, alpha: float = 1.0, name: str = ""):
        return cls(tuple(_lin_to_srgb(v) for v in _oklch_to_linear(L, C, h)), alpha, name)

    def over(self, bg: "Color", name: str | None = None) -> "Color":
        """Alpha-kompozitiranje preko neprozirne podloge."""
        a = self.alpha
        return Color(
            tuple(a * s + (1 - a) * b for s, b in zip(self.rgb, bg.rgb)),
            1.0,
            name or f"{self.name} nad {bg.name}",
        )

    def with_alpha(self, a: float, name: str | None = None) -> "Color":
        return Color(self.rgb, self.alpha * a, name or f"{self.name}/{round(a * 100)}")

    def luminance(self) -> float:
        r, g, b = (_srgb_to_lin(c) for c in self.rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def hex(self) -> str:
        return "#" + "".join(f"{round(c * 255):02x}" for c in self.rgb)

    def __repr__(self) -> str:
        return f"Color({self.name or self.hex()})"


def contrast(a: Color, b: Color) -> float:
    """WCAG omjer kontrasta. Obje boje moraju biti NEPROZIRNE (kompozitiraj prije)."""
    l1, l2 = a.luminance(), b.luminance()
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def fmt(x: float) -> str:
    """Hrvatski decimalni zarez, dvije decimale — kao u dokumentaciji projekta."""
    return f"{x:.2f}".replace(".", ",")


# ── čitanje tokena iz index.css ───────────────────────────────────────────

_OKLCH = re.compile(
    r"oklch\(\s*([0-9.]+)%?\s+([0-9.]+)\s+([0-9.]+)\s*(?:/\s*([0-9.]+)%\s*)?\)"
)
_DECL = re.compile(r"^\s*(--[a-z0-9-]+)\s*:\s*(oklch\([^)]*\))\s*;", re.MULTILINE)


def _parse_block(css: str, start: int, end: int) -> dict[str, Color]:
    out: dict[str, Color] = {}
    for m in _DECL.finditer(css, start, end):
        name, value = m.group(1), m.group(2)
        v = _OKLCH.search(value)
        if not v:
            continue
        L = float(v.group(1))
        if "%" in value.split()[0] or L > 1.5:  # oklch(52.8% …) oblik
            L /= 100.0
        alpha = float(v.group(4)) / 100.0 if v.group(4) else 1.0
        out[name[2:]] = Color.oklch(L, float(v.group(2)), float(v.group(3)), alpha, name[2:])
    return out


def load_tokens(css_path: Path = CSS) -> dict[str, dict[str, Color]]:
    """Vrati {'light': {...}, 'dark': {...}} iz `:root` i `.dark` blokova."""
    css = css_path.read_text(encoding="utf-8")
    root = css.index("\n:root {")
    dark = css.index("\n.dark {")
    base = css.index("\n@layer base") if "\n@layer base" in css else len(css)
    if not root < dark < base:
        raise SystemExit(
            f"🔴 {css_path.name}: očekivan redoslijed `:root` → `.dark` → `@layer base` "
            f"nije nađen (offseti {root}/{dark}/{base}). Struktura CSS-a se promijenila — "
            f"provjeri parser prije nego vjeruješ brojkama."
        )
    return {
        "light": _parse_block(css, root, dark),
        "dark": _parse_block(css, dark, base),
    }


# ── samotest konvertora ───────────────────────────────────────────────────

#: (opis, tema, token, ploha-token, očekivano). Sve brojke su VEĆ OBJAVLJENE u
#: dokumentaciji projekta prije nego je ova skripta postojala.
SELF_TEST = [
    ("foreground × card", "light", "foreground", "card", "19,79"),
    ("foreground × card", "dark", "foreground", "card", "17,16"),
    ("muted-foreground × card", "dark", "muted-foreground", "card", "6,91"),
    ("ring × card", "dark", "ring", "card", "3,79"),
    ("correct × correct-soft", "light", "correct", "correct-soft", "4,67"),
    ("partial × partial-soft", "dark", "partial", "partial-soft", "8,03"),
]


def self_test(tokens: dict[str, dict[str, Color]], verbose: bool = False) -> None:
    """Prekini ako konvertor ne reproducira već objavljene brojke."""
    bad = []
    for desc, theme, tok, surf, expected in SELF_TEST:
        t = tokens[theme]
        if tok not in t or surf not in t:
            bad.append(f"{desc} [{theme}]: token nedostaje u index.css")
            continue
        got = fmt(contrast(t[tok], t[surf]))
        if verbose:
            print(f"    {desc:<28} [{theme:<5}] {got}  (očekivano {expected})")
        if got != expected:
            bad.append(f"{desc} [{theme}]: dobiveno {got}, očekivano {expected}")
    if bad:
        print("🔴 SAMOTEST KONVERTORA PAO — mjerenje se NE izvodi:", file=sys.stderr)
        for b in bad:
            print(f"   • {b}", file=sys.stderr)
        print(
            "\n   Ako je promjena tokena namjerna, ažuriraj SELF_TEST u palette.py\n"
            "   uz obrazloženje — ali TEK nakon što je nova brojka provjerena ručno.",
            file=sys.stderr,
        )
        sys.exit(2)
