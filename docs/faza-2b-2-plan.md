# FAZA 2B-2 — Akcijski plan

**Diplomski rad:** Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju
**Sub-faza:** 2B-2 od 8 (predposljednja sub-podsekcija Faze 2B)
**Cilj:** Generirati 105 SQL zadataka kroz hibrid (100 LLM batch + 5 ručno za group_by) — finalni dataset za 2B-3 manual validation
**Trajanje:** 3-5h aktivnog rada (2-3h LLM batch monitoring, 1-2h ručno pisanje group_by)
**Trošak:** $5-10 realistic, per-module soft cap $1.50
**Predviđeni broj git commit-ova:** 10-14 (commit per module + setup + group_by)

---

## 1. Kontekst i ciljevi

### 1.1 Pozadina

Sve prethodne 2B-1 sub-faze (A → B → D → E → C) bile su priprema za ovaj trenutak: full generation run za 105 zadataka iz distribucijske matrice u `faza-2a-plan.md` §2.

**Naučeno iz prethodnih sub-faza koje direktno informira 2B-2:**

| Lesson | Implikacija za 2B-2 |
|---|---|
| Pilot 70% pass rate (2B-1E), 50% u Iter 2 (2B-1D) | Realistic očekivanje za 2B-2 batch je 65-75% prvi-pokušaj |
| `group_by` 0/2 u 2B-1E rerun — model ignorira ground-truth hints | Skip iz LLM batch-a, ručno napiši |
| Extended thinking always-on default je essential | Već u kodu (2B-1E) — koristi by default |
| Per-task retry overhead je značajan (3x prosječno za fail-eve) | Per-module budget cap mora ovo uračunati |
| Validator + sandbox dijagnozе mogu biti pogrešne (2B-1E `explain_plan` discovery) | Ne skin-deep interpretacije fail-eva — manual review prije panic-a |

### 1.2 Što ova sub-faza radi

1. **Pre-flight setup** — `--from-matrix` CLI flag u `generate_tasks.py` (tehnološki dug iz 2A errata)
2. **LLM batch generation, modul po modul:**
   - M1 (Osnove SELECT-a) — 21 zadataka × 6 koncepata
   - M2 (Agregacije) — 19 zadataka × 5 koncepata (skip `group_by` 5 tasks)
   - M3 (JOIN-ovi) — 28 zadataka × 7 koncepata
   - M4 (DML) — 11 zadataka × 3 koncepta (DML mode)
   - M5 (Subqueries) — 15 zadataka × 4 koncepta
   - M6 (Optimizacija) — 6 zadataka × 2 koncepta
   - M0 (Transverzalni) — 5 zadataka × 1 koncept (`null_handling`)
3. **Per-module monitoring** — pass rate, cost, failure patterns; abort & fix ako >$1.50 ili >50% fail
4. **Ručno pisanje `group_by` × 5** — nakon LLM batch, prije 2B-3 review
5. **Batch report** — `data/generated_tasks/batch_report.json` s per-module summary i overall stats

### 1.3 Što ova sub-faza NE radi

- ❌ Manual validation kroz Streamlit tool — to je 2B-3
- ❌ Re-generation failed tasks kroz custom prompts — defer u 2B-3 cleanup ako zatreba
- ❌ Tool-use grounding migration — explicit skip per Q5 odluka
- ❌ Prompt template fix-evi za nove failure patterns — defer u 2B-1F ili 2B-3 cleanup
- ❌ Concept YAML modification — locked iz 2B-1E
- ❌ Schema modification (`ConceptConfig`, `GeneratedTask`)
- ❌ Generiranje zadataka koji nisu u distribucijskoj matrici §2

### 1.4 Strateške odluke (zaključene)

| # | Odluka | Vrijednost |
|---|---|---|
| 1 | Strategija | **Hibrid**: LLM batch za 100, ručno napiši `group_by` × 5 prije 2B-3 |
| 2 | Batch organizacija | **Po module** (M1 → M2 → M3 → M4 → M5 → M6 → M0 transverzalni) |
| 3 | Trošak | **Per-module soft cap $1.50**, abort module i analyze ako pređe |
| 4 | Pausing strategija | **Po module batch** — pause & fix YAML ako systematic pattern (>50% fail u batch-u) |
| 5 | Tool-use grounding | **Skip globalno** — 70% pass je acceptable za diplomski dataset |
| 6 | `group_by` strategija | **Ručno pisanje** nakon LLM batch — 5 zadataka × 15-20 min = 75-100 min |
| 7 | Max retries per task | **5** za agregacije (M2), **3** za sve ostalo (per 2B-1E memory note) |

---

## 2. Distribucijska matrica — što generiramo

Iz `faza-2a-plan.md` §2 + prilagodbe za hibrid pristup:

| Module | Koncepti | Tasks (raw) | Tasks (LLM) | Tasks (manual) |
|---|---|---|---|---|
| M1 — Osnove SELECT | select_basic, from_clause, where_filter, order_by, limit_offset, distinct | 21 | 21 | 0 |
| M2 — Agregacije | **group_by**, having_filter, agg_count, agg_sum_avg, agg_min_max | 19 | **14** | **5 (group_by)** |
| M3 — JOIN-ovi | inner_join, left_join, right_join, full_outer_join, cross_join, self_join, multi_table_join | 28 | 28 | 0 |
| M4 — DML | insert, update, delete | 11 | 11 | 0 |
| M5 — Subqueries | scalar_subquery, in_subquery, exists_subquery, correlated_subquery | 15 | 15 | 0 |
| M6 — Optimizacija | explain_plan, index_usage | 6 | 6 | 0 |
| M0 — Transverzalni | null_handling | 5 | 5 | 0 |
| **TOTAL** | **30** | **105** | **100** | **5** |

**Napomena:** `column_alias` i `join_condition` iz transverzalnih nemaju dedicated zadatke (matrica), koriste se kao secondary_concepts.

### 2.1 Per-module trošak estimacija (informira soft cap)

Bazirano na 2B-1D/E iskustvu (~$0.012-0.015 po pozivu s thinking, prosječno 2-3 attempts po task):

| Module | Tasks | Avg cost/task | Module budget | Soft cap |
|---|---|---|---|---|
| M1 (21) | 21 | $0.013 | $0.27 | $1.50 (komotna granica) |
| M2 (14, skip group_by) | 14 | $0.015 (više retry-eva) | $0.21 | $1.50 |
| M3 (28, najveći modul) | 28 | $0.013 | $0.36 | $1.50 |
| M4 (11, DML) | 11 | $0.014 | $0.15 | $1.50 |
| M5 (15) | 15 | $0.015 | $0.23 | $1.50 |
| M6 (6, hard tier, više thinking) | 6 | $0.018 | $0.11 | $1.50 |
| M0 (5) | 5 | $0.012 | $0.06 | $1.50 |
| **TOTAL (planned)** | **100** | — | **$1.39** | **$10.50** |

**Realistic total:** ~$2-4 s normal retry overhead. $5-10 worst case ako module retry storms.

**$1.50 per-module soft cap je 5-10× iznad expected** — daje buffer za retry storms bez global panic-a.

---

## 3. Dizajn — `--from-matrix` CLI flag

### 3.1 Tehnički zahtjev (iz 2A errata)

`generate_tasks.py` trenutno radi single-concept mode (`--concept where_filter --difficulty 2 --count 1`). 2B-2 treba batch mode koji čita distribucijsku matricu i generira sve.

### 3.2 Cilj

```python
# backend/scripts/generate_tasks.py (extended)

# NEW CLI options
parser.add_argument(
    "--from-matrix",
    type=Path,
    help="Path to distribution matrix YAML/JSON. Generates all tasks per matrix.",
)
parser.add_argument(
    "--module",
    type=int,
    choices=[0, 1, 2, 3, 4, 5, 6],
    help="Only generate tasks for specified module (used with --from-matrix).",
)
parser.add_argument(
    "--skip-concepts",
    type=str,
    default="",
    help="Comma-separated concept codes to skip (e.g. 'group_by').",
)
parser.add_argument(
    "--module-budget-usd",
    type=float,
    default=1.50,
    help="Per-module soft cap in USD. Abort module if exceeded.",
)
```

### 3.3 Distribucijska matrica fajl

Novi fajl: `backend/config/task_distribution.yaml`

```yaml
# Distribucijska matrica za Fazu 2B-2 batch generation
# Source: docs/faza-2a-plan.md §2
modules:
  1:
    name: "Osnove SELECT-a"
    concepts:
      select_basic: {tier: easy, distribution: {1: 2, 2: 1, 3: 1, 4: 0, 5: 0}}
      from_clause: {tier: easy, distribution: {1: 2, 2: 1, 3: 0, 4: 0, 5: 0}}
      where_filter: {tier: easy, distribution: {1: 2, 2: 2, 3: 1, 4: 0, 5: 0}}
      order_by: {tier: easy, distribution: {1: 1, 2: 1, 3: 1, 4: 0, 5: 0}}
      limit_offset: {tier: easy, distribution: {1: 1, 2: 1, 3: 1, 4: 0, 5: 0}}
      distinct: {tier: easy, distribution: {1: 1, 2: 1, 3: 1, 4: 0, 5: 0}}
  2:
    name: "Agregacije"
    concepts:
      group_by: {tier: medium, distribution: {1: 1, 2: 1, 3: 2, 4: 1, 5: 0}}  # SKIP via --skip-concepts
      having_filter: {tier: medium, distribution: {1: 0, 2: 1, 3: 2, 4: 1, 5: 0}}
      agg_count: {tier: medium, distribution: {1: 1, 2: 1, 3: 1, 4: 1, 5: 0}}
      agg_sum_avg: {tier: medium, distribution: {1: 0, 2: 1, 3: 1, 4: 1, 5: 0}}
      agg_min_max: {tier: medium, distribution: {1: 1, 2: 1, 3: 1, 4: 0, 5: 0}}
  # ... M3-M6, M0
```

### 3.4 Batch execution flow

```python
# Pseudocode za --from-matrix mode

def batch_generate_from_matrix(matrix_path: Path, module: int | None, skip_concepts: set[str],
                                module_budget_usd: float) -> dict:
    matrix = yaml.safe_load(matrix_path.read_text())
    pipeline = _build_pipeline(...)
    report = {"modules": {}, "total_cost": 0.0, "total_tasks": 0}

    modules_to_run = [module] if module else sorted(matrix["modules"].keys())

    for mod_num in modules_to_run:
        mod_data = matrix["modules"][mod_num]
        mod_report = {"name": mod_data["name"], "concepts": {}, "module_cost": 0.0,
                      "module_tasks": 0, "aborted": False}

        for concept_code, concept_data in mod_data["concepts"].items():
            if concept_code in skip_concepts:
                print(f"⊘ Skipping {concept_code} (--skip-concepts)")
                continue

            tier = concept_data["tier"]
            # Adjust max_retries by tier
            max_retries = 5 if mod_num == 2 else 3  # agregacije više retry-eva

            for difficulty, count in concept_data["distribution"].items():
                for i in range(count):
                    # Check module budget
                    if mod_report["module_cost"] >= module_budget_usd:
                        print(f"⚠ Module {mod_num} cost ${mod_report['module_cost']:.2f} ≥ "
                              f"${module_budget_usd:.2f} cap. Aborting module.")
                        mod_report["aborted"] = True
                        break

                    meta, raw_responses = generate_one(*pipeline, concept=concept_code,
                                                       difficulty=int(difficulty),
                                                       max_retries=max_retries, ...)
                    task_cost = sum(estimate_cost_usd(...) for r in raw_responses)
                    mod_report["module_cost"] += task_cost
                    mod_report["module_tasks"] += 1

                    # Per-task log
                    status = "validated" if meta and meta.status == "validated" else "failed"
                    print(f"  [{mod_num}/{concept_code}/d{difficulty}/{i+1}] {status} "
                          f"({len(raw_responses)} attempts, ${task_cost:.4f})")

                if mod_report["aborted"]:
                    break
            if mod_report["aborted"]:
                break

        report["modules"][mod_num] = mod_report
        report["total_cost"] += mod_report["module_cost"]
        report["total_tasks"] += mod_report["module_tasks"]

        # Per-module summary
        print(f"\n=== Module {mod_num} ({mod_data['name']}) ===")
        print(f"  Tasks: {mod_report['module_tasks']}, Cost: ${mod_report['module_cost']:.4f}")
        if mod_report["aborted"]:
            print(f"  ⚠ ABORTED — investigate before continuing")
            # NE break globally — daj korisniku odluku da li nastaviti
            input("Press Enter to continue to next module, Ctrl+C to abort all...")

    # Final report
    save_report(report, "data/generated_tasks/batch_report.json")
    return report
```

### 3.5 Decision tree per-module

```
Module batch završen → pass_rate X%, cost Y

┌── cost ≥ $1.50 → ⚠ ABORT MODULE
│              ├── Save partial results
│              ├── Manual investigation (per-task review u failed/)
│              ├── Fix YAML ili prompt ako systematic
│              └── Manual decision: retry module ili skip
│
├── pass_rate < 50% → ⚠ SYSTEMATIC FAIL
│              ├── Save partial results
│              ├── Identify common failure pattern
│              ├── Fix YAML or anti_patterns
│              └── Re-run module (cost resets)
│
└── pass_rate ≥ 50% → ✓ ACCEPTABLE
               ├── Save results
               ├── Log to batch_report.json
               └── Continue to next module
```

---

## 4. Dizajn — Manual `group_by` × 5

### 4.1 Approach

5 zadataka, ručno napisanih, u istom JSON formatu kao LLM-generirani. Save-aj direktno u `data/generated_tasks/validated/` (skip validator jer ti pišeš expected_result).

### 4.2 Distribucija (per matrica)

| Difficulty | Count | Realistic example |
|---|---|---|
| 1 | 1 | "Koliko postoji različitih kategorija?" — COUNT + GROUP BY trivial |
| 2 | 1 | "Broj proizvoda po kategoriji" — basic GROUP BY |
| 3 | 2 | "Prosječna cijena po kategoriji, samo gdje > 100" — GROUP BY + HAVING; "TOP 5 kategorija po broju proizvoda" — GROUP BY + ORDER BY + LIMIT |
| 4 | 1 | "Mjesečni revenue po kategoriji za 2024" — GROUP BY na više stupaca + agregacija |

### 4.3 Workflow per zadatak

1. Pročitaj `group_by.yaml` da znaš misconceptions koje target-iramo
2. Napiši `description` (hrvatski)
3. Napiši `expected_query` (PostgreSQL syntax)
4. **Pokreni query u sandbox-u manualno:**
   ```bash
   docker exec postgres-sandbox psql -U sandbox_admin -d ecommerce_v1 -c "<query>"
   ```
5. Copy output u `expected_result` field
6. Popuni metadata (`concept_code`, `module_number`, `tier`, etc.)
7. Save JSON u `data/generated_tasks/validated/group_by_d<N>_manual<i>.json`

### 4.4 JSON template

```python
# helper.py (one-off)
import json
import uuid
from pathlib import Path

def write_manual_group_by_task(
    difficulty: int,
    seq: int,
    description: str,
    expected_query: str,
    expected_result: list[dict],
    secondary_concepts: list[str] = None,
    target_misconception: str = "",
) -> Path:
    task_id = f"group_by_d{difficulty}_manual{seq:02d}"
    task = {
        "task_id": task_id,
        "concept_code": "group_by",
        "module_number": 2,
        "module_name": "Agregacije",
        "tier": "medium",
        "difficulty": difficulty,
        "description": description,
        "expected_query": expected_query,
        "expected_result": expected_result,
        "expected_row_count": len(expected_result),
        "secondary_concepts": secondary_concepts or [],
        "target_misconception": target_misconception,
        "generation_method": "manual",  # NEW field za audit trail
        "status": "validated",
        "validation_summary": {
            "level_1_syntax": "passed (manual)",
            "level_2_ast": "passed (manual)",
            "level_3_sandbox": "passed (manual)",
            "error_type": None,
        },
    }
    output_path = Path("data/generated_tasks/validated") / f"{task_id}.json"
    output_path.write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path
```

### 4.5 Schema compatibility check

**Critical:** `generation_method: "manual"` je novo polje. Provjeri:
- Jesu li `GeneratedTask` Pydantic field-evi strict (`extra="forbid"`)? Ako da, dodaj field u schema (uvjetno, +5 min)
- Validation tool (2B-1C) read-uje sve JSON-ove iz validated/ — verify da manual JSON-ovi loadiraju bez error-a

---

## 5. Tests

| Test fajl | Status | Broj testova |
|---|---|---|
| `backend/tests/test_generate_tasks.py` | **MODIFY** | +3-5 testa za `--from-matrix`, `--skip-concepts`, `--module-budget-usd` |
| `backend/tests/test_batch_report.py` | **NEW (opcionalno)** | +2-3 testa za report generation |

**Test count target:** 245 (baseline iz 2B-1C) + 3-8 nova = **~248-253 testova prolazi**.

**Critical:** Ne testiramo live API calls. Mock pipeline za testove (kao u 2B-1B).

---

## 6. Implementacijski redoslijed

### Korak 1: Pre-flight (10 min)

```bash
cd backend

# Verify clean baseline
git status
uv run pytest -q  # target: 245 passed

# Verify sandbox running
docker ps | grep postgres-sandbox

# Backup current generated_tasks directory
cp -r data/generated_tasks data/generated_tasks.pre-2b2-backup

# Verify ANTHROPIC_API_KEY u .env
grep ANTHROPIC_API_KEY .env
```

**Commit:** `chore(2b-2): pre-flight + backup pre-2b2 generated_tasks`

### Korak 2: `--from-matrix` CLI implementation (TDD-light, ~1h)

1. Napiši `backend/config/task_distribution.yaml` — kompletna matrica iz §2
2. Modify `backend/scripts/generate_tasks.py`:
   - Add CLI flags (`--from-matrix`, `--module`, `--skip-concepts`, `--module-budget-usd`)
   - Implement `batch_generate_from_matrix()` funkciju per §3.4
   - Refactor `main()` da podržava i single-task i batch mode
3. Napiši test-eve:
   - `test_load_distribution_matrix` — verify YAML parse
   - `test_skip_concepts_excludes_listed` — flag pass-through
   - `test_module_budget_aborts` — mock pipeline returning costs > budget
   - `test_max_retries_higher_for_module_2` — verify M2 dobije 5 retries
4. Run tests: 248-253 prolaze
5. **Dry-run sanity check:**
   ```bash
   uv run python -m scripts.generate_tasks \
       --from-matrix config/task_distribution.yaml \
       --module 1 --dry-run
   ```
   Verify output prikazuje ispravan plan (21 tasks za M1, koncepti, distribucija)
6. **Commit:** `feat(2b-2): --from-matrix CLI flag + task_distribution.yaml + 3-5 testova`
7. **Tag:** `git tag faza-2b-2-cli-ready && git push origin faza-2b-2-cli-ready`

### Korak 3: M1 batch (~30 min live + analiza)

```bash
cd backend

# Live API run za M1
uv run python -m scripts.generate_tasks \
    --from-matrix config/task_distribution.yaml \
    --module 1 \
    --module-budget-usd 1.50
```

1. Monitor real-time output (per-task status, costs)
2. Po završetku, pregledaj:
   - `data/generated_tasks/validated/` — koliko M1 zadataka pass-alo?
   - `data/generated_tasks/failed/` — koje su fail razlozi?
3. Calculate pass rate (validated_M1 / 21)
4. **Decision tree (§3.5):**
   - cost ≥ $1.50 → abort, investigate
   - pass_rate < 50% → fix YAML, retry M1
   - pass_rate ≥ 50% → continue
5. **Commit:** `feat(2b-2): M1 batch — X/21 validated, $Y cost`

### Korak 4: M2 batch (skip group_by) (~30 min live)

```bash
uv run python -m scripts.generate_tasks \
    --from-matrix config/task_distribution.yaml \
    --module 2 \
    --skip-concepts group_by \
    --module-budget-usd 1.50
```

1. Real-time monitor — M2 ima više retry budget (5 vs 3)
2. Expected: 14/14 attempts, ~10-12 pass (agregacije generally harder)
3. Decision tree per §3.5
4. **Commit:** `feat(2b-2): M2 batch (skip group_by) — X/14 validated, $Y cost`

### Korak 5: M3 batch (~45 min, najveći modul)

```bash
uv run python -m scripts.generate_tasks \
    --from-matrix config/task_distribution.yaml \
    --module 3 \
    --module-budget-usd 1.50
```

1. 28 tasks — najveći modul, monitor pažljivo
2. Pažnja na `multi_table_join`, `self_join`, `right_join`, `full_outer_join` (hard tier)
3. Decision tree per §3.5
4. **Commit:** `feat(2b-2): M3 batch — X/28 validated, $Y cost`

### Korak 6: M4 batch (DML mode) (~15 min)

```bash
uv run python -m scripts.generate_tasks \
    --from-matrix config/task_distribution.yaml \
    --module 4 \
    --module-budget-usd 1.50
```

1. DML mode (insert/update/delete) — automatic detection u SandboxRunner (iz 2B-1B)
2. 11 tasks, expected ~8-10 pass (pilot 2/2 INSERT u 2B-1B/D dobar signal)
3. **Commit:** `feat(2b-2): M4 batch (DML) — X/11 validated, $Y cost`

### Korak 7: M5 batch (subqueries) (~30 min)

```bash
uv run python -m scripts.generate_tasks \
    --from-matrix config/task_distribution.yaml \
    --module 5 \
    --module-budget-usd 1.50
```

1. 15 tasks, subqueries (`scalar`, `in`, `exists`, `correlated`)
2. `correlated_subquery` je hard tier — extended thinking essential
3. **Commit:** `feat(2b-2): M5 batch — X/15 validated, $Y cost`

### Korak 8: M6 batch (optimization) (~15 min)

```bash
uv run python -m scripts.generate_tasks \
    --from-matrix config/task_distribution.yaml \
    --module 6 \
    --module-budget-usd 1.50
```

1. 6 tasks, `explain_plan` + `index_usage`
2. `explain_plan` validator placeholder fix iz 2B-1E radi → expected good pass rate
3. **Commit:** `feat(2b-2): M6 batch — X/6 validated, $Y cost`

### Korak 9: M0 batch (transverzalni `null_handling`) (~10 min)

```bash
uv run python -m scripts.generate_tasks \
    --from-matrix config/task_distribution.yaml \
    --module 0 \
    --module-budget-usd 1.50
```

1. 5 tasks, `null_handling`
2. Mala batch, brzo gotova
3. **Commit:** `feat(2b-2): M0 batch — X/5 validated, $Y cost`

### Korak 10: LLM batch checkpoint

1. Calculate total: validated + failed + cost
2. Verify batch_report.json sadrži per-module statistics
3. Sanity check: ukupno ≤ 100 zadataka u validated/+failed/ (jer skipped group_by × 5)
4. **Commit:** `docs(2b-2): LLM batch complete — X/100 validated, total cost $Y`
5. **Tag:** `git tag faza-2b-2-llm-batch-complete && git push origin faza-2b-2-llm-batch-complete`

### Korak 11: Manual `group_by` × 5 (~75-100 min)

1. Read `backend/config/concepts/group_by.yaml` (refresh on misconceptions)
2. Connect to sandbox: `docker exec -it postgres-sandbox psql -U sandbox_admin -d ecommerce_v1`
3. Pisanje per §4.2 distribucije:
   - d=1: 1 zadatak
   - d=2: 1 zadatak
   - d=3: 2 zadataka
   - d=4: 1 zadatak
4. Workflow per §4.3 (write description → write query → run in sandbox → copy output → save JSON)
5. Per task, commit: `feat(2b-2): group_by d<N> manual<i> — <short description>`

### Korak 12: Schema verification + smoke test

1. Verify svi 105 zadataka u validated/+failed/:
   ```bash
   ls data/generated_tasks/validated/ | wc -l   # Expect: ~75-90
   ls data/generated_tasks/failed/ | wc -l       # Expect: ~10-25
   ls data/generated_tasks/validated/group_by_*manual*.json | wc -l   # Expect: 5
   ```
2. Verify Streamlit tool može loadirati svih 105:
   ```bash
   uv run streamlit run scripts/validation_tool/app.py
   ```
   - Open browser, verify Stats page prikazuje 105 total tasks
   - Verify manual group_by tasks pojavljuju u "validated" filter
3. **Commit:** `chore(2b-2): verify 105 tasks loaded in validation tool`

### Korak 13: Final wrapup

1. Write `docs/faza-2b-2-wrapup.md`:
   - Per-module breakdown (validated/failed/cost)
   - Total stats (105 tasks, X validated, Y failed, $Z cost)
   - Top failure patterns (top 3 razloga)
   - Manual group_by integration notes
   - Recommendations za 2B-3 manual validation strategy
2. Run final test suite: `uv run pytest -q` → **~248-253 testova prolaze**
3. **Commit:** `docs(2b-2): faza-2b-2 wrapup s batch report breakdown`
4. **Tag:** `git tag faza-2b-2-complete && git push origin faza-2b-2-complete`

---

## 7. Entry kriteriji (start 2B-2)

- [x] 2B-1C zaključena, tag `faza-2b-1c-complete` push-an
- [x] 245 testova baseline prolaze
- [x] Streamlit tool functional (verified u 2B-1C smoke test)
- [x] Sandbox kontejner running
- [x] ANTHROPIC_API_KEY u `.env`
- [x] Budget allocation: per-module $1.50 soft cap, total expected $2-4
- [x] 30 concept YAML-ova validni (iz 2B-1A/B + 2B-1E fixes)
- [x] Extended thinking always-on default u `generate_tasks.py` (iz 2B-1E)

## 8. Exit kriteriji (kraj 2B-2)

- [ ] `--from-matrix` CLI flag implementiran, testovi prolaze
- [ ] `backend/config/task_distribution.yaml` postoji (kompletna matrica)
- [ ] LLM batch generated 100 zadataka (validated + failed)
- [ ] Manual group_by × 5 zadataka u `validated/`
- [ ] Total: 105 zadataka u `data/generated_tasks/{validated,failed}/`
- [ ] `data/generated_tasks/batch_report.json` postoji
- [ ] Streamlit tool loadira svih 105 tasks bez error-a
- [ ] **~248-253 testova prolaze**
- [ ] Total LLM cost ≤ $10 (realistic $2-4)
- [ ] `docs/faza-2b-2-wrapup.md` postoji
- [ ] Tagovi push-ani

---

## 9. Risk register

| Rizik | Vjerojatnost | Impact | Mitigacija |
|---|---|---|---|
| Module 2 (agregacije) failure rate > 80% čak i bez group_by | Medium | Medium | Per-module soft cap aborts; manual investigation; potential YAML tuning |
| Per-module budget abort blokira progress | Medium | Low | Manual `input()` na abort omogućuje korisniku odluku continue/stop |
| Total cost premaši $10 hard mental cap | Low | High | Per-module soft cap je preventivan; ako se to dogodi, abort all i revise strategija |
| Validation tool ne loadira manual group_by JSON-ove (schema mismatch) | Medium | Low | Korak 12 smoke test catch-uje; fix schema ili JSON template |
| Sandbox connection drops mid-batch (e.g. Docker restart) | Low | High | SandboxRunner has retry logic; restart batch from last successful concept |
| `--from-matrix` ima bug koji ne abort-a module budget pravilno | Medium | Medium | Test coverage u Korak 2; manual monitoring during M1 (smallest realistic batch) |
| Manual group_by tasks imaju row_mismatch jer sandbox seed promijenio | Low | Medium | Run query in sandbox JUST PRIOR to copying expected_result |
| 2B-2 trošak ide $5-10 a ja sam očekivao $0.50 | High | Low | Već informed iz 2B-1D over-run pattern |

---

## 10. Tehnološki dug i otvorena pitanja za 2B-3

| Stavka | Status nakon 2B-2 | Rok |
|---|---|---|
| Re-generation failed tasks (custom prompts) | Defer u 2B-3 reactive | 2B-3 cleanup ili Faza 3 |
| Tool-use grounding migration | Skipped per Q5 odluka | Future (možda Faza 3) |
| Per-task cost monitoring (granularniji od per-module) | Skipped | Reactive ako post-batch analysis traži |
| Bulk re-generation flag (`--regenerate-failed`) | Out-of-scope | 2B-3 ili reactive |
| Distribution matrix YAML schema validation (Pydantic) | Out-of-scope | Faza 3 ako matrica raste |

---

## 11. Reference

- `docs/faza-2a-plan.md` §2 — original distribucijska matrica (105 zadataka)
- `docs/faza-2b-1d-wrapup.md` — failure patterns, prompt template lessons
- `docs/faza-2b-1e-wrapup.md` — 70% acceptable rationale, group_by failure rationale
- `docs/faza-2b-1c-wrapup.md` — validation tool capabilities (za smoke test)
- `backend/scripts/generate_tasks.py` — extension target
- `backend/config/concepts/group_by.yaml` — reference za manual writing
- Anthropic prompt caching docs — relevant za multi-batch optimization

---

## 12. Što slijedi nakon 2B-2

**2B-3 — Manual validation kroz Streamlit tool:**
- 105 tasks × 5-10 min review = 8-15h aktivnog rada
- Approved tasks → finalni dataset
- Rejected → dropped iz dataset-a (možda re-write u kasnijoj fazi)
- Needs-fix → manual edit u JSON ili re-generate s custom prompt
- Final tag: `faza-2b-complete` (cijela faza 2B zaključena)

**Onda:**
- Faza 3 — RecommenderAgent + BKT integration
- Faza 4 — UI prototype

---

*Plan kraj. Start point: `git checkout main && git pull && git checkout -b faza-2b-2-implementation && cd backend && git status && uv run pytest -q` (verify 245 passed).*
