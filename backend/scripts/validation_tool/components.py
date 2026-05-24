"""Reusable Streamlit komponente za 2B-1C validation tool."""

from __future__ import annotations

import streamlit as st

# DML koncepti — detekcija po primary_concept za toggle dml=True u SandboxRunneru
_DML_CONCEPTS = frozenset({"insert", "update", "delete"})


def _status_badge(status: str, failure_type: str | None) -> str:
    if status == "validated":
        return "✅ validated"
    if failure_type:
        return f"❌ failed ({failure_type})"
    return "❌ failed"


def task_metadata_panel(task: dict, failure_type: str | None) -> None:
    """Prikaži metadata: concept, difficulty, status."""
    inner = task.get("task", {})
    cols = st.columns(4)
    cols[0].metric("Concept", inner.get("primary_concept", "?"))
    cols[1].metric("Difficulty", inner.get("difficulty", "?"))
    cols[2].metric("Retries", task.get("retries", 0))
    cols[3].metric("Status", _status_badge(task.get("_task_status", ""), failure_type))

    secondary = inner.get("secondary_concepts") or []
    if secondary:
        st.caption("Secondary: " + ", ".join(secondary))


def task_content_panel(task: dict) -> None:
    """Description + expected_query + expected_result + pedagogical notes."""
    inner = task.get("task", {})

    st.subheader("📝 Opis zadatka")
    st.write(inner.get("title", ""))
    st.write(inner.get("description", ""))

    st.subheader("💻 Expected query")
    st.code(inner.get("expected_query", ""), language="sql")

    st.subheader("📊 Expected result")
    expected = inner.get("expected_result", [])
    if expected:
        st.dataframe(expected, hide_index=True, use_container_width=True)
    else:
        st.caption("(empty — DML upit ili upit bez vraćenih redova)")

    misconception = inner.get("targets_misconception")
    notes = inner.get("pedagogical_notes")
    if misconception or notes:
        with st.expander("🎓 Pedagogical context", expanded=False):
            if misconception:
                st.markdown(f"**Targets misconception:** `{misconception}`")
            if notes:
                st.markdown(notes)


def failure_panel(task: dict) -> None:
    """Prikaži validation_failures (samo za failed tasks)."""
    failures = task.get("validation_failures") or []
    if not failures:
        return
    st.subheader("❓ Razlog fail-a")
    for i, f in enumerate(failures, start=1):
        level = f.get("level", "?")
        code = f.get("code", "?")
        msg = f.get("message", "")
        details = f.get("details") or {}
        with st.expander(f"#{i} {level} / {code}", expanded=(i == 1)):
            st.write(msg)
            if details:
                st.json(details)


def decision_panel(
    task: dict,
    db,  # ManualReviewDB
    failure_type: str | None,
    concept_module_map: dict[str, int],
) -> None:
    """Decision buttons (Approve/Reject/Needs-fix) + notes textarea.

    Save je idempotent — uvijek upsert s trenutnim state-om.
    """
    task_id = task["_task_id"]
    inner = task.get("task", {})
    concept = inner.get("primary_concept", "unknown")
    difficulty = int(inner.get("difficulty", 0))
    module_number = concept_module_map.get(concept, 0)

    current = db.get_review(task_id)
    current_decision = current.decision if current else "pending"
    current_notes = current.notes if current else ""

    st.subheader("✏️ Decision")
    st.caption(f"Current: **{current_decision}**")

    def _save(decision: str, notes: str) -> None:
        db.upsert_review(
            task_id=task_id,
            decision=decision,  # type: ignore[arg-type]
            notes=notes,
            concept_code=concept,
            module_number=module_number,
            difficulty=difficulty,
            task_status=task["_task_status"],
            failure_type=failure_type,
        )

    notes_key = f"notes_{task_id}"
    notes = st.text_area(
        "Notes",
        value=current_notes,
        key=notes_key,
        height=100,
        placeholder="Opcionalne bilješke (zašto reject, koja izmjena needs-fix, itd.)",
    )

    cols = st.columns(3)
    if cols[0].button("✓ Approve", key=f"approve_{task_id}", type="primary"):
        _save("approved", notes)
        st.rerun()
    if cols[1].button("✗ Reject", key=f"reject_{task_id}"):
        _save("rejected", notes)
        st.rerun()
    if cols[2].button("⚠ Needs Fix", key=f"needsfix_{task_id}"):
        _save("needs_fix", notes)
        st.rerun()


def query_runner_panel(task: dict, sandbox_runner) -> None:
    """Opcionalni re-run zadanog upita u sandbox-u. Auto-rollback za DML."""
    if sandbox_runner is None:
        st.warning(
            "⚠ Sandbox nije dostupan (postavi SANDBOX_DATABASE_URL i pokreni docker). "
            "Re-run feature je onemogućen."
        )
        return

    inner = task.get("task", {})
    concept = inner.get("primary_concept", "")
    is_dml = concept in _DML_CONCEPTS

    st.subheader("⚙ Re-run query u sandboxu")
    cols = st.columns([3, 1])
    with cols[0]:
        mode = "DML (write, auto-rollback)" if is_dml else "SELECT (read-only)"
        st.caption(f"Mode: {mode}")
    with cols[1]:
        rerun = st.button("▶ Run", key=f"rerun_{task['_task_id']}")

    if not rerun:
        return

    query = inner.get("expected_query", "")
    with st.spinner("Izvršavanje upita…"):
        try:
            result = sandbox_runner.execute(query, dml=is_dml)
        except Exception as exc:  # noqa: BLE001 — UI hard-error guard
            st.error(f"Sandbox exception: {type(exc).__name__}: {exc}")
            return

    if not result.success:
        st.error(f"✗ Sandbox vratio error: {result.error}")
        return

    st.success(
        f"✓ {len(result.rows)} rows · {result.execution_time_ms} ms · "
        f"columns: {', '.join(result.column_names) or '(none)'}"
    )
    if result.rows:
        st.dataframe(result.rows, hide_index=True, use_container_width=True)
    else:
        st.caption("(no rows returned)")


def navigation_panel(total: int) -> None:
    """Prev/Next buttons koji updejtaju st.session_state.current_idx."""
    idx = st.session_state.get("current_idx", 0)
    cols = st.columns([1, 1, 6])
    if cols[0].button("◀ Prev", disabled=idx <= 0, key="nav_prev"):
        st.session_state.current_idx = max(0, idx - 1)
        st.rerun()
    if cols[1].button("Next ▶", disabled=idx >= total - 1, key="nav_next"):
        st.session_state.current_idx = min(total - 1, idx + 1)
        st.rerun()
