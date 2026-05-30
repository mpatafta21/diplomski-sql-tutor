# Faza 2B-2 — Batch log

Per-modul rezultati LLM batch generation runova. Data fajlovi (validated/+failed/+batch_report_M*.json) su gitignored — ovaj log služi kao audit trail.

## Sažetak (running total)

| Module | Status | Validated/Planned | Pass rate | Cost | Aborted |
|---|---|---|---|---|---|
| M1 (Osnove SELECT) | ✓ | 19/21 | 90.5% | $0.44 | no |
| M2 (Agregacije) | ⊘ skip → manual | 0/14 (LLM aborted) | 0% | $0.03 | systematic |
| M3 (JOIN-ovi) | ✓ | 18/28 | 64.3% | $0.71 | no |
| M4 (DML) | ✓ | 9/11 | 81.8% | $0.21 | no |
| M5 (Subqueries) | — | — | — | — | — |
| M6 (Optimizacija) | — | — | — | — | — |
| M0 (null_handling) | — | — | — | — | — |
| **Total (LLM)** | — | 46/86 | — | $1.39 | — |
| **+ Manual (group_by 5 + agregacije 14)** | — | 0/19 | — | $0.00 | — |
| **= 105 total** | — | 46/105 | — | $1.39 | — |

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

---

## M3 — JOIN-ovi (2026-05-30, ~47 min)

**Status:** ✓ ACCEPTABLE (pass rate 64.3% ≥ 50% threshold per plan §3.5)
**Pass rate:** 18/28 validated (64.3%)
**Cost:** $0.7089 (47% iskorišten od $1.50 soft cap)
**Trajanje:** ~47 minuta (17:36 → 18:23) — najveći modul, hard tier dominant

### Per-koncept breakdown

| Concept | Validated/Planned | Cost | Note |
|---|---|---|---|
| inner_join | 4/5 (80%) | $0.136 | medium tier, ok |
| left_join | 3/6 (50%) | $0.076 | hard tier, NULL handling edge cases |
| right_join | 1/3 (33%) | $0.065 | hard tier, low pass |
| full_outer_join | 3/3 (100%) | $0.096 | hard tier, perfect ✓ |
| cross_join | 1/2 (50%) | $0.048 | hard tier |
| self_join | 4/4 (100%) | $0.095 | hard tier, perfect ✓ |
| multi_table_join | 2/5 (40%) | $0.192 | hardest, model struggles s 3+ join chain |

### Decision

**Continue to M4** — pass rate 64.3% well above 50% threshold. multi_table_join i right_join failures su očekivani (hard tier, kompleksne edge cases).

---

## M4 — DML (2026-05-30, ~7 min)

**Status:** ✓ ACCEPTABLE (pass rate 81.8% ≥ 50% threshold)
**Pass rate:** 9/11 validated (81.8%)
**Cost:** $0.2051 (14% iskorišten od $1.50 soft cap)
**Trajanje:** ~7 minuta — brzo zbog manjeg broja tasks i easy/medium tier

### Per-koncept breakdown

| Concept | Validated/Planned | Cost | Note |
|---|---|---|---|
| insert | 3/3 (100%) | $0.042 | easy tier, perfect ✓ |
| update | 3/4 (75%) | $0.074 | medium tier |
| delete | 3/4 (75%) | $0.088 | medium tier |

SandboxRunner DML mode (sandbox_readwrite role + auto-rollback) propagira through batch flag — bez issue-ova.

### Decision

**Continue to M5** — DML pipeline radi solidno. Update/delete fails su isolated cases, ne pattern.
