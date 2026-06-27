"""E2E + concurrency testovi za RecommenderAgent — 3C.2.

Zahtijeva (kao 3A.3/3B.3):
  - živući Prosody XMPP (port 5222), registrirane agente
  - živuću tutor_main bazu s proseedanim konceptima/taskovima

Pokriva:
  - concurrency: lock + to_thread serijaliziraju dijeljeni sync Prolog VM (DOKAZ,
    ne samo prisutnost) — dva konkurentna recommend-a za različite profile ne
    procure jedan u drugi
  - E2E recommend-next kroz Prosody: inform natrag Coordinatoru s task_id|None
  - robusnost: malformed payload → error inform (ne tišina), agent preživi
  - template routing: kriva ontologija ignorirana

setup() pattern: INPUT atribute NE inicijalizirati u setup() (override unutar
start()); samo OUTPUT.
"""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager

import pytest
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from sqlalchemy import delete, select

from agents.base import TutorAgent
from agents.db_helpers import load_concept_code_map
from agents.messages import Ontology, Performative, body_to_payload, payload_to_body
from agents.recommender_agent import RecommenderAgent
from agents.recommender_logic import recommend
from app.core import config
from app.db.models import Attempt, RecommendationLog, SkillMastery, User
from app.db.session import SessionLocal
from app.prolog.prolog_engine import PrologEngine
from tests.test_recommender_synthetic import M1_CONCEPTS, M2_CONCEPTS

# ALL_30 mastered profil za no_recommendation
from tests.test_recommender_synthetic import ALL_30

# ---------------------------------------------------------------------------
# Helperi za agente
# ---------------------------------------------------------------------------


async def _start(*agents: TutorAgent) -> None:
    for a in agents:
        await a.start(auto_register=False)
    await asyncio.sleep(0.5)


async def _stop(*agents: TutorAgent) -> None:
    for a in agents:
        if a.is_alive():
            await a.stop()


@asynccontextmanager
async def _running(*agents: TutorAgent):
    await _start(*agents)
    try:
        yield
    finally:
        await _stop(*agents)
        await asyncio.sleep(0.1)


# ---------------------------------------------------------------------------
# DB helperi
# ---------------------------------------------------------------------------


def _seed_mastery(user_id: int, profile: dict[str, float]) -> None:
    with SessionLocal() as sess:
        code_map = load_concept_code_map(sess)
        for code, p_l in profile.items():
            cid = code_map[code]
            row = sess.get(SkillMastery, (user_id, cid))
            if row is None:
                sess.add(SkillMastery(user_id=user_id, concept_id=cid, p_l=p_l))
            else:
                row.p_l = p_l
        sess.commit()


def _make_user(username: str, email: str) -> int:
    with SessionLocal() as sess:
        user = User(username=username, email=email, password_hash="dummy_3c2")
        sess.add(user)
        sess.commit()
        return user.id


def _delete_user(user_id: int) -> None:
    with SessionLocal() as sess:
        sess.execute(delete(RecommendationLog).where(RecommendationLog.user_id == user_id))
        sess.execute(delete(Attempt).where(Attempt.user_id == user_id))
        sess.execute(delete(SkillMastery).where(SkillMastery.user_id == user_id))
        sess.execute(delete(User).where(User.id == user_id))
        sess.commit()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def novice_user():
    uid = _make_user("rc_e2e_novice_3c2", "rc_e2e_novice_3c2@test.example")
    yield uid
    _delete_user(uid)


@pytest.fixture
def mastered_user():
    uid = _make_user("rc_e2e_mastered_3c2", "rc_e2e_mastered_3c2@test.example")
    _seed_mastery(uid, {c: 0.9 for c in ALL_30})
    yield uid
    _delete_user(uid)


@pytest.fixture
def two_profile_users():
    """Novice (bez mastery) + advanced (M1+M2 mastered) za concurrency test."""
    novice = _make_user("rc_conc_novice_3c2", "rc_conc_novice_3c2@test.example")
    advanced = _make_user("rc_conc_adv_3c2", "rc_conc_adv_3c2@test.example")
    _seed_mastery(advanced, {c: 0.9 for c in M1_CONCEPTS + M2_CONCEPTS + ["null_handling"]})
    yield {"novice": novice, "advanced": advanced}
    _delete_user(novice)
    _delete_user(advanced)


# ---------------------------------------------------------------------------
# Mock Coordinator (test stub — šalje request, prima inform)
# ---------------------------------------------------------------------------


class _RecommendRequester(TutorAgent):
    """Šalje niz recommend-next zahtjeva i skuplja inform odgovore.

    INPUT: self._requests = [{"body": str, "ontology": str?, "correlation_id": str?,
                              "timeout": float?}]
    OUTPUT: self._received = [{"payload": dict, "correlation_id": str|None}]
    """

    class _Flow(OneShotBehaviour):
        async def run(self) -> None:
            for spec in getattr(self.agent, "_requests", []):
                msg = Message(to=config.AGENT_RECOMMENDER_JID)
                msg.set_metadata("performative", Performative.REQUEST)
                msg.set_metadata(
                    "ontology", spec.get("ontology", Ontology.RECOMMEND_NEXT)
                )
                if spec.get("correlation_id"):
                    msg.set_metadata("correlation_id", spec["correlation_id"])
                msg.body = spec["body"]
                await self.send(msg)

                reply = await self.receive(timeout=spec.get("timeout", 15.0))
                if reply is not None:
                    self.agent._received.append(
                        {
                            "payload": body_to_payload(reply.body),
                            "correlation_id": reply.get_metadata("correlation_id"),
                        }
                    )
            await self.agent.stop()

    async def setup(self) -> None:
        self._received = []  # OUTPUT
        self.add_behaviour(self._Flow())


# ---------------------------------------------------------------------------
# T1 — CONCURRENCY: lock + to_thread serijaliziraju dijeljeni Prolog VM
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_recommends_serialized_and_correct(two_profile_users):
    """Dva konkurentna recommend-a (novice + advanced) se NE ispreplitaju.

    Replicira agentovu kritičnu sekciju (async with lock: await to_thread(recommend)).
    Spy na inject/clear dokazuje serijalizaciju: točno parovi inject→clear bez dva
    inject-a zaredom. Bez locka bi to_thread paralelizam mogao procuriti mastery
    jednog usera u recommend drugog (dijeljeni sync VM).
    """
    novice_id = two_profile_users["novice"]
    adv_id = two_profile_users["advanced"]

    engine = PrologEngine()
    lock = asyncio.Lock()
    events: list[tuple[str, str]] = []

    orig_inject = engine.inject_mastery
    orig_clear = engine.clear_mastery

    def spy_inject(u, snap):
        events.append(("inject", u))
        return orig_inject(u, snap)

    def spy_clear(u):
        events.append(("clear", u))
        return orig_clear(u)

    engine.inject_mastery = spy_inject
    engine.clear_mastery = spy_clear

    async def critical(uid: int) -> dict:
        with SessionLocal() as session:
            async with lock:
                return await asyncio.to_thread(recommend, session, engine, uid)

    try:
        res_nov, res_adv = await asyncio.gather(
            critical(novice_id), critical(adv_id)
        )
    finally:
        engine.inject_mastery = orig_inject
        engine.clear_mastery = orig_clear
        engine.clear_mastery(str(novice_id))
        engine.clear_mastery(str(adv_id))

    # Korektnost: svaki user dobio preporuku za SVOJ profil (nema cross-leaka)
    assert res_nov["concept"] == "select_basic", (
        f"Novice cross-contaminiran: {res_nov['concept']}"
    )
    assert res_adv["concept"] == "inner_join", (
        f"Advanced cross-contaminiran: {res_adv['concept']}"
    )

    # Serijalizacija: svi eventi jednog usera su KONTIGUIRANI (blokovi [A..A, B..B]),
    # nema A,B,A ispreplitanja. (inject_mastery interno auto-clear-a pa je >1 clear po
    # recommend-u očekivano; bitan je broj prijelaza između usera.)
    uids_in_order = [u for _, u in events]
    transitions = sum(
        1 for i in range(1, len(uids_in_order)) if uids_in_order[i] != uids_in_order[i - 1]
    )
    assert transitions == 1, (
        f"Ispreplitanje Prolog VM-a detektirano (očekivan točno 1 prijelaz user→user, "
        f"bez locka bi bilo >1): {events}"
    )
    assert events[0][0] == "inject", f"Prvi event mora biti inject: {events}"
    assert uids_in_order[0] != uids_in_order[-1], "Dva različita usera moraju biti prisutna"


# ---------------------------------------------------------------------------
# T2 — E2E happy path: novice → select_basic task vraćen Coordinatoru
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_recommend_returns_task(novice_user):
    """recommend-next za novaka → inform s task_id (int), concept, reason + correlation_id."""
    corr = str(uuid.uuid4())
    requester = _RecommendRequester("coordinator")
    requester._requests = [
        {"body": payload_to_body({"user_id": novice_user}), "correlation_id": corr}
    ]
    recommender = RecommenderAgent("recommender")

    async with _running(recommender, requester):
        await asyncio.sleep(6.0)  # request + Prolog + reply round-trip

    assert len(requester._received) == 1, "Coordinator mora dobiti točno jedan inform"
    rec = requester._received[0]
    assert rec["correlation_id"] == corr, "correlation_id mora biti propagiran"
    payload = rec["payload"]
    assert payload["user_id"] == novice_user
    assert isinstance(payload["task_id"], int), "Novak mora dobiti konkretan task_id"
    assert payload["concept"] == "select_basic"
    assert payload["reason"] == "partial_continuation"


# ---------------------------------------------------------------------------
# T3 — E2E no_recommendation: sve mastered → task_id=None, Coordinator NE visi
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_no_recommendation_returns_none(mastered_user):
    """Sve mastered → inform s task_id=None, concept=None, reason=no_recommendation."""
    requester = _RecommendRequester("coordinator")
    requester._requests = [{"body": payload_to_body({"user_id": mastered_user})}]
    recommender = RecommenderAgent("recommender")

    async with _running(recommender, requester):
        await asyncio.sleep(6.0)

    assert len(requester._received) == 1, "Coordinator mora dobiti odgovor (ne tišinu)"
    payload = requester._received[0]["payload"]
    assert payload["task_id"] is None
    assert payload["concept"] is None
    assert payload["reason"] == "no_recommendation"


# ---------------------------------------------------------------------------
# T4 — Robusnost: malformed payload → error inform, agent preživi sljedeći zahtjev
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_malformed_sends_error_then_recovers(novice_user):
    """Malformed (fali user_id) → reason=error inform; sljedeći valjan zahtjev OK."""
    requester = _RecommendRequester("coordinator")
    requester._requests = [
        {"body": '{"foo": "bar"}'},  # fali user_id → KeyError
        {"body": payload_to_body({"user_id": novice_user})},  # valjan
    ]
    recommender = RecommenderAgent("recommender")

    async with _running(recommender, requester):
        await asyncio.sleep(8.0)

    assert len(requester._received) == 2, (
        f"Oba zahtjeva moraju dobiti odgovor (agent preživio), dobiveno {len(requester._received)}"
    )
    error_reply = requester._received[0]["payload"]
    assert error_reply["reason"] == "error", "Malformed mora vratiti reason=error (ne tišinu)"
    assert error_reply["task_id"] is None

    valid_reply = requester._received[1]["payload"]
    assert valid_reply["concept"] == "select_basic", "Sljedeći valjan zahtjev mora biti obrađen"
    assert isinstance(valid_reply["task_id"], int)


# ---------------------------------------------------------------------------
# T5 — Template routing: kriva ontologija ignorirana (nema odgovora)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_wrong_ontology_ignored(novice_user):
    """Request s ontology≠recommend-next ne pokreće RecommendBehaviour → nema informa."""
    requester = _RecommendRequester("coordinator")
    requester._requests = [
        {
            "body": payload_to_body({"user_id": novice_user}),
            "ontology": Ontology.ATTEMPT_RESULT,  # KRIVA ontologija
            "timeout": 4.0,
        }
    ]
    recommender = RecommenderAgent("recommender")

    async with _running(recommender, requester):
        await asyncio.sleep(5.5)  # > requester timeout

    assert len(requester._received) == 0, (
        "RecommendBehaviour ne smije odgovoriti na krivu ontologiju — Template routing broken"
    )
