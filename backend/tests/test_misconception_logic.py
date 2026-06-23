"""Unit testovi za agents/misconception_logic.py — 3B.2.

Testiraju outcome-based misconception detekciju bez SPADE omotača.

Misconception code = "{primary_concept}__{error_type}" za konceptualne greške.
Mehaničke greške (syntax_error, timeout, execution_error, unsupported_eval) → None.

Cleanup strategija: misconception_env kreira committed usera i briše ga
(CASCADE → misconceptions) u teardown-u. Svaki test otvara svježi SessionLocal().
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, select

from agents.misconception_logic import record_misconception_if_failed
from app.db.models import Misconception, User
from app.db.session import SessionLocal

# ---------------------------------------------------------------------------
# Konstante
# ---------------------------------------------------------------------------

_MISC_USERNAME = "misc_test_user_3b2"
_MISC_EMAIL = "misc_3b2@test.example"


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def misconception_env():
    """Kreira committed test usera. Teardown briše usera (CASCADE → misconceptions)."""
    user_id = None

    with SessionLocal() as sess:
        user = User(
            username=_MISC_USERNAME,
            email=_MISC_EMAIL,
            password_hash="dummy_hash_3b2",
        )
        sess.add(user)
        sess.commit()
        user_id = user.id

    yield {"user_id": user_id}

    with SessionLocal() as cleanup:
        cleanup.execute(delete(Misconception).where(Misconception.user_id == user_id))
        cleanup.execute(delete(User).where(User.id == user_id))
        cleanup.commit()


# ---------------------------------------------------------------------------
# Pomoćna funkcija
# ---------------------------------------------------------------------------


def _get_misconception(user_id: int, code: str) -> Misconception | None:
    with SessionLocal() as sess:
        row = sess.execute(
            select(Misconception).where(
                Misconception.user_id == user_id,
                Misconception.code == code,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        sess.expunge(row)
        return row


# ---------------------------------------------------------------------------
# T1 — is_correct=True → None, nema reda
# ---------------------------------------------------------------------------


def test_correct_attempt_returns_none(misconception_env):
    """Točan attempt ne stvara misconception."""
    user_id = misconception_env["user_id"]

    with SessionLocal() as sess:
        result = record_misconception_if_failed(
            sess, user_id, "left_join", "row_mismatch", is_correct=True
        )

    assert result is None
    assert _get_misconception(user_id, "left_join__row_mismatch") is None


# ---------------------------------------------------------------------------
# T2 — Mehaničke greške → None (ne bilježe se)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("error_type", [
    "syntax_error",
    "timeout",
    "execution_error",
    "unsupported_eval",
])
def test_mechanical_errors_return_none(misconception_env, error_type):
    """Mehaničke greške (sintaksa, timeout, execution, unsupported) → None, nema reda."""
    user_id = misconception_env["user_id"]

    with SessionLocal() as sess:
        result = record_misconception_if_failed(
            sess, user_id, "left_join", error_type, is_correct=False
        )

    assert result is None
    assert _get_misconception(user_id, f"left_join__{error_type}") is None


# ---------------------------------------------------------------------------
# T3 — Konceptualna greška → kreira red s occurrences=1
# ---------------------------------------------------------------------------


def test_row_mismatch_creates_misconception(misconception_env):
    """row_mismatch na left_join → kreira 'left_join__row_mismatch', occurrences=1."""
    user_id = misconception_env["user_id"]
    expected_code = "left_join__row_mismatch"

    with SessionLocal() as sess:
        result = record_misconception_if_failed(
            sess, user_id, "left_join", "row_mismatch", is_correct=False
        )

    assert result == expected_code
    row = _get_misconception(user_id, expected_code)
    assert row is not None
    assert row.occurrences == 1
    assert row.code == expected_code
    assert row.first_seen is not None
    assert row.last_seen is not None


# ---------------------------------------------------------------------------
# T4 — Ponovljena ista greška → occurrences=2 (EXIT KRITERIJ §3B)
# ---------------------------------------------------------------------------


def test_repeated_failure_increments_occurrences(misconception_env):
    """Isti (user, code) dva puta → occurrences=2. Ovo je exit kriterij iz plana §3B."""
    user_id = misconception_env["user_id"]
    code = "left_join__row_mismatch"

    with SessionLocal() as sess:
        record_misconception_if_failed(sess, user_id, "left_join", "row_mismatch", False)

    with SessionLocal() as sess:
        record_misconception_if_failed(sess, user_id, "left_join", "row_mismatch", False)

    row = _get_misconception(user_id, code)
    assert row is not None
    assert row.occurrences == 2, f"Ocekivano occurrences=2, dobiveno {row.occurrences}"
    # last_seen mora biti >= first_seen
    assert row.last_seen >= row.first_seen


# ---------------------------------------------------------------------------
# T5 — Različit error_type isti koncept → dva odvojena reda
# ---------------------------------------------------------------------------


def test_different_error_type_creates_separate_rows(misconception_env):
    """row_mismatch i wrong_columns na istom konceptu → dva odvojena Misconception reda."""
    user_id = misconception_env["user_id"]

    with SessionLocal() as sess:
        c1 = record_misconception_if_failed(
            sess, user_id, "agg_count", "row_mismatch", False
        )
    with SessionLocal() as sess:
        c2 = record_misconception_if_failed(
            sess, user_id, "agg_count", "wrong_columns", False
        )

    assert c1 == "agg_count__row_mismatch"
    assert c2 == "agg_count__wrong_columns"

    r1 = _get_misconception(user_id, "agg_count__row_mismatch")
    r2 = _get_misconception(user_id, "agg_count__wrong_columns")
    assert r1 is not None and r1.occurrences == 1
    assert r2 is not None and r2.occurrences == 1


# ---------------------------------------------------------------------------
# T6 — primary_concept=None → None (guard)
# ---------------------------------------------------------------------------


def test_none_primary_concept_returns_none(misconception_env):
    """Ako primary_concept nije poznat (None), ne formiramo code → None."""
    user_id = misconception_env["user_id"]

    with SessionLocal() as sess:
        result = record_misconception_if_failed(
            sess, user_id, None, "row_mismatch", is_correct=False
        )

    assert result is None


# ---------------------------------------------------------------------------
# T7 — error_type=None → None (guard)
# ---------------------------------------------------------------------------


def test_none_error_type_returns_none(misconception_env):
    """Ako error_type nije poznat (None), ne formiramo code → None."""
    user_id = misconception_env["user_id"]

    with SessionLocal() as sess:
        result = record_misconception_if_failed(
            sess, user_id, "left_join", None, is_correct=False
        )

    assert result is None
