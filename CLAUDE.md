# Diplomski rad — Inteligentni agentski sustav za učenje SQL-a

## Kontekst projekta

Diplomski rad na FOI, smjer Baze podataka i baze znanja. Mentor: voditelj AI Laba.
Rok predaje: rujan.

## Glavna tema
Višeagentski sustav za adaptivno učenje SQL-a uz igrifikaciju.
Hibridni AI: Prolog (simboličko) + Bayesian Knowledge Tracing (probabilističko).

## Tech stack
- Backend: Python 3.11, FastAPI, SPADE 4.x, pyswip, SQLAlchemy
- Agenti: 5 SPADE agenata + opcionalni 6. (HintAgent)
- Baza: PostgreSQL 16 (main + sandbox), sve u Dockeru
- Frontend: React 18 + TypeScript + Vite + Tailwind + shadcn/ui + Monaco Editor
- LLM: Claude API (offline task gen), OpenAI GPT-4o-mini (opcionalno runtime hints)
- Dev: WSL2 Ubuntu 24.04, uv, SWI-Prolog 10.0.2

## Agenti i njihove uloge
1. EvaluatorAgent — evaluacija SQL upita u sandboxu, klasifikacija grešaka
2. KnowledgeModelAgent — BKT model znanja po konceptu
3. RecommenderAgent — preporuka zadataka (Prolog + BKT)
4. GamificationAgent — XP, leveli, bedževi, streakovi
5. CoordinatorAgent — orkestracija, API gateway
6. HintAgent (opcionalno) — LLM personalizirani hintovi

## Struktura repozitorija

diplomski-sql-tutor/
├── backend/
│   ├── app/         # FastAPI
│   ├── agents/      # SPADE agenti
│   ├── bkt/         # BKT implementacija
│   ├── prolog/      # Prolog ontologija
│   ├── sandbox/     # SQL izvršavanje
│   ├── llm/         # Izolirani LLM kod
│   ├── scripts/     # Utility skripte
│   └── tests/
├── frontend/        # React + TS
├── docker/          # Docker configs
└── docs/            # Dokumentacija, dijagrami

## Trenutna faza
Faza 0 — priprema (environment setup završen, SPADE + pyswip testovi prolaze).
Sljedeće: Faza 1 — Prolog ontologija + shema baze.

## Stil koda
- Python: Black + Ruff, type hints obavezni, docstrings za javne funkcije
- TypeScript: strict mode, ESLint + Prettier
- Commits: conventional commits format (feat:, fix:, docs:, refactor:)
- Jezik komentara i dokumentacije: hrvatski (jer je rad na hrvatskom)

## Važne napomene
- NE uključuj API keyove u git — koristi .env (već u .gitignore)
- Agent komunikacija: uvijek FIPA-ACL performative (request, inform, query-ref)
- Sandbox PG: svi upiti kroz read-only user, statement_timeout = 5s
- Prolog ontologija je AUTORITATIVNI izvor istine za ovisnosti koncepata
- BKT parametri inicijalizirani kao: P(L₀)=0.1, P(T)=0.2, P(G)=0.2, P(S)=0.1

## Što me pitati prije velikih promjena
- Promjene u shemi baze (utječu na migracije)
- Promjene u FIPA protokolima između agenata
- Dodavanje novih dependencies u pyproject.toml ili package.json
