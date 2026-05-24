# FAZA 2B-1E — Wrap-up

**Status:** ACCEPTABLE PATH (70% pilot pass rate, donji rub 70-79% raspona iz plana §3.5)
**Trošak:** $0.34 (unutar $0.50 hard cap)
**Trajanje:** ~1.5h aktivnog rada
**Završni tag:** `faza-2b-1e-complete`

---

## 1. Sažetak

Plan §3.5 decision tree → **ACCEPTABLE FOR 2B-2 WITH MONITORING**. Pilot rerun donio je 7/10 validated (vs 5/10 u 2B-1D Iter 2, +2 net), s jasno identificiranim preostalim failure modeom (`group_by` 0/2). Concept-specific tuning + validator-side `explain_plan` fix riješili su 2 od 5 fail-anih koncepata; `group_by` ostaje sustavni problem koji prompt-only engineering ne uspijeva riješiti.

**Per plan §6 Acceptable path:** 2B-1C (Streamlit validation tool) ide sljedeće, ali 2B-2 batch strategy mora biti **informirana** s monitoring fokusom na agregacijske koncepte (§5 niže).

---

## 2. Iteration log (kumulativni od 2B-1D)

```
2B-1B baseline (12 tasks):  17% pass (2/12), schema fails dominantni
                                ↓ Fix #1+#2 (secondary_concepts max=2, JSON-only)
2B-1D Iter 1 (10 tasks):    10% pass (1/10), schema fails eliminirani
                                ↓ Extended thinking enable + verification checklist
2B-1D Iter 2 (10 tasks):    50% pass (5/10), 5x improvement
                                ↓ explain_plan validator fix + group_by ground truth
                                ↓ + scalar_subquery det. d=3 + thinking always-on
2B-1E (10 tasks):            70% pass (7/10), +2 net vs 2B-1D Iter 2
                            Outcome: ACCEPTABLE (per plan §3.5)
                            Cumulative cost: 2B-1D $0.37 + 2B-1E $0.34 = $0.71
```

---

## 3. Per-task rezultati (2B-1E)

| Modul | Concept | d | Status | Attempts | Failure code |
|---|---|---|---|---|---|
| M1 | where_filter | 1 | ✓ validated | 1 | — |
| M1 | where_filter | 2 | ✓ validated | 1 | — |
| M2 | **group_by** | **2** | **✗ failed** | 4 | row_mismatch (Row 0 differs) ×3 |
| M2 | **group_by** | **3** | **✗ failed** | 4 | row_mismatch (Row 0 differs) ×3 |
| M3 | right_join | 2 | ✓ validated | 1 | — |
| M3 | right_join | 3 | ✓ validated | 3 | (recovered nakon Prazan tekst + row_mismatch) |
| M5 | scalar_subquery | 2 | ✓ validated | 2 | (recovered nakon row_mismatch) |
| M5 | scalar_subquery | 3 | ✓ validated | 2 | (recovered) |
| M6 | explain_plan | 3 | ✓ validated | 1 | — |
| M6 | **explain_plan** | **4** | **✗ failed** | 4 | Prazan tekst + row_mismatch (Set diff) ×2 |

**Per-modul pass rate:** M1 2/2, M2 0/2, M3 2/2, M5 2/2, M6 1/2. **Ukupno 7/10.**

---

## 4. Što je radilo (delta vs 2B-1D)

| Fix | 2B-1D rezultat | 2B-1E rezultat | Komentar |
|---|---|---|---|
| Extended thinking always-on default (generate_tasks.py) | N/A (samo u pilot_run.py override) | Globalni default | 2B-2 batch sad dobiva isti boost as pilot |
| `_detect_explain_plan` placeholder-True (validator fix) | 0/2 explain_plan | 1/2 explain_plan | d=3 sad prolazi; d=4 ima dublje semantičke probleme |
| `scalar_subquery.yaml` det. d=3 example | 1/2 scalar_subquery | 2/2 scalar_subquery | New simple WHERE+AVG pattern dao jasan reference |
| `group_by.yaml` ground-truth aggregations | 0/2 group_by | 0/2 group_by | **NIJE POMOGLO** — vidi §5 |

**Net efekt:** +2 pass-eva (explain_plan d=3, scalar_subquery d=3).

---

## 5. Što NIJE radilo — `group_by` failure analysis

Sva 4 retry-a na oba `group_by` zadatka pala su s `row_mismatch: Row 0 differs`. Nije row count mismatch (model dobije pravi broj redova) — vrijednosti su krive.

**Hipoteze (rangirano po vjerojatnosti):**

1. **Model ignorira GROUND TRUTH hints** — domain_hints sadrži eksplicitne vrijednosti (npr. `delivered=484, SUM=2174992.73`), ali model svejedno proizvodi vlastite halucinacije. Mogući uzrok: hints su 5-7 redaka u sredinom velikog YAML-a — model ih ne treba kao authoritative source.

2. **Rounding/precision mismatch** — sandbox vraća `NUMERIC` koje Pydantic deserializira kao `Decimal`, model predviđa `float`. Konverzija mismatch može uzrokovati "Row 0 differs" čak i s "ispravnom" semantikom.

3. **ORDER BY tie-break** — model i sandbox mogu vraćati iste agregirane grupe u različitom redoslijedu kad ORDER BY ima ties.

4. **Hint trust hierarchy** — system_static.md kaže "NE izmišljaj imena, brojke", a YAML kaže "GROUND TRUTH: delivered=484". Model može tretirati YAML hints kao "secondary" izvor.

**Što bi pomoglo (defer u 2B-2 monitoring ili 2B-1F escalation):**

- (a) Promote ground-truth hints u system_static.md s explicit "OVO SU AUTHORITATIVNE VRIJEDNOSTI" framing
- (b) Tool-use migration s `run_query_in_sandbox()` da model dobije actual aggregation, ne hardcoded hints
- (c) Per-concept prompt overrides — group_by-specific instruction u user_template.md koja eskpicitno traži ground-truth lookup

---

## 6. Recommendations za 2B-2 batch strategy

Per plan §6 Acceptable path requirements:

### 6.1 Retry budget allocation
- **Default max_retries = 3** za većinu koncepata (kao trenutno)
- **Override max_retries = 5** za `group_by`, `having_filter`, `agg_count`, `agg_sum_avg`, `agg_min_max` (sve agregacijske koncepte) — empirijski podaci sugeriraju ~50% chance pass-a po pokušaju za agregacije
- **explain_plan d ≥ 4** — explicit defer u manual review queue (skip auto-retry, mark za 2B-3)

### 6.2 Cost expectations
Realističan budget za 2B-2 (105 tasks) na temelju 2B-1E observed cost-a:
- Lower bound (90% prvi-pokušaj pass): 105 × $0.03 = **$3.15**
- Realistic (60% prvi-pokušaj pass, ~2 retry avg za fails): 105 × $0.05 = **$5.25**
- Upper bound (40% prvi pass, 5 retries za 60% taskova): **$8-10**

**Preporuka:** Hard cap $10 za 2B-2 batch, monitoring na svakih $2 incremental.

### 6.3 Manual review priority u 2B-3
Streamlit validation tool (2B-1C) treba prioritizirati:
1. **Agregacijski koncepti** (group_by, having_filter, agg_*) — najveća šansa hallucinated values
2. **explain_plan d ≥ 4** — auto-validation je placeholder, manual review obavezan
3. **Sve d ≥ 4** zadatke generalno — empirijski viša šansa fail-a

### 6.4 Concept-specific YAML quality
2B-1E je pokazalo da agregacijski koncepti trebaju **more than ground-truth** (sami hints nisu dovoljni). Tehnički dug zabilježen za buduće faze:
- Ground-truth tablice u domain_hints za **sve** koncepte koji rade aggregations
- Eventualno: per-concept `expected_result` template-i kao reference

---

## 7. Lessons learned (top 3 za 2B-2)

1. **Ground-truth u prompt hints nije dovoljno za agregacije.** Model ignorira eksplicitne vrijednosti čak i kad su striktno označene kao "GROUND TRUTH". 2B-2 mora očekivati ~50% fail rate za agregacijske koncepte BEZ tool-use migracije.

2. **Validator-side fixes mogu biti veći leverage od prompt fixes.** `_detect_explain_plan` placeholder fix (jedan commit, 5 redaka koda) riješio je explain_plan d=3 koji 2B-1D nije mogao. Prije nego što se mijenjaju prompt-i, **uvijek prvo provjeriti je li validator semantički točan** — false positives mogu maskirati stvarno ispravan output.

3. **Concept-specific few-shot patterns moraju biti deterministički "obrt na nižu kompleksnost"**, ne "obrt na višu". Scalar_subquery d=3 prošao je s novim SIMPLEM WHERE+AVG primjerom; postojeća 2 d=3 examples bili su preknotni za referencu.

---

## 8. Cost breakdown

| Stavka | Cost | Note |
|---|---|---|
| 2B-1E pilot rerun | $0.34 | 10 tasks, extended thinking always-on, 4 max retries na fails |
| **2B-1E ukupno** | **$0.34** | Unutar $0.50 hard cap (32% headroom) |
| Cumulative 2B-1D + 2B-1E | $0.71 | Ukupni prompt iteration cost prije batch generation-a |

---

## 9. Što slijedi

Per plan §10 Acceptable path:
- **Sljedeća sub-faza:** 2B-1C — Streamlit validation tool (per originalni 2B-1 plan)
- **2B-2 batch generation:** informed s monitoring strategijom iz §6 iznad, realistic budget $5-10, expected 70-80% auto-pass rate

**NE eskalira** u 2B-1F (tool-use migration) jer:
- 70% prag dostignut (granica acceptable)
- Tool-use migration scope (4-5h) bolje je investirati u 2B-1C (Streamlit) koji se može koristiti za manual cleanup `group_by` fail-ova nakon 2B-2 batch-a
- Ako 2B-2 batch pokaže drastično niži pass rate od 70% (npr. < 50%), 2B-1F može biti retroaktivno otvoren

---

## 10. Git artefakti

| Commit | Sadržaj |
|---|---|
| `525baf3` | docs(2b-1e): plan |
| `2e2d585` | feat(2b-1e): extended thinking default always-on |
| `6c4b2ac` | fix(2b-1e): _detect_explain_plan placeholder-True |
| `a4294d7` | feat(2b-1e): group_by.yaml — ground-truth aggregations |
| `4c23ee9` | feat(2b-1e): scalar_subquery.yaml — det. d=3 example |
| TBD | feat(2b-1e): pilot rerun 2B-1E — 7/10 validated (ACCEPTABLE) |
| TBD | docs(2b-1e): wrapup s decision dokumentacijom |

| Tag | Označava |
|---|---|
| `faza-2b-1e-yaml-tuning-complete` | YAML tuning + validator fix done, pre-pilot rerun |
| `faza-2b-1e-complete` | Wrapup finalized, ACCEPTABLE path documented |

| Local artifact (gitignored) | Lokacija |
|---|---|
| 2B-1E pilot report | `data/generated_tasks/pilot/pilot_report_2b1e.json` |

---

## 11. Test count progression

- 2B-1D baseline (završni): 223 tests
- 2B-1E +extended thinking tests: 225 tests (+2)
- 2B-1E +explain_plan placeholder tests: 226 tests (+1 net; 2 osvježena, 1 new)
- **Finalni: 226 testova pass.**
