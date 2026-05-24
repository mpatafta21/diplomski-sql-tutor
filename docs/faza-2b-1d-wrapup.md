# FAZA 2B-1D — Wrap-up

**Status:** Završeno s escalation odlukom (50% pass rate, ispod 80% target)
**Trošak ukupno:** $0.37 (over $0.15 plan hard cap — flag za 2B-2 budget)
**Trajanje:** ~1.5h aktivnog rada
**Završni tag:** `faza-2b-1d-complete`

---

## 1. Sažetak

Plan §3.4 success threshold od ≥80% pilot validation rate nije postignut. Dva prompt iteration cikla pokazala su sljedeće:

- **Iter 1 (10%):** Prompt fix-evi za schema/JSON parse problemi (Issue #1, #2) RADE perfektno — nula schema fail-ova, nula JSON parse error-a. Ali demaskirali su dublje semantičke probleme koje je 2B-1B pipeline maskirao.
- **Iter 2 (50%):** Extended thinking + execution-grounded checklist riješio polovicu novootkrivenih semantičkih problema. Preostali failure pattern je concept-specific.

Per plan §8 escalation path: 2B-1D zaključuje se s dokumentiranom escalation odlukom (vidi §5).

---

## 2. Iteration log

### Iter 1 — Prompt fix (Issue #1 + #2)

| Metric | Vrijednost |
|---|---|
| Pass rate | 1/10 (10%) |
| Cost | $0.12 |
| Validated | right_join d=3 |
| Schema/JSON fails | **0** (vs 10/10 u baseline) |
| Semantic fails | 27 (19 row_mismatch + 7 concept_not_detected + 1 prazan tekst) |

**Što je radilo:** Fix #1 (`secondary_concepts max=2`) i Fix #2 (`OUTPUT FORMAT strict` na kraj template-a) eliminirali ALL schema/JSON-parse fail-ove. Issue #1 i #2 su definitivno riješeni.

**Što je razotkrilo:** Model halucinira `expected_result` (predviđa krive redove) i piše SQL koji ne sadrži targetirani koncept (npr. EXPLAIN missing, scalar_subquery missing). Ovi su problemi bili u 2B-1B pilotu također, ali maskirani schema fail-ovima koji su dolazili ranije u pipeline-u.

**Root cause (otkriven između Iter 1 i Iter 2):** `extended_thinking` flag u `generate_tasks.py` ima default `difficulty >= 4`. Sve pilot zadatke s d=1-3 (8/10 zadataka) izvršavale su se BEZ thinking budget-a. Kad je Iter 1 prompt rekao "do so internally", model nije imao gdje raditi internu verifikaciju → preskočio ju je → halucinirao.

### Iter 2 — Extended thinking + verification checklist

| Metric | Vrijednost |
|---|---|
| Pass rate | **5/10 (50%)** |
| Cost | $0.25 |
| Validated | where_filter d=1, where_filter d=2, right_join d=2, right_join d=3, scalar_subquery d=2 |
| Fails | group_by d=2/3, scalar_subquery d=3, explain_plan d=3/4 |

**Promjene:**
- `pilot_run.py`: `extended_thinking=True` za sve pilot taske (override default-a `d>=4`)
- `user_template.md`: rephrase "INTERNI CHECKLIST" → "VERIFICATION CHECKLIST" koja explicitly nalaže rad u thinking block-u (step-by-step row walk, deterministic result derivation, syntactic concept check, essentiality check)

**Per-modul rezultat:**

| Modul | Koncept | d | Status |
|---|---|---|---|
| M1 | where_filter | 1 | ✓ |
| M1 | where_filter | 2 | ✓ |
| M2 | group_by | 2 | ✗ row_mismatch |
| M2 | group_by | 3 | ✗ row_mismatch + schema |
| M3 | right_join | 2 | ✓ |
| M3 | right_join | 3 | ✓ |
| M5 | scalar_subquery | 2 | ✓ |
| M5 | scalar_subquery | 3 | ✗ schema |
| M6 | explain_plan | 3 | ✗ primary_concept_not_detected |
| M6 | explain_plan | 4 | ✗ primary_concept_not_detected |

---

## 3. Failure pattern interpretacija (Iter 2)

Preostali fail-ovi nisu generički prompt issue — concept-specific su:

### 3.1 `explain_plan` (M6) — 2/2 fail
Model uporno ignorira "query MUST start with EXPLAIN" čak i kad je u eksplicitnoj checklist-i. Vjerojatno zato što je `EXPLAIN` perceptualno "modifier" oko običnog query-ja, ne "real" SQL koncept za model. **Fix kandidat:** Concept-specific hint u `explain_plan.yaml` few_shot_examples — sva 2 example-a moraju početi s `EXPLAIN (ANALYZE, FORMAT JSON)`. Ovo je 5-min fix, ali van scope-a 2B-1D.

### 3.2 `group_by` (M2) — 2/2 fail
Model halucinira aggregation rezultate (COUNT, SUM, AVG vrijednosti). Thinking budget nije dovoljan da bi izračunao agregaciju nad realnim podacima u glavi — invariants block nema dovoljno pre-computed values. **Fix kandidat:** Obogati `invariants_block` s explicit aggregations (`"COUNT(*) per category = {beverages: 12, electronics: 8, ...}"`) ili tool-use migration.

### 3.3 `scalar_subquery d=3` (M5) — 1/2 fail
Schema-level fail (Pydantic). Bez dubinske analize teško reći je li to model fail ili koncept je inherently teški na d=3.

### 3.4 Što je radilo (5/10 validated):
- where_filter, right_join: deterministički query-jevi nad sample podacima
- scalar_subquery d=2: simple lookup s LIMIT 1

---

## 4. Iteration log — kratki block

```
Iter 1 (prompt fix #1+#2):       10% pass (1/10), $0.12
                                  ↓ Schema/JSON fails eliminirani, semantic fails otkriveni
Iter 2 (extended thinking +       50% pass (5/10), $0.25
        verification checklist):  ↓ Generic problemi riješeni, concept-specific ostali
Outcome:                          Escalation u 2B-1E (vidi §5)
                                  Ukupni 2B-1D cost: $0.37
```

---

## 5. Escalation odluka

**Da li je escalation potreban?** DA — 50% pass rate je daleko od 80% threshold-a za 2B-2 batch generation. Ako bismo sad pokrenuli batch (~105 zadataka) s 50% pass rate, dobili bismo ~53 validated zadataka uz ~$0.45 trošak — neoptimalno za diplomski timeline.

**Sub-faza:** Novi **2B-1E** umjesto scope creep u 2B-1D. Razlog: clean tagging (2B-1D je o prompt iteration, 2B-1E bi bio o concept-specific tuning + opcionalno tool-use). Plan §5.3 default je također novi sub-fazu.

**Preporučeni scope za 2B-1E (≤4h):**

1. **Concept-specific YAML fix (2h):** Targetirano za 3 failing koncepta:
   - `explain_plan`: few_shot_examples moraju početi s `EXPLAIN` — promijeniti postojeća 2 primjera
   - `group_by`: obogati invariants_block s pre-computed aggregations (COUNT/SUM/AVG per kategorija)
   - `scalar_subquery`: dodati 1 deterministički d=3 primjer u few_shot
2. **Pilot rerun (~$0.06):** Ista 10-task batch, mjeri impact
3. **Decision point:**
   - ≥80% → 2B-1E gotov, pređi na 2B-1C
   - <80% → execute tool-use migration (4-5h, opisano u plan §5.1)

**Što ESCALATION NE radi:**
- Full tool-use migration prije nego što potvrdimo da concept-specific YAML fix nije dovoljan. Iter 2 je pokazao da 50% pass rate dolazi od generic fixes; preostalih 30 postotnih bodova vjerojatno se mogu uzeti s targetiranim concept tuning-om (jeftinije i brže od tool-use refactor-a).

**Tool-use migration kao Plan B (ako 2B-1E concept-fix < 70%):**
Vidi plan §5.1 za potpuni opis. Ključno: tool-use garantira JSON shape (kao naš Fix #2 već radi), ali NE rješava row_mismatch ili concept_coverage probleme. Bila bi potrebna `run_query_in_sandbox()` tool koji bi modelu vratio actual result da bi model napisao expected_result iz toga.

---

## 6. Top 3 lessons learned za 2B-2

1. **Extended thinking je esencijalan za task generation**, ne luxury. Default `difficulty >= 4` u `generate_tasks.py` je premalo agresivan. Preporuka za 2B-2: enable za sve task generation, ne samo pilot.

2. **Schema fail-ovi maskiraju semantic fail-ove.** Plan-time procjena pass rate-a iz 2B-1B (17%) bila je iluzija — kad su fix-evi eliminirali schema fail-ove, pravi semantic pass rate je 10%. **Implikacija za 2B-2:** ako planiramo batch od 105 zadataka, treba računati s pessimističnim pass rate-om dok god ne završimo 2B-1E.

3. **Concept-specific prompt overrides će biti potrebni za 30% koncepata.** Generic prompt nije dovoljan za `explain_plan` (prefix requirement), `group_by` (arithmetic grounding), i potencijalno druge koncepte koji nismo testirali u pilot-u (npr. `window_function`, `cte`). 2B-1E je prilika za sustavnu reviziju koncept YAML-ova.

---

## 7. Cost breakdown

| Stavka | Cost | Note |
|---|---|---|
| Iter 1 pilot | $0.12 | 10 tasks × max 3 retries = ~22 calls |
| Iter 2 pilot | $0.25 | + extended thinking budget (2000 tokens × 10 tasks) |
| **Total 2B-1D** | **$0.37** | Over $0.15 plan cap — flag za buduće planning |

**Zašto preko cap-a:** Plan je estimirano $0.04 po pilot rerun-u (10 tasks bez retries). Realnost: failed taskovi retry-aju 3x, što triplira API trošak. Iter 2 extended thinking dodaje ~25% više input tokena. Za 2B-2 (10x veći batch), realistic budget je $4-5, ne $0.50.

---

## 8. Što slijedi

**Sljedeća sub-faza: 2B-1E (NOVO)** — Concept-specific prompt tuning + opcionalno tool-use migration.

Nakon 2B-1E (≥80% pass):
1. **2B-1C** — Validation tool (Streamlit + SQLite) za human-in-the-loop validaciju
2. **2B-2** — Full generation 105 zadataka
3. **2B-3** — Manual validation kroz Streamlit tool

---

## 9. Git artefakti

| Artefakt | Lokacija |
|---|---|
| Iter 1 prompt fix commit | `123f484` |
| Iter 1 pilot rerun commit + tag | `682f0bb`, `faza-2b-1d-iter1-complete` |
| Iter 2 fix commit | `113cdc2` |
| Iter 2 pilot rerun commit | `49aff64` |
| Wrap-up + final tag | TBD, `faza-2b-1d-complete` |

| Local artifact (gitignored) | Lokacija |
|---|---|
| Baseline 2B-1B pilot (preserved) | `data/generated_tasks/pilot/pilot_report_baseline_2b1b.json` |
| Iter 1 pilot report | `data/generated_tasks/pilot/pilot_report_iter1.json` |
| Iter 2 pilot report | `data/generated_tasks/pilot/pilot_report_iter2.json` |
