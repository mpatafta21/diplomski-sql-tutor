# Design System — MASTER (SSOT)

> **LOGIKA:** Pri gradnji konkretne stranice prvo provjeri `design-system/sql-tutor/pages/[stranica].md`.
> Ako postoji, njegova pravila **nadjačavaju** ovaj Master. Ako ne postoji, strogo slijedi pravila ispod.
>
> **POVIJEST:** Prvotni generatorski output (Kids Learning / Vibrant / light-only / Fira / zeleni accent)
> odbačen je kao promašena klasifikacija — ovaj sadržaj ručno je napisan prema zaključanom design
> languageu (`docs/faza-4-plan.md` §3) i verificiranim backend skalama (Stage A2). Sve oklch vrijednosti
> numerički su provjerene (WCAG kontrast + sRGB gamut) prije upisa.

---

**Projekt:** sql-tutor — adaptivni SQL tutoring sustav (diplomski, FOI)
**Kategorija:** developer-tool / learning-dashboard (NE kids-learning, NE corporate SaaS)
**Ažurirano:** Faza 4.1b

---

## 1. Smjer

**„Mirna dev-konzola za učenje."** Dark-first (pari s Monaco editorom, smanjuje umor pri dugim SQL
sesijama); light tema ravnopravan token-set, ne naknadna misao. Precizna tipografija, velikodušan
prostor, podaci u prvom planu. Jedan **topli amber accent** rezerviran za napredak i gamifikaciju.
Motion suptilan i nagrađujući — feedback, ne konfeti-spam.

**Mood ključne riječi:** calm · precise · data-forward · intentional · rewarding-but-restrained
**Anti-mood:** playful-childish · vibrant-blocks · high-energy · video-hero · corporate-template

---

## 2. Boje

Sve boje su **oklch**, definirane u `frontend/src/index.css` kao CSS varijable u `:root` (light) i
`.dark` (dark), mapirane u `@theme inline` za Tailwind utility-e. Base neutralna paleta (background,
foreground, card, muted, border…) je shadcn-seedana i **ne dira se** — grupe ispod ju proširuju.

### 2.1 Accent — topli amber (jedini "warm" u sustavu)

Rezerviran ISKLJUČIVO za: XP, level, streak, badge, progres, CTA "sljedeći zadatak".
Ne koristi se za dekoraciju, navigaciju ni neutralne akcije.

| Token | Light | Dark | Uloga |
|---|---|---|---|
| `--accent-warm` | `oklch(0.66 0.13 72)` | `oklch(0.80 0.15 80)` | fill (XP bar, badge, progres; ≥3:1 vs bg ✓) |
| `--accent-warm-foreground` | `oklch(0.25 0.04 75)` | `oklch(0.22 0.04 80)` | tekst NA fillu (≥4.5:1 ✓) |
| `--accent-warm-text` | `oklch(0.56 0.12 70)` | `oklch(0.80 0.15 80)` | amber tekst NA pozadini (≥4.5:1 ✓) |

> Napomena o imenu: shadcn već zauzima `--accent` (neutralni hover) — topli accent je zato
> `--accent-warm`, bez gaženja postojećih shadcn stanja.

### 2.2 Semantika verdicta

| Token | Light (na bijelom ≥4.5 ✓) | Dark (na 0.145 ≥4.5 ✓) |
|---|---|---|
| `--correct` | `oklch(0.52 0.13 150)` | `oklch(0.75 0.15 150)` |
| `--incorrect` | `oklch(0.53 0.19 25)` | `oklch(0.70 0.19 25)` |
| `--partial` | `oklch(0.53 0.11 55)` | `oklch(0.78 0.13 60)` |
| `--neutral` | `oklch(0.50 0.02 260)` | `oklch(0.72 0.02 260)` |

Svaki ima `-soft` varijantu (suptilna pozadina feedback banera; tekst-token preko nje ostaje AA).

**PARTIAL JE AKTIVAN od 4.3c** (revizija ERRATA #8: `verdict` kolona i dalje ne postoji, ali je
partial DETERMINISTIČKI izvediv — backend `row_mismatch` ⇔ interni verdict "partial",
evaluation.py:186; derivacija u `lib/feedback.ts`). **Obavezno pravilo uz aktivaciju:** partial
verdikt NIKAD ne nosi samo boja — ikona (TriangleAlert) + tekstualna oznaka ("Djelomično") su
primarni kanal. Razlog (izmjereno 4.3c, `a11y-partial.py`): blizina partial hue 55–60 vs
accent-warm 70–85 → ΔE(OKLab) 0.044–0.056, pod protan/deutan simulacijom RGB dist 31–61/441 —
boja sama NIJE pouzdano razlučiva, posebno uz XP čip u istom panelu. Kandidat trajne korekcije:
pomak partial hue prema 45 (zahtijeva rekalibraciju kontrasta).

### 2.3 Mastery gradient (P(L) low→high) — sekvencijalan, CB-safe

Plavo→cijan sweep (hue 260→190), **monoton po svjetlini** (primarni CB-safe signal — čitljiv i u
grayscaleu). Isti gradijent u barovima I krivuljama. Smjer svjetline je per-tema (na bijelom: više
mastery = tamnije/zasićenije; na tamnom: više mastery = svjetlije) — u OBJE teme više mastery = veća
salijentnost.

| Stop | Light | Dark |
|---|---|---|
| `--mastery-0` | `oklch(0.85 0.05 260)` | `oklch(0.42 0.05 260)` |
| `--mastery-25` | `oklch(0.74 0.08 245)` | `oklch(0.53 0.08 245)` |
| `--mastery-50` | `oklch(0.63 0.11 225)` | `oklch(0.64 0.10 225)` |
| `--mastery-75` | `oklch(0.53 0.086 205)` | `oklch(0.75 0.11 205)` |
| `--mastery-100` | `oklch(0.44 0.072 190)` | `oklch(0.86 0.12 190)` |

(Light 75/100 chroma spuštena na sRGB gamut-max za teal pojas — verificirano skriptom.)

> **Kontrast — izmjereno u 4.4c (NALAZ #33), vrijednosti NISU mijenjane.** Prema `card`
> pozadini: `mastery-0` **2.13:1** dark / **1.58:1** light i `mastery-25` **2.28:1** light su
> ispod 3:1 (WCAG 1.4.11). Rekalibracija je **odbačena**: u light temi `mastery-0` i
> `mastery-25` trebali bi L ≤ 0.665, a `mastery-50` je već na L = 0.63 — tri donja stopa
> stisnula bi se u raspon L 0.63–0.665 i skala bi prestala biti percepcijski kontinuirana.
> Gradijent je **skala salijentnosti, ne nosilac informacije**: svaki potrošač uz njega
> ispisuje brojčanu vrijednost (bar → `role="progressbar"` + tekst %; krivulja → tekstualni
> P(L) + tablica točaka). Ne „popravljati" bez redizajna cijele skale.

### 2.4 Concept-tier skala — 3 koraka (ODVOJENA od difficulty!)

Backend istina: `concepts.tier ∈ {easy, medium, hard}` (`models.py:90`). **Violet, hue 300**,
ordinalna po svjetlini/chromi.

| Token | Light | Dark |
|---|---|---|
| `--tier-easy` | `oklch(0.72 0.09 300)` | `oklch(0.60 0.10 300)` |
| `--tier-medium` | `oklch(0.55 0.14 300)` | `oklch(0.70 0.13 300)` |
| `--tier-hard` | `oklch(0.45 0.18 300)` | `oklch(0.80 0.11 300)` |

Svaki korak ima `-foreground` par (tekst na chip fillu, ≥4.5:1 verificirano per-tema — u lightu
medium/hard nose near-white, easy near-black; u darku svi near-black).

### 2.5 Module-difficulty skala — 5 koraka (ODVOJENA od tier!)

Backend istina: `modules.difficulty ∈ {beginner, intermediate, advanced, expert, cross_module}`
(`models.py:71`). **Magenta, hue 345**, ordinalna beginner→expert; `cross_module` je transverzalna
kategorija (modul 0) — desaturirana, namjerno IZVAN ordinalnog niza.

| Token | Light | Dark |
|---|---|---|
| `--difficulty-beginner` | `oklch(0.78 0.06 345)` | `oklch(0.61 0.08 345)` |
| `--difficulty-intermediate` | `oklch(0.68 0.10 345)` | `oklch(0.66 0.11 345)` |
| `--difficulty-advanced` | `oklch(0.57 0.14 345)` | `oklch(0.74 0.13 345)` |
| `--difficulty-expert` | `oklch(0.46 0.18 345)` | `oklch(0.82 0.105 345)` |
| `--difficulty-cross-module` | `oklch(0.55 0.03 345)` | `oklch(0.68 0.03 345)` |

Svaki korak ima `-foreground` par (tekst na chip fillu, ≥4.5:1 verificirano per-tema — u lightu
advanced/expert/cross nose near-white, beginner/intermediate near-black; u darku svi near-black).

### 2.6 Data-viz paleta (Recharts)

**Kategorijska** — zamjenjuje shadcn-neutralne `--chart-1..5` placeholdere (svjesna, dopuštena iznimka
od "ne diraj postojeće"). Hue-razmaknuta, svaka serija razlučiva i po svjetlini:

| Token | Light | Dark | Hue |
|---|---|---|---|
| `--chart-1` | `oklch(0.55 0.15 250)` | `oklch(0.70 0.14 250)` | plava |
| `--chart-2` | `oklch(0.55 0.094 185)` | `oklch(0.75 0.12 185)` | teal |
| `--chart-3` | `oklch(0.55 0.16 300)` | `oklch(0.72 0.13 300)` | violet |
| `--chart-4` | `oklch(0.58 0.16 345)` | `oklch(0.74 0.13 345)` | magenta |
| `--chart-5` | `oklch(0.60 0.12 75)` | `oklch(0.80 0.14 80)` | amber |

**Sekvencijalna** = mastery gradient (§2.3) — BKT krivulje i mastery barovi dijele istu skalu (plan §3.2).

### 2.7 ⚠️ CROSS-SCALE GUARD (obavezno pravilo za sve buduće faze)

1. **Tier i difficulty NE koriste** correct/incorrect hue (150/25) **ni** amber accent (70–85).
   → tier=300 (violet), difficulty=345 (magenta) ✓
2. **Mastery gradient hue-distinktan** od accenta i semantike → mastery 190–260 vs {25, 55, 70–85, 150} ✓
3. **Mastery monoton po svjetlini** (CB-safe primarni kanal) ✓
4. Nijedna nova skala/komponenta ne smije uvesti boju koja se hue-preklapa s tuđom semantikom.
   Hue mapa sustava: **25 incorrect · 55 partial(rezerv.) · 70–85 accent · 150 correct ·
   190–260 mastery · 300 tier · 345 difficulty**.

---

## 3. Tipografija

- **Sans (UI):** Geist Variable — **ZAKLJUČAN** (`@fontsource-variable/geist`, self-hosted). `--font-sans`.
- **Mono (SQL, rezultati, kod):** JetBrains Mono Variable (`@fontsource-variable/jetbrains-mono`,
  self-hosted, isti fontsource obrazac). `--font-mono`.
- **Bez CDN-a / Google Fonts importa** — sve self-hosted (radi offline, bez FOUC layouta).
- **Modularna skala 1.250** (baza 1rem): xs 0.64 · sm 0.8 · base 1 · lg 1.25 · xl 1.563 ·
  2xl 1.953 · 3xl 2.441 · 4xl 3.052 · 5xl 3.815 (rem).
- Line-height: gušći za headinge (1.15–1.3), 1.5 za tijelo, 1.6 za duži tekst zadataka.
  Tracking: headinzi `-0.02em`, mono podaci `0` (nikad negativan tracking na mono).

---

## 4. Prostor, radijusi, elevacija

- **Spacing:** Tailwind default skala, **4px baza** (`--spacing: 0.25rem`) — zadržana, ne redefinira se.
  Velikodušan prostor: sekcije ≥ `gap-8` (32px), kartice `p-6` (24px), gušći data-gridovi `gap-4`.
- **Radijusi:** shadcn-seedana skala iz `--radius: 0.625rem` (sm→4xl) — zadržana.
- **Elevacija:** dark tema = **surface step + border** (card 0.205 na bg 0.145 + `--border`), NE sjene
  (sjene su nevidljive na tamnom). Light tema = Tailwind default `shadow-sm/md/lg` (suptilno).
  Nikad `shadow-xl+` — nije "mirna konzola".

---

## 5. Motion

Tokeni u `@theme` — **samo vrijednosti**. Motion lib (`framer-motion`/`motion`) **nije u
`package.json` i ne dolazi**: Faza 4.6 (motion + WebSocket) je REZANA (v. `docs/errata.md`,
§„Opseg implementacije — REZANE faze" + revizija 2026-08-09). Sav motion u aplikaciji je
CSS — `tw-animate-css` (`animate-in`, `fade-in`, `slide-in-*`) + ovi tokeni. Dodavanje
motion liba traži izričitu odluku, nije zatečeni plan:

| Token | Vrijednost | Namjena |
|---|---|---|
| `--ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | opći prijelazi, hover/press |
| `--ease-entrance` | `cubic-bezier(0.16, 1, 0.3, 1)` | ulazi panela/kartica (decelerate-settle) |
| `--ease-exit` | `cubic-bezier(0.4, 0, 1, 1)` | izlazi (brzi accelerate-out) |
| `--ease-reward` | `cubic-bezier(0.34, 1.25, 0.64, 1)` | XP/badge/level (blagi overshoot) |
| `--duration-instant` | `100ms` | hover, press |
| `--duration-fast` | `160ms` | mikrointerakcije |
| `--duration-base` | `240ms` | paneli, fade |
| `--duration-slow` | `400ms` | page transitions |
| `--duration-reward` | `700ms` | ⚠️ **NEKORIŠTEN** — bio rezerviran za count-up envelope NEIZVEDENE Faze 4.6 (provjereno grepom 2026-07-26: 0 pogodaka na `duration-reward` u `frontend/src`). OSTAJE radi cjelovitosti ljestvice instant→fast→base→slow→reward, ne kao najava rada |

Pravila: sve animacije poštuju `prefers-reduced-motion` · bez layout-shift hovera (translateY max 1–2px,
nikad scale koji pomiče susjede) · reward animacije SAMO na accent-warm događajima · svaka animacija
prolazi `/review-animations` gate.

⚠️ **Doseg gatea, zatečeno stanje:** `/review-animations` je stvarno pokrenut **samo nad
Task screenom** (4.3). Faza 4.6, koja ga je trebala pokrenuti globalno, je REZANA →
globalni prolaz **nikad se nije dogodio** i ne planira se. `prefers-reduced-motion` je
pokriven **univerzalnim** guardom u `index.css` (`@media (prefers-reduced-motion: reduce)`
nad `*`), ne per-komponentnim opt-inom, pa pravilo vrijedi i bez gatea. Za svaku NOVU
animiranu površinu gate ostaje obavezan.

---

## 6. Monaco editor

Custom tema izvedena iz tokena (NE default `vs-dark`): ista pozadina kao `--card`, isti amber accent,
JetBrains Mono. Definicija: `frontend/src/lib/monaco-theme.ts` (vrijednosni objekt; paket
`@monaco-editor/react` dolazi tek u 4.3). SQL keywords = chart-1 plava, stringovi = correct zelena,
brojevi = chart-2 teal, komentari = muted, funkcije = chart-3 violet.

---

## 7. Komponente — pravila

- shadcn/ui komponente **vuku tokene** (nikad hardkodirana boja po komponenti).
- Svaka data komponenta ima dizajnirana 4 stanja: **loading (skeleton, ne spinner) / empty (poziv na
  akciju) / error (oporavljiv) / success** (plan §3.4; primitivi u 4.1c).
- Ikone: **lucide-react** isključivo (nikad emoji kao ikona).
- Čipovi koncepata: tier boja (§2.4); module cards: difficulty boja (§2.5); mastery prikazi: §2.3.
- `cursor-pointer` na svemu klikabilnom; focus-visible prsten na SVEMU interaktivnom (uklj. Monaco).

## 8. Anti-patterns (NE koristi)

- ❌ Playful/vibrant/kids estetika, konfeti-spam, veliki dekorativni hero blokovi, video pozadine
- ❌ Boje mimo token sustava; miješanje skala (tier boja na difficulty i obratno)
- ❌ `partial` verdikt prenesen SAMO bojom (aktivan od 4.3c — ikona+tekst obavezni; vidi §2.2)
- ❌ Emoji kao ikone; nevidljivi fokus; instant state-change bez tranzicije; layout-shift hover
- ❌ Sjene kao elevacija u dark temi; `shadow-xl+` bilo gdje
- ❌ Google Fonts CDN import (sve self-hosted)

## 9. Pre-delivery checklist (svaka komponenta, 4.2–4.7)

- [ ] Boje isključivo iz tokena; prava skala za pravu domenu (tier≠difficulty≠mastery)
- [ ] Kontrast: tekst ≥4.5:1, UI grafika ≥3:1 (obje teme)
- [ ] Fokus vidljiv, tipkovnička navigacija radi
- [ ] `prefers-reduced-motion` poštovan; motion iz tokena (§5)
- [ ] Loading=skeleton / empty / error / success stanja dizajnirana
- [ ] Dark I light provjereni (dark-first, light ravnopravan)
- [ ] Responsive: 1440/1024 primarno, 768 upotrebljivo
