"""Bazna klasa za sve SPADE tutoring agente.

TutorAgent proširuje spade.agent.Agent s:
  - automatskim dohvaćanjem JID/lozinke iz jids.py (→ .env)
  - _async_connect overrideom koji disabluje SCRAM bez TLS-a
    (slixmpp odbija SCRAM i PLAIN bez TLS; postavljamo unencrypted_plain=True
    jer Prosody dev config nema TLS — produkcija treba TLS + brisanje ovog flag-a)
  - send_message() helperom koji setira performative + ontology metapodatke
  - log_message() koji upisuje FIPA-ACL poruku u agent_messages_log
"""

from __future__ import annotations

import uuid
from typing import Any

from spade.agent import Agent
from spade.message import Message

from agents.jids import get_jid_password
from agents.messages import payload_to_body
from app.core import config
from app.db.models import AgentMessageLog
from app.db.session import SessionLocal


class TutorAgent(Agent):
    def __init__(self, agent_name: str) -> None:
        jid, password = get_jid_password(agent_name)
        super().__init__(
            jid=jid,
            password=password,
            port=config.XMPP_PORT,
            verify_security=False,
        )

    async def _async_connect(self) -> None:
        # DEV: slixmpp odbija PLAIN i SCRAM bez TLS-a — dopusti PLAIN eksplicitno.
        self.client["feature_mechanisms"].unencrypted_plain = True
        await super()._async_connect()

    # ------------------------------------------------------------------
    # Helperi za slanje
    # ------------------------------------------------------------------

    def build_message(
        self,
        to: str,
        performative: str,
        ontology: str,
        payload: dict,
        correlation_id: str | None = None,
    ) -> Message:
        """Napravi Message s postavljenim metapodacima i JSON bodyem."""
        msg = Message(to=to)
        msg.set_metadata("performative", performative)
        msg.set_metadata("ontology", ontology)
        if correlation_id:
            msg.set_metadata("correlation_id", correlation_id)
        msg.body = payload_to_body(payload)
        return msg

    def log_message(
        self,
        sender: str,
        receiver: str,
        performative: str,
        content: dict | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Upiši FIPA-ACL poruku u agent_messages_log (best-effort, ne blokira agent)."""
        try:
            corr_uuid: uuid.UUID | None = (
                uuid.UUID(correlation_id) if correlation_id else None
            )
            with SessionLocal() as session:
                session.add(
                    AgentMessageLog(
                        sender=sender,
                        receiver=receiver,
                        performative=performative,
                        content=content,
                        correlation_id=corr_uuid,
                    )
                )
                session.commit()
        except Exception:
            pass  # log greška ne smije srušiti agenta
