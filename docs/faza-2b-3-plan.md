# FAZA 2B-3 — Plan: Ručna validacija 103 SQL zadatka

**Tip faze:** Human-in-the-loop validation (NEMA implementacije koda kao primary deliverable)
**Primarni deliverable:** decisions u `manual_review.sqlite` + tagged final dataset + coverage report + wrapup
**Trošak:** $0 API (no LLM calls); primary cost je **vrijeme** (~9-13h active review)
**Završni tagovi:** `faza-2b-3-complete`, `faza-2b-complete` (zaključuje cijelu Fazu 2B)
**Tool:** Streamlit validation tool iz 2B-1C (functional, button-only navigacija, no keyboard shortcuts)

---

## 0. Reframe — zašto su odluke coupled

Master plan milestone: **„80+ zadataka u bazi, svaki testiran"**. Attrition matematika:

- 81 validated × realnih **85-95% human-approve** = **~69-77 approved** (sredina ~73)
- Da pogodiš **floor 80** → treba **~7 salvage-anih iz 22 failed**

**Posljedica:** salvage NIJE polish nego vjerojatno nužan da dosegneš milestone. Zato je tok jedinstven:
**validated prvo (izmjeri stvarni gap) → ciljani salvage da zatvoriš do 80.**

---

## 1. Locked odluke (iz planning chata — NE preispituje se)

| # | Odluka | Vrijednost |
|---|---|---|
| Q1 | Approval threshold | **Floor 80 approved + per-koncept min ~2** (ne globalni %) |
| Q2+Q5 | Redoslijed + sesije | **Validated→failed, 3 distribuirane sesije** |
| Q3 | Failed recovery | **Demand-driven** — salvage samo do floora 80, prioritet tanki koncepti |
| Q4 | Notes discipline | **Asimetrično** — reject/fix uvijek note; approve samo ako non-obvious |
| Q6 | Dataset finalizacija | **Tagged dataset** (`approved_by_human`, `generation_method`, `recovery_applied`) + **coverage report** s replacement candidates |
| (ranije) | Workflow | Strict per-task review, svaki individualno |
| (ranije) | Ghost entries | Skip (Streamlit tolerira, nema cleanup) |
| (ranije) | Bulk actions | Skip (per 2B-1C §1.4) |

---

## 2. Dataset za review (103 reviewable)

| Bucket | Count | Lokacija |
|---|---|---|
| Validated (62 LLM + 19 manual) | 81 | `data/generated_tasks/validated/` |
| Failed saved (18 2B-2 + 4 2B-2.5) | 22 | `data/generated_tasks/failed/` |
| **Reviewable total** | **103** | both dirs |
| Permanently phantom (out of scope) | 2 | `correlated_subquery d5`, `explain_plan d5` |

### Sastav 22 failed (bitno za salvage prioritet)

| Subset | Count | Karakteristika | Salvage izgledi |
|---|---|---|---|
| 2B-2.5 regen (svi M3 hard-tier) | 4 | `left_join d4` ×2, `left_join d5`, `right_join d4` — **svi row_mismatch, solidan query+description, halucinirani expected_result** (§11) | **Visoki** — prime re-run kandidati, počni salvage ovdje |
| 2B-2 original | 18 | Mixed failure types (row_mismatch / concept_not_detected / schema) | Triage per §5 |

> Phantom math reconciliran u §11: originalnih „20 phantom" = 14 M2 koncepata već ručno rewrittenih (lažni phantomi) + 6 pravih regen-needed. Od 6: 4 recovered, 2 permanently phantom.

### Validated po modulu (banking redoslijed)

| Tier | Modul/grupa | Count | Pass rate (2B-2) | Očekivani approve |
|---|---|---|---|---|
| **High-conf** | M2 agregacije (manual) | 14 | 100% | ~14 |
| **High-conf** | group_by (manual) | 5 | 100% | ~5 |
| **High-conf** | M1 (Osnove SELECT) | 19 | 90.5% | ~17-19 |
| **High-conf** | M4 (DML) | 9 | 81.8% | ~8-9 |
| | **High-conf subtotal** | **47** | | **~44-47** |
| **Risky** | M3 (JOIN-ovi) | 18 | 64.3% | ~13-16 |
| **Risky** | M5 (Subqueries) | 10 | 66.7% | ~6-8 |
| **Risky** | M6 (Optimizacija) | 4 | 66.7% | ~3 |
| **Risky** | M0 (null_handling) | 2 | 40% | ~1-2 |
| | **Risky subtotal** | **34** | | **~23-29** |
| | **Validated total** | **81** | | **~67-76** |

> Ako validated zatvori ≥80 sam — salvage je samo polish. Realnije: gap ~4-13 → ciljani salvage u S3.

---

## 3. Struktura sesija

### Sesija 1 (~2.5-3h) — Validated high-confidence (47)
- Redoslijed: manual (M2 14 + group_by 5) → M1 (19) → M4 (9)
- Tempo: čisti slučajevi, ~3-4 min/task
- Cilj: bank ~44-47 approved, kalibrirati rubriku na lakim slučajevima
- Sidebar filter: `module` + `decision=pending`

### Sesija 2 (~3.5-4.5h) — Validated risky (34)
- Redoslijed: M3 → M5 → M6 → M0; **unutar svakog: svi d≥4 zadnji** (najviša šansa halucinacije)
- Tempo: ~6-8 min/task; **re-run obavezan za sve agregacije i d≥4**
- Cilj: kumulativno ~70-77 approved + **izračunaj gap do 80** (ovo informira S3 salvage scope)
- Posebna pažnja (iz lessons learned):
  - `scalar_subquery` (M5) — 25% pass u batchu, halucinacija scalar values → re-run
  - `multi_table_join` (M3 d4) — 40% pass
  - `null_handling` (M0) — heterogeneous failures, samo 2, distribution gap risk

### Sesija 3 (~3-5h) — Failed triage + salvage + finalizacija
- **Počni salvage s 4 2B-2.5 M3 hard-tier** (`left_join d4` ×2, `left_join d5`, `right_join d4`) — §11 ih je pred-karakterizirao kao solidan query + halucinirani expected_result → near-certain re-run salvage. Bonus: bustaju M3 d4/d5 coverage (multi_table_join bio samo 40% pass).
- Onda triage preostalih 18 (vidi §5 decision tree)
- Salvage demand-driven: salvage-aj koliko treba da dosegneš **floor 80**, prioritet konceptima ispod **per-koncept min 2**
- Generiraj coverage report → identificiraj replacement candidates
- Export tagged dataset
- Wrapup + tagovi

**Ukupno: ~9-13h kroz 3 sesije** (unutar 9-17h estimate).

---

## 4. Per-task review rubrika (validated)

Za svaki validated zadatak provjeri redom:

1. **Izvršivost** — query izvršava čisto u sandboxu (re-run ako ima sumnje)
2. **Coverage** — query stvarno sadrži `primary_concept`, ne slučajno (npr. EXPLAIN prefiks prisutan, subquery prisutan)
3. **Točnost** — `expected_result` == actual sandbox output
   → **re-run OBAVEZAN** za: sve agregacije (group_by, having, agg_*), scalar_subquery, sve d≥4
4. **Jasnoća** — `description` jednoznačan, hrvatski jezik korektan, difficulty primjeren sadržaju
5. **Pedagoška vrijednost** — zadatak smisleno uči koncept (ne trivijalan, ne dvosmislen)

**Odluka:**
- Sve 5 OK → **approve**
- Točan ali slaba formulacija / minor fix → **needs-fix** (note s konkretnim fixom)
- Query ne uči koncept / nepopravljivo dvosmislen → **reject**

---

## 5. Failed salvage decision tree (22 failed)

```
Za svaki failed task:
│
├─ failure_type = row_mismatch (halucinirani expected_result)
│   │
│   ├─ query izvršava čisto U sandboxu I sadrži target koncept?
│   │   └─ DA → "Re-run query" → copy actual output → edit expected_result
│   │           → approve (recovery_applied=true, note OBAVEZAN)
│   │   └─ NE  → reject
│
├─ failure_type = concept_not_detected
│   └─ query strukturno ne uči koncept (npr. EXPLAIN missing, subquery missing)
│      → reject  (fix = ponovno autorsko pisanje = NIJE recovery)
│
└─ failure_type = schema / parse error
    └─ reject (rijetko salvageable; ne trošiti vrijeme)
```

**Prioritizacija salvage-a (demand-driven):**
0. **Start set:** 4 2B-2.5 M3 hard-tier failed — pred-karakterizirani u §11 kao row_mismatch + solidan query → idu direktno na re-run branch (near-certain salvage)
1. Provjeri coverage tablicu iz S1+S2 — koji koncepti su <2 approved?
2. Salvage prvo failed taskove koji popunjavaju te tanke koncepte
3. Stani kad dosegneš **floor 80 AND svaki koncept ≥2** (ili kad iscrpiš viable salvage)

---

## 6. Notes discipline (asimetrično)

| Odluka | Note? | Format |
|---|---|---|
| reject | **OBAVEZAN** | `[failure_code] kratki razlog` |
| needs-fix | **OBAVEZAN** | `[fix] konkretno što popraviti` |
| approve (recovery/edited/borderline) | **OBAVEZAN** | npr. `approved after re-run; expected_result edited` ili `borderline d4 accepted` |
| approve (čist trivial) | preskoči | — |

Notes na reject = sirovina za **failure-taksonomiju u radu** + listu regeneration kandidata.
Notes na salvage = nužni za **reproducibilnost** (mijenjao si artefakt).

---

## 7. Dataset finalizacija (Q6) — CC cleanup role

### 7.1 Tagged dataset export
Export script (CC piše) čita `manual_review.sqlite` decisions + task JSON → final dataset s poljima:

```json
{
  "task_id": "...",
  "module": 3,
  "primary_concept": "left_join",
  "difficulty": 2,
  "approved_by_human": true,        // bool — samo approve odluke
  "generation_method": "llm",       // "llm" | "manual"
  "recovery_applied": false,        // true ako expected_result editiran via re-run
  "title": "...", "description": "...",
  "expected_query": "...", "expected_result": [...]
}
```

Output: **tagged JSON manifest** + opcionalni **SQL seed** za `tasks` tablicu (Faza 3 production import, per master plan §Faza 2).

### 7.2 Coverage report (gap analysis)
Tablica **koncept × difficulty** s approved count po ćeliji:
- Markiraj ćelije s approved < per-koncept floor → **replacement candidates** za buduće faze
- Eksplicitno uključi 2 permanently phantom (`correlated_subquery d5`, `explain_plan d5`) kao poznate gapove
- Matrica = **live document** koji 2B-3 zatvara s gap-listom, NE mrtvi snapshot

---

## 8. Success kriteriji (definition of done)

- [ ] **≥80 approved** zadataka
- [ ] **≥2 approved po konceptu** (28 koncepata s dediciranim zadacima; `column_alias` + `join_condition` transversal — izuzeti)
- [ ] Svi 103 reviewani (decision != pending u SQLite)
- [ ] Coverage report generiran s replacement candidates
- [ ] Tagged dataset eksportiran (JSON manifest + opcionalni SQL seed)
- [ ] Wrapup `faza-2b-3-wrapup.md` napisan
- [ ] Tagovi `faza-2b-3-complete` + `faza-2b-complete`

---

## 9. Podjela rada

### Ti (ručno, primary)
- Pokreni Streamlit, review 103 taska kroz 3 sesije (§3)
- approve/reject/needs-fix + notes (§4, §5, §6)
- Re-run salvage workflow za viable failed (§5)

### Claude Code (cleanup only, no impl)
- Export script: decisions → tagged dataset (§7.1)
- Coverage report generator (§7.2)
- Opcionalno: JSON edits za salvage ako ne radiš ručno u Streamlitu
- Draft `faza-2b-3-wrapup.md`

---

## 10. Startup checklist (prije S1)

1. `git checkout -b faza-2b-3-validation`
2. Pokreni Streamlit validation tool (iz `backend/scripts/validation_tool/`)
3. Verificiraj da se učitava svih 103 file-a (81 validated + 22 failed)
4. Ghost DB entries — **ignoriraj** (locked: skip cleanup)
5. Sidebar: filter `decision=pending`, sort po modulu
6. Otvori coverage tracking (Stats page) za live monitoring approve count-a

> Napomena: nema batch generation operacija u 2B-3, pa SQLite lock rizik (2B-2 §4.6) nije relevantan.

---

## 11. Reference

- `faza-2b-2-wrapup.md` — per-modul breakdown, failure patterns, **§11 (2B-2.5 phantom regen)**: 4 recovered M3 hard-tier failed + 2 permanently phantom
- `faza-2b-1c-wrapup.md` — Streamlit tool capabilities (button nav, re-run, Stats page)
- `faza-2b-1e-wrapup.md` — agregacijska halucinacija, recovery rationale
- `faza-2b-1d-wrapup.md` — failure mode taksonomija (row_mismatch / concept_not_detected / schema)
- `faza-1-domenski-model.md` — 30 koncepata, prerequisite graf
- `diplomski-plan.docx` §Faza 2 — milestone „80+ zadataka", §Faza 3 — downstream (tasks tablica, EvaluatorAgent, BKT)
