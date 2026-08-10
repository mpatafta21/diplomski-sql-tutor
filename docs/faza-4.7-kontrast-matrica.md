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

## DARK

| ploha | gdje se koristi | tekst token | dokaz | omjer | |
|---|---|---|---|---|---|
| `background` | ploha stranice | `foreground` | ○ AppShell | 18,16 | ✅ |
| `background` | ploha stranice | `muted-foreground` | ○ AppShell | 7,61 | ✅ |
| `card` | kartice, paneli | `foreground` | ○ svi ekrani | 16,51 | ✅ |
| `card` | kartice, paneli | `muted-foreground` | ○ svi ekrani | 6,92 | ✅ |
| `card` | kartice, paneli | `accent-warm-text` | ○ ProgressHero, AttemptRow.tsx:67 | 9,51 | ✅ |
| `card` | kartice, paneli | `correct` | ○ ConceptRow | 8,59 | ✅ |
| `card` | kartice, paneli | `incorrect` | ○ AttemptRow | 6,20 | ✅ |
| `card` | kartice, paneli | `partial` | ○ StatsSummary.tsx:69 | 8,74 | ✅ |
| `popover` | popover / tooltip | `foreground` | ○ ui/popover | 16,51 | ✅ |
| `popover` | popover / tooltip | `muted-foreground` | ○ ui/popover | 6,92 | ✅ |
| `sidebar` | lijeva navigacija | `muted-foreground` | ● AppShell.tsx:71 | 6,92 | ✅ |
| `sidebar` | lijeva navigacija | `accent-warm-text` | ○ AppShell | 9,51 | ✅ |
| `secondary` | secondary gumb | `foreground` | ○ ui/button variant=secondary | 14,00 | ✅ |
| `muted` | čipovi, prazna stanja | `muted-foreground` | ● BadgeGallery.tsx:73,97 | 5,87 | ✅ |
| `muted` | čipovi, prazna stanja | `foreground` | ○ EmptyState | 14,00 | ✅ |
| `muted` | čipovi, prazna stanja | `accent-warm-text` | ○ BadgeGallery | 8,06 | ✅ |
| `muted/30` | BadgeGallery — neosvojen bedž | `muted-foreground` | ○ BadgeGallery.tsx:62 | 6,62 | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `muted-foreground` | ○ ConceptCurveCard, RegisterPage info blok | 6,52 | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `foreground` | ○ RegisterPage info blok | 15,55 | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `accent-warm-text` | ○ ConceptCurveCard | 8,96 | ✅ |
| `muted/50` | hover stanja | `muted-foreground` | ○ ConceptCurveCard hover | 6,41 | ✅ |
| `muted/50` | hover stanja | `foreground` | ○ hover | 15,30 | ✅ |
| `muted/60` | mono blok u povijesti pokušaja | `muted-foreground` | ○ AttemptRow.tsx:117 | 6,30 | ✅ |
| `background/60` | mono blok detalja greške | `muted-foreground` | ● FeedbackPanel.tsx:163, AttemptRow.tsx:138 | 7,36 | ✅ |
| `card/50` | stale-dim rezultata | `muted-foreground` | ○ RunResultPanel stale-dim | 6,92 | ✅ |
| `sidebar-accent/40` | ConceptRow hover | `muted-foreground` | ○ ConceptRow.tsx:117 | 6,52 | ✅ |
| `sidebar-accent/40` | ConceptRow hover | `correct` | ○ ConceptRow | 8,09 | ✅ |
| `sidebar-accent/60` | nav hover | `muted-foreground` | ○ AppShell.tsx:71 hover | 6,30 | ✅ |
| `input/30` | input (dark varijanta) | `foreground` | ○ ui/input | 14,77 | ✅ |
| `input/30` | input (dark varijanta) | `muted-foreground` | ○ placeholder | 6,19 | ✅ |
| `input/80` | disabled input | `muted-foreground` | ○ disabled input | 4,89 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `correct` | ● FeedbackPanel.tsx:52-53, ContinueCard.tsx:129, TaskPage.tsx:288 | 7,74 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `foreground` | ○ FeedbackPanel.tsx:123 | 14,88 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `muted-foreground` | ○ FeedbackPanel.tsx:138,143,156,177,198 | 6,23 | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,57 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `incorrect` | ● FeedbackPanel.tsx:64-65, LoginPage.tsx:105, RegisterPage.tsx:205 | 5,72 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `foreground` | ○ FeedbackPanel.tsx:123, ErrorState.tsx:35, RunResultPanel.tsx:114 | 15,22 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `muted-foreground` | ○ ErrorState.tsx:36, RunResultPanel.tsx:130, FeedbackPanel ×5 | 6,38 | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,77 | ✅ |
| `partial-soft` | FeedbackPanel | `partial` | ● FeedbackPanel.tsx:58-59 | 8,03 | ✅ |
| `partial-soft` | FeedbackPanel | `foreground` | ○ FeedbackPanel.tsx:123 | 15,17 | ✅ |
| `partial-soft` | FeedbackPanel | `muted-foreground` | ○ FeedbackPanel ×5 | 6,36 | ✅ |
| `partial-soft` | FeedbackPanel | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,74 | ✅ |
| `accent-warm/5` | ConceptRow deep-link flash | `muted-foreground` | ○ ConceptRow.tsx:110 | 6,40 | ✅ |
| `accent-warm/5` | ConceptRow deep-link flash | `correct` | ○ ConceptRow | 7,96 | ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `accent-warm-text` | ● BadgeStrip.tsx:47+51, ContinueCard.tsx:86 | 8,01 | ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `muted-foreground` | ○ LeaderboardTable.tsx:64 | 5,83 | ✅ |
| `accent-warm/20` | BadgeGallery — osvojen bedž | `accent-warm-text` | ● BadgeGallery.tsx:72, :96 | 6,38 | ✅ |
| `incorrect/10` | ErrorState — krug ikone | `incorrect` | ● ErrorState.tsx:32, guards.tsx:69 | 5,50 | ✅ |

### DARK — čipovi (vlastiti `-foreground` na vlastitom fillu)

| tekst | ploha | omjer | |
|---|---|---|---|
| `accent-warm-foreground` | `accent-warm` | 9,15 | ✅ |
| `primary-foreground` | `primary` | 14,29 | ✅ |
| `secondary-foreground` | `secondary` | 14,00 | ✅ |
| `sidebar-accent-foreground` | `sidebar-accent` | 14,00 | ✅ |
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
| `accent-warm/5` | `card` | 1,08 | ⚠️ |
| `accent-warm/10` | `card` | 1,19 | ⚠️ |
| `accent-warm/20` | `card` | 1,49 | ⚠️ |
| `muted/40` | `card` | 1,06 | ⚠️ |
| `border@card` | `card` | 1,33 | ⚠️ |
| `border@background` | `background` | 1,27 | ⚠️ |
| `border@muted` | `muted` | 1,36 | ⚠️ |
| `input@card` | `card` | 1,57 | ⚠️ |
| `input@background` | `background` | 1,49 | ⚠️ |
| `input@muted` | `muted` | 1,59 | ⚠️ |
| `sidebar-border@sidebar` | `sidebar` | 1,33 | ⚠️ |
| `destructive/50@input` | `input/30` | 2,33 | ⚠️ |
| `destructive/50` | `card` | 2,41 | ⚠️ |
| `destructive/40` | `card` | 1,96 | ⚠️ |

---

## Padovi

**Nijedan.** ✅

