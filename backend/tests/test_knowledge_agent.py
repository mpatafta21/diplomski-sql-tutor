"""E2E testovi za KnowledgeModelAgent — 3B.3.

Integracijski testovi koji zahtijevaju:
  - živući Prosody XMPP (port 5222)
  - živuću tutor_main PostgreSQL bazu s proseedanim konceptima
  - registrirane agente u Prosody (scripts/register_agents.py)

Testira puni E2E flow: mock-Evaluator → KnowledgeModelAgent → SkillMastery DB.

Sync točka: KnowledgeModelAgent obrađuje poruku async — testovi poll-aju DB
dok SkillMastery red ne osvane (timeout 12s), ne asertiraju odmah nakon senda.

VAŽNO — setup() pattern: INPUT atribute NE inicijalizirati u setup() jer
setup() se poziva unutar start() i override-a vrijednosti. Samo OUTPUT atribute.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import pytest
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template
from sqlalchemy import delete, select

from agents.base import TutorAgent
from agents.knowledge import KnowledgeModelAgent
from agents.messages import Ontology, Performative, body_to_payload
from app.core import config
from app.db.models import Concept, SkillMastery, User
from app.db.session import SessionLocal


# ---------------------------------------------------------------------------
# Konstante
# ---------------------------------------------------------------------------

_KM_E2E_USERNAME = "km_e2e_user_3b3"
_KM_E2E_EMAIL = "km_e2e_3b3@test.example"


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def km_test_env():
    """Kreira committed test usera. Teardown briše SkillMastery + User.

    Koncepti su proseedani (agg_count, group_by, left_join — sve postoje).
    """
    user_id = None

    with SessionLocal() as sess:
        user = User(
            username=_KM_E2E_USERNAME,
            email=_KM_E2E_EMAIL,
            password_hash="dummy_hash_3b3",
        )
        sess.add(user)
        sess.commit()
        user_id = user.id

    yield {"user_id": user_id}

    with SessionLocal() as cleanup:
        cleanup.execute(delete(SkillMastery).where(SkillMastery.user_id == user_id))
        cleanup.execute(delete(User).where(User.id == user_id))
        cleanup.commit()


# ---------------------------------------------------------------------------
# Helperi
# ---------------------------------------------------------------------------


def _get_concept_id(code: str) -> int:
    with SessionLocal() as sess:
        cid = sess.scalar(select(Concept.id).where(Concept.code == code))
    assert cid is not None, f"Koncept {code!r} nije seedan"
    return cid


def _get_skill_mastery(user_id: int, concept_id: int) -> SkillMastery | None:
    with SessionLocal() as sess:
        row = sess.get(SkillMastery, (user_id, concept_id))
        if row is None:
            return None
        sess.expunge(row)
        return row


async def _poll(condition_fn, *, timeout: float = 12.0, interval: float = 0.25) -> None:
    """Poll-a condition_fn() dok ne vrati True; baca TimeoutError ako prođe timeout."""
    end = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < end:
        if condition_fn():
            return
        await asyncio.sleep(interval)
    raise TimeoutError(f"Uvjet nije zadovoljen u {timeout}s")


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
# Testni agenti
# ---------------------------------------------------------------------------


class _AttemptResultSender(TutorAgent):
    """Šalje jedan attempt-result inform KnowledgeModelAgentu i staje."""

    class _Send(OneShotBehaviour):
        async def run(self) -> None:
            payload = getattr(self.agent, "_payload", {})
            msg = self.agent.build_message(
                to=config.AGENT_KNOWLEDGE_JID,
                performative=Performative.INFORM,
                ontology=Ontology.ATTEMPT_RESULT,
                payload=payload,
            )
            await self.send(msg)
            await asyncio.sleep(0.1)
            await self.agent.stop()

    async def setup(self) -> None:
        # _payload je INPUT — ne inicijalizirati ovdje
        self.add_behaviour(self._Send())


class _RawMessageSender(TutorAgent):
    """Šalje raw Message (bez JSON serializacije) za malformed testove."""

    class _Send(OneShotBehaviour):
        async def run(self) -> None:
            raw_body = getattr(self.agent, "_raw_body", "{}")
            ontology = getattr(self.agent, "_ontology", Ontology.ATTEMPT_RESULT)

            msg = Message(to=config.AGENT_KNOWLEDGE_JID)
            msg.set_metadata("performative", Performative.INFORM)
            msg.set_metadata("ontology", ontology)
            msg.body = raw_body
            await self.send(msg)
            await asyncio.sleep(0.1)
            await self.agent.stop()

    async def setup(self) -> None:
        # INPUT atributi — ne inicijalizirati ovdje
        self.add_behaviour(self._Send())


# ---------------------------------------------------------------------------
# T1 — E2E happy path: jedan koncept
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_single_concept_creates_skill_mastery(km_test_env):
    """E2E: attempt-result inform (agg_count, correct) → SkillMastery red nastane u DB.

    Sync točka: poll-amo DB do 12s dok SkillMastery red za (user, agg_count) ne osvane.
    """
    user_id = km_test_env["user_id"]
    agg_id = _get_concept_id("agg_count")

    sender = _AttemptResultSender("coordinator")
    sender._payload = {
        "attempt_id": 99901,
        "user_id": user_id,
        "task_id": 1,
        "is_correct": True,
        "error_type": None,
        "verdict": "correct",
        "execution_time_ms": 42,
        "concepts": [{"code": "agg_count", "is_primary": True}],
        "primary_concept": "agg_count",
    }
    knowledge = KnowledgeModelAgent("knowledge")

    async with _running(knowledge, sender):
        await _poll(lambda: _get_skill_mastery(user_id, agg_id) is not None)

    row = _get_skill_mastery(user_id, agg_id)
    assert row is not None, "SkillMastery red mora postojati nakon E2E obrade"
    # medium tier: p_l0=0.15, after 1x correct ≈ 0.5541
    assert row.p_l == pytest.approx(0.55409836, rel=1e-3), (
        f"p_l={row.p_l:.6f} ne odgovara BKT medium tier (ocekivano ~0.5541)"
    )
    assert row.p_t == pytest.approx(0.20)
    assert row.attempts_count == 1
    assert row.correct_count == 1


# ---------------------------------------------------------------------------
# T2 — Multi-concept: oba koncepta dobivaju SkillMastery
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_multi_concept_creates_both_rows(km_test_env):
    """E2E: task s dva koncepta (agg_count + group_by) → oba SkillMastery reda nastanu."""
    user_id = km_test_env["user_id"]
    agg_id = _get_concept_id("agg_count")
    grp_id = _get_concept_id("group_by")

    sender = _AttemptResultSender("coordinator")
    sender._payload = {
        "attempt_id": 99902,
        "user_id": user_id,
        "task_id": 2,
        "is_correct": True,
        "error_type": None,
        "verdict": "correct",
        "execution_time_ms": 55,
        "concepts": [
            {"code": "agg_count", "is_primary": True},
            {"code": "group_by", "is_primary": False},
        ],
        "primary_concept": "agg_count",
    }
    knowledge = KnowledgeModelAgent("knowledge")

    async with _running(knowledge, sender):
        await _poll(
            lambda: (
                _get_skill_mastery(user_id, agg_id) is not None
                and _get_skill_mastery(user_id, grp_id) is not None
            )
        )

    agg_row = _get_skill_mastery(user_id, agg_id)
    grp_row = _get_skill_mastery(user_id, grp_id)
    assert agg_row is not None, "SkillMastery za agg_count mora postojati"
    assert grp_row is not None, "SkillMastery za group_by mora postojati"
    assert agg_row.attempts_count == 1
    assert grp_row.attempts_count == 1


# ---------------------------------------------------------------------------
# T3 — Robustnost: malformed payload ne ubija agenta
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_robustness_malformed_payload_agent_continues(km_test_env):
    """Malformed payload (KeyError) → agent logira, ne pukne; sljedeći valjan inform obrađen."""
    user_id = km_test_env["user_id"]
    agg_id = _get_concept_id("agg_count")

    class _MalformedThenValid(TutorAgent):
        class _Behaviour(OneShotBehaviour):
            async def run(self) -> None:
                # 1. Validan JSON ali nedostaje ključ "concepts" → KeyError u run()
                bad = Message(to=config.AGENT_KNOWLEDGE_JID)
                bad.set_metadata("performative", Performative.INFORM)
                bad.set_metadata("ontology", Ontology.ATTEMPT_RESULT)
                bad.body = '{"user_id": 99999, "is_correct": true}'  # fali "concepts"
                await self.send(bad)

                await asyncio.sleep(1.0)

                # 2. Validan inform
                good = self.agent.build_message(
                    to=config.AGENT_KNOWLEDGE_JID,
                    performative=Performative.INFORM,
                    ontology=Ontology.ATTEMPT_RESULT,
                    payload=getattr(self.agent, "_valid_payload", {}),
                )
                await self.send(good)
                await asyncio.sleep(0.1)
                await self.agent.stop()

        async def setup(self) -> None:
            # _valid_payload je INPUT
            self.add_behaviour(self._Behaviour())

    sender = _MalformedThenValid("coordinator")
    sender._valid_payload = {
        "attempt_id": 99903,
        "user_id": user_id,
        "task_id": 3,
        "is_correct": True,
        "error_type": None,
        "verdict": "correct",
        "execution_time_ms": 30,
        "concepts": [{"code": "agg_count", "is_primary": True}],
        "primary_concept": "agg_count",
    }
    knowledge = KnowledgeModelAgent("knowledge")

    async with _running(knowledge, sender):
        await _poll(
            lambda: _get_skill_mastery(user_id, agg_id) is not None,
            timeout=15.0,
        )

    row = _get_skill_mastery(user_id, agg_id)
    assert row is not None, (
        "Validan inform nije obrađen — agent možda srušio CyclicBehaviour na KeyError"
    )


# ---------------------------------------------------------------------------
# T4 — Template routing: kriva ontologija ne pokretata UpdateBehaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_template_routing_wrong_ontology_ignored(km_test_env):
    """Inform s ontology≠attempt-result ne pokretata UpdateBehaviour → nema SkillMastery."""
    user_id = km_test_env["user_id"]
    agg_id = _get_concept_id("agg_count")

    sender = _RawMessageSender("coordinator")
    sender._raw_body = str({
        "attempt_id": 99904,
        "user_id": user_id,
        "task_id": 4,
        "is_correct": True,
        "concepts": [{"code": "agg_count", "is_primary": True}],
    })
    sender._ontology = Ontology.RECOMMEND_NEXT  # KRIVA ontologija

    knowledge = KnowledgeModelAgent("knowledge")

    async with _running(knowledge, sender):
        await asyncio.sleep(2.5)  # daj agentu vremena da obradi (ako bi)

    row = _get_skill_mastery(user_id, agg_id)
    assert row is None, (
        "UpdateBehaviour ne smije obraditi poruku s krivom ontologijom — Template routing broken"
    )
