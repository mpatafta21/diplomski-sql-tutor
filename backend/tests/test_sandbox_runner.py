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


# ============================================================
# DML path (dml=True) — Korak 1 iz 2B-1B
# ============================================================

def test_execute_dml_insert_rollbacks(runner: SandboxRunner):
    """INSERT s dml=True succeeds ali se rollback-a — red ne perzistira."""
    result = runner.execute(
        "INSERT INTO categories (name, description) VALUES ('__dml_rollback_test__', 'tmp') RETURNING id;",
        dml=True,
    )
    assert result.success, f"DML INSERT failed: {result.error}"
    assert len(result.rows) == 1, "RETURNING should return inserted row"

    # Rollback verification — row must not exist
    check = runner.execute(
        "SELECT COUNT(*) AS cnt FROM categories WHERE name = '__dml_rollback_test__';"
    )
    assert check.success
    assert check.rows[0]["cnt"] == 0, "DML INSERT was not rolled back"


def test_execute_dml_update_rollbacks(runner: SandboxRunner):
    """UPDATE s dml=True se rollback-a — originalni podaci neizmijenjeni."""
    before = runner.execute("SELECT name FROM categories WHERE id = 1;")
    original_name = before.rows[0]["name"]

    result = runner.execute(
        "UPDATE categories SET name = '__dml_update_test__' WHERE id = 1 RETURNING name;",
        dml=True,
    )
    assert result.success, f"DML UPDATE failed: {result.error}"
    assert result.rows[0]["name"] == "__dml_update_test__"

    # Rollback verification
    after = runner.execute("SELECT name FROM categories WHERE id = 1;")
    assert after.rows[0]["name"] == original_name, "DML UPDATE was not rolled back"


def test_execute_dml_error_returns_failure(runner: SandboxRunner):
    """DML s greškom (unique violation) vraća ExecutionResult(success=False)."""
    result = runner.execute(
        "INSERT INTO categories (id, name, description) VALUES (1, 'dup', 'dup');",
        dml=True,
    )
    assert not result.success
    assert result.error is not None


def test_execute_dml_select_readable_via_readwrite_role(runner: SandboxRunner):
    """SELECT s dml=True (readwrite role) i dalje vraća podatke."""
    result = runner.execute("SELECT COUNT(*) AS cnt FROM categories;", dml=True)
    assert result.success
    assert result.rows[0]["cnt"] == 15


def test_execute_default_dml_false_blocks_insert(runner: SandboxRunner):
    """Regression: default execute() bez dml=True i dalje blokira DML."""
    result = runner.execute(
        "INSERT INTO categories (name, description) VALUES ('regr', 'x');"
    )
    assert not result.success
    assert "permission" in result.error.lower() or "denied" in result.error.lower()


def test_execute_dml_no_returning_returns_empty_rows(runner: SandboxRunner):
    """DML bez RETURNING vraća success=True ali rows=[]."""
    result = runner.execute(
        "UPDATE categories SET description = description WHERE id = 999;",
        dml=True,
    )
    assert result.success
    assert result.rows == []
