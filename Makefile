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
PG_SANDBOX_SERVICE := postgres-sandbox
PG_SANDBOX_USER := sandbox_admin
PG_SANDBOX_PASS := sandbox_dev_password

.PHONY: dev infra-up infra-down wait-db db-migrate db-seed db-tasks sandbox-seed sandbox-seed-if-empty register-agents sweep smoke preflight backend frontend frontend-install openapi-snapshot backup dev-reset help

help:
	@echo "Targeti:"
	@echo "  make infra-up    - digni Postgres x2 + Prosody (docker compose, detached)"
	@echo "  make wait-db     - čekaj da postgres-main bude spreman (nema healthchecka)"
	@echo "  make db-migrate  - alembic upgrade head"
	@echo "  make db-seed     - seed moduli/koncepti/bedževi + admin (idempotentno)"
	@echo "  make db-tasks    - import 83 taska iz final_dataset.json (prvi boot)"
	@echo "  make sandbox-seed - deterministički seed sandbox podataka (prvi boot)"
	@echo "  make register-agents - registriraj SPADE agente u Prosody (idempotentno)"
	@echo "  make sweep       - GATE: referentni upit svakog taska mora proći (offline jezgra)"
	@echo "  make smoke       - GATE: POST /attempt kroz ŽIVI agentski lanac (traži backend)"
	@echo "  make preflight   - sweep + smoke (pokreni PRIJE evaluacijske sesije)"
	@echo "  make backend     - uvicorn gateway na :8000 (--reload)"
	@echo "  make frontend    - Vite dev server na :5173"
	@echo "  make dev             - sve gore: infra → wait → migrate → seed → SWEEP → backend+frontend"
	@echo "  make infra-down      - zaustavi docker servise (volumeni OSTAJU)"
	@echo "  make openapi-snapshot - regeneriraj frontend/openapi.json iz app.openapi() (bez servera)"
	@echo ""
	@echo "  🔴 EVAL:"
	@echo "  make backup      - pg_dump tutor_main IZVAN volumena + VERIFIKACIJA restore-a"
	@echo "  make dev-reset   - ⚠️  BRIŠE SVE PODATKE (down -v). Traži upisanu potvrdu. ZABRANJEN tijekom evala"

# OpenAPI snapshot za typed frontend klijent (openapi-typescript).
# app.openapi() gradi spec iz app objekta BEZ servera/infra/agenata (KORAK 0 W).
# Regeneriraj kad se backend ugovor promijeni → frontend/openapi.json je diff-vidljiv u PR-u.
openapi-snapshot:
	cd backend && uv run python -c "import json,sys; from app.main import app; json.dump(app.openapi(), sys.stdout)" > ../frontend/openapi.json
	@echo "frontend/openapi.json regeneriran."

db-tasks:
	cd backend && uv run python -m scripts.import_dataset

sandbox-seed:
	cd backend && uv run python -m scripts.seed_sandbox

# Seeda sandbox SAMO ako je prazan → `make dev` je from-scratch sposoban, a na
# ponovnim startovima ne troši sekunde niti bespotrebno reseeda (seed je od
# 4.4-0e determinističan, pa je ponovni seed ionako identičan).
sandbox-seed-if-empty:
	@if [ "$$(docker compose exec -T -e PGPASSWORD=$(PG_SANDBOX_PASS) $(PG_SANDBOX_SERVICE) \
		psql -U $(PG_SANDBOX_USER) -d sandbox -tAc \
		"SELECT count(*) FROM ecommerce_v1.orders" 2>/dev/null || echo 0)" -eq 0 ]; then \
		echo "Sandbox prazan → seedam (deterministički)..."; \
		$(MAKE) --no-print-directory sandbox-seed; \
	else \
		echo "Sandbox već ima podatke — preskačem seed."; \
	fi

# SPADE agenti se spajaju na Prosody na startupu s auto_register=False → računi
# MORAJU postojati prije `make backend`. Prosody volume se briše uz `down -v`,
# pa ovo mora biti u `dev` lancu (NALAZ #26: bez toga `make dev` puca na svježem
# stacku). prosodyctl register je idempotentan.
register-agents:
	cd backend && uv run python -m scripts.register_agents

# 🔴 SWEEP = OBAVEZAN GATE PRIJE EVALUACIJSKE SESIJE (Faza 4.4-0e).
# Pušta `expected_query` svakog AKTIVNOG taska kroz istu evaluacijsku jezgru
# kojom ide studentov upit i tvrdi da referenca reproducira `expected_result`.
# Ne-nul exit ako ijedan padne ILI ako postoji ijedan perzistiran attempt s
# error_type='unsupported_eval' (BKT zagađenje) ILI ako task bank nije seedan.
# Zašto gate: 4.4-0c je pokazao 11/83 neocjenjivih taskova koje nitko nije
# primijetio jer ih ništa nije provjeravalo.
sweep:
	cd backend && uv run python -m scripts.sweep_task_integrity

# 🔴 Sweep zove evaluate() IZRAVNO → zaobilazi HTTP/XMPP/agente i ostaje zelen
# i kad `/attempt` pada. Smoke pokriva točno tu rupu: jedan pravi POST kroz
# cijeli lanac. Traži da backend VEĆ vrti (zato nije u `dev` lancu).
smoke:
	cd backend && uv run python -m scripts.smoke_live_attempt

# Pokreni PRIJE svake evaluacijske sesije (backend mora vrtjeti).
preflight: sweep smoke
	@echo "✅ PREFLIGHT ZELEN — offline jezgra i živi put su provjereni."

infra-up:
	docker compose up -d

# 🔴 BEZ `-v`. Volumeni (pg_main_data) preživljavaju — u njima su evaluacijski
# podaci. Jedini target koji smije dirati volumene je `dev-reset` (vidi dolje).
infra-down:
	docker compose down

# ══════════════════════════════════════════════════════════════════════════
# 🔴 BACKUP / RESET — NALAZ #37
# ══════════════════════════════════════════════════════════════════════════

# Dump `tutor_main` izvan docker volumena + dokaz da je restore-abilan.
# Pokreni POSLIJE SVAKE evaluacijske sesije, pa kopiraj na drugi medij.
backup:
	@./scripts/backup_eval_data.sh

# ⚠️  JEDINI target koji poziva `docker compose down -v` — briše SVE volumene
# (obje baze + Prosody registracije agenata). Nepovratno.
#
# Zašto uopće postoji: `down -v` će netko prije ili poslije htjeti pokrenuti
# (npr. za čist from-scratch test). Bolje da postoji JEDAN target koji prije
# brisanja ispiše što se gubi i traži upisanu potvrdu, nego da se komanda
# kuca ručno iz memorije — u kojem slučaju nema nikakve zaštite.
#
# 🔴 TIJEKOM EVALUACIJE JE ZABRANJEN. Vidi docs/eval-runbook.md.
dev-reset:
	@echo "═══════════════════════════════════════════════════════════"
	@echo " ⚠️  DESTRUKTIVNO: docker compose down -v"
	@echo "═══════════════════════════════════════════════════════════"
	@echo ""
	@echo " Trenutno u bazi tutor_main:"
	@docker compose exec -T $(PG_MAIN_SERVICE) psql -U $(PG_MAIN_USER) -d tutor_main -tAF' ' \
		-c "SELECT '   users:      '||count(*) FROM users UNION ALL \
		    SELECT '   attempts:   '||count(*) FROM attempts UNION ALL \
		    SELECT '   BKT točaka: '||count(*) FROM skill_mastery_history UNION ALL \
		    SELECT '   XP zapisa:  '||count(*) FROM xp_log" 2>/dev/null </dev/null \
		|| echo "   (baza ne vrti — ne mogu pročitati stanje)"
	@echo ""
	@echo " Zadnji backup:"
	@ls -1t backups/*.sql.gz 2>/dev/null </dev/null | head -1 | sed 's|^|   |' \
		|| echo "   🔴 NEMA NIJEDNOG BACKUPA — pokreni 'make backup' PRIJE ovoga!"
	@echo ""
	@echo " Ovo NEPOVRATNO briše: obje baze, sve attempte, BKT povijest, XP,"
	@echo " bedževe i Prosody registracije agenata."
	@echo ""
	@printf " Za potvrdu upiši točno  OBRISI SVE  (bilo što drugo prekida): "
	@read -r ans; \
	if [ "$$ans" = "OBRISI SVE" ]; then \
		echo ""; echo "▸ Brišem..."; \
		docker compose down -v; \
		echo "✓ Volumeni obrisani. Za ponovni boot: make dev"; \
	else \
		echo ""; echo "✅ PREKINUTO — ništa nije obrisano."; \
		exit 1; \
	fi

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
dev: infra-up wait-db db-migrate db-seed db-tasks sandbox-seed-if-empty register-agents sweep
	@trap 'kill 0' SIGINT; \
	(cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) & \
	(cd frontend && npm run dev) & \
	wait
