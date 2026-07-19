"""Smoke ŽIVOG PUTA (Faza 4.4-0g, KORAK 1b) — HTTP `/attempt` end-to-end.

Pokreni iz ``backend/`` (gateway + agenti MORAJU vrtjeti)::

    uv run python -m scripts.smoke_live_attempt
    uv run python -m scripts.smoke_live_attempt --base-url http://localhost:8000

🔴 ZAŠTO POSTOJI: `make sweep` zove `agents.evaluation.evaluate` IZRAVNO i time
zaobilazi cijeli živi put — HTTP gateway, AgentBridge, XMPP/Prosody, Coordinator
FSM, Evaluator/Knowledge/Gamification agente. Sweep je zato ostajao ZELEN i kad
`/attempt` pada (npr. neregistrirani XMPP računi nakon `docker compose down -v`).
Ovaj smoke pokriva točno tu rupu: jedan pravi POST kroz cijeli lanac.

Kriterij prolaza: referentni upit AKTIVNOG taska poslan kroz `/attempt` mora dati
`feedback.is_correct = true`. Ne-nul exit inače.

NALAZ #9 disciplina: koristi vlastitog `demo44_smoke` usera i briše ga (s FK-safe
redoslijedom) na kraju — i na uspjehu i na padu. Ne dira `demo44_student`.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

import httpx
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.db.models import (
    Attempt,
    SkillMasteryHistory,
    Task,
    User,
    XpLog,
)
from app.db.session import SessionLocal

logger = logging.getLogger("smoke_live_attempt")

DEFAULT_BASE_URL = os.environ.get("SEED_BASE_URL", "http://localhost:8000")
HTTP_TIMEOUT = 60.0  # agentski lanac (XMPP → FSM → 3 agenta) zna biti spor na hladno

SMOKE_USERNAME = "demo44_smoke"
SMOKE_EMAIL = "demo44-smoke@mailinator.com"
SMOKE_PASSWORD = "demo44_pw_Str0ng!"


def pick_task(session: Session) -> tuple[int, str, str]:
    """Determinističan izbor: aktivan task s najmanjim id-em koji ima ≥1 očekivani redak."""
    row = session.execute(
        select(Task.id, Task.source_id, Task.expected_query)
        .where(
            Task.is_active.is_(True),
            func.jsonb_array_length(Task.expected_result) >= 1,
        )
        .order_by(Task.id)
        .limit(1)
    ).first()
    if row is None:
        raise SystemExit(
            "🔴 SMOKE PAO: nema nijednog aktivnog taska — baza nije seedana "
            "(make db-tasks && make sandbox-seed)."
        )
    return int(row[0]), str(row[1]), str(row[2])


def cleanup(username: str) -> None:
    """Obriši smoke usera i SVE ovisne retke (FK-safe red; ostali su CASCADE)."""
    with SessionLocal() as session:
        uid = session.scalar(select(User.id).where(User.username == username))
        if uid is None:
            return
        session.execute(
            delete(SkillMasteryHistory).where(SkillMasteryHistory.user_id == uid)
        )
        session.execute(delete(XpLog).where(XpLog.user_id == uid))
        session.execute(delete(Attempt).where(Attempt.user_id == uid))
        session.execute(delete(User).where(User.id == uid))
        session.commit()
        logger.info("Cleanup: smoke user %r obrisan.", username)


def run_smoke(base_url: str) -> None:
    with SessionLocal() as session:
        task_id, source_id, expected_query = pick_task(session)
    logger.info("Task za smoke: id=%s source_id=%s", task_id, source_id)

    cleanup(SMOKE_USERNAME)  # ostatak prethodnog pada
    with httpx.Client(timeout=HTTP_TIMEOUT) as client:
        r = client.post(
            f"{base_url}/register",
            json={
                "username": SMOKE_USERNAME,
                "email": SMOKE_EMAIL,
                "password": SMOKE_PASSWORD,
            },
        )
        if r.status_code == 409:
            r = client.post(
                f"{base_url}/login",
                data={"username": SMOKE_USERNAME, "password": SMOKE_PASSWORD},
            )
        r.raise_for_status()
        token = r.json()["access_token"]

        resp = client.post(
            f"{base_url}/attempt",
            json={"task_id": task_id, "submitted_query": expected_query},
            headers={"Authorization": f"Bearer {token}"},
        )

    if resp.status_code != 200:
        raise SystemExit(
            f"🔴 SMOKE PAO: /attempt vratio HTTP {resp.status_code} — živi put je "
            f"pukao (gateway/XMPP/agenti). Tijelo: {resp.text[:300]}"
        )

    fb = resp.json().get("feedback", {})
    if fb.get("is_correct") is not True:
        raise SystemExit(
            f"🔴 SMOKE PAO: referentni upit taska {source_id} NIJE ocijenjen točnim "
            f"kroz živi put (is_correct={fb.get('is_correct')}, "
            f"error_type={fb.get('error_type')}, detail={fb.get('detail')})."
        )

    logger.info(
        "✅ SMOKE OK: /attempt kroz pun agentski lanac → is_correct=True (task %s).",
        source_id,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke živog /attempt puta.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        run_smoke(args.base_url)
    except httpx.HTTPError as exc:
        cleanup(SMOKE_USERNAME)
        print(
            f"🔴 SMOKE PAO: HTTP greška prema {args.base_url} — vrti li backend? {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc
    except SystemExit:
        cleanup(SMOKE_USERNAME)
        raise
    cleanup(SMOKE_USERNAME)


if __name__ == "__main__":
    main()
