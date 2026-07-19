"""Čista evaluacijska jezgra — bez SPADE, bez DB write-ova.

Eksponira:
  EvaluationOutcome  — rezultat evaluacije jednog SQL pokušaja
  evaluate()         — (task, query, runner) → EvaluationOutcome

Taksonomija grešaka (redoslijed provjere):
  syntax_error      — prazan/whitespace upit (sqlparse vrati prazan parse)
  unsupported_eval  — explain_plan / index_usage (plan-presence put nije implementiran)
  execution_error   — runner.execute() success=False (timeout → poseban error_type="timeout")
  correct           — compare().matches == True
  empty_result      — 0 actual redova, > 0 expected
  wrong_columns     — set stupaca se razlikuje (jak signal krivog upita)
  row_mismatch      — stupci OK, redovi krivi → verdict="partial"

NAPOMENA za sqlparse: parser je lenijentan — keyword typo-vi ("SELECT FORM x") prolaze
kroz sintaktičku provjeru i padaju na execution_error. Za robustnu sintaktičku provjeru
treba pg_parse/libpg_query — out of scope za MVP.
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlparse

from app.db.models import Task
from scripts.lib.sandbox_runner import SandboxRunner

# ---------------------------------------------------------------------------
# Domenske konstante — JEDAN izvor istine (dijele ih evaluator, recommender i
# dijagnostičke skripte; NE kopirati popise).
# ---------------------------------------------------------------------------

#: Koncepti koje evaluacijska jezgra NE zna ocijeniti (plan-presence put nije
#: implementiran). Recommender ih MORA preskočiti (inače trajni ćorsokak:
#: neevaluabilan task nikad ne postane `is_correct` → nikad "riješen").
UNSUPPORTED_CONCEPTS = frozenset({"explain_plan", "index_usage"})

#: Koncepti čiji `expected_query` je DML (INSERT/UPDATE/DELETE) → moraju se
#: izvršiti kroz `sandbox_readwrite` rolu u transakciji koja se UVIJEK rollbacka
#: (SandboxRunner.execute(dml=True)). Pod readonly rolom padali bi na
#: "permission denied" i student bi vidio lažno "Greška u SQL-u" (4.4-0c nalaz).
#: Derivacija iz PRIMARNOG koncepta — provjereno na svih 83 taska: identična
#: derivaciji iz SVIH koncepata i 100 % poklapanje sa sqlparse ground truthom.
DML_CONCEPTS = frozenset({"insert", "update", "delete"})


@dataclass
class EvaluationOutcome:
    is_correct: bool
    verdict: str            # "correct" | "partial" | "incorrect"
    error_type: str | None  # taksonomija dolje; None ako correct
    execution_time_ms: int
    rows_returned: int
    detail: str             # kratki opis za log/hint, nije za klasifikaciju


def evaluate(
    task: Task,
    submitted_query: str,
    runner: SandboxRunner,
    primary_concept_code: str | None = None,
) -> EvaluationOutcome:
    """Evaluiraj submitted_query na zadanom tasku.

    Args:
        task: SQLAlchemy Task objekt s expected_result (JSONB lista diktova).
        submitted_query: SQL koji je student predao.
        runner: SandboxRunner spojen na sandbox bazu.
        primary_concept_code: Primarni koncept taska (npr. "explain_plan"). Ako je
            u _UNSUPPORTED_CONCEPTS, vraća unsupported_eval odmah.

    Returns:
        EvaluationOutcome s klasifikacijom i metrikama.
    """

    # ------------------------------------------------------------------
    # 1. Provjera syntax_error (samo očiti slučajevi — empty/whitespace)
    # ------------------------------------------------------------------
    stripped = submitted_query.strip()
    if not sqlparse.parse(stripped):
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="syntax_error",
            execution_time_ms=0,
            rows_returned=0,
            detail="Prazan ili neprepoznatljiv upit",
        )

    # ------------------------------------------------------------------
    # 2. Unsupported eval (explain_plan / index_usage)
    #    TODO: Implementirati plan-presence put (3A ili 3C)
    # ------------------------------------------------------------------
    if primary_concept_code in UNSUPPORTED_CONCEPTS:
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="unsupported_eval",
            execution_time_ms=0,
            rows_returned=0,
            detail=(
                f"Koncept '{primary_concept_code}' zahtijeva plan-presence evaluaciju "
                "koja još nije implementirana."
            ),
        )

    # ------------------------------------------------------------------
    # 3. Izvršavanje u sandboxu
    # ------------------------------------------------------------------
    # DML taskovi (M4) MORAJU ići kroz readwrite rolu + transakciju s ROLLBACK-om;
    # SELECT ostaje readonly. Bez ovoga svaki INSERT/UPDATE/DELETE pada na
    # "permission denied" (execution_error) — 9/83 taskova bilo je neocjenjivo.
    is_dml = primary_concept_code in DML_CONCEPTS
    result = runner.execute(
        submitted_query, schema=task.sandbox_schema, dml=is_dml
    )

    if not result.success:
        if "Statement timeout" in (result.error or ""):
            error_type = "timeout"
        else:
            error_type = "execution_error"
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type=error_type,
            execution_time_ms=result.execution_time_ms,
            rows_returned=0,
            detail=result.error or "",
        )

    # ------------------------------------------------------------------
    # 4. Rubni slučaj: expected_result prazan
    # ------------------------------------------------------------------
    expected: list[dict] = task.expected_result or []

    if not expected:
        if not result.rows:
            return EvaluationOutcome(
                is_correct=True,
                verdict="correct",
                error_type=None,
                execution_time_ms=result.execution_time_ms,
                rows_returned=0,
                detail="OK",
            )
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="row_mismatch",
            execution_time_ms=result.execution_time_ms,
            rows_returned=len(result.rows),
            detail=f"Očekivano 0 redova, dobiveno {len(result.rows)}",
        )

    # ------------------------------------------------------------------
    # 5. Usporedba rezultata (runner.compare već normalizira Decimal/datetime)
    # ------------------------------------------------------------------
    cmp = runner.compare(result, expected, query=submitted_query)

    if cmp.matches:
        return EvaluationOutcome(
            is_correct=True,
            verdict="correct",
            error_type=None,
            execution_time_ms=result.execution_time_ms,
            rows_returned=len(result.rows),
            detail="OK",
        )

    # ------------------------------------------------------------------
    # 6. Klasifikacija neuspjeha — STRUKTURNO (ne parsiraj diff_summary)
    # ------------------------------------------------------------------

    # 6a. Prazan rezultat (0 redova, a expected ima ≥1)
    if not result.rows:
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="empty_result",
            execution_time_ms=result.execution_time_ms,
            rows_returned=0,
            detail=f"Prazan rezultat, očekivano {len(expected)} redova",
        )

    # 6b. Krivi stupci → incorrect (jak signal pogrešnog pristupa)
    actual_cols = set(result.column_names)
    expected_cols = set(expected[0].keys())

    if actual_cols != expected_cols:
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="wrong_columns",
            execution_time_ms=result.execution_time_ms,
            rows_returned=len(result.rows),
            detail=(
                f"Stupci se razlikuju — dobiveni: {sorted(actual_cols)}, "
                f"očekivani: {sorted(expected_cols)}"
            ),
        )

    # 6c. Stupci OK, redovi krivi → partial
    return EvaluationOutcome(
        is_correct=False,
        verdict="partial",
        error_type="row_mismatch",
        execution_time_ms=result.execution_time_ms,
        rows_returned=len(result.rows),
        detail=cmp.diff_summary,
    )
