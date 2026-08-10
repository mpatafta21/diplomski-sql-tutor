# Faza 4.7 — MATRICA KONTRASTA: tekst-token × ploha

**Generirano:** 2026-08-10 · **naredba:** `python3 scripts/a11y/contrast_matrix.py --md`

> ⚠️ Vrijedi za **stanje koda na taj datum**. Tokeni se čitaju iz
> `frontend/src/index.css` pri svakom pokretanju — nakon svake promjene palete
> ovaj dokument treba **regenerirati istom naredbom**, ne ručno ispravljati.

**Metoda:** oklch → Oklab → linearni sRGB → sRGB → relativna luminancija → WCAG
omjer. Alpha se **kompozitira** nad navedenom plohom. Konvertor se pri svakom
pokretanju validira na već objavljenim brojkama projekta (`SELF_TEST` u
`scripts/a11y/palette.py`); ako validacija padne, mjerenje se ne izvodi.

**Pragovi:** tekst **4,50:1** · grafika i stanja **3,00:1** (SC 1.4.11).

**Parovi nisu kartezijev produkt** — mjeri se samo par koji u kodu postoji:
**●** ploha i tekst u istom `className` · **○** tekst u podstablu elementa koji
nosi plohu. Popis i citati: `scripts/a11y/pairs.py`.

---

## LIGHT

| ploha | gdje se koristi | tekst token | dokaz | omjer | |
|---|---|---|---|---|---|
| `background` | ploha stranice | `foreground` | ○ AppShell | 19,79 | ✅ |
| `background` | ploha stranice | `muted-foreground` | ○ AppShell | 5,32 | ✅ |
| `card` | kartice, paneli | `foreground` | ○ svi ekrani | 19,79 | ✅ |
| `card` | kartice, paneli | `muted-foreground` | ○ svi ekrani | 5,32 | ✅ |
| `card` | kartice, paneli | `accent-warm-text` | ○ ProgressHero, AttemptRow.tsx:67 | 5,79 | ✅ |
| `card` | kartice, paneli | `correct` | ○ ConceptRow | 5,19 | ✅ |
| `card` | kartice, paneli | `incorrect` | ○ AttemptRow | 5,83 | ✅ |
| `card` | kartice, paneli | `partial` | ○ StatsSummary.tsx:69 | 5,48 | ✅ |
| `card` | kartice, paneli | `neutral` | ○ ConceptChip | 6,00 | ✅ |
| `popover` | popover / tooltip | `foreground` | ○ ui/popover | 19,79 | ✅ |
| `popover` | popover / tooltip | `muted-foreground` | ○ ui/popover | 5,32 | ✅ |
| `sidebar` | lijeva navigacija | `muted-foreground` | ● AppShell.tsx:71 | 5,10 | ✅ |
| `sidebar` | lijeva navigacija | `accent-warm-text` | ○ AppShell | 5,55 | ✅ |
| `secondary` | secondary gumb | `foreground` | ○ ui/button variant=secondary | 18,15 | ✅ |
| `muted` | čipovi, prazna stanja | `muted-foreground` | ● BadgeGallery.tsx:73,97 | 4,88 | ✅ |
| `muted` | čipovi, prazna stanja | `foreground` | ○ EmptyState | 18,15 | ✅ |
| `muted` | čipovi, prazna stanja | `accent-warm-text` | ○ BadgeGallery | 5,31 | ✅ |
| `muted/30` | BadgeGallery — neosvojen bedž | `muted-foreground` | ○ BadgeGallery.tsx:62 | 5,19 | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `muted-foreground` | ○ ConceptCurveCard, RegisterPage info blok | 5,14 | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `foreground` | ○ RegisterPage info blok | 19,12 | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `accent-warm-text` | ○ ConceptCurveCard | 5,60 | ✅ |
| `muted/50` | hover stanja | `muted-foreground` | ○ ConceptCurveCard hover | 5,10 | ✅ |
| `muted/50` | hover stanja | `foreground` | ○ hover | 18,96 | ✅ |
| `muted/60` | mono blok u povijesti pokušaja | `muted-foreground` | ○ AttemptRow.tsx:117 | 5,06 | ✅ |
| `background/60` | mono blok detalja greške | `muted-foreground` | ● FeedbackPanel.tsx:163, AttemptRow.tsx:138 | 5,32 | ✅ |
| `card/50` | stale-dim rezultata | `muted-foreground` | ○ RunResultPanel stale-dim | 5,32 | ✅ |
| `sidebar-accent/40` | ConceptRow hover | `muted-foreground` | ○ ConceptRow.tsx:117 | 5,14 | ✅ |
| `sidebar-accent/40` | ConceptRow hover | `correct` | ○ ConceptRow | 5,01 | ✅ |
| `sidebar-accent/60` | nav hover | `muted-foreground` | ○ AppShell.tsx:71 hover | 5,06 | ✅ |
| `input/30` | input (dark varijanta) | `foreground` | ○ ui/input | 18,51 | ✅ |
| `input/30` | input (dark varijanta) | `muted-foreground` | ○ placeholder | 4,98 | ✅ |
| `input/50` | disabled input | `muted-foreground` | ○ disabled input | 4,76 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `correct` | ● FeedbackPanel.tsx:52-53, ContinueCard.tsx:129, TaskPage.tsx:288 | 4,67 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `foreground` | ○ FeedbackPanel.tsx:123 | 17,80 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `muted-foreground` | ○ FeedbackPanel.tsx:138,143,156,177,198 | 4,79 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 5,21 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `incorrect` | ● FeedbackPanel.tsx:64-65, LoginPage.tsx:105, RegisterPage.tsx:205 | 5,15 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `foreground` | ○ FeedbackPanel.tsx:123, ErrorState.tsx:35, RunResultPanel.tsx:114 | 17,50 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `muted-foreground` | ○ ErrorState.tsx:36, RunResultPanel.tsx:130, FeedbackPanel ×5 | 4,71 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 5,12 | ✅ |
| `partial-soft` | FeedbackPanel | `partial` | ● FeedbackPanel.tsx:58-59 | 4,86 | ✅ |
| `partial-soft` | FeedbackPanel | `foreground` | ○ FeedbackPanel.tsx:123 | 17,56 | ✅ |
| `partial-soft` | FeedbackPanel | `muted-foreground` | ○ FeedbackPanel ×5 | 4,72 | ✅ |
| `partial-soft` | FeedbackPanel | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 5,14 | ✅ |
| `accent-warm/5` | ConceptRow deep-link flash | `muted-foreground` | ○ ConceptRow.tsx:110 | 5,06 | ✅ |
| `accent-warm/5` | ConceptRow deep-link flash | `correct` | ○ ConceptRow | 4,93 | ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `accent-warm-text` | ● BadgeStrip.tsx:47+51, ContinueCard.tsx:86 | 5,24 | ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `muted-foreground` | ○ LeaderboardTable.tsx:64 | 4,81 | ✅ |
| `accent-warm/20` | BadgeGallery — osvojen bedž | `accent-warm-text` | ● BadgeGallery.tsx:72, :96 | 4,72 | ✅ |
| `incorrect/10` | ErrorState — krug ikone | `incorrect` | ● ErrorState.tsx:32, guards.tsx:69 | 4,97 | ✅ |

### LIGHT — čipovi (vlastiti `-foreground` na vlastitom fillu)

| tekst | ploha | omjer | |
|---|---|---|---|
| `accent-warm-foreground` | `accent-warm` | 5,04 | ✅ |
| `primary-foreground` | `primary` | 17,16 | ✅ |
| `secondary-foreground` | `secondary` | 16,42 | ✅ |
| `sidebar-accent-foreground` | `sidebar-accent` | 16,42 | ✅ |
| `tier-easy-foreground` | `tier-easy` | 7,75 | ✅ |
| `tier-medium-foreground` | `tier-medium` | 4,93 | ✅ |
| `tier-hard-foreground` | `tier-hard` | 7,81 | ✅ |
| `difficulty-beginner-foreground` | `difficulty-beginner` | 9,63 | ✅ |
| `difficulty-intermediate-foreground` | `difficulty-intermediate` | 6,54 | ✅ |
| `difficulty-advanced-foreground` | `difficulty-advanced` | 4,61 | ✅ |
| `difficulty-expert-foreground` | `difficulty-expert` | 7,57 | ✅ |
| `difficulty-cross-module-foreground` | `difficulty-cross-module` | 4,72 | ✅ |

### LIGHT — ploha vs okolina (prag 3,00, SC 1.4.11)

| ploha | okolina | omjer | |
|---|---|---|---|
| `accent-warm/5` | `card` | 1,05 | ⚠️ |
| `accent-warm/10` | `card` | 1,11 | ⚠️ |
| `accent-warm/20` | `card` | 1,23 | ⚠️ |
| `muted/40` | `card` | 1,03 | ⚠️ |

---

## DARK

| ploha | gdje se koristi | tekst token | dokaz | omjer | |
|---|---|---|---|---|---|
| `background` | ploha stranice | `foreground` | ○ AppShell | 18,96 | ✅ |
| `background` | ploha stranice | `muted-foreground` | ○ AppShell | 7,63 | ✅ |
| `card` | kartice, paneli | `foreground` | ○ svi ekrani | 17,16 | ✅ |
| `card` | kartice, paneli | `muted-foreground` | ○ svi ekrani | 6,91 | ✅ |
| `card` | kartice, paneli | `accent-warm-text` | ○ ProgressHero, AttemptRow.tsx:67 | 9,44 | ✅ |
| `card` | kartice, paneli | `correct` | ○ ConceptRow | 8,54 | ✅ |
| `card` | kartice, paneli | `incorrect` | ○ AttemptRow | 6,16 | ✅ |
| `card` | kartice, paneli | `partial` | ○ StatsSummary.tsx:69 | 8,68 | ✅ |
| `card` | kartice, paneli | `neutral` | ○ ConceptChip | 7,22 | ✅ |
| `popover` | popover / tooltip | `foreground` | ○ ui/popover | 17,16 | ✅ |
| `popover` | popover / tooltip | `muted-foreground` | ○ ui/popover | 6,91 | ✅ |
| `sidebar` | lijeva navigacija | `muted-foreground` | ● AppShell.tsx:71 | 6,91 | ✅ |
| `sidebar` | lijeva navigacija | `accent-warm-text` | ○ AppShell | 9,44 | ✅ |
| `secondary` | secondary gumb | `foreground` | ○ ui/button variant=secondary | 14,48 | ✅ |
| `muted` | čipovi, prazna stanja | `muted-foreground` | ● BadgeGallery.tsx:73,97 | 5,83 | ✅ |
| `muted` | čipovi, prazna stanja | `foreground` | ○ EmptyState | 14,48 | ✅ |
| `muted` | čipovi, prazna stanja | `accent-warm-text` | ○ BadgeGallery | 7,97 | ✅ |
| `muted/30` | BadgeGallery — neosvojen bedž | `muted-foreground` | ○ BadgeGallery.tsx:62 | 6,60 | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `muted-foreground` | ○ ConceptCurveCard, RegisterPage info blok | 6,49 | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `foreground` | ○ RegisterPage info blok | 16,13 | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `accent-warm-text` | ○ ConceptCurveCard | 8,88 | ✅ |
| `muted/50` | hover stanja | `muted-foreground` | ○ ConceptCurveCard hover | 6,39 | ✅ |
| `muted/50` | hover stanja | `foreground` | ○ hover | 15,86 | ✅ |
| `muted/60` | mono blok u povijesti pokušaja | `muted-foreground` | ○ AttemptRow.tsx:117 | 6,28 | ✅ |
| `background/60` | mono blok detalja greške | `muted-foreground` | ● FeedbackPanel.tsx:163, AttemptRow.tsx:138 | 7,38 | ✅ |
| `card/50` | stale-dim rezultata | `muted-foreground` | ○ RunResultPanel stale-dim | 6,91 | ✅ |
| `sidebar-accent/40` | ConceptRow hover | `muted-foreground` | ○ ConceptRow.tsx:117 | 6,49 | ✅ |
| `sidebar-accent/40` | ConceptRow hover | `correct` | ○ ConceptRow | 8,03 | ✅ |
| `sidebar-accent/60` | nav hover | `muted-foreground` | ○ AppShell.tsx:71 hover | 6,28 | ✅ |
| `input/30` | input (dark varijanta) | `foreground` | ○ ui/input | 15,33 | ✅ |
| `input/30` | input (dark varijanta) | `muted-foreground` | ○ placeholder | 6,17 | ✅ |
| `input/50` | disabled input | `muted-foreground` | ○ disabled input | 5,65 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `correct` | ● FeedbackPanel.tsx:52-53, ContinueCard.tsx:129, TaskPage.tsx:288 | 7,74 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `foreground` | ○ FeedbackPanel.tsx:123 | 15,57 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `muted-foreground` | ○ FeedbackPanel.tsx:138,143,156,177,198 | 6,27 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,57 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `incorrect` | ● FeedbackPanel.tsx:64-65, LoginPage.tsx:105, RegisterPage.tsx:205 | 5,72 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `foreground` | ○ FeedbackPanel.tsx:123, ErrorState.tsx:35, RunResultPanel.tsx:114 | 15,93 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `muted-foreground` | ○ ErrorState.tsx:36, RunResultPanel.tsx:130, FeedbackPanel ×5 | 6,41 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,77 | ✅ |
| `partial-soft` | FeedbackPanel | `partial` | ● FeedbackPanel.tsx:58-59 | 8,03 | ✅ |
| `partial-soft` | FeedbackPanel | `foreground` | ○ FeedbackPanel.tsx:123 | 15,87 | ✅ |
| `partial-soft` | FeedbackPanel | `muted-foreground` | ○ FeedbackPanel ×5 | 6,39 | ✅ |
| `partial-soft` | FeedbackPanel | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,74 | ✅ |
| `accent-warm/5` | ConceptRow deep-link flash | `muted-foreground` | ○ ConceptRow.tsx:110 | 6,35 | ✅ |
| `accent-warm/5` | ConceptRow deep-link flash | `correct` | ○ ConceptRow | 7,85 | ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `accent-warm-text` | ● BadgeStrip.tsx:47+51, ContinueCard.tsx:86 | 7,86 | ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `muted-foreground` | ○ LeaderboardTable.tsx:64 | 5,75 | ✅ |
| `accent-warm/20` | BadgeGallery — osvojen bedž | `accent-warm-text` | ● BadgeGallery.tsx:72, :96 | 6,22 | ✅ |
| `incorrect/10` | ErrorState — krug ikone | `incorrect` | ● ErrorState.tsx:32, guards.tsx:69 | 5,43 | ✅ |

### DARK — čipovi (vlastiti `-foreground` na vlastitom fillu)

| tekst | ploha | omjer | |
|---|---|---|---|
| `accent-warm-foreground` | `accent-warm` | 9,15 | ✅ |
| `primary-foreground` | `primary` | 14,22 | ✅ |
| `secondary-foreground` | `secondary` | 14,48 | ✅ |
| `sidebar-accent-foreground` | `sidebar-accent` | 14,48 | ✅ |
| `tier-easy-foreground` | `tier-easy` | 4,83 | ✅ |
| `tier-medium-foreground` | `tier-medium` | 7,08 | ✅ |
| `tier-hard-foreground` | `tier-hard` | 10,25 | ✅ |
| `difficulty-beginner-foreground` | `difficulty-beginner` | 5,01 | ✅ |
| `difficulty-intermediate-foreground` | `difficulty-intermediate` | 6,02 | ✅ |
| `difficulty-advanced-foreground` | `difficulty-advanced` | 8,07 | ✅ |
| `difficulty-expert-foreground` | `difficulty-expert` | 10,83 | ✅ |
| `difficulty-cross-module-foreground` | `difficulty-cross-module` | 6,77 | ✅ |

### DARK — ploha vs okolina (prag 3,00, SC 1.4.11)

| ploha | okolina | omjer | |
|---|---|---|---|
| `accent-warm/5` | `card` | 1,09 | ⚠️ |
| `accent-warm/10` | `card` | 1,20 | ⚠️ |
| `accent-warm/20` | `card` | 1,52 | ⚠️ |
| `muted/40` | `card` | 1,06 | ⚠️ |

---

## Padovi

**Nijedan.** ✅

