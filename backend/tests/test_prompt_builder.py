"""Testovi za PromptBuilder."""

from pathlib import Path

import pytest

from scripts.lib.prompt_builder import (
    PromptBuilder,
    PromptPair,
    ConceptNotFoundError,
)


@pytest.fixture
def builder() -> PromptBuilder:
    backend_root = Path(__file__).resolve().parent.parent
    return PromptBuilder(
        concepts_config_dir=backend_root / "config" / "concepts",
        sandbox_context_path=backend_root / "config" / "sandbox_context.yaml",
        templates_dir=backend_root / "config" / "prompt_templates",
    )


def test_build_returns_non_empty_pair(builder: PromptBuilder):
    pair = builder.build("inner_join", difficulty=2)
    assert isinstance(pair, PromptPair)
    assert len(pair.system) > 500
    assert len(pair.user) > 200


def test_system_contains_schema_and_invariants(builder: PromptBuilder):
    pair = builder.build("inner_join", difficulty=2)
    assert "ANTI-HALLUCINATION" in pair.system
    assert "categories" in pair.system
    assert "25 kupaca" in pair.system or "25 customers" in pair.system


def test_user_contains_misconceptions(builder: PromptBuilder):
    pair = builder.build("inner_join", difficulty=2)
    assert "missing_join_condition" in pair.user
    assert "wrong_join_keys" in pair.user


def test_difficulty_4_adds_high_difficulty_block(builder: PromptBuilder):
    pair = builder.build("left_join", difficulty=4)
    assert "Dodatni zahtjevi" in pair.user


def test_difficulty_2_omits_high_difficulty_block(builder: PromptBuilder):
    pair = builder.build("left_join", difficulty=2)
    assert "Dodatni zahtjevi" not in pair.user


def test_few_shot_examples_rendered(builder: PromptBuilder):
    pair = builder.build("left_join", difficulty=4)
    assert "Kupci bez ijedne narudžbe" in pair.user


def test_unknown_concept_raises(builder: PromptBuilder):
    with pytest.raises(ConceptNotFoundError):
        builder.build("nonexistent_concept", difficulty=2)


def test_difficulty_out_of_range_raises(builder: PromptBuilder):
    with pytest.raises(ValueError):
        builder.build("inner_join", difficulty=0)
    with pytest.raises(ValueError):
        builder.build("inner_join", difficulty=6)


def test_system_contains_sample_rows(builder: PromptBuilder):
    """Sample rows iz sandbox-a moraju biti u system prompt-u (anti-halucinacija)."""
    pair = builder.build("inner_join", difficulty=2)
    # Konkretne vrijednosti iz Faker seed=42
    assert "Electronics" in pair.system
    assert "Keller PLC" in pair.system
    assert "Leon" in pair.system
    assert "Drniš" in pair.system  # Croatian city — UTF-8 sanity
