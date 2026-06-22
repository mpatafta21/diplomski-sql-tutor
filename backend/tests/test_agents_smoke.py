"""3A.0 de-risk: XMPP round-trip kroz Prosody + Template routing + agent_messages_log.

Ovi testovi su integracijski (trebaju živući Prosody na 5222).
Pokreću se s: uv run pytest tests/test_agents_smoke.py -v
"""

from __future__ import annotations

import asyncio

import pytest
import spade
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template

from agents.base import TutorAgent
from agents.messages import (
    Ontology,
    Performative,
    body_to_payload,
    payload_to_body,
)
from app.db.models import AgentMessageLog


# ---------------------------------------------------------------------------
# Minimalni testni agenti
# ---------------------------------------------------------------------------


class _EchoEvaluator(TutorAgent):
    """Evaluator koji prima evaluate-query request i odgovara inform echom."""

    class _EchoBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            payload = body_to_payload(msg.body)
            self.agent._received_payload = payload

            self.agent.log_message(
                sender=str(self.agent.jid),
                receiver=str(msg.sender),
                performative=Performative.INFORM,
                content=payload,
            )

            reply = self.agent.build_message(
                to=str(msg.sender),
                performative=Performative.INFORM,
                ontology=Ontology.EVALUATE_QUERY,
                payload={"echo": payload},
            )
            await self.send(reply)
            await self.agent.stop()

    async def setup(self) -> None:
        self._received_payload: dict | None = None
        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.EVALUATE_QUERY)
        self.add_behaviour(self._EchoBehaviour(), tmpl)


class _CoordinatorSender(TutorAgent):
    """Coordinator koji pošalje request i sačeka inform odgovor."""

    class _SendReceiveBehaviour(OneShotBehaviour):
        async def run(self) -> None:
            msg = self.agent.build_message(
                to=self.agent._target_jid,
                performative=Performative.REQUEST,
                ontology=Ontology.EVALUATE_QUERY,
                payload={"task_id": 42, "query": "SELECT 1"},
            )
            await self.send(msg)

            reply = await self.receive(timeout=10)
            self.agent._reply_payload = body_to_payload(reply.body) if reply else None
            await self.agent.stop()

    async def setup(self) -> None:
        self._reply_payload: dict | None = None
        self.add_behaviour(self._SendReceiveBehaviour())


class _IgnoreWrongOntologyEvaluator(TutorAgent):
    """Evaluator koji IGNORIRA poruke s krivom ontologijom — dokazuje Template routing."""

    class _TargetBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=3)
            if msg:
                self.agent._correct_received += 1
            # Bez receive-all loop-a — Template filtrira; krivi msg nikad ne stiže

    class _WrongOntologyBehaviour(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=3)
            if msg:
                self.agent._wrong_received += 1

    async def setup(self) -> None:
        self._correct_received = 0
        self._wrong_received = 0

        good_tmpl = Template()
        good_tmpl.set_metadata("ontology", Ontology.EVALUATE_QUERY)
        self.add_behaviour(self._TargetBehaviour(), good_tmpl)

        wrong_tmpl = Template()
        wrong_tmpl.set_metadata("ontology", Ontology.RECOMMEND_NEXT)
        self.add_behaviour(self._WrongOntologyBehaviour(), wrong_tmpl)


# ---------------------------------------------------------------------------
# Helperi
# ---------------------------------------------------------------------------


async def _start_agents(*agents: TutorAgent) -> None:
    for a in agents:
        await a.start(auto_register=False)
    await asyncio.sleep(0.5)  # daj Prosody malo da procesira presence


async def _stop_agents(*agents: TutorAgent) -> None:
    for a in agents:
        if a.is_alive():
            await a.stop()


# ---------------------------------------------------------------------------
# Testovi
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_xmpp_round_trip_json_payload(db_session):
    """JSON payload se prenosi netaknuto od Coordinatora do Evaluatora i natrag."""
    evaluator = _EchoEvaluator("evaluator")
    coordinator = _CoordinatorSender("coordinator")
    coordinator._target_jid = str(evaluator.jid)

    await _start_agents(evaluator, coordinator)
    await spade.wait_until_finished([evaluator, coordinator])

    assert evaluator._received_payload == {"task_id": 42, "query": "SELECT 1"}
    assert coordinator._reply_payload == {"echo": {"task_id": 42, "query": "SELECT 1"}}


@pytest.mark.asyncio
async def test_template_routing_wrong_ontology_ignored():
    """Poruka s krivom ontologijom ne triggera evaluate-query behaviour."""

    class _Sender(TutorAgent):
        class _Send(OneShotBehaviour):
            async def run(self) -> None:
                # Šalje dvije poruke: jednu točnu i jednu s krivom ontologijom
                good = self.agent.build_message(
                    to=self.agent._target_jid,
                    performative=Performative.REQUEST,
                    ontology=Ontology.EVALUATE_QUERY,
                    payload={"type": "correct"},
                )
                wrong = self.agent.build_message(
                    to=self.agent._target_jid,
                    performative=Performative.REQUEST,
                    ontology=Ontology.RECOMMEND_NEXT,
                    payload={"type": "wrong"},
                )
                await self.send(good)
                await self.send(wrong)
                await self.agent.stop()

        async def setup(self) -> None:
            self.add_behaviour(self._Send())

    receiver = _IgnoreWrongOntologyEvaluator("evaluator")
    sender = _Sender("coordinator")
    sender._target_jid = str(receiver.jid)

    await _start_agents(receiver, sender)
    await spade.wait_until_finished([sender])
    await asyncio.sleep(2)  # daj receiveru da procesira obje poruke
    await _stop_agents(receiver)

    # Točna ontology stigla u pravi behaviour, krivi u wrong behaviour
    assert receiver._correct_received == 1, (
        f"Očekivano 1 correct, primljeno {receiver._correct_received}"
    )
    assert receiver._wrong_received == 1, (
        f"Očekivano 1 wrong, primljeno {receiver._wrong_received}"
    )


@pytest.mark.asyncio
async def test_agent_messages_log_written(db_session):
    """log_message() upisuje red u agent_messages_log (provjera kroz db_session)."""
    from agents.base import TutorAgent as _TB

    class _LoggingEvaluator(_EchoEvaluator):
        pass  # koristi isti EchoBehaviour koji poziva log_message

    class _LoggingCoordinator(_CoordinatorSender):
        pass

    evaluator = _LoggingEvaluator("evaluator")
    coordinator = _LoggingCoordinator("coordinator")
    coordinator._target_jid = str(evaluator.jid)

    # Broji logove PRIJE
    before = db_session.query(AgentMessageLog).count()

    await _start_agents(evaluator, coordinator)
    await spade.wait_until_finished([evaluator, coordinator])

    db_session.expire_all()
    after = db_session.query(AgentMessageLog).count()

    assert after > before, (
        f"Očekivano barem 1 novi log u agent_messages_log, "
        f"before={before} after={after}"
    )
