# Faza 2B-3 Wrapup — Ručna validacija + dataset finalizacija

**Datum završetka:** 2026-06-22
**Grana:** `faza-2b-3-validation`
**Trošak:** $0 API (nema LLM poziva u 2B-3)

---

## 1. Pregled faze

Faza 2B-3 je provela ručnu validaciju 103 SQL zadatka (81 validated + 22 failed iz 2B-2/2B-2.5)
kroz 3 sesije, a zatim automatski salvage needs_fix taskova i finalizaciju dataseta.

**Success kriteriji — sve ispunjeno:**

| Kriterij | Rezultat |
|---|---|
| ≥80 approved zadataka | ✓ **83 approved** (85 SQLite − 2 ghost) |
| ≥2 approved po konceptu | ⚠ **26/28** — insert (1), right_join (1) ispod floora |
| Svi 103 reviewani (decision ≠ pending) | ✓ 0 pending |
| Coverage report generiran | ✓ `coverage_report.json` |
| Tagged dataset exportiran | ✓ `final_dataset.json` |
| Wrapup napisan | ✓ ovaj dokument |
| Tagovi | → sljedeći commit |

---

## 2. Dataset statistika

### Finalni dataset

| Metrika | Vrijednost |
|---|---|
| **Approved (final_dataset.json)** | **83** |
| LLM generirani | 64 (77%) |
| Ručno pisani | 19 (23%) |
| Recovery applied (re-run fix) | 16 (19%) |

### Tijek review sesija

| Sesija | Scope | Approved |
|---|---|---|
| S1 (high-conf validated) | M2 manual + M1 + M4 | ~41 |
| S2 (risky validated) | M3 + M5 + M6 + M0 | +25 = ~66 |
| S3 (salvage) | 24 needs_fix → 19 salvaged | +17 = **83** |

### Review decisions (SQLite, uključujući ghostove)

| Decision | Count |
|---|---|
| Approved | 85 |
| Rejected | 16 |
| Needs fix (ostalo) | 5 |
| Ghost entries (no JSON) | 3 |
| **Ukupno u SQLite** | 109 |

### Approved po modulu

| Modul | Koncept grupa | Approved |
|---|---|---|
| M0 | null_handling | 4 |
| M1 | Osnove SELECT | 15 |
| M2 | Agregacije | 19 |
| M3 | JOIN-ovi | 21 |
| M4 | DML + subquery | 12 |
| M5 | Subqueries | 7 |
| M6 | Optimizacija | 5 |
| **Ukupno** | | **83** |

---

## 3. Coverage matrica (approved / taskova)

| Koncept                      |   d1    |   d2    |   d3    |   d4    |   d5    | UKUPNO  |
|------------------------------|---------|---------|---------|---------|---------|---------|
| agg_count                    |    1    |    1    |    1    |    1    |    -    |    4    |
| agg_min_max                  |    1    |    1    |    1    |    -    |    -    |    3    |
| agg_sum_avg                  |    -    |    1    |    1    |    1    |    -    |    3    |
| correlated_subquery          |    -    |    -    |    1    |   1/2   |    1    |    3    |
| cross_join                   |    -    |    1    |    1    |    -    |    -    |    2    |
| delete                       |    -    |    1    |    2    |    1    |    -    |    4    |
| distinct                     |    1    | GAP(1)  |    1    |    -    |    -    |    2    |
| exists_subquery              |    -    |    1    | GAP(1)  |    1    |    -    |    2    |
| explain_plan                 |    -    |    -    |    1    |    1    | PHANTOM |    2    |
| from_clause                  |    2    |    1    |    -    |    -    |    -    |    3    |
| full_outer_join              |    -    |    -    |    1    |    1    |    1    |    3    |
| group_by                     |    1    |    1    |    2    |    1    |    -    |    5    |
| having_filter                |    -    |    1    |    2    |    1    |    -    |    4    |
| in_subquery                  |    -    |    1    |    1    |   1/2   |    -    |    3    |
| index_usage                  |    -    |    -    |    1    |    1    |    1    |    3    |
| inner_join                   |    1    |    1    |   1/2   |    1    |    -    |    4    |
| insert                       | GAP(1)  |    1    | GAP(1)  |    -    |    -    |    1  ⚠ |
| left_join                    |    -    |    1    |   1/2   |    1    |    -    |    3    |
| limit_offset                 |    1    |    1    |    1    |    -    |    -    |    3    |
| multi_table_join             |    -    |    -    |    2    |    2    |    1    |    5    |
| null_handling                |    1    | GAP(1)  |    2    |    1    |    -    |    4    |
| order_by                     | GAP(1)  |    1    |    1    |    -    |    -    |    2    |
| right_join                   |    -    | GAP(1)  |    1    | GAP(1)  |    -    |    1  ⚠ |
| scalar_subquery              |    -    |    1    |   1/2   | GAP(1)  |    -    |    2    |
| select_basic                 |   1/2   | GAP(1)  |    1    |    -    |    -    |    2    |
| self_join                    |    -    |    -    |    1    |   1/2   |    1    |    3    |
| update                       |    -    |    1    |    2    |    1    |    -    |    4    |
| where_filter                 |   1/2   |   1/2   |    1    |    -    |    -    |    3    |
|------------------------------|---------|---------|---------|---------|---------|---------|
| UKUPNO                       |   11    |   18    |   31    |   18    |    5    |   83    |

**Legenda:** broj = approved; `A/T` = approved/total (T > A); `GAP(T)` = 0 approved, T taskova;
`PHANTOM` = ćelija bez taskova (explain_plan d5 — neregenerabilna); `-` = kombinacija ne postoji.

---

## 4. Koncepti ispod floora i replacement candidates

### Ispod floora (< 2 approved)

| Koncept | Approved | Gap | Razlog |
|---|---|---|---|
| `insert` | 1 | 1 | insert_d1 (bez RETURNING, needs redesign), insert_d3 (non-deterministic PK) |
| `right_join` | 1 | 1 | right_join_d2 (title↔query semantički mismatch, needs redesign) |

### Replacement candidates za Fazu 3 (10 ćelija)

Ćelije s 0 approved ali postoje taskovi u datasetu (needs_fix/rejected — nisu salvageable):

`distinct d2`, `exists_subquery d3`, `insert d1`, `insert d3`,
`null_handling d2`, `order_by d1`, `right_join d2`, `right_join d4`,
`scalar_subquery d4`, `select_basic d2`

---

## 5. Salvage S3 — 19 od 24 needs_fix

Skripta `salvage_needs_fix.py` automatski obradila sve needs_fix taskove:

| Kategorija | Count | Akcija |
|---|---|---|
| re_run (query OK, krivi expected_result) | 17 | Sandbox re-run → update JSON → approve |
| direct_approve (validator bug) | 2 | Approve bez promjene JSON |
| description_fix (typo) | 1 | Fix description u JSON → approve |
| skip (treba redesign) | 4 | — |
| skip (empty result / pedagogical) | 1 | — |
| **Ukupno** | **24** | **19 salvaged** |

### Skippani (5 needs_fix koji ostaju):

| Task | Razlog |
|---|---|
| `right_join_d2` | Semantički mismatch title↔query — treba redesign |
| `insert_d1` | INSERT bez RETURNING → wrong_values_order nedetektabilan |
| `insert_d3` | RETURNING serial PK non-deterministic pod rollbackom |
| `in_subquery_d4_d28a` | Empty result — treba ubaciti data point |
| `order_by_d1` | Pedagoška formulacija nedostatna — treba ručni rewrite |

---

## 6. Ghost entries (3)

SQLite ima 3 „ghost" entry (record bez odgovarajućeg JSON fajla na disku):
`select_basic_d1_2fd7fa43`, `select_basic_d1_7b5d1138`, `select_basic_d1_89fe430e`.
Isključeni iz final_dataset.json i coverage_report.json.
Ostaju u SQLite (plan §10: ne čistimo). Nisu downstream issue — EvaluatorAgent
čita po task_id koji postoji u bazi, ne po SQLite review zapisu.

---

## 7. Deliverables

| Fajl | Lokacija | Opis |
|---|---|---|
| `final_dataset.json` | `data/generated_tasks/` | 83 tagged approved taska (gitignored) |
| `coverage_report.json` | `data/generated_tasks/` | Coverage matrica + gap lista (gitignored) |
| `salvage_needs_fix.py` | `backend/scripts/` | Salvage skripta (u gitu) |
| `export_tagged_dataset.py` | `backend/scripts/` | Export skripta (u gitu) |
| `generate_coverage_report.py` | `backend/scripts/` | Coverage report generator (u gitu) |

---

## 8. Što slijedi — Faza 3

**Prerequisite za Faza 3 (EvaluatorAgent + BKT):**
- `final_dataset.json` → seed SQL za `tasks` tablicu u glavnoj bazi
- Mapping: `module_number` → `module_id` (FK), `primary_concept` → `concept_id` (FK)
- Import skripta za `tasks` + `task_concepts` tablice

**Poznati gapovi koji trebaju rješenje u Fazi 3:**
- `insert`: 1 approved — potreban novi zadatak koji ne ovisi o RETURNING
- `right_join`: 1 approved — potreban novi zadatak (novi query, ne fix postojećeg)
- 10 replacement candidates za eventualno punjenje tankih ćelija

**Downstream:** EvaluatorAgent (Faza 3A) konzumira `final_dataset.json` ili
direktno iz `tasks` tablice po seedngu.
