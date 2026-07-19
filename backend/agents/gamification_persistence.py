"""Transakcijska perzistencija GamificationAgenta — Faza 3D.2.

Jedan atomski writer `persist_gamification()` + čisti read-helperi. Sav numerički
račun (XP, level, streak, badge eval) delegira se na čistu logiku iz
`gamification_logic.py` (3D.1) — ovdje je samo I/O i transakcijski redoslijed.

Idempotencija (dvostruki deliver istog attempt-result informa NE smije duplirati
nuspojave) osigurana je na tri mjesta:
  - XP po attemptu: partial-unique `xp_log(attempt_id) WHERE attempt_id IS NOT NULL`
    + `ON CONFLICT DO NOTHING RETURNING id`; users.xp/att.xp_awarded se diže SAMO
    ako je red stvarno umetnut (RETURNING ne-prazan).
  - Badge: PK `user_badges(user_id, badge_id)` + `ON CONFLICT DO NOTHING RETURNING`;
    badge-XP se dodjeljuje samo na stvarni insert.
  - current_streak/level: izvedeni (recompute), ne inkrementi → prirodno idempotentni.

Napomena (NALAZ #7): `task.module_id` ≠ primary_concept.module za 3/83 taska.
`load_attempted_modules` koristi AUTORITATIVAN put `task.module_id → modules.number`
(odluka 3D.2): "attempted a TASK in module M" je svojstvo taska, 1 modul/pokušaj.
"""

from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from agents.db_helpers import load_mastery_snapshot
from agents.gamification_logic import (
    BadgeFacts,
    compute_xp,
    eval_badges,
    level_for_xp,
    mastered_concepts,
    streak_from_active_dates,
)
from app.db.models import (
    Attempt,
    Badge,
    Module,
    Streak,
    Task,
    User,
    UserBadge,
    XpLog,
)

_log = logging.getLogger(__name__)

# Dani se računaju u lokalnoj zoni studenta (streak granica je lokalni ponoć).
_TZ = ZoneInfo("Europe/Zagreb")

_REASON_ATTEMPT = "attempt"


class AttemptNotFound(Exception):
    """Attempt s danim attempt_id ne postoji (npr. zakašnjeli/duplikat inform)."""


# ---------------------------------------------------------------------------
# Read-helperi (čiste read funkcije, bez side-effecta)
# ---------------------------------------------------------------------------


def load_attempt(session: Session, attempt_id: int) -> Attempt | None:
    """Dohvati committed Attempt po PK (attempt_number, task_id, created_at, is_correct)."""
    return session.get(Attempt, attempt_id)


def load_task_difficulty(session: Session, task_id: int) -> int:
    """Vrati tasks.difficulty (1..5). Raises ValueError ako task ne postoji."""
    difficulty = session.scalar(select(Task.difficulty).where(Task.id == task_id))
    if difficulty is None:
        raise ValueError(f"Task {task_id} nema difficulty / ne postoji")
    return difficulty


def user_has_correct(session: Session, user_id: int) -> bool:
    """True ako korisnik ima barem jedan točan pokušaj (is_correct=true)."""
    row = session.scalar(
        select(Attempt.id)
        .where(Attempt.user_id == user_id, Attempt.is_correct.is_(True))
        .limit(1)
    )
    return row is not None


def load_attempted_modules(session: Session, user_id: int) -> frozenset[int]:
    """Skup BROJEVA modula (modules.number, 0..6) u kojima je korisnik pokušao task.

    AUTORITATIVAN put (3D.2 odluka): task.module_id → modules.number.
    NE primary-concept put, NE unija svih koncepata. Vraća modules.number
    (NE module_id/PK) jer eval_badges uspoređuje s brojevima modula.
    """
    rows = session.execute(
        select(Module.number)
        .select_from(Attempt)
        .join(Task, Task.id == Attempt.task_id)
        .join(Module, Module.id == Task.module_id)
        .where(Attempt.user_id == user_id)
        .distinct()
    ).scalars()
    return frozenset(rows)


def load_evaluable_modules(session: Session) -> frozenset[int]:
    """Brojevi modula (BEZ 0) koji imaju barem jedan AKTIVAN zadatak.

    Kriterij za `explorer` (NALAZ #22): izvodi se iz PODATAKA, ne iz hardkodirane
    šestice. Modul 6 je od 4.4-0e neaktivan (NALAZ #19) pa ispada iz kriterija;
    ako ikad postane evaluabilan, bedž se automatski proširi bez izmjene koda.
    Modul 0 (transverzalni) je izuzet — nikad nije bio dio kriterija (3D nalaz #6).
    """
    rows = session.execute(
        select(Module.number)
        .join(Task, Task.module_id == Module.id)
        .where(Task.is_active.is_(True), Module.number != 0)
        .distinct()
    ).scalars()
    return frozenset(rows)


def load_earned_badge_codes(session: Session, user_id: int) -> set[str]:
    """Skup kodova bedževa koje korisnik VEĆ ima."""
    rows = session.execute(
        select(Badge.code)
        .join(UserBadge, UserBadge.badge_id == Badge.id)
        .where(UserBadge.user_id == user_id)
    ).scalars()
    return set(rows)


def _load_badge_catalog(session: Session) -> dict[str, tuple[int, int]]:
    """Vrati {code: (badge_id, xp_reward)} za sve seedane bedževe."""
    rows = session.execute(select(Badge.code, Badge.id, Badge.xp_reward)).all()
    return {code: (bid, xp_reward) for code, bid, xp_reward in rows}


# ---------------------------------------------------------------------------
# Transakcijski writer
# ---------------------------------------------------------------------------


def persist_gamification(session: Session, payload: dict) -> dict:
    """Primijeni gamifikacijske nuspojave jednog attempt-result informa, atomično.

    Koraci 1–9 (vidi 3D.2 spec). Sve u jednoj transakciji; commit na kraju.

    Args:
        session: SQLAlchemy session (bit će commitana ovdje).
        payload: 3A attempt-result payload — koristi attempt_id i verdict.

    Returns:
        Sažetak {xp_delta, new_level, new_badges, current_streak} za log.

    Raises:
        AttemptNotFound: ako attempt_id ne postoji u bazi.
        KeyError/ValueError: na nevaljan payload (nedostaje verdict / nepoznat verdict).
    """
    attempt_id = payload["attempt_id"]
    verdict = payload["verdict"]

    # 1. attempt + difficulty
    att = load_attempt(session, attempt_id)
    if att is None:
        raise AttemptNotFound(f"attempt_id={attempt_id} ne postoji")
    user_id = att.user_id
    difficulty = load_task_difficulty(session, att.task_id)

    # 2. XP delta (verdict iz PAYLOADA, attempt_number iz committed reda)
    delta = compute_xp(difficulty, verdict, att.attempt_number)

    # 3. dnevni streak red (lokalni dan); upsert inkrementira attempts_count
    today = att.created_at.astimezone(_TZ).date()
    streak_stmt = (
        pg_insert(Streak)
        .values(user_id=user_id, date=today, attempts_count=1)
        .on_conflict_do_update(
            index_elements=["user_id", "date"],
            set_={"attempts_count": Streak.attempts_count + 1},
        )
    )
    session.execute(streak_stmt)

    user = session.get(User, user_id)

    # 4. XP po attemptu — idempotentno (partial-unique na attempt_id)
    xp_applied = 0
    if delta > 0:
        xp_stmt = (
            pg_insert(XpLog)
            .values(
                user_id=user_id,
                attempt_id=attempt_id,
                delta=delta,
                reason=_REASON_ATTEMPT,
            )
            .on_conflict_do_nothing(
                index_elements=["attempt_id"],
                index_where=XpLog.attempt_id.isnot(None),
            )
            .returning(XpLog.id)
        )
        inserted = session.execute(xp_stmt).scalar()
        if inserted is not None:
            user.xp += delta
            att.xp_awarded = delta
            xp_applied = delta
        # inserted is None → već obrađen attempt; NE inkrementiraj (idempotencija)

    # 5. streak recompute iz SVIH dana korisnika (izvedeno, idempotentno)
    active_dates = set(
        session.execute(
            select(Streak.date).where(Streak.user_id == user_id)
        ).scalars()
    )
    current_streak, longest = streak_from_active_dates(active_dates, today)
    user.current_streak = current_streak
    user.longest_streak = max(user.longest_streak, longest)
    user.last_active_at = att.created_at

    # 6. badge činjenice
    facts = BadgeFacts(
        has_correct=user_has_correct(session, user_id),
        mastered=mastered_concepts(load_mastery_snapshot(session, user_id)),
        current_streak=current_streak,
        attempted_modules=load_attempted_modules(session, user_id),
        evaluable_modules=load_evaluable_modules(session),
    )
    candidate_codes = eval_badges(facts)

    # 7. dodijeli nove bedževe (PK idempotentno) + badge-XP
    earned = load_earned_badge_codes(session, user_id)
    catalog = _load_badge_catalog(session)
    new_badges: list[str] = []
    for code in candidate_codes - earned:
        badge_id, xp_reward = catalog[code]
        badge_stmt = (
            pg_insert(UserBadge)
            .values(user_id=user_id, badge_id=badge_id)
            .on_conflict_do_nothing(index_elements=["user_id", "badge_id"])
            .returning(UserBadge.user_id)
        )
        if session.execute(badge_stmt).scalar() is None:
            continue  # već dodijeljen (race) — preskoči
        new_badges.append(code)
        if xp_reward > 0:
            # attempt_id=NULL → partial-unique ne hvata; nema konflikta.
            session.execute(
                pg_insert(XpLog).values(
                    user_id=user_id,
                    attempt_id=None,
                    delta=xp_reward,
                    reason=code,
                )
            )
            user.xp += xp_reward
            xp_applied += xp_reward

    # 8. level recompute NAKON badge-XP-a (redoslijed bitan)
    user.level = level_for_xp(user.xp)

    # 9. commit
    session.commit()

    return {
        "xp_delta": xp_applied,
        "new_level": user.level,
        "new_badges": new_badges,
        "current_streak": current_streak,
    }
