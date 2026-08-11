#!/usr/bin/env python3
"""Provjera je li `lib/monaco-theme.ts` još u skladu s tokenima iz `index.css`.

    python3 scripts/a11y/monaco_check.py

🔴 ZAŠTO POSTOJI: `monaco-theme.ts` je **vrijednosna kopija** — HEX vrijednosti izvedene
iz oklch tokena, ne živi CSS. Monaco traži hex i ne vidi CSS varijable. Kad se paleta
promijeni, tema **tiho ostane stara**: editor i dalje radi, ničemu ne pukne build, a SQL
editor renderira staru paletu usred nove aplikacije.

Skripta NE mijenja `monaco-theme.ts` — samo javlja razliku. Izlazni kod 1 = ima drifta.

DODAVANJE NOVOG MAPIRANJA: upiši (ključ u temi, tema, token) u MAP. Ključ je ili
`rules[token=…].foreground` ili ime iz `colors`. Ako vrijednost NIJE čist token nego
kompozit/alpha (npr. `#F0B13533` = accent-warm @ 20 %), upiši je u ALPHA_SUFFIXED.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from palette import REPO, load_tokens  # noqa: E402

THEME = REPO / "frontend" / "src" / "lib" / "monaco-theme.ts"

#: (opis, spec, hex-u-datoteci). `spec` je izvor iz kojeg `palette.py` reproducira hex:
#:    "card"                    → čist token
#:    ("accent-warm", 0.20)     → token s alfom (8-znamenkasti hex)
#:    ("border", None, "card")  → kompozit tokena s alfom NAD plohom
#:    ("border", 0.40, "card")  → kompozit, pa još alfa preko njega
#: ⟳ 4.7 stage 1: light retci uklonjeni s light temom (oba tadašnja drifta bila su u
#: lightu → bespredmetna). ⟳ 4.7 stage 2: dodane alpha i kompozitne vrijednosti, pa je
#: NOT_DERIVED prazan i provjera pokriva SVAKI hex u datoteci.
MAP: list[tuple[str, object, str]] = [
    ("rules[''] / identifier / editor.foreground", "foreground", "F3F4FE"),
    ("rules[keyword]", "chart-1", "53A3F2"),
    ("rules[operator]", "neutral", "9DA5B1"),
    ("rules[delimiter] / comment / editorLineNumber", "muted-foreground", "9C9FB7"),
    ("rules[string]", "correct", "5DC879"),
    ("rules[number]", "chart-2", "36C6B8"),
    ("rules[predefined]", "chart-3", "B191EA"),
    ("editor.background / editorWidget.background", "card", "13142C"),
    ("editorCursor / editorLineNumber.activeForeground", "accent-warm", "F0B135"),
    ("editor.selectionBackground", ("accent-warm", 0.20), "F0B13533"),
    ("editor.inactiveSelectionBackground", ("accent-warm", 0.10), "F0B1351A"),
    ("editorBracketMatch.border", ("accent-warm", 0.50), "F0B13580"),
    ("editorSuggestWidget.selectedBackground", ("accent-warm", 0.15), "F0B13526"),
    ("editorIndentGuide.background / editorWidget.border", ("border", None, "card"), "2B2C46"),
    ("editor.lineHighlightBackground", ("border", 0.40, "card"), "2B2C4666"),
    ("scrollbarSlider.background", ("border", 0.50, "card"), "2B2C4680"),
    ("scrollbarSlider.hoverBackground", ("border", 0.80, "card"), "2B2C46CC"),
]

#: Vrijednosti u temi koje NISU izvedene ni iz jednog tokena.
#: 🔴 OD 4.7 STAGE 2 MORA BITI PRAZAN. Ručna vrijednost nema iz čega se preračunati pri
#: promjeni palete, pa je to kvar, a ne bilješka. Zadnja takva (`#292929`) zamijenjena je
#: kompozitom `--border` nad `--card`.
NOT_DERIVED: list[tuple[str, str, str]] = []


def derive(spec, t) -> str:
    """spec → hex (velikim slovima, bez #). Alfa daje 8 znamenki."""
    if isinstance(spec, str):
        return t[spec].hex().upper().lstrip("#")
    if len(spec) == 2:
        tok, alpha = spec
        return t[tok].hex().upper().lstrip("#") + f"{round(alpha * 255):02X}"
    tok, alpha, under = spec
    c = t[tok].over(t[under])
    h = c.hex().upper().lstrip("#")
    return h if alpha is None else h + f"{round(alpha * 255):02X}"


def spec_name(spec) -> str:
    if isinstance(spec, str):
        return f"--{spec}"
    if len(spec) == 2:
        return f"--{spec[0]} @ {round(spec[1] * 100)}%"
    tok, alpha, under = spec
    base = f"--{tok} nad --{under}"
    return base if alpha is None else f"{base} @ {round(alpha * 100)}%"


def main() -> int:
    tokens = load_tokens()
    t = tokens["dark"]
    src = THEME.read_text(encoding="utf-8")
    #: SVAKI hex koji je STVARNA VRIJEDNOST — dakle unutar navodnika. `rules` ih piše bez
    #: `#` (`foreground: "53A3F2"`), `colors` s njim. Navodnici su nužni jer se hex
    #: pojavljuje i u komentarima ovog modula (npr. bilješka o umirovljenom `#292929`),
    #: a komentar nije vrijednost — brojati ga značilo bi prijaviti kvar koji ne postoji.
    present = {
        m.upper() for m in re.findall(r"\"#?([0-9A-Fa-f]{8}|[0-9A-Fa-f]{6})\"", src)
    }

    print(f"Provjera {THEME.relative_to(REPO)} vs frontend/src/index.css\n")
    drift, missing, claimed = [], [], set()
    for desc, spec, in_file in MAP:
        tok = spec if isinstance(spec, str) else spec[0]
        if tok not in t:
            drift.append((desc, spec, in_file, "TOKEN NE POSTOJI"))
            continue
        derived = derive(spec, t)
        claimed.add(in_file.upper())
        if in_file.upper() not in present:
            missing.append((desc, in_file))
        ok = derived == in_file.upper()
        print(f"  {'OK ' if ok else 'DRIFT'}  {desc:<48} {spec_name(spec):<28} "
              f"u temi #{in_file.upper()}  izvedeno #{derived}")
        if not ok:
            drift.append((desc, spec, in_file, derived))

    # 🔴 Pokrivenost: hex koji MAP ne tvrdi je RUČNA vrijednost — kvar, ne bilješka.
    unclaimed = sorted(present - claimed)

    if NOT_DERIVED:
        print("\n  ⚠️  NIJE IZVEDENO IZ TOKENA:")
        for desc, hx, why in NOT_DERIVED:
            print(f"     {desc}\n        #{hx} — {why}")

    print()
    if missing:
        print("⚠️  HEX iz MAP-a više nije u datoteci (mapiranje je zastarjelo):")
        for desc, hx in missing:
            print(f"     {desc}: #{hx}")
        print()
    if unclaimed:
        print(f"🔴 RUČNE VRIJEDNOSTI: {len(unclaimed)} hex(ova) u temi nema izvor u MAP-u.")
        for hx in unclaimed:
            print(f"     #{hx}")
        print("\n   Vrijednost bez izvora ne može se preračunati pri promjeni palete —\n"
              "   upravo tako je #292929 preživio dvije promjene tokena. Ili je izvedi\n"
              "   iz tokena i upiši u MAP, ili je makni iz teme.")
    if drift:
        print(f"🔴 DRIFT: {len(drift)} vrijednosti se razilaze s tokenima.")
        for desc, spec, in_file, derived in drift:
            print(f"   {desc}: tema #{in_file.upper()} ≠ {spec_name(spec)} → #{derived}")
        print("\n   Monaco tema je vrijednosna kopija i NE prati CSS. Ažuriraj je svjesno.")
    if drift or unclaimed:
        return 1

    print(f"✅ Svih {len(present)} vrijednosti u temi izvedeno je iz tokena — nijedna ručna.")
    print("   Razlučivost sintaksnih boja MEĐUSOBNO mjeri se odvojeno:\n"
          "   `python3 scripts/a11y/contrast_matrix.py --delta-e` (skup MONACO u pairs.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
