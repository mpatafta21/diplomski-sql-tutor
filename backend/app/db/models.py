"""SQLAlchemy modeli za glavnu bazu (tutor_main).

Izvor: docs/faza-1-domenski-model.md §6.2 DDL.
Sve check-constraint-e, indekse i FK-ove definiramo eksplicitno
kako bi Alembic autogenerate mogao rekreirati točan DDL.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ============================================================
# USERS
# ============================================================
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("xp >= 0", name="ck_users_xp_nonneg"),
        CheckConstraint("level >= 1", name="ck_users_level_min"),
        CheckConstraint("current_streak >= 0", name="ck_users_cstreak_nonneg"),
        CheckConstraint("longest_streak >= 0", name="ck_users_lstreak_nonneg"),
        CheckConstraint("role IN ('student', 'admin')", name="ck_users_role"),
        Index("idx_users_xp_desc", "xp"),  # leaderboard; DESC se može dodati u migraciji
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student", server_default="student")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================
# MODULES
# ============================================================
class Module(Base):
    __tablename__ = "modules"
    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced', 'expert', 'cross_module')",
            name="ck_modules_difficulty",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)


# ============================================================
# CONCEPTS
# ============================================================
class Concept(Base):
    __tablename__ = "concepts"
    __table_args__ = (
        CheckConstraint("tier IN ('easy', 'medium', 'hard')", name="ck_concepts_tier"),
        Index("idx_concepts_module", "module_id"),
        Index("idx_concepts_code", "code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), nullable=False)
    tier: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)


# ============================================================
# CONCEPT_PREREQUISITES (M:N self-ref)
# ============================================================
class ConceptPrerequisite(Base):
    __tablename__ = "concept_prerequisites"
    __table_args__ = (
        CheckConstraint("concept_id != prerequisite_id", name="ck_concept_prereq_self"),
    )

    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True
    )
    prerequisite_id: Mapped[int] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True
    )


# ============================================================
# TASKS
# ============================================================
class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 5", name="ck_tasks_difficulty"),
        Index("idx_tasks_module", "module_id"),
        Index("idx_tasks_difficulty", "difficulty"),
        Index("idx_tasks_active", "is_active", postgresql_where="is_active = TRUE"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sandbox_schema: Mapped[str] = mapped_column(String(100), nullable=False)
    expected_query: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_time_sec: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================
# TASK_CONCEPTS (M:N sa is_primary)
# ============================================================
class TaskConcept(Base):
    __tablename__ = "task_concepts"
    __table_args__ = (
        Index("idx_task_concepts_concept", "concept_id"),
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


# ============================================================
# ATTEMPTS
# ============================================================
class Attempt(Base):
    __tablename__ = "attempts"
    __table_args__ = (
        CheckConstraint("attempt_number >= 1", name="ck_attempts_num_min"),
        Index("idx_attempts_user_task", "user_id", "task_id"),
        Index("idx_attempts_user_created", "user_id", "created_at"),
        Index(
            "idx_attempts_error_type", "error_type",
            postgresql_where="error_type IS NOT NULL",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    submitted_query: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_type: Mapped[str | None] = mapped_column(String(100))
    execution_time_ms: Mapped[int | None] = mapped_column(Integer)
    rows_returned: Mapped[int | None] = mapped_column(Integer)
    xp_awarded: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    hint_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================
# SKILL_MASTERY (BKT stanje)
# ============================================================
class SkillMastery(Base):
    __tablename__ = "skill_mastery"
    __table_args__ = (
        CheckConstraint("p_l BETWEEN 0 AND 1", name="ck_sm_p_l"),
        CheckConstraint("p_t BETWEEN 0 AND 1", name="ck_sm_p_t"),
        CheckConstraint("p_g BETWEEN 0 AND 1", name="ck_sm_p_g"),
        CheckConstraint("p_s BETWEEN 0 AND 1", name="ck_sm_p_s"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), primary_key=True)
    p_l: Mapped[float] = mapped_column(Float, nullable=False, default=0.15, server_default="0.15")
    p_t: Mapped[float] = mapped_column(Float, nullable=False, default=0.20, server_default="0.20")
    p_g: Mapped[float] = mapped_column(Float, nullable=False, default=0.20, server_default="0.20")
    p_s: Mapped[float] = mapped_column(Float, nullable=False, default=0.10, server_default="0.10")
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================
# MISCONCEPTIONS
# ============================================================
class Misconception(Base):
    __tablename__ = "misconceptions"
    __table_args__ = (
        UniqueConstraint("user_id", "code", name="uq_misconceptions_user_code"),
        Index("idx_misconceptions_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    occurrences: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================
# BADGES
# ============================================================
class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(50))
    rule: Mapped[str] = mapped_column(Text, nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


# ============================================================
# USER_BADGES
# ============================================================
class UserBadge(Base):
    __tablename__ = "user_badges"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id"), primary_key=True)
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================
# XP_LOG
# ============================================================
class XpLog(Base):
    __tablename__ = "xp_log"
    __table_args__ = (
        Index("idx_xp_log_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    attempt_id: Mapped[int | None] = mapped_column(ForeignKey("attempts.id"))
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================
# STREAKS
# ============================================================
class Streak(Base):
    __tablename__ = "streaks"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")


# ============================================================
# HINTS
# ============================================================
class Hint(Base):
    __tablename__ = "hints"
    __table_args__ = (
        CheckConstraint("difficulty_min BETWEEN 1 AND 5", name="ck_hints_diffmin"),
        CheckConstraint("difficulty_max BETWEEN 1 AND 5", name="ck_hints_diffmax"),
        Index("idx_hints_error_concept", "error_type", "concept_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id"))
    hint_text: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_min: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    difficulty_max: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="hr", server_default="hr")


# ============================================================
# RECOMMENDATIONS_LOG
# ============================================================
class RecommendationLog(Base):
    __tablename__ = "recommendations_log"
    __table_args__ = (
        Index("idx_recommendations_user", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    recommended_task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    reasoning: Mapped[dict] = mapped_column(JSONB, nullable=False)
    accepted: Mapped[bool | None] = mapped_column(Boolean)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================
# AGENT_MESSAGES_LOG (FIPA-ACL log)
# ============================================================
class AgentMessageLog(Base):
    __tablename__ = "agent_messages_log"
    __table_args__ = (
        Index("idx_agent_messages_correlation", "correlation_id"),
        Index("idx_agent_messages_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sender: Mapped[str] = mapped_column(String(50), nullable=False)
    receiver: Mapped[str] = mapped_column(String(50), nullable=False)
    performative: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[dict | None] = mapped_column(JSONB)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
