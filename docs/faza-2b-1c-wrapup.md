# FAZA 2B-1C — Wrap-up

**Status:** COMPLETE (svi koraci iz plana §6 isporučeni; code review NEEDS_FIX → MEDIUM-i fixani)
**Trošak:** $0 (no LLM calls — pure tooling)
**Trajanje:** ~3h aktivnog rada (uključujući VS crash recovery na Koraku 8)
**Završni tag:** `faza-2b-1c-complete`

---

## 1. Sažetak

2B-1C je isporučio Streamlit-based **manual validation tool** za AI-generirane SQL zadatke iz 2B-2 batch pipeline-a. Tool ima multi-page layout (Review + Stats), SQLite persistenciju decisions/notes, sidebar filtere, i opcionalni sandbox re-run upita. Kod je novo napisan (876 LOC across 7 fajlova) i pokriven s 19 novih testova (8 loader + 11 DB). Test count: 226 baseline → **245 passed**.

**Decision tree exit:** sav plan §6 (Koraci 1-13) je obrađen. Streamlit-shortcuts dependency je odbačen u Koraku 9 nakon što se pokazao flaky pod Streamlit rerun ciklusom (iframe listener detach) — fallback na button-only navigation per plan §4.4.

---

## 2. Isporučeno po Korakima

| Korak | Naslov | Commit | Napomena |
|-------|--------|--------|----------|
| 1 | Pre-flight + streamlit dep | `2723370` | streamlit + streamlit-shortcuts u pyproject.toml |
| 2 | SQLite ManualReviewDB | `c76421a` | 11 testova, parameterized CRUD |
| 3 | Task loaders + failure_type mapper | `674db5b` | 8 testova |
| 4 | Streamlit app entrypoint | `fecf420` | sys.path fix za package resolution |
| 5 | Review page task display | `90ba58d` | Cached loading + session-state navigation |
| 6 | Decision buttons + notes + persistencija | `11200ff` | Verified s 3 decision tipa kroz browser reload |
| 7 | Sidebar filteri (module/concept/decision/failure) | `cede4f9` | DB-side filtering za decision/metadata |
| 8 | Re-run query u sandboxu | `321a2f8` | SELECT read-only + DML auto-rollback; verified s live sandbox |
| 9 | Keyboard shortcuts | `0aeb8b9` | **Fallback per plan §4.4** — streamlit-shortcuts drop |
| 10 | Stats page (progress + breakdowns) | `2e4401e` | Total/reviewed metrics + Vega bar charts + dataframe top-10 |
| 11 | Polish — Next pending button | `247fade` | Skipa already-reviewed; disabled kad sve done |
| 12 | Code review checkpoint | `6d027b1` | NEEDS_FIX → 3 MEDIUM fixed |
| 13 | Final wrapup | (ovaj doc) | + tag `faza-2b-1c-complete` |

---

## 3. Code review nalazi i fixovi

Reviewer: `superpowers:code-reviewer`. Fokus per plan §6 Korak 12 (SQL injection, race conditions, sandbox lifecycle, error handling).

### MEDIUM fixed (commit `6d027b1`)

1. **`review_page.py:127-136`** — filter_signature je sad tuple koji uključuje `len(filtered)`. Sprječava index drift kad `bootstrap_pending_reviews` mid-session doda nove zadatke i clamp logika silently skoči na pogrešan task.
2. **`components.py:161-168`** — `query_runner_panel` na sandbox exception poziva `st.cache_resource.clear()` + UI info banner. Recovery path nakon Docker bounce-a (stari kod je zauvijek držao dead psycopg connection).
3. **`app.py:37,72`** — page i sidebar title fix: `2B-3 Validation Tool` → `2B-1C Validation Tool`. Pogrešna fazna oznaka.

### LOW shipped as-is (sve označene od reviewera kao "ship as follow-up")

- `loaders.py:108` — `int(inner.get("difficulty"))` nije guard-an protiv non-numeric → potencijalni crash u `bootstrap_pending_reviews` ako 2B-2 ikad emitira string difficulty.
- `loaders.py:107` — missing `primary_concept` silently default-a na "unknown" + module=0 bez warninga.
- `components.py:113-131` — `notes_key = f"notes_{task_id}"` perzistira u session_state cijeli session; memory leak za stotinu+ tasks, plus stale-state risk.
- `app.py:52-55` — URL prefix replacement strip-a samo `postgresql+psycopg://`, ne `postgresql+psycopg2://`.
- `app.py` modul docstring — nije eksplicitan da je tool single-reviewer.
- `components.py:80,83,134` — `db` i `sandbox_runner` parametri nemaju proper type hints (komentari umjesto annotations).
- `review_page.py:82` — jedna linija > 100 znakova (Black/Ruff).

**Razlog za defer:** sve LOW stavke su lokalne i ne sprječavaju pilotni use u 2B-3 manual review fazi. Otvoreni su kao follow-up za eventualnu refaktorizaciju ako se tool intenzivno koristi.

### Pozitivno

- **Parameterized SQL throughout** — zero string interpolation u CRUD-u. `Literal[...]` type guard + `CHECK (decision IN (...))` u schema-i kao defense-in-depth.
- **Idempotent bootstrap** — safe na svaki Streamlit rerun.
- **Loader gracefully skip-a malformed JSON** s warning logom.
- **`@dataclass(frozen=True)` TaskReview** — immutable, hashable.
- **Clear separation of concerns** — DB ↔ loaders ↔ orchestration ↔ UI panels ↔ entry.
- **Stats page agregira na DB layer-u** (`get_stats()` vraća dict; UI samo renderira).

---

## 4. Tehničke odluke (s posljedicama)

### 4.1 streamlit-shortcuts drop (Korak 9)

**Što:** Plan §4.4 je predviđao keyboard shortcuts J/K/A/R/F kroz `streamlit-shortcuts` paket. Wired-up implementacija je commitana, ali Playwright smoke test je pokazao da nakon prvog reruna `el.click()` synthetic event uopće ne fire-a (iframe replacement detacha listener iz parent document-a; `clear_shortcuts() + add_shortcuts()` re-init pattern nije pomogao pouzdano).

**Posljedica:** Manualni reviewer mora koristiti mouse za prev/next/decisions. UX malo sporiji, ali deterministički.

**Razlog za fallback:** plan §4.4 je eksplicitno dopustio "pure HTML buttons s clear labels, no shortcuts" kao fallback. Time-budget rationale: alternative bi zahtijevale custom JS injection s vlastitim listener-reattach mehanizmom (~3-4h dodatnog rada, neizvjestan ishod). Korisnik je pragmatic-confirmed odluku.

**Dep cleanup:** `streamlit-shortcuts>=0.1.9` uklonjen iz `pyproject.toml`, `uv sync` uninstalled v1.2.1.

### 4.2 .playwright-mcp/ u .gitignore

Smoke testovi tijekom razvoja generiraju snapshot i console log artefakte u `.playwright-mcp/`. Direktorij dodan u `.gitignore` (commit `f71f316`) jer su lokalni development artefakti, ne reproducibilan output.

### 4.3 SQLite WAL nije aktiviran

Tool je single-reviewer. Concurrent reviewers nisu use-case. Reviewer je preporučio dodati to u module docstring kao explicit assumption — to je LOW item shipped as-is.

---

## 5. Test count progression

```
Baseline (kraj 2B-1E):              226 passed
+ test_manual_review_db.py (11):    237 passed (Korak 2)
+ test_validation_tool_loaders.py (8): 245 passed (Korak 3)
─────────────────────────────────────────────────
Total na kraju 2B-1C:               245 passed
```

Plan §2.5 očekivao ~239 (13 novih). Dobili 19 novih (+5 vs target) jer su loader edge cases (corrupt JSON, missing dirs, bootstrap idempotency) zahtijevali više pokrivenosti.

---

## 6. Known limitations (za 2B-3 stage)

- **Keyboard shortcuts nedostaju** (drop u Koraku 9) — reviewer koristi mouse only.
- **Single-reviewer assumption** — više istovremenih reviewera na istom DB-u nije podržano (SQLite bez WAL-a, no row locking).
- **Sandbox connection cache** — sad ima recovery path (clear-on-exception), ali UI zahtijeva manual reload nakon clear-a.
- **Loaders robustness** — non-numeric `difficulty` ili missing `primary_concept` neće gracefully degradirati (LOW items, defer-ani).
- **2B-2 batch dependency** — tool je smislen tek kad 2B-2 generira validated/ i failed/ direktorije; trenutno radi nad pilot data-om (3 zadatka u stagingu).

---

## 7. Što slijedi

**2B-2: SQL task batch generation** (per docs/faza-2b-plan.md). Budget $5-10 s monitoring fokusom na `group_by` (per 2B-1E findings). Output: ~100 validated tasks u `data/generated_tasks/validated/` koje će ovaj tool review-irati.

**2B-3: Manual review stage** — tool koji je ovdje isporučen. Otvorena pitanja koja će 2B-3 trebati odgovoriti (per plan §10.2):
- Treba li bedge/score sistem za review fatigue management?
- Workflow za bulk-reject pattern-based failures?
- Export approved tasks u format za production import?

---

## 8. Git artefakti

**Branch:** `faza-2b-1c-implementation`
**Komitovi (15):** od `7100047` (plan doc) do `6d027b1` (code review fix).

**Tagovi:**
- `faza-2b-1c-db-layer` — nakon Koraka 3 (DB layer + loader testovi green)
- `faza-2b-1c-complete` — nakon Koraka 13 (final wrapup)

**Files changed (vs main):**
```
 backend/app/db/manual_review.py                | +210
 backend/scripts/validation_tool/__init__.py    |   +0
 backend/scripts/validation_tool/app.py         |  +98
 backend/scripts/validation_tool/components.py  | +224
 backend/scripts/validation_tool/loaders.py     | +121
 backend/scripts/validation_tool/review_page.py | +156
 backend/scripts/validation_tool/stats_page.py  |  +82
 backend/tests/test_manual_review_db.py         | +XXX
 backend/tests/test_validation_tool_loaders.py  | +227
```

**Push:** `git push origin faza-2b-1c-implementation --tags`

---

## 9. Lessons learned

1. **Streamlit custom components + iframe lifecycle = trap za listener-based features.** Bilo koja library koja injecta JS listener iz custom componenta će umrijeti nakon prvog reruna. Future tooling: drži listenere u top-level page script via `st.components.v1.html()` s eksplicitnim re-attach na svaki render, ili koristi server-side polling state.
2. **Playwright synthetic events != trusted events.** `el.click()` iz JS-a ne triggera Streamlit's React onChange. Sve smoke testove koji prate state moraju ići preko `mcp__playwright__browser_click` (trusted) ili real keyboard.press, ne JS injection.
3. **Code review pre tag-a je vrijedan.** Reviewer je pronašao 3 MEDIUM-a koja su sva bila netrivijalna user-facing (index drift, stale sandbox, wrong title). Fixevi su trajali ~10 min. Bez review-a bi defekti došli do mentora.
