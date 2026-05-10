"""
Pydantic schema za concept YAML config-ove (backend/config/concepts/*.yaml).

Validira strukturu, tipove i required keys za sve concept config-ove
prije nego što idu u prompt builder ili meta-generation pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


# ============================================================
# Nested models
# ============================================================

class Misconception(BaseModel):
    """Jedna ciljana zabluda (target_misconception) za koncept."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=3, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(min_length=10, max_length=300)
    priority: Literal["critical", "high", "medium", "low"]


class FewShotExample(BaseModel):
    """Jedan few-shot primjer zadatka koji se ubacuje u user prompt."""

    model_config = ConfigDict(extra="forbid")

    difficulty: int = Field(ge=1, le=5)
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10)
    expected_query: str = Field(min_length=10)
    expected_concepts: list[str] = Field(min_length=1)
    targets_misconception: str = Field(min_length=3)


# ============================================================
# Top-level model
# ============================================================

class ConceptConfig(BaseModel):
    """Schema za jedan concept YAML config (backend/config/concepts/<code>.yaml)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    concept_code: str = Field(min_length=3, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    concept_name: str = Field(min_length=3, max_length=100)
    module_number: int = Field(ge=0, le=6)
    module_name: str = Field(min_length=3, max_length=100)
    tier: Literal["easy", "medium", "hard"]

    target_misconceptions: list[Misconception] = Field(min_length=1)
    domain_hints: list[str] = Field(min_length=1)
    anti_patterns: list[str] = Field(min_length=1)
    required_for_high_difficulty: list[str] = Field(default_factory=list)
    few_shot_examples: list[FewShotExample] = Field(min_length=1)
    ast_validation_rules: list[str] = Field(min_length=1)

    @field_validator("target_misconceptions")
    @classmethod
    def _unique_misconception_codes(cls, v: list[Misconception]) -> list[Misconception]:
        # min_length=1 je enforced na Field razini — ova provjera hvata duplikate
        codes = [m.code for m in v]
        seen: set[str] = set()
        duplicates = sorted({c for c in codes if c in seen or seen.add(c)})  # type: ignore[func-returns-value]
        if duplicates:
            raise ValueError(
                f"target_misconceptions sadrži duplikate u 'code' polju: {duplicates}"
            )
        return v


# ============================================================
# Loader helper
# ============================================================

class ConceptConfigError(Exception):
    """Raised when YAML doesn't conform to ConceptConfig schema."""


def load_concept_config(path: Path) -> ConceptConfig:
    """
    Učitava i validira concept YAML kroz ConceptConfig schemu.

    Raises:
        FileNotFoundError: Ako YAML fajl ne postoji.
        ConceptConfigError: Ako YAML ne prolazi schema validaciju.
    """
    if not path.exists():
        raise FileNotFoundError(f"Concept config not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConceptConfigError(
            f"Concept config {path.name} mora biti YAML mapping (dict), "
            f"a ne {type(raw).__name__}"
        )

    try:
        return ConceptConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConceptConfigError(
            f"Validation failed for {path.name}: {exc}"
        ) from exc
