"""TDD testovi za agents/evaluation.py — čista evaluacijska jezgra (bez SPADE/XMPP).

Testovi koriste STVARNE seedane taskove iz tutor_main baze i sandbox_runner fixture.
Pokretanje: uv run pytest tests/test_evaluation.py -v
"""

from __future__ import annotations

import pytest

from agents.evaluation import EvaluationOutcome, evaluate, plan_is_stable
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
# explain_plan / index_usage → plan-presence evaluacija (ERRATA #66)
#
# 🔴 Do 2026-08-14 oba su koncepta vraćala `unsupported_eval` bez izvršavanja.
# Sada se ocjenjuju usporedbom izvedbenog plana; logika je u
# `tests/test_evaluation_plan.py`, ovdje ostaje samo veza na STVARNE zadatke
# kataloga — jer su upravo oni bili kriv dio nalaza.
# ---------------------------------------------------------------------------


def test_ispravan_M6_zadatak_prolazi_kroz_plan_provjeru(db_session, sandbox_runner):
    """`index_usage_d3_41c8280e` (task 81) referentno rješenje daje Bitmap Index Scan."""
    task = _task(db_session, "index_usage_d3_41c8280e")
    outcome = evaluate(
        task, task.expected_query, sandbox_runner, primary_concept_code="index_usage"
    )

    assert outcome.is_correct is True
    assert outcome.error_type is None


@pytest.mark.parametrize(
    "source_id",
    [
        "explain_plan_d3_60b9eaee",  # task 79
        "explain_plan_d4_54c05243",  # task 80
        "index_usage_d4_68049f11",  # task 82
    ],
)
def test_zateceni_pokvareni_M6_zadaci_padaju_na_gateu_stabilnosti(
    source_id, db_session, sandbox_runner
):
    """🔴 Tri zadatka koja su srušila izvornu pretpostavku (ERRATA #66).

    Svi gađaju `customers` (200 redaka), gdje planer bira Seq Scan iako indeks
    postoji — pa referentno rješenje ne radi ono što opis zadatka tvrdi.

    🔴 **Tvrdi se STABILNOST, ne konkretan ishod `evaluate()`.** Prva verzija
    ovog testa tvrdila je da anti-pattern prolazi kao točan; prošla je izolirano
    a pala u punoj datoteci, jer se plan za `customers` prebacuje na mrtve retke
    iz rollbackanog DML-a drugog testa. Tvrdnja o ishodu bila bi time i sama
    flaky — a upravo je ta nestabilnost razlog zašto zadatak ne valja.
    """
    task = _task(db_session, source_id)
    assert task.is_active is False, f"{source_id} ne smije biti aktivan (ERRATA #66)"

    stabilan, razlog = plan_is_stable(
        task.expected_query, sandbox_runner, schema=task.sandbox_schema
    )

    assert stabilan is False, (
        f"{source_id} bi prošao gate — ako je zadatak popravljen, ispravi i ovaj test"
    )
    assert razlog


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


# ---------------------------------------------------------------------------
# DML put (M4) — Faza 4.4-0d
#
# 🔴 Ova klasa NIKAD prije nije bila pokrivena (nalaz 4.4-0c A4): evaluacijska
# jezgra je hardkodirala dml=False pa je SVAKI INSERT/UPDATE/DELETE task padao
# na "permission denied" (execution_error) — 9/83 taskova bilo je neocjenjivo,
# a student bi vidio lažno "Greška u SQL-u".
# ---------------------------------------------------------------------------


def test_dml_insert_task_is_correct(db_session, sandbox_runner):
    """INSERT task s primary_concept='insert' → readwrite rola → is_correct."""
    task = _task(db_session, "insert_d2_bc637919")
    outcome = evaluate(
        task, task.expected_query, sandbox_runner, primary_concept_code="insert"
    )

    assert outcome.is_correct is True, f"INSERT nije ocijenjen točnim: {outcome.detail}"
    assert outcome.verdict == "correct"
    assert outcome.error_type is None


def test_dml_update_task_is_correct(db_session, sandbox_runner):
    """UPDATE task s primary_concept='update' → readwrite rola → is_correct."""
    task = _task(db_session, "update_d2_b0b659e4")
    outcome = evaluate(
        task, task.expected_query, sandbox_runner, primary_concept_code="update"
    )

    assert outcome.is_correct is True, f"UPDATE nije ocijenjen točnim: {outcome.detail}"
    assert outcome.verdict == "correct"
    assert outcome.error_type is None


def test_dml_delete_task_is_correct(db_session, sandbox_runner):
    """DELETE task s primary_concept='delete' → readwrite rola → is_correct."""
    task = _task(db_session, "delete_d2_9b0f6b74")
    outcome = evaluate(
        task, task.expected_query, sandbox_runner, primary_concept_code="delete"
    )

    assert outcome.is_correct is True, f"DELETE nije ocijenjen točnim: {outcome.detail}"
    assert outcome.verdict == "correct"
    assert outcome.error_type is None


def test_dml_evaluation_rolls_back_sandbox(db_session, sandbox_runner):
    """🔴 ROLLBACK INVARIJANTA: nakon evaluacije DELETE taska sandbox je NEPROMIJENJEN.

    Task `delete_d2_9b0f6b74` je `DELETE FROM orders WHERE id = 2 RETURNING ...`.
    Da rollback ne radi, sandbox bi se TRAJNO zagadio za sve studente — zato se
    tvrde konkretne brojke, ne samo "nema greške".
    """

    def _count(sql: str) -> int:
        res = sandbox_runner.execute(sql)
        assert res.success, f"kontrolni upit pao: {res.error}"
        return res.rows[0]["c"]

    before_total = _count("SELECT COUNT(*) AS c FROM orders;")
    before_row = _count("SELECT COUNT(*) AS c FROM orders WHERE id = 2;")
    assert before_row == 1, "preduvjet: order id=2 mora postojati prije testa"

    task = _task(db_session, "delete_d2_9b0f6b74")
    outcome = evaluate(
        task, task.expected_query, sandbox_runner, primary_concept_code="delete"
    )
    assert outcome.is_correct is True

    assert _count("SELECT COUNT(*) AS c FROM orders;") == before_total, (
        "broj redaka u orders se promijenio — DML NIJE rollbackan"
    )
    assert _count("SELECT COUNT(*) AS c FROM orders WHERE id = 2;") == 1, (
        "order id=2 je nestao — DML NIJE rollbackan, sandbox je trajno zagađen"
    )


def test_non_dml_concept_still_runs_readonly(db_session, sandbox_runner):
    """Regresija: koncept koji NIJE u DML_CONCEPTS ostaje na readonly roli.

    Dokaz je jak: DML upit poslan na SELECT-task mora pasti na 'permission
    denied' — da je rola readwrite, upit bi prošao.
    """
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    outcome = evaluate(
        task,
        "DELETE FROM orders WHERE id = 999999;",
        sandbox_runner,
        primary_concept_code="agg_sum_avg",
    )

    assert outcome.is_correct is False
    assert outcome.error_type == "execution_error"
    assert "permission denied" in (outcome.detail or "").lower(), (
        f"očekivan permission denied pod readonly rolom, dobiveno: {outcome.detail}"
    )


# ---------------------------------------------------------------------------
# Faza 5.1 (B1) — sqlstate na EvaluationOutcome
# ---------------------------------------------------------------------------


def test_execution_error_outcome_carries_sqlstate(db_session, sandbox_runner):
    """`execution_error` nosi SQLSTATE — jedini signal koji taj tip smije poslati LLM-u.

    🔴 `detail` ONDJE nosi doslovni redak studentovog upita (mjereno, §A1), pa je
    izbačen iz bijele liste. Bez `sqlstate` bi hint za `execution_error` mogao reći
    samo „baza je odbila upit", što student već vidi.
    """
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    outcome = evaluate(task, "SELECT nepostojeci_stupac FROM products", sandbox_runner)

    assert outcome.error_type == "execution_error"
    assert outcome.sqlstate == "42703"
    # Šifra je zatvoren skup i NE nosi studentov tekst; `detail` ga nosi.
    assert "nepostojeci_stupac" not in outcome.sqlstate
    assert "nepostojeci_stupac" in outcome.detail


def test_correct_outcome_has_no_sqlstate(db_session, sandbox_runner):
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")
    outcome = evaluate(task, task.expected_query, sandbox_runner)
    assert outcome.is_correct is True
    assert outcome.sqlstate is None


def test_non_execution_failures_have_no_sqlstate(db_session, sandbox_runner):
    """Sintaktički i rezultatski promašaji nemaju SQLSTATE — baza ih nije odbila."""
    task = _task(db_session, "agg_sum_avg_d3_manual_f239bc99")

    prazan = evaluate(task, "   ", sandbox_runner)
    assert prazan.error_type == "syntax_error"
    assert prazan.sqlstate is None

    krivi = evaluate(task, "SELECT 1 AS bogus_kolona", sandbox_runner)
    assert krivi.error_type in ("wrong_columns", "row_mismatch")
    assert krivi.sqlstate is None
