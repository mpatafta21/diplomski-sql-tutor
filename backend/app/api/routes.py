"""HTTP rute gatewaya (Faza 3E.3).

Tok /attempt: HTTP → bridge.register(cid,future) → gateway šalje submit-attempt
Coordinatoru → FSM → attempt-response natrag na gateway → bridge.resolve → HTTP.

/next-task: lakši put — gateway šalje recommend-next IZRAVNO Recommenderu (sender-based
reply već radi, 3C), bez punog FSM-a. Ne gradi se drugi FSM.

/profile: ČISTI DB read (users + skill_mastery + user_badges), bez agenata/bridgea —
kroz to_thread (sync SQLAlchemy ne smije blokirati event loop).
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import select

from agents.coordinator import ERROR_EVALUATION_TIMEOUT, ONTOLOGY_SUBMIT_ATTEMPT
from agents.messages import Ontology
from app.api.schemas import (
    AttemptRequest,
    AttemptResponse,
    NextTaskResponse,
    ProfileResponse,
)
from app.core import config
from app.db.models import Badge, Concept, SkillMastery, User, UserBadge
from app.db.session import SessionLocal

_log = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Mapiranje Coordinator payloada → AttemptResponse
# ---------------------------------------------------------------------------


def _to_attempt_response(result: dict) -> AttemptResponse:
    feedback = result.get("feedback") or {}
    gam = result.get("gamification") or {}
    rec = result.get("recommendation") or {}
    return AttemptResponse(
        feedback={
            "is_correct": feedback.get("is_correct"),
            "error_type": feedback.get("error_type"),
        },
        xp_delta=int(gam.get("xp_delta") or 0),
        xp=int(gam.get("xp") or 0),
        level=int(gam.get("level") or 1),
        current_streak=int(gam.get("current_streak") or 0),
        new_badges=list(gam.get("new_badges") or []),
        recommendation={
            "task_id": rec.get("task_id"),
            "concept": rec.get("concept"),
            "reason": rec.get("reason"),
        },
    )


# ---------------------------------------------------------------------------
# POST /attempt — puni orkestrirani FSM tok
# ---------------------------------------------------------------------------


@router.post("/attempt", response_model=AttemptResponse)
async def post_attempt(req: AttemptRequest, request: Request) -> AttemptResponse:
    bridge = request.app.state.bridge
    gateway = request.app.state.gateway

    cid, _future = bridge.register()
    gateway.send_fipa(
        to=config.AGENT_COORDINATOR_JID,
        ontology=ONTOLOGY_SUBMIT_ATTEMPT,
        payload=req.model_dump(),
        cid=cid,
    )

    try:
        result = await bridge.wait(cid, timeout=config.GATEWAY_TIMEOUT)
    except (asyncio.TimeoutError, TimeoutError):
        # Coordinator se uopće nije javio u zadanom prozoru.
        raise HTTPException(status_code=504, detail="orchestration_timeout")

    # Coordinatorov definiran timeout-odgovor (UPDATE timeout) → 504 sa strukturom.
    if isinstance(result, dict) and result.get("error") == ERROR_EVALUATION_TIMEOUT:
        raise HTTPException(status_code=504, detail=ERROR_EVALUATION_TIMEOUT)

    return _to_attempt_response(result)


# ---------------------------------------------------------------------------
# GET /next-task — izravan recommend-next kroz bridge (bez FSM-a)
# ---------------------------------------------------------------------------


@router.get("/next-task", response_model=NextTaskResponse)
async def get_next_task(request: Request, user_id: int = Query(...)) -> NextTaskResponse:
    bridge = request.app.state.bridge
    gateway = request.app.state.gateway

    cid, _future = bridge.register()
    gateway.send_fipa(
        to=config.AGENT_RECOMMENDER_JID,
        ontology=Ontology.RECOMMEND_NEXT,
        payload={"user_id": user_id},
        cid=cid,
    )

    try:
        result = await bridge.wait(cid, timeout=config.GATEWAY_TIMEOUT)
    except (asyncio.TimeoutError, TimeoutError):
        raise HTTPException(status_code=504, detail="recommender_timeout")

    return NextTaskResponse(
        task_id=result.get("task_id"),
        concept=result.get("concept"),
        reason=result.get("reason"),
    )


# ---------------------------------------------------------------------------
# GET /profile — čisti DB read (bez agenata)
# ---------------------------------------------------------------------------


def _read_profile(user_id: int) -> dict | None:
    """Sinkroni DB read profila — pozvan kroz to_thread."""
    with SessionLocal() as session:
        user = session.get(User, user_id)
        if user is None:
            return None

        mastery_rows = session.execute(
            select(Concept.code, SkillMastery.p_l)
            .join(SkillMastery, SkillMastery.concept_id == Concept.id)
            .where(SkillMastery.user_id == user_id)
            .order_by(Concept.code)
        ).all()

        badge_rows = session.execute(
            select(Badge.code)
            .join(UserBadge, UserBadge.badge_id == Badge.id)
            .where(UserBadge.user_id == user_id)
            .order_by(Badge.code)
        ).scalars()

        return {
            "xp": user.xp,
            "level": user.level,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "mastery": [{"concept": code, "p_l": p_l} for code, p_l in mastery_rows],
            "badges": list(badge_rows),
        }


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user_id: int = Query(...)) -> ProfileResponse:
    data = await asyncio.to_thread(_read_profile, user_id)
    if data is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return ProfileResponse(**data)
