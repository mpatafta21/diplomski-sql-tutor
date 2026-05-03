"""Testovi za GeneratedTask Pydantic schemu."""

import pytest
from pydantic import ValidationError

from app.schemas.generated_task import GeneratedTask, GeneratedTaskMeta


def test_valid_minimal_task_parses():
    """Validan minimalni task uspješno parse-a."""
    payload = {
        "title": "Pronađi sve kupce iz Hrvatske",
        "description": "Ispiši id, first_name, last_name svih kupaca čija je country = 'Croatia'.",
        "primary_concept": "where_filter",
        "secondary_concepts": ["select_basic"],
        "difficulty": 2,
        "estimated_time_sec": 120,
        "sandbox_schema": "ecommerce_v1",
        "expected_query": "SELECT id, first_name, last_name FROM customers WHERE country = 'Croatia';",
        "expected_result": [{"id": 1, "first_name": "Ana", "last_name": "Horvat"}],
    }
    task = GeneratedTask.model_validate(payload)
    assert task.primary_concept == "where_filter"
    assert task.difficulty == 2
    assert task.targets_misconception is None


def test_title_too_short_raises():
    payload = {
        "title": "Kratko",
        "description": "Validan opis koji ima minimum 20 znakova teksta.",
        "primary_concept": "select_basic",
        "difficulty": 1,
        "estimated_time_sec": 60,
        "expected_query": "SELECT id FROM categories;",
        "expected_result": [],
    }
    with pytest.raises(ValidationError, match="at least 10"):
        GeneratedTask.model_validate(payload)


def test_difficulty_out_of_range_raises():
    payload = {
        "title": "Validan naslov zadatka X",
        "description": "Validan opis koji ima minimum 20 znakova teksta.",
        "primary_concept": "select_basic",
        "difficulty": 6,
        "estimated_time_sec": 60,
        "expected_query": "SELECT id FROM categories;",
        "expected_result": [],
    }
    with pytest.raises(ValidationError):
        GeneratedTask.model_validate(payload)


def test_secondary_concepts_max_2():
    payload = {
        "title": "Validan naslov zadatka X",
        "description": "Validan opis koji ima minimum 20 znakova teksta.",
        "primary_concept": "select_basic",
        "secondary_concepts": ["a", "b", "c"],
        "difficulty": 1,
        "estimated_time_sec": 60,
        "expected_query": "SELECT id FROM categories;",
        "expected_result": [],
    }
    with pytest.raises(ValidationError):
        GeneratedTask.model_validate(payload)


def test_invalid_sandbox_schema_raises():
    payload = {
        "title": "Validan naslov zadatka X",
        "description": "Validan opis koji ima minimum 20 znakova teksta.",
        "primary_concept": "select_basic",
        "difficulty": 1,
        "estimated_time_sec": 60,
        "sandbox_schema": "ecommerce_v2",
        "expected_query": "SELECT id FROM categories;",
        "expected_result": [],
    }
    with pytest.raises(ValidationError):
        GeneratedTask.model_validate(payload)


def test_meta_wraps_task():
    task = GeneratedTask.model_validate({
        "title": "Validan naslov zadatka X",
        "description": "Validan opis koji ima minimum 20 znakova teksta.",
        "primary_concept": "select_basic",
        "difficulty": 1,
        "estimated_time_sec": 60,
        "expected_query": "SELECT id FROM categories;",
        "expected_result": [],
    })
    meta = GeneratedTaskMeta(
        task=task,
        generation_id="abc-123",
        api_input_tokens=100,
        api_output_tokens=200,
        api_cached_tokens=0,
        retries=0,
        validation_passed=True,
        validation_failures=[],
        generated_at="2026-05-04T12:00:00Z",
        model_used="claude-sonnet-4-6",
        extended_thinking=False,
    )
    assert meta.task.primary_concept == "select_basic"
    assert meta.retries == 0
