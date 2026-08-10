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


# ── gamut: klampanje se PRIJAVLJUJE, ne prešućuje ─────────────────────────

#: {(ime, L, C, h): C_max_u_gamutu} — puni se pri parsiranju CSS-a.
#: 🔴 Ključ MORA nositi i vrijednosti: isti token ima različitu vrijednost po temi, a
#: dedupliciranje samo po imenu sakrilo bi drugu (light `--destructive` je sakrio dark).
GAMUT_WARNINGS: dict[tuple[str, float, float, float], float] = {}


def max_chroma_in_gamut(L: float, h: float, hi: float = 0.5) -> float:
    """Najveća chroma koja na (L, h) još stane u sRGB. Bisekcija, 60 koraka."""
    lo = 0.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if all(-1e-9 <= v <= 1 + 1e-9 for v in _oklch_to_linear(L, mid, h)):
            lo = mid
        else:
            hi = mid
    return lo


def _check_gamut(L: float, C: float, h: float, name: str) -> None:
    """🔴 `_lin_to_srgb` tiho klampa na [0,1]. Boja izvan gamuta zato NE bi pukla —
    vratila bi brojku za boju koja NIJE deklarirana. Alat koji tiho laže gori je od
    alata koji ne postoji (isti poučak kao #39: guard netestiran u oba smjera)."""
    key = (name, L, C, h)
    if not name or key in GAMUT_WARNINGS:
        return
    if all(-1e-9 <= v <= 1 + 1e-9 for v in _oklch_to_linear(L, C, h)):
        return
    GAMUT_WARNINGS[key] = max_chroma_in_gamut(L, h)


class Color:
    """sRGB boja u rasponu 0..1 + alpha."""

    __slots__ = ("rgb", "alpha", "name")

    def __init__(self, rgb, alpha: float = 1.0, name: str = ""):
        self.rgb, self.alpha, self.name = rgb, alpha, name

    @classmethod
    def oklch(cls, L: float, C: float = 0.0, h: float = 0.0, alpha: float = 1.0, name: str = ""):
        _check_gamut(L, C, h, name)
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


def oklab(c: Color) -> tuple[float, float, float]:
    """sRGB → Oklab (L, a, b). Ulaz mora biti NEPROZIRAN (kompozitiraj prije)."""
    lr, lg, lb = (_srgb_to_lin(v) for v in c.rgb)
    l = 0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb
    m = 0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb
    s = 0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb
    l_, m_, s_ = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def delta_e(a: Color, b: Color) -> float:
    """ΔE_ok — euklidska udaljenost u Oklabu.

    🔴 Odgovara na DRUGO pitanje nego `contrast()`: ne „vidi li se ovo na ovome" nego
    „razlikuju li se ovo dvoje". Koristi se za cross-scale guard (MASTER §2.7), i to
    ISKLJUČIVO nad sukorištenim parovima — v. `pairs.CO_USED_EXTRA` i NALAZ N-12.
    """
    return math.dist(oklab(a), oklab(b))


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
    """Vrati `{'dark': {...}}` iz jedinog `:root` bloka.

    🔴 Aplikacija je od Faze 4.7 DARK-ONLY: `.dark` blok više ne postoji, svi su tokeni u
    `:root`. Rječnik zadržava ključ teme (a ne vraća gol `dict[str, Color]`) namjerno —
    `contrast_matrix.py` petlja po temama, pa bi promjena oblika povukla izmjene svugdje
    radi ničega. Ključ je `dark` jer to i jest jedina tema, ne `default`: ime govori ŠTO
    se mjeri, a ne da tema ima ime.

    Parser i dalje PREKIDA ako struktura CSS-a nije očekivana — bolje pad nego tihe krive
    brojke.
    """
    css = css_path.read_text(encoding="utf-8")
    if "\n.dark {" in css:
        raise SystemExit(
            f"🔴 {css_path.name}: nađen `.dark` blok. Aplikacija je dark-only od 4.7 i svi "
            f"tokeni pripadaju u `:root`. Ako se light tema vraća, vrati i dvotemni parser "
            f"— ali svjesno, ne tako da ovaj tiho pročita samo pola palete."
        )
    root = css.index("\n:root {")
    base = css.index("\n@layer base") if "\n@layer base" in css else len(css)
    if not root < base:
        raise SystemExit(
            f"🔴 {css_path.name}: očekivan redoslijed `:root` → `@layer base` nije nađen "
            f"(offseti {root}/{base}). Struktura CSS-a se promijenila — provjeri parser "
            f"prije nego vjeruješ brojkama."
        )
    out = {"dark": _parse_block(css, root, base)}
    report_gamut()
    return out


def report_gamut(stream=sys.stderr) -> int:
    """Glasno prijavi svaki token izvan sRGB gamuta. Vrati broj takvih tokena.

    NE prekida izvođenje: brojke su i dalje upotrebljive (razlika je ispod praga
    vidljivosti), ali tvrdnja „izmjereno na vrijednosti X" prestaje biti točna, pa se
    razlika mora vidjeti. Tiho klampanje je isto što i nemjerenje.
    """
    if not GAMUT_WARNINGS:
        return 0
    print("\n⚠️  IZVAN sRGB GAMUTA — `_lin_to_srgb` klampa, mjeri se KLAMPANA boja:",
          file=stream)
    for (name, L, C, h), cmax in sorted(GAMUT_WARNINGS.items()):
        print(f"   • --{name}: oklch({L} {C} {h}) — višak chrome {C - cmax:+.4f} "
              f"(maksimum u gamutu na toj svjetlini i hueu: {cmax:.4f})", file=stream)
    print("   Ili spusti chromu na navedeni maksimum, ili svjesno prihvati razliku —\n"
          "   ali je ne prešućuj (v. ERRATA #52).", file=stream)
    return len(GAMUT_WARNINGS)


# ── samotest konvertora ───────────────────────────────────────────────────

#: (opis, tema, token, ploha-token, očekivano). Sve brojke su VEĆ OBJAVLJENE u
#: dokumentaciji projekta prije nego je ova skripta postojala.
#:
#: ⟳ 4.7 stage 1: tri LIGHT retka uklonjena jer light teme više nema. Zamijenjena su
#: trima DARK retcima iz iste objavljene tablice (`docs/faza-4.7-kontrast-matrica.md`,
#: retci 141/145/136) — broj provjera ostaje šest, pokrivenost se ne smanjuje.
#:
#: ⟳ 4.7 stage 2 (ink-indigo paleta): tri KROMA retka su pala jer su im se tokeni
#: namjerno promijenili. Nove brojke provjerene ručno prije upisa:
#:    foreground × card        17,16 → 16,46  (foreground 0.985→0.970, card dobio tintu)
#:    muted-foreground × card   6,91 →  6,89  (L nepromijenjen, razlika je čista kroma)
#:    ring × card               3,79 →  4,94  (ring 0.556→0.620 akromatski, N-12)
#: Tri SEMANTIČKA retka nisu ni zatitrala (7,74 · 5,72 · 8,03) — to je ujedno i dokaz
#: da redizajn nije dirnuo zamrznute tokene.
SELF_TEST = [
    ("foreground × card", "dark", "foreground", "card", "16,46"),
    ("muted-foreground × card", "dark", "muted-foreground", "card", "6,89"),
    ("ring × card", "dark", "ring", "card", "4,94"),
    ("correct × correct-soft", "dark", "correct", "correct-soft", "7,74"),
    ("incorrect × incorrect-soft", "dark", "incorrect", "incorrect-soft", "5,72"),
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
