# Faza 4 — Frontend (FULL BUILD) — Master plan

**Status:** plan (ulaz nakon `faza-3-complete`, backend 402/1, 0 regresija, sve mergeano u `main`)
**Cilj faze:** kompletan, izpoliran React UI za adaptivni SQL tutoring sustav — student flow + dashboard + profil + leaderboard + admin, podignut na produkcijsku razinu dizajna i UX-a.
**Rok konteksta:** rujan (obrana). **Odluka korisnika:** full build bez vremenskog rezanja — kvaliteta dizajna prioritet. Runway-disciplina i dalje vrijedi na razini *redoslijeda* (jezgra prije ukrasa), ali ništa se ne reže unaprijed.
**Izvor istine za ugovor:** `backend/app/api/schemas.py` + `routes.py` (3 postojeće rute) → proširuje se u 4.0. Ovaj dokument je plan; **stvarni CC promptovi pišu se per-checkpoint** (isti model kao 3A–3E).

---

## 0. Napomena o brojidbi (uskladi i ostavi)

| Traka | Naziv frontenda |
|---|---|
| Master plan (`diplomski-plan.docx`) | **Faza 4** = Frontend (4 tjedna, sada full) |
| Stara radna traka (`faza-3-plan.md`) | nazivala backend "Faza 3" + `3F` frontend |
| **Od sada (ovaj dokument)** | **Faza 4** s pod-fazama **4.0 → 4.7** |

Faza 5 (HintAgent + LLM) i dalje POSLIJE frontenda. Faza 6 eval, Faza 7 pisanje. Frontend ne smije pojesti runway za eval+pisanje — zato je redoslijed pod-faza takav da je **funkcionalna jezgra (4.0–4.4) upotrebljiva za eval i prije nego 4.5–4.7 završe**. Ako rok ipak pritisne, **prva se reže 4.6/4.7 polish, NIKAD 4.0–4.4**.

---

## 1. Zaključane odluke (ledger)

| # | Odluka | Vrijednost / razlog |
|---|---|---|
| D-AUTH | **Pravi JWT.** `/register` (role forsiran `student`) + `/login`. 1 admin seedan (ti + mentor). | `users` već ima `password_hash` + `role{student,admin}` — infra postoji, samo nije spojena. Eval mora razlučiti studente. Full build gradi protiv konačnog ugovora od dana 1, bez retrofita. |
| D-RUN | **`POST /run`** (izvrši upit BEZ bodovanja) uz postojeći `POST /attempt` (scored). | Diže UX task screena — "Run" prije "Submit", + pokriva sample-data preview istim endpointom. |
| D-HIST | **`skill_mastery_history`** tablica; KM upisuje snapshot po svakom BKT updateu. | `skill_mastery` je current-only upsert → nema izvora za "P(L) kroz vrijeme". Snapshot od sada = krivulje se grade tijekom eval-a (poklapa se s prikupljanjem podataka). |
| D-ER | **ER dijagram statički** (jedan dijeljeni `ecommerce_v1` sandbox), sample-data preview **kroz `/run`**. | Sandbox je jedna dijeljena shema → jedan dizajnirani ER, nije per-task. Jedan endpoint (`/run`) pokriva i preview i ad-hoc izvršavanje. |
| D-REST | **REST core**, WebSocket opcionalni finale (4.6). | `POST /attempt` vraća sve sinkrono → REST await dovoljan za jezgru. WS je "live" sloj, ne temelj. |
| D-CLIENT | **Typed API klijent generiran iz OpenAPI** (`openapi-typescript`). | FastAPI izlaže `/openapi.json` → frontend tipovi se generiraju iz backenda. Garantira da komponenta gleda točno ono što ruta vraća (polja/tipovi/null) — direktno servisira "verificiraj da ruta vraća ono što komponenta očekuje". |

---

## 2. Ciljna API površina nakon Faze 4.0 (ugovor koji frontend konzumira)

Legenda: **[POSTOJI]** = već u `main` · **[NOVO]** = gradi se u 4.0 · 🔒 = traži JWT nakon 4.0b · 🛡️ = admin-only.

| Metoda | Path | Vraća | Stanje |
|---|---|---|---|
| POST | `/register` | `{token, user:{id,email,role}}` | **[NOVO 4.0b]** |
| POST | `/login` | `{token, user:{id,email,role}}` | **[NOVO 4.0b]** |
| GET | `/me` 🔒 | trenutni user (zamjena za gol `user_id`) | **[NOVO 4.0b]** |
| POST | `/attempt` 🔒 | `AttemptResponse` (feedback, xp_delta, xp, level, current_streak, new_badges, recommendation) | **[POSTOJI]** → migrira `user_id` iz body-a u token |
| POST | `/run` 🔒 | `{columns, rows, exec_ms, error}` (bez bodovanja) | **[NOVO 4.0a]** |
| GET | `/next-task` 🔒 | `NextTaskResponse` (task_id, concept, reason) | **[POSTOJI]** → `user_id` iz tokena |
| GET | `/task/{id}` 🔒 | `{id, title, description, difficulty, concepts[], module_id}` (+ ER/sample se ne šalju — ER statički, sample kroz `/run`) | **[NOVO 4.0a]** |
| GET | `/profile` 🔒 | `ProfileResponse` (xp, level, streak ×2, mastery[{concept,p_l}], badges[]) — ostaje "tanak" | **[POSTOJI]** → `user_id` iz tokena |
| GET | `/modules` 🔒 | moduli + koncepti `{code, name, module_id, tier, order_index, prerequisites[]}` | **[NOVO 4.0a]** |
| GET | `/badges` 🔒 | katalog svih bedževa `{code, name, description, criteria, icon}` (za locked/unlocked galeriju) | **[NOVO 4.0a]** |
| GET | `/attempts` 🔒 | povijest pokušaja trenutnog usera (paginirano) | **[NOVO 4.0a]** |
| GET | `/mastery-history` 🔒 | `[{concept, p_l, ts}]` za BKT krivulje | **[NOVO 4.0a]** (čita `skill_mastery_history`) |
| GET | `/leaderboard` 🔒 | global + weekly `[{rank, display_name, xp, level}]` | **[NOVO 4.0a]** |
| GET | `/admin/agent-logs` 🔒🛡️ | `agent_messages_log` (paginirano, filter po cid/agentu) | **[NOVO 4.0a]** |

**Dizajn-odluka (potvrđena):** `/profile` i `/modules` ostaju razdvojeni; frontend joina `mastery (concept→p_l)` s `/modules (concept→name/module)` u klijentskom cacheu. Manje endpoint-churn-a, jedan izvor taksonomije.

---

## 3. Design language (sloj koji diže build iznad templatea)

> Ovo nije "instaliraj shadcn pa kreni". Definira se kao **prvi razred** u 4.1b prije ijedne ekranske komponente. Cilj: aplikacija koja izgleda kao namjeran proizvod, ne kao starter.

### 3.1 Smjer (prijedlog — potvrditi u 4.1b)
**"Mirna dev-konzola za učenje."** Dark-first (pari s Monaco editorom, smanjuje umor pri dugim SQL sesijama), s jednim toplim accentom za napredak/gamifikaciju. Light tema kao ravnopravan token-set, ne naknadna misao. Estetika: precizna tipografija, velikodušan prostor, podaci u prvom planu, suptilan motion koji nagrađuje — bez "dječje gamifikacije".

### 3.2 Tokeni (definiraju se kao CSS varijable + Tailwind theme extend)
- **Tipografija:** UI sans (npr. Inter / Geist) + monospace za SQL i rezultate (npr. JetBrains Mono). Modularna skala (1.250), definirani line-height/tracking tokeni.
- **Boja — semantika:** `correct` / `incorrect` / `partial` (rezervirano za buduću migraciju verdicta), `neutral`, `accent`. Svi kao HSL token trojke za dark/light.
- **Boja — mastery skala:** kontinuirani gradijent low→high P(L) (npr. hladno→toplo), **colorblind-safe**, isti se koristi u barovima i krivuljama.
- **Boja — tier skala:** Beginner→Expert (5 koraka), dosljedna na module cards, badge okvirima, koncept čipovima.
- **Data-viz paleta:** zaseban set za Recharts (BKT krivulje, distribucije) — kategorijska + sekvencijalna, a11y-provjerena.
- **Radijusi / sjene / spacing:** skala (4px baza), elevation tokeni.
- **Monaco tema:** custom tema usklađena s UI tokenima (ne default vs-dark) — isti accent, ista pozadina, isti mono font.

### 3.3 Motion sustav (Framer Motion / `motion`)
Definirani easing/duration tokeni; svaka mikrointerakcija vuče iz njih. Gamifikacijski momenti (XP gain count-up, level-up, badge unlock, streak flame) imaju namjenske, suzdržane animacije — feedback, ne konfeti-spam. Motion odluke vodi `emil-design-eng` skill; svaka napisana animacija prolazi `/review-animations` gate prije commita (vidi §4 skill-lanac).

### 3.4 Stanja kao prvi razred
Svaka data komponenta ima dizajnirano: **loading** (skeleton, ne spinner), **empty** (poziv na akciju), **error** (oporavljiv), **success**. Definira se kao primitiv u 4.1c, koristi posvuda.

### 3.5 Accessibility baseline
WCAG 2.1 AA: kontrast ≥ AA na svim tokenima, fokus-vidljivost, tipkovnička navigacija (uklj. Monaco i submit/run shortcuts), ARIA na interaktivnim komponentama, `prefers-reduced-motion` poštovan. Provjera u 4.7.

---

## 4. Tech izbori (zaključani za 4.1)

| Sloj | Izbor | Razlog |
|---|---|---|
| Build | Vite + React + TS | plan + brzina |
| Styling | Tailwind + shadcn/ui (token-customiziran) | brzina + kontrola; tokeni ga skidaju s "stock" izgleda |
| Data fetching | **TanStack Query** | cache, loading/error stanja, invalidacija nakon attempta — diže iznad `useState`+fetch |
| API tipovi | **openapi-typescript** (+ tanak `openapi-fetch` wrapper) | tipovi iz backend OpenAPI = contract-safe |
| Forme | react-hook-form + zod | auth forme, validacija usklađena s backend pravilima |
| Editor | `@monaco-editor/react` + custom SQL tema | jezgra task screena |
| Charts | Recharts | BKT krivulje, mastery viz (plan) |
| Motion | Framer Motion (`motion`) | gamifikacijske animacije, page transitions |
| Ikone | lucide-react | dosljedan set |
| Toasts | shadcn `sonner` ili radix toast | badge/feedback notifikacije |
| Routing | react-router-dom | protected routes |

### Design-skill lanac (Claude Code)

Frontend se NE gradi golim shadcn-om. CC ima 5 design skillova; svaki pokriva drugu fazu izrade komponente:

| Skill | Uloga | Aktivacija | Poziv / artefakt |
|---|---|---|---|
| `ui-ux-pro-max` | **plan** izgleda — paleta, font par, layout pattern, izbor grafa (161 palet / 57 fontova / 25 chart tipova, mapirano na React+Tailwind+shadcn) | auto | `python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<opis>" --design-system --persist` → generira `design-system/MASTER.md` (SSOT) |
| `ui-styling` | **gradnja** komponenti — shadcn/Radix/Tailwind, dark/light theming, responsive grid/stack, accessible dijalozi/tablice/forme | auto | — |
| `emil-design-eng` | **polish + motion** — mikrointerakcije, easing/timing, "nevidljivi detalji" (Emil Kowalski standard) | auto | — |
| `accessibility-review` | **WCAG 2.1 AA audit** — kontrast (4.5:1), keyboard nav, focus, touch-targeti ≥44px, form labels, ARIA/screen-reader; strukturiran output (nalaz po kriteriju + severity 🔴/🟡/🟢 + prioritizirani fix) | auto / fraze ("audit accessibility", "check a11y") | — |
| `review-animations` | **QA animacija** — kritika timing/easing/treperenja/`prefers-reduced-motion`; defaultno flagga, ne tapše | **ručno** `/review-animations` | — |

**Per-komponentni tok (standard za sve build pod-faze 4.2–4.6):**
`ui-ux-pro-max` (plan) → `ui-styling` (implementacija) → `emil-design-eng` (polish) → `/review-animations` + `/code-review` (prije commita).

**Gdje koji vodi:**
- `ui-ux-pro-max` → primarno **4.1b** (seedira `MASTER.md` = izvor istine za tokene §3); feedback i u **4.2** (data-dense scannable dashboard) i **4.4** (izbor grafa za BKT — progress/heatmap, ne pie).
- `ui-styling` → **4.1c nadalje**, sve ekranske komponente.
- `emil-design-eng` → **4.6** + opći polish gamifikacijskih momenata i editor-feedback prijelaza (4.3).
- `accessibility-review` → **4.7** (sustavni WCAG AA audit cijele app), + brza provjera paleta već u **4.1b** (kontrast tokena prije nego ih komponente prošire).
- `review-animations` → **ručni gate** prije commita svake animacije (editor feedback 4.3, sav motion 4.6).

> Napomena o pokrivenosti: lanac sada pokriva **plan → gradnja → polish → a11y audit → review**. `accessibility-review` zatvara WCAG audit (prije je bio ručni axe/Lighthouse korak). Dio njegovih funkcija (čitanje iz Figme, otvaranje ticketa) traži MCP konektore kojih ovdje nema — bez njih skill i dalje radi audit nad kodom/opisom/URL-om, samo ne čita direktno iz Figme/Linear-a (vidi bundlani `CONNECTORS.md`). Za našu upotrebu (audit nad gotovim komponentama) to je dovoljno; axe/Lighthouse ostaju kao jeftina dvostruka provjera, ne kao primarni alat.

---

## 5. Pod-faze (checkpoint model: tag po checkpointu, PR po pod-fazi)

> **Radni model (netaknut):** ja (chat-Claude) pišem CC promptove + analiziram izvještaje, NE pišem produkcijski kod. Svaki CC prompt ima eksplicitne **"STANI i javi"** guardove + **"NE radi X"** scope granice. Pre-flight (READ-ONLY KORAK 0) ide gdje god postoji nepoznanica koju bi CC inače popunio pretpostavkom. **Value-add se na frontendu seli** s "assert stvarno ponašanje agenta" na **"verificiraj da ruta vraća točno ono što komponenta očekuje"** (polja/tipovi/null) + "radi li flow i izgleda li namjerno".
>
> **Frontend per-komponentni tok (build pod-faze 4.2–4.6):** moji CC promptovi eksplicitno upućuju lanac `ui-ux-pro-max` → `ui-styling` → `emil-design-eng` → `/review-animations`+`/code-review` (vidi §4). Promptovi referenciraju `design-system/MASTER.md` (iz 4.1b) kao izvor istine za tokene da UI ostane konzistentan kroz faze.

---

### 4.0 — Backend contract completion (CC teren, TDD)
**Cilj:** dovesti API do ciljne površine iz §2 PRIJE frontenda, da frontend gradi protiv konačnog ugovora.

#### 4.0a — Read endpointi + `/run` + history
- **Entry:** `main` zelen (402/1). Ugovor §2 potvrđen kao meta.
- **Deliverables:** `/task/{id}`, `/modules`, `/badges`, `/attempts` (paginirano), `/mastery-history`, `/leaderboard`, `/admin/agent-logs` (guard-stub dok auth ne legne), `POST /run`; migracija `skill_mastery_history` + KM hook (upis snapshota po updateu); nove Pydantic sheme; integ. testovi po ruti.
- **Exit (DoD):**
  - [ ] svaka nova ruta ima response_model + test koji asertira **stvaran oblik** (polja/tipovi/null), ne pretpostavljen
  - [ ] `/run` izvršava u sandboxu s istim statement_timeout zaštitama kao Evaluator, NE persistira attempt, NE dira XP/BKT
  - [ ] `skill_mastery_history` se puni pri svakom BKT updateu (provjereno testom: N attempta → N+ redova)
  - [ ] 0 regresija na postojećih 402
- **Value-add hook (gdje lovim CC):** da li `/run` slučajno ide kroz attempt-persist put (mora biti čist exec); da li `/task/{id}` izlaže `expected_query`/`expected_result` (NE SMIJE — to je rješenje, curenje kroz API); paginacija `/attempts` (assert stvaran limit/offset, ne "valjda radi"); `/leaderboard` weekly prozor (koji timezone — Europe/Zagreb, isti kao streak).
- **Tag:** `faza-4-0a-read-endpoints`

#### 4.0b — JWT auth
- **Entry:** 4.0a mergean.
- **Deliverables:** `passlib[bcrypt]` + `python-jose` u deps; `password_hash` popunjavanje/provjera; `/register` (role→`student`), `/login`, `/me`; `Depends(get_current_user)`; **migracija `/attempt` `/next-task` `/profile` `/run` `/task` na `user_id` iz tokena** (makni iz body/query); admin role-guard na `/admin/*`; seed 1 admin; `.env` JWT secret.
- **Exit (DoD):**
  - [ ] 3 postojeće rute više NE primaju `user_id` iz klijenta — vuku iz tokena (test: poziv bez tokena → 401)
  - [ ] `/admin/agent-logs` → 403 za studenta, 200 za admina
  - [ ] register→login→protected-call e2e prolazi
  - [ ] schemas.py docstring ("BEZ auth/session") ažuriran da odražava novo stanje
- **Value-add hook:** ovo je **contract change** — svaka komponenta koja bi slala `user_id` sad ga NE smije; lovim da CC ne ostavi dvostruki put (i token i body). Provjeri da timeout/error putevi (504/422) i dalje rade nakon auth gatea.
- **Tag:** `faza-4-0b-auth` · **PR: Faza 4.0**

---

### 4.1 — Frontend foundation
**Cilj:** scaffold + design sistem + app shell. Nakon ove pod-faze postoji prazna ali "lijepa i spojena" ljuska s auth flowom.

#### 4.1a — Tooling & scaffold
- **Deliverables:** `frontend/` (Vite+React+TS), Tailwind, shadcn init, ESLint+Prettier, path aliasi, `.env` (`VITE_API_URL`), **Makefile/README run-targets za frontend I backend** (riješi nedokumentirano pokretanje: `uvicorn app.main:app` + port, compose up Postgres×2+Prosody, `.env.example`).
- **Exit (DoD):** `make dev` (ili dokumentirana komanda) diže backend+frontend lokalno; prazna ruta renderira; lint/format prolazi.
- **Value-add hook:** potvrdi backend run-recept (port, .env obavezna polja — `DATABASE_URL` baca rano) da dev nije pogađanje.
- **Tag:** `faza-4-1a-scaffold`

#### 4.1b — Design system & tokeni  *(NOVO — nije bilo u 4-tjednom planu)*
- **Deliverables:** `ui-ux-pro-max --design-system --persist` → **`design-system/MASTER.md`** (paleta + font par + layout pattern za "SQL learning dashboard", izvor istine za UI kroz sve faze); iz njega → CSS varijable + Tailwind theme extend (tipografija, semantika, mastery/tier/data-viz skale, dark+light), custom Monaco tema, motion tokeni, ikona set; token-preview stranica (živi katalog boja/tipa/komponenti).
- **Exit (DoD):** `MASTER.md` postoji i usklađen sa §3; token-preview stranica pokazuje sve skale; dark/light prebacivanje radi; Monaco tema usklađena; shadcn komponente vuku tokene (ne default).
- **Value-add hook:** vizualni teren — manje "assert", više "izgleda li namjerno". Lovim da CC ne preskoči `MASTER.md` i ne improvizira boje po komponenti (mora vući iz tokena). Skill-lanac: `ui-ux-pro-max` (plan/`MASTER.md`) → `ui-styling` (token setup) → `emil-design-eng` (theming detalji).
- **Tag:** `faza-4-1b-design-system`

#### 4.1c — App shell & infra
- **Deliverables:** routing + layout (sidebar/header), **typed API klijent** (`openapi-typescript` iz `/openapi.json` + wrapper), TanStack Query provider, auth context (token storage, refresh strategija), protected routes, login/register stranice (react-hook-form+zod), toast sustav, error boundary, **state-primitivi** (skeleton/empty/error iz §3.4).
- **Exit (DoD):**
  - [ ] login/register → token → protected ruta radi e2e protiv živog backenda
  - [ ] typed klijent generiran iz backend OpenAPI; tip-mismatch puca na build-u (dokaz contract-safetyja)
  - [ ] 401 → redirect na login; logout čisti stanje
- **Value-add hook:** prva prilika da uhvatim **oblik-mismatch** — generirani tipovi vs ono što komponenta očekuje. Ako CC negdje ručno tipizira odgovor umjesto da koristi generirane tipove → STANI.
- **Tag:** `faza-4-1c-app-shell` · **PR: Faza 4.1**

---

### 4.2 — Dashboard + Module overview
**Cilj:** student vidi svoj napredak i ima jasan poziv na sljedeći zadatak.
- **Deliverables:** Dashboard (XP bar + level + streak hero, recommended-task CTA iz `/next-task`, mastery viz iz `/profile`+`/modules` join, badge highlights); Module overview (6 module cards Beginner→Expert s % savladanosti, koncept-razina mastery, locked/unlocked stanja iz prereq grafa).
- **Exit (DoD):**
  - [ ] svi podaci iz stvarnih endpointa (nula mock-a)
  - [ ] mastery skala vizualno čita low→high; locked moduli jasno označeni
  - [ ] loading→skeleton, empty (novi user bez mastery), error stanja pokrivena
- **Value-add hook:** `/profile.mastery` vraća **samo `concept` code + `p_l`** — komponenta MORA joinati s `/modules` za ime/modul. Lovim da CC ne hardkodira mapu ili ne pretpostavi da `/profile` daje ime. Locked/unlocked logika mora doći iz `prerequisites` (`/modules`), ne izmišljena.
- **Tag:** `faza-4-2-dashboard` · **PR: Faza 4.2**

---

### 4.3 — Task screen (JEZGRA)
**Cilj:** kompletna petlja: dohvati zadatak → piši SQL → Run/Submit → feedback → sljedeći. Ovo je srce eval-a.
- **Deliverables:**
  - lijevo: opis zadatka (`/task/{id}`), koncepti (čipovi, tier-obojeni), težina, **statički ER dijagram `ecommerce_v1`** (dizajnirana SVG/React komponenta, ne generička lib), sample-data preview (kroz `/run` SELECT)
  - sredina: Monaco SQL editor (custom tema, SQL config, **Cmd/Ctrl+Enter = Run, Shift+Enter = Submit**)
  - desno/dolje: rezultat tablica (`/run` ili `/attempt`), feedback render (correct/incorrect + `error_type` mapiran na ljudski tekst), XP/badge delta, "sljedeći zadatak" CTA iz `recommendation`
- **Exit (DoD):**
  - [ ] **Run** izvršava i prikazuje rezultat BEZ bodovanja; **Submit** ide na `/attempt` i prikazuje pun feedback
  - [ ] feedback razlučuje correct/incorrect iz `is_correct`+`error_type` (**partial se NE prikazuje** — ERRATA #8: nema verdict kolone; samo correct/incorrect)
  - [ ] 504 timeout → graciozno (poruka "evaluacija predugo traje, pokušaj ponovno"), ne visi spinner
  - [ ] new_badges su **kozmetika**; autoritativno stanje vuče iz `/profile` (badge-best-effort flag #3)
  - [ ] optimistic/loading stanje na Submit; editor ostaje editabilan nakon greške
- **Value-add hook:** najgušći oblik-mismatch teren. `recommendation.task_id` može biti `None` (kraj puta) — komponenta mora pokriti. `error_type` enum (`syntax_error`/`execution_error`/`timeout`/`empty_result`/`wrong_columns`/`row_mismatch`/`unsupported_eval`) → svaki ima ljudsku poruku, NE sirovi string. Lovim da CC ne pretpostavi da `/attempt` vraća redove rezultata (NE vraća — samo feedback; redovi idu kroz `/run`).
- **Tag:** `faza-4-3-task-screen` · **PR: Faza 4.3** ⭐ *(kritični checkpoint — nakon ovoga sustav je eval-upotrebljiv)*

---

### 4.4 — Profile / Stats
**Cilj:** dubina napretka — bedževi, povijest, BKT krivulje.
- **Deliverables:** badge galerija (locked+unlocked: `/badges` katalog × `/profile` earned), povijest pokušaja (`/attempts`, filtri po modulu/ishodu), **BKT P(L) krivulje kroz vrijeme** (`/mastery-history`, Recharts, po konceptu/modulu), stats sažetak (ukupno pokušaja, accuracy, vrijeme).
- **Exit (DoD):**
  - [ ] locked bedževi prikazani zatamnjeno s kriterijem; unlocked s datumom
  - [ ] krivulje renderiraju iz `skill_mastery_history` (prazno ako je user nov — empty stanje, ne crash)
  - [ ] povijest paginirana, ne učitava sve odjednom
- **Value-add hook:** krivulje ovise o D-HIST — ako 4.0a snapshot nije počeo puniti na vrijeme, novi useri nemaju podatke; empty stanje mora biti dizajnirano, ne bug. Provjeri da `/mastery-history` timestamp granularnost daje smislenu krivulju (ne 1 točka).
- **Tag:** `faza-4-4-profile` · **PR: Faza 4.4**

---

### 4.5 — Leaderboard + Admin
**Cilj:** kompetitivni sloj + alat za tebe/mentora tijekom eval-a.
- **Deliverables:** Leaderboard (global + weekly, `/leaderboard`, isticanje trenutnog usera), Admin panel (agent-log viewer `/admin/agent-logs`, filter po cid/agentu/vremenu, role-guarded; osnovne eval-statistike).
- **Exit (DoD):**
  - [ ] admin rute nedostupne studentu (UI + backend 403 oboje)
  - [ ] log viewer čitljiv (FIPA poruke formatirane, ne sirovi JSON dump)
  - [ ] weekly prozor dosljedan backend definiciji (Europe/Zagreb)
- **Value-add hook:** admin je za eval debugging — log viewer mora pokazati correlation_id flow (RECEIVE→EVALUATE→UPDATE→RECOMMEND→RESPOND) čitljivo, jer to je vrijednost za tezu. Lovim da se ne izloži ništa što student ne smije vidjeti.
- **Tag:** `faza-4-5-leaderboard-admin` · **PR: Faza 4.5**

---

### 4.6 — Motion & interaction polish
**Cilj:** gamifikacijski "feel" + glatke tranzicije + opcionalni live sloj.
- **Deliverables:** XP gain count-up, level-up celebration, badge-unlock animacija, streak flame, page transitions, hover/press mikrointerakcije, command palette (opcionalni flourish, ⌘K); **opcionalni WebSocket** live sloj (real-time XP/badge tijekom aktivne sesije — `app/api/ws.py` backend + frontend subscribe). WS je nadogradnja na REST jezgru, ne zamjena.
- **Exit (DoD):**
  - [ ] sve animacije poštuju `prefers-reduced-motion`
  - [ ] motion vuče iz tokena (§3.3), dosljedan
  - [ ] **svaka animacija prošla `/review-animations`** (timing/easing/treperenje) — ručni gate, ne preskače se
  - [ ] (ako WS) fallback na REST ako konekcija padne — nikad slomljen flow
- **Value-add hook:** polish ne smije slomiti jezgru; WS je čisti add-on (REST i dalje radi sam). Ovo je prva pod-faza koja se reže ako rok pritisne. Skill-lanac: `emil-design-eng` (gradnja motiona) → `/review-animations` (QA).
- **Tag:** `faza-4-6-motion-polish` · **PR: Faza 4.6**

---

### 4.7 — Visual QA · a11y · responsive · hardening  *(NOVO — nije bilo u 4-tjednom planu)*
**Cilj:** finalni prolaz koji pretvara "radi" u "izpolirano".
- **Deliverables:** audit svih empty/loading/error stanja kroz app, responsive breakpointi (desktop primaran, tablet upotrebljiv), **WCAG 2.1 AA pass kroz `accessibility-review` skill** (strukturiran nalaz po kriteriju + severity → prioritizirani popravci; kontrast, fokus, tipkovnica, touch-targeti, ARIA, reduced-motion), cross-browser smoke, performance (lazy-load route, Monaco code-split), finalni vizualni polish (razmaci, poravnanja, dosljednost tokena), happy-path e2e (Playwright) za student flow.
- **Exit (DoD):**
  - [ ] `accessibility-review` pokrenut nad svim glavnim ekranima; svi 🔴 nalazi popravljeni, 🟡 svjesno odlučeni
  - [ ] axe/Lighthouse kao dvostruka provjera — zelено
  - [ ] nijedan ekran nema neobrađeno error/empty stanje
  - [ ] student-flow e2e zelen (login→task→submit→feedback→next)
  - [ ] Lighthouse/bundle u razumnim granicama
- **Value-add hook:** sustavni "gdje izgleda nedovršeno" pregled; ovo je gdje frontend prelazi prag "nadograđen i savršen".
- **Tag:** `faza-4-7-visual-qa` · **PR: Faza 4.7** · **tag `faza-4-complete`**

---

## 6. Definition of Done — Faza 4 (cijela)

- [ ] Student se registrira/logira, riješi zadatak (Run→Submit), vidi feedback i napredak — end-to-end protiv živog backenda
- [ ] Dashboard, Module overview, Task screen, Profile, Leaderboard, Admin svi rade s realnim podacima (nula mock-a)
- [ ] Svi tipovi odgovora generirani iz backend OpenAPI (contract-safe)
- [ ] Dizajn dosljedan kroz token-sistem; dark+light; Monaco usklađen
- [ ] a11y AA; sva data-stanja (loading/empty/error/success) dizajnirana
- [ ] Auth gate na svim zaštićenim rutama; admin razdvojen
- [ ] `skill_mastery_history` se puni → BKT krivulje imaju izvor za eval
- [ ] 0 regresija na backend suite; happy-path e2e zelen
- [ ] **Eval-spreman PRIJE 4.6/4.7** (jezgra 4.0–4.4 dovršena i upotrebljiva)

---

## 7. Tagovi (checkpoint trag)

```
faza-4-0a-read-endpoints
faza-4-0b-auth
faza-4-1a-scaffold
faza-4-1b-design-system
faza-4-1c-app-shell
faza-4-2-dashboard
faza-4-3-task-screen        ⭐ eval-upotrebljivo
faza-4-4-profile
faza-4-5-leaderboard-admin
faza-4-6-motion-polish
faza-4-7-visual-qa
faza-4-complete
```

PR po pod-fazi (4.0 / 4.1 / 4.2 / 4.3 / 4.4 / 4.5 / 4.6 / 4.7).

---

## 8. Otvoreni dug iz backenda koji dira frontend (errata-trail)

| # | Stavka | Utjecaj na Fazu 4 |
|---|---|---|
| ERRATA #8 | `attempts` nema `verdict` kolonu | Partial se NE razlučuje u UI — prikazuje samo correct/incorrect (4.3). Partial = buduća migracija. |
| flag #3 | `new_badges` best-effort (`user_badges` nema `attempt_id`) | Badge-unlock je kozmetika; autoritativno stanje iz `/profile` (4.3/4.4). |
| flag #5 | F2 mentor-pending XP konstante (TODO(mentor)) | Ne blokira frontend (struktura radi). **Pingaj mentora paralelno.** |
| NALAZ #7 | `task.module_id ≠ primary_concept.module` za 3/83 | Module overview mapiranje (4.2) — moguć rubni slučaj; data cleanup Faza 6. |

---

## 9. Sljedeći korak

1. **4.0a CC prompt** (read endpointi + `/run` + `skill_mastery_history`, TDD, READ-ONLY pre-flight gdje treba, "STANI i javi" guardovi + scope granice).
2. Zatim **4.0b auth prompt** (zaseban — dira postojeći ugovor).
3. Paralelno: **ping mentoru** za F2 XP konstante (ne blokira).
4. Pa redom 4.1a → 4.7 po checkpoint modelu.
