"""Registry JID-eva i lozinki agenata — čita iz config.py (→ .env)."""

from __future__ import annotations

from app.core import config

_REGISTRY: dict[str, tuple[str, str]] = {
    "evaluator": (config.AGENT_EVALUATOR_JID, config.AGENT_EVALUATOR_PASSWORD),
    "coordinator": (config.AGENT_COORDINATOR_JID, config.AGENT_COORDINATOR_PASSWORD),
    "knowledge": (config.AGENT_KNOWLEDGE_JID, config.AGENT_KNOWLEDGE_PASSWORD),
    "recommender": (config.AGENT_RECOMMENDER_JID, config.AGENT_RECOMMENDER_PASSWORD),
    "gamification": (config.AGENT_GAMIFICATION_JID, config.AGENT_GAMIFICATION_PASSWORD),
}


def get_jid_password(agent_name: str) -> tuple[str, str]:
    """Vrati (jid, password) za danog agenta po imenu.

    Raises:
        KeyError: ako agent_name nije registriran.
    """
    try:
        return _REGISTRY[agent_name]
    except KeyError:
        raise KeyError(
            f"Agent '{agent_name}' nije registriran. Dostupni: {list(_REGISTRY)}"
        )
