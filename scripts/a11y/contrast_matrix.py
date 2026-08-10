#!/usr/bin/env python3
"""Matrica kontrasta tekst-token × ploha — jedna naredba, pun izlaz, obje teme.

    python3 scripts/a11y/contrast_matrix.py                  # tablica u terminal
    python3 scripts/a11y/contrast_matrix.py --md > out.md    # markdown
    python3 scripts/a11y/contrast_matrix.py --pair muted-foreground incorrect-soft
    python3 scripts/a11y/contrast_matrix.py --theme light

Izlazni kod: 0 = svi parovi prolaze · 1 = barem jedan pad · 2 = samotest konvertora pao.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pairs import (  # noqa: E402
    AA_NON_TEXT,
    AA_TEXT,
    CHIPS,
    GRAPHIC_ONLY,
    PAIRS,
    SURFACE_USE,
    SURFACE_VS_SURROUND,
    SURFACES,
)
from palette import Color, contrast, fmt, load_tokens, self_test  # noqa: E402

CMD = "python3 scripts/a11y/contrast_matrix.py"


def resolve_surface(spec, tokens: dict[str, Color]) -> Color:
    """Ime tokena → Color; (token, alpha, ploha) → kompozit nad plohom."""
    if isinstance(spec, str):
        return tokens[spec]
    tok, alpha, under = spec
    return tokens[tok].with_alpha(alpha).over(tokens[under])


def build(theme: str, tokens_all) -> tuple[list[tuple], list[tuple]]:
    """Vrati (retci, padovi) za jednu temu."""
    t = tokens_all[theme]
    rows, fails = [], []
    for sname, spec in SURFACES.items():
        if sname not in PAIRS:
            continue
        surf = resolve_surface(spec, t)
        for text_tok, proof in PAIRS[sname].items():
            if text_tok not in t:
                rows.append((sname, text_tok, proof, None, None, "TOKEN NE POSTOJI"))
                fails.append((theme, sname, text_tok, "—", proof))
                continue
            r = contrast(t[text_tok], surf)
            thr = AA_NON_TEXT if (sname, text_tok) in GRAPHIC_ONLY else AA_TEXT
            ok = r >= thr
            rows.append((sname, text_tok, proof, r, thr, "PASS" if ok else "FAIL"))
            if not ok:
                fails.append((theme, sname, text_tok, fmt(r), proof))
    return rows, fails


def chip_rows(theme: str, tokens_all):
    t = tokens_all[theme]
    out, fails = [], []
    for fg, bg in CHIPS:
        if fg not in t or bg not in t:
            continue
        r = contrast(t[fg], t[bg])
        out.append((fg, bg, r, r >= AA_TEXT))
        if r < AA_TEXT:
            fails.append((theme, bg, fg, fmt(r), "● vlastiti fill"))
    return out, fails


def surround_rows(theme: str, tokens_all):
    t = tokens_all[theme]
    out = []
    for sname, under in SURFACE_VS_SURROUND:
        surf = resolve_surface(SURFACES[sname], t)
        r = contrast(surf, t[under])
        out.append((sname, under, r, r >= AA_NON_TEXT))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", action="store_true", help="markdown umjesto terminalskog ispisa")
    ap.add_argument("--theme", choices=["light", "dark"], help="samo jedna tema")
    ap.add_argument("--pair", nargs=2, metavar=("TEKST", "PLOHA"), help="jedan par")
    ap.add_argument("--quiet-selftest", action="store_true")
    a = ap.parse_args()

    tokens = load_tokens()
    self_test(tokens, verbose=not a.quiet_selftest and not a.md)

    themes = [a.theme] if a.theme else ["light", "dark"]

    if a.pair:
        text_tok, sname = a.pair
        if sname not in SURFACES:
            print(f"🔴 nepoznata ploha {sname!r}. Poznate: {', '.join(SURFACES)}", file=sys.stderr)
            return 2
        bad = False
        for th in themes:
            t = tokens[th]
            if text_tok not in t:
                print(f"🔴 token {text_tok!r} ne postoji u {th} temi", file=sys.stderr)
                return 2
            surf = resolve_surface(SURFACES[sname], t)
            r = contrast(t[text_tok], surf)
            thr = AA_NON_TEXT if (sname, text_tok) in GRAPHIC_ONLY else AA_TEXT
            ok = r >= thr
            bad |= not ok
            print(
                f"{th:<5} {text_tok} na {sname} ({surf.hex()}): "
                f"{fmt(r)}:1  prag {fmt(thr)}  {'PASS ✅' if ok else 'FAIL ❌'}"
            )
        return 1 if bad else 0

    all_fails = []
    out = []
    if a.md:
        out += [
            "# Faza 4.7 — MATRICA KONTRASTA: tekst-token × ploha",
            "",
            f"**Generirano:** {date.today().isoformat()} · **naredba:** `{CMD} --md`",
            "",
            "> ⚠️ Vrijedi za **stanje koda na taj datum**. Tokeni se čitaju iz",
            "> `frontend/src/index.css` pri svakom pokretanju — nakon svake promjene palete",
            "> ovaj dokument treba **regenerirati istom naredbom**, ne ručno ispravljati.",
            "",
            "**Metoda:** oklch → Oklab → linearni sRGB → sRGB → relativna luminancija → WCAG",
            "omjer. Alpha se **kompozitira** nad navedenom plohom. Konvertor se pri svakom",
            "pokretanju validira na već objavljenim brojkama projekta (`SELF_TEST` u",
            "`scripts/a11y/palette.py`); ako validacija padne, mjerenje se ne izvodi.",
            "",
            f"**Pragovi:** tekst **{fmt(AA_TEXT)}:1** · grafika i stanja **{fmt(AA_NON_TEXT)}:1** (SC 1.4.11).",
            "",
            "**Parovi nisu kartezijev produkt** — mjeri se samo par koji u kodu postoji:",
            "**●** ploha i tekst u istom `className` · **○** tekst u podstablu elementa koji",
            "nosi plohu. Popis i citati: `scripts/a11y/pairs.py`.",
            "",
        ]
    for th in themes:
        rows, fails = build(th, tokens)
        chips, cfails = chip_rows(th, tokens)
        surr = surround_rows(th, tokens)
        all_fails += fails + cfails
        if a.md:
            out += ["---", "", f"## {th.upper()}", "",
                    "| ploha | gdje se koristi | tekst token | dokaz | omjer | |",
                    "|---|---|---|---|---|---|"]
            for sname, tok, proof, r, thr, st in rows:
                val = fmt(r) if r is not None else "—"
                mark = "✅" if st == "PASS" else "❌"
                out.append(
                    f"| `{sname}` | {SURFACE_USE.get(sname, '')} | `{tok}` | {proof} | {val} | {mark} |"
                )
            out += ["", f"### {th.upper()} — čipovi (vlastiti `-foreground` na vlastitom fillu)", "",
                    "| tekst | ploha | omjer | |", "|---|---|---|---|"]
            for fg, bg, r, ok in chips:
                out.append(f"| `{fg}` | `{bg}` | {fmt(r)} | {'✅' if ok else '❌'} |")
            out += ["", f"### {th.upper()} — ploha vs okolina (prag {fmt(AA_NON_TEXT)}, SC 1.4.11)", "",
                    "| ploha | okolina | omjer | |", "|---|---|---|---|"]
            for sname, under, r, ok in surr:
                out.append(f"| `{sname}` | `{under}` | {fmt(r)} | {'✅' if ok else '⚠️'} |")
            out.append("")
        else:
            print(f"\n{'=' * 72}\n{th.upper()}\n{'=' * 72}")
            for sname, tok, proof, r, thr, st in rows:
                val = fmt(r) if r is not None else "—"
                print(f"  {'✅' if st == 'PASS' else '❌'} {tok:<18} na {sname:<18} {val:>6}  {proof}")
            print(f"  ── čipovi ──")
            for fg, bg, r, ok in chips:
                print(f"  {'✅' if ok else '❌'} {fg:<34} na {bg:<22} {fmt(r):>6}")
            print(f"  ── ploha vs okolina (prag {fmt(AA_NON_TEXT)}) ──")
            for sname, under, r, ok in surr:
                print(f"  {'✅' if ok else '⚠️ '} {sname:<18} vs {under:<10} {fmt(r):>6}")

    if a.md:
        out += ["---", "", "## Padovi", ""]
        if all_fails:
            out += ["| tema | ploha | tekst token | omjer | dokaz |", "|---|---|---|---|---|"]
            out += [f"| {t} | `{s}` | `{k}` | **{r}** | {p} |" for t, s, k, r, p in all_fails]
        else:
            out.append("**Nijedan.** ✅")
        out.append("")
        print("\n".join(out))
    else:
        print(f"\n{'=' * 72}")
        if all_fails:
            print(f"🔴 PADOVA: {len(all_fails)}")
            for t, s, k, r, p in all_fails:
                print(f"   {t:<5} {k} na {s}: {r}  ({p})")
        else:
            print("✅ Svi mjereni parovi prolaze.")

    return 1 if all_fails else 0


if __name__ == "__main__":
    sys.exit(main())
