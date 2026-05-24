# FAZA 2B-1C — Akcijski plan

**Diplomski rad:** Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju
**Sub-faza:** 2B-1C od 8 (posljednja sub-podsekcija Faze 2B-1)
**Cilj:** Streamlit validation tool + SQLite persistence za human-in-the-loop review 105 generiranih zadataka u 2B-3
**Trajanje:** 2.5-3h aktivnog rada (Standard sophistication)
**Trošak:** $0 (no API calls — pure local development)
**Predviđeni broj git commit-ova:** 6-8

---

## 1. Kontekst i ciljevi

### 1.1 Pozadina

2B-1A → 2B-1E sve su bile o pripremi LLM generation pipeline-a. 2B-1C je **kvalitativno drugačija** sub-faza — pure UI development, no API calls, no LLM. Tool postoji da bi ti (jedini reviewer) mogao efikasno proći kroz 105 zadataka u Fazi 2B-3 nakon batch generation-a u 2B-2.

**Naučeno iz prethodnih sub-faza koje informira 2B-1C:**

| Lesson | Implikacija |
|---|---|
| Pilot 70% pass rate → ~30 fail-eva u 2B-2 batch | Tool mora podržati failure_type filter za triage |
| 2B-1B uveo DML mode u SandboxRunner | Re-run query button mora podržati DML tasks |
| `validation_summary` u `GeneratedTask` schema već postoji (iz 2A) | Source-of-truth za failure_type filter postoji |
| 105 × 5-10 min review = realnih 8-15h vremena u tool-u | Standard UX investment je opravdan, ne over-engineering |

### 1.2 Što ova sub-faza radi

1. **Streamlit web app** s 2 page-a:
   - **Review page** — task viewer s decision buttons, notes, re-run query
   - **Stats page** — overview (X/105 reviewed, breakdown per decision/concept/module)
2. **SQLite persistence layer** (`data/generated_tasks/manual_review.sqlite`) — schema za review decisions
3. **Filter sistem** — module + concept + decision + failure_type
4. **Re-run query feature** — opcionalni sandbox execution s SELECT i DML mode podrškom
5. **Keyboard shortcuts** (J/K za prev/next) — power-user navigation za batch review
6. **Progress indicator** — X/Y reviewed, % completion

### 1.3 Što ova sub-faza NE radi

- ❌ Bulk actions (svaki zadatak individual review)
- ❌ Re-generation of tasks (failed tasks idu u 2B-2 retry, ne u tool)
- ❌ Schema modifications na `GeneratedTask` ili `ConceptConfig`
- ❌ Diff view (proposed_query vs current_query) — to je 2B-3 cleanup feature ako zatreba
- ❌ Export feature in-tool (manual `sqlite3` CSV export na kraju 2B-3 dovoljan)
- ❌ Multi-user collaboration (ti si jedini reviewer)
- ❌ Authentication / login (lokalna development app)
- ❌ Deployment configuration (runs lokalno preko `streamlit run`)
- ❌ Mobile-friendly responsive design

### 1.4 Strateške odluke (zaključene)

| # | Odluka | Vrijednost |
|---|---|---|
| 1 | Sophistication level | **Standard** (2.5-3h, dobra UX) |
| 2 | Persistence | **SQLite** (`manual_review.sqlite`, gitignored) |
| 3 | Run query feature | **Hibrid** (default preview, opcionalni re-run button) |
| 4 | Filter granularnost | **Module + concept + decision + failure_type** |
| 5 | Bulk actions | **Skip** (individual review only) |
| 6 | Streamlit dep status | **Mora se dodati u `pyproject.toml`** (verified <not found> u 2B-1B dump-u) |

---

## 2. Deliverables

### 2.1 Kod (6 novih fajlova + 1 modifikacija)

| Path | Status | LoC (procjena) | Odgovornost |
|---|---|---|---|
| `pyproject.toml` | **MODIFY** | +1 line | Dodaj `streamlit>=1.40` u deps |
| `backend/app/db/manual_review.py` | **NEW** | ~80 | SQLite schema + CRUD operacije za task_reviews tablicu |
| `backend/scripts/validation_tool/__init__.py` | **NEW** | 0 | Package marker |
| `backend/scripts/validation_tool/app.py` | **NEW** | ~50 | Streamlit entrypoint — routing, sidebar layout |
| `backend/scripts/validation_tool/loaders.py` | **NEW** | ~80 | Load tasks from validated/failed dirs, parse, cache |
| `backend/scripts/validation_tool/review_page.py` | **NEW** | ~150 | Main review page — task display, decision controls, filters |
| `backend/scripts/validation_tool/stats_page.py` | **NEW** | ~80 | Stats overview page — progress, breakdowns |
| `backend/scripts/validation_tool/components.py` | **NEW** | ~70 | Reusable UI components (task card, decision panel, query runner) |

**Total:** ~510 LoC novih + 1 line modifikacija

### 2.2 Tests

| Test fajl | Status | Broj testova |
|---|---|---|
| `backend/tests/test_manual_review_db.py` | **NEW** | ~8 (CRUD ops, schema init, idempotency, filter queries) |
| `backend/tests/test_validation_tool_loaders.py` | **NEW** | ~5 (load validated, load failed, malformed JSON handling, empty dir) |
| Streamlit UI testovi | **SKIP** | UI tests s Streamlit zahtijevaju `playwright` ili `streamlit-testing-library` — out of scope |

**Test count target:** 226 (baseline iz 2B-1E) + ~13 nova = **~239 testova prolazi**.

**Što NE testiramo:**
- Streamlit page rendering — manual sanity check umjesto automated
- Keyboard shortcuts — manual test
- Re-run query button click flow — manual test (mock sandbox bi bio over-engineering)

### 2.3 Artefakti

| Path | Status | Sadržaj |
|---|---|---|
| `data/generated_tasks/manual_review.sqlite` | **NEW (gitignored)** | SQLite database s review decisions |
| `data/generated_tasks/.gitignore` | **MODIFY (uvjetno)** | Add `manual_review.sqlite` ako već ne pokriva |
| `docs/faza-2b-1c-wrapup.md` | **NEW** | Wrap dokument, manual test report, screenshot |

### 2.4 Git artefakti

| Tag | Što označava |
|---|---|
| `faza-2b-1c-db-layer` | SQLite schema + CRUD radi, testovi prolaze (checkpoint nakon Koraka 3) |
| `faza-2b-1c-complete` | Final tag — Streamlit tool functional, manual smoke test prolazi |

### 2.5 Verification (Milestone)

- [ ] `streamlit` u `pyproject.toml`, `uv sync` radi
- [ ] `backend/app/db/manual_review.py` postoji, CRUD operacije testirane
- [ ] Streamlit app pokreće se s `streamlit run backend/scripts/validation_tool/app.py`
- [ ] Review page prikazuje task description + query (syntax highlighted) + expected_result
- [ ] Filteri rade (module, concept, decision, failure_type)
- [ ] Decision buttons (Approve / Reject / Needs-fix) perzistiraju u SQLite
- [ ] Notes textarea perzistira u SQLite
- [ ] Re-run query button izvršava query u sandbox-u (SELECT i DML mode)
- [ ] Keyboard shortcuts rade (J = next, K = prev)
- [ ] Stats page prikazuje progress + breakdowns
- [ ] Manual smoke test: review 3-5 tasks iz pilot-a, verify decisions persistuje
- [ ] **~239 testova prolazi**
- [ ] Tagovi push-ani

---

## 3. Dizajn — SQLite schema

### 3.1 Tablica `task_reviews`

```sql
CREATE TABLE IF NOT EXISTS task_reviews (
    task_id TEXT PRIMARY KEY,                -- UUID iz GeneratedTask JSON (npr. "where_filter_d2_a1b2c3d4")
    decision TEXT NOT NULL,                  -- 'pending' | 'approved' | 'rejected' | 'needs_fix'
    notes TEXT DEFAULT '',
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Denormalized metadata za bržu pretragu (dohvaća se iz task JSON-a pri prvom save-u)
    concept_code TEXT NOT NULL,
    module_number INTEGER NOT NULL,
    difficulty INTEGER NOT NULL,
    task_status TEXT NOT NULL,               -- 'validated' | 'failed' (iz JSON-a)
    failure_type TEXT,                       -- 'json_parse' | 'schema' | 'row_mismatch' | 'concept_not_detected' | 'sandbox_error' | NULL ako validated
    CHECK (decision IN ('pending', 'approved', 'rejected', 'needs_fix'))
);

CREATE INDEX idx_task_reviews_decision ON task_reviews(decision);
CREATE INDEX idx_task_reviews_concept ON task_reviews(concept_code);
CREATE INDEX idx_task_reviews_module ON task_reviews(module_number);
CREATE INDEX idx_task_reviews_failure ON task_reviews(failure_type);
```

### 3.2 Dizajn odluke

| Odluka | Razlog |
|---|---|
| `task_id TEXT PRIMARY KEY` (string, ne autoincrement) | Match-a JSON filename pattern `{concept}_d{difficulty}_{uuid8}` |
| Denormalized metadata (concept_code, module, etc.) | Brži filteri (no JOIN na external data); JSON-i su immutable po dogovoru iz 2A |
| `decision = 'pending'` default | Loader inicijalizira pending entry za novi task; lakše per-task tracking |
| `failure_type` može biti NULL | Validated tasks nemaju failure type |
| Index na svim filter columns | 105 rows × 4 indexes je trivial overhead; query latency < UI redraw |
| `CHECK` constraint za decision values | SQLite-level validation; catch tipos prije UI bug-ova |
| Bez `tasks` master tablice | Tasks ostaju JSON files na disku; SQLite samo store-uje decisions (single-source-of-truth: JSON files) |

### 3.3 Failure type taxonomy

**Iz wrapup-ova faza 2B-1D i 2B-1E:**

| Failure type | Što označava | Iz koje validacije level |
|---|---|---|
| `json_parse` | Model output nije validan JSON | Level 0 (pre-schema) |
| `schema` | JSON ne match-a `GeneratedTask` Pydantic | Level 1 |
| `concept_not_detected` | AST analyzer ne pronalazi primary concept | Level 2 |
| `row_mismatch` | Sandbox result ≠ expected_result | Level 3 |
| `sandbox_error` | Sandbox execution exception (timeout, SQL error) | Level 3 |
| `other` | Sve ostalo | Fallback |

**Critical:** Source za failure_type je `validation_summary.error_type` u `GeneratedTask` JSON-u. Loader mora čitati taj field i mapirati na taxonomy. Ako se field ne podudara, dodati helper mapper u `loaders.py`.

### 3.4 CRUD API u `manual_review.py`

```python
# backend/app/db/manual_review.py

from pathlib import Path
import sqlite3
from typing import Literal
from dataclasses import dataclass

Decision = Literal["pending", "approved", "rejected", "needs_fix"]

@dataclass(frozen=True)
class TaskReview:
    task_id: str
    decision: Decision
    notes: str
    reviewed_at: str
    concept_code: str
    module_number: int
    difficulty: int
    task_status: str
    failure_type: str | None


class ManualReviewDB:
    """SQLite layer za task review decisions. Single-connection per Streamlit session."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        """Idempotent schema creation."""
        ...

    def upsert_review(
        self,
        task_id: str,
        decision: Decision,
        notes: str,
        # Denormalized fields (iz task JSON-a, pri prvom save-u)
        concept_code: str,
        module_number: int,
        difficulty: int,
        task_status: str,
        failure_type: str | None,
    ) -> None:
        """Insert or update review. Idempotent."""
        ...

    def get_review(self, task_id: str) -> TaskReview | None:
        """Retrieve single review by task_id."""
        ...

    def list_reviews(
        self,
        decision: Decision | None = None,
        concept_code: str | None = None,
        module_number: int | None = None,
        failure_type: str | None = None,
    ) -> list[TaskReview]:
        """List reviews with optional filters."""
        ...

    def get_stats(self) -> dict:
        """Aggregated stats: count by decision, by concept, by module."""
        ...
```

---

## 4. Dizajn — Streamlit struktura

### 4.1 App layout (multi-page)

```
backend/scripts/validation_tool/
├── __init__.py
├── app.py                  # Entrypoint, sidebar navigation
├── loaders.py              # Task loading from validated/failed dirs
├── review_page.py          # Main review UI
├── stats_page.py           # Stats overview
└── components.py           # Reusable widgets (task card, decision panel, query runner)
```

### 4.2 `app.py` — Entrypoint

```python
# backend/scripts/validation_tool/app.py

import streamlit as st
from pathlib import Path
from app.db.manual_review import ManualReviewDB
from scripts.validation_tool import review_page, stats_page

# Page config
st.set_page_config(
    page_title="2B-3 Validation Tool",
    page_icon="✓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize DB
BACKEND_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = BACKEND_ROOT.parent / "data" / "generated_tasks" / "manual_review.sqlite"

@st.cache_resource
def get_db() -> ManualReviewDB:
    return ManualReviewDB(DB_PATH)

# Sidebar navigation
st.sidebar.title("2B-3 Validation Tool")
page = st.sidebar.radio("Page", ["Review", "Stats"])

# Progress indicator (always visible)
db = get_db()
stats = db.get_stats()
total = stats["total"]
reviewed = stats["reviewed"]
st.sidebar.metric(
    "Progress",
    f"{reviewed}/{total}",
    delta=f"{int(100 * reviewed / max(total, 1))}%",
)

# Route to page
if page == "Review":
    review_page.render(db)
elif page == "Stats":
    stats_page.render(db)
```

### 4.3 `review_page.py` — Main review UI

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ Sidebar (existing)         │  Main area             │
│ ─────────                  │  ────────              │
│ Filters:                   │  Task #X / Y           │
│ □ Module                   │  Concept: where_filter │
│ □ Concept                  │  Difficulty: 2         │
│ □ Decision                 │  ─────────────────     │
│ □ Failure type             │  📝 Description        │
│                            │  Find all products...  │
│ [Apply Filters]            │  ─────────────────     │
│                            │  💻 Expected Query     │
│ Filtered: 30 tasks         │  SELECT * FROM ...     │
│                            │  ─────────────────     │
│ ◀ J: Prev  K: Next ▶       │  📊 Expected Result    │
│                            │  | id | name | ...     │
│                            │  ─────────────────     │
│                            │  ⚙ Re-run Query        │
│                            │  ─────────────────     │
│                            │  ❓ Failure Reason     │
│                            │  (only if failed)      │
│                            │  ─────────────────     │
│                            │  Decision:             │
│                            │  ✓ Approve             │
│                            │  ✗ Reject              │
│                            │  ⚠ Needs Fix          │
│                            │  ─────────────────     │
│                            │  Notes:                │
│                            │  [textarea]            │
└─────────────────────────────────────────────────────┘
```

### 4.4 Keyboard shortcuts

**Implementation:** Streamlit native ne podržava keyboard shortcuts. Use `streamlit-shortcuts` package ILI workaround s `streamlit-keyup`:

```python
# Pristup A: streamlit-shortcuts (dependency)
# pip install streamlit-shortcuts

import streamlit_shortcuts

streamlit_shortcuts.add_keyboard_shortcuts({
    "j": "next_task",
    "k": "prev_task",
    "a": "approve",
    "r": "reject",
    "f": "needs_fix",
})
```

**Pristup B (fallback):** Pure Streamlit buttons s `key=` prop + custom JS injection through `st.markdown(unsafe_allow_html=True)`. Više rada, manje clean.

**Preporuka:** Pristup A. Dependency je legit za internal tool. Ako Pristup A ne radi (kompatibilnost Streamlit verzije), fallback je manual Prev/Next buttons.

### 4.5 Re-run query feature

```python
# components.py

def query_runner_panel(task: dict, sandbox_runner: SandboxRunner) -> None:
    """Optional sandbox re-run for sanity check."""
    st.subheader("⚙ Re-run Query")

    col1, col2 = st.columns([3, 1])

    with col1:
        # Determine if DML based on concept_code
        is_dml = task["concept_code"] in {"insert", "update", "delete"}
        st.caption(f"Mode: {'DML (write, auto-rollback)' if is_dml else 'SELECT (read-only)'}")

    with col2:
        rerun = st.button("▶ Run", key=f"rerun_{task['task_id']}")

    if rerun:
        with st.spinner("Executing..."):
            try:
                result = sandbox_runner.execute(task["expected_query"], dml=is_dml)
                if result.success:
                    st.success(f"✓ Returned {len(result.rows)} rows")
                    st.dataframe(result.rows)
                else:
                    st.error(f"✗ Error: {result.error}")
            except Exception as exc:
                st.error(f"Sandbox exception: {exc}")
```

### 4.6 Sandbox connection management

**Issue:** Streamlit re-runs entire script on every interaction. Sandbox connection mora biti cached:

```python
@st.cache_resource
def get_sandbox_runner() -> SandboxRunner:
    """Lazy-loaded sandbox runner. Reused across Streamlit reruns."""
    return SandboxRunner(connection_string=os.getenv("SANDBOX_DB_URL"))
```

**Pre-flight check:** Tool first-run mora verificirati da sandbox je available. Ako nije, prikazati banner ("⚠ Sandbox not running, re-run feature disabled") ali tool i dalje radi za review (samo bez re-run).

---

## 5. Dizajn — Loaders

### 5.1 Task loading flow

```python
# loaders.py

@st.cache_data(ttl=60)  # Cache za 60s da se izbjegne re-read svake interakcije
def load_all_tasks(generated_tasks_dir: Path) -> list[dict]:
    """Load sve task JSON-ove iz validated/ i failed/ subdirs."""
    tasks = []
    for status in ("validated", "failed"):
        subdir = generated_tasks_dir / status
        if not subdir.exists():
            continue
        for json_path in sorted(subdir.glob("*.json")):
            try:
                task = json.loads(json_path.read_text(encoding="utf-8"))
                task["_task_status"] = status      # Annotate za UI
                task["_source_path"] = str(json_path)
                tasks.append(task)
            except json.JSONDecodeError as exc:
                # Malformed JSON — log ali skip
                st.warning(f"Skipped malformed JSON: {json_path.name}")
    return tasks


def task_id_from_path(path: Path) -> str:
    """Extract task_id iz filename (no .json extension)."""
    return path.stem


def extract_failure_type(task: dict) -> str | None:
    """Map validation_summary.error_type na failure taxonomy."""
    if task["_task_status"] == "validated":
        return None
    error_type = task.get("validation_summary", {}).get("error_type", "other")
    # Mapping logic (vidi §3.3 taxonomy)
    mapping = {
        "json_parse_error": "json_parse",
        "schema_validation_error": "schema",
        "primary_concept_not_detected": "concept_not_detected",
        "row_count_mismatch": "row_mismatch",
        "row_value_mismatch": "row_mismatch",
        "sandbox_execution_error": "sandbox_error",
    }
    return mapping.get(error_type, "other")
```

### 5.2 Bootstrap reviews (first-time tool launch)

Pri prvom pokretanju, tool mora kreirati pending entries za sve tasks. Loader integration:

```python
def bootstrap_pending_reviews(tasks: list[dict], db: ManualReviewDB) -> int:
    """Insert 'pending' review za sve nove tasks. Returns count of new entries."""
    count = 0
    for task in tasks:
        task_id = task_id_from_path(Path(task["_source_path"]))
        if db.get_review(task_id) is None:
            db.upsert_review(
                task_id=task_id,
                decision="pending",
                notes="",
                concept_code=task["concept_code"],
                module_number=task["module_number"],
                difficulty=task["difficulty"],
                task_status=task["_task_status"],
                failure_type=extract_failure_type(task),
            )
            count += 1
    return count
```

---

## 6. Implementacijski redoslijed (TDD gdje smisleno)

**Workflow:** TDD za DB layer (testabilan), iterativni dev za UI (manual sanity check).

### Korak 1: Pre-flight + Streamlit dependency

1. Verify clean baseline:
   ```bash
   cd backend
   git status
   uv run pytest -q  # target 226
   ```
2. Add `streamlit>=1.40` i `streamlit-shortcuts>=0.1.9` u `pyproject.toml`
3. `uv sync`
4. Verify install: `uv run streamlit --version`
5. **Commit:** `chore(2b-1c): add streamlit + streamlit-shortcuts deps`

### Korak 2: SQLite schema + CRUD (TDD)

1. Napiši test `test_schema_init_idempotent` (RED)
2. Napiši test `test_upsert_new_review` (RED)
3. Napiši test `test_upsert_overwrite_existing` (RED)
4. Napiši test `test_get_review_not_found_returns_none` (RED)
5. Napiši test `test_list_reviews_filter_by_decision` (RED)
6. Napiši test `test_list_reviews_filter_by_concept` (RED)
7. Napiši test `test_list_reviews_filter_by_failure_type` (RED)
8. Napiši test `test_get_stats_aggregation` (RED)
9. Implementiraj `app/db/manual_review.py` da svi testovi prolaze (GREEN)
10. Run tests: `uv run pytest backend/tests/test_manual_review_db.py -v` — 8 passed
11. **Commit:** `feat(2b-1c): SQLite ManualReviewDB + 8 testova`

### Korak 3: Loaders (TDD)

1. Napiši test `test_load_all_tasks_from_validated_and_failed` (RED)
2. Napiši test `test_load_all_tasks_handles_malformed_json` (RED)
3. Napiši test `test_load_all_tasks_empty_dir` (RED)
4. Napiši test `test_extract_failure_type_mapping` (RED)
5. Napiši test `test_bootstrap_pending_reviews_idempotent` (RED)
6. Implementiraj `validation_tool/loaders.py` da svi testovi prolaze (GREEN)
7. Run tests: 13 nova passed, ukupno **~239 testova**
8. **Commit:** `feat(2b-1c): task loaders + failure_type mapper + 5 testova`
9. **Tag:** `git tag faza-2b-1c-db-layer && git push origin faza-2b-1c-db-layer`

### Korak 4: Streamlit app.py + base layout

1. Implementiraj `validation_tool/app.py` (entrypoint, sidebar nav, progress metric)
2. Implementiraj minimal `review_page.py` i `stats_page.py` (placeholder content)
3. Manual smoke test:
   ```bash
   cd backend
   uv run streamlit run scripts/validation_tool/app.py
   ```
4. Verify: opens browser, sidebar shows pages, no errors u console
5. **Commit:** `feat(2b-1c): Streamlit app entrypoint + sidebar layout`

### Korak 5: Review page — task display

1. Implementiraj task card components u `components.py`:
   - `task_metadata_panel(task)` — concept, difficulty, module, status
   - `task_content_panel(task)` — description, expected_query (syntax highlight), expected_result
2. Implementiraj `review_page.py` main flow:
   - Load tasks via cached `loaders.load_all_tasks()`
   - Bootstrap pending reviews
   - Display first task (index 0)
3. Manual test: pokreni tool, verify task se prikazuje
4. **Commit:** `feat(2b-1c): review page task display (no decisions yet)`

### Korak 6: Decision controls + notes + persistencija

1. Implementiraj decision panel u `components.py`:
   - 3 buttons (Approve / Reject / Needs-fix)
   - Notes textarea (`st.text_area`)
   - On-click: `db.upsert_review(...)` + `st.rerun()`
2. Implementiraj Prev/Next navigation buttons
3. Add session state za current task index
4. Manual test:
   - Approve 2 tasks
   - Reject 1 task
   - Verify SQLite ima 3 entries s ispravnim decisions
   - Restart tool, verify decisions persistuju
5. **Commit:** `feat(2b-1c): decision buttons + notes + SQLite persistence`

### Korak 7: Filteri (sidebar)

1. Implementiraj filter widgets u sidebar:
   - `st.selectbox("Module", [None] + modules)` 
   - `st.selectbox("Concept", [None] + concepts)`
   - `st.selectbox("Decision", [None, "pending", "approved", "rejected", "needs_fix"])`
   - `st.selectbox("Failure Type", [None, "json_parse", "schema", ..., "row_mismatch"])`
2. Filter logic: build query iz selected filtera, `db.list_reviews(**filters)`
3. Update task list based on filter, reset index to 0
4. Show filtered count: `st.caption(f"Filtered: {len(filtered)} of {total}")`
5. Manual test: filter by "needs_fix" decision, verify only matching tasks
6. **Commit:** `feat(2b-1c): sidebar filters (module/concept/decision/failure_type)`

### Korak 8: Re-run query feature

1. Implementiraj sandbox connection u `components.py` (cached via `st.cache_resource`)
2. Implementiraj `query_runner_panel(task, sandbox_runner)` per §4.5
3. Detect DML based on concept_code, pass `dml=True` to sandbox
4. Display result u dataframe; handle errors gracefully
5. Pre-flight check: ako sandbox not available, banner instead of disabled button
6. Manual test:
   - Re-run SELECT query — verify result
   - Re-run INSERT query — verify success + rollback (next run shows clean state)
7. **Commit:** `feat(2b-1c): re-run query feature + DML mode handling`

### Korak 9: Keyboard shortcuts

1. Add `streamlit-shortcuts` integration u `review_page.py`:
   - J = next task
   - K = previous task
   - A = approve current
   - R = reject current
   - F = needs_fix current
2. Test ručno: hold J → tasks advance; press A → decision saved
3. Fallback ako `streamlit-shortcuts` ne radi: pure HTML buttons s clear labels, no shortcuts
4. **Commit:** `feat(2b-1c): keyboard shortcuts (J/K/A/R/F)`

### Korak 10: Stats page

1. Implementiraj `stats_page.py`:
   - Total progress: X/Y reviewed, % completion
   - Breakdown by decision (st.dataframe ili bar chart)
   - Breakdown by concept (top 10 koncepata po pending count)
   - Breakdown by failure_type (samo failed tasks)
2. Manual test: stats reflektira current DB state
3. **Commit:** `feat(2b-1c): stats page (progress + breakdowns)`

### Korak 11: Polish (Standard sophistication touches)

1. Syntax highlighting verify (`st.code(query, language="sql")`)
2. Progress bar u sidebar (visual indikator)
3. "Next pending task" button (skip already-reviewed)
4. Empty state messages (npr. "All filtered tasks reviewed")
5. Manual test: full review of 3-5 tasks, verify UX flow
6. **Commit:** `feat(2b-1c): UX polish (syntax highlight, progress bar, empty states)`

### Korak 12: Code review checkpoint

Pokreni code review skill na:
- `manual_review.py` (DB layer)
- `loaders.py` (file IO)
- `review_page.py` + `components.py` (UI)

**Fokus:**
- SQL injection protection u CRUD (parametrized queries?)
- Race conditions u Streamlit re-run flow (npr. session state inconsistency)
- Sandbox connection lifecycle (proper cleanup?)
- Error handling u file loading

Ako HIGH findings, fix commit prije final tag-a.

### Korak 13: Final wrapup

1. Manual smoke test scenario:
   - Open tool, verify load 1+ tasks
   - Approve 2 tasks
   - Reject 1 task s notes
   - Mark 1 task as needs_fix
   - Filter by "rejected" — verify shows only rejected
   - Re-run query za 1 task — verify result displays
   - Navigate s keyboard shortcuts (J/K) — verify smooth
   - Check stats page — verify reflects 4 decisions
   - Close tool, reopen, verify all decisions persist
2. Write `docs/faza-2b-1c-wrapup.md`:
   - Functionality verification (sve iz §2.5 verification checklist)
   - Known limitations / future improvements
   - Screenshot (opcionalno) ili tekstualan opis layouta
3. Run final test suite: `uv run pytest -q` → **~239 testova prolaze**
4. **Commit:** `docs(2b-1c): wrapup + manual smoke test report`
5. **Tag:** `git tag faza-2b-1c-complete && git push origin faza-2b-1c-complete`

---

## 7. Entry kriteriji (start 2B-1C)

- [x] 2B-1E zaključena, tag `faza-2b-1e-complete` push-an
- [x] 226 testova baseline prolaze
- [x] Sandbox kontejner running (potreban za re-run query feature)
- [x] Pilot reports postoje u `data/generated_tasks/pilot/` (mogu se koristiti kao test data za tool)
- [x] `streamlit>=1.40` može se dodati u deps (network access)
- [x] Trošak: $0 (no API calls)

## 8. Exit kriteriji (kraj 2B-1C)

- [ ] Streamlit tool pokreće se s `streamlit run`
- [ ] Manual smoke test scenario iz Koraka 13 sve checked
- [ ] SQLite persistencija radi (decisions, notes)
- [ ] Filteri rade (module, concept, decision, failure_type)
- [ ] Re-run query radi za SELECT i DML
- [ ] Keyboard shortcuts rade (ili graceful fallback ako ne)
- [ ] Stats page reflektira realnu DB state
- [ ] **~239 testova prolaze** (13 nova + 226 baseline)
- [ ] `docs/faza-2b-1c-wrapup.md` postoji
- [ ] Tagovi push-ani

---

## 9. Risk register

| Rizik | Vjerojatnost | Impact | Mitigacija |
|---|---|---|---|
| `streamlit-shortcuts` ne radi s trenutnom Streamlit verzijom | Medium | Low | Graceful fallback na buttons-only navigation |
| Streamlit re-runs konfuziraju session state (npr. current_task_index reset) | High | Medium | Eksplicitno koristiti `st.session_state` za sve mutable state |
| Sandbox connection postaje stale između re-runs | Medium | Medium | `@st.cache_resource` decorator + connection health check pre-execute |
| SQLite file lock contention (rare za single-user) | Low | Low | SQLite default mode je dovoljan |
| Streamlit dev server crashes during long review session | Low | Low | Restart `streamlit run`, decisions perzistuju u SQLite |
| Re-run DML query unexpected side effects (rollback fail) | Low | High | SandboxRunner SAVEPOINT pattern (iz 2B-1B) je tested; trust impl |
| Manual smoke test ne pokrije edge case (npr. malformed JSON) | Medium | Low | Loader has try/except + warning banner; uđi u 2B-3 reactive fix |
| Tool postaje sporiji nakon 100+ tasks loaded | Low | Low | `@st.cache_data(ttl=60)` na `load_all_tasks` — re-read svakih 60s |

---

## 10. Tehnološki dug i otvorena pitanja

### Što ostaje za buduće faze (uvjetno)

| Stavka | Status nakon 2B-1C | Rok |
|---|---|---|
| Bulk actions (reject/approve cluster) | Skipped per §1.4 odluka | 2B-3 reactive ako se javi pattern |
| Diff view (current vs proposed query) | Out-of-scope | 2B-3 ili Faza 3 |
| Export to CSV in-tool | Manual `sqlite3` CSV export dovoljan | 2B-3 wrap |
| Multi-user / authentication | Out-of-scope (single user) | n/a |
| Streamlit UI automated testing | Skipped (manual testing sufficient) | n/a |
| Markdown notes rendering | Plain textarea sufficient | Reactive ako zatreba |

### Otvorena pitanja koja će 2B-3 trebati odgovoriti

- Koliko notes per task piše u prosjeku (proxy za UX evaluation tool-a)?
- Treba li dodatak "next pending task" button performance optimization?
- Da li failure_type taxonomy treba refine-anje (npr. "row_mismatch" pretiroko)?

---

## 11. Reference

- `docs/faza-2b-1d-wrapup.md` — failure mode patterns koji informiraju filter design
- `docs/faza-2b-1e-wrapup.md` — pass rate context, 2B-2 monitoring strategy
- `backend/app/schemas/generated_task.py` — `GeneratedTask` schema (CC mora pročitati prije Koraka 5)
- `backend/scripts/lib/sandbox_runner.py` — DML mode iz 2B-1B (re-run feature)
- `backend/scripts/lib/task_validator.py` — `validation_summary.error_type` source za failure_type taxonomy
- Streamlit dokumentacija: https://docs.streamlit.io/library/api-reference
- `streamlit-shortcuts` package: https://pypi.org/project/streamlit-shortcuts/

---

## 12. Što slijedi nakon 2B-1C

**2B-2 — Full generation run za 105 zadataka:**
- Budget: $5-10 realistic (informed by 2B-1D/E lessons)
- Strategija: batchevi po modulu s monitoring fokusom (failing koncepti retry budget veći)
- Output: ~70-90 validated u `data/generated_tasks/validated/`, ~15-35 failed u `failed/`

**2B-3 — Manual validation kroz Streamlit tool:**
- 105 × 5-10 min = 8-15h aktivnog review-a
- Approved tasks ulaze u finalni dataset za diplomski
- Needs-fix tasks idu kroz 2B-3 cleanup ili u re-generation batch
- Final tag: `faza-2b-complete`

**Onda:** Faza 3 — RecommenderAgent + integration s BKT modelom.

---

*Plan kraj. Start point: `git checkout main && git pull && git checkout -b faza-2b-1c-implementation && cd backend && git status && uv run pytest -q` (verify 226 passed).*
