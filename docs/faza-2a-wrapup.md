# FAZA 2A — Wrap-up i evaluacija

**Diplomski rad:** Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju
**Faza:** 2A od 7 (Sub-faza A od Faze 2 — generator SQL zadataka)
**Status:** Završena 04.05.2026.
**Trajanje:** 1 dan implementacije (planirano 2-3 dana)
**Verifikacija:** 173/173 testova prolazi (132 nova + 41 baseline iz Faze 1), live API test pass-a end-to-end na 2. attempt-u uz $0.0068 cost

---

## 1. Sažetak izvedenog rada

Sub-faza 2A izgradila je **infrastrukturu** za poluautomatsko generiranje SQL zadataka kroz Anthropic Claude API: prompt builder iz YAML konfiguracije, SDK wrapper s prompt caching-om i retry logikom, AST-based concept coverage analyzer za svih 30 SQL koncepata iz Faze 1, sandbox SQL runner s read-only role isolation, i 3-razinski validator (sintaksa → AST coverage → result match). Cilj nije bila masovna generacija (to je 2B), nego dokaz da pipeline radi end-to-end na 1 zadatku s manje od $0.05 troška.

Komponente (po implementacijskom redoslijedu):

| Komponenta | Datoteka | LoC | Odgovornost |
|---|---|---|---|
| Pydantic schema | `app/schemas/generated_task.py` | 41 | Strukturna validacija LLM outputa (`GeneratedTask`, `GeneratedTaskMeta`) |
| JSON helper | `scripts/lib/json_extract.py` | 34 | Izvlačenje JSON-a iz markdown code-blockova / bare objects |
| Sandbox runner | `scripts/lib/sandbox_runner.py` | 155 | psycopg3 + `SET ROLE sandbox_readonly`, statement_timeout 5s, compare() |
| Prompt builder | `scripts/lib/prompt_builder.py` | 127 | YAML → system+user prompt s sample rows blokom |
| AST analyzer | `scripts/lib/ast_analyzer.py` | 543 | 30 detektora (17 trivial + 7 join + 6 complex + index_usage placeholder) |
| Anthropic SDK wrapper | `scripts/lib/api_client.py` | 91 | Retry, prompt caching (`cache_control=ephemeral`), extended thinking |
| Validator | `scripts/lib/task_validator.py` | 178 | 3-razinska validacija sa short-circuit i broad except wrapper-ima |
| CLI entrypoint | `scripts/generate_tasks.py` | 282 | argparse + retry petlja + per-task cost logging + save_meta routing |
| **Ukupno (kod)** | — | **1 451** | — |

## 2. Ključni doprinosi

| Doprinos | Dokaz |
|---|---|
| Hibridna AST-based concept coverage (regex + sqlparse + sqlglot) | 30 detektora, 84 testa, 0 false-positives na quoted identifiers / nested comments / escaped quotes |
| Anti-halucinacija kroz sample rows + LIMIT N pravilo u system promptu | Live test: model 1. attempt halucinirao (`actual=30 vs expected=3`), 2. attempt PASS s točnim Faker-generiranim vrijednostima (`Keller PLC, josephbrennan@brandt-hickman.com`) |
| Prompt caching ostvaruje 90% off na cached input | Live test pokazao 2 873 cached tokens vs 2 fresh input tokens nakon 1. poziva |
| Defensible 3-razinska validacija s short-circuit | Validator ispravno odbio halucinirane zadatke u `failed/` subdir, prihvatio jedini točan u `validated/` |
| Test-driven implementacija s 3 nezavisne code-review iteracije | 16 commit-ova, 132 nova testa, sve HIGH severity findings adresirane prije commit-anja taska |
| Cijenovna učinkovitost u domeni starter credit-a | Live test: $0.0068 za 1 zadatak (ekstrapolacija: ~$0.71 za 105 zadataka u 2B, dobro unutar $5 starter credit-a) |

## 3. Verifikacija deliverables (kraj Sub-faze 2A)

### 3.1 Kvantitativni dokazi

| Metrika | Vrijednost | Source |
|---|---|---|
| Komponenti (lib + schema + CLI) | 8 | `backend/scripts/lib/`, `backend/app/schemas/generated_task.py`, `backend/scripts/generate_tasks.py` |
| Linija koda (kompletna 2A) | 1 451 | `wc -l` na svih 8 produkcijskih fajlova |
| AST detektora (30 koncepata) | 30 | `_DETECTORS` dispatch tablica u `ast_analyzer.py` |
| Concept YAML config-ova | 3 (sample) | `select_basic`, `inner_join`, `left_join` (preostalih 27 ide u 2B) |
| Sample rows po tablici | 3-5 | `sandbox_context.yaml` (Faker seed=42, stvarni podaci iz sandbox-a) |
| Testova ukupno (projekt) | 173 | `uv run pytest --co -q` (41 baseline + 132 nova) |
| Code-review checkpoint-a | 3 | Nakon AstAnalyzer / TaskValidator / Integration |
| Git commits u 2A | 17 | `git log faza-1-complete..faza-2a-complete --oneline` |
| Live API trošak (1 zadatak) | $0.0068 | CLI cost log iz `select_basic_d1_2fd7fa43.json` (in=2, out=397, cached=2873) |

### 3.2 Distribucija testova po komponenti

| Test fajl | Broj testova | Pokrivenost |
|---|---|---|
| `test_ast_analyzer.py` | 84 | 30 detektora × 2-4 testa + 6 regression za code review #1 |
| `test_task_validator.py` | 11 | 6 baseline + 5 regression za code review #2 (broad except, details promotion, TRUNCATE, empty result) |
| `test_prompt_builder.py` | 9 | 8 baseline + 1 sample_rows assertion |
| `test_sandbox_runner.py` | 7 | execute (3) + compare (3) + null handling (1) |
| `test_generated_task_schema.py` | 6 | Pydantic positive + 4 negative + meta wrapper |
| `test_api_client.py` | 5 | Happy path + retry + auth + thinking + caching |
| `test_json_extract.py` | 5 | Plain + markdown + unlabeled + surrounded + raise |
| `test_generate_tasks_integration.py` | 5 | failed/ + validated/ routing + max_retries + schema retry + UTF-8 |
| **Ukupno (2A novi)** | **132** | — |

### 3.3 Live API test rezultati

Komanda:
```bash
uv run python -m scripts.generate_tasks \
    --concept select_basic --difficulty 1 --count 1 \
    --dry-run --output-dir ../data/generated_tasks/
```

Tijek:
| Attempt | Stage | Outcome | Razlog |
|---|---|---|---|
| 1 | API → schema → validator | FAIL na razini 3 (`row_mismatch`) | Model produced 3-row expected_result vs sandbox vrati 30 redova (no LIMIT) |
| 2 | API → schema → validator | **PASS** | Model dodao `ORDER BY id LIMIT 3`, koristio stvarne sample row vrijednosti |

Generirani zadatak (sažetak iz `data/generated_tasks/validated/select_basic_d1_2fd7fa43.json`):

```json
{
  "title": "Prikaz naziva i e-maila svih dobavljača",
  "primary_concept": "select_basic",
  "secondary_concepts": ["from_clause"],
  "difficulty": 1,
  "expected_query": "SELECT name, contact_email FROM suppliers ORDER BY id LIMIT 3;",
  "expected_result": [
    {"name": "Keller PLC", "contact_email": "josephbrennan@brandt-hickman.com"},
    {"name": "Collins, Carney and Santos", "contact_email": "clam@wright.com"},
    {"name": "Chapman and Sons", "contact_email": "adrianzimmerman@perez.com"}
  ],
  "targets_misconception": "select_star_overuse"
}
```

| Token / Cost metrika | Vrijednost |
|---|---|
| Input tokens (fresh) | 2 |
| Input tokens (cached) | 2 873 |
| Output tokens | 397 |
| Trošak | $0.0068 |
| Cache hit ratio | 99.93% (2 873 / 2 875) |
| Retries | 1 (PASS na 2. attempt) |
| Vrijeme do success-a | ~17 sekundi |

### 3.4 Code review checkpointi i adresiranja

| # | Komponenta | Severity findings | Što je popravljeno | Regression testova |
|---|---|---|---|---|
| 1 | AstAnalyzer | 3 HIGH + 1 MEDIUM | Quoted identifiers (`"where"`), `''` escape leak, nested `/* /* */ */`, comma-join u multi_table_join | 6 |
| 2 | TaskValidator | 1 HIGH + 2 MEDIUM | Broad `except` wrapper za detector_crashed/runner_crashed/comparison_crashed, `is_in_comment` u details, TRUNCATE regex | 5 |
| 3 | CLI / Integration | 2 HIGH + 1 MEDIUM | Eksplicitni SDK `max_retries=2`, integration test split na 5, per-task cost logging | 4 (integration tests) |

### 3.5 Git artefakti

```
faza-2a-complete    (Sub-faza 2A milestone — push-an na origin)
```

17 commit-ova kroz 16 task-ova plana (1 environment setup + 11 implementation + 3 review fixes + 1 prompt enrichment + 1 docs):

```
1f663fc feat(2a): sample rows + LIMIT N pravilo u prompt — anti-halucinacija
7352dcc fix(2a): CLI/integration hardening from code review #3 + 4 nova testa
a1a3f3b test(2a): integration test za generate_tasks pipeline
ab7b236 feat(2a): generate_tasks CLI — orkestracija pipeline-a
d8f312e fix(2a): TaskValidator hardening from code review #2 + 5 regression tests
49b725a feat(2a): TaskValidator — 3-razinska validacija + 6 tests
90dee3b feat(2a): AnthropicClient — generate + retry + caching + 5 tests
6574903 fix(2a): AstAnalyzer hardening from code review #1 + 6 regression tests
7f38e06 feat(2a): AstAnalyzer COMPLEX detectors (6 + index_usage placeholder) + 21 tests
a73cc58 feat(2a): AstAnalyzer JOIN detectors (7 koncepata) + 21 tests
1fe3fe5 feat(2a): AstAnalyzer trivial detectors (17 koncepata) + 36 tests
2cf2f4d feat(2a): PromptBuilder — system+user assembly iz YAML + 8 tests
fba38cd feat(2a): SandboxRunner — execute + compare + 7 tests
3a98335 feat(2a): extract_json helper — markdown codeblock + bare object + 5 tests
0fba6c7 feat(2a): GeneratedTask Pydantic schema + 6 tests
4a06140 chore(2a): environment setup — deps, configs, fixtures, dirs
```

## 4. Errata za dokument `faza-2a-plan.md`

Tijekom implementacije identificirana su sljedeća odstupanja od plana — dokumentirana ovdje za buduće ažuriranje plana:

| # | Lokacija | Original plan | Stvarna implementacija | Razlog |
|---|---|---|---|---|
| 1 | §4.4 | `postgresql://app_user:pass@localhost:5433/sandbox` | `postgresql://sandbox_admin:...` + `SET ROLE sandbox_readonly` per query | `app_user` ne postoji u sandbox-u; `sandbox_admin` je vlasnik iz Faze 1C, role-switch defense-in-depth pattern je čišći |
| 2 | §4.5 (correlated_subquery) | `find_all(exp.Subquery)` | `find_all(exp.Subquery) + find_all(exp.Exists)` | sqlglot 30.x ne wrapuje EXISTS u Subquery node, nego u Exists direktno |
| 3 | §4.5 (`index_usage`) | "Query koristi `WHERE col = X` na indexed column (semantic check kasnije)" | `NotImplementedError` placeholder s razlogom | Pravi semantički check zahtijeva runtime EXPLAIN ANALYZE — defer u Modul 6 / Faza 6 |
| 4 | §6 (test count) | "60+ test cases" | 84 testa | Opcija C iz brainstorming-a (svih 30 detektora grupirano) + 6 regression za code review #1 |
| 5 | §10 (rizik matrica) | "Cached tokens ne rade (prvi poziv = cache miss)" | Cache hit nakon 1. poziva, 99.93% ratio | Predviđeno; samo potvrđeno empirijski u live testu |
| 6 | §7 (sandbox_context.yaml) | Schema + invariante | + sample_rows blok (3-5 stvarnih redova po tablici) | Tijekom live testiranja se pokazalo da bez sample data model halucinira `supplier_name_1, supplier_name_2,...` placeholder-e — sample rows + LIMIT N pravilo riješili problem |

## 5. Tehnološki dug (rješava se u Fazi 2B i kasnije)

| Stavka | Opis | Rok | Težina |
|---|---|---|---|
| 27 preostalih concept YAML config-ova | 2A ima samo 3 sample-a (`select_basic`, `inner_join`, `left_join`); preostali idu prije generation run-a | Faza 2B | Medium |
| `index_usage` detektor (placeholder) | Trenutno vraća `detected=False` s razlogom; pravi check zahtijeva EXPLAIN ANALYZE parsing | Faza 6 (Optimizacija) | Medium |
| `--dry-run` flag je trenutno no-op | Zadržan u argparse-u, ali nikad ne čita `args.dry_run`; postaje funkcionalan u Fazi 2C kad se doda DB write | Faza 2C | Low |
| `secondary_concepts` validacija | Validator trenutno provjerava samo `primary_concept`; secondary su samo informativni, ali bi se mogli surface-ati u `ValidationResult.warnings` | Faza 2B | Low |
| Dollar-quoted strings u AST stripper-u | `$$...$$` PostgreSQL syntax nije strip-ana; LLM nije sklon proizvesti ih, ali edge case ostaje | Faza 6 ili po potrebi | Low |
| Per-component import hygiene | `sqlglot` import bio mid-file (pre-fix) → sad na vrhu; future detektori treba držati isto | Stalna praksa | Low |

## 6. Spremnost za Fazu 2B

Fazu 2B (full generation run za 105 zadataka + ručna validacija) blokirale bi sljedeće stvari iz 2A; sve su završene:

- [x] CLI radi end-to-end (live test prošao s $0.0068)
- [x] AST analyzer pokriva svih 30 koncepata iz Prolog ontologije
- [x] Validator ispravno odbacuje halucinirane zadatke (dokazano u attempt 1 live testa)
- [x] Prompt caching radi (99.93% hit ratio)
- [x] Cost logging granularan po taskou (CLI ispisuje per-task estimate)
- [x] Output routing u `validated/` vs `failed/` subdirektorije radi
- [x] UTF-8 round-trip za hrvatske dijakritike (testirano s "ž" iz "Narudžbe")
- [x] Sandbox kontejner i Faker seed potvrđeni reproducibilni

Što treba **prije** pokretanja generation run-a u 2B:

- [ ] Napisati 27 preostalih concept YAML config-ova (procijenjeno 2-3 sata, šablonski rad)
- [ ] Napraviti `--from-matrix` flag u CLI (trenutno postoji samo single-concept mode)
- [ ] Pripremiti budget guard rail (npr. abort ako kumulativni cost prekorači $3 — pola starter credit-a)

## 7. Reflektivne napomene

**Što je dobro funkcioniralo:**
- TDD pristup po komponenti — svaka komponenta je počela s failing testom, što je natjeralo definiranje interface-a prije implementacije
- 3 code-review checkpoint-a (nakon AstAnalyzer / Validator / Integration) — svaki je pronašao 1-3 HIGH severity findings koji su bili nevidljivi u tijeku pisanja
- Code review #1 je posebno prevenirao buduće 2B debug headache (quoted identifiers `"where"` bi false-positively detektirali where_filter u 2B generation run-u)
- Pre-flight verifikacija prije pisanja plana (data dir, deps, sandbox, API key) — uštedjela ~30 min "ah, fali mi X" detour-a

**Što treba pamtiti za buduće faze:**
- LLM ne može predvidjeti random Faker vrijednosti bez sample data — anti-halucinacija pravila (sample rows + LIMIT N) su core, ne polish; ako se koriste novi tipovi tasks-a u 2B/2C, pravila treba prilagoditi po tipu
- sqlglot vs sqlparse: sqlparse je lexer (brz, krhk), sqlglot je pravi AST parser (sporiji, robustan). Pravilo: sqlparse za syntax-only checks, sqlglot za semantic scope analysis
- Anthropic SDK ima vlastiti retry layer (default `max_retries=2`); bez eksplicitnog postavljanja, layered retry može otići do 9 poziva po taskou s nepredvidljivim budget impactom — uvijek eksplicitno postaviti
- Prompt caching s `cache_control=ephemeral` je 90% off od inputa — za 2B s 105 tasks isti system prompt ide u cache nakon 1. poziva, što praktički eliminira input-token cost (samo ~2 fresh tokens po pozivu)

---

*Faza 2A zaključena 04.05.2026. Sljedeći korak: Faza 2B — popunjavanje preostalih 27 concept YAML-ova, pokretanje generation run-a za 105 zadataka, ručna validacija od strane korisnika.*
