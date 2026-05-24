"""Stats page za 2B-1C validation tool — placeholder verzija (Korak 4)."""

from __future__ import annotations

import streamlit as st

from app.db.manual_review import ManualReviewDB


def render(db: ManualReviewDB) -> None:
    st.title("Stats")
    st.caption("Placeholder — breakdowns dolaze u Koraku 10.")
    stats = db.get_stats()
    st.json(stats)
