"""Outcome-based misconception detekcija za KnowledgeModelAgent — 3B.2.

Misconception code = "{primary_concept}__{error_type}" kad je attempt netočan
i error_type je konceptualni signal (ne mehanička greška).

Mehaničke greške (syntax_error, timeout, execution_error, unsupported_eval)
se preskakuju — student je možda samo pretipkao, nije signal pogrešnog razumijevanja.
Konceptualni signali: row_mismatch, wrong_columns, empty_result.

TODO (Faza 4): prava semantička detekcija kroz sqlglot AST (npr. wrong_join_type,
left_join_vs_inner_with_null). Trenutni kod bilježi outcome, ne uzrok.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Misconception

# Mehaničke greške — ne bilježi se kao misconception
_MECHANICAL_ERRORS: frozenset[str] = frozenset({
    "syntax_error",
    "timeout",
    "execution_error",
    "unsupported_eval",
    # ERRATA #66 — oba su omaška/smetnja, ne zabluda:
    "explain_submitted",  # student zalijepio EXPLAIN
    "plan_unavailable",   # EXPLAIN nije uspio (infrastruktura)
    # 🔴 `plan_mismatch` NAMJERNO NIJE ovdje — anti-pattern je stvarna zabluda
    # o tome kako baza koristi indeks, i mora se bilježiti kao misconception.
})


def record_misconception_if_failed(
    session: Session,
    user_id: int,
    primary_concept: str | None,
    error_type: str | None,
    is_correct: bool,
) -> str | None:
    """Upsertaj Misconception red ako je attempt netočan i greška je konceptualna.

    Args:
        session:         SQLAlchemy session — commita unutar ove funkcije.
        user_id:         FK na users.id.
        primary_concept: primarni koncept zadatka iz attempt-result payloada.
        error_type:      klasifikacija greške iz EvaluatorAgenta.
        is_correct:      ishod attempta.

    Returns:
        misconception code (str) ako je zabilježena, None inače.
    """
    if is_correct:
        return None
    if primary_concept is None or error_type is None:
        return None
    if error_type in _MECHANICAL_ERRORS:
        return None

    code = f"{primary_concept}__{error_type}"
    now = datetime.now(timezone.utc)

    row = session.execute(
        select(Misconception).where(
            Misconception.user_id == user_id,
            Misconception.code == code,
        )
    ).scalar_one_or_none()

    if row is None:
        row = Misconception(
            user_id=user_id,
            code=code,
            occurrences=1,
            first_seen=now,
            last_seen=now,
        )
        session.add(row)
    else:
        row.occurrences += 1
        row.last_seen = now

    session.commit()
    return code
