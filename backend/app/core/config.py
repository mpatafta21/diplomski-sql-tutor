"""Konfiguracija iz .env fajla.

Učitava environment varijable preko python-dotenv i izlaže ih kao
modul-level konstante. Iznimka se baca rano ako DATABASE_URL nedostaje.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_DIR / ".env")


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Obavezna env varijabla nedostaje: {name}")
    return value


DATABASE_URL: str = _required("DATABASE_URL")
SANDBOX_DATABASE_URL: str | None = os.getenv("SANDBOX_DATABASE_URL")

# XMPP / Prosody
XMPP_SERVER: str = os.getenv("XMPP_SERVER", "localhost")
XMPP_PORT: int = int(os.getenv("XMPP_PORT", "5222"))
# Dopušta PLAIN bez TLS-a — samo za dev; produkcija zahtijeva TLS+SCRAM
XMPP_ALLOW_PLAINTEXT: bool = os.getenv("XMPP_ALLOW_PLAINTEXT", "false").lower() == "true"

AGENT_EVALUATOR_JID: str = os.getenv("AGENT_EVALUATOR_JID", "evaluator@localhost")
AGENT_EVALUATOR_PASSWORD: str = os.getenv("AGENT_EVALUATOR_PASSWORD", "eval_pw")

AGENT_COORDINATOR_JID: str = os.getenv("AGENT_COORDINATOR_JID", "coordinator@localhost")
AGENT_COORDINATOR_PASSWORD: str = os.getenv("AGENT_COORDINATOR_PASSWORD", "coord_pw")

AGENT_KNOWLEDGE_JID: str = os.getenv("AGENT_KNOWLEDGE_JID", "knowledge@localhost")
AGENT_KNOWLEDGE_PASSWORD: str = os.getenv("AGENT_KNOWLEDGE_PASSWORD", "know_pw")

AGENT_RECOMMENDER_JID: str = os.getenv("AGENT_RECOMMENDER_JID", "recommender@localhost")
AGENT_RECOMMENDER_PASSWORD: str = os.getenv("AGENT_RECOMMENDER_PASSWORD", "recom_pw")

AGENT_GAMIFICATION_JID: str = os.getenv("AGENT_GAMIFICATION_JID", "gamification@localhost")
AGENT_GAMIFICATION_PASSWORD: str = os.getenv("AGENT_GAMIFICATION_PASSWORD", "gamif_pw")

# Gateway (3E.3) — XMPP arm HTTP gatewaya; most između AgentBridge i FIPA svijeta.
AGENT_GATEWAY_JID: str = os.getenv("AGENT_GATEWAY_JID", "gateway@localhost")
AGENT_GATEWAY_PASSWORD: str = os.getenv("AGENT_GATEWAY_PASSWORD", "gateway_pw")

# HTTP gateway timeout (s) — MORA biti > Coordinator UPDATE+RECOMMEND timeouta, da
# gateway ne istekne PRIJE Coordinatorovog definiranog timeout-odgovora.
GATEWAY_TIMEOUT: float = float(os.getenv("GATEWAY_TIMEOUT", "15"))
