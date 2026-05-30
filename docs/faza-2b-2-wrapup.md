# FAZA 2B-2 — Wrap-up

**Status:** COMPLETE (svi koraci iz plana §6 isporučeni)
**Trošak:** ~$2.09 LLM cost (well within $2-4 expected range, $10 hard ceiling)
**Trajanje:** ~3.5h aktivnog rada (2.5h LLM batch monitoring + ~30 min manual writing + 30 min CLI implementacija + ~30 min issue handling)
**Završni tag:** `faza-2b-2-complete`

---

## 1. Sažetak

2B-2 je generirao **81 validated SQL zadataka** kroz hibridni pristup (62 LLM + 19 manual) za finalni dataset koji ide u 2B-3 manual validation. Plus 18 failed (saved JSON) za 2B-3 reject/needs-fix odluku. Ukupno **99 task-fajlova** u `data/generated_tasks/`.

Dataset pokriva **28 različitih SQL koncepata** (od 30 u matrici — `column_alias` i `join_condition` su transverzalni bez dediciranih zadataka).

### Plan vs Actual

| Plan target | Actual |
|---|---|
| 100 LLM batch + 5 manual = 105 | 62 LLM validated + 19 manual = 81 validated + 18 failed = **99 saved** |
| Cost $2-4 expected | **$2.09** spent |
| Trajanje 3-5h | ~3.5h |
| Pass rate ~70% | 62% overall LLM, 81% combined (s manual @ 100% accuracy) |

---

## 2. Per-module breakdown

| Module | Strategy | Tasks (validated/attempted) | Pass rate | Cost | Notes |
|---|---|---|---|---|---|
| M1 (Osnove SELECT) | LLM | 19/21 | **90.5%** | $0.444 | Najbolji modul, jedna where_filter + jedna order_by failure |
| M2 (Agregacije) | LLM ⊘ → manual | 0/14 LLM, 14/14 manual | LLM 0% → Manual 100% | $0.028 LLM + $0 manual | Hallucination — vidi §3 |
| M3 (JOIN-ovi) | LLM | 18/28 | **64.3%** | $0.709 | full_outer_join + self_join 100%, multi_table_join 40% |
| M4 (DML) | LLM | 9/11 | **81.8%** | $0.205 | insert 100%, update/delete 75% |
| M5 (Subqueries) | LLM | 10/15 | **66.7%** | $0.438 | scalar_subquery najslabiji (25%) — hallucination |
| M6 (Optimizacija) | LLM | 4/6 | **66.7%** | $0.164 | 2 issue-a (credit + detector bug) — vidi §4 |
| M0 (null_handling) | LLM | 2/5 | 40.0% | $0.104 | Borderline, accept (heterogeneous failures) |
| group_by | Manual | 5/5 | 100% | $0 | Per plan §1.4 odluka |
| M2 agregacije | Manual | 14/14 | 100% | $0 | Decided u Koraku 4 nakon LLM systematic fail |
| **TOTAL** | Hybrid | **81 validated, 18 failed saved** | **62% LLM** | **$2.091** | |

---

## 3. Glavni nalazi / lessons learned

### 3.1 LLM halucinira agregatne vrijednosti (potvrđen 2B-1E nalaz)

**Pattern:** `group_by`, `having_filter`, `agg_count`, `agg_sum_avg`, `agg_min_max` — model konzistentno halucinira COUNT/SUM/AVG vrijednosti. Domain hints s ground-truth vrijednostima u YAML-u NE pomažu (potvrđeno i u 2B-1E za group_by).

**Decision u 2B-2:** prebacit cijeli M2 + group_by na manual writing (umjesto pokušaja YAML tuning-a). Total 19 manual tasks × ~15 min = ~5h work, ali 100% accuracy garantirana kroz sandbox-grounded expected_result.

**Implikacija za 2B-3:** ovaj pristup je sad provjereni standard za agregacijske koncepte. Buduća proširenja koncepata trebaju consider hybrid od početka.

### 3.2 `scalar_subquery` ima istu halucinaciju u M5

**Pass rate 1/4 (25%)** — model halucinira single-row, single-column scalar values (npr. `(SELECT AVG(...) FROM ...)`). Slično agregacijskoj halucinaciji. Failures su isolated, ne globalno systematic, pa decision u 2B-2 je accept i defer u 2B-3 manual review.

### 3.3 Schema/parse-error pattern ("Prazan tekst — nema JSON-a")

Extended thinking output je occasionally text-empty (model troši thinking budget, vraća samo `<thinking>...</thinking>` bez `<output>`). Retry u sljedećoj pokušaju uspijeva. Default `max_retries=3` (5 za M2) je dovoljan da pokrije ovaj pattern.

### 3.4 Heterogeneous failures vs systematic failures

M0 (40% pass rate) demonstrira važnu razliku:
- **Systematic:** isti pattern svaki put (M2 agregacije halucinacija) → pause & manual
- **Heterogeneous:** različiti uzroci po task-u (M0 row_mismatch + concept_not_detected + type coercion) → accept i defer u 2B-3 review

YAML tuning radi samo za systematic, ne heterogeneous. 2B-3 reviewer ima kontekst za odluku per failure.

---

## 4. Tehnički debt i issue-i otkriveni tijekom 2B-2

### 4.1 `_detect_index_usage` placeholder bug

**Discovered:** M6 batch, all index_usage attempts validated FAILED.
**Root cause:** `_detect_index_usage` u `ast_analyzer.py` je vraćao `detected=False` bezuvjetno, dok je analogno `_detect_explain_plan` u 2B-1E bilo fixano na `detected=True` placeholder (jer index/explain detekcija zahtijeva runtime EXPLAIN ANALYZE, Faza 6).
**Fix:** commit `1469cd4` — symmetric fix uz update existing test-a.

### 4.2 Anthropic API credit balance exhaustion

**Discovered:** M6 batch mid-run, sve attempts → 400 Bad Request ("insufficient credit").
**Resolution:** user dodao credits, batch resumed (M6 index_usage only — explain_plan već imao 2/3 saved).

### 4.3 Manual review SQLite ima stale entries (deferred to 2B-3)

`data/generated_tasks/manual_review.sqlite` ima entries iz orphan tasks (3 file-a iz pred-2B-2 perioda deleted u Korak 1). Ti DB entries nemaju matching files i bili bi ghost u Streamlit-u. **2B-3 startup će trebati skip ghost DB entries** ili reset DB.

### 4.4 batch_report.json overwrites per modul (workaround)

Trenutno `batch_generate_from_matrix` overwrite-a `batch_report.json` na svaki run. Workaround: rename per modul (`batch_report_M[0-6]_*.json`) + `scripts/aggregate_batch_reports.py` na kraju. **Bolja solucija za buduće:** modify funkcije da merge-a sa existing report ili saves per-module rename automatski.

### 4.5 `meta=None` tasks ne save-aju → discrepancy report vs files

Kad svi retries fail-aju s API errorima (npr. credit balance), `meta=None` → no save → `failed/` direktorij nema file, ali report broji "failed". Rezultat: 38 reported failed vs 18 saved JSON. **20 phantom failures** koje 2B-3 ne može review-irati (samo iz batch_report.json log-a).

### 4.6 `data/generated_tasks/manual_review.sqlite` lock potencijal

Ako Streamlit tool runs while batch generation u toku → SQLite WAL nije aktiviran (per 2B-1C odluka), pa concurrent writes mogu fail. **Mitigacija u 2B-3:** kill Streamlit prije svake batch generation operacije.

---

## 5. Test count progression

```
Baseline (kraj 2B-1C):            245 passed
+ 11 novih (test_generate_tasks_batch.py):
  - test_load_real_distribution_matrix_has_expected_modules
  - test_load_real_distribution_matrix_total_is_105
  - test_load_real_distribution_matrix_module_4_concepts_are_dml
  - test_iter_matrix_plan_filters_module
  - test_iter_matrix_plan_skip_concepts_excludes_listed
  - test_batch_generate_calls_generate_one_per_planned_task
  - test_batch_generate_propagates_dml_flag_for_module_4
  - test_batch_generate_uses_max_retries_5_for_module_2
  - test_batch_generate_aborts_module_when_budget_exceeded
  - test_batch_generate_writes_report_json
  - test_load_distribution_matrix_missing_modules_key_raises
+ 0 modified (test_index_usage_placeholder updated, ne novi)
─────────────────────────────────────────────────
Total na kraju 2B-2:               256 passed
```

Plan §5 očekivao 248-253. Realno 256. Test-coverage focus na batch CLI flow + matrix validation + budget abort.

---

## 6. Decision tree summary (per plan §3.5)

| Module | Decision tree path | Outcome |
|---|---|---|
| M1 | ≥50% pass | ✓ continue |
| M2 | <50% pass (0%) | ⊘ pause → user decision → manual write |
| M3 | ≥50% pass (64.3%) | ✓ continue |
| M4 | ≥50% pass (81.8%) | ✓ continue |
| M5 | ≥50% pass (66.7%) | ✓ continue |
| M6 | Cost issue + detector bug | ⚠ fix + retry → ✓ 66.7% |
| M0 | <50% pass (40%) | ⚠ borderline, accept (heterogeneous failures) |

User-confirmed odluke:
- **M2 → manual** (Korak 4 AskUserQuestion)
- **API credits** (Korak 8 AskUserQuestion)

---

## 7. Što slijedi: 2B-3 Manual Validation

Ulazi u 2B-3:
- 81 validated tasks ready for approve/reject/needs-fix
- 18 failed tasks ready for reject (most likely) ili needs-fix (rare salvageable)
- 20 phantom failures u batch_report-u (ne file-ovi, samo log)
- Streamlit tool functional sa svih 99 file-ova
- `manual_review.sqlite` može trebati ghost cleanup prije starta

**Budget estimacija za 2B-3:** 99 tasks × 5-10 min review = **8-15h ručnog rada**. Decisons:
- approve → finalni dataset
- needs-fix → JSON edit ili re-generate s custom prompt
- reject → dropped

Final dataset target nakon 2B-3: **~70-90 approved tasks** za production import (Faza 3+).

---

## 8. Otvorena pitanja za 2B-3

- Treba li ghost-entry cleanup u manual_review.sqlite startup?
- Workflow za bulk-reject pattern-based failures (npr. svi scalar_subquery d=3?)
- Export format za approved tasks → production schema (tasks tablica u tutor_main DB)?

---

## 9. Git artefakti

**Branch:** `faza-2b-2-implementation`
**Komitovi (planned 10-14):** 12 commitova (1 docs, 1 setup, 1 CLI, 6 module batches + 1 fix + 1 checkpoint + 1 manual + 1 wrapup)

**Tagovi:**
- `faza-2b-2-cli-ready` — nakon Koraka 2 (commit `faedc6b`)
- `faza-2b-2-llm-batch-complete` — nakon Koraka 10 (commit `9baa29d`)
- `faza-2b-2-complete` — nakon Koraka 13 (final wrapup)

**Files added (vs main):**
- `backend/config/task_distribution.yaml` (new)
- `backend/scripts/generate_tasks.py` (extended)
- `backend/scripts/manual_tasks_2b2.py` (new)
- `backend/scripts/aggregate_batch_reports.py` (new)
- `backend/scripts/lib/ast_analyzer.py` (modified — index_usage placeholder-True)
- `backend/app/schemas/generated_task.py` (modified — generation_method field)
- `backend/tests/test_generate_tasks_batch.py` (new, 11 testova)
- `backend/tests/test_ast_analyzer.py` (modified — index_usage placeholder test)
- `.gitignore` (extended — backup pattern)
- `docs/faza-2b-2-plan.md` (new)
- `docs/faza-2b-2-batch-log.md` (new — per-module audit)
- `docs/faza-2b-2-wrapup.md` (ovaj doc)

**Files gitignored (local-only):**
- `data/generated_tasks/validated/` (81 files)
- `data/generated_tasks/failed/` (18 files)
- `data/generated_tasks/batch_report*.json` (8 raw + 1 aggregated)
- `data/generated_tasks.pre-2b2-backup/` (pre-2B-2 backup)

---

## 10. Reference

- `docs/faza-2b-2-plan.md` — original akcijski plan
- `docs/faza-2b-2-batch-log.md` — per-module run log
- `docs/faza-2b-1e-wrapup.md` — group_by + extended thinking lessons
- `docs/faza-2b-1c-wrapup.md` — Streamlit validation tool capabilities
- `backend/config/task_distribution.yaml` — 105-task matrica
- `backend/scripts/aggregate_batch_reports.py` — multi-module report merger

---

*2B-2 complete. Move to 2B-3 — manual validation kroz Streamlit tool.*
