# Faza 4.7 — MATRICA KONTRASTA: tekst-token × ploha

**Datum:** 2026-08-10 · **Grana:** `faza-4-7-polish` · **Status:** vrijednosti PRIMIJENJENE 2026-08-10

## Zašto postoji

Ovo je bio **treći** krug otkrivanja iste greške: mjereno vs `card` → otkriveno da
elementi stoje na `-soft` → otkriveno da `-soft` ima potrošače izvan FeedbackPanela.
Matrica prekida niz mjerenjem **cijelog prostora**, ne sljedećeg sloja.

## Metoda

oklch → Oklab → linearni sRGB → sRGB → relativna luminancija → WCAG omjer. Alpha se
**kompozitira** nad `card` (oznaka u opisu plohe). Konvertor validiran na šest ranije
objavljenih brojki projekta (`ring`×`card` 2,59/3,79 · `muted-foreground`×`card`
4,73/6,91 · `foreground`×`card` 19,79/17,16) — sve reproducirane na dvije decimale.

**Pragovi:** tekst **4,50:1** (sve je 10–16 px, nema large-text iznimke) ·
grafika i stanja **3,00:1** (SC 1.4.11).

**Parovi nisu kartezijev produkt.** Mjeri se samo ono što u kodu postoji:
**●** = ploha i tekst u **istom** `className` (dokazano) · **○** = tekst je u
podstablu elementa koji nosi plohu (naslijeđeno).

**PRIMIJENJENO (light, 2026-08-10, commit stage 4c):** `--muted-foreground` 0.556 → **0.528** ·
`--accent-warm-text` 0.56 → **0.514**. **Dark se ne mijenja.**

---

## LIGHT

| ploha | gdje se koristi | tekst token | dokaz | prije 4c | PRIMIJENJENO |
|---|---|---|---|---|---|
| `background` | ploha stranice | `foreground` | ○ AppShell | 19,79 | — ✅ |
| `background` | ploha stranice | `muted-foreground` | ○ AppShell | 4,73 | **5,32** ✅ |
| `card` | kartice, paneli | `foreground` | ○ svi ekrani | 19,79 | — ✅ |
| `card` | kartice, paneli | `muted-foreground` | ○ svi ekrani | 4,73 | **5,32** ✅ |
| `card` | kartice, paneli | `accent-warm-text` | ○ ProgressHero, AttemptRow:67 | 4,78 | **5,79** ✅ |
| `card` | kartice, paneli | `correct` | ○ ConceptRow | 5,19 | — ✅ |
| `card` | kartice, paneli | `incorrect` | ○ AttemptRow | 5,83 | — ✅ |
| `card` | kartice, paneli | `partial` | ○ StatsSummary:69 | 5,48 | — ✅ |
| `card` | kartice, paneli | `neutral` | ○ ConceptChip | 6,00 | — ✅ |
| `popover` | popover/tooltip | `foreground` | ○ ui/popover | 19,79 | — ✅ |
| `popover` | popover/tooltip | `muted-foreground` | ○ ui/popover | 4,73 | **5,32** ✅ |
| `sidebar` | lijeva navigacija | `muted-foreground` | ● AppShell.tsx:71 | 4,53 | **5,10** ✅ |
| `sidebar` | lijeva navigacija | `accent-warm-text` | ○ AppShell | 4,58 | **5,55** ✅ |
| `secondary` | secondary gumb | `foreground` | ○ ui/button secondary | 18,15 | — ✅ |
| `muted` | čipovi, prazna stanja | `muted-foreground` | ● BadgeGallery.tsx:73,97 | 4,34 | **4,88** ✅ |
| `muted` | čipovi, prazna stanja | `foreground` | ○ EmptyState | 18,15 | — ✅ |
| `muted` | čipovi, prazna stanja | `accent-warm-text` | ○ BadgeGallery | 4,38 | **5,31** ✅ |
| `muted/30` | BadgeGallery neosvojen | `muted-foreground` | ○ BadgeGallery.tsx:62 | 4,61 | **5,19** ✅ |
| `muted/40` | info blok, odabrana kartica | `muted-foreground` | ○ ConceptCurveCard, RegisterPage info blok | 4,57 | **5,14** ✅ |
| `muted/40` | info blok, odabrana kartica | `foreground` | ○ RegisterPage info blok | 19,12 | — ✅ |
| `muted/40` | info blok, odabrana kartica | `accent-warm-text` | ○ ConceptCurveCard | 4,62 | **5,60** ✅ |
| `muted/50` | hover | `muted-foreground` | ○ ConceptCurveCard hover | 4,53 | **5,10** ✅ |
| `muted/50` | hover | `foreground` | ○ hover | 18,96 | — ✅ |
| `muted/60` | mono blok u povijesti | `muted-foreground` | ○ AttemptRow.tsx:117 mono | 4,49 | **5,06** ✅ |
| `background/60` | mono blok detalja | `muted-foreground` | ● FeedbackPanel.tsx:163, AttemptRow.tsx:138 | 4,73 | **5,32** ✅ |
| `card/50` | stale-dim | `muted-foreground` | ○ RunResultPanel stale-dim | 4,73 | **5,32** ✅ |
| `sidebar-accent/40` | ConceptRow hover | `muted-foreground` | ○ ConceptRow.tsx:117 hover | 4,57 | **5,14** ✅ |
| `sidebar-accent/40` | ConceptRow hover | `correct` | ○ ConceptRow | 5,01 | — ✅ |
| `sidebar-accent/60` | nav hover | `muted-foreground` | ○ AppShell.tsx:71 hover | 4,49 | **5,06** ✅ |
| `input/30` | input (dark varijanta) | `foreground` | ○ ui/input (dark) | 18,51 | — ✅ |
| `input/30` | input (dark varijanta) | `muted-foreground` | ○ placeholder | 4,43 | **4,98** ✅ |
| `input/50` | disabled input | `muted-foreground` | ○ disabled input | 4,23 | **4,76** ✅ |
| `correct-soft` | FeedbackPanel, čip Riješeno | `correct` | ● FeedbackPanel.tsx:52-53, ContinueCard:129, TaskPage:288 | 4,67 | — ✅ |
| `correct-soft` | FeedbackPanel, čip Riješeno | `foreground` | ○ FeedbackPanel.tsx:123 | 17,80 | — ✅ |
| `correct-soft` | FeedbackPanel, čip Riješeno | `muted-foreground` | ○ FeedbackPanel.tsx:138,143,156,177,198 | 4,26 | **4,79** ✅ |
| `correct-soft` | FeedbackPanel, čip Riješeno | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 4,30 | **5,21** ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `incorrect` | ● FeedbackPanel.tsx:64-65, LoginPage:105, RegisterPage:205 | 5,15 | — ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `foreground` | ○ FeedbackPanel.tsx:123, ErrorState.tsx:35, RunResultPanel:114 | 17,50 | — ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `muted-foreground` | ○ ErrorState.tsx:36, RunResultPanel:130, FeedbackPanel ×5 | 4,18 | **4,71** ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 4,22 | **5,12** ✅ |
| `partial-soft` | FeedbackPanel | `partial` | ● FeedbackPanel.tsx:58-59 | 4,86 | — ✅ |
| `partial-soft` | FeedbackPanel | `foreground` | ○ FeedbackPanel.tsx:123 | 17,56 | — ✅ |
| `partial-soft` | FeedbackPanel | `muted-foreground` | ○ FeedbackPanel ×5 | 4,20 | **4,72** ✅ |
| `partial-soft` | FeedbackPanel | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 4,24 | **5,14** ✅ |
| `accent-warm/5` | ConceptRow deep-link | `muted-foreground` | ○ ConceptRow.tsx:110 deep-link | 4,50 | **5,06** ✅ |
| `accent-warm/5` | ConceptRow deep-link | `correct` | ○ ConceptRow | 4,93 | — ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `accent-warm-text` | ● BadgeStrip.tsx:47+51 (ikona), ContinueCard:86 ⚠️ ikona (BadgeStrip:51) — grafika; ContinueCard:86 ikona | 4,32 | **5,24** ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `muted-foreground` | ○ LeaderboardTable.tsx:64 redak „ja” | 4,28 | **4,81** ✅ |
| `accent-warm/20` | BadgeGallery osvojen | `accent-warm-text` | ● BadgeGallery.tsx:72 (ikona), :96 (TEKST 10,4 px) ⚠️ ikona (:72) — grafika 3:1; ALI :96 je TEKST | 3,89 | **4,72** ✅ |
| `incorrect/10` | ErrorState krug ikone | `incorrect` | ● ErrorState.tsx:32 (ikona), guards.tsx:69 ⚠️ samo ikona — grafika, prag 3:1 | 4,97 | — ✅ |

---

## DARK

| ploha | gdje se koristi | tekst token | dokaz | prije 4c | PRIMIJENJENO |
|---|---|---|---|---|---|
| `background` | ploha stranice | `foreground` | ○ AppShell | 18,96 | — ✅ |
| `background` | ploha stranice | `muted-foreground` | ○ AppShell | 7,63 | — ✅ |
| `card` | kartice, paneli | `foreground` | ○ svi ekrani | 17,16 | — ✅ |
| `card` | kartice, paneli | `muted-foreground` | ○ svi ekrani | 6,91 | — ✅ |
| `card` | kartice, paneli | `accent-warm-text` | ○ ProgressHero, AttemptRow:67 | 9,44 | — ✅ |
| `card` | kartice, paneli | `correct` | ○ ConceptRow | 8,54 | — ✅ |
| `card` | kartice, paneli | `incorrect` | ○ AttemptRow | 6,16 | — ✅ |
| `card` | kartice, paneli | `partial` | ○ StatsSummary:69 | 8,68 | — ✅ |
| `card` | kartice, paneli | `neutral` | ○ ConceptChip | 7,22 | — ✅ |
| `popover` | popover/tooltip | `foreground` | ○ ui/popover | 17,16 | — ✅ |
| `popover` | popover/tooltip | `muted-foreground` | ○ ui/popover | 6,91 | — ✅ |
| `sidebar` | lijeva navigacija | `muted-foreground` | ● AppShell.tsx:71 | 6,91 | — ✅ |
| `sidebar` | lijeva navigacija | `accent-warm-text` | ○ AppShell | 9,44 | — ✅ |
| `secondary` | secondary gumb | `foreground` | ○ ui/button secondary | 14,48 | — ✅ |
| `muted` | čipovi, prazna stanja | `muted-foreground` | ● BadgeGallery.tsx:73,97 | 5,83 | — ✅ |
| `muted` | čipovi, prazna stanja | `foreground` | ○ EmptyState | 14,48 | — ✅ |
| `muted` | čipovi, prazna stanja | `accent-warm-text` | ○ BadgeGallery | 7,97 | — ✅ |
| `muted/30` | BadgeGallery neosvojen | `muted-foreground` | ○ BadgeGallery.tsx:62 | 6,60 | — ✅ |
| `muted/40` | info blok, odabrana kartica | `muted-foreground` | ○ ConceptCurveCard, RegisterPage info blok | 6,49 | — ✅ |
| `muted/40` | info blok, odabrana kartica | `foreground` | ○ RegisterPage info blok | 16,13 | — ✅ |
| `muted/40` | info blok, odabrana kartica | `accent-warm-text` | ○ ConceptCurveCard | 8,88 | — ✅ |
| `muted/50` | hover | `muted-foreground` | ○ ConceptCurveCard hover | 6,39 | — ✅ |
| `muted/50` | hover | `foreground` | ○ hover | 15,86 | — ✅ |
| `muted/60` | mono blok u povijesti | `muted-foreground` | ○ AttemptRow.tsx:117 mono | 6,28 | — ✅ |
| `background/60` | mono blok detalja | `muted-foreground` | ● FeedbackPanel.tsx:163, AttemptRow.tsx:138 | 7,38 | — ✅ |
| `card/50` | stale-dim | `muted-foreground` | ○ RunResultPanel stale-dim | 6,91 | — ✅ |
| `sidebar-accent/40` | ConceptRow hover | `muted-foreground` | ○ ConceptRow.tsx:117 hover | 6,49 | — ✅ |
| `sidebar-accent/40` | ConceptRow hover | `correct` | ○ ConceptRow | 8,03 | — ✅ |
| `sidebar-accent/60` | nav hover | `muted-foreground` | ○ AppShell.tsx:71 hover | 6,28 | — ✅ |
| `input/30` | input | `foreground` | ○ ui/input (dark) | 15,33 | — ✅ |
| `input/30` | input | `muted-foreground` | ○ placeholder | 6,17 | — ✅ |
| `input/50` | disabled input | `muted-foreground` | ○ disabled input | 5,65 | — ✅ |
| `correct-soft` | FeedbackPanel, čip Riješeno | `correct` | ● FeedbackPanel.tsx:52-53, ContinueCard:129, TaskPage:288 | 7,74 | — ✅ |
| `correct-soft` | FeedbackPanel, čip Riješeno | `foreground` | ○ FeedbackPanel.tsx:123 | 15,57 | — ✅ |
| `correct-soft` | FeedbackPanel, čip Riješeno | `muted-foreground` | ○ FeedbackPanel.tsx:138,143,156,177,198 | 6,27 | — ✅ |
| `correct-soft` | FeedbackPanel, čip Riješeno | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,57 | — ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `incorrect` | ● FeedbackPanel.tsx:64-65, LoginPage:105, RegisterPage:205 | 5,72 | — ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `foreground` | ○ FeedbackPanel.tsx:123, ErrorState.tsx:35, RunResultPanel:114 | 15,93 | — ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `muted-foreground` | ○ ErrorState.tsx:36, RunResultPanel:130, FeedbackPanel ×5 | 6,41 | — ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,77 | — ✅ |
| `partial-soft` | FeedbackPanel | `partial` | ● FeedbackPanel.tsx:58-59 | 8,03 | — ✅ |
| `partial-soft` | FeedbackPanel | `foreground` | ○ FeedbackPanel.tsx:123 | 15,87 | — ✅ |
| `partial-soft` | FeedbackPanel | `muted-foreground` | ○ FeedbackPanel ×5 | 6,39 | — ✅ |
| `partial-soft` | FeedbackPanel | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,74 | — ✅ |
| `accent-warm/5` | ConceptRow deep-link | `muted-foreground` | ○ ConceptRow.tsx:110 deep-link | 6,35 | — ✅ |
| `accent-warm/5` | ConceptRow deep-link | `correct` | ○ ConceptRow | 7,85 | — ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `accent-warm-text` | ● BadgeStrip.tsx:47+51 (ikona), ContinueCard:86 ⚠️ ikona (BadgeStrip:51) — grafika; ContinueCard:86 ikona | 7,86 | — ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `muted-foreground` | ○ LeaderboardTable.tsx:64 redak „ja” | 5,75 | — ✅ |
| `accent-warm/20` | BadgeGallery osvojen | `accent-warm-text` | ● BadgeGallery.tsx:72 (ikona), :96 (TEKST 10,4 px) ⚠️ ikona (:72) — grafika 3:1; ALI :96 je TEKST | 6,22 | — ✅ |
| `incorrect/10` | ErrorState krug ikone | `incorrect` | ● ErrorState.tsx:32 (ikona), guards.tsx:69 ⚠️ samo ikona — grafika, prag 3:1 | 5,43 | — ✅ |

---

## Padovi NAKON primjene

**Nijedan.** ✅

