"""Streamlit entrypoint za 2B-1C validation tool.

Pokretanje:
    cd backend
    uv run streamlit run scripts/validation_tool/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend/ je u sys.path (Streamlit run ne aktivira package context)
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import streamlit as st  # noqa: E402

from app.db.manual_review import ManualReviewDB  # noqa: E402
from scripts.validation_tool import review_page, stats_page  # noqa: E402

_REPO_ROOT = _BACKEND_ROOT.parent
DB_PATH = _REPO_ROOT / "data" / "generated_tasks" / "manual_review.sqlite"
TASKS_DIR = _REPO_ROOT / "data" / "generated_tasks"
CONCEPTS_DIR = _BACKEND_ROOT / "config" / "concepts"


def _configure_page() -> None:
    st.set_page_config(
        page_title="2B-3 Validation Tool",
        page_icon="✓",
        layout="wide",
        initial_sidebar_state="expanded",
    )


@st.cache_resource
def get_db() -> ManualReviewDB:
    return ManualReviewDB(DB_PATH)


def main() -> None:
    _configure_page()
    db = get_db()

    st.sidebar.title("2B-3 Validation Tool")
    page = st.sidebar.radio("Page", ["Review", "Stats"], key="nav_page")

    stats = db.get_stats()
    total = stats["total"]
    reviewed = stats["reviewed"]
    pct = int(100 * reviewed / max(total, 1))
    st.sidebar.metric("Progress", f"{reviewed}/{total}", delta=f"{pct}%")
    if total > 0:
        st.sidebar.progress(reviewed / total)

    if page == "Review":
        review_page.render(
            db=db,
            tasks_dir=TASKS_DIR,
            concepts_dir=CONCEPTS_DIR,
        )
    else:
        stats_page.render(db)


main()
