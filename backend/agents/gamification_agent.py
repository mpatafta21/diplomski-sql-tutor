"""GamificationAgent — SPADE omotač oko persist_gamification() (3D.2).

Prima 'attempt-result' inform od EvaluatorAgenta (isti broadcast koji ide i
KnowledgeModelAgentu) i atomično perzistira XP/level/streak/bedževe.

Opcija A: badge-eval je u Pythonu (gamification_logic.py) — NE konzultira se
badges.pl, NE dira se nijedan Prolog VM. Time Gamification zaobilazi lockless
pyswip VM problem i nema Prolog na hot pathu.

Session lifecycle: novi SessionLocal() po run() pozivu (3A/3B/3C lekcija). Sav
sinkroni DB rad ide kroz asyncio.to_thread (SQLAlchemy je sync; ne blokira loop).

Ovdje se NE šalje downstream inform — notifikacije o level-upu/bedžu su posao
Coordinatora/Faze 3E. Greška u obradi jedne poruke NE ruši CyclicBehaviour.
"""

from __future__ import annotations

import asyncio
import logging

from spade.behaviour import CyclicBehaviour
from spade.template import Template

from agents.base import TutorAgent
from agents.gamification_persistence import AttemptNotFound, persist_gamification
from agents.messages import Ontology, Performative, body_to_payload
from app.db.session import SessionLocal

_log = logging.getLogger(__name__)


class GamificationAgent(TutorAgent):
    """Perzistira gamifikacijske nuspojave na svaki attempt-result inform."""

    class GamificationBehaviour(CyclicBehaviour):

        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            correlation_id: str | None = msg.get_metadata("correlation_id")

            try:
                payload = body_to_payload(msg.body)

                if payload.get("attempt_id") is None:
                    _log.warning(
                        "GamificationAgent: inform bez attempt_id — preskačem (payload=%s)",
                        payload,
                    )
                    return

                self.agent.log_message(
                    sender=str(msg.sender),
                    receiver=str(self.agent.jid),
                    performative=Performative.INFORM,
                    content=payload,
                    correlation_id=correlation_id,
                )

                with SessionLocal() as session:
                    summary = await asyncio.to_thread(
                        persist_gamification, session, payload
                    )

                _log.info(
                    "GamificationAgent: attempt=%s xp_delta=%s level=%s badges=%s streak=%s",
                    payload["attempt_id"],
                    summary["xp_delta"],
                    summary["new_level"],
                    summary["new_badges"],
                    summary["current_streak"],
                )

            except AttemptNotFound:
                _log.warning(
                    "GamificationAgent: attempt ne postoji — preskačem (ne rušim behaviour)"
                )
            except Exception:
                _log.exception(
                    "GamificationBehaviour: neuhvaćena greška — CyclicBehaviour se nastavlja"
                )

    async def setup(self) -> None:
        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.ATTEMPT_RESULT)
        self.add_behaviour(self.GamificationBehaviour(), tmpl)
