# Faza 2B-2 — Batch log

Per-modul rezultati LLM batch generation runova. Data fajlovi (validated/+failed/+batch_report_M*.json) su gitignored — ovaj log služi kao audit trail.

## Sažetak (running total)

| Module | Status | Validated/Planned | Pass rate | Cost | Aborted |
|---|---|---|---|---|---|
| M1 (Osnove SELECT) | ✓ | 19/21 | 90.5% | $0.44 | no |
| M2 (Agregacije) | ⊘ skip → manual | 0/14 (LLM aborted) | 0% | $0.03 | systematic |
| M3 (JOIN-ovi) | — | — | — | — | — |
| M4 (DML) | — | — | — | — | — |
| M5 (Subqueries) | — | — | — | — | — |
| M6 (Optimizacija) | — | — | — | — | — |
| M0 (null_handling) | — | — | — | — | — |
| **Total (LLM)** | — | 19/86 | — | $0.47 | — |
| **+ Manual (group_by 5 + agregacije 14)** | — | 0/19 | — | $0.00 | — |
| **= 105 total** | — | 19/105 | — | $0.47 | — |

---

## M1 — Osnove SELECT-a (2026-05-30, ~17 min)

**Status:** ✓ ACCEPTABLE (pass rate 90.5% ≥ 50% threshold per plan §3.5)
**Pass rate:** 19/21 validated (90.5%)
**Cost:** $0.4437 (29% iskorišten od $1.50 soft cap)
**Trajanje:** ~17 minuta (17:05 → 17:22)

### Per-koncept breakdown

| Concept | Validated | Failed | Cost |
|---|---|---|---|
| select_basic | 4/4 | 0 | $0.069 |
| from_clause | 3/3 | 0 | $0.045 |
| where_filter | 4/5 | 1 | $0.102 |
| order_by | 2/3 | 1 | $0.071 |
| limit_offset | 3/3 | 0 | $0.077 |
| distinct | 3/3 | 0 | $0.080 |

### Failure patterns

- **where_filter d=?:** row_mismatch (Faker seed deterministic — model halucinirao stupce ili filtere)
- **order_by d=?:** row_mismatch (vjerojatno sort order ili tie-breaking issue)
- **Common retry pattern:** "Schema/parse error — Prazan tekst" pa retry succeeds — extended thinking output ponekad nema text content; retry pattern nije concerning

### Decision

**Continue to M2** — pass rate well above 50% threshold.

---

## M2 — Agregacije (2026-05-30, SKIPPED — defer to manual)

**Status:** ⊘ SYSTEMATIC FAIL → defer to manual (per plan §3.5)
**Pass rate:** 0/14 (LLM batch aborted nakon attempts round 1+2)
**Cost:** ~$0.03 (samo having_filter d=2 round 2 attempts; ostatak round 1 nije imao loga zbog `| tail -3`)
**Trajanje:** ~10 minuta combined obje round-e

### Failure pattern (round 2 log analysis)

Svi having_filter d=2 attempts (5 retries):
- Attempt 1: actual `broj_recenzija=6`, expected `3` — model halucinirao COUNT
- Attempt 2: actual `category_id=13, prosjecna_cijena=726.70`, expected `category_id=14, 623.45` — model expected different row entirely
- Attempt 3: actual `broj_proizvoda=6`, expected `7` — off by one
- Attempt 4: Prazan tekst (extended thinking output bez JSON-a)
- Attempt 5: identical row_mismatch kao attempt 3

**Dijagnoza:** model konzistentno halucinira agregatne vrijednosti (COUNT, SUM, AVG) — **isti pattern kao group_by u 2B-1E**. Domain hints s ground-truth vrijednostima nisu pomogli ni tamo, ne očekujemo da bi pomogli ovdje.

### Decision (user-confirmed)

**Manual write svih 14 M2 zadataka** u Koraku 11, alongside 5 group_by.
- Ukupni manual workload: **19 taskova** (5 group_by + 14 agregacije)
- Estimated: 19 × 15-20 min = **5-6.5 hours** ručnog pisanja
- LLM batch za M2 SKIP — $0 daljnjeg trošenja
- Sandbox-grounded expected_results garantiraju 100% accuracy

### Implikacije

- Plan §6 Korak 11 (5 group_by manual) → eksplandira na **19 manual tasks**
- Total LLM target: 86 (umjesto 100), Manual: 19 (umjesto 5)
- Cost saving od $0.20-0.40 koje bi M2 inače potrošio
