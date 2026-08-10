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

#: (opis, tema, token, hex-u-datoteci) — izvedeno iz komentara u monaco-theme.ts (4.1b).
#: ⟳ 4.7 stage 1: light retci uklonjeni s light temom. Dva drifta koja su ovdje
#: stajala od commita 5994107 bila su OBA u lightu → bespredmetni, ne popravljaju se.
MAP: list[tuple[str, str, str, str]] = [
    ("rules[''] / editor.foreground", "dark", "foreground", "FAFAFA"),
    ("rules[keyword]", "dark", "chart-1", "53A3F2"),
    ("rules[operator]", "dark", "neutral", "9DA5B1"),
    ("rules[string]", "dark", "correct", "5DC879"),
    ("rules[number]", "dark", "chart-2", "36C6B8"),
    ("rules[comment] / editorLineNumber", "dark", "muted-foreground", "A1A1A1"),
    ("rules[predefined]", "dark", "chart-3", "B191EA"),
    ("editor.background", "dark", "card", "171717"),
    ("editorLineNumber.activeForeground / cursor", "dark", "accent-warm", "F0B135"),
]


#: Vrijednosti u temi koje NISU izvedene ni iz jednog aktualnog tokena — ručno odabrane.
#: Prijavljuju se posebno: nisu „drift", ali kod redizajna palete NEMAJU izvor iz kojeg
#: bi se preračunale, pa ih treba odlučiti ručno.
NOT_DERIVED: list[tuple[str, str, str, str]] = [
    (
        "editorIndentGuide / widget.border / lineHighlight / scrollbar",
        "dark",
        "292929",
        "komentar u monaco-theme.ts:48-49 pripisuje ga tokenu --border, ali dark --border "
        "je oklch(1 0 0 / 10%) → bijela s alfom, a #292929 = oklch(0.279 0 0), što nije "
        "nijedan token (najbliži --muted oklch(0.269) daje #262626)",
    ),
]


def main() -> int:
    tokens = load_tokens()
    src = THEME.read_text(encoding="utf-8")
    present = {m.upper() for m in re.findall(r"#?([0-9A-Fa-f]{6})(?:[0-9A-Fa-f]{2})?\b", src)}

    print(f"Provjera {THEME.relative_to(REPO)} vs frontend/src/index.css\n")
    drift, missing = [], []
    for desc, theme, token, in_file in MAP:
        t = tokens[theme]
        if token not in t:
            drift.append((desc, theme, token, in_file, "TOKEN NE POSTOJI"))
            continue
        derived = t[token].hex().upper().lstrip("#")
        ok = derived == in_file.upper()
        if in_file.upper() not in present:
            missing.append((desc, theme, in_file))
        status = "OK " if ok else "DRIFT"
        print(
            f"  {status}  [{theme:<5}] {desc:<42} --{token:<18} "
            f"u temi #{in_file.upper()}  iz tokena #{derived}"
        )
        if not ok:
            drift.append((desc, theme, token, in_file, derived))

    if NOT_DERIVED:
        print("\n  ⚠️  NIJE IZVEDENO IZ TOKENA (ručno odabrano — kod redizajna nema izvor):")
        for desc, theme, hx, why in NOT_DERIVED:
            print(f"     [{theme}] {desc}\n        #{hx} — {why}")

    print()
    if missing:
        print("⚠️  HEX iz MAP-a više nije u datoteci (mapiranje je zastarjelo):")
        for desc, theme, hx in missing:
            print(f"     [{theme}] {desc}: #{hx}")
        print()
    if drift:
        print(f"🔴 DRIFT: {len(drift)} vrijednosti se razilaze s tokenima.")
        for desc, theme, token, in_file, derived in drift:
            print(f"   [{theme}] {desc}: tema #{in_file.upper()} ≠ --{token} → #{derived}")
        print(
            "\n   Monaco tema je vrijednosna kopija i NE prati CSS. Ažuriraj je svjesno\n"
            "   (i provjeri kontrast u editoru), ne automatski — boje sintakse imaju\n"
            "   dodatni zahtjev razlučivosti MEĐUSOBNO, koji ova skripta ne mjeri."
        )
        return 1

    print("✅ Sve mapirane vrijednosti poklapaju se s tokenima.")
    print(
        "   Napomena: poklapanje s tokenima NIJE isto što i čitljivost sintakse —\n"
        "   međusobna razlučivost boja tokena (keyword vs string vs number) nije\n"
        "   pokrivena ovom provjerom."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
