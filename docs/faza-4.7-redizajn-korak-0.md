# Faza 4.7 — REDIZAJN, KORAK 0: inventar palete (READ-ONLY)

**Datum:** 2026-08-10 · **Grana:** `faza-4-7-polish` · **Izmjena koda: NULA.**
Nijedan `.css`, `.ts`, `.tsx` ni `package.json` nije dirnut. Sve mjerenje kandidat-palete
radilo se nad **kopijom** `index.css` u scratchpadu; repo je bajt-identičan stanju na
commitu `7f7c9aa`.

**Ulazne odluke (ne re-odlučuju se):** dark-only · nova paleta mijenja samo KROMU ·
jedan display font preko fontsource · `monaco-theme.ts` bez ručnih literala.

---

## 🔴 SAŽETAK: što traži odluku prije stagea 1

| # | nalaz | težina |
|---|---|---|
| **R-1** | Uklanjanje `ThemeProvider`a **ne ruši** `sonner`, ali ruši `--radius` ako se briše cijeli `:root` blok (`--radius` je JEDINI token kojeg `.dark` ne redefinira) — v. §A.2, §A.5 | 🔴 zamka |
| **R-2** | Mockupov `--grad-primary` (violet `#A78BFA` h≈293,5 → cijan `#38D6F5` h≈214,5) sjedi **unutar obje zamrznute skale**: 6,5° od tier 300 i unutar mastery 190–260. **NE SMIJE UĆI.** Isto vrijedi za oba radial-glowa u pozadini mockupa | 🔴 granica |
| **R-3** | Predloženi `--ring` je najbliži `tier-easy` (ΔE_ok **0,067**). Pomicanje je iscrpljeno: pretraga cijelog (L,C) prostora @ hue 280 pokazuje da **nijedna** upotrebljiva vrijednost ne prelazi ΔE 0,11 — v. §C.4. Preporuka: prihvatiti uz kontekstualno obrazloženje | 🟡 odluka |
| **R-4** | `--destructive` (18 potrošača) je **izvan sRGB gamuta** i **nema nijedan redak u matrici** — zatečeno stanje, nije uzrokovano redizajnom | 🟡 zatečeno |
| **R-5** | `pairs.py` mjeri par `neutral × card` uz dokaz „○ ConceptChip", ali `ConceptChip` **ne koristi** `--neutral` (fallback je `text-muted-foreground`). Par je fantomski; `--neutral` ima **0 potrošača** | 🟡 ispravak |
| **R-6** | Brief tvrdi da `~5 min` „ne postoji u podacima". **Netočno:** `estimated_time_sec` je u API-ju i **već se renderira** ([TaskPage.tsx:279-281](frontend/src/pages/TaskPage.tsx#L279-L281)) — v. §E.2 | 🔴 ispravak premise |
| **R-7** | 2 od 9 snimki u `docs/figures/` su u light temi (`08`, `09`) → **nevažeće za rad** čim light nestane | 🔴 posljedica |

**Matrica prolazi.** Predložena paleta: **52 para + 12 čipova, 0 padova**, u prvoj
iteraciji. Druga iteracija dirala je samo `--ring` (radi R-3), ne zbog pada.

---

# A — INVENTAR ZA UKIDANJE LIGHT TEME

## A.1 Što light temu drži — potpun popis

| # | mjesto | što točno | opseg brisanja |
|---|---|---|---|
| 1 | [index.css:152-224](frontend/src/index.css#L152-L224) | `:root` blok, **63 tokena** | 73 retka |
| 2 | [index.css:226-297](frontend/src/index.css#L226-L297) | `.dark` blok, **62 tokena** | ostaje (postaje jedini) |
| 3 | [index.css:7](frontend/src/index.css#L7) | `@custom-variant dark (&:is(.dark *))` | v. §A.5 |
| 4 | [lib/theme/ThemeProvider.tsx](frontend/src/lib/theme/ThemeProvider.tsx) | cijela datoteka (36 redaka) | provider + `useEffect` koji toggla klasu |
| 5 | [lib/theme/context.ts](frontend/src/lib/theme/context.ts) | `ThemeContextValue { dark, toggle }` | 15 redaka |
| 6 | [hooks/useTheme.ts](frontend/src/hooks/useTheme.ts) | hook + throw guard | 12 redaka |
| 7 | [main.tsx:7,34,41](frontend/src/main.tsx#L34) | `<ThemeProvider>` wrapper | 3 retka |
| 8 | [AppShell.tsx:83,114-123](frontend/src/components/layout/AppShell.tsx#L114-L123) | toggle gumb + `Sun`/`Moon` importi (:12,:14) | ~12 redaka |
| 9 | [ThemeProvider.tsx:8](frontend/src/lib/theme/ThemeProvider.tsx#L8) | `localStorage` ključ `"sql_tutor_theme"` | 🔴 v. §A.4 |
| 10 | [lib/monaco-theme.ts:60-95](frontend/src/lib/monaco-theme.ts#L60-L95) | `sqlTutorLight` objekt (**36 redaka, 11 rules + 14 colors**) | + import i grana u [SqlEditor.tsx:16,35,85](frontend/src/components/task/SqlEditor.tsx#L85) |
| 11 | [TaskPage.tsx:35,121](frontend/src/pages/TaskPage.tsx#L121) | `const { dark } = useTheme()` → prop u `SqlEditor` | 2 retka |
| 12 | [ui/sonner.tsx:3,8,12](frontend/src/components/ui/sonner.tsx#L12) | `theme={dark ? "dark" : "light"}` | v. §A.2 |
| 13 | [scripts/a11y/palette.py](scripts/a11y/palette.py) | `load_tokens` vraća `{'light', 'dark'}`; `SELF_TEST` ima **3 light retka** | v. §A.6 |
| 14 | [scripts/a11y/monaco_check.py](scripts/a11y/monaco_check.py) | `MAP` ima **11 light redaka** | v. §A.6 |
| 15 | [index.html:7](frontend/index.html#L7) | `<meta name="theme-color" content="#0a0a0a">` | vrijednost prati novi `--background` |
| 16 | `docs/figures/08`, `09` | dvije light snimke | v. §A.7 |
| 17 | `package.json` — `next-themes@^0.4.6` | **mrtva dependency** | v. §A.3 |

**Ukupno za brisanje:** ~190 redaka u 8 datoteka + 1 dependency + 2 snimke.

## A.2 🔴 Ruši li uklanjanje `ThemeProvider`a `sonner`? — **NE**

**Nalaz: ne ruši, ali ne smije se samo obrisati wrapper.**

`sonner@2.0.7` **nema** `next-themes` ni u `dependencies` ni u `peerDependencies`
(provjereno u `node_modules/sonner/package.json` — peer je samo `react`/`react-dom`).
Ovisnost je isključivo o **našem** hooku:

```tsx
// components/ui/sonner.tsx:8,12
const { dark } = useTheme()
<Sonner theme={dark ? "dark" : "light"} … />
```

Ako se `ThemeProvider` ukloni bez ove izmjene, `useTheme()` **baca**
(`useTheme.ts:8` — `throw new Error("useTheme mora biti korišten unutar <ThemeProvider>")`),
i to iz komponente **izvan** `<ErrorBoundary>` ([main.tsx:39](frontend/src/main.tsx#L39)) →
bijeli ekran, ne degradirano stanje. Isto vrijedi za `AppShell.tsx:83` i `TaskPage.tsx:121`.

🔴 **Nije dovoljno „ukloniti provider" — sve tri pozivna mjesta moraju otići istim potezom.**
Za `sonner` je zamjena jednoredna i **bez** ikakve ovisnosti o mehanizmu tema:

```tsx
<Sonner theme="dark" … />   // aplikacija je dark-only
```

Ako se `theme` prop izostavi, sonnerov default je `"light"` → **svijetli toast usred tamne
aplikacije**. Prop mora ostati, s literalom.

**Preporuka: PUNO uklanjanje, ne zadržavanje mehanizma.** Brief nudi kompromis
(zadržati mehanizam, ukloniti light vrijednosti) kao „manji diff". Ovdje ne kupuje ništa:
mehanizam ima **3 potrošača** i svaki se rješava jednim retkom, a zadržan provider koji
uvijek vraća `dark: true` je mrtav kod koji izgleda kao živa značajka. Zadržavanje bi bilo
opravdano da `sonner` ovisi o `next-themes` — ne ovisi.

## A.3 `next-themes` je već mrtav

```
$ grep -rn "next-themes" frontend/src frontend/e2e
src/components/ui/sonner.tsx:1:// Adaptirano: shadcn stub pretpostavlja next-themes (Next.js) …
```
Jedini pogodak je **komentar**. Paket je u `dependencies` (`^0.4.6`) i nikad se ne importa —
ostatak shadcn stuba iz 4.1. Uklanja se istim potezom (ne mijenja bundle, tree-shaking ga
ionako izbacuje, ali `package.json` prestaje lagati o ovisnostima).

## A.4 🔴 `localStorage` ključ — zamka za zatečene korisnike

`sql_tutor_theme` je već zapisan u preglednicima svih koji su aplikaciju otvorili
(`ThemeProvider.tsx:22` piše ga pri **svakom** mountu, ne samo pri toggleu). Ako se čitanje
ukloni, ključ ostaje kao smeće — bezopasno, ali:

🔴 **Korisnik koji je eksplicitno odabrao light temu dobit će dark bez ikakve najave.**
To je namjeravan ishod odluke, ali treba biti svjesna, ne slučajna posljedica. Nema mehanizma
kojim bi se to objasnilo (nema onboarding poruke ni changeloga u aplikaciji).

Odluka: **ne** dodavati migracijski kod za brisanje ključa. Jedan mrtav string u
localStorageu nije vrijedan koda koji bi ga uklonio; alternativa (`localStorage.removeItem`
pri bootu) je kod koji nikad ne bi bio uklonjen.

## A.5 🔴 DVIJE zamke pri brisanju `:root` bloka

**Zamka 1 — `--radius`.** Mjereno skriptom nad `index.css`:

```
:root  = 63 tokena (retci 152–225)
.dark  = 62 tokena (retci 226–298)
SAMO u :root: ['--radius']      ← .dark ga NE redefinira, nasljeđuje ga
SAMO u .dark: []
```

`--radius: 0.625rem` postoji **isključivo** u `:root` ([index.css:177](frontend/src/index.css#L177)).
Iz njega se izvodi svih 7 radius stepenica (`--radius-sm` … `--radius-4xl`,
[index.css:95-101](frontend/src/index.css#L95-L101)) i koristi ga `sonner`
([sonner.tsx](frontend/src/components/ui/sonner.tsx) `"--border-radius": "var(--radius)"`).
Brisanje `:root` bloka u cijelosti → **svaki `rounded-*` u aplikaciji postaje `calc(NaN)`**.
Migracija mora `--radius` prenijeti u novi jedini blok.

**Zamka 2 — `@custom-variant dark`.** Ako se tokeni presele iz `.dark` u `:root`, a
`<html>` više ne dobiva klasu `dark`, tada `@custom-variant dark (&:is(.dark *))`
([index.css:7](frontend/src/index.css#L7)) **prestaje matchati** i svih 8 `dark:` prefiksa
iz §A.8 tiho gubi svoja pravila. Dvije čiste opcije:

- **(a)** tokeni ostaju u `.dark`, a `<html class="dark">` se hardkodira u
  [index.html](frontend/index.html) → `dark:` varijante nastavljaju raditi, diff je minimalan,
  a `@custom-variant` ostaje smislen;
- **(b)** tokeni idu u `:root`, `.dark` i `@custom-variant` nestaju, **i svih 8 `dark:`
  prefiksa mora se ručno razriješiti** (§A.8).

**Preporuka: (b).** Opcija (a) ostavlja aplikaciju koja se *pretvara* da ima dvije teme
(`.dark` klasa, `dark:` varijante) dok ih nema — točno ona vrsta tihe neistine koju je
4.7 inače uklanjao. (b) je 8 ručnih razrješenja, sva trivijalna (§A.8).

## A.6 Posljedica za a11y harness (`scripts/a11y/`)

| datoteka | što puca | zašto |
|---|---|---|
| `palette.py` — `load_tokens` | `css.index("\n:root {")` **baca `ValueError`** ako `:root` bloka nema | funkcija tvrdo traži redoslijed `:root` → `.dark` → `@layer base` i sama upozorava: „Struktura CSS-a se promijenila — provjeri parser prije nego vjeruješ brojkama" |
| `palette.py` — `SELF_TEST` | 3 od 6 redaka su light (`foreground × card`, `correct × correct-soft`) | ostaju bez teme |
| `palette.py` — `SELF_TEST` (dark) | sva 3 dark retka **padaju**: `foreground × card` 17,16 → **16,46**, `muted-foreground × card` 6,91 → **6,89**, `ring × card` 3,79 → **4,90** | promjena krome ih mijenja po definiciji |
| `contrast_matrix.py` | `--theme light`, dvotemna petlja, „obje teme" u markdownu | |
| `monaco_check.py` | 11 od 20 redaka u `MAP` je light; 2 od njih **već driftaju** (v. §A.9) | |

🔴 **Ovo je posljedica koja se ne smije izvesti tiho.** `SELF_TEST` je zaključan na
**objavljene** brojke iz dokumentacije projekta i namjerno prekida izvođenje kad ne
odgovaraju (poučak #39). Kad se paleta promijeni, njegove nove vrijednosti moraju se
**ručno provjeriti i objaviti u istom commitu** kao i sama paleta — inače harness postaje
pečat koji potvrđuje sam sebe.

## A.7 🔴 `docs/figures/` — 2 od 9 snimki su light

| datoteka | tema | status nakon redizajna |
|---|---|---|
| `01-dashboard-dark.png` … `07-fipa-agent-log-dark.png` | dark | 🟡 zastarjele (nova paleta), ali **važeće po temi** |
| **`08-fipa-agent-log-light.png`** | **light** | 🔴 **NEVAŽEĆA** — prikazuje temu koje neće biti |
| **`09-profil-bkt-krivulje-light.png`** | **light** | 🔴 **NEVAŽEĆA** — isto |

Prema `docs/figures/README.md`, `08` i `09` postoje **samo** da pokažu „isto, svijetla
tema" uz `07` odnosno `03`. Time gube i sadržaj i svrhu: nema drugog kadra koji bi
prikazivali. **Brišu se, ne presnimavaju.**

Preostalih 7 mora se presnimiti nakon primjene palete. Snimanje je opisano u
`figures/README.md` (chrome-headless-shell preko CDP-a) — **ali je od commita `7f7c9aa`
dostupan Playwright** (`@playwright/test@^1.62.1`, `frontend/e2e/`), pa je harness za
snimanje sada jeftiniji nego kad je README pisan. Vrijedi provjeriti prije nego se ponovi
stara scratchpad skripta. Dvije zamke iz READMEa (Monaco ignorira `textarea.value`; upit
mora u novi redak) vrijede i dalje — `e2e/smoke.spec.ts:33-40` ih je neovisno potvrdio.

## A.8 `dark:` prefiksi koji postaju mrtvi — svih 8

```
$ grep -rn "dark:" frontend/src --include=*.tsx --include=*.ts | wc -l   →  8
```
(2 od 8 pogodaka nisu Tailwind varijante nego identifikatori `dark: boolean` —
`lib/theme/context.ts:9` i `components/task/SqlEditor.tsx:24`. Stvarnih varijanti je **6**,
raspoređenih u **3 datoteke**.)

| datoteka:redak | pravilo | razrješenje |
|---|---|---|
| [ui/button.tsx:8](frontend/src/components/ui/button.tsx#L8) | `dark:aria-invalid:border-destructive/50` `dark:aria-invalid:ring-destructive/40` | zadrži dark granu, ukloni prefiks |
| [ui/button.tsx:14](frontend/src/components/ui/button.tsx#L14) (`outline`) | `dark:border-input dark:bg-input/30 dark:hover:bg-input/50` — **gazi** light `border-border bg-background hover:bg-muted` | 🔴 nije samo brisanje prefiksa: light vrijednosti u istom stringu treba **ukloniti**, inače ostaje mrtav CSS koji izgleda kao namjera |
| [ui/button.tsx:18](frontend/src/components/ui/button.tsx#L18) (`ghost`) | `dark:hover:bg-muted/50` gazi `hover:bg-muted` | isto |
| [ui/button.tsx:20](frontend/src/components/ui/button.tsx#L20) (`destructive`) | `dark:bg-destructive/20 dark:hover:bg-destructive/30 dark:focus-visible:ring-destructive/40` | isto |
| [ui/input.tsx:12](frontend/src/components/ui/input.tsx#L12) | `dark:bg-input/30 dark:disabled:bg-input/80 dark:aria-invalid:*` | isto |
| [ui/field.tsx:107](frontend/src/components/ui/field.tsx#L107) | `dark:has-data-checked:border-primary/20 dark:has-data-checked:bg-primary/10` | isto |

🔴 **Sve tri datoteke su `ui/` primitivi na eval-verificiranom putu.** `button` i `input`
su na Task screenu; v. §F.

## A.9 Usputni nalaz: `monaco_check.py` već prijavljuje 2 drifta — oba u lightu

```
$ python3 scripts/a11y/monaco_check.py
DRIFT [light] rules[comment]/editorLineNumber      tema #737373 ≠ --muted-foreground → #6B6B6B
DRIFT [light] editorLineNumber.activeForeground    tema #A06604 ≠ --accent-warm-text → #925800
```
Nastali su commitom `5994107` (4c korekcija light tokena) — `monaco-theme.ts` nije ažuriran
uz `index.css`. **Točno onaj kvar zbog kojeg skripta postoji.** Ukidanjem light teme oba
nestaju sama; ne treba ih posebno popravljati, ali treba ih zabilježiti kao **dokaz da
vrijednosna kopija drifta u praksi, ne samo u teoriji** — što je i razlog zahtjeva iz
briefa da `monaco-theme.ts` više ne smije nositi ručne literale.

🔴 Skripta usput prijavljuje i **jednu vrijednost bez izvora**: `#292929`
(`editorIndentGuide`, `widget.border`, `lineHighlight`, `scrollbar` u **dark** temi).
Komentar joj pripisuje `--border`, ali dark `--border` je `oklch(1 0 0 / 10%)` — bijela s
alfom. `#292929` nije nijedan token. **Pri redizajnu ta vrijednost nema iz čega se
preračunati** i mora se odlučiti ručno; prirodni kandidat je kompozit
`border` nad `card` (= `#27293a` u predloženoj paleti).

---

# B — INVENTAR KROME (dark blok)

Potrošači brojani regexom nad `frontend/src` (`.ts`/`.tsx`/`.css`, bez `index.css`):
Tailwind utility `<prefiks>-<token>` (uz negativni lookahead da `accent` ne hvata
`accent-warm`) **ili** `var(--token)`.

## B.1 KROMA — slobodna za promjenu

| token | dark vrijednost | potrošača | bilješka |
|---|---|---:|---|
| `--muted-foreground` | `oklch(0.708 0 0)` | **118** | daleko najkorišteniji token u aplikaciji |
| `--border` | `oklch(1 0 0 / 10%)` | **45** | + `@layer base` `*{@apply border-border}` |
| `--foreground` | `oklch(0.985 0 0)` | 28 | |
| `--muted` | `oklch(0.269 0 0)` | 35 | uz 4 alpha-varijante (`/30 /40 /50 /60`) |
| `--ring` | `oklch(0.556 0 0)` | 19 | 🔴 v. §C.4 |
| `--destructive` | `oklch(0.704 0.191 22.216)` | 18 | 🔴 v. §B.3 |
| `--primary` | `oklch(0.922 0 0)` | 8 | 🔴 v. §C.3 |
| `--input` | `oklch(1 0 0 / 15%)` | 7 | uz `/30`, `/50` |
| `--sidebar-accent` | `oklch(0.269 0 0)` | 5 | AppShell ×3, ConceptRow, MasteryHighlights |
| `--card` | `oklch(0.205 0 0)` | 4 | nizak broj vara: `ui/card.tsx` ga nosi za sve kartice |
| `--background` | `oklch(0.145 0 0)` | 4 | + `@layer base` `body{@apply bg-background}` |
| `--secondary` | `oklch(0.269 0 0)` | 3 | samo `ui/button.tsx` |
| `--sidebar-accent-foreground` | `oklch(0.985 0 0)` | 3 | samo AppShell |
| `--popover` | `oklch(0.205 0 0)` | 2 | sonner + ConceptCurveDetail |
| `--sidebar-border` | `oklch(1 0 0 / 10%)` | 2 | samo AppShell |
| `--secondary-foreground` | `oklch(0.985 0 0)` | 2 | |
| `--card-foreground` · `--popover-foreground` · `--primary-foreground` | | 1 svaki | |
| `--sidebar` | `oklch(0.205 0 0)` | 1 | AppShell |
| `--radius` | `0.625rem` (**samo `:root`**) | 2 | 🔴 §A.5 |

### 🔴 Tokeni s NULA potrošača (KROMA)

| token | dark vrijednost | preporuka |
|---|---|---|
| `--accent` | `oklch(0.269 0 0)` | zadrži (shadcn ugovor — `ui/*` ga može zatražiti) |
| `--accent-foreground` | `oklch(0.985 0 0)` | zadrži, isti razlog |
| `--sidebar-foreground` | `oklch(0.985 0 0)` | zadrži (sidebar ga nasljeđuje od `body`) |
| **`--sidebar-primary`** | `oklch(0.488 0.243 264.376)` | 🔴 **BRISATI** — v. §B.2 |
| **`--sidebar-primary-foreground`** | `oklch(0.985 0 0)` | 🔴 **BRISATI** uz gornji |
| `--sidebar-ring` | `oklch(0.556 0 0)` | zadrži, prati `--ring` (4c ih je već uskladio) |

## B.2 🔴 `--sidebar-primary` je jedini KROMA token koji ulazi u semantički prostor

`oklch(0.488 0.243 264.376)` — **chroma 0,243**, najviša u cijelom dark bloku (sljedeća je
`--incorrect` 0,19). Hue 264,4° je **4,4° od gornjeg ruba mastery skale (260)**, a chroma
je 4,9× viša od `mastery-0`.

Zatečen je iz shadcn seeda, **nikad korišten** (0 potrošača, oba retka), i jedini je token
u KROMI koji bi — da ga netko upotrijebi — čitao kao mastery signal. Redizajn je prilika da
nestane, a ne da dobije novu vrijednost.

## B.3 🔴 `--destructive` — dvije stvari odjednom, obje zatečene

**(1) Izvan sRGB gamuta.** Provjereno konverzijom u linearni sRGB:

```
--destructive: oklch(0.704 0.191 22.216) → lin (1.0127, 0.1268, 0.1356)   R > 1
```
`palette.py` (`_lin_to_srgb`) **tiho klampa** na 1,0. Svako mjerenje koje uključuje
`--destructive` mjeri **klampanu**, ne deklariranu boju. To nije uzrokovano redizajnom —
vrijednost je shadcn default — ali jest tiha netočnost u alatu na kojem 4.7 gradi tvrdnje.

**(2) 18 potrošača, 0 redaka u matrici.** `--destructive` se ne pojavljuje ni u `SURFACES`
ni u `PAIRS` (`scripts/a11y/pairs.py`). Najveći nepokriveni token u aplikaciji.

**(3) Granični slučaj opsega.** Brief ga ne navodi ni u KROMI ni u SEMANTICI. Hue 22,2° je
**2,8° od `--incorrect` (25)** — funkcionalno je duplikat skale greške.
**Preporuka: tretirati kao ZAMRZNUT** (ne dirati u redizajnu) i otvoriti zasebno pitanje
„zašto postoje dva crvena tokena" — to je konsolidacija, ne prebojavanje.

## B.4 SEMANTIKA — zamrznuto, mjereno samo radi potpunosti

Sve vrijednosti ostaju **bajt-identične**. Brojevi potrošača:

| skupina | potrošača | bilješka |
|---|---|---|
| `accent-warm` (22) · `accent-warm-text` (18) · `accent-warm-foreground` (3) | 43 | najkorišteniji semantički trio |
| `incorrect` (18) · `incorrect-soft` (7) | 25 | |
| `correct` (12) · `correct-soft` (4) | 16 | |
| `partial` (5) · `partial-soft` (2) | 7 | aktivan od 4.3c |
| `mastery-0..100` | 7 ukupno | 5 od 7 kroz `lib/mastery.ts` |
| `tier-*` ×6 | 6 | svi kroz `ConceptChip.tsx` |
| `difficulty-*` ×10 | 10 | svi kroz `DifficultyChip.tsx` |
| `chart-1` (4) · `chart-2` (2) | 6 | |

### 🔴 Semantički tokeni s NULA potrošača

| token | vrijednost (dark) | nalaz |
|---|---|---|
| **`--neutral`** | `oklch(0.72 0.02 260)` | **0 potrošača** — v. §B.5 |
| `--chart-3` | `oklch(0.72 0.13 300)` | 0 u komponentama; **jest** izvor za monaco `rules[predefined]` (`#B191EA`) |
| `--chart-4` | `oklch(0.74 0.13 345)` | 0 potrošača |
| `--chart-5` | `oklch(0.8 0.14 80)` | 0 potrošača |

`chart-3/4/5` ostaju: kategorijska skala od 5 mora imati svih 5 članova da bi bila skala
(isti argument kojim `--duration-reward` ostaje u ljestvici trajanja, [index.css:145-149](frontend/src/index.css#L145-L149)).

## B.5 🔴 R-5: `pairs.py` mjeri par koji ne postoji

```python
# scripts/a11y/pairs.py, PAIRS["card"]
"neutral": "○ ConceptChip",
```

`ConceptChip.tsx` **ne referencira** `--neutral`. Njegov fallback za nepoznat tier je:

```tsx
// components/ConceptChip.tsx:32-33
// Nepoznat tier (buduća migracija) → neutralan chip, ne kriva skala.
TIER_CLASS[tier] ?? "bg-muted text-muted-foreground",
```

Riječ „neutralan" u komentaru odnosi se na **namjeru**, ne na token. `grep -rn "neutral"
frontend/src` daje 12 pogodaka i **nijedan** nije Tailwind klasa `text-neutral`/`bg-neutral`
— sve su ili `index.css` deklaracije, ili hrvatska riječ u komentarima, ili komentar u
`monaco-theme.ts`.

**Posljedica:** matrica sadrži jedan redak (`neutral × card`, 7,22:1) koji mjeri par koji se
nikad ne renderira. Ne mijenja nijedan zaključak (par prolazi), ali krši vlastito pravilo
`pairs.py`-ja: *„Bez citata se par NE dodaje — tvrdnja bez dokaza je ista klasa kao tvrdnja
bez plohe."* Citat postoji, ali je **netočan**.

Jedini stvarni potrošač `--neutral`a je `monaco-theme.ts` `rules[operator]` (`#9DA5B1`) —
a to je vrijednosna kopija, ne CSS potrošač. Redak u `PAIRS` treba ili obrisati, ili
zamijeniti stvarnim dokazom iz monaca.

---

# C — CILJNA PALETA

## C.0 Metoda i dokaz da je konvertor ispravan

Prije ijednog mjerenja kandidata, `contrast_matrix.py` pokrenut je nad **nedirnutim**
`index.css`:

```
foreground × card       [light] 19,79  (očekivano 19,79)   ✅
foreground × card       [dark ] 17,16  (očekivano 17,16)   ✅
muted-foreground × card [dark ]  6,91  (očekivano  6,91)   ✅
ring × card             [dark ]  3,79  (očekivano  3,79)   ✅
correct × correct-soft  [light]  4,67  (očekivano  4,67)   ✅
partial × partial-soft  [dark ]  8,03  (očekivano  8,03)   ✅
✅ Svi mjereni parovi prolaze.
```

Kandidat se potom mjeri **istim** `build()`/`chip_rows()`/`surround_rows()` funkcijama, nad
kopijom CSS-a u scratchpadu. `SELF_TEST` se pritom **namjerno preskače** — zaključan je na
zatečene brojke koje kandidat po definiciji mijenja, pa bi njegov pad bio očekivan i
besmislen. Ispravnost konvertora dokazana je gore, na nedirnutom ulazu.

## C.1 Mockup: hex → oklch (izvedeno, ne prepisano)

| mockup | hex | **izvedeni oklch** |
|---|---|---|
| `--bg` | `#0B0E1A` | `oklch(0.167 0.026 272.6)` |
| `--bg-soft` | `#0F1326` | `oklch(0.194 0.039 273.3)` |
| `--surface` | `#141936` | `oklch(0.226 0.056 273.7)` |
| `--text` | `#E7EAFB` | `oklch(0.940 0.023 278.0)` |
| `--text-dim` | `#9AA1C7` | `oklch(0.717 0.056 276.7)` |
| `--text-mute` | `#626A93` | `oklch(0.534 0.065 275.5)` |
| `--line` (rgba nad surface) | `#232A4E` | `oklch(0.298 0.066 273.5)` |

**🔴 Tvrdnja iz briefa provjerena i POTVRĐENA na decimalu:**
`--text-mute #626A93` na `--surface #141936` = **3,28:1** — ispod AA (4,50).
Za usporedbu, `--text-dim` na istoj plohi = 6,79:1 (prolazi).
Mockup dakle **ima** upotrebljiv sekundarni ton; greška je što uvodi i **treći**, tercijarni,
koji AA ne izdrži. Predložena paleta ne uvodi treću razinu teksta — v. §C.3.

## C.2 Izbor huea — izveden, ne odabran

> ### ⟳ REVIZIJA 2026-08-10 (stage 1, t.0a) — tvrdnja „izveden, ne odabran" je PRESNAŽNA
>
> Izvod ispod koristi **kutnu udaljenost od skala**. Ta je metrika u N-12 opovrgnuta za
> `--ring` i premjerena nad **sukorištenim** parovima. Ponovljena za hue:
>
> - **Globalno najgori sukorišteni ΔE je 0,1020 i NE OVISI O HUEU** — vezujući par je
>   `ring × mastery-50`, a prsten je akromatski (N-12).
> - Ograničeno na tokene koji **nose** hue, cijela krivulja 0°–360° varira **0,1192
>   (h 60) … 0,1587 (h 240)**. hue 280 daje **0,1525**, maksimum je 0,0062 iznad.
> - **Nijedan hue na krugu ne proizvodi koliziju** (sve ≫ prag 0,05).
>
> **Zaključak: ispravljena metrika hue NE RAZLIKUJE.** hue 280 stoga **nije izveden iz
> nje** — nije ni opovrgnut njome. Ono što ga i dalje bira je pravilo iz MASTER §2.7:
> generički UI ne smije **preuzeti hue-pojas** semantičke skale. Maksimum krivulje
> (h 240) leži **unutar mastery pojasa 190–260** i bio bi upravo takvo preuzimanje.
> To je argument o **identitetu i naučivosti skale**, ne o razlučivosti pojedinog para —
> druga vrsta ograničenja, i jedina koja ovdje odlučuje. Hue se **ne mijenja**.
>
> Ostale vrijednosti §C.3 provjerene istom mjerom: nijedna osim `--ring` nije bila birana
> radi sudara koji se ne renderira. **R-2 dobiva brojku umjesto samo hue-argumenta:**
> mockupov `#A78BFA` kao `--primary` = ΔE **0,0345** prema `tier-medium` (sukorišteni —
> Submit gumb i `ConceptChip` su na istom ekranu, `TaskPage.tsx:277` + `:340`) → 🔴
> kolizija potvrđena mjerenjem. Predloženi `oklch(0.922 0.020 280)` = **0,1525** ✅.

Semantička hue karta (§2.7): `25` incorrect · `55–60` partial · `70–85` accent-warm ·
`150` correct · `190–260` mastery · `300` tier · `345` difficulty.

**Sve praznine u karti, mjerene:**

| praznina | širina | središte | poluširina (= max. moguća udaljenost) |
|---|---:|---:|---:|
| 85° → 150° | 65° | 117,5° | 32,5° |
| 300° → 345° | 45° | 322,5° | 22,5° |
| **260° → 300°** | **40°** | **280,0°** | **20,0°** |
| 150° → 190° | 40° | 170,0° | 20,0° |
| 345° → 25° | 40° | 5,0° | 20,0° |
| 25° → 55° | 30° | 40,0° | 15,0° |
| 60° → 70° | 10° | 65,0° | 5,0° |

Najšira praznina (117,5°) je žuto-zelena, druga (322,5°) je magenta **između tier i
difficulty** — ni jedna ni druga nisu „ink" ploha, a druga bi ploha smjestila točno između
dvije zamrznute skale. Prva upotrebljiva je **280°**, i ondje je udaljenost od obiju
susjednih skala **točno jednaka**:

```
  hue |  mastery |  tier |  min
  270 |       10 |    30 |   10
  275 |       15 |    25 |   15
  280 |       20 |    20 |   20   ⬅ maksimum
  285 |       25 |    15 |   15
  290 |       30 |    10 |   10
```

**Odabir: hue 280°.** Nije preuzet iz mockupa (273,6°) nego izveden — mockupova vrijednost
je 6,4° bliža mastery skali bez ikakve dobiti.

## C.3 Predložena paleta

**Načelo:** `L` svakog sloja ostaje **bajt-identičan zatečenom** (izmjereno: `background`
0,145 → `card` 0,205 → `muted` 0,269; Δ = **+0,060** i **+0,064**). Mijenja se samo
`C` i `h`. Chroma raste sa slojem — isti obrazac koji mockup koristi (0,026 → 0,039 → 0,056),
skaliran na našu, širu ljestvicu svjetlina.

```css
.dark {
  /* ── ploha: ink-indigo, hue 280, L ljestvica NEPROMIJENJENA ── */
  --background:                 oklch(0.145 0.020 280);   /* bilo: 0.145 0 0    */
  --card:                       oklch(0.205 0.030 280);   /* bilo: 0.205 0 0    */
  --popover:                    oklch(0.205 0.030 280);
  --sidebar:                    oklch(0.205 0.030 280);
  --muted:                      oklch(0.269 0.038 280);   /* bilo: 0.269 0 0    */
  --secondary:                  oklch(0.269 0.038 280);
  --accent:                     oklch(0.269 0.038 280);
  --sidebar-accent:             oklch(0.269 0.038 280);

  /* ── tekst ── */
  --foreground:                 oklch(0.970 0.013 280);   /* bilo: 0.985 0 0    */
  --card-foreground:            oklch(0.970 0.013 280);
  --popover-foreground:         oklch(0.970 0.013 280);
  --secondary-foreground:       oklch(0.970 0.013 280);
  --accent-foreground:          oklch(0.970 0.013 280);
  --sidebar-foreground:         oklch(0.970 0.013 280);
  --sidebar-accent-foreground:  oklch(0.970 0.013 280);
  --muted-foreground:           oklch(0.708 0.035 280);   /* L NEPROMIJENJEN    */

  /* ── obrisi (alpha se zadržava — border mora raditi nad svakom plohom) ── */
  --border:                     oklch(0.780 0.050 280 / 12%);  /* bilo: 1 0 0 / 10% */
  --sidebar-border:             oklch(0.780 0.050 280 / 12%);
  --input:                      oklch(0.780 0.050 280 / 17%);  /* bilo: 1 0 0 / 15% */

  /* ── fokus ── */
  --ring:                       oklch(0.620 0.040 280);   /* bilo: 0.556 0 0    */
  --sidebar-ring:               oklch(0.620 0.040 280);

  /* ── primary: ostaje visokokontrastan neutral, samo tintan ── */
  --primary:                    oklch(0.922 0.020 280);
  --primary-foreground:         oklch(0.205 0.030 280);

  /* --sidebar-primary, --sidebar-primary-foreground: BRISATI (§B.2) */
  /* --destructive: NE DIRATI (§B.3) */
  /* --radius: PRENIJETI iz :root (§A.5) */
}
```

**Gamut:** svih 22 predloženih vrijednosti provjereno konverzijom u linearni sRGB —
**nijedna nije izvan [0,1]**, dakle nijedna ne trpi tiho klampanje. (Jedina vrijednost izvan
gamuta u cijelom dark bloku je zatečeni `--destructive`, §B.3.)

### 🔴 R-2: što iz mockupa NE ulazi u paletu

| mockup | hex | izvedeni hue | sudar |
|---|---|---|---|
| `--grad-primary` start | `#A78BFA` | **293,5°** | **6,5° od tier 300** — gumb bi čitao kao tier čip |
| `--grad-primary` kraj | `#38D6F5` | **214,5°** | **unutar mastery 190–260** — gumb bi čitao kao mastery gradijent |
| pozadinski glow (gore desno) | `rgba(167,139,250,.09)` | 293,5° | isto kao gore |
| pozadinski glow (dolje lijevo) | `rgba(56,214,245,.07)` | 214,5° | isto |
| `--kw` (syntax) | `#A78BFA` | 293,5° | naš `--chart-3` je 300 — **namjerno**, syntax je van UI skala |

Mockupov identitet **jest** taj gradijent, i on je **jedina stvar iz mockupa koju granica
zabranjuje**. Sve ostalo (ink podloga, slojevi, tipografija, raspored) prolazi.

**Zamjena za gradijent u stageu koji ga bude trebao:** `--primary` ostaje
visokokontrastan gotovo-bijeli neutral s indigo tintom. Ako se traži „poseban" primarni
gumb, jedina slobodna visoka-chroma zona je **280°** sama — ali tada se `--primary` i
`--ring` počinju stapati. Preporuka: **ne uvoditi kromatski primary.** Hijerarhiju gumba
nositi svjetlinom (bijeli fill vs obris), kako je i sad.

## C.4 🔴 R-3: `--ring` — jedina vrijednost koja se opirala

Mjera: ΔE u Oklabu (euklidski) od **renderirane** boje do **najbližeg** semantičkog
tokena. Alpha tokeni se kompozitiraju nad `card` — čist token s alfom nikad nije prikazan sam.

| KROMA token | renderirano | najbliži semantički | ΔE_ok | ocjena |
|---|---|---|---:|---|
| `background` | `#080912` | `mastery-0` `#3d4e69` | 0,277 | ✅ |
| `card` / `sidebar` / `popover` | `#141625` | `mastery-0` | 0,216 | ✅ |
| `muted` / `secondary` / `accent` / `sidebar-accent` | `#222439` | `mastery-0` | 0,152 | ✅ |
| `border` (nad card) | `#27293a` | `mastery-0` | 0,136 | ✅ |
| `input` (nad card) | `#2f3143` | `mastery-0` | 0,104 | ✅ |
| `primary` | `#e2e4f3` | `mastery-100` `#60eae2` | 0,137 | ✅ |
| `foreground` | `#f3f4fe` | `mastery-100` | 0,163 | ✅ |
| **`ring`** | `#81849e` | **`tier-easy`** `#8972b3` | **0,067** | 🟡 |
| **`muted-foreground`** | `#9c9fb7` | **`neutral`** `#9da5b1` | **0,021** | 🟡 v. niže |

**Sve plohe su razlučive s velikom rezervom.** Dva ostatka:

### `muted-foreground` × `neutral` — kolizija s mrtvim tokenom

ΔE 0,021. **Ali zatečeno stanje ima ΔE 0,023** (`#a1a1a1` vs `#9da5b1`) — dakle problem je
predredizajnski i redizajn ga ne pogoršava. Uz to `--neutral` ima **0 potrošača** (§B.5):
kolizija je s bojom koja se nikad ne renderira. **Nije blokada.** Jest još jedan argument
da `--neutral` treba nestati, ali on je u zamrznutom skupu → **prijavljuje se, ne dira se.**

### `ring` × `tier-easy` — pomicanje je iscrpljeno

Pretražen je cijeli `(L, C)` prostor @ hue 280 uz tvrdi uvjet ≥ 3,00:1 prema `card`,
`background` **i** `muted/40` (SC 1.4.11; `muted/40` jer `ConceptCurveCard` koristi `ring`
kao indikator stanja, ERRATA #48):

```
     ΔE |     L     C | najbliži semantički       | ×card | ×muted/40
  0.109 |  0.85  0.00 | difficulty-expert         | 11,37 | 10,70   ← globalni maksimum
  0.107 |  0.84  0.00 | difficulty-expert         | 11,00 | 10,35
  0.102 |  0.82  0.00 | neutral                   | 10,29 |  9,69
```

**Globalni maksimum je ΔE 0,109, i to na L 0,85 C 0,00** — dakle skoro bijelom, akromatskom
prstenu koji bi bio nerazlučiv od `--foreground` (`#f3f4fe`). U upotrebljivom pojasu
(L 0,55–0,75) izmjereno:

| kandidat | hex | ΔE | najbliži | × card | × muted/40 |
|---|---|---:|---|---:|---:|
| **zatečeno** `oklch(0.556 0 0)` | `#737373` | 0,084 | `mastery-25` | 3,80 | 3,56 |
| v1 `oklch(0.60 0.07 280)` | `#787caa` | 0,042 | `tier-easy` | 4,49 | 4,23 |
| **v2 `oklch(0.62 0.04 280)`** ⬅ | `#81849e` | **0,067** | `tier-easy` | **4,90** | **4,61** |
| v3 `oklch(0.66 0.025 280)` | `#8f91a2` | 0,036 | `difficulty-cross-module` | 5,76 | 5,42 |
| v4 `oklch(0.70 0.045 280)` | `#989cbb` | 0,034 | `neutral` | 6,68 | 6,29 |

🔴 **Nalaz koji vrijedi zapisati: semantička karta je gusta i „bijeg prema svjetlijem" ne
radi.** Čim se prsten posvijetli, najbliži susjed prestaje biti `tier-easy` i postaje
`difficulty-cross-module` (`oklch(0.68 0.03 345)` — namjerno **desaturiran** token) ili
`neutral`. Svaki akromatski srednje-svijetli sivi u ovoj paleti je nečiji susjed.

**Preporuka: v2, `oklch(0.62 0.04 280)`.** Obrazloženje:

1. **Najveći ΔE među opcijama čiji je najbliži susjed *stvarno renderiran i kromatski* token.**
   v3 i v4 imaju formalno manji ΔE prema `difficulty-cross-module`/`neutral`, ali prvi je
   namjerno bezbojan (svaki sivi mu je blizu), a drugi ima 0 potrošača.
2. **Kontrast raste na svim mjerenim plohama:** ×card 3,80 → **4,90**, ×background 4,19 →
   **5,41**, ERRATA #48 (`ring` vs `muted/40`) 3,56 → **4,61**.
3. **Oblik razdvaja ono što boja ne razdvaja.** `tier-easy` se renderira isključivo kao
   **ispunjen čip s tamnim tekstom** ([ConceptChip.tsx:16](frontend/src/components/ConceptChip.tsx#L16)
   `bg-tier-easy text-tier-easy-foreground`). `--ring` se renderira isključivo kao **2px
   obris s 2px odmakom**. Ne dijele nijedan oblik — isti argument kojim je 4c zadržao
   `0.556` unatoč tome što je bajt-identičan light `muted-foreground`u
   (commit `5994107`, t.3b: *„razlikuje ih GEOMETRIJA, ne boja"*).

🔴 **Uvjet:** v2 nosi istu obavezu kao 4c — **vizualnu provjeru po snimkama u stageu koji
ga izvodi**, s fokusom stvarno postavljenim, na 5 mjesta iz izlaznog kriterija 1C
(`docs/faza-4.7-errata-prijedlog.md`, §4). Brojka mjeri element; snimka mjeri hijerarhiju.

## C.5 PUNA MATRICA — dark, predložena paleta vs zatečeno

Generirano istim funkcijama kao `contrast_matrix.py`. **Pragovi:** tekst **4,50:1** ·
grafika i stanja **3,00:1** (SC 1.4.11). **●** ploha i tekst u istom `className` ·
**○** tekst u podstablu elementa koji nosi plohu.

| ploha | gdje se koristi | tekst token | dokaz | zatečeno | **predloženo** | |
|---|---|---|---|---|---|---|
| `background` | ploha stranice | `foreground` | ○ AppShell | 18,96 | **18,14** | ✅ |
| `background` | ploha stranice | `muted-foreground` | ○ AppShell | 7,63 | **7,60** | ✅ |
| `card` | kartice, paneli | `foreground` | ○ svi ekrani | 17,16 | **16,46** | ✅ |
| `card` | kartice, paneli | `muted-foreground` | ○ svi ekrani | 6,91 | **6,89** | ✅ |
| `card` | kartice, paneli | `accent-warm-text` | ○ ProgressHero, AttemptRow.tsx:67 | 9,44 | **9,48** | ✅ |
| `card` | kartice, paneli | `correct` | ○ ConceptRow | 8,54 | **8,56** | ✅ |
| `card` | kartice, paneli | `incorrect` | ○ AttemptRow | 6,16 | **6,18** | ✅ |
| `card` | kartice, paneli | `partial` | ○ StatsSummary.tsx:69 | 8,68 | **8,71** | ✅ |
| `card` | kartice, paneli | `neutral` | ○ ConceptChip 🔴 §B.5 | 7,22 | **7,25** | ✅ |
| `popover` | popover / tooltip | `foreground` | ○ ui/popover | 17,16 | **16,46** | ✅ |
| `popover` | popover / tooltip | `muted-foreground` | ○ ui/popover | 6,91 | **6,89** | ✅ |
| `sidebar` | lijeva navigacija | `muted-foreground` | ● AppShell.tsx:71 | 6,91 | **6,89** | ✅ |
| `sidebar` | lijeva navigacija | `accent-warm-text` | ○ AppShell | 9,44 | **9,48** | ✅ |
| `secondary` | secondary gumb | `foreground` | ○ ui/button variant=secondary | 14,48 | **13,92** | ✅ |
| `muted` | čipovi, prazna stanja | `muted-foreground` | ● BadgeGallery.tsx:73,97 | 5,83 | **5,83** | ✅ |
| `muted` | čipovi, prazna stanja | `foreground` | ○ EmptyState | 14,48 | **13,92** | ✅ |
| `muted` | čipovi, prazna stanja | `accent-warm-text` | ○ BadgeGallery | 7,97 | **8,02** | ✅ |
| `muted/30` | BadgeGallery — neosvojen bedž | `muted-foreground` | ○ BadgeGallery.tsx:62 | 6,60 | **6,59** | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `muted-foreground` | ○ ConceptCurveCard, RegisterPage | 6,49 | **6,49** | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `foreground` | ○ RegisterPage info blok | 16,13 | **15,49** | ✅ |
| `muted/40` | info blok /register, odabrana krivulja | `accent-warm-text` | ○ ConceptCurveCard | 8,88 | **8,92** | ✅ |
| `muted/50` | hover stanja | `muted-foreground` | ○ ConceptCurveCard hover | 6,39 | **6,38** | ✅ |
| `muted/50` | hover stanja | `foreground` | ○ hover | 15,86 | **15,23** | ✅ |
| `muted/60` | mono blok u povijesti pokušaja | `muted-foreground` | ○ AttemptRow.tsx:117 | 6,28 | **6,27** | ✅ |
| `background/60` | mono blok detalja greške | `muted-foreground` | ● FeedbackPanel.tsx:163, AttemptRow.tsx:138 | 7,38 | **7,35** | ✅ |
| `card/50` | stale-dim rezultata | `muted-foreground` | ○ RunResultPanel stale-dim | 6,91 | **6,89** | ✅ |
| `sidebar-accent/40` | ConceptRow hover | `muted-foreground` | ○ ConceptRow.tsx:117 | 6,49 | **6,49** | ✅ |
| `sidebar-accent/40` | ConceptRow hover | `correct` | ○ ConceptRow | 8,03 | **8,06** | ✅ |
| `sidebar-accent/60` | nav hover | `muted-foreground` | ○ AppShell.tsx:71 hover | 6,28 | **6,27** | ✅ |
| `input/30` | input (dark varijanta) | `foreground` | ○ ui/input | 15,33 | **15,12** | ✅ |
| `input/30` | input (dark varijanta) | `muted-foreground` | ○ placeholder | 6,17 | **6,33** | ✅ |
| `input/50` | disabled input | `muted-foreground` | ○ disabled input | 5,65 | **5,93** | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `correct` | ● FeedbackPanel.tsx:52-53, ContinueCard.tsx:129, TaskPage.tsx:288 | 7,74 | **7,74** | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `foreground` | ○ FeedbackPanel.tsx:123 | 15,57 | **14,88** | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `muted-foreground` | ○ FeedbackPanel.tsx:138,143,156,177,198 | 6,27 | **6,23** | ✅ |
| `correct-soft` | FeedbackPanel, čip „Riješeno” | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,57 | **8,57** | ✅ |
| `incorrect-soft` | FeedbackPanel, ErrorState, Run greška, Login/Register | `incorrect` | ● FeedbackPanel.tsx:64-65, LoginPage.tsx:105, RegisterPage.tsx:205 | 5,72 | **5,72** | ✅ |
| `incorrect-soft` | (isto) | `foreground` | ○ FeedbackPanel.tsx:123, ErrorState.tsx:35, RunResultPanel.tsx:114 | 15,93 | **15,22** | ✅ |
| `incorrect-soft` | (isto) | `muted-foreground` | ○ ErrorState.tsx:36, RunResultPanel.tsx:130, FeedbackPanel ×5 | 6,41 | **6,38** | ✅ |
| `incorrect-soft` | (isto) | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,77 | **8,77** | ✅ |
| `partial-soft` | FeedbackPanel | `partial` | ● FeedbackPanel.tsx:58-59 | 8,03 | **8,03** | ✅ |
| `partial-soft` | FeedbackPanel | `foreground` | ○ FeedbackPanel.tsx:123 | 15,87 | **15,17** | ✅ |
| `partial-soft` | FeedbackPanel | `muted-foreground` | ○ FeedbackPanel ×5 | 6,39 | **6,36** | ✅ |
| `partial-soft` | FeedbackPanel | `accent-warm-text` | ○ FeedbackPanel.tsx:147,169 | 8,74 | **8,74** | ✅ |
| `accent-warm/5` | ConceptRow deep-link flash | `muted-foreground` | ○ ConceptRow.tsx:110 | 6,35 | **6,36** | ✅ |
| `accent-warm/5` | ConceptRow deep-link flash | `correct` | ○ ConceptRow | 7,85 | **7,90** | ✅ |
| `accent-warm/10` | BadgeStrip, ContinueCard, ljestvica „ja” | `accent-warm-text` | ● BadgeStrip.tsx:47+51, ContinueCard.tsx:86 | 7,86 | **7,94** | ✅ |
| `accent-warm/10` | (isto) | `muted-foreground` | ○ LeaderboardTable.tsx:64 | 5,75 | **5,78** | ✅ |
| `accent-warm/20` | BadgeGallery — osvojen bedž | `accent-warm-text` | ● BadgeGallery.tsx:72, :96 | 6,22 | **6,31** | ✅ |
| `incorrect/10` | ErrorState — krug ikone | `incorrect` | ● ErrorState.tsx:32, guards.tsx:69 | 5,43 | **5,47** | ✅ |

### Čipovi (vlastiti `-foreground` na vlastitom fillu)

| tekst | ploha | zatečeno | **predloženo** | |
|---|---|---|---|---|
| `accent-warm-foreground` | `accent-warm` | 9,15 | **9,15** | ✅ |
| `primary-foreground` | `primary` | 14,22 | **14,24** | ✅ |
| `secondary-foreground` | `secondary` | 14,48 | **13,92** | ✅ |
| `sidebar-accent-foreground` | `sidebar-accent` | 14,48 | **13,92** | ✅ |
| `tier-easy-foreground` | `tier-easy` | 4,83 | **4,83** | ✅ |
| `tier-medium-foreground` | `tier-medium` | 7,08 | **7,08** | ✅ |
| `tier-hard-foreground` | `tier-hard` | 10,25 | **10,25** | ✅ |
| `difficulty-beginner-foreground` | `difficulty-beginner` | 5,01 | **5,01** | ✅ |
| `difficulty-intermediate-foreground` | `difficulty-intermediate` | 6,02 | **6,02** | ✅ |
| `difficulty-advanced-foreground` | `difficulty-advanced` | 8,07 | **8,07** | ✅ |
| `difficulty-expert-foreground` | `difficulty-expert` | 10,83 | **10,83** | ✅ |
| `difficulty-cross-module-foreground` | `difficulty-cross-module` | 6,77 | **6,77** | ✅ |

### Ploha vs okolina (prag 3,00 — SC 1.4.11)

| ploha | okolina | zatečeno | **predloženo** | |
|---|---|---|---|---|
| `accent-warm/5` | `card` | 1,09 | **1,08** | ⚠️ |
| `accent-warm/10` | `card` | 1,20 | **1,19** | ⚠️ |
| `accent-warm/20` | `card` | 1,50 | **1,50** | ⚠️ |
| `muted/40` | `card` | 1,06 | **1,06** | ⚠️ |

Sva četiri ⚠️ su **zatečena i nepromijenjena** (ERRATA #51): tint je ukras, stanje nose
ikona + tekst + `aria-current`. Redizajn ih ne pogoršava (najveća promjena je −0,01).

### Dodatne provjere izvan `PAIRS`

| provjera | zatečeno | **predloženo** | |
|---|---|---|---|
| `ring` × `card` | 3,79 | **4,90** | ✅ ⬆ |
| `ring` × `background` | 4,18 | **5,41** | ✅ ⬆ |
| `ring` × `muted` | 3,19 | **4,15** | ✅ ⬆ |
| ERRATA #48 — `ring` vs `muted/40` @ card | 3,56 | **4,61** | ✅ ⬆ |
| ljestvica `background` → `card` | 1,10 | **1,10** | odnos očuvan |
| ljestvica `card` → `muted` | 1,19 | **1,18** | odnos očuvan |
| `border` nad `card` (vs card) | 1,32 | **1,25** | 🟡 obrisi malo mekši |
| `input` nad `card` (vs card) | 1,57 | **1,40** | 🟡 isto |

## C.6 Rezultat matrice

> **52 mjerena para + 12 čipova = 64 provjere · 0 PADOVA.**
> Prošlo iz **prve** iteracije. Druga iteracija (v1 → v2) dirala je samo `--ring`, i to
> radi ΔE prema `tier-easy`, ne radi pada kontrasta.

**Jedina regresija:** `border`/`input` obrisi gube ~5 % kontrasta prema plohi (1,32 → 1,25).
Uzrok: zatečena čista bijela s alfom (`oklch(1 0 0 / 10%)`) je najsvjetlija moguća, a
tintani `oklch(0.78 …)` nije. Kompenzirano podizanjem alfe `input`a 15 % → 17 %. Ako se u
stageu pokaže da su obrisi premekani, prostor postoji: alfa se smije dizati do 15 %/20 %
bez ikakvog utjecaja na tekstualne parove (obrisi nisu tekst i mjere se prema
SC 1.4.11, gdje ionako nijedan zatečeni obris ne prelazi 3:1 — ni sad ni prije).

---

# D — DISPLAY FONT

## D.1 Bricolage Grotesque JEST na fontsourceu

| paket | verzija | unpacked | osi |
|---|---|---|---|
| **`@fontsource-variable/bricolage-grotesque`** | **5.3.0** | 544 183 B | `index.css` = **samo `wght` 200–800** |
| `@fontsource/bricolage-grotesque` | 5.3.0 | 640 222 B | statične težine |

Licenca **OFL-1.1**, bez runtime dependencyja. Varijanta koja se importa
(`main: index.css`) je `wght`-only — **ne** `standard.css` (koja nosi sve tri osi
`opsz`+`wdth`+`wght` i latin subset joj je 131 548 B).

### Stvarna cijena na mreži

| subset | datoteka | veličina | kad se dohvaća |
|---|---|---:|---|
| latin | `bricolage-grotesque-latin-wght-normal.woff2` | **41 344 B** (40,4 KB) | uvijek |
| **latin-ext** | `bricolage-grotesque-latin-ext-wght-normal.woff2` | **18 668 B** (18,2 KB) | 🔴 **uvijek u praksi** — v. niže |
| vietnamese | `…-vietnamese-wght-normal.woff2` | 30 736 B | nikad |

🔴 **latin-ext nije opcionalan.** `unicode-range` latin subseta je `U+0000-00FF`; hrvatski
`č ć ž š đ Č Ć Ž Š Đ` leže u `U+0100-02BA` = **latin-ext**. Naslov „Točno" ili „Vježbaonica"
povlači drugi file. Realna cijena je **60 012 B ≈ 58,6 KB**, ne 40 KB.

Za usporedbu, zatečeni body font: Geist latin 29 400 B + latin-ext 16 512 B = **45,9 KB**.
Bricolage je **+31 %** naspram toga.

## D.2 Gdje bi se koristio

Predloženo: **`--font-heading` prestaje biti alias `--font-sans`.**
Danas je [index.css:10](frontend/src/index.css#L10) `--font-heading: var(--font-sans)` —
token postoji, ali **ne postoji nijedna komponenta koja ga koristi**; naslovi vuku
`font-sans` preko `html { @apply font-sans }`.

| mjesto | element | ima li već `text-2xl`+ |
|---|---|---|
| [TaskPage.tsx:271](frontend/src/pages/TaskPage.tsx#L271) | `<h1>` naslov zadatka | `text-2xl font-semibold tracking-tight` |
| `DashboardPage` | `<h1>` | za provjeriti u stageu |
| `ModulesPage` | `<h1>` + `<h2>` po modulu | |
| `ProfilePage` | `<h1>` + `<h2>` sekcija | |
| `LeaderboardPage` | `<h1>` | |
| `AppShell.tsx:94` | wordmark „SQL Tutor" | `text-base font-semibold tracking-tight` |
| `EmptyState` / `ErrorState` | naslov stanja | |

**Granica: `h1`/`h2` i wordmark. NE:** body, `h3`+, čipovi, gumbi, labeli, tablice.
Razlog nije estetski nego mjeriv — display crta ima uži razmak i izraženiji kontrast poteza;
ispod ~20 px gubi na čitljivosti, a upravo su ondje sve a11y-kritične površine iz matrice
(`muted-foreground` na 118 mjesta je `text-xs`/`text-sm`).

🔴 **Brojke ostaju mono.** To je zaseban zahtjev iz §E i **ne prelazi na display font** —
Bricolage nema tabularne brojke deklarirane u fontsource CSS-u, pa bi XP brojač poskakivao
pri promjeni znamenke.

## D.3 Bundle i FOUT

**Bundle:** +58,6 KB preko mreže, **0 KB u JS bundleu** (woff2 su zasebni assetovi koje
Vite hashira i servira paralelno). Ukupni font payload aplikacije raste s ~46 KB (Geist) +
JetBrains Mono na ~105 KB + JetBrains Mono.

**Nula CDN-a — invarijanta držana.** Fontsource paketi su lokalni npm assetovi; `@import`
u `index.css` ide kroz Viteov resolver, ne kroz mrežu. Isti mehanizam kao već postojeći
Geist i JetBrains Mono ([index.css:4-5](frontend/src/index.css#L4-L5)).

**FOUT:** fontsource deklarira `font-display: swap` u vlastitom `@font-face`
(provjereno u `index.css` paketa). Dakle **FOUT, ne FOIT** — naslov se prvo iscrta
sistemskim fontom pa zamijeni. Tri posljedice, po težini:

1. 🔴 **Pomak layouta na naslovima.** Bricolage je uži od `system-ui` fallbacka pri istoj
   veličini → naslov se pri swapu **skrati**. Na `TaskPage` `<h1>` nosi `text-balance`, pa
   se prelom može promijeniti. Mitigacija bez novog paketa: `size-adjust` na lokalnom
   `@font-face` fallbacku, ili `<link rel="preload">` za latin+latin-ext woff2 u
   [index.html](frontend/index.html).
2. 🟡 **Dva zahtjeva umjesto jednog** za prvi naslov s dijakritikom. Preload rješava.
3. 🟢 **Nema utjecaja na body ni mono** — Geist i JetBrains Mono ostaju netaknuti, pa
   tekst zadatka i editor ne trepere.

**Preporuka:** uvesti **s preloadom** oba subseta u `index.html`. Bez preloada FOUT je
vidljiv na svakom hladnom učitavanju, a evaluacija ide na javni URL gdje je prvo učitavanje
ujedno i prvi dojam.

## D.4 Alternative (za slučaj da se Bricolage odbaci)

Nisu potrebne — Bricolage **jest** dostupan. Ako se ipak traži drugi karakter, oba su na
fontsourceu s `wght` osi i latin-ext subsetom:

- **Instrument Sans** (`@fontsource-variable/instrument-sans`) — geometrijski grotesk s
  neuobičajeno visokim x-heightom i uskim `t`/`f`; djeluje tehnički, bliže Geistu nego
  Bricolage. Manje „karaktera", ali savršeno se slaže s body fontom.
- **Space Grotesk** (`@fontsource-variable/space-grotesk`) — izvedena iz Space Mono, ima
  monospace DNA u proporcionalnom obliku (kvadratične kontrapunkte, ravni terminali).
  🔴 To je **argument i protiv**: sučelje već ima jak mono glas (JetBrains Mono za SQL,
  brojke, breadcrumb) i display koji ga oponaša oslabio bi razliku „ovo je kod" / „ovo je
  naslov".

Bricolage je bolji izbor od obje jer njegov kontrast (varijabilna `wght` do 800, izražene
zaobljene forme) **ne** konkurira monou i **ne** kopira body.

---

# E — ŠTO IZ MOCKUPA ULAZI, ŠTO NE

## E.1 ULAZI — datoteke i kolizije

| stavka iz mockupa | dira | kolizija sa 1C |
|---|---|---|
| `-- ` mono section headeri (mockup `.nav-label`: „učenje", „napredak", „sustav") | [AppShell.tsx:38-79](frontend/src/components/layout/AppShell.tsx#L38-L79) `SidebarNav` — traži grupiranje `NAV_ITEMS` (danas ravan niz od 5) | 🔴 **DA — isti fajl** |
| mono breadcrumb (`sql_tutor . dashboard`) | [AppShell.tsx:102-111](frontend/src/components/layout/AppShell.tsx#L102-L111) header. ⚠️ `TaskPage.tsx:221-268` **već ima** vlastiti breadcrumb (`<nav aria-label="Putanja">`) → **dva breadcrumba jedan iznad drugog** ako se doda globalni | 🔴 **DA — isti fajl** |
| XP/level kartica na dnu sidebara | `AppShell.tsx` (novi footer) + novi `useProfile()` poziv u ljusci; podaci **postoje** (`ProfileResponse.xp/level/xp_in_level/xp_to_next/current_streak`) | 🔴 **DA — isti fajl** |
| user kartica iz topbara u sidebar | [AppShell.tsx:125-139](frontend/src/components/layout/AppShell.tsx#L125-L139) → premještanje u footer | 🔴 **DA — isti fajl** |
| dot-grid pozadina | `index.css` `@layer base` `body`. Mockup je čisti CSS `radial-gradient(… 1px, transparent 1.4px) 0 0/24px 24px` — **nema canvasa ni JS-a** unatoč komentaru „dot-grid canvas" na [sql-tutor-redesign-v3.html:46](docs/sql-tutor-redesign-v3.html#L46) | ne |
| brojke dosljedno u mono | `ProgressHero`, `StatsSummary`, `LeaderboardTable`, `BadgeStrip`, `MasteryBar`, `AttemptRow`, `ConceptCurveCard` (7 datoteka, `font-mono` klasa) | ne |

### 🔴 Kolizija: **4 od 6 stavki diraju `AppShell.tsx`, a on je i cijeli opseg stagea 1C**

Stage 1C (`docs/faza-4.7-nalazi.md` N-5) traži mobilni drawer s obaveznom stavkom **Profil**,
jer je ispod 768px sidebar `hidden … md:flex` ([AppShell.tsx:88](frontend/src/components/layout/AppShell.tsx#L88))
i **nema zamjenske navigacije** — prijavljen korisnik na telefonu nema puta do
`/profile#sudjelovanje`, teksta o sudjelovanju, kontaktu i brisanju podataka.

**Presuda: JEDAN PROLAZ kroz `AppShell.tsx`.** Redizajn sidebara i mobilni drawer moraju se
izvesti **istim potezom**, jer:

1. Drawer mora **replicirati strukturu** sidebara. Ako se prvo doda ravan drawer pa se
   sidebar potom pregrupira u tri sekcije s mono headerima, drawer odmah divergira.
2. XP kartica i user kartica u sidebar footeru **moraju** biti i u draweru — inače
   korisnik na telefonu i dalje nema Odjavu (danas je u headeru, koji ostaje, ali nakon
   preseljenja u sidebar bi nestala s mobilnog).
3. 🔴 **Izlazni kriterij N-5 se time proširuje:** drawer mora imati **Profil _i_ Odjavu**.
   Preseljenje user kartice iz topbara u sidebar je promjena koja Odjavu (danas
   `AppShell.tsx:141-144`, vidljiva na svim širinama) čini nedostupnom na mobilnom ako se
   drawer izvede bez nje.

**Napomena o `--ring`:** korekcija prstena na `oklch(0.556 0 0)` — koja je u
`faza-4.7-errata-prijedlog.md` §4 bila zakazana „za stage 1C" — **već je izvedena** u
commitu `5994107` (4c), za obje teme. Stage 1C je time sveden na mobilnu navigaciju.
Predloženi `oklch(0.62 0.04 280)` iz §C.4 je **nova, treća** vrijednost i nasljeđuje isti
zahtjev za vizualnom provjerom.

## E.2 NE ULAZI — provjereno iz koda, ne iz slike

| stavka | dokaz | presuda |
|---|---|---|
| **rang u sidebaru** (mockup: `Ljestvica <span class="badge hot">#14</span>`) | `Page_LeaderboardItem_` = `{items, total, limit, offset}`. `LeaderboardItem` ima `rank`, ali **samo za korisnike na dohvaćenoj stranici**. Envelope nema `my_rank` ni ekvivalent (`grep -in "my_rank\|rank" schema.d.ts`) | ✅ **potvrđeno — podatak ne postoji.** Izračun bi tražio dohvat svih stranica |
| **sparkline 7 dana** | `ProfileResponse` nema vremenski niz XP-a. `MasteryHistoryPoint` postoji, ali je **P(L) po konceptu**, ne XP po danu — i vezan je na `attempt_id`, ne na kalendar | ✅ **potvrđeno** |
| **dnevni cilj** | `grep -in "goal\|daily" schema.d.ts` → **0 pogodaka**. Nema ni polja ni koncepta u backendu | ✅ **potvrđeno** |
| **trendovi ▲▼** | traže dvije vremenske točke iste metrike. `ProfileResponse` vraća samo trenutno stanje (`xp`, `level`, `current_streak`, `longest_streak`) | ✅ **potvrđeno** |
| **zvono / obavijesti** | 14 endpointa u `schema.d.ts`, nijedan nije notifikacijski (`/register /login /me /attempt /next-task /profile /task/{id} /modules /badges /attempts /leaderboard /mastery-history /run /admin/agent-logs`) | ✅ **potvrđeno** |
| **Vježbaonica / Postignuća / Postavke** | `routes/router.tsx` — postoje `/`, `/modules`, `/task`, `/task/:taskId`, `/profile`, `/leaderboard`, `/admin`, `/login`, `/register`. Nijedne od tri rute nema | ✅ **potvrđeno.** „Postignuća" bi bila duplikat `BadgeGallery` na `/profile` |
| **konfeti** | Faza 4.6 (motion) **REZANA**; `framer-motion`/`motion` nisu u `package.json` — [index.css:130-135](frontend/src/index.css#L130-L135) to izrijekom zabranjuje | ✅ **potvrđeno** |
| **cmdk** (mockup `⌘K` pretraga) | `cmdk` nije u `package.json`; nema search endpointa | ✅ **potvrđeno** |
| **klizni indikator** (mockup `.caret`) | Faza 4.6 rezana | ✅ **potvrđeno** |
| 🔴 **`~5 min`** | **PREMISA JE NETOČNA.** `TaskDetailResponse.estimated_time_sec: number \| null` postoji, backend ga puni ([routes.py:364](backend/app/api/routes.py#L364), model `GeneratedTask` ga traži `ge=30, le=600`), a frontend ga **već renderira**: [TaskPage.tsx:213-214](frontend/src/pages/TaskPage.tsx#L213-L214) računa `estMin`, [TaskPage.tsx:279-281](frontend/src/pages/TaskPage.tsx#L279-L281) ga prikazuje kao `<Clock/>~{estMin} min` | 🔴 **NIJE „ne ulazi jer nema podataka" — VEĆ POSTOJI.** Stavka se briše s popisa; pitanje je samo hoće li redizajn zadržati zatečeni prikaz (preporuka: da, nepromijenjeno) |

## E.3 🔴 Koliko modula stvarno postoji: **7, ne 12**

Mockup: `Moduli <span class="badge">12</span>` ([sql-tutor-redesign-v3.html:483](docs/sql-tutor-redesign-v3.html#L483)).

Autoritativni izvor je Prolog ontologija (CLAUDE.md: *„Prolog ontologija je AUTORITATIVNI
izvor istine"*):

```prolog
% backend/prolog/ontology.pl:3-4
% Sub-faza 1B: 30 koncepata, 7 modula (1..6 + 0 transverzalni),
%              30 in_module mapping, 30 tier, 38 prerequisite
```

**7 modula** (0 = „Transverzalni", 1–6 tematski). Brojka 12 iz mockupa je izmišljena.
Ako se brojčani badge uz „Moduli" zadrži, mora se izvoditi iz `useModules()`
(`ModuleNode[]`), ne hardkodirati — inače je to treći podatak koji sučelje tvrdi bez pokrića.

---

# F — RIZIK NA EVAL-VERIFICIRANOM PUTU

## F.1 Datoteke koje redizajn dira na Task screenu

| datoteka | redaka | što se mijenja | rizik |
|---|---:|---|---|
| [pages/TaskPage.tsx](frontend/src/pages/TaskPage.tsx) | 401 | 4 stanja panela (`feedback`/`infra`/`gateway`/`null`), breadcrumb, grid `xl:grid-cols-[minmax(360px,5fr)_7fr]`, uklanjanje `useTheme` | 🔴 **visok** |
| [components/task/FeedbackPanel.tsx](frontend/src/components/task/FeedbackPanel.tsx) | 228 | sve tri `-soft` plohe + `background/60` mono blok + `accent-warm-text` XP čip | 🔴 **visok** |
| [components/task/RunResultPanel.tsx](frontend/src/components/task/RunResultPanel.tsx) | 222 | `card/50` stale-dim, `incorrect-soft` greška | 🟡 srednji |
| [components/task/SqlEditor.tsx](frontend/src/components/task/SqlEditor.tsx) | 95 | uklanjanje `dark` propa i light grane (`:24, :35, :85`) | 🔴 **visok** |
| [lib/monaco-theme.ts](frontend/src/lib/monaco-theme.ts) | 122 | brisanje `sqlTutorLight` + **preračun svih 11 hex vrijednosti** dark teme | 🔴 **visok** |
| [components/task/SchemaReference.tsx](frontend/src/components/task/SchemaReference.tsx) | 119 | plohe + mono | 🟢 nizak |
| [components/task/TaskDifficultyChip.tsx](frontend/src/components/task/TaskDifficultyChip.tsx) | 44 | **ništa** — čisto `difficulty-*` (zamrznuto) | 🟢 nema |
| [components/ui/button.tsx](frontend/src/components/ui/button.tsx) | — | 4 `dark:` razrješenja (§A.8) | 🔴 **visok** — Run i Submit |
| [components/ui/input.tsx](frontend/src/components/ui/input.tsx) | — | 1 `dark:` razrješenje | 🟡 srednji |
| [lib/verdict-ui.ts](frontend/src/lib/verdict-ui.ts) | 60 | mapa verdikt → klase; **`soft` ima 0 potrošača** (ERRATA #10b) | 🟡 srednji |

## F.2 🔴 Najveći pojedinačni rizik: `monaco-theme.ts`

Brief traži da datoteka **više ne sadrži nijedan ručni literal** i da se sve izvodi kroz
`scripts/a11y/palette.py`. To je najveći skok u opsegu cijelog redizajna, jer:

1. **Monaco ne vidi CSS varijable.** Traži hex. Izvedenost se može postići samo
   **generiranjem** datoteke (skripta piše `.ts`) ili **runtime konverzijom**
   (`getComputedStyle` + oklch→hex u JS-u). Prvo dodaje build korak; drugo dodaje
   konverzijski kod u frontend koji dosad ne postoji.
2. **`#292929` nema izvor** (§A.9). Bez odluke odakle dolazi, „nula literala" nije
   dostižno — jedan literal ostaje ili se mora izmisliti token.
3. **Sintaksne boje imaju dodatni zahtjev koji matrica ne mjeri:** moraju biti razlučive
   **međusobno**, ne samo prema pozadini. `monaco_check.py` to izrijekom kaže i ne mjeri.
   Nova pozadina (`--card` s indigo tintom, `#141625` umjesto `#171717`) mijenja kontrast
   svih 7 sintaksnih boja odjednom.

**Preporuka: razdvojiti.** Uklanjanje `sqlTutorLight` (mehaničko, sigurno) ide u stage s
ukidanjem light teme. Izvođenje dark vrijednosti kroz `palette.py` je **zaseban stage** s
vlastitim izlaznim kriterijem — inače se najrizičnija promjena skriva u najvećem commitu.

## F.3 Što točno mora u re-verifikaciju

### Automatski — `frontend/e2e/smoke.spec.ts` postoji od `7f7c9aa`

Pokriva: `register → login → /task → Run → Submit → feedback → „Sljedeći zadatak"`.
🔴 **Ali njegov vlastiti docstring ograničava doseg:** *„mehanika, ne točnost… NE tvrdi da
je verdikt 'Točno'"*. Smoke dokazuje da lanac **prolazi**, ne da izgleda ispravno.
Za paletu je slijep.

Dodatno, smoke ovisi o Monacu na način koji redizajn dira: `typeSql()` koristi
`keyboard.insertText` jer `keyboard.type()` aktivira SQL autocomplete
(`e2e/smoke.spec.ts:28-40` — dokumentiran incident iz runa 2026-08-10). Promjena Monaco
teme **ne bi smjela** to dirati, ali `beforeMount={defineThemes}` mijenja se istim potezom.

### Ručno — 4 stanja FeedbackPanela, s pravim podacima

| # | stanje | kako se dobiva | što se gleda |
|---|---|---|---|
| 1 | **correct** | točan upit | `correct-soft` ploha, `correct` tekst (7,74:1), XP čip `accent-warm-text` (8,57:1), `--ease-reward` animacija (`FeedbackPanel.tsx:130`) |
| 2 | **partial** | upit s `row_mismatch` (`lib/feedback.ts` `deriveVerdict`) | `partial-soft`, i 🔴 **ikona + tekstualna oznaka** — obavezan kanal jer je partial hue 55–60 blizu accent-warm 70–85 (ERRATA #13) |
| 3 | **incorrect** | netočan upit | `incorrect-soft`, `background/60` mono blok s detaljem greške (7,35:1) |
| 4 | **infra / gateway** | 504 ili pad backenda | `TaskPage.tsx:195-200`. 🔴 **N-10:** ErrorState posuđuje **verdict** plohu za **sistemsku** grešku — student ne razlikuje vlastiti neuspjeh od kvara aplikacije. Redizajn to **ne popravlja**, ali ga čini vidljivijim (tint postaje jači) |

### Ručno — Monaco i gumbi

| # | što | kriterij |
|---|---|---|
| 5 | Monaco na novoj `--card` podlozi | 7 sintaksnih boja razlučivo **međusobno** i od `#141625`; cursor/aktivni broj retka (`accent-warm`) i dalje čitljivi |
| 6 | Run gumb (`variant="outline"`) | nakon uklanjanja `dark:border-input dark:bg-input/30` — obris i dalje vidljiv nad `card` |
| 7 | Submit gumb (`variant="default"`) | `primary` s indigo tintom i dalje čita kao primarna akcija |
| 8 | fokus na Run/Submit tipkovnicom | novi `--ring` (`#81849e`) — 🔴 ovo je jedno od 5 mjesta iz izlaznog kriterija 1C |
| 9 | `Ctrl+Enter` / `Shift+Enter` | kratice **ne smiju** puknuti — registriraju se u `onMount` i ovise o tome da `onRun`/`onSubmit` postoje od PRVOG rendera (`SqlEditor.tsx:57-59`) |

## F.4 Redoslijed koji minimizira rizik

1. **Ukidanje light teme** — mehaničko, nula novih vrijednosti. Smoke mora proći.
   (Uključuje `--radius` migraciju §A.5, `sonner` literal §A.2, 6 `dark:` razrješenja §A.8.)
2. **Ažuriranje harnessa** — `palette.py` (`load_tokens` + `SELF_TEST`), `contrast_matrix.py`,
   `monaco_check.py`, `pairs.py` (fantomski `neutral` par §B.5). Bez ovoga korak 3 nema čime
   dokazati da je prošao.
3. **Primjena palete** — jedna datoteka (`index.css`), puna matrica, presnimavanje 7 figura.
4. **`monaco-theme.ts` izvedenost** — zaseban stage (§F.2).
5. **`AppShell` + mobilni drawer (1C)** — jedan prolaz (§E.1).
6. **Display font** — zadnji, jer jedini mijenja metriku teksta i time sve snimke.

---

## Reproducibilnost

Svo mjerenje u §C izvedeno je funkcijama iz `scripts/a11y/` nad kopijom `index.css`:

```bash
# baseline — dokaz da je konvertor ispravan (§C.0)
python3 scripts/a11y/contrast_matrix.py

# gamut, hue-udaljenost, ΔE kolizije, (L,C) pretraga za --ring
# skripte u scratchpadu; ulazi su čitani iz repoa, izlazi nisu upisivani u repo
```

🔴 **Ništa od ovoga nije commitano u `index.css`.** Predložena paleta iz §C.3 je tekst u
ovom dokumentu, ne kod. `git status` na `faza-4-7-polish` pokazuje samo ovaj dokument i
`docs/sql-tutor-redesign-v3.html` (mockup, untracked).
