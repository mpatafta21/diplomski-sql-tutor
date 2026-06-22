"""KnowledgeModelAgent — SPADE omotač oko update_mastery_for_attempt().

Prima attempt-result inform od EvaluatorAgenta, updatea skill_mastery
tablicu kroz BKT logiku iz knowledge_logic.py.

Session lifecycle: novi SessionLocal() otvara se u svakom run() pozivu
(isti princip kao EvaluatorAgent). PrologEngine instanca je shared na
razini agenta jer je pyswip Prolog class-level singleton — višestruke
instance dijele istu Prolog VM. get_tier() pozivi idu kroz asyncio.to_thread
(enkapsuliran u update_mastery_for_attempt).

Greška u obradi jedne poruke ne ubija CyclicBehaviour — agent logira i nastavlja.
"""

from __future__ import annotations

import asyncio
import logging

from spade.behaviour import CyclicBehaviour
from spade.template import Template

from agents.base import TutorAgent
from agents.knowledge_logic import update_mastery_for_attempt
from agents.messages import Ontology, Performative, body_to_payload
from app.db.session import SessionLocal
from app.prolog.prolog_engine import PrologEngine

_log = logging.getLogger(__name__)


class KnowledgeModelAgent(TutorAgent):
    """Updatea BKT model znanja na temelju attempt-result informa."""

    class UpdateBehaviour(CyclicBehaviour):

        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            try:
                payload = body_to_payload(msg.body)

                user_id: int = payload["user_id"]
                is_correct: bool = payload["is_correct"]
                concepts: list[str] = [c["code"] for c in payload["concepts"]]
                correlation_id: str | None = msg.get_metadata("correlation_id")

                self.agent.log_message(
                    sender=str(msg.sender),
                    receiver=str(self.agent.jid),
                    performative=Performative.INFORM,
                    content=payload,
                    correlation_id=correlation_id,
                )

                with SessionLocal() as session:
                    updated = await update_mastery_for_attempt(
                        session,
                        self.agent.prolog_engine,
                        user_id,
                        concepts,
                        is_correct,
                    )

                _log.info(
                    "KnowledgeModelAgent: user=%s updated=%s concepts",
                    user_id,
                    len(updated),
                )

                # TODO: pošalji "model-updated" inform Coordinatoru kad 3E zatreba orkestraciju
                # payload = {"user_id": user_id, "updated_concepts": updated}

            except Exception:
                _log.exception(
                    "UpdateBehaviour: neuhvaćena greška — CyclicBehaviour se nastavlja"
                )

    async def setup(self) -> None:
        # Shared PrologEngine za get_tier() u lazy init (class-level Prolog singleton)
        self.prolog_engine = PrologEngine()

        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.ATTEMPT_RESULT)
        self.add_behaviour(self.UpdateBehaviour(), tmpl)
