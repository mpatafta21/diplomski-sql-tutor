"""
Testovi za ConceptConfig Pydantic schema i load_concept_config helper.

TDD red-green-refactor po faza-2b-1a-plan.md §4.
"""

import pytest
from pathlib import Path

from pydantic import ValidationError

from app.schemas.concept_config import ConceptConfig, ConceptConfigError, load_concept_config


CONCEPTS_DIR = Path(__file__).parent.parent / "config" / "concepts"


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def minimal_valid_config() -> dict:
    """Minimalan validan dict za happy path test."""
    return {
        "concept_code": "test_concept",
        "concept_name": "Test Concept",
        "module_number": 1,
        "module_name": "Test Module",
        "tier": "easy",
        "target_misconceptions": [
            {
                "code": "test_misconception",
                "description": "A test misconception for validation testing",
                "priority": "high",
            }
        ],
        "domain_hints": ["Test hint 1"],
        "anti_patterns": ["Test anti-pattern 1"],
        "required_for_high_difficulty": [],
        "few_shot_examples": [
            {
                "difficulty": 1,
                "title": "Test example",
                "description": "Test description for example",
                "expected_query": "SELECT 1 AS x;",
                "expected_concepts": ["test_concept"],
                "targets_misconception": "test_misconception",
            }
        ],
        "ast_validation_rules": ["Mock validation rule"],
    }


# ============================================================
# Test 1 — Happy path (minimal valid config)
# ============================================================

def test_minimal_valid_config_loads(minimal_valid_config):
    config = ConceptConfig.model_validate(minimal_valid_config)
    assert config.concept_code == "test_concept"
    assert config.tier == "easy"
    assert len(config.target_misconceptions) == 1
    assert len(config.few_shot_examples) == 1


# ============================================================
# Tests 2-4 — Backward compat: existing production YAMLs
# ============================================================

def test_select_basic_yaml_loads():
    config = load_concept_config(CONCEPTS_DIR / "select_basic.yaml")
    assert config.concept_code == "select_basic"
    assert config.tier == "easy"


def test_inner_join_yaml_loads():
    config = load_concept_config(CONCEPTS_DIR / "inner_join.yaml")
    assert config.concept_code == "inner_join"
    assert config.tier == "medium"


def test_left_join_yaml_loads():
    config = load_concept_config(CONCEPTS_DIR / "left_join.yaml")
    assert config.concept_code == "left_join"
    assert config.tier == "hard"


# ============================================================
# Tests 5-15 — Negative / validation error cases
# ============================================================

def test_missing_concept_code_raises(minimal_valid_config):
    del minimal_valid_config["concept_code"]
    with pytest.raises(ValidationError):
        ConceptConfig.model_validate(minimal_valid_config)


def test_invalid_tier_raises(minimal_valid_config):
    minimal_valid_config["tier"] = "extreme"
    with pytest.raises(ValidationError):
        ConceptConfig.model_validate(minimal_valid_config)


def test_invalid_module_number_raises(minimal_valid_config):
    minimal_valid_config["module_number"] = 7
    with pytest.raises(ValidationError):
        ConceptConfig.model_validate(minimal_valid_config)


def test_invalid_concept_code_pattern_raises(minimal_valid_config):
    minimal_valid_config["concept_code"] = "InnerJoin"
    with pytest.raises(ValidationError):
        ConceptConfig.model_validate(minimal_valid_config)


def test_extra_field_raises(minimal_valid_config):
    """Typo 'target_misconception' (singular) should fail with extra='forbid'."""
    minimal_valid_config["target_misconception"] = []
    with pytest.raises(ValidationError):
        ConceptConfig.model_validate(minimal_valid_config)


def test_empty_misconceptions_raises(minimal_valid_config):
    minimal_valid_config["target_misconceptions"] = []
    with pytest.raises(ValidationError):
        ConceptConfig.model_validate(minimal_valid_config)


def test_duplicate_misconception_codes_raises(minimal_valid_config):
    minimal_valid_config["target_misconceptions"] = [
        {"code": "same_code", "description": "First misconception description here", "priority": "high"},
        {"code": "same_code", "description": "Second misconception description here", "priority": "low"},
    ]
    with pytest.raises(ValidationError, match="same_code"):
        ConceptConfig.model_validate(minimal_valid_config)


def test_invalid_priority_raises(minimal_valid_config):
    minimal_valid_config["target_misconceptions"][0]["priority"] = "hi"
    with pytest.raises(ValidationError):
        ConceptConfig.model_validate(minimal_valid_config)


def test_few_shot_difficulty_out_of_range_raises(minimal_valid_config):
    minimal_valid_config["few_shot_examples"][0]["difficulty"] = 6
    with pytest.raises(ValidationError):
        ConceptConfig.model_validate(minimal_valid_config)


def test_load_nonexistent_file_raises():
    with pytest.raises(FileNotFoundError):
        load_concept_config(CONCEPTS_DIR / "nonexistent_concept.yaml")


def test_load_yaml_list_raises(tmp_path):
    """YAML that is a list instead of a dict should raise ConceptConfigError."""
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text("- item1\n- item2\n")
    with pytest.raises(ConceptConfigError):
        load_concept_config(yaml_file)


# ============================================================
# Test 16 — Integration: all production YAMLs pass schema
# ============================================================

def test_all_concept_yamls_validate():
    """Regression net: svi production YAML-ovi prolaze schema."""
    yaml_files = list(CONCEPTS_DIR.glob("*.yaml"))
    assert len(yaml_files) >= 3, f"Expected ≥3 concept YAMLs, found {len(yaml_files)}"

    for yaml_path in yaml_files:
        try:
            config = load_concept_config(yaml_path)
            assert config.concept_code, f"Empty concept_code in {yaml_path.name}"
        except ConceptConfigError as e:
            pytest.fail(f"{yaml_path.name} failed schema validation: {e}")
