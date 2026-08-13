"""EvaluatorAgent — SPADE omotač oko evaluate() + persist_attempt().

Prima FIPA-ACL request s ontologijom 'evaluate-query', evaluira SQL upit
u sandboxu, persistira attempt i šalje 'attempt-result' inform prema
KnowledgeModelAgentu i GamificationAgentu.

D6 garancija: persist_attempt() commitira PRIJE nego se inform pošalje,
čime 3B/3D agenti mogu odmah čitati committed attempt red po attempt_id.

Session lifecycle: novi SessionLocal() otvara se u svakom run() pozivu;
nikad se ne dijeli kroz pozive (izbjegava stale data i thread issues).
"""

from __future__ import annotations

import logging

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from spade.behaviour import CyclicBehaviour
from spade.template import Template

from agents.base import TutorAgent
from agents.evaluation import evaluate
from agents.messages import Ontology, Performative, body_to_payload
from agents.persistence import persist_attempt
from app.core import config
from app.db.models import Attempt, Concept, Task, TaskConcept
from app.db.session import SessionLocal
from scripts.lib.sandbox_runner import SandboxRunner

_log = logging.getLogger(__name__)


def persist_sqlstate(session: Session, attempt_id: int, sqlstate: str | None) -> bool:
    """Upiši PG SQLSTATE na već perzistiran attempt. Vrati je li upisan.

    🔴 ZAŠTO ZASEBAN UPIS, a ne polje u ``persist_attempt``: ``persistence.py`` je
    zamrznut (odluka 8 plana 5.1), a ``persist_attempt`` gradi ``Attempt(...)`` sa
    zatvorenim popisom polja — ``sqlstate`` kroz njega ne može bez izmjene te
    datoteke. Odluka korisnika 2026-08-12: zaseban ``UPDATE`` ovdje.

    🔴 Poštuje D6: ``persist_attempt`` je već commitao, pa ``attempt_id`` postoji i
    redak je vidljiv nizvodnim agentima. Ovaj upis ide PRIJE ``inform``a, dakle
    nijedan agent ne vidi redak bez koda koji bi trebao imati.

    🔴 No-op kad koda nema — a nema ga za sve osim ``execution_error``/``timeout``
    (živo ~3/13 pokušaja). Bezuvjetni UPDATE bio bi trošak na svakom ``POST /attempt``
    bez ijedne dobiti.
    """
    if sqlstate is None:
        return False
    session.execute(
        update(Attempt).where(Attempt.id == attempt_id).values(sqlstate=sqlstate)
    )
    session.commit()
    return True


def _sandbox_conn_string() -> str:
    """Vrati psycopg3 connection string bez SQLAlchemy dialect prefiksa."""
    raw = config.SANDBOX_DATABASE_URL or (
        "postgresql+psycopg://sandbox_admin:sandbox_dev_password@localhost:5433/sandbox"
    )
    return raw.replace("postgresql+psycopg://", "postgresql://")


class EvaluatorAgent(TutorAgent):
    """Evaluira SQL pokušaje studenata i usmjerava rezultate prema 3B/3D agentima."""

    class EvaluateBehaviour(CyclicBehaviour):

        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            correlation_id: str | None = msg.get_metadata("correlation_id")

            try:
                payload = body_to_payload(msg.body)
                user_id: int = payload["user_id"]
                task_id: int = payload["task_id"]
                submitted_query: str = payload["submitted_query"]

                self.agent.log_message(
                    sender=str(msg.sender),
                    receiver=str(self.agent.jid),
                    performative=Performative.REQUEST,
                    content=payload,
                    correlation_id=correlation_id,
                )

                runner = SandboxRunner(_sandbox_conn_string())

                with SessionLocal() as session:
                    task = session.get(Task, task_id)

                    if task is None:
                        await self._send_task_not_found(
                            to=str(msg.sender),
                            user_id=user_id,
                            task_id=task_id,
                            correlation_id=correlation_id,
                        )
                        return

                    concepts, primary_concept = self._load_concepts(session, task_id)

                    outcome = evaluate(
                        task,
                        submitted_query,
                        runner,
                        primary_concept_code=primary_concept,
                    )

                    attempt_id = persist_attempt(
                        session, user_id, task_id, submitted_query, outcome
                    )
                    # session je committana (D6) — attempt_id je validan

                    # Faza 5.1 (B1): SQLSTATE ide zasebnim upisom jer je
                    # `persistence.py` zamrznut (odluka 8). No-op osim za
                    # execution_error/timeout. Ide PRIJE informa, pa nizvodni
                    # agenti nikad ne vide redak bez koda koji bi trebao imati.
                    persist_sqlstate(session, attempt_id, outcome.sqlstate)

                result_payload: dict = {
                    "attempt_id": attempt_id,
                    "user_id": user_id,
                    "task_id": task_id,
                    "is_correct": outcome.is_correct,
                    "error_type": outcome.error_type,
                    "verdict": outcome.verdict,
                    "execution_time_ms": outcome.execution_time_ms,
                    "concepts": concepts,
                    "primary_concept": primary_concept,
                }

                for target_jid in (
                    config.AGENT_KNOWLEDGE_JID,
                    config.AGENT_GAMIFICATION_JID,
                ):
                    inform = self.agent.build_message(
                        to=target_jid,
                        performative=Performative.INFORM,
                        ontology=Ontology.ATTEMPT_RESULT,
                        payload=result_payload,
                        correlation_id=correlation_id,
                    )
                    await self.send(inform)
                    self.agent.log_message(
                        sender=str(self.agent.jid),
                        receiver=target_jid,
                        performative=Performative.INFORM,
                        content=result_payload,
                        correlation_id=correlation_id,
                    )

            except Exception:
                _log.exception(
                    "EvaluateBehaviour: neuhvaćena greška — CyclicBehaviour se nastavlja"
                )

        async def _send_task_not_found(
            self,
            to: str,
            user_id: int,
            task_id: int,
            correlation_id: str | None,
        ) -> None:
            error_payload = {
                "user_id": user_id,
                "task_id": task_id,
                "is_correct": False,
                "verdict": "incorrect",
                "error_type": "task_not_found",
            }
            msg = self.agent.build_message(
                to=to,
                performative=Performative.INFORM,
                ontology=Ontology.ATTEMPT_RESULT,
                payload=error_payload,
                correlation_id=correlation_id,
            )
            await self.send(msg)
            self.agent.log_message(
                sender=str(self.agent.jid),
                receiver=to,
                performative=Performative.INFORM,
                content=error_payload,
                correlation_id=correlation_id,
            )

        @staticmethod
        def _load_concepts(
            session, task_id: int
        ) -> tuple[list[dict], str | None]:
            rows = session.execute(
                select(Concept.code, TaskConcept.is_primary)
                .join(TaskConcept, Concept.id == TaskConcept.concept_id)
                .where(TaskConcept.task_id == task_id)
            ).all()
            concepts = [{"code": r.code, "is_primary": r.is_primary} for r in rows]
            primary = next((c["code"] for c in concepts if c["is_primary"]), None)
            return concepts, primary

    async def setup(self) -> None:
        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.EVALUATE_QUERY)
        self.add_behaviour(self.EvaluateBehaviour(), tmpl)
