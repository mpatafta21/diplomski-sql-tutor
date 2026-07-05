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
→ backend (uvicorn `:8000`) + frontend (Vite `:5173`) zajedno.

### Ručno (isti redoslijed)
```bash
make infra-up      # docker compose up -d  (postgres-main, postgres-sandbox, prosody)
make wait-db       # čeka pg_isready (compose nema healthcheck → izbjegava race)
make db-migrate    # cd backend && uv run alembic upgrade head
make db-seed       # cd backend && uv run python -m app.db.seed
make backend       # uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
make frontend      # (u drugom terminalu) cd frontend && npm run dev
```

> **XMPP napomena:** SPADE agenti se spajaju na Prosody **na startupu** (on-startup, ne lazy) —
> Prosody mora biti gore **prije** `make backend`, inače uvicorn lifespan padne. `make infra-up`
> ga diže zajedno s bazama.

Backend API: `http://localhost:8000` (`/openapi.json`, `/docs`). Frontend: `http://localhost:5173`.

## Struktura

Vidi `docs/` za detalje.
