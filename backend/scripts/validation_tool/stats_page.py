"""Stats page za 2B-1C validation tool."""

from __future__ import annotations

import streamlit as st

from app.db.manual_review import ManualReviewDB


_DECISION_ORDER = ("pending", "approved", "rejected", "needs_fix")


def _progress_section(stats: dict) -> None:
    total = stats.get("total", 0)
    reviewed = stats.get("reviewed", 0)
    pct = (reviewed / total * 100) if total else 0.0

    cols = st.columns(3)
    cols[0].metric("Total tasks", total)
    cols[1].metric("Reviewed", f"{reviewed} / {total}")
    cols[2].metric("Completion", f"{pct:.1f}%")
    st.progress(min(pct / 100, 1.0))


def _decision_section(by_decision: dict[str, int]) -> None:
    st.subheader("Breakdown by decision")
    if not by_decision:
        st.caption("Nema reviewova još.")
        return
    rows = [
        {"decision": d, "count": by_decision.get(d, 0)} for d in _DECISION_ORDER
    ]
    st.bar_chart(rows, x="decision", y="count", horizontal=False)


def _concept_section(by_concept: dict[str, int], limit: int = 10) -> None:
    st.subheader(f"Top {limit} concepts po broju zadataka")
    if not by_concept:
        st.caption("Nema podataka.")
        return
    sorted_items = sorted(by_concept.items(), key=lambda kv: -kv[1])[:limit]
    rows = [{"concept": k, "count": v} for k, v in sorted_items]
    st.dataframe(rows, hide_index=True, width="stretch")


def _failure_section(by_failure: dict[str, int]) -> None:
    st.subheader("Breakdown by failure_type (samo failed)")
    if not by_failure:
        st.caption("Nema failed zadataka — sve validated.")
        return
    rows = sorted(
        ({"failure_type": k, "count": v} for k, v in by_failure.items()),
        key=lambda r: -r["count"],
    )
    st.dataframe(rows, hide_index=True, width="stretch")


def _module_section(by_module: dict[int, int]) -> None:
    st.subheader("Breakdown by module")
    if not by_module:
        st.caption("Nema podataka.")
        return
    rows = [
        {"module": str(m), "count": c}
        for m, c in sorted(by_module.items(), key=lambda kv: kv[0])
    ]
    st.bar_chart(rows, x="module", y="count", horizontal=False)


def render(db: ManualReviewDB) -> None:
    st.title("Stats")
    stats = db.get_stats()

    _progress_section(stats)
    st.divider()
    _decision_section(stats.get("by_decision", {}))
    st.divider()
    _module_section(stats.get("by_module", {}))
    st.divider()
    _concept_section(stats.get("by_concept", {}))
    st.divider()
    _failure_section(stats.get("by_failure", {}))
