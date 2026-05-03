"""Testovi za TaskValidator — 3-razinska validacija."""

from unittest.mock import MagicMock

import pytest

from app.schemas.generated_task import GeneratedTask
from scripts.lib.task_validator import (
    TaskValidator,
    ValidationResult,
    ValidationFailure,
)
from scripts.lib.sandbox_runner import ExecutionResult, ComparisonResult
from scripts.lib.ast_analyzer import ConceptDetectionResult


def make_task(**overrides) -> GeneratedTask:
    base = {
        "title": "Naslov zadatka koji ima dovoljno znakova",
        "description": "Opis koji ima minimum 20 znakova teksta jer Pydantic to traži.",
        "primary_concept": "select_basic",
        "secondary_concepts": [],
        "difficulty": 1,
        "estimated_time_sec": 60,
        "expected_query": "SELECT id, name FROM categories ORDER BY id;",
        "expected_result": [{"id": 1, "name": "Foo"}],
    }
    base.update(overrides)
    return GeneratedTask.model_validate(base)


@pytest.fixture
def mock_runner():
    runner = MagicMock()
    runner.execute.return_value = ExecutionResult(
        success=True,
        rows=[{"id": 1, "name": "Foo"}],
        column_names=["id", "name"],
        execution_time_ms=10,
    )
    runner.compare.return_value = ComparisonResult(
        matches=True, diff_summary="OK", actual_count=1, expected_count=1
    )
    return runner


@pytest.fixture
def mock_analyzer():
    analyzer = MagicMock()
    analyzer.detects_concept.return_value = ConceptDetectionResult(
        detected=True, location="top-level SELECT"
    )
    return analyzer


@pytest.fixture
def validator(mock_runner, mock_analyzer) -> TaskValidator:
    return TaskValidator(sandbox_runner=mock_runner, ast_analyzer=mock_analyzer)


def test_valid_task_all_three_pass(validator):
    task = make_task()
    result = validator.validate(task)
    assert result.passed
    assert result.failures == []


def test_syntax_failure_short_circuits(validator, mock_runner, mock_analyzer):
    task = make_task(expected_query="DROP TABLE customers;")
    result = validator.validate(task)
    assert not result.passed
    assert result.failures[0].level == "syntax"
    assert result.failures[0].code == "dangerous_pattern"
    # ostale razine ne smiju biti zvane
    mock_analyzer.detects_concept.assert_not_called()
    mock_runner.execute.assert_not_called()


def test_concept_coverage_failure(validator, mock_analyzer, mock_runner):
    mock_analyzer.detects_concept.return_value = ConceptDetectionResult(
        detected=False, is_in_comment=True
    )
    task = make_task()
    result = validator.validate(task)
    assert not result.passed
    assert result.failures[0].level == "concept_coverage"
    mock_runner.execute.assert_not_called()


def test_result_mismatch_failure(validator, mock_runner):
    mock_runner.compare.return_value = ComparisonResult(
        matches=False,
        diff_summary="Row count mismatch: actual=2 vs expected=1",
        actual_count=2,
        expected_count=1,
    )
    task = make_task()
    result = validator.validate(task)
    assert not result.passed
    assert result.failures[0].level == "result_match"
    assert result.failures[0].details["actual_count"] == 2


def test_execution_error_fails_result_match(validator, mock_runner):
    mock_runner.execute.return_value = ExecutionResult(
        success=False, error="permission denied"
    )
    task = make_task()
    result = validator.validate(task)
    assert not result.passed
    assert result.failures[0].code == "execution_failed"


def test_detector_not_implemented_returns_failure(validator, mock_analyzer):
    mock_analyzer.detects_concept.side_effect = NotImplementedError(
        "Detector for 'totally_fake' not implemented"
    )
    task = make_task(primary_concept="totally_fake")
    result = validator.validate(task)
    assert not result.passed
    assert result.failures[0].code == "detector_not_implemented"


# ============================================================================
# REGRESSION TESTS — code review #2 fixes
# ============================================================================

def test_analyzer_attribute_error_returns_detector_crashed(
    validator, mock_analyzer
):
    """Bilo koja crash u AstAnalyzer-u (osim NotImplementedError) -> failure, ne raise."""
    mock_analyzer.detects_concept.side_effect = AttributeError(
        "'NoneType' object has no attribute 'tokens'"
    )
    task = make_task()
    result = validator.validate(task)
    assert not result.passed
    assert result.failures[0].level == "concept_coverage"
    assert result.failures[0].code == "detector_crashed"
    assert "AttributeError" in result.failures[0].message


def test_runner_crash_returns_runner_crashed(validator, mock_runner):
    mock_runner.execute.side_effect = ConnectionError("DB connection lost")
    task = make_task()
    result = validator.validate(task)
    assert not result.passed
    assert result.failures[0].level == "result_match"
    assert result.failures[0].code == "runner_crashed"


def test_truncate_blocked_by_dangerous_pattern(validator):
    task = make_task(expected_query="TRUNCATE customers;")
    result = validator.validate(task)
    assert not result.passed
    assert result.failures[0].code == "dangerous_pattern"


def test_concept_coverage_failure_promotes_in_comment_to_details(
    validator, mock_analyzer
):
    """is_in_comment / is_in_string moraju biti u details, ne samo u message."""
    mock_analyzer.detects_concept.return_value = ConceptDetectionResult(
        detected=False, is_in_comment=True, is_in_string=False
    )
    task = make_task()
    result = validator.validate(task)
    assert not result.passed
    assert result.failures[0].details["is_in_comment"] is True
    assert result.failures[0].details["is_in_string"] is False


def test_empty_expected_result_passes_when_actual_empty(
    validator, mock_runner
):
    """Task koji očekuje 0 redova prolazi ako sandbox vrati 0 redova."""
    mock_runner.execute.return_value = ExecutionResult(
        success=True, rows=[], column_names=["id"], execution_time_ms=5
    )
    mock_runner.compare.return_value = ComparisonResult(
        matches=True, diff_summary="OK", actual_count=0, expected_count=0
    )
    task = make_task(expected_result=[])
    result = validator.validate(task)
    assert result.passed
