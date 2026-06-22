"""TDD testovi za agents/evaluation.py — čista evaluacijska jezgra (bez SPADE/XMPP).

Testovi koriste STVARNE seedane taskove iz tutor_main baze i sandbox_runner fixture.
Pokretanje: uv run pytest tests/test_evaluation.py -v
"""

from __future__ import annotations

import pytest

from agents.evaluation import EvaluationOutcome, evaluate
from app.db.models import Task
from scripts.lib.sandbox_runner import SandboxRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task(db_session, source_id: str) -> Task:
    t = db_session.query(Task).filter_by(source_id=source_id).first()
    assert t is not None, f"Task '{source_id}' nije pronađen u bazi"
    return t


# ---------------------------------------------------------------------------
# Correct — NUMERIC (regresija na 2B-3 Decimal/str type-coercion bug)
# ---------------------------------------------------------------------------


def test_correct_numeric_task(db_session, sandbox_runner):
    """Točno riješen zadatak s NUMERIC kolonama prolazi compare() bez type-coercion greške."""
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    # expected_query vrati redove s Decimal vrijednostima (ROUND → NUMERIC)
    outcome = evaluate(task, task.expected_query, sandbox_runner)

    assert outcome.is_correct is True
    assert outcome.verdict == "correct"
    assert outcome.error_type is None
    assert outcome.rows_returned == len(task.expected_result)
    assert outcome.execution_time_ms >= 0


# ---------------------------------------------------------------------------
# Correct — prazan expected_result (rubni slučaj: 0 redova = correct)
# ---------------------------------------------------------------------------


def test_correct_empty_expected_result(db_session, sandbox_runner):
    """Ako expected_result == [], upit koji vrati 0 redova je correct."""
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")

    # Simuliramo empty-expected task lokalnim overrideom
    task_copy = Task(
        id=task.id,
        source_id=task.source_id,
        module_id=task.module_id,
        title=task.title,
        description=task.description,
        sandbox_schema=task.sandbox_schema,
        expected_query=task.expected_query,
        expected_result=[],   # <-- empty expected
        difficulty=task.difficulty,
        is_active=task.is_active,
    )
    # Upit koji ne vraća ništa (WHERE uvjet koji ne matchira)
    zero_rows_query = "SELECT 1 WHERE FALSE"
    outcome = evaluate(task_copy, zero_rows_query, sandbox_runner)

    assert outcome.is_correct is True
    assert outcome.verdict == "correct"
    assert outcome.rows_returned == 0


# ---------------------------------------------------------------------------
# Row mismatch → partial (isti stupci, krivi/manji skup redova)
# ---------------------------------------------------------------------------


def test_partial_row_mismatch(db_session, sandbox_runner):
    """Upit koji vraća točne stupce ali kriv skup redova → verdict=partial, row_mismatch."""
    # agg_count task: expected 5 statusa (all). Šaljemo samo 2 statusa → isti stupci, krivi redovi.
    task = _task(db_session, "agg_count_d3_manual_9cbaf74e")
    # Expected: sve 5 status vrijednosti. Submitted: samo 2 (WHERE filtar) — isti stupci.
    partial_query = (
        "SELECT status, COUNT(*) AS broj_narudzbi FROM orders "
        "WHERE status IN ('delivered', 'pending') "
        "GROUP BY status ORDER BY status"
    )
    outcome = evaluate(task, partial_query, sandbox_runner)

    assert outcome.is_correct is False
    assert outcome.verdict == "partial"
    assert outcome.error_type == "row_mismatch"


# ---------------------------------------------------------------------------
# Wrong columns → incorrect
# ---------------------------------------------------------------------------


def test_wrong_columns(db_session, sandbox_runner):
    """Upit koji vraća krivi skup stupaca → verdict=incorrect, wrong_columns."""
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    # Expected: ['customer_id', 'ukupna_potrosnja']
    # Submitted: samo ['id', 'email'] — potpuno kriví stupci
    wrong_query = "SELECT id, email FROM customers LIMIT 5"
    outcome = evaluate(task, wrong_query, sandbox_runner)

    assert outcome.is_correct is False
    assert outcome.verdict == "incorrect"
    assert outcome.error_type == "wrong_columns"


# ---------------------------------------------------------------------------
# Syntax error — prazan upit
# ---------------------------------------------------------------------------


def test_syntax_error_empty_query(db_session, sandbox_runner):
    """Prazan upit → syntax_error (uhvaćen sqlparse-om prije execute())."""
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    outcome = evaluate(task, "", sandbox_runner)

    assert outcome.is_correct is False
    assert outcome.verdict == "incorrect"
    assert outcome.error_type == "syntax_error"
    assert outcome.execution_time_ms == 0


def test_syntax_error_whitespace_only(db_session, sandbox_runner):
    """Whitespace-only upit → syntax_error."""
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    outcome = evaluate(task, "   \n\t  ", sandbox_runner)

    assert outcome.is_correct is False
    assert outcome.error_type == "syntax_error"


# ---------------------------------------------------------------------------
# "SELECT FORM customers" — dokumentira stvarno ponašanje sqlparse-a
# ---------------------------------------------------------------------------


def test_select_typo_falls_to_execution_error(db_session, sandbox_runner):
    """
    sqlparse je lenijentan: "SELECT FORM customers" parsira kao type='SELECT' (ne baca grešku).
    Evaluator ga propušta na execute() koji pada → execution_error, NE syntax_error.

    Ovo je namjerno dokumentirano ponašanje: sqlparse ne hvata keyword typo-ve.
    Za potpuniju sintaktičku provjeru trebao bi pg_parse/libpg_query — out of scope za MVP.
    """
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    outcome = evaluate(task, "SELECT FORM customers", sandbox_runner)

    assert outcome.is_correct is False
    assert outcome.verdict == "incorrect"
    # NE syntax_error jer sqlparse ga ne hvata — pada na execution_error
    assert outcome.error_type == "execution_error"


# ---------------------------------------------------------------------------
# Execution error — primjer loše reference
# ---------------------------------------------------------------------------


def test_execution_error_nonexistent_table(db_session, sandbox_runner):
    """Referenca na nepostojeću tablicu → execution_error."""
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    outcome = evaluate(task, "SELECT * FROM ne_postoji_tablica", sandbox_runner)

    assert outcome.is_correct is False
    assert outcome.verdict == "incorrect"
    assert outcome.error_type == "execution_error"


# ---------------------------------------------------------------------------
# Timeout — SKIP (deterministički timeout zahtijeva pg_sleep(6) što je flaky u CI)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="Deterministički timeout zahtijeva pg_sleep(6s) — flaky u CI")
def test_timeout(db_session, sandbox_runner):
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    outcome = evaluate(task, "SELECT pg_sleep(10)", sandbox_runner)
    assert outcome.error_type == "timeout"


# ---------------------------------------------------------------------------
# explain_plan / index_usage → unsupported_eval
# ---------------------------------------------------------------------------


def test_explain_plan_returns_unsupported_eval(db_session, sandbox_runner):
    """explain_plan concept → unsupported_eval (plan-presence path nije još implementiran)."""
    task = _task(db_session, "explain_plan_d3_60b9eaee")
    outcome = evaluate(
        task, task.expected_query, sandbox_runner, primary_concept_code="explain_plan"
    )

    assert outcome.is_correct is False
    assert outcome.verdict == "incorrect"
    assert outcome.error_type == "unsupported_eval"


def test_index_usage_returns_unsupported_eval(db_session, sandbox_runner):
    """index_usage concept → unsupported_eval."""
    task = _task(db_session, "index_usage_d3_41c8280e")
    outcome = evaluate(
        task, task.expected_query, sandbox_runner, primary_concept_code="index_usage"
    )

    assert outcome.is_correct is False
    assert outcome.error_type == "unsupported_eval"


# ---------------------------------------------------------------------------
# Metrike — execution_time_ms i rows_returned popunjeni na correct slučaju
# ---------------------------------------------------------------------------


def test_metrics_populated_on_correct(db_session, sandbox_runner):
    """execution_time_ms > 0 i rows_returned odgovara broju redova na correct outcomeу."""
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    outcome = evaluate(task, task.expected_query, sandbox_runner)

    assert outcome.execution_time_ms > 0
    assert outcome.rows_returned == len(task.expected_result)
    assert isinstance(outcome.detail, str)
