"""Pydantic v2 request/response sheme za HTTP gateway.

Auth (Faza 4.0b): zaštićene rute deriviraju user_id iz JWT tokena
(get_current_user), NE iz body/query — klijent ga više ne bira. AttemptRequest
zato više ne nosi user_id.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, EmailStr


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class AttemptRequest(BaseModel):
    # user_id NAMJERNO uklonjen (Faza 4.0b.2) — derivira se iz JWT tokena, klijent ga ne bira.
    task_id: int
    submitted_query: str


# ---------------------------------------------------------------------------
# Auth (Faza 4.0b) — /register, /login, /me
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str


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


# ---------------------------------------------------------------------------
# Statički read endpointi (Faza 4.0a-1) — /task/{id}, /modules, /badges
# ---------------------------------------------------------------------------


class ConceptRef(BaseModel):
    code: str
    name: str
    is_primary: bool


class TaskDetailResponse(BaseModel):
    """Detalj zadatka za studenta. NAMJERNO bez expected_query / expected_result /
    sandbox_schema — rješenje se NE izlaže kroz ovaj endpoint."""

    id: int
    title: str
    description: str
    difficulty: int
    estimated_time_sec: int | None
    module_id: int
    concepts: list[ConceptRef]


class ConceptNode(BaseModel):
    id: int
    code: str
    name: str
    tier: str
    order_index: int
    prerequisites: list[str]


class ModuleNode(BaseModel):
    id: int
    number: int
    name: str
    description: str | None
    difficulty: str
    order_index: int
    concepts: list[ConceptNode]


class BadgeCatalogItem(BaseModel):
    """Katalog bedževa — bez `rule` (Prolog kriterij se ne izlaže klijentu)."""

    code: str
    name: str
    description: str | None
    icon: str | None
    xp_reward: int


# ---------------------------------------------------------------------------
# Paginacijski envelope (Faza 4.0a-2) — generički, reusan (/attempts, /leaderboard, …)
# ---------------------------------------------------------------------------


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# User read endpointi (Faza 4.0a-2) — /attempts, /leaderboard
# ---------------------------------------------------------------------------


class AttemptItem(BaseModel):
    id: int
    task_id: int
    task_title: str
    submitted_query: str
    is_correct: bool
    error_type: str | None
    execution_time_ms: int | None
    rows_returned: int | None
    xp_awarded: int
    hint_requested: bool
    attempt_number: int
    created_at: datetime


class LeaderboardItem(BaseModel):
    """`xp` je score za dani scope (global = User.xp, weekly = SUM(delta) u prozoru).
    `level` je uvijek trenutni User.level."""

    rank: int
    username: str
    xp: int
    level: int


class MasteryHistoryPoint(BaseModel):
    """Jedna točka BKT krivulje (snapshot p_l pri updateu)."""

    concept: str
    p_l: float
    attempt_id: int | None
    created_at: datetime


# ---------------------------------------------------------------------------
# POST /run — čisti sandbox exec (Faza 4.0a-4)
# ---------------------------------------------------------------------------


class RunRequest(BaseModel):
    task_id: int | None = None  # opcionalni kontekst; NE mijenja izvršavanje
    query: str


class RunResponse(BaseModel):
    columns: list[str]
    rows: list[dict]
    exec_ms: int
    error: str | None = None  # None == uspjeh; inače SQL/timeout poruka (nije HTTP greška)


# ---------------------------------------------------------------------------
# GET /admin/agent-logs — FIPA-ACL log (Faza 4.0a-4)
# ---------------------------------------------------------------------------


class AgentLogItem(BaseModel):
    id: int
    sender: str
    receiver: str
    performative: str
    content: dict | None
    correlation_id: str | None
    created_at: datetime
