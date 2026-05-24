"""Reusable Streamlit komponente za 2B-1C validation tool."""

from __future__ import annotations

import streamlit as st


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
