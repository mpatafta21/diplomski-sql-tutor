"""Persistencija rezultata evaluacije u attempts tablicu.

Jedino mjesto u 3A koje commita (D6 zahtjev): EvaluatorAgent mora commitati
attempt red PRIJE nego pošalje inform poruku, da 3B/3D agenti čitaju committed
red po attempt_id.

Race fix: attempt_number se računa kao COUNT(*)+1. Dva simultana submita istog
(user, task) mogu dobiti isti broj → UNIQUE constraint (uq_attempts_user_task_number)
hvata koliziju → rollback + retry (max 3 puta).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from agents.evaluation import EvaluationOutcome
from app.db.models import Attempt

_UQ_CONSTRAINT = "uq_attempts_user_task_number"
_MAX_RETRIES = 3


def _count_attempts(session: Session, user_id: int, task_id: int) -> int:
    """Broji postojeće attempts za (user_id, task_id). Ekstrahovano radi testabilnosti."""
    return (
        session.scalar(
            select(func.count()).select_from(Attempt).where(
                Attempt.user_id == user_id,
                Attempt.task_id == task_id,
            )
        )
        or 0
    )


def persist_attempt(
    session: Session,
    user_id: int,
    task_id: int,
    submitted_query: str,
    outcome: EvaluationOutcome,
) -> int:
    """Zapisuje EvaluationOutcome u attempts tablicu i commita.

    Args:
        session: SQLAlchemy session — bit će commitana unutar ove funkcije (D6).
        user_id: FK na users.id (mora postojati).
        task_id: FK na tasks.id (mora postojati).
        submitted_query: SQL koji je student predao.
        outcome: Rezultat evaluate() — ne mijenja se ovdje.

    Returns:
        attempt.id — validan tek nakon commita.

    Raises:
        RuntimeError: Ako race conflict ostane nakon _MAX_RETRIES pokušaja.
        IntegrityError: Za sve ostale integrity greške (ne retry).
    """
    for _ in range(_MAX_RETRIES):
        count = _count_attempts(session, user_id, task_id)
        attempt_number = count + 1

        row = Attempt(
            user_id=user_id,
            task_id=task_id,
            submitted_query=submitted_query,
            is_correct=outcome.is_correct,
            error_type=outcome.error_type,
            # Stage 0b: correct nema detalj (evaluate() tamo stavlja placeholder
            # "OK" — to nije pedagoški sadržaj pa se NE persistira).
            detail=None if outcome.is_correct else (outcome.detail or None),
            execution_time_ms=outcome.execution_time_ms,
            rows_returned=outcome.rows_returned,
            attempt_number=attempt_number,
            xp_awarded=0,
            hint_requested=False,
        )
        session.add(row)
        try:
            session.commit()
            return row.id
        except IntegrityError as exc:
            if _UQ_CONSTRAINT not in str(exc):
                raise
            session.rollback()

    raise RuntimeError(
        f"persist_attempt: max retries ({_MAX_RETRIES}) exceeded "
        f"for user_id={user_id} task_id={task_id}"
    )
