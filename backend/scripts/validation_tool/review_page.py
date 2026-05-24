"""Review page za 2B-1C validation tool — placeholder verzija (Korak 4)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.db.manual_review import ManualReviewDB


def render(
    db: ManualReviewDB,
    tasks_dir: Path,
    concepts_dir: Path,
) -> None:
    st.title("Review")
    st.caption("Placeholder — task display dolazi u Koraku 5.")
    st.write(f"Tasks dir: `{tasks_dir}`")
    st.write(f"Concepts dir: `{concepts_dir}`")
    st.write(f"DB path: `{db.db_path}`")
