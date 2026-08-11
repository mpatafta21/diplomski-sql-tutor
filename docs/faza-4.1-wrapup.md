# Faza 4.1 — Frontend foundation — WRAP-UP

**Status:** ✅ KOMPLETNA (4.1a + 4.1b + 4.1c, mergeano u `main` kroz PR #18). Postoji "lijepa i spojena" ljuska: design sistem + typed klijent + auth flow + protected shell — sve buduće faze (4.2–4.7) grade na ovome bez retrofita.
**Obuhvat:** pod-faze **4.1a** (tooling & scaffold), **4.1b** (design system & tokeni), **4.1c** (app shell & infra).
**Rezultat:** backend suite **466 passed / 1 skipped** (netaknut — 0 izmjena backenda u 4.1b/c); frontend **`tsc -b` + build + oxlint + prettier zeleni**; **ručna** e2e verifikacija kroz headless Chrome (CDP, živi backend): **12 scenarija** — *nije* committed automatizirani suite (NALAZ #17).
**Grane/PR/tagovi:** `faza-4-1-frontend` (PR #18, mergean) · tagovi `faza-4-1a-scaffold` → `faza-4-1b-design-system` → `faza-4-1c-app-shell`.

Cilj cijele 4.1: frontend temelj koji je **contract-safe od prvog dana** (tipovi generirani iz backend OpenAPI-ja) i **vizualno namjeran** (token-sistem prije ijedne ekranske komponente), s auth gate-om koji radi e2e protiv živog backenda.

---

## 1. Što je 4.1a donijela (tooling & scaffold)

- **`frontend/`**: Vite + React 19 + TypeScript 6, Tailwind **v4 CSS-first** (bez tailwind.config.js — `@theme` u CSS-u), shadcn (stil **Nova**, neutral/oklch baza), oxlint + prettier, path aliasi (`@/`).
- **CORS** na backendu (jedina backend izmjena cijele 4.1; `VITE_API_URL=http://localhost:8000`).
- **Makefile run-recepti** (riješeno nedokumentirano pokretanje): `infra-up` / `wait-db` / `db-migrate` / `db-seed` / `backend` / `frontend` / `dev` (sve odjednom).
- Font: Geist Variable kroz **fontsource** (self-hosted npm paket, bez CDN-a) — obrazac koji 4.1b ponavlja za mono.

---

## 2. Što je 4.1b donijela (design system & tokeni)

### 2.1 MASTER.md — SSOT (s epizodom)
- `ui-ux-pro-max --design-system --persist` generirao je `design-system/sql-tutor/MASTER.md` — ali **krivo klasificiran** ("Kids Learning / Vibrant / light-only / Fira / zeleni accent"), suprotno §3 plana.
- **Odluka:** sadržaj odbačen i **ručno prepisan** prema zaključanom design languageu (dark-first "mirna dev-konzola", Geist zaključan, jedan topli amber accent). Zadržan samo generički spacing/shadow kostur. Povijest odbacivanja zabilježena u headeru datoteke.
- MASTER.md je od sada **izvor istine za sve tokene** kroz 4.2–4.7.

### 2.2 Token sustav (`frontend/src/index.css`, oklch, light+dark)
Sve vrijednosti **numerički AA-verificirane** (skripta: oklch→sRGB gamut + WCAG kontrast; tekst ≥4.5:1, UI grafika ≥3:1, obje teme):

| Grupa | Sadržaj |
|---|---|
| Semantika verdicta | `correct`(hue 150) / `incorrect`(25) / `partial`(55–60, **REZERVIRAN** — ERRATA #8) / `neutral` + `-soft` pozadine |
| Amber accent **trio** | `--accent-warm` (fill) / `-foreground` (tekst na fillu) / `-text` (tekst na pozadini) — **isključivo za XP/level/streak/badge/progres**; ime `-warm` jer shadcn već zauzima `--accent` |
| Mastery gradient | P(L) low→high, plavo→cijan (260→190), **monoton po svjetlini** (CB-safe primarni kanal), 5 stopova |
| Concept-tier (×3) | violet 300 — `easy/medium/hard` (`concepts.tier`, models.py:90) + `-foreground` parovi |
| Module-difficulty (×5) | magenta 345 — `beginner..expert` + desaturirani `cross_module` (models.py:71) + `-foreground` parovi. **ODVOJENA skala od tier!** |
| Data-viz | `--chart-1..5` (plava/teal/violet/magenta/amber) — zamijenjeni shadcn sivi placeholderi |
| Tipografija | modularna skala 1.250 + line-height/tracking; `--font-mono` (JetBrains Mono Variable, fontsource) |
| Motion | `--ease-standard/entrance/exit/reward` + `--duration-instant..reward` (vrijednosti; framer-motion tek 4.6) |
| A11y | globalni `prefers-reduced-motion` guard u `@layer base` |

**Cross-scale guard** (pravilo u MASTER.md §2.7): tier/difficulty NE koriste correct/incorrect hue ni amber; mastery hue-distinktan od accenta i semantike. Hue mapa: `25 incorrect · 55 partial · 70-85 accent · 150 correct · 190-260 mastery · 300 tier · 345 difficulty`.

### 2.3 Monaco tema
- `src/lib/monaco-theme.ts` — dark+light **vrijednosni objekti** (bez monaco paketa; 4.3 ih primjenjuje). Pozadina = `--card`, kursor/selekcija = amber, SQL keyword = chart-1, string = correct, broj = chart-2, funkcija = chart-3. Hex vrijednosti derivirane iz tokena istom kalibracijskom skriptom.

---

## 3. Što je 4.1c donijela (app shell & infra)

### 3.1 Typed API klijent (contract-safety jezgra)
- `openapi-typescript` → `src/lib/api/schema.d.ts` iz živog `/openapi.json` (`npm run gen:api`); `openapi-fetch` wrapper s Bearer middlewareom.
- **Dokazano:** namjerni pristup nepostojećem polju → `error TS2339` → build fail (pa maknuto). Nula ručno tipiziranih API odgovora.

### 3.2 Auth flow
- `AuthProvider`: register (JSON) / **login (username+password, form-encoded — OAuth2 form!)** → token (localStorage) → `GET /me`; mount validacija postojećeg tokena.
- **401 tok:** middleware (runtime, jer security dep NIJE u OpenAPI shemi → tipizirana error grana je `never`) → `status='anon'` → deklarativni `<Navigate to="/login">` + sonner toast "Sesija je istekla".

### 3.3 Routing & shell
- react-router **v7** `createBrowserRouter`: `/login`, `/register` javne (`PublicOnlyRoute` — authed → `/`); `/` protected placeholder ("Dashboard dolazi u 4.2").
- `AppShell`: sidebar (nav **skica** — Dashboard/Moduli/Zadatak/Profil/Ljestvica vode na `/`; **Admin stavka role-gated**) + header (theme toggle, username + role badge, logout). Dark-first, sve iz tokena.

### 3.4 Primitivi (§3.4 plana — koriste se posvuda od 4.2)
- `LoadingState` (**skeleton, ne spinner**) + `FullPageLoading` · `EmptyState` (ikona+poruka+CTA) · `ErrorState` (oporavljiv, retry) · `ErrorBoundary` (class, hvata render greške; mrežne idu kroz TanStack Query).
- Login/Register stranice: RHF + zod v4, inline greške po polju, 401/409/422 poruke, loading na submitu.

### 3.5 E2E dokaz (RUČNA verifikacija kroz headless Chrome/CDP, živi backend) — 12 scenarija
anon→/login redirect · register→shell · login→shell · logout→token clear · krivi kredencijali→inline poruka · **401 (pokvaren token)→redirect+clear** · 409 duplikat poruka · **admin role-gate (student ne vidi / admin vidi)** · nula pageerror-a.

---

## 4. Čemu ovo služi ostalim fazama

- **4.2 (Dashboard/Modules):** state-primitivi + typed klijent + tokeni (mastery gradient za vizualizacije, difficulty skala za module cards); klijentski join `/profile.mastery` × `/modules`.
- **4.3 (Task screen):** Monaco tema + `--font-mono` spremni; semantika verdicta (`correct`/`incorrect` + `-soft` baneri) definirana; shell ruta se samo dodaje.
- **4.4–4.5:** chart paleta za Recharts (BKT krivulje), tier čipovi s foreground parovima, admin ruta iza postojećeg role-gatea.
- **4.6 (Motion):** easing/duration tokeni već definirani — framer-motion ih samo konzumira.
- **4.7 (QA):** AA baseline već numerički postavljen; reduced-motion guard globalan.

---

## 5. Zaključane odluke / napomene za nasljednike

> ⟳ **NUMERACIJA NAPUŠTENA (2026-08-10, Faza 4.7 / NALAZ N-8).** Popis ispod ostaje
> **nepromijenjen kao povijesni zapis** — sadržaj sve tri invarijante i dalje vrijedi.
> Napušteni su **brojevi**, ne pravila. Razlog: numeracija je ostala neodržavana (kasniji
> wrapupi — 4.2 §5, 4.3 §5, 4.4b — nabrajaju invarijante u istom odjeljku **bez brojeva**),
> pa su komentari u kodu naknadno izmislili `#4` i `#6` kojih ovdje nema, a `#1` i `#2`
> upotrijebili za **druga pravila** nego što ovdje piše. Od 4.7 kod referencira invarijante
> **opisno, bez broja** (17 mjesta u 18 datoteka). Isti obrazac i isti razlog kao ispravak
> `#49` u `docs/errata.md` — v. ondje konvenciju o prostoru imena.
>
> ⟳ **KONSOLIDIRANO (2026-08-10, 1C-zatvaranje): kanonski popis je sada
> `docs/invarijante.md`.** Sve tri invarijante ispod ondje su prenesene s opisnim
> naslovima i stabilnim sidrima, uz hazard i presedan. **Ovaj odjeljak ostaje
> nepromijenjen kao povijesni zapis** — ne ažurira se više.

- **Invarijanta #1 — 401 runtime:** security dep nije u OpenAPI shemi → NIKAD hvatati auth greške kroz tipiziranu `error` granu (ona je `never`); uvijek `response.ok` + middleware. Vrijedi za SVE zaštićene pozive.
- **Invarijanta #2 — TS6 `erasableSyntaxOnly`:** bez parameter-properties (class polja eksplicitno).
- **Invarijanta #3 — 44px touch-targeti (WCAG 2.5.5):** shadcn Nova je kompaktan (h-8!) → vendorani defaulti bumpani: button `default h-11 / lg h-12 / icon size-11`, input `h-11`. `xs/sm` varijante = svjesni escape-hatch za gusti sekundarni UI, NE za primarne akcije.
- **Komponente vuku tokene** — nula hardkodiranih boja (grep-verificirano); MASTER.md je SSOT.
- **shadcn CLI kvake:** treba `npm_config_legacy_peer_deps=true` (peer konflikt `openapi-typescript`↔TS6); registry item `form` je **prazan stub** → koristi se `field`; `sonner.tsx` stub pretpostavlja next-themes → adaptiran na vlastiti `ThemeProvider` (`src/lib/theme/`, `.dark` klasa + localStorage).
- **Token-preview stranica** (živi katalog iz 4.1b) uklonjena u 4.1c — dostupna na tagu `faza-4-1b-design-system`.
- **Sandbox ne može `git push`** — commit/tag lokalno, push+PR ručno (obrazac od 3D nadalje).

### Errata-trail (ažurirano stanje nakon 4.1)
| # | Stavka | Stanje |
|---|---|---|
| ERRATA #8 | `attempts` nema `verdict` | I dalje otvoreno — `partial` token postoji ali se NE koristi u UI (4.3 prikazuje samo correct/incorrect) |
| flag #3 | `new_badges` best-effort | Otvoreno — badge-unlock kozmetika, autoritativno iz `/profile` (4.3/4.4) |
| flag #5 | F2 XP konstante | ✅ **ZATVOREN** (2026-07-08, grana `faza-gamifikacija-xp`, tag `flag-5-xp-konstante`) — mentor potvrdio postojeće vrijednosti, TODO markeri → racional, 0 behavioralnih promjena |
| NALAZ #7 | `task.module_id ≠ primary_concept.module` (3/83) | Otvoreno — Module overview (4.2) rubni slučaj; cleanup Faza 6 |
| **NOVO** | Leaderboard test nije izoliran od stvarnih usera | `test_leaderboard_global_order_and_rank` asertira `total` nad cijelom dev bazom → svaki ručno registriran student ruši test. Sanirano brisanjem artefakata; trajni fix (test-DB izolacija ili scoped assert) = kandidat za 4.5/6. E2E skripte ne smiju ostavljati usere u `tutor_main`. |

---

## 6. Sljedeće na redu

**Faza 4.2 — Dashboard + Module overview:**
1. Dashboard: XP bar + level + streak hero (accent-warm tokeni), recommended-task CTA iz `/next-task`, mastery viz (klijentski join `/profile.mastery` × `/modules` — mastery vraća SAMO `concept`+`p_l`, ime/modul dolaze iz `/modules`!), badge highlights.
2. Module overview: 6 module cards (difficulty skala ×5), koncept-razina mastery (tier čipovi ×3 + mastery gradient), locked/unlocked iz `prerequisites` grafa (ne izmišljati logiku).
3. Skill-lanac po planu §4: `ui-ux-pro-max` (data-dense layout) → `ui-styling` → `emil-design-eng` → `/code-review`.

> Jezgra (4.0–4.4) mora ostati eval-upotrebljiva prije 4.6/4.7 polisha. Frontend od sada samo konzumira zaključani backend ugovor; svi podaci s pravih endpointa (nula mock-a).
