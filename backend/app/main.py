"""FastAPI HTTP gateway (Faza 3E.3) — zatvara Fazu 3E.

End-to-end: HTTP → AgentBridge → FIPA Coordinatoru → FSM → FIPA reply → bridge → HTTP.

🔴 PLAIN-BRIDGE INVARIANT (3E.2a KORAK 0): AgentBridge je plain asyncio (future.set_result
direktno) i vrijedi SAMO ako Coordinator behaviour i HTTP handler dijele isti event loop.
Zato se SVI agenti INSTANCIRAJU i STARTAJU UNUTAR uvicornovog loopa (lifespan) — SPADE
Container posvaja loop koji teče u trenutku prve instancijacije (Agent.__init__). Nikad ne
instanciraj agente na import-time (loop tada ne postoji → Container bi vezao tuđi loop).

start_gateway_stack/stop_gateway_stack su izdvojeni da ih i integracijski testovi mogu
pozvati na svom event loopu (s mock agentima) bez pokretanja produkcijskog lifespana.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.coordinator import CoordinatorAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.gamification_agent import GamificationAgent
from agents.hint_agent import HintAgent
from agents.knowledge_agent import KnowledgeModelAgent
from agents.recommender_agent import RecommenderAgent
from app.api.routes import router
from app.bridge.agent_bridge import AgentBridge
from app.bridge.gateway_agent import GatewayAgent
from app.core import config

_log = logging.getLogger(__name__)


def _build_domain_agents() -> list:
    """Produkcijski set: 5 domenskih agenata + Coordinator (instancirano na tekućem loopu).

    Faza 5.1: HintAgent je šesti. Startanjem NE ulazi ni u jedan postojeći tok —
    sluša vlastitu ontologiju (`request-hint`) i nikad ne prima poruke Coordinatora.
    Dok je `USE_LLM_HINTS=false`, do njega ne dolazi ni jedan zahtjev.
    """
    return [
        EvaluatorAgent("evaluator"),
        KnowledgeModelAgent("knowledge"),
        RecommenderAgent("recommender"),
        GamificationAgent("gamification"),
        HintAgent("hint"),
        CoordinatorAgent("coordinator"),
    ]


async def start_gateway_stack(app: FastAPI, *, agents: list | None = None) -> None:
    """Instanciraj bridge+gateway, startaj agente na TEKUĆEM (uvicorn) loopu, spoji app.state.

    agents=None → produkcijski set. Testovi prosljeđuju mock agente.
    """
    bridge = AgentBridge()
    gateway = GatewayAgent(bridge)

    domain_agents = agents if agents is not None else _build_domain_agents()
    for agent in domain_agents:
        await agent.start(auto_register=False)
    await gateway.start(auto_register=True)  # gateway JID se registrira in-band (dev)

    app.state.bridge = bridge
    app.state.gateway = gateway
    app.state.agents = domain_agents
    _log.info("Gateway stack started: %d agenata + gateway", len(domain_agents))


async def stop_gateway_stack(app: FastAPI) -> None:
    """Zaustavi gateway + sve agente čisto."""
    for agent in [app.state.gateway, *app.state.agents]:
        if agent.is_alive():
            await agent.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_gateway_stack(app)
    try:
        yield
    finally:
        await stop_gateway_stack(app)


def create_app() -> FastAPI:
    app = FastAPI(title="SQL Tutor Gateway", version="3E.3", lifespan=lifespan)
    # CORS (Faza 4.1a): Vite frontend (:5173) → gateway (:8000) je cross-origin.
    # Bearer JWT ide u Authorization header (ne cookie) → allow_credentials=False,
    # što dopušta allow_headers=["*"] (uklj. Authorization) bez wildcard-credentials sukoba.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
