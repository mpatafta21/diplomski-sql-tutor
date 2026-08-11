# Faza 3 — Agentni tutoring sustav (plan)

**Status:** plan (ulaz nakon `faza-2b-3-complete`)
**Grana baze:** `faza-2b-3-validation` → nova grana `faza-3-agents`
**Rok:** rujan (obrana). Faza 3 = build sloj; ostavi runway za evaluacijsku studiju + pisanje.
**Izvor istine:** ovaj dokument + audit repoa (2026-06). Sve potpise dolje provjeri prije implementacije ako prođe vrijeme.

---

## 0. Polazište (stvarno stanje iz audita)

| Komponenta | Stanje | Napomena za Fazu 3 |
|---|---|---|
| 16 DB tablica, `alembic head = ac6a5eeac6e5` | ✓ | `tasks`/`task_concepts` PRAZNE |
| `modules` (7: 0–6), `concepts` (30), `badges` (5) | ✓ seedano | `seed.py` ne seeda taskove |
| `bkt/model.py` `BKT`, `bkt/parameters.py` `TIER_DEFAULTS` | ✓ | tier init neupotrijebljen u runtime-u |
| `app/prolog/prolog_engine.py` + `rules.pl` | ✓ query-ready | `recommend_next/2` vraća `(concept, reason)` |
| `prolog/badges.pl` | ✗ prazan placeholder | 3D piše od nule |
| `scripts/lib/sandbox_runner.py` `SandboxRunner` | ✓ | ima `.execute()` I `.compare()`; NUMERIC→str |
| SPADE 4.1.2 + Prosody (docker-compose) | ✓ infra | nijedan agent registriran; `backend/agents/` ne postoji |
| `final_dataset.json` (83, gitignored) | ✓ na disku | wrapper objekt, `module` int, `task_id` slug |
| FastAPI app / rute / frontend | ✗ | scaffold prazan |

**Kritični put:** `3.0 seed → 3A Evaluator → 3B Knowledge → 3C Recommender → 3E Coordinator+API → 3F Frontend`. `3D Gamification` grana paralelno nakon 3A. **3.0 i 3A su tvrdi blokeri za sve.**

---

## 0.1 Arhitekturne odluke (zaključane iz audita)

**D1 — `source_id` na `tasks`.** Mala migracija: `ALTER TABLE tasks ADD COLUMN source_id VARCHAR(64) UNIQUE`. Daje idempotentni upsert (`ON CONFLICT (source_id)`) + traceability slug→DB. Bez toga nemaš stabilan ključ jer je dataset gitignored/regenerabilan.

**D2 — filtriranje koncepata pri importu.** `primary_concept` MORA postojati u `concepts.code` (inače hard-fail tog taska + log). `secondary_concepts` se filtriraju: nepostojeći kodovi (npr. `aggregate_functions`) se **tiho preskaču uz warning log**, ne ruše import.

**D3 — tier-based init je posao KnowledgeModelAgenta, ne DB-a.** Pri prvom attemptu za par `(user, concept)`, agent radi lazy init kroz `create_bkt_for_concept(concept, engine)` i upisuje stvarne tier-parametre. DB default 0.15 je samo fallback; ne oslanjaj se na njega.

**D4 — Evaluator omata `SandboxRunner.compare()`, ne reimplementira.** Postojeći `compare()` već normalizira Decimal→str i datetime→ISO. EvaluatorAgent ga poziva i mapira `ComparisonResult` u svoju klasifikaciju. **Iznimka:** `explain_plan`/`index_usage` ne idu kroz strict row-match — poseban put (plan-string-presence: traži „Index Scan" prisutan / „Seq Scan" odsutan).

**D5 — SPADE verzija (writing-reconcile).** Kod = 4.1.2 (async). Teza citira Palanca 2020 (SPADE 3) kao platformu — zadrži citat, dodaj rečenicu „implementirano na SPADE 4.1.2". Sve behaviour klase (`CyclicBehaviour`, `PeriodicBehaviour`, `FSMBehaviour`, `OneShotBehaviour`) postoje u 4.1.2.

**D6 — race condition Evaluator → Knowledge/Gamification.** Rješenje: **EvaluatorAgent persistira `attempts` red (s klasifikacijom) PRIJE nego pošalje `inform`.** Downstream agenti dobivaju `attempt_id` u poruci i čitaju COMMITTED red. Tako je perzistencija sync točka — Knowledge i Gamification mogu teći paralelno jer oba samo čitaju isti commitani attempt. Nema dijeljenog mutable stanja u letu.

**D7 — `insert`/`right_join` gap (1 approved svaki).** Treba 1 NOVI zadatak po konceptu (sandbox-grounded `expected_result`), dodati u dataset, re-import (idempotentno → nula rework). Slot: tijekom 3.0, paralelno s import skriptom. Ako ne stignu, EvaluatorAgent fallback (D u 3C) ih ne servira dok `task_concepts` < 2.

---

## 3.0 — Seed: sandbox snapshot + import `tasks`/`task_concepts` (GATING)

**Cilj:** napuniti `tasks` (83) i `task_concepts` iz `final_dataset.json`, uz zamrznut sandbox kao izvor istine za `expected_result`.

**Entry:**
- `final_dataset.json` na disku (`data/generated_tasks/`)
- `alembic upgrade head` primijenjen, `concepts`/`modules` seedani

**Koraci:**
1. **Sandbox snapshot (KRITIČNO, flag #1 iz 2B-3).** Faker seed NE štiti od drift-a verzije Fakera. Robusnije:
   - `pg_dump --data-only --schema=ecommerce_v1 sandbox > data/sandbox_snapshots/ecommerce_v1__ds-2b3.sql`
   - SHA-256 dumpa → upiši u `data/sandbox_snapshots/manifest.json` uz `dataset_version: "2b-3"` + git SHA
   - Od Faze 3 nadalje sandbox se **restora iz dumpa**, ne regenerira `seed_sandbox.py`
2. **Migracija D1:** `source_id VARCHAR(64) UNIQUE` na `tasks` (+ `downgrade`).
3. **Import skripta** `backend/scripts/import_dataset.py`:
   - Učitaj wrapper, iteriraj `tasks[]`
   - `module (int) → module_id` preko mape iz `seed.py` (modules po `number`)
   - `primary_concept → concept_id` (hard-fail ako nema)
   - Upsert u `tasks` po `source_id = task_id` (`ON CONFLICT DO UPDATE`)
   - `task_concepts`: primary `is_primary=true`; sekundarni filtrirani po `concepts.code`, `is_primary=false`
   - `sandbox_schema='ecommerce_v1'`, `difficulty` int, `estimated_time_sec` nullable
4. **(paralelno, D7)** napiši `insert` + `right_join` nova zadatka, sandbox-grounded, dodaj u dataset, re-run import.

**Deliverables:** `import_dataset.py`, migracija `00X_add_source_id.py`, `manifest.json` + dump, 2 nova taska (opcionalno).

**Exit:**
- `SELECT count(*) FROM tasks` = 83 (ili 85 s D7)
- `task_concepts` popunjen, svaki task ≥1 primary
- Re-run importa idempotentan (count se ne mijenja)
- **Smoke test:** odaberi 5 random taskova → izvrši `expected_query` kroz `SandboxRunner` na restoranom snapshotu → output == `expected_result` (dokazuje da snapshot čuva istinu)

**Test (TDD):** `test_import_dataset.py` — mapping module→id, concept hard-fail, secondary filter (`aggregate_functions` se preskače), idempotentnost (dvostruki import → isti count).

---

## 3A — EvaluatorAgent (srce sustava)

**Cilj:** SQL upit studenta → sandbox izvršavanje → usporedba s `expected_result` → klasifikacija → strukturirani rezultat + persist `attempts`.

**Entry:** 3.0 gotov (tasks seedani). Nova `backend/agents/` struktura.

**Predložena struktura `backend/agents/`:**
```
__init__.py
base.py          # TutorAgent(Agent): zajednički setup, config (JID/pass iz .env), FIPA log u agent_messages_log
messages.py      # performative + ontology konstante; JSON payload (de)serialize u msg.body
jids.py          # registry JID-eva agenata
evaluator.py     # EvaluatorAgent (CyclicBehaviour)
```

**Protokol poruke (SPADE 4.1.2):**
- Payload = JSON u `msg.body`; `msg.set_metadata("performative", "request"|"inform")`; `msg.set_metadata("ontology", "evaluate-query")`
- Routing kroz `Template` (match po performative+ontology) → behaviour
- Ulaz: od Coordinatora `request` / `evaluate-query`: `{user_id, task_id, submitted_query}`
- Izlaz: `inform` prema Knowledge + Gamification: `{attempt_id, user_id, task_id, concepts:[...], is_correct, error_type}`

**Logika (TDD redoslijed):**
1. Sintaktička provjera (`sqlparse`) prije izvršavanja → `error_type=syntax_error` rano
2. Izvršavanje kroz `SandboxRunner.execute(query, schema, dml=<task DML?>)` (timeout 5s, `SET ROLE` već u runneru)
3. Usporedba kroz `SandboxRunner.compare(actual, expected)` (D4 — već normalizira tipove)
4. Za `explain_plan`/`index_usage`: poseban put (plan-string-presence), NE strict row-match
5. Klasifikacija greške: `syntax_error`, `execution_error` (timeout/exception), `row_mismatch`, `wrong_concept` (AST ne sadrži ciljani konstrukt), `empty_result`
6. **Persist `attempts`** (D6) PRIJE informa: `submitted_query, is_correct, error_type, execution_time_ms, rows_returned, attempt_number`
7. Pošalji `inform` (s `attempt_id`) prema Knowledge + Gamification

**Deliverables:** `base.py`, `messages.py`, `evaluator.py`, conftest fixtures (`sandbox_runner`, `db_session` s rollbackom — audit kaže da NE postoje).

**Exit:**
- Evaluira 3 ishoda (točno / djelomično / netočno) + 5 klasifikacija greške
- Decimal usporedba prolazi (regression za 2B-3 type-coercion bug)
- `explain_plan` zadatak evaluiran plan-presence putem, ne row-matchom
- `attempts` red commitan prije informa (dokazano testom)

**Test (TDD):** `test_evaluator.py` — happy path, syntax_error, row_mismatch, NUMERIC-kolona task (Decimal), explain_plan plan-presence, timeout→execution_error, persist-before-inform ordering.

**Rizik:** `SandboxRunner.compare()` semantika za djelomično-točno (partial) — ako vraća samo bool, Evaluator dodaje vlastiti partial-match sloj (npr. točan set stupaca, krivi redovi). Provjeri `ComparisonResult` polja prije pisanja.

---

## 3B — KnowledgeModelAgent (BKT runtime)

**Cilj:** ishod attempta → BKT posterior update po konceptu → upis u `skill_mastery`.

**Entry:** 3A šalje `inform` s `attempt_id`.

**Logika:**
- `CyclicBehaviour` sluša `inform`/`attempt-result`
- Čita commitani attempt (D6) → lista koncepata zadatka (`task_concepts`)
- Za svaki koncept: učitaj `skill_mastery` red; ako ne postoji → **lazy init kroz `create_bkt_for_concept(concept, engine)`** (D3), ne DB default
- `bkt.update(is_correct)` → novi `p_l` → upsert `skill_mastery` (+ `attempts_count`, `last_updated`)
- Misconception detekcija (pattern, npr. ponovljeni `wrong_join_type`) → `misconceptions` upsert
- `PeriodicBehaviour` (opcionalno) za batch perzistenciju ako single-write postane usko grlo
- Izlaz: `inform` prema Coordinatoru (model ažuriran); odgovara Recommenderu na `request` za snapshot

**Deliverables:** `knowledge.py`, `test_knowledge.py`.

**Exit:**
- BKT update mijenja `p_l` u skladu s `bkt/model.py` (regression na poznati primjer iz Faze 1 §5.5)
- Lazy tier-init: novi `(user, hard-concept)` dobiva `p_l0=0.05`, ne 0.15
- Misconception se inkrementira na ponovljenoj grešci

**Rizik:** `inject_mastery` u `PrologEngine` očekuje `dict[str, float]` snapshot — Knowledge mora znati emitirati taj format za 3C.

---

## 3C — RecommenderAgent (Prolog + BKT)

**Cilj:** preporuka sljedećeg zadatka kombinirajući prerequisite graf (Prolog) + mastery (BKT).

**Entry:** 3B upisuje `skill_mastery`. `prolog_engine.py` + `rules.pl` query-ready.

**Logika:**
- Na `request`/`recommend-next` za `user_id`:
  - Učitaj mastery snapshot iz `skill_mastery` → `engine.inject_mastery(user_id, snapshot)`
  - `engine.recommend_next(user_id)` → `(concept, reason)` ili `None`
  - Concept → odaberi konkretan `task` iz tog koncepta (filtriraj `is_active`, izbjegni nedavno riješene)
  - **D7 fallback:** ako koncept ima < 2 aktivna taska (`insert`/`right_join`), preskoči ili degradiraj na susjedni ready koncept
- Izlaz: `inform` Coordinatoru `{task_id, concept, reason}`

**Deliverables:** `recommender.py`, `test_recommender_agent.py` (uz postojeće `test_recommender_synthetic.py`).

**Exit:**
- 3 sintetička profila (weak / partial / unlock) vraćaju očekivani koncept (reuse postojećih testova)
- `recommend_next` → konkretan `task_id`, ne samo koncept
- Fallback ne servira sub-floor koncept

**Rizik:** `inject_mastery` koristi `:- dynamic(mastery/3)` — pazi na `clear_mastery` između korisnika (stale fact leak; Faza 1 code-review je već uhvatio sličan ordering bug).

---

## 3D — GamificationAgent (paralelno nakon 3A)

**Cilj:** ishod attempta → XP → level → badge → streak.

**Entry:** 3A `inform`. **`badges.pl` je prazan — piše se od nule.**

**Logika:**
- `CyclicBehaviour` sluša `attempt-result`
- XP formula (plan §3.4): `težina × točnost × bonus_za_prvi_pokušaj` → `xp_log` + `users.xp`
- Level-up: XP threshold tablica → `users.level`
- Badge: napiši `award_badge(UserID, BadgeCode) :- ...` i `earned_badges/2` u `badges.pl` za 5 seedanih bedževa (JOIN Master, Speed Demon, Comeback Kid, Streak 7, Group Master) → `user_badges`
- Streak: dnevni tracking → `streaks` + `users.current_streak`/`longest_streak`
- Event-driven, **ne blokira** Evaluator/Knowledge

**Deliverables:** `gamification.py`, `prolog/badges.pl` (popunjen), `test_gamification.py`.

**Exit:**
- XP/level/streak update na attempt
- Bar 2 badgea dodijeljena pravilima iz `badges.pl` (npr. Speed Demon < 30s, Comeback Kid nakon 5+ fail)

---

## 3E — CoordinatorAgent + FastAPI

**Cilj:** orkestracija (FSM) + HTTP gateway koji frontend vidi.

**Entry:** 3A–3D agenti rade pojedinačno.

**Logika:**
- `CoordinatorAgent` = `FSMBehaviour` (`add_state`/`add_transition`): npr. `RECEIVE → EVALUATE → UPDATE(KM+Gam paralelno) → RECOMMEND → RESPOND`
- FastAPI bridge (`app/bridge/agent_bridge.py`): HTTP → FIPA-ACL poruka Coordinatoru, čeka odgovor (async)
- Rute: `POST /attempt` (submit query), `GET /next-task`, `GET /profile` (XP/level/mastery/badges)
- Session state: koji korisnik radi koji zadatak
- Log svih FIPA poruka → `agent_messages_log` (za evaluaciju i rad)

**Deliverables:** `coordinator.py`, `app/main.py` (FastAPI), `app/api/*.py`, `agent_bridge.py`, `test_api.py` (integration).

**Exit:**
- `POST /attempt` → evaluacija → BKT update → preporuka → JSON odgovor, end-to-end
- `GET /next-task` vraća preporuku, `GET /profile` vraća stanje
- FIPA poruke logirane

**Rizik:** async bridge HTTP↔XMPP — request/response korelacija (conversation-id). Bez nje Coordinator ne zna koji odgovor pripada kojem HTTP requestu. Koristi `msg.thread` / metadata `conversation-id`.

---

## 3F — Frontend (MVP, ne polishan)

**Cilj:** student flow + dashboard. Najduži dio; **drži MVP** zbog roka.

**Logika:**
- React + TS + Monaco Editor (SQL pisanje)
- Flow: dohvati zadatak (`GET /next-task`) → piši SQL → `POST /attempt` → prikaži feedback (točno/greška/klasifikacija) → sljedeći
- Dashboard: XP, level, badge-ovi, mastery po konceptu (`GET /profile`)
- **Cut za MVP:** animacije, hint UI (ovisi o opcionalnom HintAgentu), leaderboard polish

**Deliverables:** React app, `test` minimalno (happy-path e2e).

**Exit:** student može riješiti zadatak i vidjeti feedback + napredak end-to-end.

---

## Opcionalno / deferrabilno (ako rok pritisne)

- **HintAgent (6. agent)** — `USE_LLM_HINTS` feature flag, ~~GPT-4o-mini~~ **Anthropic `claude-haiku-4-5`** (ispravljeno u Fazi 5.0 — v. `docs/errata.md` #59). Defer ako kasniš; rule-based `hints` tablica je fallback.
- **Leaderboard, WebSocket** (`app/api/ws.py`) — nice-to-have za demo, ne za eval.
- **BKT kalibracija** na prvim studentskim podacima — to je **istraživački doprinos rada**, radi se u Fazi 4 (eval), ne u 3.

---

## Sekvenca i runway (rok rujan)

Preporučeni redoslijed = kritični put. CC procjena ~6–8 tj build. Za zaštitu evaluacije + pisanja:
- **Cilj:** 3.0+3A+3B+3C+3E funkcionalno do ~kraja srpnja, 3F MVP sredina kolovoza
- **Zaštiti ≥3 tjedna** na kraju za eval studiju (pre/post test traži stvarne korisnike) + pisanje (Faza 7)
- **Ako kasniš:** režeš 3F polish, HintAgent, WebSocket — NE Evaluator/BKT (to je jezgra doprinosa)

## Tagovi (checkpoint po pod-fazi)
`faza-3-0-seed` · `faza-3a-evaluator` · `faza-3b-knowledge` · `faza-3c-recommender` · `faza-3d-gamification` · `faza-3e-coordinator-api` · `faza-3f-frontend` · `faza-3-complete`
