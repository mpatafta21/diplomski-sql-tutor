"""Testovi za SandboxRunner."""

import pytest

from scripts.lib.sandbox_runner import (
    SandboxRunner,
    ExecutionResult,
    ComparisonResult,
)


@pytest.fixture
def runner(sandbox_connection_string: str) -> SandboxRunner:
    return SandboxRunner(connection_string=sandbox_connection_string, timeout_seconds=5)


def test_execute_returns_15_categories(runner: SandboxRunner):
    result = runner.execute("SELECT id, name FROM categories ORDER BY id;")
    assert result.success
    assert len(result.rows) == 15
    assert result.column_names == ["id", "name"]
    assert result.error is None


def test_execute_timeout_returns_error(runner: SandboxRunner):
    result = runner.execute("SELECT pg_sleep(10);")
    assert not result.success
    assert "timeout" in result.error.lower()


def test_execute_insert_blocked_by_readonly_role(runner: SandboxRunner):
    result = runner.execute(
        "INSERT INTO categories (name, description) VALUES ('hack', 'should fail');"
    )
    assert not result.success
    assert "permission" in result.error.lower() or "denied" in result.error.lower()


def test_compare_identical_results_match(runner: SandboxRunner):
    actual = runner.execute("SELECT id FROM categories WHERE id IN (1, 2, 3) ORDER BY id;")
    expected = [{"id": 1}, {"id": 2}, {"id": 3}]
    result = runner.compare(actual, expected, query="SELECT ... ORDER BY id")
    assert result.matches
    assert result.diff_summary == "OK"


def test_compare_different_row_counts_fail(runner: SandboxRunner):
    actual = runner.execute("SELECT id FROM categories WHERE id IN (1, 2) ORDER BY id;")
    expected = [{"id": 1}, {"id": 2}, {"id": 3}]
    result = runner.compare(actual, expected, query="ORDER BY")
    assert not result.matches
    assert "Row count mismatch" in result.diff_summary


def test_compare_unordered_set_match(runner: SandboxRunner):
    actual = runner.execute("SELECT id FROM categories WHERE id IN (3, 1, 2);")
    expected = [{"id": 1}, {"id": 2}, {"id": 3}]
    result = runner.compare(actual, expected, order_matters=False)
    assert result.matches


def test_compare_handles_null_values(runner: SandboxRunner):
    actual = runner.execute(
        "SELECT id, employee_id FROM orders WHERE employee_id IS NULL ORDER BY id LIMIT 2;"
    )
    assert actual.success
    assert all(r["employee_id"] is None for r in actual.rows)
