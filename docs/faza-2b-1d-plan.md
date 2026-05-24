# FAZA 2B-1D — Akcijski plan

**Diplomski rad:** Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju
**Sub-faza:** 2B-1D od 7 (umetnuta sub-podsekcija unutar Faze 2B-1, prije 2B-1C)
**Cilj:** Fix pilot fail-ova kroz prompt iteraciju (target ≥80% validated u pilot rerun) prije batch generation-a u 2B-2
**Trajanje:** 1.5-3h aktivnog rada (1.5h ako iter 1 prolazi, 3h ako stigne do iter 2 + escalation prep)
**Trošak:** ~$0.06-$0.12 (2 rerun-a × ~$0.04 + retry buffer)
**Predviđeni broj git commit-ova:** 4-7

---

## 1. Kontekst i ciljevi

### 1.1 Pozadina (zašto 2B-1D postoji)

Pilot run u 2B-1B dao je rezultat **2/12 validated (17% pass rate)** — daleko ispod batch-spremne kvalitete. Identificirana su 2 prompt template issue-a (handoff iz 2B-1B):

| Issue | Lokacija | Pogađa |
|---|---|---|
| #1: `secondary_concepts max=2` constraint nije u promptu | `backend/config/prompt_templates/user_template.md` | Svi koncepti |
| #2: Plain-text scratchpad umjesto JSON-only output | `backend/config/prompt_templates/user_template.md` | 80% pilot fail-ova (5 koncepata) |

INSERT path (DML) je solid (2/2 pass) — issue #2 je specifičan za free-text generation flow gdje model "razmišlja u markdownu" prije JSON-a.

2B-1D fiksira ove issue-e prije nego što trošimo $0.50+ na batch generation u 2B-2.

### 1.2 Što ova sub-faza radi

1. **Iter 1: Prompt-only fix** — dva targeted fix-a u `user_template.md` (issue #1 + #2)
2. **Pilot rerun (10 tasks)** — 5 problematičnih koncepata × 2 težine, mjeri prvi-pokušaj pass rate
3. **Analiza Iter 1** — summary failure modes (top 3 razloga, per-concept pass rate)
4. **Iter 2 (uvjetno)** — ako Iter 1 < 80%: targeted fix na preostale failure modes
5. **Pilot rerun #2 (uvjetno)** — analizira detaljno (per-task breakdown)
6. **Escalation (uvjetno)** — ako Iter 2 < 80%: priprema za tool-use migration kao novi sub-task (2B-1E ili scope creep u 2B-1D)

### 1.3 Što ova sub-faza NE radi

- ❌ Tool-use migration za `generate_tasks.py` — samo planiranje ako prompt-only ne uspije (escalation path)
- ❌ Validation tool (Streamlit) — to je 2B-1C, sljedeća sub-faza
- ❌ Full batch generation — to je 2B-2
- ❌ Schema promjene u `ConceptConfig`, `GeneratedTask` — samo prompt + pilot config
- ❌ Concept-specific fine-tuning per module (npr. agg-specific prompts) — generic prompt fix prvo
- ❌ Refactor `task_validator.py` — ali može trebati malu izmjenu (vidi §4.3) ako fail reporting nije dovoljan za analizu

### 1.4 Strateške odluke (zaključene)

| # | Odluka | Vrijednost |
|---|---|---|
| 1 | Strategija | Hibrid: prompt-only prvo → tool-use kao escalation ako Iter 2 < 80% |
| 2 | Pilot rerun scope | 5 problematičnih koncepata × 2 težine = 10 tasks (ne 12 kao u 2B-1B) |
| 3 | Success threshold | **80% (8/10 validated)** triggera prelazak u 2B-1C |
| 4 | Max iteracija | 2 (Iter 1 → analiza → Iter 2 → escalation/done) |
| 5 | Failure analiza | Hibrid: summary nakon Iter 1, detailed nakon Iter 2 (samo ako se aktivira) |
| 6 | Iteration log | Block u `docs/faza-2b-1d-wrapup.md` (5-10 redaka po iteraciji) |

---

## 2. Deliverables

### 2.1 Kod (1-3 modifikacije, 0 novih fajlova)

| Path | Status | Izmjena |
|---|---|---|
| `backend/config/prompt_templates/user_template.md` | **MODIFY** | Fix #1 + #2 (Iter 1), targeted fixes (Iter 2 if needed) |
| `backend/scripts/pilot_run.py` | **MODIFY (možda)** | Dodaj `--concepts` CLI flag ILI 2B-1D specific config (vidi §3.3) |
| `backend/scripts/lib/task_validator.py` | **MODIFY (uvjetno)** | Samo ako pilot_report.json ne razlikuje fail razloge dovoljno granularno za analizu (vidi §4.3) |

**Naglasak:** Plan NE specificira točan format fix-a u `user_template.md`. Claude Code mora **prvo pročitati postojeći template**, identificirati pravi injection point, pa pozicionirati fix prema §4.1 smjernicama.

### 2.2 Tests

| Test fajl | Status | Broj testova |
|---|---|---|
| `backend/tests/test_pilot_run_smoke.py` | **MODIFY (uvjetno)** | +1-2 testa ako pilot_run.py dobije `--concepts` flag |
| Sve ostalo | Unchanged | 220 baseline testova mora prolaziti |

**Test count target:** 220 (baseline) + 0-2 nova = **220-222 testova prolazi**.

**Critical:** Iter 1 fix u `user_template.md` ne bi trebao razbiti postojeće testove. Ako razbije — issue je u test fixture stale, ne u promptu (popraviti fixture, ne prompt).

### 2.3 Artefakti

| Path | Status | Sadržaj |
|---|---|---|
| `data/generated_tasks/pilot/pilot_report.json` | **OVERWRITE** (s timestamp suffix-om za history) | Najnoviji pilot rerun rezultat |
| `data/generated_tasks/pilot/pilot_report_iter1.json` | **NEW** | Backup Iter 1 rezultata |
| `data/generated_tasks/pilot/pilot_report_iter2.json` | **NEW (uvjetno)** | Iter 2 rezultat ako se aktivira |
| `docs/faza-2b-1d-wrapup.md` | **NEW** | Wrap dokument s prompt iteration log block-om |

### 2.4 Git artefakti

| Tag | Što označava | Kraj kojeg koraka iz §6 |
|---|---|---|
| `faza-2b-1d-iter1-complete` | Iter 1 fix primijenjen + pilot rerun završen (bez obzira na pass rate) | Korak 4 |
| `faza-2b-1d-complete` | Final tag — bilo: ≥80% pass nakon Iter 1, ili ≥80% nakon Iter 2, ili escalation odluka donesena s dokumentacijom | Korak 7 ili 9 |

**Napomena o tag-ovima:** Ako Iter 1 odmah donese ≥80%, `faza-2b-1d-iter1-complete` i `faza-2b-1d-complete` su isti commit (oba taga na istom commit-u, dva taga su explicit za historiju).

### 2.5 Verification (Milestone)

- [ ] Iter 1 fix primijenjen u `user_template.md` (issue #1 + #2 adresiran)
- [ ] Pilot rerun #1 izvršen, `pilot_report_iter1.json` postoji
- [ ] Summary analize Iter 1 dokumentiran u commit message ili wrapup.md
- [ ] **Branch decision document-iran:** Iter 1 ≥80% → end, ILI < 80% → Iter 2 plan
- [ ] (Ako Iter 2) Targeted fix primijenjen, rerun izvršen, detailed analysis u wrapup.md
- [ ] (Ako escalation) Tool-use migration plan kao kratki block u wrapup.md (NE implementacija)
- [ ] `docs/faza-2b-1d-wrapup.md` postoji s iteration log block-om
- [ ] Tagovi `faza-2b-1d-iter1-complete` i `faza-2b-1d-complete` postavljeni i push-ani
- [ ] 220+ testova prolaze

---

## 3. Dizajn — Pilot rerun konfiguracija

### 3.1 Skraćeni pilot config (5 koncepata × 2 težine = 10 tasks)

5 problematičnih koncepata (svi koji su pali u 2B-1B pilot, iz handoff-a):

| Module | Concept | Težine | Sandbox mode | Razlog uključivanja |
|---|---|---|---|---|
| 1 | `where_filter` | 1, 2 | SELECT | Failio u 2B-1B pilot |
| 2 | `group_by` | 2, 3 | SELECT | Failio u 2B-1B |
| 3 | `right_join` | 2, 3 | SELECT | Failio u 2B-1B |
| 5 | `scalar_subquery` | 2, 3 | SELECT | Failio u 2B-1B |
| 6 | `explain_plan` | 3, 4 | SELECT | Failio u 2B-1B |

**Što je IZ pilot-a:**
- `insert` (M4) — solid u 2B-1B, ne moramo retestirati
- Transverzalni koncepti (`null_handling`) — biti će testirani indirektno kroz secondary_concepts u SELECT zadacima

**Što se mjeri:**
- Prvi-pokušaj pass rate (kao 2B-1B) — Iter 1 i Iter 2 moraju biti apples-to-apples comparable
- Per-concept pass/fail (5 koncepata × 2 težine = 10 data points)
- Failure razlozi (top 3 ili više)

### 3.2 Pilot rerun command (target)

```bash
cd backend

# Option A: ako pilot_run.py dobije --concepts flag
uv run python -m scripts.pilot_run \
    --concepts where_filter,group_by,right_join,scalar_subquery,explain_plan \
    --output-suffix iter1

# Option B: ako --concepts ne implementiramo, edit-aj PILOT_CONFIG inline
uv run python -m scripts.pilot_run
```

### 3.3 Pilot config strategija — odluka za CC

**CC mora odlučiti** koji od dva pristupa:

**Pristup A: Dodaj `--concepts` flag** (preferred ako jednostavno)
- Modify `pilot_run.py` da prima `--concepts <code1,code2,...>` (default: postojeći PILOT_CONFIG)
- Modify `pilot_run.py` da prima `--output-suffix <name>` za pilot_report iter naming
- Dodaj 1-2 smoke testa za nove flag-ove
- Trošak: ~15 min implementacije

**Pristup B: Edit PILOT_CONFIG inline za 2B-1D, revert na kraju**
- Privremena izmjena 2B-1B PILOT_CONFIG-a, run pilot, revert
- Manji scope ali manja reproducibilnost
- Pilot report path bi morao biti manualno preimenovan

**Preporuka:** **Pristup A**, jer:
- Mali code change (~10 linija), high reuse value (može trebati i u 2B-2 monitoring-u)
- Reproducibilnost — 2B-1D rerun može se replay-ati za diplomski rad
- Output suffix omogućuje history (iter1, iter2, iter3...)

**Ali**: ako CC procijeni da je Pristup B brži (npr. ako pilot_run.py struktura ne prima lako flag-ove), prihvatljiv je. Plan ne forsira.

### 3.4 Pilot success kriteriji (decision tree)

```
Iter 1 rerun → pass rate X%

┌── X ≥ 80% → ✓ DONE
│              └── tag faza-2b-1d-iter1-complete + faza-2b-1d-complete (isti commit)
│
├── 60% ≤ X < 80% → Iter 2 (targeted fix na ostale 20-40%)
│              └── tag faza-2b-1d-iter1-complete, nastavi
│
└── X < 60% → Iter 2 OBA fix-a (issue #1 + #2 možda nisu adresirani u Iter 1)
               └── OPCIJA: pređi direktno na escalation (tool-use migration plan)
```

**Granica 60% je arbitrary** ali heuristic — ako fix-evi donesu <60%, sistemski problem je veći od ona 2 issue-a koja smo identificirali, pa je tool-use migration jaki kandidat za rješenje.

---

## 4. Dizajn — Prompt fix smjernice

### 4.1 Iter 1 fix-evi

Ovo je smjernica za CC, NE finalni prompt copy-paste. CC treba prvo pročitati `user_template.md`, vidjeti gdje su prirodni injection point-i, pa primijeniti.

#### Fix #1: secondary_concepts max=2 constraint

**Što treba dodati u prompt:**
```
**IMPORTANT CONSTRAINTS:**
- `secondary_concepts` MUST contain at most 2 concept codes (NOT more)
- `secondary_concepts` MUST NOT include the primary concept (no duplicates)
- `secondary_concepts` MUST be different concepts that the task ALSO exercises
```

**Pozicija u template-u:** Negdje pored `{{misconceptions_block}}` ili `{{anti_patterns_block}}` — gdje god ima drugih structural constraints. Inline s drugim "rules" — ne na kraju (kraj je za output format instrukciju).

**Verifikacija:** Nakon fix-a, manualno generiraj 1 task za `where_filter` (`uv run python -m scripts.generate_tasks --concept where_filter --difficulty 2 --count 1`). Pregledaj output JSON — `secondary_concepts` ima ≤2 entry-ja? Ako da, fix #1 radi.

#### Fix #2: JSON-only output (no markdown scratchpad)

**Što treba dodati na KRAJ user_template.md:**
```
**OUTPUT FORMAT (strict):**
Respond with ONLY a valid JSON object matching the schema above.
- DO NOT wrap the JSON in markdown code blocks (no ```json ... ``` fences)
- DO NOT include any explanation, preamble, or "reasoning" before/after the JSON
- DO NOT include comments inside the JSON
- The first character of your response MUST be `{` and the last character MUST be `}`
- If you need to think through the problem, do so internally — only the final JSON is your response
```

**Pozicija u template-u:** **Striktno na kraj** user prompt-a — Anthropic best practice je da imperative output instructions idu na kraj jer model ih daje najveću težinu (recency bias).

**Verifikacija:** Manualno run jednog `where_filter` zadatka, provjeri da je response **čist JSON** (parsea s `json.loads()` bez `json_extract.py` markdown stripping). Ako još uvijek ima markdown, fix #2 nije dovoljan — escalation kandidat.

### 4.2 Što IZBJEGAVATI u prompt fix-u

- ❌ Ne dodavati concept-specific instrukcije (npr. "for where_filter, always include INDEX") — generic fix prvo
- ❌ Ne mijenjati `{{placeholder}}` strukturu — to bi razbilo `PromptBuilder` rendering
- ❌ Ne dodavati examples u prompt — već postoje `few_shot_examples` u concept config-ima, dvostruko bi confuse-alo model
- ❌ Ne brisati postojeća pravila — samo dodaj, ne refactor

### 4.3 task_validator.py uvjetni mod

**Trigger:** Ako pilot_report.json (nakon Iter 1) ne razlikuje fail razloge dovoljno granularno za analizu.

**Konkretno:** Ako su svi fail-ovi tagirani kao `"json_parse_error"` bez detalja zašto, validator ne razlikuje:
- Model vratio markdown (issue #2) → fix-evi rade na Iter 2
- Model vratio drugačiji JSON shape od schema → drugi problem
- Model vratio prazan response → API timeout

**Fix u `task_validator.py`:** Dodaj detail-niji error klasifikacija (~10 linija):
```python
error_type = "json_parse_error"
if response.startswith("```"):
    error_subtype = "markdown_wrapped"
elif "{" not in response:
    error_subtype = "no_json_block"
else:
    error_subtype = "malformed_json"
```

**Ovo je OPTIONAL** — samo ako CC procijeni da postojeći error reporting nije dovoljan za Iter 1 analizu.

### 4.4 Iter 2 fix smjernice (samo ako se aktivira)

Iter 2 je **reaktivan** na Iter 1 rezultat — ne može se planirati unaprijed. Smjernice za CC:

**Ako 60-80% pass rate s 1-2 koncepta koja gore u plamenu:**
- Concept-specific fix u `user_template.md` ili u njihov YAML config (`few_shot_examples` poboljšaj)
- Primjer: ako `scalar_subquery` jedini fail-a, dodaj boji example u `scalar_subquery.yaml`

**Ako fail-ovi su uniformno raspoređeni preko svih 5 koncepata:**
- Probaj jači imperative u JSON-only output instrukciju (npr. dodaj "Failure to comply with the output format will be penalized")
- Ili razmotri partial tool-use migration (manje invazivan od full migration)

**Ako fail-ovi su <50% nakon Iter 1:**
- Skip Iter 2 fix iteraciju, direktno pređi na escalation plan (vidi §5)

---

## 5. Escalation path — Tool-use migration plan

Ovo je **planning-only** dokument za 2B-1D wrapup ako se aktivira. **NE implementira se u 2B-1D.**

### 5.1 Što tool-use migration uključuje

| Komponenta | Izmjena |
|---|---|
| `backend/scripts/lib/api_client.py` | Već ima `generate_structured_output()` (iz 2B-1B). Reuse direktno. |
| `backend/scripts/generate_tasks.py` | Refactor: `generate_one()` koristi `generate_structured_output(schema=GeneratedTask.model_json_schema())` umjesto `generate() + json_extract` |
| `backend/scripts/lib/task_validator.py` | Validator skip-a "JSON parse" step jer tool-use guarantira validni JSON shape. Level 1 syntax check ostaje. |
| `backend/app/schemas/generated_task.py` | Potencijalne izmjene da Pydantic schema bude ČIŠĆA za tool input_schema (npr. eksplicitne `Field(description=...)` da model razumije polja) |
| Tests | ~10 novih + ~5 modificiranih testova |

### 5.2 Procjena trajanja escalation

- Implementacija: ~2-3h
- Tests: ~1h
- Pilot rerun nakon migration: ~30 min
- **Ukupno: ~4-5h** (zato je escalation odluka važna — može produžiti 2B-1D 3x)

### 5.3 Escalation decision tree (za 2B-1D wrapup)

Wrapup dokument mora odgovoriti:

1. **Da li escalation potreban?** (DA/NE — na temelju Iter 2 rezultata)
2. **Ako DA, sub-faza:** Novi `2B-1E` ili scope creep u `2B-1D` revisit?
3. **Ako NE escalation, ali pass rate je 70-79%:** Acceptable za 2B-2 batch ili lower threshold?

**Default odluka u planu (ako nijedna iteracija ne stigne do 80%):** Novi sub-faza `2B-1E` umjesto scope creep — održava clean tagging i historiju.

---

## 6. Implementacijski redoslijed

**Workflow:** Pragmatičan, ne striktni TDD jer 2B-1D nije code-heavy. Glavni fokus je iterativno mjerenje pilot rezultata.

### Korak 1: Pre-flight (5 min)

```bash
cd backend

# Verify clean baseline
git status
uv run pytest -q  # target: 220 passed

# Backup trenutni pilot report za historiju
cp data/generated_tasks/pilot/pilot_report.json \
   data/generated_tasks/pilot/pilot_report_baseline_2b1b.json
```

**Commit:** `chore(2b-1d): backup 2B-1B pilot report`

### Korak 2: pilot_run.py konfiguracija (ako Pristup A iz §3.3)

1. Modify `pilot_run.py`:
   - Dodaj argparse: `--concepts` (comma-separated), `--output-suffix` (e.g. "iter1")
   - Default ostavi 2B-1B PILOT_CONFIG (backward compat)
2. Modify `test_pilot_run_smoke.py`: dodaj test za `--concepts` flag (1 test minimum)
3. Run testovi → 222 passed
4. **Commit:** `feat(2b-1d): pilot_run.py --concepts i --output-suffix flagovi`

### Korak 3: Iter 1 fix u user_template.md

1. **Prvo PROČITAJ** `backend/config/prompt_templates/user_template.md`
2. Identificiraj injection points:
   - Fix #1 (max=2 constraint): negdje u sredinom — pored drugih structural rules
   - Fix #2 (JSON-only output): na kraj template-a
3. Apply fix-eve s točnim tekstom iz §4.1
4. **Sanity check:** Manualno generiraj 1 task da vidiš da fix-evi nisu razbili rendering:
   ```bash
   uv run python -m scripts.generate_tasks \
       --concept where_filter --difficulty 1 --count 1 --dry-run
   ```
5. Verify output je clean JSON, secondary_concepts ≤2
6. **Commit:** `feat(2b-1d): iter 1 prompt fix — secondary_concepts max=2 + JSON-only output`

### Korak 4: Pilot rerun #1 + analiza (live API, ~15 min)

```bash
cd backend
uv run python -m scripts.pilot_run \
    --concepts where_filter,group_by,right_join,scalar_subquery,explain_plan \
    --output-suffix iter1
```

1. Pregledaj `data/generated_tasks/pilot/pilot_report_iter1.json`
2. Izračunaj pass rate (validated_count / 10)
3. Summary failure modes (top 3 razloga)
4. Per-concept pass rate (5 koncepata × 2 težine)
5. Document findings u commit message ili `docs/faza-2b-1d-wrapup.md` (prvi draft)
6. **Commit:** `feat(2b-1d): pilot rerun iter1 — X/10 validated, top fail: <reason>`
7. **Tag:** `git tag faza-2b-1d-iter1-complete && git push origin faza-2b-1d-iter1-complete`

### Korak 5: Decision point (5 min)

Na temelju pass rate iz Koraka 4:

| Pass rate | Akcija | Sljedeći korak |
|---|---|---|
| ≥ 80% (8+/10) | ✓ DONE | Korak 9 (final wrapup) |
| 60% ≤ X < 80% | Iter 2 targeted fix | Korak 6 |
| < 60% | Iter 2 aggressive fix ILI direkt escalation | Korak 6 ili 8 |

**Document decision** u kratkom commit message ili note u wrapup.md.

### Korak 6: Iter 2 targeted fix (uvjetno, ~30 min)

1. Re-pregledaj `pilot_report_iter1.json` u **detalju** (per-task failure razlozi)
2. Identificiraj 1-3 targeted fix points (vidi §4.4)
3. Apply fix-eve u `user_template.md` ili concept-specific YAML (`few_shot_examples`)
4. Manual sanity check (1-2 task generiranje)
5. **Commit:** `feat(2b-1d): iter 2 targeted fix — <description>`

### Korak 7: Pilot rerun #2 + detailed analysis (live API + analiza, ~30 min)

```bash
uv run python -m scripts.pilot_run \
    --concepts where_filter,group_by,right_join,scalar_subquery,explain_plan \
    --output-suffix iter2
```

1. Compare pass rate vs Iter 1
2. **Detailed analysis** (per task, prompt diff vs Iter 1)
3. Document u wrapup.md (full block, ne samo summary)
4. **Commit:** `feat(2b-1d): pilot rerun iter2 — X/10 validated, analysis dokumentirana`

### Korak 8: Escalation decision (uvjetno, ~15 min)

Aktivira se ako Iter 2 < 80%:

1. Document u wrapup.md:
   - Iter 1 pass rate, Iter 2 pass rate
   - Što je probano u oba iter
   - Zašto prompt-only nije dovoljno (data-backed claim)
   - **Recommendation:** Tool-use migration u novom sub-task-u 2B-1E
2. **NE implementiraj** tool-use migration — samo planiranje
3. **Commit:** `docs(2b-1d): escalation odluka — tool-use migration planirana kao 2B-1E`

### Korak 9: Final wrapup + tag

1. Finaliziraj `docs/faza-2b-1d-wrapup.md`:
   - Iteration log block (Iter 1 → Iter 2 → outcome)
   - Top 3 lessons learned za 2B-2
   - Recommendations za 2B-2 batch generation strategy
2. Run final test suite: `uv run pytest -q` → **220-222 passed**
3. **Commit:** `docs(2b-1d): faza-2b-1d wrapup s iteration log block-om`
4. **Tag:** `git tag faza-2b-1d-complete && git push origin faza-2b-1d-complete`

### Korak 10: Update memory file (uvjetno)

Ako 2B-1D pronašao važne insights za buduće faze, ažuriraj memory file (ili novi handoff document) — vidi 2B-1B handoff format kao referencu.

---

## 7. Entry kriteriji (start 2B-1D)

- [x] 2B-1B zaključena, tag `faza-2b-1b-complete` push-an i mergan u main
- [x] 220 testova prolazi baseline
- [x] `data/generated_tasks/pilot/pilot_report.json` postoji (2B-1B baseline za usporedbu)
- [x] `anthropic` SDK ≥0.97.0
- [x] Sandbox kontejner running
- [x] `ANTHROPIC_API_KEY` u `backend/.env`
- [x] Budget: ~$0.15 (2 rerun-a × ~$0.04 + buffer; max 3 rerun-a × ~$0.04 = $0.12)

## 8. Exit kriteriji (kraj 2B-1D)

### Happy path (≥80% u Iter 1 ili Iter 2):
- [ ] `user_template.md` fixed (issue #1 + #2 adresiran)
- [ ] Pilot rerun pass rate ≥ 80% (8+/10)
- [ ] `pilot_report_iter1.json` (i `iter2.json` ako se aktivirao) postoje
- [ ] `docs/faza-2b-1d-wrapup.md` s iteration log block-om
- [ ] Tagovi push-ani

### Escalation path (< 80% nakon Iter 2):
- [ ] `docs/faza-2b-1d-wrapup.md` sadrži escalation odluku
- [ ] Tool-use migration plan dokumentiran kao block u wrapup
- [ ] Decision: novi sub-faza 2B-1E ili scope creep — explicit u wrapup
- [ ] Tagovi push-ani (faza-2b-1d-complete označava završetak iteracije, ne success)

---

## 9. Risk register

| Rizik | Vjerojatnost | Impact | Mitigacija |
|---|---|---|---|
| Iter 1 razbije postojeće testove jer fixture stale | Low | Low | Update fixture (ne prompt revert) |
| Iter 1 pass rate < 30% (sistemski problem) | Low | High | Skip Iter 2 fix, direktno escalation s detailed analysis |
| Iter 2 pass rate je MANJA od Iter 1 (loš fix) | Low | Medium | Revert Iter 2 fix, finalize s Iter 1 + escalation |
| Pilot rerun cost > $0.10 (token blow-up) | Low | Low | Hard cap u API client (postojeci `--hard-cap-usd` iz 2B-1B) |
| Model fiksira issue #2 ali otkriva novi (npr. invalid SQL syntax češći) | Medium | Medium | Analysis u Iter 2 — možda concept-specific fix |
| 2B-1B PILOT_CONFIG nije modify-iran ali plan ga zahtjeva | Medium | Low | Pristup A iz §3.3 (dodavanje flag-a) ili Pristup B (inline edit + revert) |
| Tool-use migration scope ispada veći od 4-5h procjene | Medium | High | Strogo defer u 2B-1E sub-fazu, ne extend 2B-1D |

---

## 10. Tehnološki dug i otvorena pitanja za 2B-1C/2B-2

| Stavka | Status nakon 2B-1D | Rok |
|---|---|---|
| Tool-use migration za `generate_tasks.py` | Možda novi 2B-1E (ako se aktivira escalation) | 2B-1E (uvjetno) ili Faza 3 |
| Concept-specific prompt tuning (per modul) | Otvoren ako pilot otkrije module-specific issues | 2B-2 monitoring |
| `--from-matrix` CLI flag za `generate_tasks.py` | Iz 2A errata, još uvijek defer | 2B-2 |
| Validation tool (Streamlit + SQLite) | 2B-1C ostaje pending | 2B-1C |

---

## 11. Reference

- `docs/faza-2b-1b-wrapup.md` ili equivalent — pilot findings koji su trigger za 2B-1D
- `docs/faza-2b-1b-plan.md` §6 — original pilot design (5+1 koncepata, INSERT path)
- `backend/config/prompt_templates/user_template.md` — fix target lokacija
- `backend/scripts/pilot_run.py` — pilot pipeline
- `backend/scripts/lib/api_client.py` — `generate_structured_output()` za escalation reference
- Anthropic prompt engineering docs: output format placement, imperative instructions

---

## 12. Što slijedi nakon 2B-1D

### Ako 2B-1D = happy path (≥80% pass):
- **2B-1C — Validation tool (Streamlit + SQLite)** — kao originalno planirano

### Ako 2B-1D = escalation aktivirana:
- **2B-1E — Tool-use migration** za `generate_tasks.py` (novi sub-task)
- Tek nakon 2B-1E, prelazak na 2B-1C

### Onda:
- **2B-2 — Full generation run za 105 zadataka** (s prompt template iz 2B-1D ili tool-use API iz 2B-1E)
- **2B-3 — Manual validation kroz Streamlit tool**

---

*Plan kraj. Start point: `git checkout main && git pull && git checkout -b faza-2b-1d-implementation && cd backend && git status && uv run pytest -q` (verify 220 passed).*
