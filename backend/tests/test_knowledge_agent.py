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
import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template
from sqlalchemy import delete, select

from agents.base import TutorAgent
from agents.knowledge_agent import KnowledgeModelAgent
from agents.messages import Ontology, Performative, body_to_payload
from app.core import config
from app.db.models import (
    Attempt,
    Concept,
    Misconception,
    SkillMastery,
    SkillMasteryHistory,
    Task,
    User,
)
from app.db.session import SessionLocal


# ---------------------------------------------------------------------------
# Konstante
# ---------------------------------------------------------------------------

_KM_E2E_USERNAME = "km_e2e_user_3b3"
_KM_E2E_EMAIL = "km_e2e_3b3@test.example"
# Attempt_id-evi koje payloadi ovih testova koriste — od 4.0a-3.1 KM hook piše
# skill_mastery_history s FK na attempts.id, pa ovi redovi moraju STVARNO postojati.
_KM_E2E_ATTEMPT_IDS = [99901, 99902, 99903, 99904, 99905, 99906, 99907]


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

        # Realni attempt redovi s eksplicitnim id-evima koje payloadi koriste —
        # potrebno jer skill_mastery_history sada ima FK na attempts.id.
        task_id = sess.scalar(select(Task.id).limit(1))
        assert task_id is not None, "tasks moraju biti seedani"
        for n, aid in enumerate(_KM_E2E_ATTEMPT_IDS, start=1):
            sess.add(
                Attempt(
                    id=aid,
                    user_id=user_id,
                    task_id=task_id,
                    submitted_query="SELECT 1;",
                    is_correct=True,
                    attempt_number=n,
                )
            )
        sess.commit()

    yield {"user_id": user_id}

    with SessionLocal() as cleanup:
        # FK redoslijed: smh (→attempts) → misconception/skill_mastery → attempts → user
        cleanup.execute(
            delete(SkillMasteryHistory).where(SkillMasteryHistory.user_id == user_id)
        )
        cleanup.execute(delete(Misconception).where(Misconception.user_id == user_id))
        cleanup.execute(delete(SkillMastery).where(SkillMastery.user_id == user_id))
        cleanup.execute(delete(Attempt).where(Attempt.user_id == user_id))
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


# ---------------------------------------------------------------------------
# Pomoćnik za misconception testove
# ---------------------------------------------------------------------------


def _get_misconception_occurrences(user_id: int, code: str) -> int:
    with SessionLocal() as sess:
        row = sess.execute(
            select(Misconception).where(
                Misconception.user_id == user_id,
                Misconception.code == code,
            )
        ).scalar_one_or_none()
        if row is None:
            return 0
        return row.occurrences


# ---------------------------------------------------------------------------
# T5 — E2E misconception: occurrences=2 na ponovljenoj grešci
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_misconception_increments_on_repeated_failure(km_test_env):
    """2× attempt-result (is_correct=False, left_join, row_mismatch) → Misconception.occurrences=2.

    Exit kriterij §3B: misconception se inkrementira na ponovljenoj grešci.
    Sync točka: poll DB dok occurrences ne dosegne 2 (timeout 15s).
    """
    user_id = km_test_env["user_id"]
    mc_code = "left_join__row_mismatch"

    _incorrect_payload = {
        "attempt_id": 99905,
        "user_id": user_id,
        "task_id": 5,
        "is_correct": False,
        "error_type": "row_mismatch",
        "verdict": "incorrect",
        "execution_time_ms": 40,
        "concepts": [{"code": "left_join", "is_primary": True}],
        "primary_concept": "left_join",
    }

    class _TwoShotSender(TutorAgent):
        """Šalje isti incorrect inform dvaput s pauzom između."""

        class _Send(OneShotBehaviour):
            async def run(self) -> None:
                payload = getattr(self.agent, "_payload", {})
                for _ in range(2):
                    msg = self.agent.build_message(
                        to=config.AGENT_KNOWLEDGE_JID,
                        performative=Performative.INFORM,
                        ontology=Ontology.ATTEMPT_RESULT,
                        payload=payload,
                    )
                    await self.send(msg)
                    await asyncio.sleep(1.5)  # čekaj da agent obradi prvi prije slanja drugog
                await self.agent.stop()

        async def setup(self) -> None:
            # _payload je INPUT
            self.add_behaviour(self._Send())

    sender = _TwoShotSender("coordinator")
    sender._payload = _incorrect_payload
    knowledge = KnowledgeModelAgent("knowledge")

    async with _running(knowledge, sender):
        await _poll(
            lambda: _get_misconception_occurrences(user_id, mc_code) >= 2,
            timeout=15.0,
        )

    occurrences = _get_misconception_occurrences(user_id, mc_code)
    assert occurrences == 2, (
        f"Ocekivano occurrences=2 za '{mc_code}', dobiveno {occurrences}"
    )


# ---------------------------------------------------------------------------
# Fan-in signal (3E.1) — model-updated prema Coordinatoru
# ---------------------------------------------------------------------------


class _CoordinatorProbe(TutorAgent):
    """Simulira Coordinatora: pošalje attempt-result KM-u i hvata model-updated.

    Prijavljuje se kao 'coordinator' (isti JID na koji KM šalje fan-in signal),
    pa istovremeno šalje ulazni inform i sluša povratni 'model-updated'.
    Primljeni signali se spremaju u self._received (OUTPUT atribut).
    """

    class _Send(OneShotBehaviour):
        async def run(self) -> None:
            payload = getattr(self.agent, "_payload", {})
            correlation_id = getattr(self.agent, "_correlation_id", None)
            msg = self.agent.build_message(
                to=config.AGENT_KNOWLEDGE_JID,
                performative=Performative.INFORM,
                ontology=Ontology.ATTEMPT_RESULT,
                payload=payload,
                correlation_id=correlation_id,
            )
            await self.send(msg)
            # NE zaustavlja agenta — mora ostati živ da uhvati model-updated.

    class _Listen(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return
            self.agent._received.append(
                {
                    "to": str(msg.to),
                    "sender": str(msg.sender),
                    "performative": msg.get_metadata("performative"),
                    "ontology": msg.get_metadata("ontology"),
                    "correlation_id": msg.get_metadata("correlation_id"),
                    "payload": body_to_payload(msg.body),
                }
            )

    async def setup(self) -> None:
        # _payload / _correlation_id su INPUT — ne inicijalizirati ovdje.
        self._received: list[dict] = []  # OUTPUT
        self.add_behaviour(self._Send())
        listen_tmpl = Template()
        listen_tmpl.set_metadata("ontology", Ontology.MODEL_UPDATED)
        self.add_behaviour(self._Listen(), listen_tmpl)


# ---------------------------------------------------------------------------
# T6 — model-updated se šalje na uspješan attempt (updated NEprazan)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_model_updated_sent_on_success_with_correlation(km_test_env):
    """E2E: uspješan attempt → KM šalje model-updated Coordinatoru.

    Asertira to/performative/ontology/payload + da je correlation_id propagiran
    s ulazne poruke na izlazni signal.
    """
    user_id = km_test_env["user_id"]
    correlation_id = str(uuid.uuid4())

    probe = _CoordinatorProbe("coordinator")
    probe._payload = {
        "attempt_id": 99906,
        "user_id": user_id,
        "task_id": 6,
        "is_correct": True,
        "error_type": None,
        "verdict": "correct",
        "execution_time_ms": 33,
        "concepts": [{"code": "agg_count", "is_primary": True}],
        "primary_concept": "agg_count",
    }
    probe._correlation_id = correlation_id
    knowledge = KnowledgeModelAgent("knowledge")

    async with _running(knowledge, probe):
        await _poll(lambda: len(probe._received) >= 1)

    assert len(probe._received) >= 1, "Coordinator nije primio model-updated signal"
    signal = probe._received[0]
    assert signal["ontology"] == Ontology.MODEL_UPDATED
    assert signal["performative"] == Performative.INFORM
    assert "coordinator" in signal["to"], (
        f"model-updated mora ići Coordinatoru, dobiveno to={signal['to']!r}"
    )
    assert signal["correlation_id"] == correlation_id, (
        "correlation_id mora biti propagiran s ulazne poruke na model-updated"
    )
    assert signal["payload"]["user_id"] == user_id
    assert signal["payload"]["attempt_id"] == 99906
    assert "agg_count" in signal["payload"]["updated_concepts"], (
        "updated_concepts mora sadržavati stvarno diran koncept"
    )


# ---------------------------------------------------------------------------
# T7 — 🔴 GUARD: model-updated se šalje i kad nijedan koncept nije diran
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_model_updated_sent_on_mechanical_error_empty_updated(km_test_env):
    """E2E GUARD: mehanička greška bez konceptualnog updatea → updated_concepts == [],
    ali model-updated SVEJEDNO stiže.

    Bez ovog signala Coordinator FSM visi (čeka signal koji nikad ne stigne) →
    HTTP timeout. Simuliramo "nijedan koncept diran" praznom concepts listom
    (KM update vrati {} → updated_concepts == []).
    """
    user_id = km_test_env["user_id"]
    correlation_id = str(uuid.uuid4())

    probe = _CoordinatorProbe("coordinator")
    probe._payload = {
        "attempt_id": 99907,
        "user_id": user_id,
        "task_id": 7,
        "is_correct": False,
        "error_type": "syntax_error",  # mehanička greška
        "verdict": "incorrect",
        "execution_time_ms": 5,
        "concepts": [],  # nijedan koncept → updated == {}
        "primary_concept": None,
    }
    probe._correlation_id = correlation_id
    knowledge = KnowledgeModelAgent("knowledge")

    async with _running(knowledge, probe):
        await _poll(lambda: len(probe._received) >= 1)

    assert len(probe._received) >= 1, (
        "model-updated MORA stići i na mehaničkoj grešci (updated==[]) — "
        "inače Coordinator FSM visi"
    )
    signal = probe._received[0]
    assert signal["ontology"] == Ontology.MODEL_UPDATED
    assert signal["correlation_id"] == correlation_id
    assert signal["payload"]["attempt_id"] == 99907
    assert signal["payload"]["updated_concepts"] == [], (
        "updated_concepts mora biti prazan kad nijedan koncept nije diran"
    )


# ---------------------------------------------------------------------------
# T8 — best-effort: pad self.send-a NE ruši behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_model_updated_send_is_best_effort_on_send_failure():
    """Unit: ako self.send digne iznimku (Coordinator/XMPP nedostupan), _send_model_updated
    je proguta — UpdateBehaviour ne pada (signal je best-effort kao log_message)."""
    knowledge = KnowledgeModelAgent("knowledge")
    behaviour = KnowledgeModelAgent.UpdateBehaviour()
    behaviour.set_agent(knowledge)
    behaviour.send = AsyncMock(side_effect=RuntimeError("XMPP down"))

    # Ne smije podići iznimku unatoč padu send-a.
    await behaviour._send_model_updated(
        user_id=99999,
        attempt_id=99999,
        updated_concepts=[],
        correlation_id=None,
    )

    behaviour.send.assert_awaited_once()
