"""Pydantic schemas za output Anthropic generatora SQL zadataka."""

from typing import Literal

from pydantic import BaseModel, Field


class GeneratedTask(BaseModel):
    """Output schema za jedan generirani SQL zadatak."""

    title: str = Field(..., min_length=10, max_length=255)
    description: str = Field(..., min_length=20, max_length=2000)

    primary_concept: str
    secondary_concepts: list[str] = Field(default_factory=list, max_length=2)

    difficulty: int = Field(..., ge=1, le=5)
    estimated_time_sec: int = Field(..., ge=30, le=600)

    sandbox_schema: Literal["ecommerce_v1"] = "ecommerce_v1"
    expected_query: str = Field(..., min_length=10)
    expected_result: list[dict]

    targets_misconception: str | None = None
    pedagogical_notes: str | None = None


class GeneratedTaskMeta(BaseModel):
    """Metapodaci o generaciji (dodaje generator, ne LLM)."""

    task: GeneratedTask
    generation_id: str
    api_input_tokens: int
    api_output_tokens: int
    api_cached_tokens: int
    retries: int
    validation_passed: bool
    validation_failures: list[dict]
    generated_at: str
    model_used: str
    extended_thinking: bool
    generation_method: str = "llm"  # "llm" (default) ili "manual" (group_by × 5 u 2B-2)
