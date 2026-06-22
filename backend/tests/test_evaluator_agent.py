"""E2E testovi za EvaluatorAgent — 3A.3.

Integracijski testovi koji zahtijevaju:
  - živući Prosody XMPP (port 5222)
  - živuću tutor_main PostgreSQL bazu
  - živuću sandbox PostgreSQL bazu (port 5433)
  - registrirane agente u Prosody (scripts/register_agents.py)

Testira puni E2E flow: Coordinator → EvaluatorAgent → Prosody → Knowledge/Gamification.
D6 garancija: attempt u DB mora biti COMMITTED prije nego inform stigne receiveru.

VAŽNO — setup() pattern: INPUT atribute (koje test postavlja PRZED start()) NE
inicijalizirati u setup() jer setup() se poziva unutar start() i override-a vrijednost.
Samo OUTPUT atribute (koje pokreće behaviour, čita test) inicijalizirati u setup().

Cleanup: eval_test_env fixture briše sve attempts + entitete u teardown-u.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import pytest
import spade
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template
from sqlalchemy import delete, func, select

from agents.base import TutorAgent
from agents.evaluator import EvaluatorAgent
from agents.messages import Ontology, Performative, body_to_payload
from app.core import config
from app.db.models import Attempt, Module, Task, User
from app.db.session import SessionLocal


# ---------------------------------------------------------------------------
# Konstante i fixture za test entitete
# ---------------------------------------------------------------------------

_EVAL_USERNAME = "eval_test_user_3a3"
_EVAL_EMAIL = "eval_3a3@test.example"
_EVAL_MODULE_NUMBER = 9802

# Upit koji uvijek vraća [{"n": 1}] — funkcionira bez ikakvog schema sadrzaja
_CORRECT_QUERY = "SELECT 1 AS n"
_EXPECTED_RESULT = [{"n": 1}]


@pytest.fixture
def eval_test_env():
    """Kreira test user, module i task za evaluator E2E testove.

    Task koristi SELECT 1 AS n koji radi na svakom sandbox schemi bez tablicnih
    podataka. Teardown briše sve attempts, user, task i module.
    """
    user_id = task_id = module_id = None

    with SessionLocal() as sess:
        mod = Module(
            number=_EVAL_MODULE_NUMBER,
            name="Test modul eval 3a3",
            difficulty="beginner",
            order_index=_EVAL_MODULE_NUMBER,
        )
        sess.add(mod)
        sess.flush()

        task = Task(
            module_id=mod.id,
            title="Test task eval 3a3",
            description="EvaluatorAgent E2E test task",
            sandbox_schema="ecommerce_v1",
            expected_query=_CORRECT_QUERY,
            expected_result=_EXPECTED_RESULT,
            difficulty=1,
        )
        sess.add(task)
        sess.flush()

        user = User(
            username=_EVAL_USERNAME,
            email=_EVAL_EMAIL,
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
# Testni agenti (minimalni stubs)
#
# Pravilo: INPUT atribute (_payload, _target_jid…) NE inicijalizirati u setup()
# jer se setup() poziva unutar start() — override-a vrijednost postavljenu prije
# poziva start(). Samo OUTPUT atribute (_received, _reply…) inicijalizirati.
# ---------------------------------------------------------------------------


class _EvalRequester(TutorAgent):
    """Šalje jedan evaluate-query request i odmah staje (OneShotBehaviour)."""

    class _Send(OneShotBehaviour):
        async def run(self) -> None:
            payload = getattr(self.agent, "_payload", {})
            msg = self.agent.build_message(
                to=config.AGENT_EVALUATOR_JID,
                performative=Performative.REQUEST,
                ontology=Ontology.EVALUATE_QUERY,
                payload=payload,
            )
            await self.send(msg)
            await asyncio.sleep(0.1)
            await self.agent.stop()

    async def setup(self) -> None:
        # _payload je INPUT — postavlja se PRIJE start(), ne ovdje
        self.add_behaviour(self._Send())


class _EvalRequesterWithReply(TutorAgent):
    """Šalje evaluate-query request i čeka inform reply (za task_not_found test)."""

    class _SendReceive(OneShotBehaviour):
        async def run(self) -> None:
            payload = getattr(self.agent, "_payload", {})
            msg = self.agent.build_message(
                to=config.AGENT_EVALUATOR_JID,
                performative=Performative.REQUEST,
                ontology=Ontology.EVALUATE_QUERY,
                payload=payload,
            )
            await self.send(msg)
            reply = await self.receive(timeout=10)
            self.agent._reply = body_to_payload(reply.body) if reply else None
            await self.agent.stop()

    async def setup(self) -> None:
        # _payload INPUT — ne inicijalizirati ovdje
        self._reply: dict | None = None  # OUTPUT
        self.add_behaviour(self._SendReceive())


class _AttemptResultReceiver(TutorAgent):
    """Čeka attempt-result informs i bilježi ih (CyclicBehaviour s Templateom)."""

    class _RecvBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=5)
            if msg is not None:
                self.agent._received.append(body_to_payload(msg.body))

    async def setup(self) -> None:
        self._received: list[dict] = []  # OUTPUT
        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.ATTEMPT_RESULT)
        self.add_behaviour(self._RecvBehaviour(), tmpl)


# ---------------------------------------------------------------------------
# Helperi
# ---------------------------------------------------------------------------


async def _start(*agents: TutorAgent) -> None:
    """Pokreni agente i daj Prosodyu kratko da procesira presence."""
    for a in agents:
        await a.start(auto_register=False)
    await asyncio.sleep(0.5)


async def _stop(*agents: TutorAgent) -> None:
    for a in agents:
        if a.is_alive():
            await a.stop()


@asynccontextmanager
async def _running(*agents: TutorAgent):
    """Context manager: start agents, yield, always stop them."""
    await _start(*agents)
    try:
        yield
    finally:
        await _stop(*agents)
        await asyncio.sleep(0.1)


async def _poll(condition_fn, *, timeout: float = 12.0, interval: float = 0.2) -> None:
    """Pollingom čeka condition_fn() == True; baca TimeoutError ako ne uspije."""
    end = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < end:
        if condition_fn():
            return
        await asyncio.sleep(interval)
    raise TimeoutError(f"Uvjet nije zadovoljen u roku od {timeout}s")


def _count_attempts_in_db(user_id: int) -> int:
    with SessionLocal() as sess:
        return sess.scalar(
            select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id)
        ) or 0


def _get_attempt_in_db(user_id: int, task_id: int) -> Attempt | None:
    with SessionLocal() as sess:
        row = sess.execute(
            select(Attempt)
            .where(Attempt.user_id == user_id, Attempt.task_id == task_id)
            .limit(1)
        ).scalar_one_or_none()
        if row is None:
            return None
        sess.expunge(row)
        return row


# ---------------------------------------------------------------------------
# Testovi
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_correct_submit(eval_test_env):
    """E2E: tocan submit → attempt commitan s is_correct=True, inform primljen."""
    user_id = eval_test_env["user_id"]
    task_id = eval_test_env["task_id"]

    requester = _EvalRequester("coordinator")
    requester._payload = {
        "user_id": user_id,
        "task_id": task_id,
        "submitted_query": _CORRECT_QUERY,
    }
    knowledge_recv = _AttemptResultReceiver("knowledge")
    gamif_recv = _AttemptResultReceiver("gamification")
    evaluator = EvaluatorAgent("evaluator")

    async with _running(evaluator, knowledge_recv, gamif_recv, requester):
        await spade.wait_until_finished([requester])

        # Cekaj da knowledge receiver dobije inform
        await _poll(lambda: len(knowledge_recv._received) >= 1)

    # --- Provjera DB (D6): attempt mora biti committed ---
    attempt = _get_attempt_in_db(user_id, task_id)
    assert attempt is not None, "Attempt nije committan u DB"
    assert attempt.is_correct is True, f"Ocekivano is_correct=True, dobiveno {attempt.is_correct}"
    assert attempt.error_type is None
    assert attempt.attempt_number == 1

    # --- Provjera inform payload-a ---
    assert len(knowledge_recv._received) >= 1
    inform = knowledge_recv._received[0]
    assert inform["attempt_id"] == attempt.id
    assert inform["user_id"] == user_id
    assert inform["task_id"] == task_id
    assert inform["is_correct"] is True
    assert inform["verdict"] == "correct"
    assert inform["error_type"] is None

    # Gamification takoder treba dobiti inform
    assert len(gamif_recv._received) >= 1


@pytest.mark.asyncio
async def test_incorrect_submit(eval_test_env):
    """E2E: krivi submit → attempt is_correct=False, inform verdict != correct."""
    user_id = eval_test_env["user_id"]
    task_id = eval_test_env["task_id"]

    requester = _EvalRequester("coordinator")
    requester._payload = {
        "user_id": user_id,
        "task_id": task_id,
        "submitted_query": "SELECT 999 AS n",  # krivi rezultat
    }
    knowledge_recv = _AttemptResultReceiver("knowledge")
    gamif_recv = _AttemptResultReceiver("gamification")
    evaluator = EvaluatorAgent("evaluator")

    async with _running(evaluator, knowledge_recv, gamif_recv, requester):
        await spade.wait_until_finished([requester])
        await _poll(lambda: len(knowledge_recv._received) >= 1)

    attempt = _get_attempt_in_db(user_id, task_id)
    assert attempt is not None
    assert attempt.is_correct is False

    inform = knowledge_recv._received[0]
    assert inform["is_correct"] is False
    assert inform["verdict"] != "correct"


@pytest.mark.asyncio
async def test_task_not_found(eval_test_env):
    """task_not_found: nepostojeci task_id → error inform Coordinatoru, bez Attempt retka."""
    user_id = eval_test_env["user_id"]
    fake_task_id = 999_999

    requester = _EvalRequesterWithReply("coordinator")
    requester._payload = {
        "user_id": user_id,
        "task_id": fake_task_id,
        "submitted_query": "SELECT 1",
    }
    evaluator = EvaluatorAgent("evaluator")

    async with _running(evaluator, requester):
        await spade.wait_until_finished([requester])

    # Nema attempt retka u DB
    assert _count_attempts_in_db(user_id) == 0

    # Requester je dobio error inform
    reply = requester._reply
    assert reply is not None, "Coordinator nije dobio error inform"
    assert reply["error_type"] == "task_not_found"
    assert reply["is_correct"] is False
    assert reply["verdict"] == "incorrect"


@pytest.mark.asyncio
async def test_robustness_malformed_json(eval_test_env):
    """CyclicBehaviour prezivljava malformed JSON — agent nastavlja petlju.

    Test: pošalji krivi JSON, pa validan request; assert da je validan obradjen.
    """
    user_id = eval_test_env["user_id"]
    task_id = eval_test_env["task_id"]

    class _MalformedThenValidRequester(TutorAgent):
        class _Behaviour(OneShotBehaviour):
            async def run(self) -> None:
                # 1. Malformed poruka (parsiranje ce baciti JSONDecodeError)
                bad = Message(to=config.AGENT_EVALUATOR_JID)
                bad.set_metadata("performative", Performative.REQUEST)
                bad.set_metadata("ontology", Ontology.EVALUATE_QUERY)
                bad.body = "ovo nije validan JSON {"
                await self.send(bad)

                # Kratka pauza da evaluator obradi loseg kandidata
                await asyncio.sleep(1.0)

                # 2. Validan request
                good = self.agent.build_message(
                    to=config.AGENT_EVALUATOR_JID,
                    performative=Performative.REQUEST,
                    ontology=Ontology.EVALUATE_QUERY,
                    payload=getattr(self.agent, "_valid_payload", {}),
                )
                await self.send(good)
                await asyncio.sleep(0.1)
                await self.agent.stop()

        async def setup(self) -> None:
            # _valid_payload je INPUT — ne inicijalizirati ovdje
            self.add_behaviour(self._Behaviour())

    knowledge_recv = _AttemptResultReceiver("knowledge")
    requester = _MalformedThenValidRequester("coordinator")
    requester._valid_payload = {
        "user_id": user_id,
        "task_id": task_id,
        "submitted_query": _CORRECT_QUERY,
    }
    evaluator = EvaluatorAgent("evaluator")

    async with _running(evaluator, knowledge_recv, requester):
        await spade.wait_until_finished([requester])
        # Cekaj da validan request bude obradjen
        await _poll(lambda: len(knowledge_recv._received) >= 1, timeout=15.0)

    # Agent je prezivio malformed JSON i obradio validan request
    attempt = _get_attempt_in_db(user_id, task_id)
    assert attempt is not None, "Validan request nije obradjen — agent mozda ugasio cyclic"
    assert attempt.is_correct is True


@pytest.mark.asyncio
async def test_template_routing_wrong_ontology_ignored(eval_test_env):
    """Poruka s krivom ontologijom ne pokrece EvaluateBehaviour — nema Attempt retka."""
    user_id = eval_test_env["user_id"]
    task_id = eval_test_env["task_id"]

    class _WrongOntologySender(TutorAgent):
        class _Send(OneShotBehaviour):
            async def run(self) -> None:
                payload = getattr(self.agent, "_payload", {})
                msg = self.agent.build_message(
                    to=config.AGENT_EVALUATOR_JID,
                    performative=Performative.REQUEST,
                    ontology=Ontology.RECOMMEND_NEXT,  # KRIVA ontologija
                    payload=payload,
                )
                await self.send(msg)
                await asyncio.sleep(0.1)
                await self.agent.stop()

        async def setup(self) -> None:
            # _payload INPUT — ne inicijalizirati ovdje
            self.add_behaviour(self._Send())

    sender = _WrongOntologySender("coordinator")
    sender._payload = {
        "user_id": user_id,
        "task_id": task_id,
        "submitted_query": _CORRECT_QUERY,
    }
    evaluator = EvaluatorAgent("evaluator")

    async with _running(evaluator, sender):
        await spade.wait_until_finished([sender])
        await asyncio.sleep(2.0)  # daj evaluatoru dovoljno da bi obradio (ako bi)

    # Nema attempt retka — EvaluateBehaviour nije pokrenut
    assert _count_attempts_in_db(user_id) == 0, (
        "EvaluateBehaviour je obradio poruku s krivom ontologijom — Template routing broken"
    )
