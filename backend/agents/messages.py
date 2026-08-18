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
    MODEL_UPDATED = "model-updated"
    # Faza 5.1 — hint ide gateway → HintAgent i natrag pod ISTOM ontologijom
    # (presedan RECOMMEND_NEXT), pa `_Resolve` u gatewayu razlikuje odgovor po njoj.
    REQUEST_HINT = "request-hint"


#: Evaluator odbija isporučiti `model-updated` za ovaj tok — plan izvedbe se nije
#: mogao dohvatiti, pa POKUŠAJ NIJE NI NASTAO (ERRATA #66/#69).
#:
#: 🔴 Živi OVDJE, a ne u `coordinator.py`, jer je to jedina riječ koju evaluator i
#: koordinator moraju dijeliti. Evaluator koji uvozi koordinator obrnuo bi smjer
#: ovisnosti (orkestrator ovisi o agentima, ne obratno).
#:
#: 🔴 Prenosi se PERFORMATIVOM (`refuse`), ne poljem u payloadu. Granananje na
#: sadržaj bilo bi „novo ponašanje bez novog imena" — obrazac koji je u ovom
#: projektu već proizveo tri nalaza (v. wrapup §G2): sutrašnji legitiman
#: `model-updated` s poljem `error` tiho bi prekidao tok. Ontologija je TEMA
#: razgovora, performativ je GOVORNI ČIN: `refuse(model-updated)` = „odbijam
#: isporučiti model-updated za ovaj tok". Presedan: `_refuse_busy`.
ERROR_PLAN_UNAVAILABLE = "plan_unavailable"


# ---------------------------------------------------------------------------
# (De)serijalizacija payloada
# ---------------------------------------------------------------------------

def payload_to_body(payload: dict) -> str:
    """Serijaliziraj dict payload u JSON string za msg.body."""
    return json.dumps(payload, ensure_ascii=False)


def body_to_payload(body: str) -> dict:
    """Deserijaliziraj msg.body JSON string u dict payload."""
    return json.loads(body)
