# Faza 2B-2 — Batch log

Per-modul rezultati LLM batch generation runova. Data fajlovi (validated/+failed/+batch_report_M*.json) su gitignored — ovaj log služi kao audit trail.

## Sažetak (running total)

| Module | Status | Validated/Planned | Pass rate | Cost | Aborted |
|---|---|---|---|---|---|
| M1 (Osnove SELECT) | ✓ | 19/21 | 90.5% | $0.44 | no |
| M2 (Agregacije, skip group_by) | — | — | — | — | — |
| M3 (JOIN-ovi) | — | — | — | — | — |
| M4 (DML) | — | — | — | — | — |
| M5 (Subqueries) | — | — | — | — | — |
| M6 (Optimizacija) | — | — | — | — | — |
| M0 (null_handling) | — | — | — | — | — |
| **Total (LLM)** | — | 19/100 | — | $0.44 | — |
| **+ group_by manual (Korak 11)** | — | 0/5 | — | $0.00 | — |
| **= 105 total** | — | 19/105 | — | $0.44 | — |

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
