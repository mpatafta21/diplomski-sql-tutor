"""🔴 ERRATA #63 — odustajanje i upis se ne smiju razići.

INVARIJANTA: za jednu predaju vrijedi **točno jedno** — ili je klijent dobio odgovor,
ili u bazi nema traga. Nikad oboje: „student vidi grešku, a pokušaj je zabilježen"
znači da je kažnjen za nešto što mu sustav tvrdi da se nije dogodilo.

🔴 ZAŠTO SKRAĆEN `update_timeout`: kvar je UTRKA između Coordinatorovog odustajanja i
Evaluatorovog commita, ne svojstvo konkretne brojke. U produkciji su
`statement_timeout = 5 s` i `DEFAULT_UPDATE_TIMEOUT = 5.0` **jednaki**, pa je utrka
odlučena režijom od nekoliko ms — što je za test neupotrebljivo tanko. Ovdje se ista
utrka postavlja široko (prozor 1 s, upit 2 s) pa je ishod determinističan. Isti kod,
isti put, samo mjerljivo.

Stvarne konstante izmjerene su zasebno i zapisane u `docs/fix-62-63-wrapup.md`.

Traži živu bazu, Prosody i SANDBOX (upit se stvarno izvršava).
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest
from sqlalchemy import delete, func, select

from agents.coordinator import CoordinatorAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.gamification_agent import GamificationAgent
from agents.knowledge_agent import KnowledgeModelAgent
from app.db.models import (
    Attempt,
    Misconception,
    SkillMastery,
    SkillMasteryHistory,
    Task,
    User,
    UserBadge,
    XpLog,
)
from app.db.session import SessionLocal
from app.main import create_app, start_gateway_stack, stop_gateway_stack
from tests.conftest import auth_header
from tests.test_coordinator import _MockRecommender  # noqa: E402

#: Prozor u kojem Coordinator odustaje. Kraći od upita → utrka je odlučena unaprijed.
_UPDATE_TIMEOUT = 1.0
#: Koliko upit spava. Mora biti < sandbox `statement_timeout` (5 s) da TOČNA
#: varijanta uopće može vratiti ispravan rezultat.
_SLEEP_S = 2


@pytest.fixture
def slow_user():
    with SessionLocal() as s:
        u = User(
            username="slow63_user",
            email="slow63@test.example",
            password_hash="dummy_hash_63",
        )
        s.add(u)
        s.commit()
        uid = u.id
        row = s.execute(
            select(Task.id, Task.expected_query)
            .where(
                Task.is_active.is_(True),
                func.jsonb_array_length(Task.expected_result) >= 1,
            )
            .order_by(Task.id)
            .limit(1)
        ).first()
    assert row is not None, "treba aktivan zadatak s očekivanim rezultatom"

    yield {"user_id": uid, "task_id": int(row[0]), "expected_query": str(row[1])}

    with SessionLocal() as s:
        s.execute(delete(SkillMasteryHistory).where(SkillMasteryHistory.user_id == uid))
        s.execute(delete(SkillMastery).where(SkillMastery.user_id == uid))
        s.execute(delete(Misconception).where(Misconception.user_id == uid))
        s.execute(delete(XpLog).where(XpLog.user_id == uid))
        s.execute(delete(Attempt).where(Attempt.user_id == uid))
        s.execute(delete(UserBadge).where(UserBadge.user_id == uid))
        s.execute(delete(User).where(User.id == uid))
        s.commit()


@asynccontextmanager
async def _stack(app, agents):
    await start_gateway_stack(app, agents=agents)
    await asyncio.sleep(0.6)
    try:
        yield
    finally:
        await stop_gateway_stack(app)
        await asyncio.sleep(0.1)


@asynccontextmanager
async def _client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


def _spor_tocan(expected_query: str) -> str:
    """Upit koji vraća TOČAN rezultat, ali sporo.

    `pg_sleep(n)::text` je prazan niz, pa je predikat uvijek istinit i skup redaka se
    ne mijenja; podupit ga izvršava jednom, ne po retku. Provjereno: `evaluate()`
    vraća `is_correct=True`.
    """
    return (
        f"SELECT * FROM ({expected_query.strip().rstrip(';')}) AS sub "
        f"WHERE (SELECT pg_sleep({_SLEEP_S})::text) = '';"
    )


def _stanje(uid: int) -> dict:
    with SessionLocal() as s:
        return {
            "attempts": s.scalar(
                select(func.count()).select_from(Attempt).where(Attempt.user_id == uid)
            ),
            "bkt_snapshotova": s.scalar(
                select(func.count())
                .select_from(SkillMasteryHistory)
                .where(SkillMasteryHistory.user_id == uid)
            ),
            "xp_redaka": s.scalar(
                select(func.count()).select_from(XpLog).where(XpLog.user_id == uid)
            ),
            "xp_ukupno": s.scalar(
                select(func.coalesce(func.sum(XpLog.delta), 0)).where(XpLog.user_id == uid)
            ),
        }


async def _predaj(slow_user, upit: str) -> tuple[httpx.Response, dict]:
    """Jedna predaja kroz PUNI lanac (pravi Evaluator/KM/Gamification)."""
    app = create_app()
    agenti = [
        EvaluatorAgent("evaluator"),
        KnowledgeModelAgent("knowledge"),
        GamificationAgent("gamification"),
        _MockRecommender("recommender"),
        CoordinatorAgent("coordinator", update_timeout=_UPDATE_TIMEOUT),
    ]
    async with _stack(app, agenti), _client(app) as c:
        resp = await c.post(
            "/attempt",
            json={"task_id": slow_user["task_id"], "submitted_query": upit},
            headers=auth_header(slow_user["user_id"]),
        )
        # Pusti nizvodne agente da dovrše — upravo je to bit kvara: oni rade dalje
        # nakon što je Coordinator odustao.
        await asyncio.sleep(_SLEEP_S + 3)
    return resp, _stanje(slow_user["user_id"])


@pytest.mark.parametrize("ponavljanje", [1, 2, 3])
@pytest.mark.asyncio
async def test_incorrect_slow_query_leaves_no_orphan_row(slow_user, ponavljanje) -> None:
    """🔴 Netočan spor upit: ili odgovor, ili nikakav trag — nikad oboje.

    PADA prije popravka: 504 `evaluation_timeout` **i** redak u `attempts` **i** BKT
    snapshot. Student je kažnjen za predaju o kojoj mu sustav tvrdi da nije prošla.
    """
    resp, st = await _predaj(slow_user, f"SELECT pg_sleep({_SLEEP_S});")

    greska = resp.status_code != 200
    assert not (greska and st["attempts"] > 0), (
        f"🔴 NESKLAD: klijent je dobio HTTP {resp.status_code} "
        f"({resp.json().get('detail')}), a u bazi stoji {st['attempts']} pokušaj "
        f"i {st['bkt_snapshotova']} BKT snapshot(a). Student je kažnjen za predaju "
        f"koju mu je sustav odbio."
    )
    # Druga polovica: kad redak postoji, odgovor mora nositi STVARNI ishod, ne samo
    # „nije greška". Inače bi test prolazio i da vraćamo prazan 200.
    if st["attempts"] > 0:
        fb = resp.json()["feedback"]
        assert fb["is_correct"] is False and fb["error_type"], (
            f"200 bez stvarnog ishoda: {fb}"
        )


@pytest.mark.parametrize("ponavljanje", [1, 2, 3])
@pytest.mark.asyncio
async def test_correct_slow_query_never_awards_xp_behind_an_error(
    slow_user, ponavljanje
) -> None:
    """🔴 TOČAN spor upit — slučaj koji KORAK 0 nije izmjerio, nego izveo iz koda.

    Ako student riješi zadatak ispravno a evaluacija prekorači prozor, po izvodu iz
    koda XP se dodjeljuje (Gamification visi o Evaluatorovom informu, ne o
    Coordinatoru) dok student vidi grešku. Ovaj test to **mjeri**.

    Gore je od netočne varijante: točan pokušaj nosi XP, `solved` status i first-solve
    gate — student koji vidi grešku i preda ponovno dobiva „već riješeno, bez XP-a"
    za zadatak koji misli da nije predao.
    """
    resp, st = await _predaj(slow_user, _spor_tocan(slow_user["expected_query"]))

    greska = resp.status_code != 200
    assert not (greska and st["attempts"] > 0), (
        f"🔴 NESKLAD (točan upit): klijent je dobio HTTP {resp.status_code} "
        f"({resp.json().get('detail')}), a u bazi stoji {st['attempts']} pokušaj, "
        f"{st['bkt_snapshotova']} BKT snapshot(a), {st['xp_redaka']} XP redak/redaka "
        f"u iznosu {st['xp_ukupno']}. Student je nagrađen iza poruke o grešci."
    )
    if st["attempts"] > 0:
        fb = resp.json()["feedback"]
        assert fb["is_correct"] is True, (
            f"točno rješenje mora biti prikazano kao točno, a ne progutano: {fb}"
        )
