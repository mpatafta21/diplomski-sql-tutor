"""GatewayAgent — XMPP arm HTTP gatewaya (Faza 3E.3).

KORAK 0 wiring odluka (Coordinator↔bridge bez prljanja FIPA razdvoja):
  CoordinatorAgent (3E.2b) ostaje ČISTI FIPA agent — on samo odgovara pošiljatelju
  (attempt-response na msg.sender). GatewayAgent je dedicirani SPADE agent koji glumi
  tog pošiljatelja: HTTP ruta kroz njega šalje FIPA zahtjev (sender = gateway JID), a
  kad korelirani FIPA odgovor stigne natrag na gateway JID, GatewayAgent rezolvira
  odgovarajući AgentBridge Future po correlation_id-u.

Time je granica HTTP↔XMPP čista: bridge (plain asyncio Future registry) ↔ gateway
(XMPP I/O) ↔ Coordinator (orkestracija). Nijedan domenski agent ne zna za bridge/HTTP.

Plain-asyncio invariant (3E.2a): GatewayAgent se starta UNUTAR uvicornovog loopa
(app lifespan), pa bridge.resolve() iz _Resolve behavioura i HTTP handler koji čeka
Future dijele isti event loop → future.set_result je siguran.
"""

from __future__ import annotations

import logging

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.template import Template

from agents.base import TutorAgent
from agents.coordinator import ONTOLOGY_ATTEMPT_RESPONSE
from agents.messages import Ontology, Performative, body_to_payload
from app.bridge.agent_bridge import AgentBridge
from app.core import config

_log = logging.getLogger(__name__)


class GatewayAgent(TutorAgent):
    """Šalje FIPA zahtjeve u ime HTTP ruta i rezolvira bridge Future po reply-cidu."""

    def __init__(self, bridge: AgentBridge) -> None:
        # Zaobiđi jids.py registry (gateway je bridge-sloj, ne jedan od 5 domenskih agenata).
        Agent.__init__(
            self,
            jid=config.AGENT_GATEWAY_JID,
            password=config.AGENT_GATEWAY_PASSWORD,
            port=config.XMPP_PORT,
            verify_security=False,
        )
        self._bridge = bridge

    class _Resolve(CyclicBehaviour):
        """Hvata korelirane FIPA odgovore i rezolvira pripadni Future u bridgeu."""

        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return
            cid = msg.get_metadata("correlation_id")
            if not cid:
                _log.warning("GatewayAgent: odgovor bez correlation_id — ignoriram")
                return
            try:
                payload = body_to_payload(msg.body)
            except Exception:
                payload = {}
            resolved = self.agent._bridge.resolve(cid, payload)
            if not resolved:
                # cid nepoznat ili Future već dovršen (npr. HTTP već timeoutao) — benigno.
                _log.debug("GatewayAgent: nije rezolviran cid=%s (nepoznat/already-done)", cid)

    async def setup(self) -> None:
        # Sluša TRI tipa odgovora: attempt-response (od Coordinatora, /attempt),
        # recommend-next (izravno od Recommendera, /next-task) i request-hint
        # (izravno od HintAgenta, /hint).
        #
        # 🔴 Faza 5.1: bez `t_hint` u ovom OR-u odgovor HintAgenta stigne na gateway,
        # ne odgovara nijednom predlošku, nikad ne uđe u `_Resolve`, i Future ostane
        # neriješen do `HINT_TIMEOUT` → svaki `/hint` bi bio 504. Predložak je jedina
        # stvar koja te dvije komponente povezuje.
        t_attempt = Template()
        t_attempt.set_metadata("ontology", ONTOLOGY_ATTEMPT_RESPONSE)
        t_recommend = Template()
        t_recommend.set_metadata("ontology", Ontology.RECOMMEND_NEXT)
        t_hint = Template()
        t_hint.set_metadata("ontology", Ontology.REQUEST_HINT)
        self.add_behaviour(self._Resolve(), t_attempt | t_recommend | t_hint)

    def send_fipa(
        self,
        *,
        to: str,
        ontology: str,
        payload: dict,
        cid: str,
        performative: str = Performative.REQUEST,
    ) -> None:
        """Zakaži slanje jednog FIPA zahtjeva (ne blokira HTTP handler).

        Slanje ide kroz OneShotBehaviour na agentovom loopu; sender = gateway JID,
        pa odgovor dolazi natrag na gateway i _Resolve ga pokupi.
        """
        gateway = self

        class _Send(OneShotBehaviour):
            async def run(self) -> None:
                msg = gateway.build_message(
                    to=to,
                    performative=performative,
                    ontology=ontology,
                    payload=payload,
                    correlation_id=cid,
                )
                await self.send(msg)
                gateway.log_message(
                    sender=str(gateway.jid),
                    receiver=to,
                    performative=performative,
                    content=payload,
                    correlation_id=cid,
                )

        self.add_behaviour(_Send())
