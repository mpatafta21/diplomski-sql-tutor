"""Pydantic v2 request/response sheme za HTTP gateway (Faza 3E.3).

MVP napomena: rute primaju user_id u bodyju/queryju (BEZ auth/session). Produkcija
treba autentikaciju (Faza 3F+) — user_id se tada izvodi iz tokena, ne iz klijenta.
"""

from __future__ import annotations

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class AttemptRequest(BaseModel):
    user_id: int
    task_id: int
    submitted_query: str


# ---------------------------------------------------------------------------
# Zajedničke pod-sheme
# ---------------------------------------------------------------------------


class FeedbackModel(BaseModel):
    is_correct: bool | None = None
    error_type: str | None = None


class RecommendationModel(BaseModel):
    task_id: int | None = None
    concept: str | None = None
    reason: str | None = None


class MasteryItem(BaseModel):
    concept: str
    p_l: float


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class AttemptResponse(BaseModel):
    feedback: FeedbackModel
    xp_delta: int
    xp: int
    level: int
    current_streak: int
    new_badges: list[str]
    recommendation: RecommendationModel


class NextTaskResponse(BaseModel):
    task_id: int | None = None
    concept: str | None = None
    reason: str | None = None


class ProfileResponse(BaseModel):
    xp: int
    level: int
    current_streak: int
    longest_streak: int
    mastery: list[MasteryItem]
    badges: list[str]
