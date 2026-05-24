"""Review page za 2B-1C validation tool."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.db.manual_review import ManualReviewDB

from . import components
from .loaders import (
    bootstrap_pending_reviews,
    extract_failure_type,
    load_all_tasks,
    load_concept_module_map,
)


_FAILURE_TYPES = [
    "row_mismatch",
    "concept_not_detected",
    "sandbox_error",
    "schema",
    "json_parse",
    "other",
]
_DECISIONS = ["pending", "approved", "rejected", "needs_fix"]


@st.cache_data(ttl=60)
def _cached_load_tasks(tasks_dir: str) -> list[dict]:
    return load_all_tasks(Path(tasks_dir))


@st.cache_data(ttl=300)
def _cached_concept_map(concepts_dir: str) -> dict[str, int]:
    return load_concept_module_map(Path(concepts_dir))


def _sidebar_filters(tasks: list[dict], concept_map: dict[str, int]) -> dict:
    """Render sidebar filter selectboxes. Vraća dict filter clauses (None = sve)."""
    modules = sorted({concept_map.get(t["task"]["primary_concept"], 0) for t in tasks})
    concepts = sorted({t["task"]["primary_concept"] for t in tasks})

    st.sidebar.divider()
    st.sidebar.subheader("Filteri")
    module = st.sidebar.selectbox(
        "Module", [None, *modules], format_func=lambda v: "—" if v is None else str(v)
    )
    concept = st.sidebar.selectbox(
        "Concept", [None, *concepts], format_func=lambda v: "—" if v is None else v
    )
    decision = st.sidebar.selectbox(
        "Decision",
        [None, *_DECISIONS],
        format_func=lambda v: "—" if v is None else v,
    )
    failure_type = st.sidebar.selectbox(
        "Failure type",
        [None, *_FAILURE_TYPES],
        format_func=lambda v: "—" if v is None else v,
    )
    return {
        "module_number": module,
        "concept_code": concept,
        "decision": decision,
        "failure_type": failure_type,
    }


def _apply_filters(
    tasks: list[dict],
    filters: dict,
    db: ManualReviewDB,
    concept_map: dict[str, int],
) -> list[dict]:
    """Filter tasks list by sidebar selection — koristi DB filter za decision,
    in-memory za module/concept/failure_type (DB ima sve metadata)."""
    # Najprije DB filter (uključuje denormalized metadata)
    db_filtered_ids: set[str] | None = None
    if any(filters[k] is not None for k in ("decision", "module_number", "failure_type", "concept_code")):
        reviews = db.list_reviews(
            decision=filters["decision"],
            concept_code=filters["concept_code"],
            module_number=filters["module_number"],
            failure_type=filters["failure_type"],
        )
        db_filtered_ids = {r.task_id for r in reviews}

    if db_filtered_ids is None:
        return tasks
    return [t for t in tasks if t["_task_id"] in db_filtered_ids]


def render(
    db: ManualReviewDB,
    tasks_dir: Path,
    concepts_dir: Path,
) -> None:
    st.title("Review")

    tasks = _cached_load_tasks(str(tasks_dir))
    concept_map = _cached_concept_map(str(concepts_dir))

    if not tasks:
        st.info(
            f"Nema zadataka u `{tasks_dir}/validated` ili `{tasks_dir}/failed`. "
            "Pokreni 2B-2 batch generation da napuniš direktorije."
        )
        return

    added = bootstrap_pending_reviews(tasks, db, concept_map)
    if added > 0:
        st.toast(f"Bootstrapped {added} new pending reviews")

    filters = _sidebar_filters(tasks, concept_map)
    filtered = _apply_filters(tasks, filters, db, concept_map)
    st.sidebar.caption(f"Filtered: {len(filtered)} / {len(tasks)}")

    if not filtered:
        st.info("Nijedan zadatak ne match-a trenutne filtere.")
        return

    # Session-state navigation — reset ako filter promijeni count
    state_key = "filter_signature"
    sig = (filters["module_number"], filters["concept_code"], filters["decision"], filters["failure_type"])
    if st.session_state.get(state_key) != sig:
        st.session_state.current_idx = 0
        st.session_state[state_key] = sig

    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0
    idx = max(0, min(st.session_state.current_idx, len(filtered) - 1))
    st.session_state.current_idx = idx

    task = filtered[idx]
    task_id = task["_task_id"]
    failure_type = extract_failure_type(task)

    st.caption(f"Task {idx + 1} / {len(filtered)} — `{task_id}`")

    components.navigation_panel(len(filtered))
    components.task_metadata_panel(task, failure_type=failure_type)
    components.task_content_panel(task)
    components.failure_panel(task)
    components.decision_panel(task, db, failure_type, concept_map)
