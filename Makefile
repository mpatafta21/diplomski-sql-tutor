# SQL Tutor — dev run-targeti (Faza 4.1a)
#
# Redoslijed za čist boot: infra-up → wait-db → db-migrate → db-seed → (backend + frontend).
# `make dev` lanča sve gore jednom komandom.
#
# Preduvjeti:
#   - Docker + docker compose v2
#   - uv (Python), Node >= 20 + npm (WSL-native, ne /mnt/c interop)
#   - backend/.env  (obavezno: DATABASE_URL, JWT_SECRET)  — vidi backend/.env.example
#   - frontend/.env (VITE_API_URL)                        — vidi frontend/.env.example

# DB kredencijali izvedeni iz docker-compose.yml (postgres-main: POSTGRES_USER=tutor)
PG_MAIN_SERVICE := postgres-main
PG_MAIN_USER := tutor

.PHONY: dev infra-up infra-down wait-db db-migrate db-seed db-tasks sandbox-seed sweep backend frontend frontend-install openapi-snapshot help

help:
	@echo "Targeti:"
	@echo "  make infra-up    - digni Postgres x2 + Prosody (docker compose, detached)"
	@echo "  make wait-db     - čekaj da postgres-main bude spreman (nema healthchecka)"
	@echo "  make db-migrate  - alembic upgrade head"
	@echo "  make db-seed     - seed moduli/koncepti/bedževi + admin (idempotentno)"
	@echo "  make db-tasks    - import 83 taska iz final_dataset.json (prvi boot)"
	@echo "  make sandbox-seed - deterministički seed sandbox podataka (prvi boot)"
	@echo "  make sweep       - GATE: referentni upit svakog taska mora proći"
	@echo "  make backend     - uvicorn gateway na :8000 (--reload)"
	@echo "  make frontend    - Vite dev server na :5173"
	@echo "  make dev             - sve gore: infra → wait → migrate → seed → SWEEP → backend+frontend"
	@echo "  make infra-down      - zaustavi docker servise"
	@echo "  make openapi-snapshot - regeneriraj frontend/openapi.json iz app.openapi() (bez servera)"

# OpenAPI snapshot za typed frontend klijent (openapi-typescript).
# app.openapi() gradi spec iz app objekta BEZ servera/infra/agenata (KORAK 0 W).
# Regeneriraj kad se backend ugovor promijeni → frontend/openapi.json je diff-vidljiv u PR-u.
openapi-snapshot:
	cd backend && uv run python -c "import json,sys; from app.main import app; json.dump(app.openapi(), sys.stdout)" > ../frontend/openapi.json
	@echo "frontend/openapi.json regeneriran."

# Prvi boot (jednokratno, NIJE u `dev` lancu jer su skupi i destruktivni za sandbox):
#   make db-tasks && make sandbox-seed
db-tasks:
	cd backend && uv run python -m scripts.import_dataset

sandbox-seed:
	cd backend && uv run python -m scripts.seed_sandbox

# 🔴 SWEEP = OBAVEZAN GATE PRIJE EVALUACIJSKE SESIJE (Faza 4.4-0e).
# Pušta `expected_query` svakog AKTIVNOG taska kroz istu evaluacijsku jezgru
# kojom ide studentov upit i tvrdi da referenca reproducira `expected_result`.
# Ne-nul exit ako ijedan padne ILI ako postoji ijedan perzistiran attempt s
# error_type='unsupported_eval' (BKT zagađenje) ILI ako task bank nije seedan.
# Zašto gate: 4.4-0c je pokazao 11/83 neocjenjivih taskova koje nitko nije
# primijetio jer ih ništa nije provjeravalo.
sweep:
	cd backend && uv run python -m scripts.sweep_task_integrity

infra-up:
	docker compose up -d

infra-down:
	docker compose down

# docker-compose NEMA healthcheck → čekamo pg_isready prije migracija (izbjegava race).
wait-db:
	@echo "Čekam postgres-main ($(PG_MAIN_USER))..."
	@until docker compose exec -T $(PG_MAIN_SERVICE) pg_isready -U $(PG_MAIN_USER) >/dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "postgres-main spreman."

db-migrate:
	cd backend && uv run alembic upgrade head

db-seed:
	cd backend && uv run python -m app.db.seed

backend:
	cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend-install:
	cd frontend && npm install

frontend:
	cd frontend && npm run dev

# Puni dev boot: infra + čekanje + migracije + seed, pa backend i frontend zajedno.
# XMPP napomena: agenti se spajaju na Prosody NA STARTUPU (on-startup, ne lazy) →
# Prosody mora biti gore prije `make backend` (infra-up ga diže).
dev: infra-up wait-db db-migrate db-seed sweep
	@trap 'kill 0' SIGINT; \
	(cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) & \
	(cd frontend && npm run dev) & \
	wait
