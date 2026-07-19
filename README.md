# Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju

Diplomski rad — FOI, smjer Baze podataka i baze znanja.

## Tech stack

- **Backend**: Python 3.11, FastAPI, SPADE, pyswip, PostgreSQL 16
- **Frontend**: React 18 + TypeScript, Vite, Tailwind, shadcn/ui
- **Agenti**: 5 SPADE agenata (Evaluator, KnowledgeModel, Recommender, Gamification, Coordinator) + opcionalni HintAgent
- **AI**: Prolog (ontologija) + Bayesian Knowledge Tracing (vjerojatnosni model)

## Status

🚧 U razvoju — Faza 4.1 (frontend foundation). Backend contract je zaključan (Faza 4.0).

## Lokalno pokretanje (dev)

### Preduvjeti
- Docker + `docker compose` (v2)
- [uv](https://docs.astral.sh/uv/) (Python 3.11)
- Node **≥ 20** + npm (WSL-native, **ne** Windows npm preko `/mnt/c` interopa)

### Env
- `backend/.env` — kopiraj iz `backend/.env.example`. **Obavezno:** `DATABASE_URL`, `JWT_SECRET`
  (oba bacaju ranu grešku ako nedostaju). Ostalo ima defaulte.
- `frontend/.env` — kopiraj iz `frontend/.env.example` (`VITE_API_URL=http://localhost:8000`).

### Jednom komandom
```bash
make dev
```
Diže: Postgres×2 + Prosody → čeka DB → `alembic upgrade head` → seed (moduli/koncepti/bedževi
+ admin) → **import taskova** → **seed sandboxa (samo ako je prazan)** → **registracija SPADE
agenata u Prosody** → **`make sweep` (gate)** → backend (uvicorn `:8000`) + frontend (Vite `:5173`).

**Od Faze 4.4-0g `make dev` radi FROM SCRATCH** — nakon `docker compose down -v` ne treba
nijedna ručna komanda. (Prije toga su nedostajali import taskova, seed sandboxa i registracija
agenata, pa je backend pucao na svježem Prosody volumenu.)

> **🔴 Task bank je VERZIONIRAN ARTEFAKT RADA.** `data/generated_tasks/final_dataset.json`
> (**85 zadataka**, `version: 2b-3+4.4-0h`) jedini je izvor koji `scripts/import_dataset.py` čita i
> **nalazi se pod verzijom** — repo sam po sebi rekonstruira eval-spreman sustav.
> LLM međukoraci (`pilot/`, `failed/`, `validated/`, `raw/`, batch reporti) ostaju
> gitignorirani jer su velike, nereproducibilne sirovine.
> **Ne regenerirati dataset kroz LLM bez izričite odluke** — zadaci su ručno validirani
> i njihovi `expected_result` zapisi vezani su uz deterministički sandbox seed (NALAZ #20).

### Ručno (isti redoslijed)
```bash
make infra-up      # docker compose up -d  (postgres-main, postgres-sandbox, prosody)
make wait-db       # čeka pg_isready (compose nema healthcheck → izbjegava race)
make db-migrate    # cd backend && uv run alembic upgrade head
make db-seed       # cd backend && uv run python -m app.db.seed
make db-tasks      # import taskova iz final_dataset.json (idempotentan upsert)
make sandbox-seed-if-empty  # deterministički seed sandboxa ako je prazan
make register-agents        # SPADE računi u Prosody (idempotentno)
make sweep         # GATE — vidi dolje
make backend       # uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
make frontend      # (u drugom terminalu) cd frontend && npm run dev
```

> **XMPP napomena:** SPADE agenti se spajaju na Prosody **na startupu** (on-startup, ne lazy) —
> Prosody mora biti gore **prije** `make backend`, inače uvicorn lifespan padne. `make infra-up`
> ga diže zajedno s bazama.

Backend API: `http://localhost:8000` (`/openapi.json`, `/docs`). Frontend: `http://localhost:5173`.

### 🔴 `make sweep` — OBAVEZAN gate prije evaluacijske sesije

```bash
make sweep    # cd backend && uv run python -m scripts.sweep_task_integrity
```

Pušta `expected_query` **svakog aktivnog taska** kroz **istu evaluacijsku jezgru** kojom ide
studentov upit i tvrdi da referentni upit reproducira vlastiti `expected_result`.
Izlazi s **ne-nul kodom** ako:

- ijedan referentni upit ne reproducira `expected_result` (pokvaren/zastario task),
- postoji ijedan perzistiran attempt s `error_type='unsupported_eval'` (BKT zagađenje —
  0 XP + kazna, curi i na evaluabilne sekundarne koncepte),
- task bank nije seedan (0 aktivnih taskova).

**Zašto gate:** Faza 4.4-0c otkrila je **11 od 83** neocjenjivih taskova koje nitko nije
primijetio jer ih ništa nije provjeravalo (9 DML + 2 datumski zastarjela). Sweep je ugrađen
u `make dev` da se to ne može ponoviti tiho.

### 🔴 `make preflight` — pokreni PRIJE evaluacijske sesije

```bash
make preflight    # = make sweep + make smoke   (backend mora vrtjeti)
```

`make sweep` zove evaluacijsku jezgru **izravno** i time zaobilazi HTTP gateway, AgentBridge,
XMPP/Prosody, Coordinator FSM i agente — pa ostaje **zelen i kad `/attempt` pada** (npr.
neregistrirani XMPP računi). `make smoke` pokriva točno tu rupu: jedan pravi `POST /attempt`
kroz cijeli lanac mora dati `is_correct=true`. Smoke sam čisti svog `demo44_smoke` usera.

**Ne pokreći evaluacijsku sesiju dok `make preflight` nije zelen.**

## 🔴 Osobni podaci u agentskim logovima (prije evaluacije pročitati)

Administratorski pregled (`/admin`, samo `role=admin`) prikazuje tablicu
`agent_messages_log` — FIPA promet između agenata. **Ti zapisi sadrže
`submitted_query`: doslovan SQL koji je student napisao**, povezan s
`user_id`-em, a ljestvica i profil povezuju `user_id` s `username`-om.

Što je provjereno (sken **svih 552 zapisa**, Faza 4.5 KORAK 0):

- ❌ **NEMA** `expected_query` ni očekivanih redaka → rješenja zadataka nisu izložena
- ❌ **NEMA** lozinki, hasheva (`$2b$`), tokena ni e-mail adresa
- ✅ jedini osjetljiv sadržaj je **studentov vlastiti upit**

**To nije sigurnosni propust, ali JEST obrada osobnih podataka.** Studentovi
pokušaji (uključujući pogrešne) vidljivi su administratoru i vežu se uz
korisničko ime. Prije evaluacije:

1. sudionici moraju biti obaviješteni da se njihovi upiti bilježe i pregledavaju,
2. to mora biti pokriveno **suglasnošću sudionika**,
3. u radu se podaci prikazuju **agregirano ili anonimizirano**, ne s
   korisničkim imenima.

Napomena o količini: **12 zapisa po predanom zadatku**, a `limit` je server-side
capiran na **200** (NALAZ #36) — cjelovit pregled ide isključivo filtriranjem po
`correlation_id`.

## Struktura

Vidi `docs/` za detalje.
