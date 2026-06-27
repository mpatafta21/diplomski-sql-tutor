"""RecommenderAgent — SPADE omotač oko recommend() logike (3C.2).

Prima `recommend-next` request od Coordinatora, vraća `inform` s preporukom
sljedećeg zadatka: {task_id|None, concept|None, reason}.

Concurrency (pyswip = jedan globalni sync VM, nije thread-safe):
  - mitigacija A: CyclicBehaviour obrađuje poruke serijalno (jedna po jedna)
  - mitigacija B: asyncio.to_thread miče blokirajući sync rad (inject→recommend_next
    →clear + DB čitanja u recommend()) s event loopa
  - mitigacija C: self.prolog_lock (asyncio.Lock) serijalizira Prolog sekciju —
    štiti od budućeg 3E paralelizma (više konkurentnih recommend zahtjeva)

Session lifecycle: novi SessionLocal() po run() pozivu (3A/3B lekcija); nikad
dijeljen kroz pozive.

RecommendationLog: upisuje se SAMO za servirane preporuke (task_id != None), jer
je `recommended_task_id` NOT NULL u shemi. Za exhausted/no_recommendation nema
reda — ti ishodi su zabilježeni u agent_messages_log (inform). Promjena sheme
(nullable task) nije rađena u 3C.2.

Uvijek odgovara informom — i na grešci s reason="error" — da 3E FSM ne visi na
tišini kad čeka recommend odgovor.
"""

from __future__ import annotations

import asyncio
import logging

from spade.behaviour import CyclicBehaviour
from spade.template import Template

from agents.base import TutorAgent
from agents.messages import Ontology, Performative, body_to_payload
from agents.recommender_logic import recommend
from app.db.models import RecommendationLog
from app.db.session import SessionLocal
from app.prolog.prolog_engine import PrologEngine

_log = logging.getLogger(__name__)


class RecommenderAgent(TutorAgent):
    """Preporučuje sljedeći zadatak (Prolog ZPD + BKT) na recommend-next request."""

    class RecommendBehaviour(CyclicBehaviour):

        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            correlation_id: str | None = msg.get_metadata("correlation_id")
            sender = str(msg.sender)
            user_id = None

            try:
                payload = body_to_payload(msg.body)
                user_id = payload["user_id"]

                self.agent.log_message(
                    sender=sender,
                    receiver=str(self.agent.jid),
                    performative=Performative.REQUEST,
                    content=payload,
                    correlation_id=correlation_id,
                )

                with SessionLocal() as session:
                    # Serijaliziraj Prolog sekciju (B+C); sav sync rad u threadu.
                    async with self.agent.prolog_lock:
                        result = await asyncio.to_thread(
                            recommend, session, self.agent.prolog_engine, user_id
                        )

                    # RecommendationLog samo za servirane preporuke (task NOT NULL u shemi).
                    if result["task_id"] is not None:
                        session.add(
                            RecommendationLog(
                                user_id=user_id,
                                recommended_task_id=result["task_id"],
                                strategy=result["reason"],
                                reasoning={
                                    "concept": result["concept"],
                                    "reason": result["reason"],
                                },
                            )
                        )
                        session.commit()

                await self._send_inform(
                    to=sender,
                    payload={"user_id": user_id, **result},
                    correlation_id=correlation_id,
                )

            except Exception:
                _log.exception(
                    "RecommendBehaviour: greška — šaljem error inform, CyclicBehaviour se nastavlja"
                )
                # Uvijek odgovori da Coordinator (3E FSM) ne visi na tišini.
                await self._send_inform(
                    to=sender,
                    payload={
                        "user_id": user_id,
                        "task_id": None,
                        "concept": None,
                        "reason": "error",
                    },
                    correlation_id=correlation_id,
                )

        async def _send_inform(
            self, to: str, payload: dict, correlation_id: str | None
        ) -> None:
            inform = self.agent.build_message(
                to=to,
                performative=Performative.INFORM,
                ontology=Ontology.RECOMMEND_NEXT,
                payload=payload,
                correlation_id=correlation_id,
            )
            await self.send(inform)
            self.agent.log_message(
                sender=str(self.agent.jid),
                receiver=to,
                performative=Performative.INFORM,
                content=payload,
                correlation_id=correlation_id,
            )

    async def setup(self) -> None:
        # Shared PrologEngine (class-level Prolog singleton) + lock za serijalizaciju.
        self.prolog_engine = PrologEngine()
        self.prolog_lock = asyncio.Lock()

        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.RECOMMEND_NEXT)
        self.add_behaviour(self.RecommendBehaviour(), tmpl)
