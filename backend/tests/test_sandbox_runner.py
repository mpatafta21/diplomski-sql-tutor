"""Testovi za SandboxRunner."""

import pytest

from scripts.lib.sandbox_runner import (
    ExecutionResult,
    SandboxRunner,
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
    actual = runner.execute(
        "SELECT id FROM categories WHERE id IN (1, 2, 3) ORDER BY id;"
    )
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


# ============================================================
# compare() — numerička usporedba (errata 2A, fix 3.0)
#
# Bug: execute() normalizira Decimal→str via _normalize_value, ali
# expected_result iz JSONB dolazi kao Python float. Usporedba str '726.70'
# != float 726.7 davala je lažni mismatch.
# ============================================================


def _fake_runner() -> SandboxRunner:
    """Runner koji se koristi samo za compare() — ne otvara stvarnu konekciju."""
    return SandboxRunner("postgresql://fake:fake@localhost/fake")


def _actual(rows: list[dict]) -> ExecutionResult:
    """Simulira rezultat execute() gdje su Decimal vrijednosti već str."""
    return ExecutionResult(
        success=True,
        rows=rows,
        column_names=list(rows[0].keys()) if rows else [],
        execution_time_ms=1,
    )


# --- padajući testovi na trenutnom kodu (Korak A) ---


def test_compare_float_vs_decimal_str_ordered() -> None:
    """float iz JSONB (72755.21) mora matchati Decimal-as-str ('72755.21') — ORDER BY put."""
    r = _fake_runner()
    actual = _actual(
        [
            {"customer_id": 21, "ukupna_potrosnja": "72755.21"},
            {"customer_id": 13, "ukupna_potrosnja": "67527.47"},
        ]
    )
    expected = [
        {"customer_id": 21, "ukupna_potrosnja": 72755.21},
        {"customer_id": 13, "ukupna_potrosnja": 67527.47},
    ]
    res = r.compare(actual, expected, query="... ORDER BY ...")
    assert res.matches, f"Trebalo matchati ali nije: {res.diff_summary}"


def test_compare_trailing_zero_float_vs_str() -> None:
    """'726.70' (str s trailing zero iz Decimal) mora matchati 726.7 (float iz JSONB)."""
    r = _fake_runner()
    actual = _actual([{"prosjecna_cijena": "726.70"}])
    expected = [{"prosjecna_cijena": 726.7}]
    res = r.compare(actual, expected)
    assert res.matches, f"Trebalo matchati ali nije: {res.diff_summary}"


# --- regresijski testovi (moraju prolaziti i prije i poslije fixa) ---


def test_compare_int_vs_int_regression() -> None:
    """int == int ostaje ispravan."""
    r = _fake_runner()
    actual = _actual([{"broj_proizvoda": 7}])
    expected = [{"broj_proizvoda": 7}]
    res = r.compare(actual, expected)
    assert res.matches


def test_compare_null_vs_null_regression() -> None:
    """None == None ostaje ispravan."""
    r = _fake_runner()
    actual = _actual([{"employee_id": None}])
    expected = [{"employee_id": None}]
    res = r.compare(actual, expected)
    assert res.matches


def test_compare_null_vs_number_no_match() -> None:
    """None vs broj → NE match."""
    r = _fake_runner()
    actual = _actual([{"val": None}])
    expected = [{"val": 5}]
    res = r.compare(actual, expected)
    assert not res.matches


def test_compare_leading_zero_string_guard() -> None:
    """'007' i '7' su oba stringa — NE smiju matchati numerički (zip-code guard)."""
    r = _fake_runner()
    actual = _actual([{"zip_code": "007"}])
    expected = [{"zip_code": "7"}]
    res = r.compare(actual, expected)
    assert not res.matches, "String '007' ne smije numerički matchati '7'"


# ---------------------------------------------------------------------------
# Faza 5.1 (B1) — SQLSTATE se propušta iz psycopg iznimke
# ---------------------------------------------------------------------------


def test_execute_error_carries_sqlstate(runner: SandboxRunner):
    """🔴 `.sqlstate` je JEDINI signal koji `execution_error` smije poslati LLM-u.

    Zatvoren šifrarnik od 5 znakova, bez ijednog studentovog znaka — dok poruka
    pored njega nosi doslovni redak upita (v. docs/faza-5-korak-0.md §A1).
    Do 5.1 se gubio u `str(e)`; ovaj test čuva da se ne izgubi opet.
    """
    res = runner.execute("SELECT id, name, county FROM suppliers LIMIT 3")
    assert res.success is False
    assert res.sqlstate == "42703"  # undefined_column
    # Kod NE smije nositi studentov tekst, poruka smije.
    assert "county" not in res.sqlstate
    assert "county" in (res.error or "")


def test_execute_success_has_no_sqlstate(runner: SandboxRunner):
    res = runner.execute("SELECT 1 AS x")
    assert res.success is True
    assert res.sqlstate is None


def test_execute_grouping_error_sqlstate(runner: SandboxRunner):
    """42803 pogađa `group_by` i `having_filter` — dva od osam top koncepata."""
    res = runner.execute(
        "SELECT category_id, name, COUNT(*) FROM products GROUP BY category_id"
    )
    assert res.success is False
    assert res.sqlstate == "42803"
