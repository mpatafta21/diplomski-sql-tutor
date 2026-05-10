"""Testovi za meta_gen.py — generiranje concept YAML config-ova kroz tool-use API."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.lib.meta_gen import (
    collect_few_shot_yamls,
    build_meta_gen_prompts,
    parse_and_validate,
    generate_one_yaml,
)
from app.schemas.concept_config import ConceptConfig


MINIMAL_VALID_CONFIG = {
    "concept_code": "test_concept",
    "concept_name": "Test Concept",
    "module_number": 1,
    "module_name": "Test Module",
    "tier": "easy",
    "target_misconceptions": [
        {
            "code": "test_misconception",
            "description": "Test misconception description za SQL koncept.",
            "priority": "high",
        }
    ],
    "domain_hints": ["Test domain hint za sandbox."],
    "anti_patterns": ["Test anti-pattern koji treba izbjegavati."],
    "required_for_high_difficulty": [],
    "few_shot_examples": [
        {
            "difficulty": 2,
            "title": "Test example title za sql",
            "description": "Test example description za SQL upit koji testira concept.",
            "expected_query": "SELECT 1 AS x;",
            "expected_concepts": ["test_concept"],
            "targets_misconception": "test_misconception",
        }
    ],
    "ast_validation_rules": ["Test AST validation rule za concept."],
}

EXAMPLE_META = {
    "module_number": 1,
    "module_name": "Osnove SELECT-a",
    "tier": "easy",
    "description": "Test concept za meta-gen testiranje.",
}


def test_collect_few_shot_yamls(tmp_path: Path):
    """Vraća {stem: raw_text} za sve *.yaml fajlove; ne-YAML fajlovi se ignoriraju."""
    (tmp_path / "alpha.yaml").write_text("concept_code: alpha\n", encoding="utf-8")
    (tmp_path / "beta.yaml").write_text("concept_code: beta\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("not a yaml", encoding="utf-8")

    result = collect_few_shot_yamls(tmp_path)

    assert set(result.keys()) == {"alpha", "beta"}
    assert "concept_code: alpha" in result["alpha"]
    assert "concept_code: beta" in result["beta"]


def test_build_meta_gen_prompts_no_feedback():
    """Vraća (system, user) tuple; user sadrži concept_code, bez schema error info."""
    few_shot = {"inner_join": "concept_code: inner_join\ntier: medium\n"}

    system, user = build_meta_gen_prompts(
        target_concept_code="where_filter",
        target_concept_meta=EXAMPLE_META,
        few_shot_examples=few_shot,
    )

    assert isinstance(system, str) and len(system) > 50
    assert isinstance(user, str) and len(user) > 10
    assert "where_filter" in user
    # Bez schema error feedbacka u user promptu
    assert "schema error" not in user.lower()


def test_build_meta_gen_prompts_with_schema_feedback():
    """schema_error_feedback se pojavljuje u user promptu radi retry guidance."""
    few_shot = {"inner_join": "concept_code: inner_join\n"}
    error_msg = "Schema validation failed: tier must be easy|medium|hard"

    _, user = build_meta_gen_prompts(
        target_concept_code="where_filter",
        target_concept_meta=EXAMPLE_META,
        few_shot_examples=few_shot,
        schema_error_feedback=error_msg,
    )

    assert error_msg in user


def test_parse_and_validate_schema_pass(tmp_path: Path):
    """Validan dict → (ConceptConfig, None); YAML fajl se piše u output_dir."""
    config, err = parse_and_validate(MINIMAL_VALID_CONFIG, tmp_path)

    assert err is None
    assert isinstance(config, ConceptConfig)
    assert config.concept_code == "test_concept"
    assert (tmp_path / "test_concept.yaml").exists()


def test_parse_and_validate_schema_fail_returns_error(tmp_path: Path):
    """Nevalidan dict (nedostaju required field-ovi) → (None, error_str)."""
    bad_config = {"concept_code": "test", "concept_name": "bad concept name"}

    config, err = parse_and_validate(bad_config, tmp_path)

    assert config is None
    assert isinstance(err, str) and len(err) > 0


def test_generate_one_yaml_success_first_try(tmp_path: Path):
    """Happy path: validan response → status=success, attempts=1."""
    client = MagicMock()
    response = MagicMock()
    response.parsed = MINIMAL_VALID_CONFIG
    response.input_tokens = 1000
    response.output_tokens = 500
    response.cached_tokens = 800
    client.generate_structured_output.return_value = response

    result = generate_one_yaml(
        client=client,
        concept_code="test_concept",
        concept_meta=EXAMPLE_META,
        few_shot_examples={"example": "concept_code: example\n"},
        output_dir=tmp_path,
    )

    assert result["status"] == "success"
    assert result["attempts"] == 1
    assert result["concept_code"] == "test_concept"
    assert result["error"] is None
    assert isinstance(result["cost_usd"], float) and result["cost_usd"] >= 0
    client.generate_structured_output.assert_called_once()


def test_generate_one_yaml_retry_on_schema_fail(tmp_path: Path):
    """1. poziv vraca nevalidan dict, 2. validan → attempts=2, status=success."""
    client = MagicMock()

    bad_response = MagicMock()
    bad_response.parsed = {"concept_code": "bad"}  # missing required fields
    bad_response.input_tokens = 1000
    bad_response.output_tokens = 200
    bad_response.cached_tokens = 0

    good_response = MagicMock()
    good_response.parsed = MINIMAL_VALID_CONFIG
    good_response.input_tokens = 1000
    good_response.output_tokens = 500
    good_response.cached_tokens = 800

    client.generate_structured_output.side_effect = [bad_response, good_response]

    result = generate_one_yaml(
        client=client,
        concept_code="test_concept",
        concept_meta=EXAMPLE_META,
        few_shot_examples={"example": "concept_code: example\n"},
        output_dir=tmp_path,
        max_retries=1,
    )

    assert result["status"] == "success"
    assert result["attempts"] == 2
    assert client.generate_structured_output.call_count == 2
    # Drugi poziv mora sadržavati schema error feedback u user_message
    second_kwargs = client.generate_structured_output.call_args_list[1].kwargs
    assert "schema" in second_kwargs["user_message"].lower()


def test_generate_one_yaml_manual_review_after_max_retries(tmp_path: Path):
    """Svi pokušaji fail-aju → status=manual_review, attempts=max_retries+1."""
    client = MagicMock()
    bad_response = MagicMock()
    bad_response.parsed = {"concept_code": "bad"}  # uvijek invalid
    bad_response.input_tokens = 1000
    bad_response.output_tokens = 200
    bad_response.cached_tokens = 0
    client.generate_structured_output.return_value = bad_response

    result = generate_one_yaml(
        client=client,
        concept_code="test_concept",
        concept_meta=EXAMPLE_META,
        few_shot_examples={"example": "concept_code: example\n"},
        output_dir=tmp_path,
        max_retries=1,
    )

    assert result["status"] == "manual_review"
    assert result["attempts"] == 2
    assert result["error"] is not None
    assert client.generate_structured_output.call_count == 2
