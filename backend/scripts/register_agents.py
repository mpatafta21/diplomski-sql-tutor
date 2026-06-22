"""Registriraj sve SPADE agente u Prosody XMPP server.

Idempotentno — prosodyctl register je siguran za poziv na već postojeći račun
(exit 0, ne ruši skript). Pokreni iz backend/ direktorija:

    python scripts/register_agents.py

Preduvjeti:
  - Docker container 'sql-tutor-prosody' mora biti aktivan
  - .env mora biti populiran s JID-evima i lozinkama
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Dodaj backend/ u sys.path kad se skript poziva direktno
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import config

_PROSODY_CONTAINER = "sql-tutor-prosody"


def _jid_parts(jid: str) -> tuple[str, str]:
    """Razdvoji 'user@host' u (user, host)."""
    user, host = jid.split("@", 1)
    return user, host


_AGENTS: list[tuple[str, str]] = [
    (config.AGENT_EVALUATOR_JID, config.AGENT_EVALUATOR_PASSWORD),
    (config.AGENT_COORDINATOR_JID, config.AGENT_COORDINATOR_PASSWORD),
    (config.AGENT_KNOWLEDGE_JID, config.AGENT_KNOWLEDGE_PASSWORD),
    (config.AGENT_RECOMMENDER_JID, config.AGENT_RECOMMENDER_PASSWORD),
    (config.AGENT_GAMIFICATION_JID, config.AGENT_GAMIFICATION_PASSWORD),
]


def _register(jid: str, password: str) -> bool:
    user, host = _jid_parts(jid)
    result = subprocess.run(
        [
            "docker", "exec", _PROSODY_CONTAINER,
            "prosodyctl", "register", user, host, password,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  GREŠKA ({result.returncode}): {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def main() -> None:
    print(f"Prosody container: {_PROSODY_CONTAINER}")
    ok = 0
    for jid, password in _AGENTS:
        print(f"  Registriram {jid} ...", end=" ", flush=True)
        if _register(jid, password):
            print("OK")
            ok += 1
        else:
            print("GREŠKA")

    print(f"\nRegistrirano {ok}/{len(_AGENTS)} agenata.")
    if ok < len(_AGENTS):
        sys.exit(1)


if __name__ == "__main__":
    main()
