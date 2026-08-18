# Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju

Diplomski rad — FOI, smjer Baze podataka i baze znanja.

---

## O čemu se radi

Web-aplikacija u kojoj student uči SQL rješavanjem zadataka nad stvarnom bazom, a
sustav mu **sam bira sljedeći zadatak** na temelju procjene onoga što već zna.

Student u pregledniku dobiva zadatak („izlistaj kupce iz Hrvatske"), piše upit u SQL
editoru i predaje ga. Upit se **stvarno izvršava** nad izoliranom PostgreSQL bazom, uspoređuje
s referentnim rješenjem i dobiva ocjenu s objašnjenjem — ne samo „točno/netočno" nego i
**kakva je greška** (krivi stupci, prazan rezultat, redci u krivom poretku, upit koji ne
koristi indeks…). Iz tog ishoda sustav osvježi procjenu znanja za svaki koncept koji je
zadatak dodirnuo i preporuči sljedeći korak.

### Što ga čini „inteligentnim"

Odluku o sljedećem zadatku donosi **hibridni model — simbolički i vjerojatnosni zajedno**:

| sloj | čime | što odlučuje |
|---|---|---|
| **Simbolički** | Prolog ontologija (`backend/prolog/`) | koji su koncepti **preduvjet** kojima — `inner_join` se ne nudi prije `join_condition` |
| **Vjerojatnosni** | Bayesian Knowledge Tracing | kolika je vjerojatnost `P(L)` da student **već zna** pojedini koncept |

Prolog je autoritativan za strukturu gradiva, BKT za stanje znanja. Preporuka je presjek:
koncept koji je **otključan** (preduvjeti zadovoljeni) i **najslabiji** (najniži `P(L)`).

### Zašto agenti

Sustav nije jedan monolit nego **šest SPADE agenata** koji razmjenjuju FIPA-ACL poruke:

| agent | zadaća |
|---|---|
| **EvaluatorAgent** | izvrši upit u sandboxu, usporedi s očekivanim, klasificira grešku |
| **KnowledgeModelAgent** | BKT ažuriranje `P(L)` po svakom konceptu zadatka |
| **RecommenderAgent** | Prolog + BKT → sljedeći zadatak i obrazloženje |
| **GamificationAgent** | XP, level, streak, bedževi |
| **CoordinatorAgent** | orkestracija toka predaje (FSM), API gateway |
| **HintAgent** | savjet nakon netočne predaje — LLM ili katalog |

Svaka poruka između njih je zabilježena i vidljiva u administratorskom pregledu, pa se
**cijeli put jedne predaje može rekonstruirati** — to je i predmet rada, ne samo implementacija.

### Cilj rada

Pokazati da se **adaptivno sekvenciranje gradiva** može izvesti spojem simboličkog i
vjerojatnosnog modela u višeagentskoj arhitekturi, i **izmjeriti gdje takav pristup puca**.

Rad zato ne tvrdi da sustav radi — tvrdi **što je izmjereno**. Svi nalazi, uključujući one
koji pokazuju granice pristupa, vode se u [`docs/errata.md`](docs/errata.md) (#7–#84) i
razvrstani su po poglavljima rada u [`docs/mapa-nalaza.md`](docs/mapa-nalaza.md). Primjeri
granica koje su izmjerene, a ne pretpostavljene:

- **rezultatska evaluacija ne razlikuje ekvivalentne formulacije** — 20 od 30 koncepata
  ima zaobilaznu formulaciju koja daje iste retke bez upotrebe koncepta (#29);
- **koncepti se „savladaju" prije nego ih sustav počne poučavati**, jer BKT raste i od
  zadataka u kojima je koncept sporedan (#35);
- **savjet promašuje kad mu dijagnoza nije jednoznačna** — 0 od 2 pogotka na `row_mismatch` (#80).

### Sadržaj i opseg

**88 aktivnih zadataka** (od 92 ukupno) · **30 koncepata** · **7 modula** · **5 bedževa**

| modul | tema |
|---|---|
| 1 | Osnove SELECT-a — `SELECT`, `FROM`, `WHERE`, `ORDER BY`, `LIMIT`, `DISTINCT` |
| 2 | Agregacije i grupiranje — `GROUP BY`, `HAVING`, `COUNT`, `SUM`/`AVG`, `MIN`/`MAX` |
| 3 | JOIN-ovi — `INNER`, `LEFT`, `RIGHT`, `FULL OUTER`, `CROSS`, `SELF`, 3+ tablica |
| 4 | DML operacije — `INSERT`, `UPDATE`, `DELETE` |
| 5 | Podupiti — skalarni, `IN`, `EXISTS`, korelirani |
| 6 | Optimizacija — čitanje `EXPLAIN` plana, korištenje indeksa |
| 0 | Transverzalni — `NULL` handling, aliasi, uvjet spajanja (protežu se kroz sve module) |

---

## Kako se pokreće

### Preduvjeti

- Docker + `docker compose` (v2)
- [uv](https://docs.astral.sh/uv/) (Python 3.11)
- Node **≥ 20** + npm (WSL-native, **ne** Windows npm preko `/mnt/c` interopa)

### Konfiguracija

- `backend/.env` — kopiraj iz `backend/.env.example`. **Obavezno:** `DATABASE_URL`, `JWT_SECRET`
  (oba bacaju ranu grešku ako nedostaju). Ostalo ima defaulte.
- `frontend/.env` — kopiraj iz `frontend/.env.example` (`VITE_API_URL=http://localhost:8000`).
- **LLM savjeti** (opcionalno): `USE_LLM_HINTS=true` + `ANTHROPIC_API_KEY`. Bez toga sustav
  radi normalno — gumb za savjet se jednostavno ne prikazuje.

### Jednom komandom

```bash
make dev
```

Diže: Postgres×2 + Prosody → čeka DB → `alembic upgrade head` → seed (moduli/koncepti/bedževi
+ admin) → import zadataka → seed sandboxa (samo ako je prazan) → registracija SPADE agenata
u Prosody → **`make sweep` (gate)** → backend (uvicorn `:8000`) + frontend (Vite `:5173`).

Otvori **`http://localhost:5173`**.

**`make dev` radi FROM SCRATCH** — nakon `docker compose down -v` ne treba nijedna ručna
komanda (NALAZ #26).

> **🔴 `--workers 1` je invarijanta, ne postavka.** Agenti postoje **jednom po procesu**;
> drugi uvicorn radnik prijavio bi se na Prosody istim JID-om i odgovori bi se tiho gubili.
> V. [`docs/invarijante.md`](docs/invarijante.md#jedan-uvicorn-radnik).

### Ručno (isti redoslijed)

```bash
make infra-up      # docker compose up -d  (postgres-main, postgres-sandbox, prosody)
make wait-db       # čeka pg_isready (compose nema healthcheck → izbjegava race)
make db-migrate    # alembic upgrade head
make db-seed       # moduli, koncepti, bedževi, admin
make db-tasks      # import zadataka iz final_dataset.json (idempotentan upsert)
make sandbox-seed-if-empty  # deterministički seed sandboxa ako je prazan
make register-agents        # SPADE računi u Prosody (idempotentno)
make sweep                  # GATE — v. niže
make backend                # uvicorn :8000
make frontend               # (u drugom terminalu) Vite :5173
```

> **XMPP napomena:** SPADE agenti se spajaju na Prosody **na startupu** — Prosody mora biti
> gore **prije** `make backend`, inače uvicorn lifespan padne. `make infra-up` ga diže.

Backend API: `http://localhost:8000` (`/docs`, `/openapi.json`). Frontend: `http://localhost:5173`.

---

## Kako se koristi

### Studentov put

1. **Registracija** (`/register`) — korisničko ime, e-adresa, lozinka.
   🔴 Prijava ide **po korisničkom imenu**, ne po e-adresi. Korisničko ime je vidljivo
   drugima na ljestvici.
2. **Dashboard** (`/`) — XP, level, streak i kartica **„Nastavi ovdje"** s preporučenim
   zadatkom i **obrazloženjem zašto baš taj**.
3. **Zadatak** (`/task`) — sustav razriješi preporuku i otvori zadatak:
   - lijevo: opis, koncepti koje vježba, **shema sandbox baze** (klik na tablicu → stupci),
   - desno: **Monaco SQL editor**.

   | akcija | kratica | što radi |
   |---|---|---|
   | **Run** | `Ctrl`+`Enter` | izvrši upit i pokaže rezultat — **ne boduje se** |
   | **Submit** | `Shift`+`Enter` | predaja: ocjena, XP, BKT ažuriranje, nova preporuka |
   | **Zatraži hint** | — | savjet; dostupan **tek nakon netočne predaje** |

4. **Povratna sprega** — tri stanja, razlučena ikonom i tekstom, ne samo bojom:
   **Točno** · **Djelomično** (stupci točni, redci nisu — nosi pola XP-a) · **Netočno**.
   Uz ocjenu ide obrazloženje greške i gumb **„Sljedeći zadatak"** s novom preporukom.
5. **Moduli** (`/modules`) — cijelo gradivo, po modulima i konceptima. Zaključani koncepti
   pokazuju **što im nedostaje**. Klik na koncept otvara njegov sljedeći neriješen zadatak —
   to je put kojim se bira samostalno, umjesto da se prati preporuka.
6. **Profil** (`/profile`) — bedževi, statistika, povijest pokušaja i **BKT krivulje**:
   po jedan mini-graf za svaki koncept, s vidljivim pragom ovladanosti.
7. **Ljestvica** (`/leaderboard`) — globalno ili zadnjih 7 dana.

### Savjeti (hintovi)

- Otključavaju se **tek nakon netočne predaje** — savjet bez pokušaja nema što dijagnosticirati.
- Limit **5**, dopuna **+1 svaka 4 sata**. Brojač stoji uz gumb.
- Dva izvora, ovisno o tome određuje li vrsta greške dijagnozu jednoznačno:
  **`llm`** (model, uz opis greške — nikad studentov upit) ili **`fallback`** (pripremljeni
  katalog). Pravilo i razlog: ERRATA #72.

### Igrifikacija

`XP = baza(težina) × faktor(verdikt) × bonus(redni pokušaj)`

- baza **10–50** po težini 1–5 · verdikt **1,0** točno / **0,5** djelomično
- bonus **×2,0** iz prve, **×1,5** iz druge, **×1,0** od treće — opada **na** bazu, ne ispod nje
- **Level = 1 + XP/100**

Ponovno rješavanje već riješenog zadatka **ne nosi XP** (NALAZ #41), ali i dalje diže BKT.
Pet bedževa: `first_correct`, `join_master`, `null_ninja`, `explorer`, `streak_7`.

### Administratorski pregled

`/admin` (samo `role=admin`) — **FIPA tok agenata** po `correlation_id`: cijeli put jedne
predaje, poruka po poruku. V. napomenu o osobnim podacima niže.

---

## Stanje projekta

**Sustav je dovršen** — slijedi pisanje rada. Oznaka stanja: tag **`pred-pisanje`**.

- 930 testova (`pytest`) · 5 e2e scenarija (Playwright) · `make preflight` zelen
- **kompletan prolaz kroz sučelje: 88/88 zadataka**, 130 predaja — galerija, podaci i analiza
  u [`docs/e2e-kompletan-prolaz-wrapup.md`](docs/e2e-kompletan-prolaz-wrapup.md)
- nalazi #7–#84 u [`docs/errata.md`](docs/errata.md), razvrstani u
  [`docs/mapa-nalaza.md`](docs/mapa-nalaza.md)

### Ponavljanje kompletnog prolaza

```bash
cd backend && uv run python ../scripts/prolaz/1_kandidati.py   # mutacije + verifikacija
python3 scripts/prolaz/2_plan.py                                # plan (60/30/10)
cd frontend && npm run e2e:prolaz                               # prolaz kroz sučelje
python3 scripts/prolaz/3_izvoz.py                               # CSV-ovi
```

🔴 Prolaz **piše u živu bazu i ne vraća je na baseline** — podaci ostaju kao materijal za rad.
Prije pokretanja obavezno `make backup`.

---

## Gateovi i procedure

> **🔴 Task bank je VERZIONIRAN ARTEFAKT RADA.** `data/generated_tasks/final_dataset.json`
> jedini je izvor koji `scripts/import_dataset.py` čita i **nalazi se pod verzijom** — repo
> sam po sebi rekonstruira eval-spreman sustav. LLM međukoraci ostaju gitignorirani.
> **Ne regenerirati dataset kroz LLM bez izričite odluke** — zadaci su ručno validirani i
> njihovi `expected_result` zapisi vezani su uz deterministički sandbox seed (NALAZ #20).

### 🔴 `make sweep` — obavezan gate

```bash
make sweep
```

Pušta `expected_query` **svakog aktivnog zadatka** kroz **istu evaluacijsku jezgru** kojom ide
studentov upit i tvrdi da referentni upit reproducira vlastiti `expected_result`. Ne-nul izlaz ako:

- ijedan referentni upit ne reproducira `expected_result` (pokvaren/zastario zadatak),
- postoji ijedan perzistiran pokušaj s `error_type='unsupported_eval'` (BKT zagađenje),
- task bank nije seedan (0 aktivnih zadataka).

**Zašto gate:** Faza 4.4-0c otkrila je **11 od 83** neocjenjiva zadatka koje nitko nije
primijetio jer ih ništa nije provjeravalo. Sweep je ugrađen u `make dev` da se to ne ponovi tiho.

### 🔴 `make preflight` — prije evaluacijske sesije

```bash
make preflight    # = sweep + smoke   (backend mora vrtjeti)
```

`sweep` zove evaluacijsku jezgru **izravno** i zaobilazi HTTP gateway, XMPP, Coordinator FSM i
agente — pa ostaje zelen **i kad `/attempt` pada**. `smoke` pokriva točno tu rupu: jedan pravi
`POST /attempt` kroz cijeli lanac.

**Ne pokreći evaluacijsku sesiju dok `make preflight` nije zelen.**

### 🔴 `make backup` — poslije svake evaluacijske sesije

```bash
make backup
```

Evaluacijski podaci nastaju **jednom** i **nenadoknadivi su** (NALAZ #37). Skripta ne staje na
dumpu: vrati ga u privremenu bazu, usporedi broj redaka po tablici i agregat pokušaja s izvorom,
pa je obriše. **Backup koji nije testiran nije backup.**

🔴 Dump se **mora kopirati na drugi medij**; `backups/` je u `.gitignore` (dumpovi sadrže
e-adrese i hasheve lozinki), dakle git ih ne čuva. Laptop je jedna točka kvara.

### 🔴 `docker compose down -v` je zabranjen tijekom evaluacije

`-v` briše volumene = sve pokušaje, BKT povijest i XP sudionika. Nijedan `make` target ne poziva
`down -v` implicitno (`make infra-down` je bez `-v`); jedini koji ga poziva je **`make dev-reset`**,
i to tek nakon što ispiše što se gubi i traži da doslovno upišeš `OBRISI SVE`.

Cjelovit postupak za dan evaluacije: [`docs/eval-runbook.md`](docs/eval-runbook.md).

---

## 🔴 Osobni podaci u agentskim logovima (prije evaluacije pročitati)

Administratorski pregled (`/admin`) prikazuje `agent_messages_log` — FIPA promet između agenata.
**Ti zapisi sadrže `submitted_query`: doslovan SQL koji je student napisao**, povezan s
`user_id`-em, a ljestvica i profil povezuju `user_id` s korisničkim imenom.

Što je provjereno (sken svih 552 zapisa, Faza 4.5 KORAK 0):

- ❌ **NEMA** `expected_query` ni očekivanih redaka → rješenja zadataka nisu izložena
- ❌ **NEMA** lozinki, hasheva (`$2b$`), tokena ni e-adresa
- ✅ jedini osjetljiv sadržaj je **studentov vlastiti upit**

**To nije sigurnosni propust, ali JEST obrada osobnih podataka.** Prije evaluacije:

1. sudionici moraju biti obaviješteni da se njihovi upiti bilježe i pregledavaju,
2. to mora biti pokriveno **suglasnošću sudionika**,
3. u radu se podaci prikazuju **agregirano ili anonimizirano**, ne s korisničkim imenima.

Količina: **12 zapisa po predanom zadatku**, `limit` je server-side capiran na **200**
(NALAZ #36) — cjelovit pregled ide isključivo filtriranjem po `correlation_id`.

🔴 Uz to: `agent_messages_log` **nema `user_id`**, pa se podaci pojedinog sudionika **ne mogu
obrisati po osobi** — jedini put je `TRUNCATE` cijele tablice (ERRATA #46, odluka: ne gradi se).

---

## Struktura repozitorija

```
backend/
  app/        FastAPI (rute, sheme, DB modeli, migracije)
  agents/     SPADE agenti + evaluacijska jezgra
  bkt/        Bayesian Knowledge Tracing
  prolog/     ontologija koncepata i pravila preporuke
  scripts/    import, seed, sweep, smoke, backup, validacija zadataka
  tests/      930 testova
frontend/
  src/        React + TS (stranice, komponente, API klijent)
  e2e/        Playwright — ulazni gate (4 scenarija)
  e2e-prolaz/ Playwright — kompletan prolaz kroz 88 zadataka
docker/       Postgres ×2 + Prosody (XMPP)
scripts/      backup, a11y matrica, priprema i izvoz prolaza
docs/         dokumentacija faza, errata, invarijante, galerija, podaci prolaza
```

Ključni dokumenti: [`docs/errata.md`](docs/errata.md) (nalazi) ·
[`docs/invarijante.md`](docs/invarijante.md) (pravila koja se ne krše) ·
[`docs/mapa-nalaza.md`](docs/mapa-nalaza.md) (nalaz → poglavlje rada) ·
[`docs/eval-runbook.md`](docs/eval-runbook.md) (dan evaluacije).
