"""Testovi za agents/persistence.py — persist_attempt().

Cleanup strategija: db_session fixture radi rollback ali persist_attempt eksplicitno
commita (D6 zahtjev). Koristimo persist_env fixture koji kreira test entitete
(user, module, task) u committed transakciji i briše sve u teardown-u.
Svaki test koristi svježi SessionLocal() za pozivanje persist_attempt.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy import delete

import agents.persistence as _persistence_mod
from agents.evaluation import EvaluationOutcome
from agents.persistence import persist_attempt
from app.db.models import Attempt, Module, Task, User
from app.db.session import SessionLocal


# ---------------------------------------------------------------------------
# Pomocne konstante i factory
# ---------------------------------------------------------------------------

_USERNAME = "persist_test_user_3a2"
_EMAIL = "persist_3a2@test.example"
_MODULE_NUMBER = 9801  # ne kolidira s pravim modulima (1-7)


def _outcome(
    *,
    is_correct: bool = True,
    error_type: str | None = None,
    execution_time_ms: int = 10,
    rows_returned: int = 1,
) -> EvaluationOutcome:
    return EvaluationOutcome(
        is_correct=is_correct,
        verdict="correct" if is_correct else "incorrect",
        error_type=error_type,
        execution_time_ms=execution_time_ms,
        rows_returned=rows_returned,
        detail="ok",
    )


# ---------------------------------------------------------------------------
# Fixture: kreira test entitete, briše sve u teardown-u
# ---------------------------------------------------------------------------


@pytest.fixture
def persist_env():
    """Setup/teardown za persistence testove.

    Kreira committed user + module + task. Teardown briše sve attempts
    vezane uz test usera, pa i samog usera, task i module.
    Nema oslanjanja na db_session rollback jer persist_attempt commita.
    """
    user_id = task_id = module_id = None

    with SessionLocal() as sess:
        mod = Module(
            number=_MODULE_NUMBER,
            name="Test modul persist 3a2",
            difficulty="beginner",
            order_index=_MODULE_NUMBER,
        )
        sess.add(mod)
        sess.flush()

        task = Task(
            module_id=mod.id,
            title="Test task persist 3a2",
            description="Persistence test task",
            sandbox_schema="ecommerce_v1",
            expected_query="SELECT 1",
            expected_result=[],
            difficulty=1,
        )
        sess.add(task)
        sess.flush()

        user = User(
            username=_USERNAME,
            email=_EMAIL,
            password_hash="dummy_hash",
        )
        sess.add(user)
        sess.commit()

        module_id = mod.id
        task_id = task.id
        user_id = user.id

    yield {"user_id": user_id, "task_id": task_id}

    with SessionLocal() as cleanup:
        cleanup.execute(delete(Attempt).where(Attempt.user_id == user_id))
        cleanup.execute(delete(User).where(User.id == user_id))
        cleanup.execute(delete(Task).where(Task.id == task_id))
        cleanup.execute(delete(Module).where(Module.id == module_id))
        cleanup.commit()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_returns_positive_id(persist_env):
    """persist_attempt vraca int id > 0; red postoji u DB s tocnim is_correct/error_type."""
    user_id = persist_env["user_id"]
    task_id = persist_env["task_id"]

    with SessionLocal() as sess:
        attempt_id = persist_attempt(sess, user_id, task_id, "SELECT 1", _outcome(is_correct=True))

    assert isinstance(attempt_id, int)
    assert attempt_id > 0

    with SessionLocal() as verify:
        row = verify.get(Attempt, attempt_id)
        assert row is not None
        assert row.user_id == user_id
        assert row.task_id == task_id
        assert row.is_correct is True
        assert row.error_type is None
        assert row.attempt_number == 1
        assert row.xp_awarded == 0
        assert row.hint_requested is False


def test_detail_persisted(persist_env):
    """detail (Faza 4.3 Stage 0b) se upisuje u attempts.detail — postojeći
    EvaluationOutcome.detail tekst, bez ikakve transformacije."""
    user_id = persist_env["user_id"]
    task_id = persist_env["task_id"]

    with SessionLocal() as sess:
        attempt_id = persist_attempt(
            sess, user_id, task_id, "SELECT 2", _outcome(is_correct=False, error_type="wrong_columns")
        )

    with SessionLocal() as verify:
        row = verify.get(Attempt, attempt_id)
        assert row.detail == "ok"  # _outcome factory postavlja detail="ok"


# ---------------------------------------------------------------------------
# Monotono rastuce attempt_number
# ---------------------------------------------------------------------------


def test_attempt_number_monotonic_increment(persist_env):
    """3 uzastopna persist-a daju attempt_number 1, 2, 3."""
    user_id = persist_env["user_id"]
    task_id = persist_env["task_id"]
    ids = []

    for _ in range(3):
        with SessionLocal() as sess:
            aid = persist_attempt(sess, user_id, task_id, "SELECT 1", _outcome())
            ids.append(aid)

    with SessionLocal() as verify:
        numbers = [verify.get(Attempt, aid).attempt_number for aid in ids]

    assert numbers == [1, 2, 3]


# ---------------------------------------------------------------------------
# NULL za tocne attemptove
# ---------------------------------------------------------------------------


def test_error_type_null_on_correct(persist_env):
    """error_type=None za tocan attempt se upisuje kao SQL NULL, ne string 'None'."""
    user_id = persist_env["user_id"]
    task_id = persist_env["task_id"]

    with SessionLocal() as sess:
        aid = persist_attempt(sess, user_id, task_id, "SELECT 1", _outcome(is_correct=True, error_type=None))

    with SessionLocal() as verify:
        row = verify.get(Attempt, aid)
        assert row.error_type is None


def test_error_type_stored_for_incorrect(persist_env):
    """error_type string se upisuje za netocne attemptove."""
    user_id = persist_env["user_id"]
    task_id = persist_env["task_id"]

    with SessionLocal() as sess:
        aid = persist_attempt(
            sess, user_id, task_id, "SELECT nope",
            _outcome(is_correct=False, error_type="execution_error"),
        )

    with SessionLocal() as verify:
        row = verify.get(Attempt, aid)
        assert row.error_type == "execution_error"
        assert row.is_correct is False


# ---------------------------------------------------------------------------
# Race simulacija — retry path
# ---------------------------------------------------------------------------


def test_race_retry_succeeds(persist_env):
    """Race simulacija: stale COUNT vraca 0 → IntegrityError → retry → uspjeh s number=2.

    Pre-insert attempt_number=1 (committed) simulira concurrent submit koji je 'pobijedio'.
    Mockamo _count_attempts da vraci 0 (stale read) na prvom pozivu, zatim pravi COUNT.
    persist_attempt mora: detektirati IntegrityError na uq_attempts_user_task_number,
    rollbackati, retryjati s pravim brojem (2), uspjesno commitati.
    """
    user_id = persist_env["user_id"]
    task_id = persist_env["task_id"]

    # Simuliraj "pobjednicki" concurrent submit — attempt_number=1 vec postoji
    with SessionLocal() as preinsert:
        preinsert.add(
            Attempt(
                user_id=user_id,
                task_id=task_id,
                submitted_query="SELECT 1 -- concurrent",
                is_correct=True,
                error_type=None,
                execution_time_ms=5,
                rows_returned=1,
                attempt_number=1,
                xp_awarded=0,
                hint_requested=False,
            )
        )
        preinsert.commit()

    real_count = _persistence_mod._count_attempts
    call_count = [0]

    def mock_count(session, uid, tid):
        call_count[0] += 1
        if call_count[0] == 1:
            return 0  # stale read — kao da nema prethodnih attemptova
        return real_count(session, uid, tid)

    with patch("agents.persistence._count_attempts", side_effect=mock_count):
        with SessionLocal() as sess:
            aid = persist_attempt(sess, user_id, task_id, "SELECT 1 -- retry", _outcome())

    assert aid > 0
    assert call_count[0] >= 2, "Retry se nije dogodio — COUNT mora biti pozvan barem 2x"

    with SessionLocal() as verify:
        row = verify.get(Attempt, aid)
        assert row.attempt_number == 2, f"Ocekivano attempt_number=2, dobiveno {row.attempt_number}"
