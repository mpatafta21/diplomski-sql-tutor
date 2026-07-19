"""Purge dev demo usera (Faza 4.4-0, KORAK 2) — briše ISKLJUČIVO usere sa
sentinel prefiksom ``demo44_`` (username ILI email) i SVE njihove ovisne retke.

Pokreni iz ``backend/``::

    uv run python -m scripts.purge_demo_users

Sigurnost: NIKAD ne briše po nečem osim prefiksa ``demo44_``. Prefiks se
provjerava u Pythonu (``str.startswith``), NE kroz SQL ``LIKE`` (izbjegava
``_`` wildcard zamku — ``LIKE 'demo44_%'`` bi ``_`` tretirao kao wildcard).

FK red brisanja (IZMJEREN iz information_schema, ne pretpostavljen):
  - ``attempts.user_id`` = NO ACTION → attempts se briše ručno PRIJE ``users``.
  - ``attempts.id`` ← ``skill_mastery_history.attempt_id`` (NO ACTION) i
    ``xp_log.attempt_id`` (NO ACTION) → ta dva se brišu PRIJE ``attempts``.
  - Ostalo (``misconceptions``, ``recommendations_log``, ``skill_mastery``,
    ``streaks``, ``user_badges``) = ON DELETE CASCADE → padne s ``users``.
"""

from __future__ import annotations

import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Attempt, SkillMasteryHistory, User, XpLog
from app.db.session import SessionLocal

logger = logging.getLogger("purge_demo_users")

#: Jedini kriterij brisanja. Mijenjati OVDJE i nigdje drugdje.
SENTINEL = "demo44_"


def find_demo_user_ids(session: Session) -> list[int]:
    """ID-evi usera čiji username ILI email počinje sentinel prefiksom.

    Provjera je ``startswith`` u Pythonu (ne SQL LIKE) da ``_`` u prefiksu
    ne bi bio protumačen kao LIKE wildcard.
    """
    rows = session.execute(select(User.id, User.username, User.email)).all()
    return [
        uid
        for uid, username, email in rows
        if (username or "").startswith(SENTINEL) or (email or "").startswith(SENTINEL)
    ]


def purge_demo_users(session: Session) -> dict[str, int]:
    """Obriši sve ``demo44_`` usere + ovisne retke. Vrati broj obrisanih redaka.

    Idempotentno: nema li demo usera, vraća ``{"users_matched": 0}`` bez izmjena.
    Sve u jednoj transakciji (commit na kraju).
    """
    ids = find_demo_user_ids(session)
    counts: dict[str, int] = {"users_matched": len(ids)}
    if not ids:
        return counts

    # Red je bitan zbog NO ACTION FK-ova (vidi docstring modula).
    counts["skill_mastery_history"] = session.execute(
        delete(SkillMasteryHistory).where(SkillMasteryHistory.user_id.in_(ids))
    ).rowcount
    counts["xp_log"] = session.execute(
        delete(XpLog).where(XpLog.user_id.in_(ids))
    ).rowcount
    counts["attempts"] = session.execute(
        delete(Attempt).where(Attempt.user_id.in_(ids))
    ).rowcount
    # users → CASCADE pokriva misconceptions, recommendations_log,
    # skill_mastery, streaks, user_badges.
    counts["users"] = session.execute(
        delete(User).where(User.id.in_(ids))
    ).rowcount

    session.commit()
    return counts


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    with SessionLocal() as session:
        counts = purge_demo_users(session)
    logger.info("Purge demo44_ usera — obrisano po tablici: %s", counts)


if __name__ == "__main__":
    main()
