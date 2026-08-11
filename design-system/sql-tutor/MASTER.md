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

Sve boje su **oklch**, definirane u `frontend/src/index.css` kao CSS varijable u **jednom `:root`
bloku**, mapirane u `@theme inline` za Tailwind utility-e.

> ⟳ **APLIKACIJA JE DARK-ONLY (Faza 4.7 redizajn, 2026-08-10).** Light tema je ukinuta: nema
> `.dark` bloka, `@custom-variant dark`, `ThemeProvider`a ni toggla. Svaka tvrdnja „light / dark"
> ispod odnosi se na povijest, ne na zatečeno stanje. Snimke `08-fipa-agent-log-light.png` i
> `09-profil-bkt-krivulje-light.png` time postaju **nevažeće**.
>
> ⟳ **BASE PALETA VIŠE NIJE SHADCN-SEEDANA.** Tvrdnja „u pravilu se ne dira" vrijedila je do 4.7.
> Cijela KROMA — `background`, `card`, `popover`, `muted`, `secondary`, `accent`, `sidebar*`,
> `foreground`, `muted-foreground`, `border`, `input`, `ring`, `primary` — prebojena je u
> **ink-indigo, hue 280**, uz **nepromijenjenu ljestvicu svjetlina** (`background` 0,145 →
> `card` 0,205 → `muted` 0,269; Δ +0,060 i +0,064, identično zatečenom).
>
> **Hue 280 nije izveden iz ΔE mjere** — ta mjera hue ne razlikuje (cijela krivulja 0°–360°
> varira 0,1192–0,1587, nigdje kolizije). Bira ga pravilo §2.7: generički UI ne smije **preuzeti
> hue-pojas** semantičke skale. 280° je središte jedine upotrebljive praznine (260°–300°), na
> točno 20° i od mastery i od tiera. Detalji: `docs/faza-4.7-redizajn-korak-0.md` §C.2.
>
> **Obrisano:** `--sidebar-primary` i `--sidebar-primary-foreground` — 0 potrošača, a
> `--sidebar-primary` je bio jedini KROMA token u semantičkom prostoru
> (`oklch(0.488 0.243 264.376)`: najviša chroma u paleti, 4,4° od ruba mastery skale).
>
> ⟳ **IZNIMKA (Faza 4.7-4c, 2026-08-10) — tri shadcn-seedana tokena promijenjena su u LIGHT temi**,
> uz mjerenje i uz odluku korisnika. Dark je netaknut.
>
> | Token | prije | poslije | razlog |
> |---|---|---|---|
> | `--muted-foreground` | `oklch(0.556 0 0)` | `oklch(0.528 0 0)` | padao je AA na `-soft` plohama (4,18–4,26) i na `bg-muted` (4,34); sada ≥4,71 na svim stvarnim plohama |
> | `--ring` | `oklch(0.708 0 0)` | `oklch(0.556 0 0)` | fokus indikator bio 2,48–2,59:1, ispod 3:1 (SC 1.4.11); sada ≥4,18 na svim plohama |
> | `--sidebar-ring` | `oklch(0.708 0 0)` | `oklch(0.556 0 0)` | neovisan literal iste vrijednosti — mijenja se istovremeno da ne divergira tiho |
>
> Puna matrica: `docs/faza-4.7-kontrast-matrica.md`. Tvrdnja o nediranju vrijedila je do 4.7.
> (Te su tri light vrijednosti nestale s light temom u stageu 1 redizajna; redak ostaje kao
> zapis odluke, ne kao opis zatečenog stanja.)

#### 🔒 INVARIJANTA: `--ring` je AKROMATSKI, i to nije stvar ukusa

`--ring` i `--sidebar-ring` = **`oklch(0.62 0 0)`**. Chroma **mora** ostati 0.

**Razlog je strukturni, ne estetski.** Prsten fokusa okružuje sadržaj, pa mu je sve unutra
sukorišteno — a `ConceptRow.tsx:112-120` stavlja **tier čip unutar `<Link>`a** koji nosi
`focus-visible:outline-ring`. Tier skala se u paleti proteže **L 0,60 → 0,80 na hue 300**, dakle
kroz cijeli upotrebljiv raspon svjetline prstena. Svaki **kromatski** prsten u tom pojasu ulazi u
njezin prostor:

| `--ring` | ΔE do najbližeg sukorištenog | najbliži | kontrast (najgora ploha od 11) |
|---|:---:|---|:---:|
| `oklch(0.556 0 0)` (do 4.7) | 0,084 | `mastery-25` | 3,21 |
| `oklch(0.62 0.04 280)` (tintan) | **0,067** | `tier-easy` | 4,15 |
| **`oklch(0.62 0 0)`** | **0,102** | `mastery-50` | **4,18** |

Tinta ne kupuje ništa, a plaća koliziju: ista svjetlina **bez** krome diže ΔE za **52 %** uz
jednak kontrast. Sve semantičke skale imaju C ≥ 0,03 — akromatski prsten je **po konstrukciji**
izvan svih njih. Ploha smije nositi identitet palete; prsten mora nositi razlučivost.

🔴 **Ako se `--ring` ikad tintira, provjera koja to hvata je**
`python3 scripts/a11y/contrast_matrix.py --delta-e`, ne matrica kontrasta. Nalaz: N-12.

#### 🔴 `--border` i `--input` NE dosežu 3:1 — ni prije ni poslije redizajna

Da se za godinu dana ne pročita kao „popravljeno". Izmjereno 2026-08-10, alpha-kompozitirano:

| obrub | prije 4.7 | poslije 4.7 | prag |
|---|:---:|:---:|:---:|
| `border` nad `background` / `card` / `muted` | 1,25 / 1,32 / 1,37 | **1,27 / 1,34 / 1,36** | 3,00 |
| `input` nad `background` / `card` / `muted` | 1,47 / 1,57 / 1,62 | **1,50 / 1,58 / 1,60** | 3,00 |
| `sidebar-border` nad `sidebar` | 1,32 | **1,34** | 3,00 |

Redizajn ih je vratio **na paritet** (alfa `border` 10→15 %, `input` 15→22 %) jer bi ih tintana
baza inače spustila — bijela s alfom je najsvjetlija moguća, tintana nije. **Paritet nije prolaz.**
Doseći stvarnih 3:1 traži alfu **48–50 %**, što je drugi vizualni jezik i **dizajnerska odluka**,
ne korekcija palete.

Ovo je izravan nastavak **poučka #33**: docstring je nekoć tvrdio „border ≥3:1", a stvarnost je
bila upola manja. Zato je svih 7 parova sada u `pairs.py` — tvrdnja više ne može živjeti nemjerena.

### 2.1 Accent — topli amber (jedini "warm" u sustavu)

Rezerviran ISKLJUČIVO za: XP, level, streak, badge, progres, CTA "sljedeći zadatak".
Ne koristi se za dekoraciju, navigaciju ni neutralne akcije.

| Token | Light | Dark | Uloga |
|---|---|---|---|
| `--accent-warm` | `oklch(0.66 0.13 72)` | `oklch(0.80 0.15 80)` | fill (XP bar, badge, progres). ⚠️ **Ploha:** ≥3:1 vrijedi vs `card`/`background`; kao **alpha-kompozit** (`accent-warm/5,10,20`) NE doseže 3:1 vs `card` (1,05–1,52 light, 1,09–1,52 dark, mjereno 2026-08-10) — tint je ondje **ukras**, stanje nose ikona + tekst. V. errata i `docs/faza-4.7-kontrast-matrica.md` |
| `--accent-warm-foreground` | `oklch(0.25 0.04 75)` | `oklch(0.22 0.04 80)` | tekst NA punom fillu `--accent-warm` — **ploha: `accent-warm`**, 5,04:1 light / 9,15:1 dark (2026-08-10) ✓ |
| `--accent-warm-text` | `oklch(0.514 0.12 70)` ⟳ | `oklch(0.80 0.15 80)` | amber tekst na plohi. ⟳ **light potamnjen 0.56 → 0.514 u 4.7-4c** jer je stara vrijednost padala na `-soft` (4,22–4,30) i na `accent-warm/20` (3,89). **Ploha:** ≥4,72:1 na SVE stvarne plohe (`card` 5,79 · `sidebar` 5,55 · `muted` 5,31 · `accent-warm/10` 5,24 · `-soft` 5,12–5,21 · `accent-warm/20` **4,72** ← vezujuća), mjereno 2026-08-10 |

> Napomena o imenu: shadcn već zauzima `--accent` (neutralni hover) — topli accent je zato
> `--accent-warm`, bez gaženja postojećih shadcn stanja.

### 2.2 Semantika verdicta

| Token | Light — **ploha `card`/`background` (bijela)**, ≥4.5 ✓ | Dark — **ploha `background` (0.145)**, ≥4.5 ✓ |
|---|---|---|
| `--correct` | `oklch(0.52 0.13 150)` | `oklch(0.75 0.15 150)` |
| `--incorrect` | `oklch(0.53 0.19 25)` | `oklch(0.70 0.19 25)` |
| `--partial` | `oklch(0.53 0.11 55)` | `oklch(0.78 0.13 60)` |
| `--neutral` | `oklch(0.50 0.02 260)` | `oklch(0.72 0.02 260)` |

> ⟳ **`--neutral-soft` = `oklch(0.28 0.02 260)` — NOVO u 4.7, s NULA potrošača, namjerno.**
> Postoji da N-10 (`ErrorState` posuđuje `incorrect-soft` za **sistemsku** grešku, pa student ne
> razlučuje vlastiti neuspjeh od kvara aplikacije) ima gdje sletjeti, a da se `index.css` i ovaj
> dokument ne otvaraju drugi put. Žičenje je **stage 2**.
>
> 🔴 **Obrazac `-soft` se ovdje LOMI.** Zatečeni `-soft` imaju L = 0,240 (sva tri), hue baze, i
> C = 0,035–0,040 (0,18–0,31 × C baze). Ali te su baze **kromatske** (C 0,13–0,19), a `--neutral`
> ima C = 0,02. Omjerno bi dalo C ≈ 0,005 (nevidljivo od `card`); apsolutno C ≈ 0,04, tj. soft
> **kromatskiji od vlastite baze** — obrnuto od onoga što „-soft" znači.
>
> Zato je reproducirano ono što obrazac **postiže**, a ne brojka kojom to postiže: ΔE prema `card`
> 0,0761 (zatečeni raspon 0,0624–0,0746) i ΔE prema braći ≥ 0,0635 (zatečeni međusobno
> 0,0231–0,0666). ⚠️ **L = 0,28, ne 0,240** — na 0,240 uz C 0,02 ploha je na ΔE 0,0493 od
> `incorrect-soft`, ispod praga kolizije; panel sistemske greške koji se ne razlikuje od panela
> netočnog odgovora **jest N-10, samo obrnuto**. Separaciju nosi svjetlina, ne kroma.

Svaki ima `-soft` varijantu (suptilna pozadina feedback banera). ⚠️ **Ploha:** tvrdnja da tekst-token
preko nje ostaje AA vrijedi za **verdict tokene** (`--correct` 4,67 · `--incorrect` 5,15 ·
`--partial` 4,86 light, mjereno 2026-08-10) — ali do 4.7-4c **NIJE** vrijedila za
`--muted-foreground` (4,18–4,26) ni `--accent-warm-text` (4,22–4,30), koji na tim plohama također
stoje (FeedbackPanel, ErrorState, RunResultPanel). Oba su potamnjena u 4c; v. errata i matricu.

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

⟳ **2026-08-10 (korisnikova odluka):** skala prelazi s jednohuene rampe (violet 300, samo
L/C) na **HUE RAMPU hladno→toplo** — razina se čita iz TONA. Svijetli registar (čip s
tamnim tekstom). Backend istina nepromijenjena: `concepts.tier ∈ {easy, medium, hard}`.

| Token | Vrijednost (dark-only) | ton |
|---|---|---|
| `--tier-easy` | `oklch(0.75 0.11 255)` | plava |
| `--tier-medium` | `oklch(0.72 0.15 295)` | ljubičasta |
| `--tier-hard` | `oklch(0.74 0.19 335)` | magenta |

C raste s razinom (0,11 → 0,19 — „toplina"), L ~konstantan (ujednačena težina čipa).
`-foreground` = tamni `oklch(0.145 0 0)` na sva tri; tekst na fillu **7,60–8,91** ✅.
Susjedne razine ΔE **0,1011 / 0,1238**.

### 2.5 Module-difficulty skala — 5 koraka (ODVOJENA od tier!)

⟳ **2026-08-10 (korisnikova odluka):** ista hue logika hladno→toplo, ali **TAMNI registar**
(badge sa svijetlim tekstom) — dvije se skale više ne razdvajaju hueom (300 vs 345) nego
REGISTROM: tier×difficulty min ΔE **0,3754**. `cross_module` desaturiran, izvan rampe.

| Token | Vrijednost (dark-only) | ton |
|---|---|---|
| `--difficulty-beginner` | `oklch(0.38 0.058 205)` | teal (⟳ s 245: premala razlika od Srednje, ΔE 0,0597 → 0,1027; C ispod gamut maksimuma 0,0649) |
| `--difficulty-intermediate` | `oklch(0.35 0.09 285)` | indigo |
| `--difficulty-advanced` | `oklch(0.34 0.10 320)` | ljubičasto-magenta |
| `--difficulty-expert` | `oklch(0.35 0.12 355)` | vruća magenta |
| `--difficulty-cross-module` | `oklch(0.34 0.02 300)` | neutralna |

`-foreground` = svijetli tint istog huea `oklch(0.95 0.02 h)`; tekst na fillu
**8,49–10,58** ✅. Susjedne razine ΔE **0,0588–0,1102** (Početna×Srednja 0,1027). Min ΔE
prema sukorištenom skupu (verdict + -soft, mastery ×5, accent-warm, muted, card + vrh
kartice, primary): **0,0615** (cross vs neutral-soft; beginner vs mastery-0 0,0643 —
sve ≥ prag 0,05).

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
   ⟳ 2026-08-10: → tier 255–335 i difficulty 245–355 (obje hladna strana kruga; najbliži
   dodir semantici je tier-hard 335 vs incorrect 25 → ΔE 0,1655 ✓)
2. **Mastery gradient hue-distinktan** od accenta i semantike → mastery 190–260 vs {25, 55, 70–85, 150} ✓
3. **Mastery monoton po svjetlini** (CB-safe primarni kanal) ✓
4. Nijedna nova skala/komponenta ne smije uvesti boju koja se hue-preklapa s tuđom semantikom.
   ⟳ Hue mapa sustava (2026-08-10): **25 incorrect · 55 partial(rezerv.) · 70–85 accent ·
   150 correct · 190–260 mastery · 245–355 tier+difficulty**. Tier i difficulty dijele
   pojas, a razdvaja ih **REGISTAR** (svijetli čip vs tamni badge, min ΔE 0,3754) —
   hue-preklop unutar istog registra i dalje je zabranjen.

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

⟳ **4.6 se IZVODI unutar 4.7 (stage 3, DIO B; 2026-08-10)** — prijašnja formulacija „4.6
je REZANA" vrijedi još samo za WebSocket i ⌘K paletu (v. errata §REZANE faze, 4. revizija).
`framer-motion`/`motion` i dalje **ne dolaze** — sav 4.6 motion je CSS + minimalni JS kroz
ove tokene. Jedina nova ovisnost: `canvas-confetti` (~7 kB gzip, dinamički import → nije u
initial bundleu), samo za level-up burst (B.5).
⚠️ Trajanja rade kroz `@utility` most u `index.css`, ne kroz `@theme` (N-18: `--duration-*`
nije utility namespace u TW v4 — do 2026-08-10 su SVE tranzicije tiho radile na 150 ms):

| Token | Vrijednost | Namjena |
|---|---|---|
| `--ease-standard` | `cubic-bezier(0.2, 0, 0, 1)` | opći prijelazi, hover/press |
| `--ease-entrance` | `cubic-bezier(0.16, 1, 0.3, 1)` | ulazi panela/kartica (decelerate-settle) |
| `--ease-exit` | `cubic-bezier(0.4, 0, 1, 1)` | izlazi (brzi accelerate-out) |
| `--ease-reward` | `cubic-bezier(0.34, 1.25, 0.64, 1)` | XP/badge/level (blagi overshoot) |
| `--duration-instant` | `100ms` | hover, press |
| `--duration-fast` | `160ms` | mikrointerakcije |
| `--duration-base` | `240ms` | paneli, fade · ⟳ i hover kartica (2026-08-10, po mockupu `.card:hover`: 240 ms + CSS `ease` + sjena 0 10px 30px; nav stavke: 160 ms + `ease`, translateX(2px) + scale ikone 1.08). 🔴 U tranzicijskim listama stoji **`translate`/`scale`**, ne `transform` — TW v4 translate/scale utilityji pišu ta svojstva; s `transform` u listi pomak je TRENUTAN (uzrok „trzaja" 4.6 B.1, otkriven i popravljen 2026-08-10) |
| `--duration-slow` | `400ms` | page transitions |
| `--duration-reward` | `700ms` | ⟳ **KORIŠTEN od B.5 (2026-08-10)** — točno za ono za što je rezerviran: XP count-up envelope (`useXpCountUp` čita token iz computed stylea) + `level-pulse` keyframe |

Pravila: sve animacije poštuju `prefers-reduced-motion` · bez layout-shift hovera (translateY max 1–2px,
nikad scale koji pomiče susjede) · reward animacije SAMO na accent-warm događajima · svaka animacija
prolazi `/review-animations` gate.

⚠️ **JEDNA BESKONAČNA PETLJA — `bar-shimmer` na XP baru** (zraka koja prolazi kroz traku,
ciklus 2 s: prolaz 1,3 s + stanka 0,7 s). Sve ostale animacije poštuju obrazac „pokret dulji
od 5 s ograniči TRAJANJEM" (WCAG 2.2.2; v. `flame-flicker` 3×600 ms, `level-pulse`,
`brand-pop`) — XP zraka je **odstupanje na izričit korisnikov zahtjev** („treba ići svake 2
sekunde", 2026-08-10). Ublažavanje: pokret je suptilan (Δ svjetline ~95/255 na uskom pojasu,
bez pomicanja sadržaja), nije uz tekst koji se čita, i **globalni `prefers-reduced-motion`
guard ga gasi u cijelosti**. 2.2.2 traži mehanizam pauze za pokret >5 s koji je *dio*
sadržaja — ovdje je dekorativan, ali odstupanje se ne prešućuje.

⚠️ **Doseg gatea:** `/review-animations` je stvarno pokrenut samo nad Task screenom (4.3).
⟳ B/4.6 (2026-08-10): skupine B.1–B.6 prošle su **ručni review po istim kriterijima**
(tokeni · reduced-motion · 2.2.2 · podaci nedirnuti) jer `/review-animations` nije bio
dostupan u sesiji — svaki commit skupine nosi checklist. `prefers-reduced-motion` je
pokriven **univerzalnim** guardom u `index.css` (trajanje I delay), a komponente s hover
POMAKOM dodaju vlastite `motion-reduce:` klase (guard ruši trajanje, ne ciljno stanje).
Za svaku NOVU animiranu površinu gate (ili njegov dokumentirani ručni ekvivalent) ostaje
obavezan.

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
- ❌ Sjene kao STATIČKA elevacija u dark temi; `shadow-xl+` bilo gdje. ⟳ B.1 (2026-08-10):
  prolazna hover sjena na kartici (`hover:shadow-lg`, uz lift −2px) je svjesna iznimka —
  mikrointerakcija, ne elevacijski sustav
- ❌ Google Fonts CDN import (sve self-hosted)

## 9. Pre-delivery checklist (svaka komponenta, 4.2–4.7)

- [ ] Boje isključivo iz tokena; prava skala za pravu domenu (tier≠difficulty≠mastery)
- [ ] Kontrast: tekst ≥4.5:1, UI grafika ≥3:1 (obje teme) — 🔒 **uz NAVEDENU PLOHU**: mjeri se
      prema plohi na kojoj element STVARNO stoji (alpha-kompoziti se kompozitiraju), ne prema `card`
      po defaultu. Tvrdnja o kontrastu bez navedene plohe je nepotpuna tvrdnja.
- [ ] Fokus vidljiv, tipkovnička navigacija radi
- [ ] `prefers-reduced-motion` poštovan; motion iz tokena (§5)
- [ ] Loading=skeleton / empty / error / success stanja dizajnirana
- [ ] Dark I light provjereni (dark-first, light ravnopravan)
- [ ] Responsive: 1440/1024 primarno, 768 upotrebljivo

---

## 2.8 Gradijenti — granica, i zašto je pomaknuta

⟳ **Faza 4.7-r2.** Do r2 je zabrana bila globalna (KORAK 0 §R-2: „gradijent iz mockupa ne
ulazi"). To je bilo **pretjerano**: zabranjivalo je i mjesta koja ne nose status. Granica je
pomaknuta na pravilo koje se može provjeriti:

> **Gradijent je ZABRANJEN gdje element može čitati kao NOSITELJ STATUSA.**
> Dopušten je na chromeu koji status ne nosi.

| ZABRANJENO | DOPUŠTENO |
|---|---|
| ~~trake napretka~~ · čipovi · bedževi · verdict plohe · **bilo što uz tier/mastery/verdict** | brand ikona · wordmark · pozadinski glow · hairline/separator · hover obrub kartice · aktivni nav indikator (nosi poziciju, ne status) · **CTA gumb** · **XP bar** (v. iznimku) |

⟳ **IZNIMKA ZA XP BAR (korisnikova odluka, 2026-08-10).** „Trake napretka" ostaju
zabranjene kao skupina, ali XP bar iz njih **izlazi**: on nije statusna skala nego
**reward domena** (`accent-warm`, MASTER §2.1) — ne kodira mastery ni verdict, nego napredak
prema idućem levelu. Mastery trake (`MasteryBar` u `ConceptRow`, `MasteryHighlights`,
`ModuleCard`) i dalje su **bez gradijenta**, jer njihova boja JEST skala.

### 🔒 Dvije invarijante

**1. Svaki gradijent je JEDNOHUEN (h280) — putuju samo L i C.** Prelazak hue-pojasa ulazi u
prostor neke skale. Mockupov `--grad-primary` (`#A78BFA` h≈293,5 → `#38D6F5` h≈214,5) je
zato odbijen: prvi kraj je **ΔE 0,0345 od `tier-medium`** (sukorišteni par — Submit i
`ConceptChip` su na istom ekranu), drugi leži unutar mastery pojasa 190–260.

**2. Srednji stop se UPISUJE, ne prepušta.** CSS i SVG interpoliraju u sRGB ako se ne kaže
drukčije, a sve su brojke ispod mjerene na **oklch-sredini**. Bez upisanog srednjeg stopa
mjerenje ne opisuje ono što se renderira.

### Što je izmjereno (2026-08-10, `--grad-*` u `index.css`; CTA i glow revidirani u r3 A.1)

| gradijent | raspon | najgori kontrast | ΔE do najbližeg sukorištenog |
|---|---|:---:|:---:|
| `--grad-brand` (ikona) | `0,55 0,15` → `0,78 0,11` | 3,56 vs `sidebar` | — (skup je **prazan**) |
| `--grad-wordmark` | `0,60 0,155` → `0,90 0,045` | 4,38 vs `sidebar` | — (skup je **prazan**) |
| `--grad-cta` (r3 A.1) | `0,85 0,065` → `0,97 0,013` | **11,30** (tamni tekst) · 11,30 (fill vs `card`) | **0,1956** (`tier-hard`; ⟳ 2026-08-10 novi tier-hard 335 — prije 0,0734) |
| `--glow-a` / `--glow-b` (r3 A.1) | h280 @ 18 % / 12 % | `foreground` 18,16 → **14,40** (puna α) | — |
| `--grad-sidebar` (r3 A.2a; ⟳ staklo 2026-08-10) | `0,175 0,035` → `0,148 0,03` @ **92 % alfe** (180°, tone prema dnu) | tamnije od svih ranijih iteracija → ranije brojke su donje granice | — (skup je **prazan**) |
| `--grad-xp` (XP bar, 2026-08-10) | `0,80 0,15 h80` → `0,72 0,17 h45` (90°, žuto→crveno) | fill je grafika, ne tekst | **0,0685** (`incorrect`) · 0,1266 od `accent-warm` |

🔴 **`--grad-xp` je JEDINI gradijent koji prelazi hue-pojas** (80 → 45) — dopuštena iznimka
od invarijante 1, jer cijeli raspon ostaje **unutar reward domene** (`accent-warm` 70–85 →
topliji kraj) i ne ulazi ni u jednu skalu. Kraj je od `incorrect` (h25) na ΔE **0,0685** ✓.
⚠️ Tranzit kroz ~h60 je na ΔE 0,0364 od `partial` — **svjesno**: XP bar (Dashboard hero) i
verdict panel (Task) nisu nikad u istom kadru, a `partial` obvezno nosi ikonu + tekst (§2.2).

**Staklo sidebara** (`.liquid-glass`, `index.css`): polupropusna ploha + `backdrop-filter:
blur(8px) saturate(1.7)` + dijagonalni odsjaj + specularni unutarnji rub. Tonalitet je
namjerno **taman** (donji stop 0,148 ≈ `background` 0,145) — ploha se uklapa u pozadinu, a
granicu drži `border-r` + specularni rub.
| `--grad-card` (r3 A.2b) | `0,2175 0,0505` → `0,1925 0,0455` (sredina == `--card`) | `muted-fg` **6,73** na vrhu · `fg` 16,07 | min **0,20** (mastery-0); `-soft` 0,0704–0,0880; `muted` 0,0524 (vrh spušten s 0,22 zbog 0,0498) |

⟳ **r3 A.1 (2026-08-10):** CTA start `0,90 0,045` → `0,85 0,065` po pikselnom kriteriju
vidljivosti (§3.3): Δ kroz površinu **R 24 · G 22 → R 40 · G 37** (B ~5 — pri vrhu gamuta
B nema kamo, v. (a) niže). Napomena poštenja: **stari CTA je prag R/G ≥ 15 već prolazio**;
raspon je proširen odlukom o istaknutosti, ne zbog pada na pragu. ΔE do `tier-hard`
0,1217 → 0,0734 — guard ≥ 0,05 i dalje drži (ravni `--primary`: 0,1525).

**Sidebar nema nijedan semantički token** (`grep` nad `AppShell.tsx`: nav je
`muted-foreground`, aktivna stavka `sidebar-accent`) → ondje ograničenja ΔE nema, pa brand
smije biti pun i vidljiv. Logotip je uz to **izuzet od 1.4.3/1.4.11**; 3,56:1 je mjera
vidljivosti, ne zahtjev.

### 🔴 Tri stvari koje su gradijente OBLIKOVALE, a nisu očite

**(a) sRGB gamut na h280 se ruši prema bijelom.** `C max` = 0,102 @ L 0,80 → 0,049 @ L 0,90
→ **0,014 @ L 0,97**. Zato svijetli CTA gradijent ne može biti jako obojen; prvi predloženi
(`0,88 0,06 → 0,97 0,02`) bio je **izvan gamuta na oba kraja**.

**(b) Postoji mrtvi pojas svjetline L 0,557–0,606 u kojem NIJEDAN tekst ne prolazi AA** na
h280 fillu: svijetli `foreground` pada ispod 4,50 iznad L 0,557, tamni `primary-foreground`
ispod 4,50 ispod L 0,606. Gradijent koji taj pojas presijeca nema upotrebljivu boju teksta.
Prvi predloženi CTA (`0,45 → 0,68`) presijecao ga je po sredini.

**(c) Tamni CTA je odbijen zbog SC 1.4.11, ne zbog ΔE.** Ispunjen gumb se identificira
ispunom, pa mu granica prema plohi traži 3:1; tamni raspon `0,47 → 0,55` daje **2,43 vs
`card`**. Uz to bi degradirao hijerarhiju: današnji CTA je najsvjetliji element na kartici.
**Zato CTA ostaje SVIJETLI fill s tamnim tekstom — gradijent živi unutar te svjetline.**

### Što NIJE dobilo gradijent, i zašto

**Vlastito ime u naslovu** („Bok, **admin**"). Ime je **sadržaj** → traži AA 4,50 na
najtamnijem kraju, što pri h280 znači L ≥ 0,584. Ali pretraga cijelog prostora
(L 0,60–0,95 × C 0,08–0,18) daje **nula kandidata** koji istovremeno drže AA i ΔE ≥ 0,10
prema tier skali — svaki dovoljno svijetao ton je preblizu `tier-hard` (`0,80 0,11 300`).
Jedina prohodna varijanta bila je tint 0,90 → 0,97, efekt koji se ne vidi. **Ime ostaje
puni `foreground`.** Proračun je umjesto toga otišao u wordmark, gdje ograničenja nema.

---

## 3.1 Display font (Faza 4.7-r2)

**`Bricolage Grotesque Variable`** (`@fontsource-variable/bricolage-grotesque@5.3.0`,
OFL-1.1, os `wght` 200–800). **Nula CDN-a** — lokalni npm asset koji Vite hashira, isti
mehanizam kao Geist i JetBrains Mono.

| gdje | kako |
|---|---|
| `h1`, `h2` | `@layer base { h1, h2 { font-family: var(--font-heading) } }` — jedno mjesto, ne `font-heading` na svaki naslov |
| **svi `CardTitle`** | `ui/card.tsx:41` **već je nosio** `font-heading` — v. ispravak ispod |
| hero brojka levela | `ProgressHero.tsx:26`, utility `font-heading` (utilities > base, pa pobjeđuje nad mono pravilom za brojke) |
| **NIGDJE drugdje** | body ostaje Geist, mono ostaje JetBrains Mono |

> 🔴 **ISPRAVAK VLASTITE TVRDNJE (2026-08-10, 1C t.0a).** U KORAKU 0 §D.2 i u commitu
> `8504f3c` napisao sam da `--font-heading` ima **nula potrošača**. **Netočno.**
> `grep -rn "font-heading" frontend/src` daje **dva**: `ProgressHero.tsx:26` i —
> ključno — **`ui/card.tsx:41`**, gdje `CardTitle` nosi `font-heading` od shadcn setupa.
>
> Dok je `--font-heading` bio alias za `--font-sans`, taj potrošač **nije imao učinak**,
> pa ga je površan grep previdio. Čim je token dobio vlastiti font, display se
> **automatski proširio na SVE naslove kartica** — širi doseg nego što je commit tvrdio.
>
> **Prihvaćeno, ne vraćeno.** Naslovi kartica **jesu** naslovi, pa je proširenje u duhu
> pravila. Legibilnost provjerena na snimci Modula: `CardTitle` je `text-base` (16 px),
> dakle **ispod praga od ~20 px** iz pravila niže — ali su to kratke, poludebele niske
> (`font-medium`), ne tekst za čitanje, i na snimci su jasne.
>
> **Poučak:** token koji je *alias* nema vidljive potrošače, ali ih ima. Prije nego se
> aliasu da vlastita vrijednost, grepa se **ime tokena**, ne njegov učinak.

🔴 **Ne ide na `h3`+ ni na body tekst.** Display crta ima uži razmak i jači kontrast
poteza, pa ispod ~20 px gubi na čitljivosti — a ondje živi većina a11y-kritičnog teksta
(`muted-foreground` na 118 mjesta, uglavnom `text-xs`/`text-sm`). Iznimka su `CardTitle`
niske (16 px), v. ispravak gore.

### Cijena i CLS — izmjereno 2026-08-10

| | prije | poslije | Δ |
|---|---|---|---|
| woff2 u `dist/` | 160 636 B | 229 256 B | +68 620 B |
| **stvarno dohvaćeno (hrvatski)** | — | **60 012 B** | latin 41 344 + latin-ext 18 668 |
| CSS bundle | 56 854 B | 58 071 B | +1 217 B |

`vietnamese` subset (8 608 B) se **nikad ne dohvaća**. `latin-ext` se dohvaća **uvijek**,
jer hrvatski `č ć ž š đ` leže u `U+0100-02BA`, a `latin` pokriva samo `U+0000-00FF`.

**CLS = 0,0055** na hladnom učitavanju Dashboarda (prag „dobar" je 0,1 — dakle **18× ispod**).

🔴 **Zašto je CLS tako nizak, i zašto `size-adjust` NIJE potreban:** fallback u
`--font-heading` je **`"Geist Variable"`, ne `system-ui`**. Geist je body font i već je
učitan kad naslov prvi put crta, a metrički je gotovo identičan Bricolageu:

| font | širina istog naslova | Δ vs Geist |
|---|---|---|
| Bricolage Grotesque | 450,9 px | — |
| **Geist (fallback)** | **449,9 px** | **+0,2 %** |
| system-ui | 521,0 px | +15,8 % |

Da je fallback `system-ui`, swap bi pomicao naslov za ~16 % širine. Ovako je 1 px.
**Zaključak: `font-display: swap` (fontsource default) ostaje, `size-adjust` i `optional`
nisu potrebni.** Ako se lanac fallbacka ikad promijeni, CLS treba **ponovno izmjeriti**.

**Preload:** `index.html` preloada obje osi (`latin` + `latin-ext`) s `crossorigin`.
Vite pri buildu prepisuje `href` u hashirani asset. ⚠️ `crossorigin` je obavezan i za isti
origin — bez njega preglednik dohvati font dvaput i preload odmaže.

---

## 3.2 Mono identitet (Faza 4.7-r2)

Mono nije samo za kod. U ovoj aplikaciji mono znači **„ovo je podatak ili identifikator,
ne proza"** — dio dev-konzolnog glasa iz §1.

| što | kako | zašto |
|---|---|---|
| **sve brojke** | `@layer base { .tabular-nums { font-family: var(--font-mono) } }` | `tabular-nums` je već posvuda gdje stoji brojka (~50 mjesta). Jedno pravilo umjesto 50 poziva → svaka **nova** brojka je dosljedna bez da se netko sjeti |
| **nazivi koncepata** | `font-mono` na `ConceptChip`, `ConceptRow`, `MasteryHighlights` | naziv koncepta (`select_basic`, `INNER JOIN`) je identifikator gradiva |
| ~~sidebar section headeri~~ | ~~`-- učenje` / `-- napredak` / `-- sustav`~~ ⟳ UKLONJENI (2026-08-10, korisnikov zahtjev — nepotrebni) | grupe za čitač i dalje nosi `aria-label` na `<ul>`; mono glas ostaje u level/streak labelama |
| **SQL u editoru** | JetBrains Mono, od 4.3 | — |

🔴 **Promjena obitelji fonta NE mijenja nijedan kontrastni omjer** — WCAG omjer ovisi o
boji, ne o fontu, a nijedna niska ne seli na drugu plohu. Mijenja se **širina**, pa je
provjera prelijevanja **snimka**, ne izračun. (Ovo je iznimka od pravila „svaka nova niska
dobiva izmjeren kontrast": mjeriti bi značilo prepisati brojke koje već stoje u matrici.)

⚠️ **Što NIJE u monou, iako spada u duh pravila:** SQL ključne riječi unutar **opisa
modula i zadataka** (`module.description`, `task.description`) — npr. „Projekcija, FROM,
WHERE, ORDER BY, LIMIT, DISTINCT." To je **slobodan tekst iz baze**; selektivno stiliziranje
tražilo bi parsiranje ili označavanje kojeg u podacima nema. Kandidat za Fazu 6 (uz
promjenu sheme), ne za CSS.

---

## 3.3 Dot-grid i glow (Faza 4.7-r2 · alfe revidirane u r3 A.1)

`body` nosi tri sloja preko `--background`: `--dot-grid` (24×24 px, alfa 12 %) i dva
radijalna glowa (18 % i 12 %), svi h280, svi `background-attachment: fixed` da ne putuju
sa skrolom.

⟳ **r3 A.1 (2026-08-10): alfe 3,5 % → 12 % i 6/4 % → 18/12 %.** r2 alfe birane su samo
po kriteriju „ne smije pokvariti kontrast"; kriterij „mora se vidjeti" nije postojao.
Zato je postavljen **pikselni kriterij vidljivosti: Δ ≥ 15 po sRGB kanalu KROZ površinu**,
mjereno na snimci živog Dashboarda @1440 (dpr 1), ne okom. r2 vrijednosti su taj prag
promašivale višestruko — efekt plaćen, a nevidljiv:

| mjera (pikseli sa snimke) | r2 | **r3** | prag ≥15 |
|---|:---:|:---:|---|
| dot-grid, vrh točke, Δ R·G·B | 7·7·7 | **21·21·23** | ✓ sva tri kanala |
| glow, najjača vidljiva točka, Δ R·G·B | 4·4·7 | **13·14·21** | ✓ na B (nositelj h280 boje); R/G na granici |

🔴 **Glow ima strop, ne samo prag.** Centar (85 %, −10 %) je IZVAN kadra, pa najjača
točka koja se uopće vidi nosi ~0,62 pune alfe (izmjereno). Sva tri kanala ≥ 15 dala bi
tek α 24 % — ali ta uz dot 12 % ruši `muted-foreground` na 4,24 konzervativno → **svjesno
odbijeno**. Kandidati 9/12/15 % (dot) i 12/18/24 % (glow) izmjereni su i snimljeni
(artifact „A.1 — kandidati alfe", 2026-08-10).

Kontrast unatrag (2026-08-10):

| sloj | `foreground` | `muted-foreground` |
|---|:---:|:---:|
| čista `background` | 18,16 | 7,61 |
| + dot-grid 12 % | 15,20 | 6,37 |
| + glow 18 % (puna α) | 14,40 | 6,03 |
| **+ oboje, konzervativno (glow puna α)** | **11,31** | **4,74** |
| + oboje, najgora točka U KADRU (glow × 0,62) | 12,77 | 5,35 |

AA 4,50 drži u **obje** konvencije. Konvencija „glow pune alfe" naslijeđena je iz r2 i
konzervativna je: ta točka fizički nikad nije na zaslonu. 🔴 Dot-grid i dalje ima **nižu**
alfu od glowa namjerno: mreža pokriva **cijelu** plohu, pa se njezin doprinos zbraja preko
svakog piksela teksta, dok je glow lokalan. `-soft` plohe su neprozirne (alpha = 1,00) →
pozadina ispod njih se ne vidi i ne može ih razbiti.
