"""HintAgent — 6. agent (Faza 5.1): LLM hint s fallbackom na katalog.

🔴 NE ULAZI U COORDINATOROV FSM (§B.4.4). Coordinator serijalizira SVE studentske
tokove kroz jedan mailbox; LLM poziv traje sekunde, pa bi kroz FSM svaka tuđa
`POST /attempt` čekala taj poziv i uz `GATEWAY_TIMEOUT=15` padala u 504. Ide se
izravno gateway → HintAgent, po presedanu `/next-task`.

🔴 SAV SINKRONI RAD IDE U `asyncio.to_thread`. SPADE dijeli JEDAN event loop s
uvicornom (plain-bridge invariant). Blokirajući SDK poziv od 8 s na tom loopu
zaustavio bi svaki HTTP handler u procesu — ista regresija koju §B.4.4 izbjegava
zaobilaženjem FSM-a, samo drugim putem.

Performativi (§B.4.2): `inform` kad je hint sastavljen, `failure` kad ni LLM ni
katalog nemaju ništa. `refuse` (limit) ovdje NEMA proizvođača — limit se provjerava
u ruti, prije nego se agent uopće probudi; v. `docs/faza-5-1-wrapup.md`.
"""

from __future__ import annotations

import asyncio
import logging

from spade.behaviour import CyclicBehaviour
from spade.template import Template

from agents.base import TutorAgent
from agents.hint_llm import HintLLMError, generate_hint
from agents.hint_logic import (
    fallback_hint,
    mastery_p_l,
    primary_concept,
    unlocking_attempt,
)
from agents.hint_payload import build_hint_payload
from agents.messages import Ontology, Performative, body_to_payload
from app.core import config
from app.db.models import HintRequest, Task
from app.db.session import SessionLocal

_log = logging.getLogger(__name__)

#: Razlozi neuspjeha koje ruta prevodi u HTTP kod.
REASON_UNAVAILABLE = "hint_unavailable"
REASON_NOT_UNLOCKED = "hint_not_unlocked"


def produce_hint(user_id: int, task_id: int) -> dict:
    """Sastavi hint i UPIŠI `hint_requests`. Sinkrono — poziva se kroz to_thread.

    Redoslijed je namjeran: LLM → katalog → ništa. Katalog nije zamjena za LLM
    nego mreža ispod njega, pa se poziv ne preskače kad je flag uključen.

    🔴 UPIS ISHODA JE OVDJE, a ne u ruti, i to je odluka s razlogom: ako HTTP klijent
    odustane (504, zatvorena kartica), poziv je već plaćen. Zapis u agentu bilježi i
    taj slučaj; zapis u ruti bi ga izgubio i telemetrija bi podbrojila potrošnju.

    🔴 `source='unavailable'` se UPISUJE iako student ništa nije dobio — rupa u
    pokrivenosti kataloga se mjeri, ne prešućuje. Taj redak NE troši kredit (C.1).

    Returns:
        Na uspjeh: ``{task_id, source, hint_text, concept, error_type}``.
        Na neuspjeh: ``{task_id, error: REASON_*}``.
    """
    with SessionLocal() as session:
        attempt = unlocking_attempt(session, user_id, task_id)
        if attempt is None:
            # Utrka između provjere u ruti i ovog trenutka (student je u međuvremenu
            # riješio zadatak). Nema retka — zahtjev nikad nije ušao u posluživanje.
            return {"task_id": task_id, "error": REASON_NOT_UNLOCKED}

        task = session.get(Task, task_id)
        if task is None:  # pragma: no cover — FK na attempts to sprječava
            return {"task_id": task_id, "error": REASON_NOT_UNLOCKED}

        concept_id, concept_code = primary_concept(session, task_id)
        error_type = attempt.error_type or "unsupported_eval"

        hint_text: str | None = None
        source = "unavailable"
        hint_id: int | None = None

        if config.USE_LLM_HINTS and config.ANTHROPIC_API_KEY:
            payload = build_hint_payload(
                task=task,
                error_type=error_type,
                detail=attempt.detail,
                sqlstate=attempt.sqlstate,
                concept_code=concept_code,
                p_l=mastery_p_l(session, user_id, concept_id),
            )
            try:
                hint_text = generate_hint(payload).text
                source = "llm"
            except HintLLMError as e:
                # Bez ponavljanja (odluka 1) — odmah na katalog.
                _log.warning("HintAgent: LLM pao, idem na katalog: %s", e)

        if hint_text is None:
            row = fallback_hint(session, error_type, concept_id)
            if row is not None:
                hint_text, hint_id, source = row.hint_text, row.id, "fallback"

        session.add(
            HintRequest(
                user_id=user_id,
                task_id=task_id,
                after_attempt_id=attempt.id,
                error_type=error_type,
                source=source,
                hint_id=hint_id,
                hint_text=hint_text,
            )
        )
        session.commit()

        if hint_text is None:
            return {"task_id": task_id, "error": REASON_UNAVAILABLE}
        return {
            "task_id": task_id,
            "source": source,
            "hint_text": hint_text,
            "concept": concept_code,
            "error_type": error_type,
        }


class HintAgent(TutorAgent):
    """Odgovara na `request-hint`: sastavi hint (LLM ili katalog) i vrati ga."""

    class HintBehaviour(CyclicBehaviour):

        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return

            correlation_id: str | None = msg.get_metadata("correlation_id")
            sender = str(msg.sender)
            task_id = None

            try:
                payload = body_to_payload(msg.body)
                user_id = payload["user_id"]
                task_id = payload["task_id"]

                # Dolazni zahtjev nosi samo identifikatore — ništa za redigirati.
                self.agent.log_message(
                    sender=sender,
                    receiver=str(self.agent.jid),
                    performative=Performative.REQUEST,
                    content={"user_id": user_id, "task_id": task_id},
                    correlation_id=correlation_id,
                )

                result = await asyncio.to_thread(produce_hint, user_id, task_id)

            except Exception:
                _log.exception("HintBehaviour: greška — šaljem failure, agent se nastavlja")
                result = {"task_id": task_id, "error": REASON_UNAVAILABLE}

            await self._reply(sender, result, correlation_id)

        async def _reply(
            self, to: str, result: dict, correlation_id: str | None
        ) -> None:
            performative = (
                Performative.FAILURE if "error" in result else Performative.INFORM
            )
            reply = self.agent.build_message(
                to=to,
                performative=performative,
                ontology=Ontology.REQUEST_HINT,
                payload=result,
                correlation_id=correlation_id,
            )
            await self.send(reply)
            # 🔴 D4: u `agent_messages_log` ide REDIGIRAN sadržaj. Tekst hinta je
            # jedini podatak u lancu koji je LLM proizveo o studentovom radu; log je
            # trajan i izvozi se, pa se bilježi samo njegovo POSTOJANJE i duljina.
            # `base.py` se pritom ne dira — redigira se sadržaj, ne mehanizam.
            self.agent.log_message(
                sender=str(self.agent.jid),
                receiver=to,
                performative=performative,
                content={
                    "task_id": result.get("task_id"),
                    "source": result.get("source", "unavailable"),
                    "hint_len": len(result.get("hint_text") or ""),
                    "error": result.get("error"),
                },
                correlation_id=correlation_id,
            )

    async def setup(self) -> None:
        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.REQUEST_HINT)
        self.add_behaviour(self.HintBehaviour(), tmpl)
