# FAZA 2B-1E — Akcijski plan

**Diplomski rad:** Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju
**Sub-faza:** 2B-1E od 8 (umetnuta sub-podsekcija unutar Faze 2B-1, nakon 2B-1D)
**Cilj:** Concept-specific YAML tuning za 3 failing koncepta + extended thinking default change + pilot rerun (target ≥80% validated, fallback path na 70% i <70%)
**Trajanje:** 2-3h aktivnog rada
**Trošak:** ~$0.40 (realistic budget, hard cap $0.50)
**Predviđeni broj git commit-ova:** 5-7

---

## 1. Kontekst i ciljevi

### 1.1 Pozadina (zašto 2B-1E postoji)

2B-1D zaključen je s 50% pilot pass rate (5/10), ispod 80% target-a. Eskalacijska odluka per plan §5 = novi sub-task 2B-1E za concept-specific tuning prije tool-use migration.

**Što je 2B-1D potvrdio (lessons learned iz `docs/faza-2b-1d-wrapup.md`):**

| Lesson | Implikacija za 2B-1E |
|---|---|
| Fix #1 + #2 iz 2B-1D RADE perfektno (0 schema/JSON fails) | NE diraj generic prompt — fokusiraj se na concept-specific |
| Extended thinking je esencijalan, ne luxury (default `d>=4` premalo) | **Scope change:** mijenjamo default u `generate_tasks.py` |
| Failure pattern je concept-specific (explain_plan, group_by, scalar_subquery) | YAML config tuning targetiran |
| Tool-use migration ne rješava row_mismatch ili concept_coverage problem | Defer tool-use kao Plan B (samo ako <70% rezultat) |

### 1.2 Što ova sub-faza radi

1. **Extended thinking default change u `generate_tasks.py`** — promijeni trigger sa `difficulty >= 4` na `always-on` (ili `>= 2`, vidi §3.1)
2. **Concept-specific YAML tuning za 3 koncepta:**
   - `explain_plan.yaml` — few_shot examples počinju s `EXPLAIN`
   - `group_by.yaml` — invariants_block ili few_shot s pre-computed aggregations
   - `scalar_subquery.yaml` — dodati deterministički d=3 example
3. **Pilot rerun (10 tasks)** — apples-to-apples comparison s 2B-1D (isti 5 koncepata × 2 težine)
4. **Kondicionalna analiza i decision:**
   - ≥80% → prelazak na 2B-1C (Streamlit validation tool)
   - 70-79% → acceptable za 2B-2 s monitoring (clear documentation lessons za 2B-2 batch strategy)
   - <70% → eskalacija na novi sub-task 2B-1F (tool-use migration ili full prompt overhaul)

### 1.3 Što ova sub-faza NE radi

- ❌ Tool-use migration za `generate_tasks.py` — samo planning kao escalation path
- ❌ Validation tool (Streamlit + SQLite) — to je 2B-1C
- ❌ Generic prompt fix u `user_template.md` — 2B-1D je već adresiralo issue #1 + #2
- ❌ Per-modul prompt tuning (npr. agg-specific prompts) — samo per-koncept YAML
- ❌ Schema promjene u `ConceptConfig`, `GeneratedTask`
- ❌ Refactor `task_validator.py` ili `pilot_run.py` core logike
- ❌ Testiranje koncepata koji NISU u 2B-1D pilot scope-u (npr. `inner_join`, `cte`) — to je za 2B-2 monitoring

### 1.4 Strateške odluke (zaključene)

| # | Odluka | Vrijednost |
|---|---|---|
| 1 | Scope | **Proširi**: 3 koncept YAML fix + extended thinking default change u `generate_tasks.py` |
| 2 | Budget cap | **$0.50** realistic (3x worst case retry s thinking, naučeno iz 2B-1D over-run-a) |
| 3 | Success threshold | **Kondicionalni**: ≥80% → 2B-1C; 70-79% → acceptable za 2B-2 s monitoring; <70% → eskalacija na 2B-1F |
| 4 | Pilot rerun scope | **5 koncepata × 2 = 10 tasks** (apples-to-apples vs 2B-1D) |
| 5 | scalar_subquery d=3 | Generic fix (dodaj d=3 example), rerun, empirijski vidi |

---

## 2. Deliverables

### 2.1 Kod (1 modifikacija + 3 YAML fix-eva)

| Path | Status | Izmjena |
|---|---|---|
| `backend/scripts/generate_tasks.py` | **MODIFY** | Change extended_thinking default trigger (od `d>=4` na `always` ili `d>=2`) |
| `backend/config/concepts/explain_plan.yaml` | **MODIFY** | Few_shot examples počinju s `EXPLAIN` |
| `backend/config/concepts/group_by.yaml` | **MODIFY** | Invariants ili few_shot s pre-computed aggregations |
| `backend/config/concepts/scalar_subquery.yaml` | **MODIFY** | Dodati deterministički d=3 example |

### 2.2 Tests

| Test fajl | Status | Broj testova |
|---|---|---|
| `backend/tests/test_generate_tasks.py` (ako postoji) ili sl. | **MODIFY (uvjetno)** | +1-2 testa za novi extended_thinking default |
| Sve ostalo | Unchanged | 223 baseline mora prolaziti |

**Test count target:** 223 (baseline) + 0-2 nova = **223-225 testova prolazi**.

**Critical:** Concept YAML fixes ne razbijaju testove (YAML-ovi nisu unit-tested direktno, prolaze samo kroz `test_all_concept_yamls_validate` u 2B-1A integration test-u). Ako test taj `test_all_concept_yamls_validate` razbije — fix YAML, ne test.

### 2.3 Artefakti

| Path | Status | Sadržaj |
|---|---|---|
| `data/generated_tasks/pilot/pilot_report.json` | **OVERWRITE** | Najnoviji 2B-1E rerun rezultat |
| `data/generated_tasks/pilot/pilot_report_2b1e.json` | **NEW** | Backup 2B-1E rerun |
| `docs/faza-2b-1e-wrapup.md` | **NEW** | Wrap dokument |

### 2.4 Git artefakti

| Tag | Što označava |
|---|---|
| `faza-2b-1e-yaml-tuning-complete` | YAML tuning primijenjeni (commit-ovi prije pilot rerun-a) |
| `faza-2b-1e-complete` | Final tag — pilot rerun završen, decision dokumentirana |

### 2.5 Verification (Milestone)

- [ ] `generate_tasks.py` extended_thinking default izmijenjen
- [ ] 3 concept YAML-a fix-ana (`explain_plan`, `group_by`, `scalar_subquery`)
- [ ] Sva 30 YAML-a prolaze schema integration test
- [ ] Pilot rerun završen, `pilot_report.json` postoji
- [ ] Pass rate izračunat i kategorizovan (≥80% / 70-79% / <70%)
- [ ] `docs/faza-2b-1e-wrapup.md` postoji s decision dokumentacijom
- [ ] Tagovi `faza-2b-1e-yaml-tuning-complete` i `faza-2b-1e-complete` push-ani
- [ ] 223+ testova prolaze
- [ ] Trošak ≤ $0.50

---

## 3. Dizajn — Implementation detalji

### 3.1 Extended thinking default change

**Trenutno (pre-2B-1E):** `generate_tasks.py` koristi extended thinking samo za `difficulty >= 4`. 2B-1D Iter 2 eksplicitno override-ao to (`extended_thinking=True` za sve pilot tasks) i dobio 5x improvement.

**Cilj:** Promijeniti default tako da batch generation u 2B-2 dobije isto ponašanje kao pilot u 2B-1D Iter 2.

**Strateška mini-odluka za CC:** Two pristupa, jedan treba odabrati:

**Pristup A: Always-on extended thinking**
- Najsigurnije: garantira da se 2B-1D Iter 2 ponašanje primjenjuje na sve task generation
- Trošak: ~25% više input tokens po pozivu
- Za batch 105 zadataka: ~$0.50 extra cost (procjena)

**Pristup B: Threshold change s `d>=4` na `d>=2`**
- Štedi 30-40% troška za d=1 tasks (najjednostavniji)
- Rizik: d=1 zadaci mogu pasti ako thinking bio implicitno potreban (mali rizik za `where_filter d=1`, viši za `null_handling d=1`)

**Preporuka:** **Pristup A (always-on)** — naučeno iz 2B-1D je da thinking je esencijalan, ne luxury. Štednja na d=1 tasks je marginalna ($0.50 batch).

**Test impact:** Provjeri da li postoji test `test_extended_thinking_default_*` — ako da, update; ako ne, dodaj 1 test koji potvrđuje novo ponašanje.

### 3.2 Concept YAML fixes — smjernice

Ovo su smjernice za CC, ne copy-paste finalni YAML. CC prvo PROČITA postojeći YAML, pa modificira.

#### Fix #1: `explain_plan.yaml`

**Problem (iz 2B-1D wrapup §3.1):** Model ignorira "query MUST start with EXPLAIN" — perceptualno tretira EXPLAIN kao modifier oko običnog query-ja.

**Fix:** Update few_shot_examples — sva 2 example-a moraju jasno demonstrirati EXPLAIN prefix:

```yaml
# Trenutno (likely): few_shot examples imaju SELECT bez EXPLAIN
# Cilj: oba example-a počinju s EXPLAIN (ANALYZE) ili EXPLAIN (FORMAT JSON)

few_shot_examples:
  - difficulty: 3
    title: "..."
    description: "..."
    expected_query: "EXPLAIN (ANALYZE) SELECT * FROM orders WHERE customer_id = 42"
    expected_concepts: ["explain_plan"]
    targets_misconception: "..."
  - difficulty: 5
    title: "..."
    description: "..."
    expected_query: "EXPLAIN (ANALYZE, FORMAT JSON) SELECT ..."
    expected_concepts: ["explain_plan"]
    targets_misconception: "..."
```

**Dodatna mjera (uvjetno):** Razmotri dodati eksplicitan invariant u `anti_patterns`:
- "Query bez EXPLAIN prefix nije validan za explain_plan koncept"

#### Fix #2: `group_by.yaml`

**Problem (iz 2B-1D wrapup §3.2):** Model halucinira aggregation rezultate (COUNT, SUM, AVG vrijednosti) jer thinking budget nije dovoljan da izračuna agregaciju nad realnim podacima.

**Fix:** Obogati few_shot_examples i potencijalno custom invariants:

Two pristupa, oba moguća:

**A) Pre-computed aggregations u few_shot examples:**
Few_shot examples eksplicitno pokazuju expected_result s ispravnim aggregation vrijednostima — model uči pattern.

**B) Custom invariants u domain_hints ili anti_patterns:**
Dodaj hint poput:
- "Sandbox podaci: categories table ima 8 distinct values, products table ima ~50 rows raspoređeno preko kategorija."
- "Per-category counts: beverages=12, electronics=8, books=10, ..." (ako je determinističko iz Faker seed-a)

**Preporuka:** Kombinacija A + B. Ako sandbox data je deterministička (Faker seed), B je vrlo efikasan jer model dobije ground truth.

**Critical:** Ako uvodimo pre-computed aggregations u domain_hints, treba ih VERIFICATI protiv stvarne sandbox baze. Manual `psql` query da potvrdi vrijednosti.

#### Fix #3: `scalar_subquery.yaml`

**Problem (iz 2B-1D wrapup §3.3):** d=3 schema-level fail, bez deep analysis. Mogući uzrok: postojeća 2 few_shot examples su d=2 i d=4 — d=3 ima slabu referencu.

**Fix:** Dodati treći few_shot example, deterministički d=3:

```yaml
few_shot_examples:
  # ... postojeći d=2 ...
  # ... postojeći d=4 ili d=5 ...
  - difficulty: 3
    title: "..."
    description: "..."
    expected_query: "SELECT name FROM products WHERE price > (SELECT AVG(price) FROM products WHERE category_id = 1)"
    expected_concepts: ["scalar_subquery"]
    targets_misconception: "..."
```

**Smjernica:** Example treba biti **deterministički** (LIMIT 1, no JOIN, no GROUP BY complexity) tako da model lako prati pattern. Nemoj raditi d=3 example koji je u biti d=4 obfuscated.

### 3.3 Sandbox data verification (za group_by fix)

**Action item za CC:** Ako uvodimo pre-computed aggregations u `group_by.yaml` domain_hints, treba verifikovati:

```bash
# Pre-flight verification
cd backend
docker exec postgres-sandbox psql -U sandbox_admin -d ecommerce_v1 \
    -c "SELECT c.name, COUNT(*) FROM products p JOIN categories c ON p.category_id = c.id GROUP BY c.name ORDER BY c.name;"
```

Output ovog query-ja postaje source-of-truth za invariants block u `group_by.yaml`. Ako se vrijednosti razlikuju, fix-ati YAML ne sandbox.

### 3.4 Pilot rerun — apples-to-apples

**Identičan config kao 2B-1D:**
```bash
cd backend
uv run python -m scripts.pilot_run \
    --concepts where_filter,group_by,right_join,scalar_subquery,explain_plan \
    --output-suffix 2b1e
```

**Ako pilot_run.py nema --output-suffix iz 2B-1D Pristupa A:** Manualno rename `pilot_report.json` → `pilot_report_2b1e.json` nakon rerun-a.

### 3.5 Decision tree (post-rerun)

```
2B-1E pilot rerun → pass rate X%

┌── X ≥ 80% → ✓ HAPPY PATH
│              ├── Document u wrapup.md
│              ├── Tag faza-2b-1e-complete
│              └── Sljedeća faza: 2B-1C (Streamlit validation tool)
│
├── 70% ≤ X < 80% → ACCEPTABLE FOR 2B-2 WITH MONITORING
│              ├── Document u wrapup.md (eksplicitno: "concept fix-evi pomažu, ali ne dovoljno za strict 80%")
│              ├── Document recommendations za 2B-2 batch strategy (npr. focus retry budget na failing koncepte)
│              ├── Tag faza-2b-1e-complete
│              └── Sljedeća faza: 2B-1C (s informed expectation da batch može imati 25-30% fail rate)
│
└── X < 70% → ESCALATE TO 2B-1F
               ├── Document u wrapup.md (detailed analysis: što je radilo, što nije)
               ├── Recommend 2B-1F scope: tool-use migration ILI full prompt overhaul
               ├── Tag faza-2b-1e-complete (označava završetak pokušaja, ne success)
               └── Sljedeća faza: 2B-1F (novi sub-task)
```

**Granica 70% (vs 60% u 2B-1D):** Više je optimistic-na, ali odražava progress iz 2B-1D (10% → 50% s thinking + prompt). Ako 2B-1E s concept fix-evima donese 50-69%, znači concept tuning ne pomaže dovoljno — tool-use je real opcija. Ako 70%+, marginally acceptable.

---

## 4. Implementacijski redoslijed

**Workflow:** Pragmatičan, mali code change preko nekoliko commitова. Glavni rad je sandbox verification + YAML editing.

### Korak 1: Pre-flight (5 min)

```bash
cd backend

# Verify clean baseline
git status
uv run pytest -q  # target: 223 passed

# Backup 2B-1D pilot reports za historiju
ls data/generated_tasks/pilot/  # Verify postoje pilot_report_iter1.json i iter2.json
```

**Commit:** `chore(2b-1e): pre-flight verification`

### Korak 2: Extended thinking default change

1. Read `backend/scripts/generate_tasks.py`, identificiraj postojeći extended_thinking trigger logic
2. Change na Pristup A (always-on) ili Pristup B (d>=2) — preporuka: Pristup A
3. Update relevantne testove (ili dodaj 1-2 nova)
4. Run testovi: `uv run pytest -q` → 223-225 prolaze
5. **Sanity check:** `uv run python -m scripts.generate_tasks --concept where_filter --difficulty 1 --count 1 --dry-run` — verify thinking je enabled
6. **Commit:** `feat(2b-1e): extended thinking default always-on (lessons learned iz 2B-1D)`

### Korak 3: explain_plan.yaml fix

1. Read trenutni `backend/config/concepts/explain_plan.yaml`
2. Verify trenutna 2 few_shot examples — provjeri da li već imaju EXPLAIN
3. Modify few_shot examples — sva 2 počinju s `EXPLAIN (...) SELECT ...`
4. Opcionalno: dodaj anti_pattern entry
5. Run integration test: `uv run pytest backend/tests/test_concept_config.py::test_all_concept_yamls_validate -v`
6. **Commit:** `feat(2b-1e): explain_plan.yaml — sva few_shot examples počinju s EXPLAIN`

### Korak 4: group_by.yaml fix

1. **Pre-flight:** Manualni psql query za pre-computed aggregations (vidi §3.3)
2. Read trenutni `backend/config/concepts/group_by.yaml`
3. Modify few_shot examples i/ili domain_hints s ground-truth aggregation vrijednostima
4. Verify schema validation
5. Integration test prolazi
6. **Commit:** `feat(2b-1e): group_by.yaml — pre-computed aggregations u domain_hints`

### Korak 5: scalar_subquery.yaml fix

1. Read trenutni `backend/config/concepts/scalar_subquery.yaml`
2. Verify postojeća few_shot examples (difficulty list)
3. Add d=3 deterministički example (vidi §3.2 Fix #3)
4. Schema validation prolazi
5. **Commit:** `feat(2b-1e): scalar_subquery.yaml — dodan deterministički d=3 example`

### Korak 6: YAML tuning checkpoint

1. Run cijeli test suite: `uv run pytest -q` → 223-225 prolaze
2. **Tag:** `git tag faza-2b-1e-yaml-tuning-complete && git push origin faza-2b-1e-yaml-tuning-complete`

### Korak 7: Pilot rerun (live API, ~15 min)

```bash
cd backend
uv run python -m scripts.pilot_run \
    --concepts where_filter,group_by,right_join,scalar_subquery,explain_plan \
    --output-suffix 2b1e
```

1. Live API call execution
2. Pregledaj `data/generated_tasks/pilot/pilot_report_2b1e.json`
3. Izračunaj pass rate (validated_count / 10)
4. Note total cost (mora biti ≤ $0.50)
5. Identify failure modes (which concepts still fail, why)

**Hard cap monitoring:** Ako cost approaches $0.45 mid-rerun, abort i analyze partial results.

### Korak 8: Analiza i decision

Per §3.5 decision tree:

#### Sub-korak 8a: Ako ≥80% (HAPPY PATH)
1. Document u wrapup.md (summary + per-concept results)
2. Top 3 lessons learned for 2B-2 (npr. "thinking je essential", "group_by treba ground-truth aggregations")
3. **Commit:** `docs(2b-1e): pilot rerun X/10 validated, ≥80% target dostignut`
4. Skip na Korak 9 (final tag)

#### Sub-korak 8b: Ako 70-79% (ACCEPTABLE)
1. Document u wrapup.md (eksplicitno: "acceptable za 2B-2 s monitoring")
2. Recommendations za 2B-2 batch strategy:
   - Failing koncepti dobivaju veći retry budget
   - Manual review priority za failing koncepte u 2B-3
3. **Commit:** `docs(2b-1e): pilot rerun X/10 (acceptable), 2B-2 monitoring strategy`
4. Skip na Korak 9

#### Sub-korak 8c: Ako <70% (ESCALATE)
1. Detailed analysis u wrapup.md:
   - Što je radilo (iz 5/10 validated u 2B-1D), što je 2B-1E poboljšao, što nije
   - Per-task breakdown
   - Hypothesis za 2B-1F
2. **2B-1F scope recommendation:**
   - Tool-use migration (4-5h)
   - ALI: razmotri i "concept-specific prompt overrides" (potencijalno manji scope, ako problem je primarily prompt-engineering, not schema-fitting)
   - Predloži oba options s pros/cons
3. **Commit:** `docs(2b-1e): pilot rerun X/10, eskalacija na 2B-1F (tool-use ili prompt overhaul)`

### Korak 9: Final wrapup

1. Finaliziraj `docs/faza-2b-1e-wrapup.md`:
   - Outcome (happy/acceptable/escalate)
   - Iteration log (vidi 2B-1D wrapup §2 kao referencu)
   - Per-task results (10 tasks tablica)
   - Cost breakdown
   - Lessons learned
   - Recommendations za sljedeću sub-fazu
2. Run final test suite: `uv run pytest -q` → **223-225 passed**
3. **Tag:** `git tag faza-2b-1e-complete && git push origin faza-2b-1e-complete`

### Korak 10: Update memory file (uvjetno)

Update CC memory s 2B-1E outcome — ovisno o ishodu, memory može reflektirati:
- "2B-1E completed, idemo na 2B-1C"
- "2B-1E acceptable, idemo na 2B-1C ali 2B-2 ima monitoring strategy"
- "2B-1E eskalirao, sljedeća sub-faza je 2B-1F (tool-use ili prompt overhaul)"

---

## 5. Entry kriteriji (start 2B-1E)

- [x] 2B-1D zaključena, tag `faza-2b-1d-complete` push-an
- [x] 223 testova prolaze baseline
- [x] `data/generated_tasks/pilot/pilot_report_iter1.json` i `iter2.json` postoje (history)
- [x] Sandbox kontejner running, deterministička podatci (Faker seed)
- [x] `ANTHROPIC_API_KEY` u `backend/.env`
- [x] Budget: $0.50 hard cap (realistic na temelju 2B-1D over-run-a)
- [x] 30 concept YAML-ova u `backend/config/concepts/` (iz 2B-1B + 2B-1A)

## 6. Exit kriteriji (kraj 2B-1E)

### Happy path (≥80%):
- [ ] Extended thinking default izmijenjen u `generate_tasks.py`
- [ ] 3 YAML-a fix-ana (`explain_plan`, `group_by`, `scalar_subquery`)
- [ ] Pilot rerun pass rate ≥80%
- [ ] `docs/faza-2b-1e-wrapup.md` postoji s happy path documentation
- [ ] Tagovi push-ani

### Acceptable path (70-79%):
- [ ] Sve iz happy path-a
- [ ] Wrapup eksplicitno dokumentira "acceptable za 2B-2 s monitoring"
- [ ] 2B-2 batch strategy recommendations u wrapup-u

### Escalation path (<70%):
- [ ] Sve iz happy path-a (YAML changes su finalizirane bez obzira na ishod)
- [ ] Wrapup sadrži detailed analysis i 2B-1F scope recommendation
- [ ] Tag `faza-2b-1e-complete` označava završetak pokušaja, ne success

---

## 7. Risk register

| Rizik | Vjerojatnost | Impact | Mitigacija |
|---|---|---|---|
| Extended thinking always-on povećava cost > expected | Medium | Low | Hard cap $0.50; ako rerun premaši $0.45, abort |
| `group_by` ground-truth aggregations su pogrešne | Medium | Medium | Pre-flight psql verification (Korak 4 prvo korak) |
| `explain_plan` fix nije dovoljan (model i dalje ignorira EXPLAIN) | Medium | Medium | Detailed analysis u Iter 2 wrapup; potencijalno koncept-specific prompt overhaul u 2B-1F |
| Pilot rerun pass rate je niži od 2B-1D (regression) | Low | High | Document u wrapup, eskalacija na 2B-1F s revert option |
| 2B-1D Iter 2 pilot was anomaly (50% bio luck) | Low | Medium | Apples-to-apples comparison u 2B-1E daje signal; flaky LLM može distortirati 1-2 task points |
| YAML fix razbije postojeći test_all_concept_yamls_validate | Low | Low | Schema validation per YAML; fix YAML, ne test |
| scalar_subquery d=3 fix uzrokuje regression na d=2 ili d=5 | Low | Low | Apples-to-apples mjeri sve d-vrijednosti za scalar_subquery |

---

## 8. Tehnološki dug i otvorena pitanja

### Što ostaje za 2B-1F (uvjetno, samo ako eskalacija)

| Stavka | Procjena | Razlog |
|---|---|---|
| Tool-use migration za `generate_tasks.py` | 4-5h | Plan §5.1 iz 2B-1D wrapup-a |
| `run_query_in_sandbox()` tool za grounded expected_result | 2-3h | Wrapup §5: rješava row_mismatch globalno |
| Concept-specific prompt overrides (alternativa tool-use) | 2-3h | Manji scope, ali širi rizik za 2B-2 |

### Tech debt zabilježen za 2B-2

| Stavka | Status |
|---|---|
| Realistic batch budget revisited | $4-5 za 105 zadataka (ne $0.50 kao originalno) |
| Per-task retry budget allocation (failing koncepti dobivaju više) | Uvjetno, ako 2B-1E je 70-79% |
| Per-task cost monitoring (abort task ako košta više od X) | Defer u 2B-2 — nice to have, ne kritično |

---

## 9. Reference

- `docs/faza-2b-1d-wrapup.md` — pilot findings, lessons learned, escalation odluka
- `docs/faza-2b-1d-plan.md` §3.4, §5 — decision tree i escalation path template
- `backend/config/concepts/explain_plan.yaml`, `group_by.yaml`, `scalar_subquery.yaml` — fix target lokacije
- `backend/scripts/generate_tasks.py` — extended thinking default trigger
- `backend/scripts/pilot_run.py` — pilot pipeline iz 2B-1B s `--concepts` flag-om iz 2B-1D
- Anthropic prompt engineering docs: few-shot examples kvaliteta, ground-truth in prompt context

---

## 10. Što slijedi nakon 2B-1E

### Ako 2B-1E = happy path (≥80%):
- **2B-1C — Streamlit validation tool** (per originalni 2B-1 plan)

### Ako 2B-1E = acceptable (70-79%):
- **2B-1C — Streamlit validation tool**, ali 2B-2 batch strategy je informed s monitoring focus

### Ako 2B-1E = escalation (<70%):
- **2B-1F — Tool-use migration ILI prompt overhaul** (novi sub-task, scope ovisi o 2B-1E findings)
- Nakon 2B-1F, prelazak na 2B-1C

### Onda:
- **2B-2 — Full generation run za 105 zadataka** (realistic budget $4-5)
- **2B-3 — Manual validation kroz Streamlit tool**

---

*Plan kraj. Start point: `git checkout main && git pull && git checkout -b faza-2b-1e-implementation && cd backend && git status && uv run pytest -q` (verify 223 passed).*
