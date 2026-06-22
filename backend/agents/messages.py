"""FIPA-ACL konstante i (de)serijalizacija poruka.

Sve što je vezano uz formate poruka ide ovdje — bez agent-specifične logike.
"""

from __future__ import annotations

import json


# ---------------------------------------------------------------------------
# Performative konstante (FIPA-ACL subset koji koristimo)
# ---------------------------------------------------------------------------
class Performative:
    REQUEST = "request"
    INFORM = "inform"
    QUERY_REF = "query-ref"
    FAILURE = "failure"
    REFUSE = "refuse"


# ---------------------------------------------------------------------------
# Ontology konstante
# ---------------------------------------------------------------------------
class Ontology:
    EVALUATE_QUERY = "evaluate-query"
    ATTEMPT_RESULT = "attempt-result"
    RECOMMEND_NEXT = "recommend-next"
    UPDATE_MASTERY = "update-mastery"
    GAMIFICATION_EVENT = "gamification-event"


# ---------------------------------------------------------------------------
# (De)serijalizacija payloada
# ---------------------------------------------------------------------------

def payload_to_body(payload: dict) -> str:
    """Serijaliziraj dict payload u JSON string za msg.body."""
    return json.dumps(payload, ensure_ascii=False)


def body_to_payload(body: str) -> dict:
    """Deserijaliziraj msg.body JSON string u dict payload."""
    return json.loads(body)
