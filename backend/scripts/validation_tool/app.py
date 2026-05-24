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

import logging  # noqa: E402
import os  # noqa: E402

import streamlit as st  # noqa: E402

from app.db.manual_review import ManualReviewDB  # noqa: E402
from scripts.lib.sandbox_runner import SandboxRunner  # noqa: E402
from scripts.validation_tool import review_page, stats_page  # noqa: E402

_log = logging.getLogger(__name__)

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


@st.cache_resource
def get_sandbox_runner() -> SandboxRunner | None:
    """Lazy sandbox runner. Pre-flight ping; vraća None ako nedostupan."""
    url = os.environ.get(
        "SANDBOX_DATABASE_URL",
        "postgresql+psycopg://sandbox_admin:sandbox_dev_password@localhost:5433/sandbox",
    ).replace("postgresql+psycopg://", "postgresql://")
    runner = SandboxRunner(connection_string=url, timeout_seconds=5)
    try:
        ping = runner.execute("SELECT 1", dml=False)
    except Exception as exc:  # noqa: BLE001
        _log.warning("Sandbox pre-flight failed: %s", exc)
        return None
    if not ping.success:
        _log.warning("Sandbox pre-flight unsuccessful: %s", ping.error)
        return None
    return runner


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
            sandbox_runner=get_sandbox_runner(),
        )
    else:
        stats_page.render(db)


main()
