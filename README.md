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
Diže: Postgres×2 + Prosody → čeka DB → `alembic upgrade head` → seed (moduli/koncepti/bedževi + admin)
→ **`make sweep` (gate)** → backend (uvicorn `:8000`) + frontend (Vite `:5173`) zajedno.

**Prvi boot** (jednokratno, prije prvog `make dev` — puni task bank i sandbox podatke):
```bash
make db-tasks      # import 83 taska iz data/generated_tasks/final_dataset.json
make sandbox-seed  # deterministički Faker seed sandbox podataka
```

### Ručno (isti redoslijed)
```bash
make infra-up      # docker compose up -d  (postgres-main, postgres-sandbox, prosody)
make wait-db       # čeka pg_isready (compose nema healthcheck → izbjegava race)
make db-migrate    # cd backend && uv run alembic upgrade head
make db-seed       # cd backend && uv run python -m app.db.seed
make db-tasks      # (prvi boot) import taskova iz final_dataset.json
make sandbox-seed  # (prvi boot) deterministički seed sandbox podataka
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
u `make dev` da se to ne može ponoviti tiho. **Ne pokreći evaluacijsku sesiju dok sweep nije zelen.**

## Struktura

Vidi `docs/` za detalje.
