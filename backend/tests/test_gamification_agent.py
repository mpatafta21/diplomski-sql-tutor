"""Testovi za 3D.2 — persist_gamification() transakcijski writer + E2E wrapper.

Većina testova gađa persist_gamification() direktno (brzo, bez XMPP); jedan E2E
test dokazuje Template routing inform/attempt-result → GamificationAgent → DB.

Cleanup: persist_gamification commita, pa db_session rollback ne pomaže. Koristi
se gam_env fixture koji kreira committed entitete i briše ih u teardown-u
(xp_log, user_badges, streaks, skill_mastery, attempts, test-taskove, usera).
Moduli i koncepti su seedani — NE brišu se.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pytest
import spade
from spade.behaviour import OneShotBehaviour
from sqlalchemy import delete, func, select

from agents.base import TutorAgent
from agents.gamification_agent import GamificationAgent
from agents.gamification_persistence import persist_gamification
from agents.messages import Ontology, Performative
from app.core import config
from app.db.models import (
    Attempt,
    Badge,
    Concept,
    Module,
    SkillMastery,
    Streak,
    Task,
    User,
    UserBadge,
    XpLog,
)
from app.db.session import SessionLocal

_USERNAME = "gam_test_user_3d2"
_EMAIL = "gam_3d2@test.example"


# ---------------------------------------------------------------------------
# Fixture + factory helperi
# ---------------------------------------------------------------------------


@pytest.fixture
def gam_env():
    """Committed user; factoryji za task/attempt/mastery; potpun teardown."""
    created_task_ids: list[int] = []

    with SessionLocal() as sess:
        user = User(username=_USERNAME, email=_EMAIL, password_hash="dummy_3d2")
        sess.add(user)
        sess.commit()
        user_id = user.id

    def _module_id(number: int) -> int:
        with SessionLocal() as s:
            mid = s.scalar(select(Module.id).where(Module.number == number))
        assert mid is not None, f"Modul number={number} nije seedan"
        return mid

    def make_task(module_number: int = 1, difficulty: int = 1) -> int:
        with SessionLocal() as s:
            task = Task(
                module_id=_module_id(module_number),
                title="gam test task",
                description="gam 3d2",
                sandbox_schema="ecommerce_v1",
                expected_query="SELECT 1",
                expected_result=[],
                difficulty=difficulty,
            )
            s.add(task)
            s.commit()
            tid = task.id
        created_task_ids.append(tid)
        return tid

    def make_attempt(
        task_id: int,
        *,
        is_correct: bool,
        created_at: datetime,
        attempt_number: int = 1,
    ) -> int:
        with SessionLocal() as s:
            att = Attempt(
                user_id=user_id,
                task_id=task_id,
                submitted_query="SELECT 1",
                is_correct=is_correct,
                error_type=None if is_correct else "row_mismatch",
                execution_time_ms=5,
                rows_returned=1,
                attempt_number=attempt_number,
                created_at=created_at,
            )
            s.add(att)
            s.commit()
            return att.id

    def set_mastery(codes: list[str], p_l: float = 0.9) -> None:
        with SessionLocal() as s:
            for code in codes:
                cid = s.scalar(select(Concept.id).where(Concept.code == code))
                assert cid is not None, f"Koncept {code} nije seedan"
                s.add(SkillMastery(user_id=user_id, concept_id=cid, p_l=p_l))
            s.commit()

    def set_user_xp(xp: int, level: int = 1) -> None:
        with SessionLocal() as s:
            u = s.get(User, user_id)
            u.xp = xp
            u.level = level
            s.commit()

    def get_user() -> User:
        with SessionLocal() as s:
            u = s.get(User, user_id)
            s.expunge(u)
            return u

    yield {
        "user_id": user_id,
        "make_task": make_task,
        "make_attempt": make_attempt,
        "set_mastery": set_mastery,
        "set_user_xp": set_user_xp,
        "get_user": get_user,
    }

    with SessionLocal() as c:
        c.execute(delete(XpLog).where(XpLog.user_id == user_id))
        c.execute(delete(UserBadge).where(UserBadge.user_id == user_id))
        c.execute(delete(Streak).where(Streak.user_id == user_id))
        c.execute(delete(SkillMastery).where(SkillMastery.user_id == user_id))
        c.execute(delete(Attempt).where(Attempt.user_id == user_id))
        for tid in created_task_ids:
            c.execute(delete(Task).where(Task.id == tid))
        c.execute(delete(User).where(User.id == user_id))
        c.commit()


def _payload(attempt_id: int, verdict: str, **extra) -> dict:
    base = {"attempt_id": attempt_id, "verdict": verdict, "is_correct": verdict == "correct"}
    base.update(extra)
    return base


def _count_xp(user_id: int, reason: str | None = None) -> int:
    with SessionLocal() as s:
        stmt = select(func.count()).select_from(XpLog).where(XpLog.user_id == user_id)
        if reason is not None:
            stmt = stmt.where(XpLog.reason == reason)
        return s.scalar(stmt)


def _count_badges(user_id: int) -> int:
    with SessionLocal() as s:
        return s.scalar(
            select(func.count()).select_from(UserBadge).where(UserBadge.user_id == user_id)
        )


_DAY = datetime(2030, 3, 10, 12, 0, tzinfo=timezone.utc)  # podne UTC → isti dan u Zagrebu


# ---------------------------------------------------------------------------
# IDEMPOTENCIJA — ključno
# ---------------------------------------------------------------------------


def test_idempotent_double_deliver(gam_env):
    """Dvaput isti attempt_id (correct) → xp/level/badges/streak nepromijenjeni nakon 2."""
    tid = gam_env["make_task"](module_number=1, difficulty=1)
    aid = gam_env["make_attempt"](tid, is_correct=True, created_at=_DAY)

    with SessionLocal() as s:
        first = persist_gamification(s, _payload(aid, "correct"))

    u1 = gam_env["get_user"]()
    badges1 = _count_badges(gam_env["user_id"])

    with SessionLocal() as s:
        second = persist_gamification(s, _payload(aid, "correct"))

    u2 = gam_env["get_user"]()
    badges2 = _count_badges(gam_env["user_id"])

    # 1. poziv: attempt XP (20) + first_correct badge (10) = 30, level 1, 1 badge, streak 1
    assert first["xp_delta"] == 30
    assert u1.xp == 30
    # 2. poziv: ništa novo
    assert second["xp_delta"] == 0
    assert u2.xp == u1.xp == 30
    assert u2.level == u1.level
    assert u2.current_streak == u1.current_streak == 1
    assert badges2 == badges1 == 1


def test_attempt_xp_tied_to_insert(gam_env):
    """2. deliver ne diže users.xp (xp_log RETURNING prazan na konfliktu)."""
    tid = gam_env["make_task"](difficulty=3)
    aid = gam_env["make_attempt"](tid, is_correct=True, created_at=_DAY)

    with SessionLocal() as s:
        persist_gamification(s, _payload(aid, "correct"))
    xp_after_first = gam_env["get_user"]().xp

    with SessionLocal() as s:
        persist_gamification(s, _payload(aid, "correct"))
    xp_after_second = gam_env["get_user"]().xp

    assert xp_after_second == xp_after_first
    # samo JEDAN "attempt" xp_log red postoji (idempotencija)
    assert _count_xp(gam_env["user_id"], reason="attempt") == 1


# ---------------------------------------------------------------------------
# NETOČAN ATTEMPT — delta=0, ali streak/explorer žive
# ---------------------------------------------------------------------------


def test_incorrect_attempt_no_xp_but_streak(gam_env):
    """Netočan pokušaj: delta=0, nema 'attempt' xp_log reda, ALI streaks dobiva red."""
    tid = gam_env["make_task"](difficulty=2)
    aid = gam_env["make_attempt"](tid, is_correct=False, created_at=_DAY)

    with SessionLocal() as s:
        summary = persist_gamification(s, _payload(aid, "incorrect"))

    u = gam_env["get_user"]()
    assert summary["xp_delta"] == 0
    assert u.xp == 0
    assert _count_xp(gam_env["user_id"], reason="attempt") == 0
    assert u.current_streak == 1  # streak živi na netočnom pokušaju
    with SessionLocal() as s:
        streak_rows = s.scalar(
            select(func.count()).select_from(Streak).where(Streak.user_id == gam_env["user_id"])
        )
    assert streak_rows == 1
    assert _count_badges(gam_env["user_id"]) == 0  # has_correct=False → nema first_correct


# ---------------------------------------------------------------------------
# FIRST-SOLVE GATE — već riješen task NE farma XP (bugfix 4.6-eval)
# ---------------------------------------------------------------------------


def test_resolve_already_solved_no_xp(gam_env):
    """Već točno riješen task NE dodjeljuje XP ponovno: 2. točan pokušaj →
    already_solved=True, 0 novih 'attempt' xp_log redova, users.xp nepromijenjen."""
    tid = gam_env["make_task"](difficulty=3)
    a1 = gam_env["make_attempt"](
        tid, is_correct=True, created_at=_DAY, attempt_number=1
    )
    with SessionLocal() as s:
        first = persist_gamification(s, _payload(a1, "correct"))
    xp_after_first = gam_env["get_user"]().xp

    a2 = gam_env["make_attempt"](
        tid, is_correct=True, created_at=_DAY, attempt_number=2
    )
    with SessionLocal() as s:
        second = persist_gamification(s, _payload(a2, "correct"))
    xp_after_second = gam_env["get_user"]().xp

    assert first["already_solved"] is False
    assert second["already_solved"] is True
    assert second["xp_delta"] == 0
    assert xp_after_second == xp_after_first
    # Samo PRVI solve nosi 'attempt' xp_log red — re-solve ga ne dodaje.
    assert _count_xp(gam_env["user_id"], reason="attempt") == 1


def test_first_correct_after_incorrect_awards(gam_env):
    """Task s ranijim SAMO netočnim pokušajima: prvi točan je PRVO rješavanje →
    nosi XP, already_solved=False (gate ne smije gledati incorrect kao solve)."""
    tid = gam_env["make_task"](difficulty=2)
    a1 = gam_env["make_attempt"](
        tid, is_correct=False, created_at=_DAY, attempt_number=1
    )
    with SessionLocal() as s:
        persist_gamification(s, _payload(a1, "incorrect"))

    a2 = gam_env["make_attempt"](
        tid, is_correct=True, created_at=_DAY, attempt_number=2
    )
    with SessionLocal() as s:
        summary = persist_gamification(s, _payload(a2, "correct"))

    assert summary["already_solved"] is False
    assert summary["xp_delta"] > 0
    assert _count_xp(gam_env["user_id"], reason="attempt") == 1


def test_solved_task_does_not_block_other_task(gam_env):
    """Gate je per-task: riješen task A ne gasi XP za PRVO rješavanje taska B."""
    ta = gam_env["make_task"](difficulty=1)
    aa = gam_env["make_attempt"](
        ta, is_correct=True, created_at=_DAY, attempt_number=1
    )
    with SessionLocal() as s:
        persist_gamification(s, _payload(aa, "correct"))

    tb = gam_env["make_task"](difficulty=1)
    ab = gam_env["make_attempt"](
        tb, is_correct=True, created_at=_DAY, attempt_number=1
    )
    with SessionLocal() as s:
        summary = persist_gamification(s, _payload(ab, "correct"))

    assert summary["already_solved"] is False
    assert summary["xp_delta"] > 0


# ---------------------------------------------------------------------------
# BADGE AWARD + xp_reward, bez ponavljanja
# ---------------------------------------------------------------------------


def test_first_correct_badge_awarded_once(gam_env):
    """Prvi correct dodjeli first_correct (+10 xp, xp_log reason=first_correct);
    drugi attempt NE dodjeljuje ponovno (PK)."""
    t1 = gam_env["make_task"](difficulty=1)
    a1 = gam_env["make_attempt"](t1, is_correct=True, created_at=_DAY)

    with SessionLocal() as s:
        persist_gamification(s, _payload(a1, "correct"))

    assert _count_badges(gam_env["user_id"]) == 1
    assert _count_xp(gam_env["user_id"], reason="first_correct") == 1
    xp_after_first = gam_env["get_user"]().xp  # 20 attempt + 10 badge = 30
    assert xp_after_first == 30

    # drugi (različit) correct attempt — first_correct se NE dodjeljuje opet
    t2 = gam_env["make_task"](difficulty=1)
    a2 = gam_env["make_attempt"](t2, is_correct=True, created_at=_DAY, attempt_number=1)
    with SessionLocal() as s:
        persist_gamification(s, _payload(a2, "correct"))

    assert _count_badges(gam_env["user_id"]) == 1  # i dalje 1
    assert _count_xp(gam_env["user_id"], reason="first_correct") == 1
    # +20 (attempt) ali NE +10 badge ponovno → 30 + 20 = 50
    assert gam_env["get_user"]().xp == 50


# ---------------------------------------------------------------------------
# LEVEL recompute NAKON badge-XP-a (dokaz koraka 8)
# ---------------------------------------------------------------------------


def test_level_recompute_after_badge_xp(gam_env):
    """Attempt-XP=0 (incorrect) ne prelazi prag, ali badge-XP (join_master +50) prelazi
    → level skoči s 1 na 2. Dokazuje da se level računa NAKON badge-XP-a."""
    gam_env["set_user_xp"](85, level=1)
    gam_env["set_mastery"](["inner_join", "left_join", "right_join"], p_l=0.9)

    tid = gam_env["make_task"](module_number=3, difficulty=2)
    aid = gam_env["make_attempt"](tid, is_correct=False, created_at=_DAY)

    with SessionLocal() as s:
        summary = persist_gamification(s, _payload(aid, "incorrect"))

    u = gam_env["get_user"]()
    assert "join_master" in summary["new_badges"]
    assert summary["xp_delta"] == 50  # samo badge-XP (attempt delta=0)
    assert u.xp == 135
    assert u.level == 2  # 1 + 135//100 — prijelaz isključivo zbog badge-XP-a


# ---------------------------------------------------------------------------
# STREAK preko dana
# ---------------------------------------------------------------------------


def test_streak_consecutive_then_gap(gam_env):
    """3 uzastopna dana → current=3; rupa → current reset na 1, longest ostaje 3."""
    uid = gam_env["user_id"]
    days = [
        datetime(2030, 5, 1, 12, 0, tzinfo=timezone.utc),
        datetime(2030, 5, 2, 12, 0, tzinfo=timezone.utc),
        datetime(2030, 5, 3, 12, 0, tzinfo=timezone.utc),
    ]
    last = None
    for d in days:
        tid = gam_env["make_task"]()
        aid = gam_env["make_attempt"](tid, is_correct=False, created_at=d)
        with SessionLocal() as s:
            last = persist_gamification(s, _payload(aid, "incorrect"))
    assert last["current_streak"] == 3
    assert gam_env["get_user"]().current_streak == 3
    assert gam_env["get_user"]().longest_streak == 3

    # rupa: preskoči 2030-05-04, pokušaj na 2030-05-05
    gap_day = datetime(2030, 5, 5, 12, 0, tzinfo=timezone.utc)
    tid = gam_env["make_task"]()
    aid = gam_env["make_attempt"](tid, is_correct=False, created_at=gap_day)
    with SessionLocal() as s:
        after_gap = persist_gamification(s, _payload(aid, "incorrect"))

    assert after_gap["current_streak"] == 1  # reset
    u = gam_env["get_user"]()
    assert u.current_streak == 1
    assert u.longest_streak == 3  # longest > current, ne pada


# ---------------------------------------------------------------------------
# Europe/Zagreb dan (tz konverzija)
# ---------------------------------------------------------------------------


def test_zagreb_day_boundary(gam_env):
    """Attempt u 23:30 UTC = sljedeći dan u Zagrebu → streak red na lokalni dan."""
    uid = gam_env["user_id"]
    created = datetime(2030, 6, 10, 23, 30, tzinfo=timezone.utc)  # 01:30 CEST 11.6.
    tid = gam_env["make_task"]()
    aid = gam_env["make_attempt"](tid, is_correct=False, created_at=created)

    with SessionLocal() as s:
        persist_gamification(s, _payload(aid, "incorrect"))

    with SessionLocal() as s:
        streak_date = s.scalar(select(Streak.date).where(Streak.user_id == uid))
    assert streak_date.isoformat() == "2030-06-11"  # Zagreb dan, ne UTC 06-10


# ---------------------------------------------------------------------------
# EXPLORER pin: number-put + modul 0 se NE broji
# ---------------------------------------------------------------------------


def test_explorer_module_zero_excluded(gam_env):
    """Modul 0 (transverzalni) NE ulazi u explorer kriterij.

    4.4-0f / NALAZ #22: kriterij nije fiksnih {1..6} nego moduli koji STVARNO
    imaju aktivne zadatke. Invarijanta koju test čuva: pokušaj u modulu 0 NE
    nadomješta modul koji nedostaje.

    🔴 Skup je 2026-08-14 narastao s {1..5} na **{1..6}** (ERRATA #66): M6 je
    dobio ispravne zadatke i plan-presence evaluaciju. Kriterij se proširio SAM,
    kako je 4.4-0f i predviđao — zato je ovdje trebalo dopuniti test, ne kod.

    🔴 Da M6 nije dosežan, ovo bi bedž učinilo NEDOSTIŽNIM (regresija #22 i
    mehanizam #25). Provjereno simulacijom, ne rezoniranjem:
    `test_m6_reachability.py` — savršen student posjeti module 0–6.
    """
    uid = gam_env["user_id"]

    # pokušaji u modulima 1,2,3,4,5 i 0 — modul 6 NEDOSTAJE
    for mod in [1, 2, 3, 4, 5, 0]:
        tid = gam_env["make_task"](module_number=mod)
        aid = gam_env["make_attempt"](tid, is_correct=False, created_at=_DAY)
        with SessionLocal() as s:
            persist_gamification(s, _payload(aid, "incorrect"))

    earned_codes = _earned_codes(uid)
    assert "explorer" not in earned_codes, (
        "modul 0 NE smije nadomjestiti modul 6 koji nedostaje"
    )

    # dodaj modul 6 → kriterij (evaluabilni moduli) je kompletiran
    tid = gam_env["make_task"](module_number=6)
    aid = gam_env["make_attempt"](tid, is_correct=False, created_at=_DAY)
    with SessionLocal() as s:
        persist_gamification(s, _payload(aid, "incorrect"))

    assert "explorer" in _earned_codes(uid), (
        "svi evaluabilni moduli pokušani → explorer se MORA dodijeliti "
        "(dokaz da kriterij prati podatke, ne hardkodiranu šesticu)"
    )

def _earned_codes(user_id: int) -> set[str]:
    with SessionLocal() as s:
        rows = s.execute(
            select(Badge.code)
            .join(UserBadge, UserBadge.badge_id == Badge.id)
            .where(UserBadge.user_id == user_id)
        ).scalars()
        return set(rows)


# ---------------------------------------------------------------------------
# E2E — Template routing inform/attempt-result → GamificationAgent → DB
# ---------------------------------------------------------------------------


class _AttemptResultSender(TutorAgent):
    """Šalje jedan attempt-result inform GamificationAgentu i staje."""

    class _Send(OneShotBehaviour):
        async def run(self) -> None:
            payload = getattr(self.agent, "_payload", {})
            msg = self.agent.build_message(
                to=config.AGENT_GAMIFICATION_JID,
                performative=Performative.INFORM,
                ontology=Ontology.ATTEMPT_RESULT,
                payload=payload,
            )
            await self.send(msg)
            await asyncio.sleep(0.1)
            await self.agent.stop()

    async def setup(self) -> None:
        self.add_behaviour(self._Send())


@asynccontextmanager
async def _running(*agents: TutorAgent):
    for a in agents:
        await a.start(auto_register=False)
    await asyncio.sleep(0.5)
    try:
        yield
    finally:
        for a in agents:
            if a.is_alive():
                await a.stop()
        await asyncio.sleep(0.1)


async def _poll(fn, *, timeout: float = 12.0, interval: float = 0.25) -> None:
    end = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < end:
        if fn():
            return
        await asyncio.sleep(interval)
    raise TimeoutError(f"Uvjet nije zadovoljen u {timeout}s")


@pytest.mark.asyncio
async def test_e2e_attempt_result_routes_to_gamification(gam_env):
    """E2E: inform(attempt-result) → GamificationAgent perzistira xp_log red."""
    uid = gam_env["user_id"]
    tid = gam_env["make_task"](difficulty=1)
    aid = gam_env["make_attempt"](tid, is_correct=True, created_at=_DAY)

    gamification = GamificationAgent("gamification")
    sender = _AttemptResultSender("coordinator")
    sender._payload = _payload(aid, "correct")

    async with _running(gamification, sender):
        await spade.wait_until_finished([sender])
        await _poll(lambda: _count_xp(uid, reason="attempt") == 1)

    assert _count_xp(uid, reason="attempt") == 1
    assert gam_env["get_user"]().xp == 30  # 20 attempt + 10 first_correct
