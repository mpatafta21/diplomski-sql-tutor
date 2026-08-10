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
    CO_USED_EXTRA,
    DE_ACCEPTED,
    DE_CLOSE,
    DE_COLLISION,
    GRAPHIC_ONLY,
    MONACO,
    PAIRS,
    SURFACE_USE,
    SURFACE_VS_SURROUND,
    SURFACES,
)
from palette import Color, contrast, delta_e, fmt, load_tokens, self_test  # noqa: E402

#: Semantički (zamrznuti) tokeni — druga strana svakog ΔE para.
SEMANTIC = {
    "correct", "correct-soft", "incorrect", "incorrect-soft", "partial", "partial-soft",
    "neutral", "accent-warm", "accent-warm-text", "accent-warm-foreground",
    *(f"mastery-{k}" for k in (0, 25, 50, 75, 100)),
    *(f"tier-{k}" for k in ("easy", "medium", "hard")),
    *(f"difficulty-{k}" for k in
      ("beginner", "intermediate", "advanced", "expert", "cross-module")),
    *(f"chart-{k}" for k in range(1, 6)),
}

CMD = "python3 scripts/a11y/contrast_matrix.py"


def resolve_surface(spec, tokens: dict[str, Color]) -> Color:
    """Ime tokena → Color; (token, alpha, ploha) → kompozit nad plohom.

    `under` smije biti i DRUGA PLOHA iz SURFACES, ne samo gol token: obrub nevaljanog
    polja leži nad `input/30` (vlastita pozadina polja), a ta je i sama kompozit.
    Bez toga se stvaran par ne može izraziti, pa bi se mjerio pogrešan (#50).
    """
    if isinstance(spec, str):
        return tokens[spec]
    tok, alpha, under = spec
    base = resolve_surface(SURFACES[under], tokens) if under in SURFACES else tokens[under]
    return tokens[tok].with_alpha(alpha).over(base)


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
        base = resolve_surface(SURFACES[under], t) if under in SURFACES else t[under]
        r = contrast(surf, base)
        out.append((sname, under, r, r >= AA_NON_TEXT))
    return out


def co_used_map() -> dict[str, dict[str, str]]:
    """kroma-token → {semantički token: citat}. Izvedeno iz PAIRS + CO_USED_EXTRA.

    Iz PAIRS: tekst na plohi ⇒ sukorišten je i s tom plohom i s ostalim tekstom na njoj.
    To pokriva sve što se vidi „na plohi"; fokus i sadržaj Monaca PAIRS ne vidi, pa ih
    donosi CO_USED_EXTRA (v. N-12).
    """
    out: dict[str, dict[str, str]] = {}

    def add(kroma: str, sem: str, why: str) -> None:
        if kroma != sem and sem in SEMANTIC and kroma not in SEMANTIC:
            out.setdefault(kroma, {}).setdefault(sem, why)

    for surf, texts in PAIRS.items():
        base = surf.split("/")[0].split("@")[0]
        sem_here = [t for t in texts if t in SEMANTIC]
        for text_tok in texts:
            for s in sem_here:
                add(base, s, f"PAIRS[{surf}] — `{s}` se renderira na toj plohi")
                add(text_tok, s, f"PAIRS[{surf}] — `{text_tok}` i `{s}` dijele plohu")
            if base in SEMANTIC:
                add(text_tok, base, f"PAIRS[{surf}] — `{text_tok}` stoji NA `{base}`")
    # obrub okružuje element na plohi → nasljeđuje njezino susjedstvo
    for b in ("border", "input", "sidebar-border"):
        for s, why in out.get("card", {}).items():
            add(b, s, f"obrub elementa na `card` — {why}")
    # Monaco: svi tokeni dijele jedan pravokutnik → svi sa svima
    for a in MONACO:
        for b in MONACO:
            add(a, b, f"Monaco — `{a}` ({MONACO[a]}) × `{b}` ({MONACO[b]})")
    for kroma, sems in CO_USED_EXTRA.items():
        for s, why in sems.items():
            add(kroma, s, why)
    return out


def delta_e_rows(theme: str, tokens_all) -> list[tuple]:
    """(ΔE, kroma, semantički, citat, oznaka) — sortirano od najbližeg."""
    t = tokens_all[theme]
    card = t.get("card")
    rows = []
    for kroma, sems in co_used_map().items():
        if kroma not in t:
            continue
        a = t[kroma].over(card) if t[kroma].alpha < 1 else t[kroma]
        for sem, why in sems.items():
            if sem not in t:
                continue
            b = t[sem].over(card) if t[sem].alpha < 1 else t[sem]
            d = delta_e(a, b)
            key = (kroma, sem) if (kroma, sem) in DE_ACCEPTED else (sem, kroma)
            if d < DE_COLLISION:
                mark = "PRIHVAĆENO" if key in DE_ACCEPTED else "KOLIZIJA"
            elif d < DE_CLOSE:
                mark = "BLIZU"
            else:
                mark = "OK"
            rows.append((d, kroma, sem, why, mark))
    rows.sort()
    return rows


def run_delta_e(themes, tokens, md: bool) -> int:
    """ΔE provjera cross-scale guarda. Izlazni kod 1 ako ima neprihvaćene kolizije."""
    bad = 0
    for th in themes:
        rows = delta_e_rows(th, tokens)
        if md:
            print(f"\n### {th.upper()} — ΔE nad sukorištenim parovima\n")
            print("| ΔE | kroma token | semantički token | dokaz sukorištenosti | |")
            print("|---|---|---|---|---|")
        else:
            print(f"\n{'=' * 72}\n{th.upper()} — ΔE (Oklab) nad SUKORIŠTENIM parovima")
            print(f"pragovi: 🔴 < {DE_COLLISION} kolizija · 🟡 < {DE_CLOSE} blizu · ✅ iznad")
            print("=" * 72)
        icon = {"KOLIZIJA": "🔴", "PRIHVAĆENO": "🟨", "BLIZU": "🟡", "OK": "✅"}
        for d, kroma, sem, why, mark in rows:
            if mark == "OK" and not md:
                continue  # terminal: prikaži samo ono što traži pažnju
            if md:
                print(f"| {d:.4f} | `{kroma}` | `{sem}` | {why} | {icon[mark]} |")
            else:
                print(f"  {icon[mark]} {d:.4f}  {kroma:<20} × {sem:<22} {why}")
            if mark == "KOLIZIJA":
                bad += 1
        if not md:
            worst = rows[0] if rows else None
            print(f"  ── {len(rows)} sukorištenih parova · najbliži "
                  f"{worst[0]:.4f} ({worst[1]} × {worst[2]})" if worst else "  ── nema parova")
    if bad:
        print(f"\n🔴 NEPRIHVAĆENIH KOLIZIJA: {bad}. Ili pomakni kroma-token, ili upiši par u "
              f"`DE_ACCEPTED` (pairs.py) S RAZLOGOM.")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", action="store_true", help="markdown umjesto terminalskog ispisa")
    ap.add_argument("--theme", choices=["light", "dark"], help="samo jedna tema")
    ap.add_argument("--pair", nargs=2, metavar=("TEKST", "PLOHA"), help="jedan par")
    ap.add_argument("--delta-e", action="store_true",
                    help="ΔE nad SUKORIŠTENIM parovima (cross-scale guard, MASTER §2.7)")
    ap.add_argument("--quiet-selftest", action="store_true")
    a = ap.parse_args()

    tokens = load_tokens()
    self_test(tokens, verbose=not a.quiet_selftest and not a.md)

    themes = [a.theme] if a.theme else list(tokens)

    if a.delta_e:
        return run_delta_e(themes, tokens, a.md)

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
