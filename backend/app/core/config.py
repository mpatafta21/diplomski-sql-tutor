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


def _list(name: str, default: list[str]) -> list[str]:
    """Comma-separated env varijabla → lista; prazno/odsutno → default."""
    raw = os.getenv(name)
    if not raw:
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


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

# JWT auth (Faza 4.0b) — JWT_SECRET je OBAVEZAN (isti obrazac kao DATABASE_URL).
JWT_SECRET: str = _required("JWT_SECRET")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Seed admin (Faza 4.0b) — kredencijali iz env-a; password se NIKAD ne hardkodira.
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@sql-tutor.local")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin_dev_password")

# CORS (Faza 4.1a) — dopušteni origini za Vite frontend (cross-origin :5173 → :8000).
# Comma-separated override kroz env; default pokriva Vite dev server.
CORS_ORIGINS: list[str] = _list(
    "CORS_ORIGINS",
    ["http://localhost:5173", "http://127.0.0.1:5173"],
)
