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


@st.cache_data(ttl=60)
def _cached_load_tasks(tasks_dir: str) -> list[dict]:
    return load_all_tasks(Path(tasks_dir))


@st.cache_data(ttl=300)
def _cached_concept_map(concepts_dir: str) -> dict[str, int]:
    return load_concept_module_map(Path(concepts_dir))


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

    # Session-state navigation
    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0
    idx = max(0, min(st.session_state.current_idx, len(tasks) - 1))
    st.session_state.current_idx = idx

    task = tasks[idx]
    task_id = task["_task_id"]

    st.caption(f"Task {idx + 1} / {len(tasks)} — `{task_id}`")

    components.task_metadata_panel(task, failure_type=extract_failure_type(task))
    components.task_content_panel(task)
    components.failure_panel(task)
