"""Sweep integriteta zadataka (Faza 4.4-0b, KORAK 1) — READ-ONLY dijagnostika.

Pokreni iz ``backend/``::

    uv run python -m scripts.sweep_task_integrity            # tablica + JSON sažetak
    uv run python -m scripts.sweep_task_integrity --json     # samo JSON
    uv run python -m scripts.sweep_task_integrity --deep 5   # + duboka usporedba za N padova

INVARIJANTA KOJU TESTIRA: referentni upit (``tasks.expected_query``) MORA na
vlastitom tasku dati ``is_correct=True``. Svaki drugi ishod znači pokvaren task
(referenca ne reproducira ``expected_result``).

🔴 NE POPRAVLJA NIŠTA. Ne piše u bazu, ne stvara attempte, ne dira agente:
koristi ČISTU evaluacijsku jezgru ``agents.evaluation.evaluate`` — ISTI put
kojim ide studentov upit (ista taksonomija grešaka, ista ``runner.compare``
normalizacija) — samo bez perzistencije.

NAPOMENA: koncepti ``explain_plan``/``index_usage`` (modul 6) po dizajnu vraćaju
``unsupported_eval`` (plan-presence evaluacija nije implementirana) — to NISU
pokvareni taskovi i izvještaj ih broji odvojeno.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.evaluation import evaluate
from agents.evaluator_agent import _sandbox_conn_string
from app.db.models import Concept, Module, Task, TaskConcept
from app.db.session import SessionLocal
from scripts.lib.sandbox_runner import SandboxRunner

# Vraćaju unsupported_eval po dizajnu (agents/evaluation.py::_UNSUPPORTED_CONCEPTS).
_BY_DESIGN_UNSUPPORTED = frozenset({"explain_plan", "index_usage"})


@dataclass
class TaskRow:
    task_id: int
    title: str
    difficulty: int
    module_number: int
    primary_concept: str | None
    is_correct: bool
    error_type: str | None
    detail: str
    rows_returned: int


def _load_tasks(session: Session) -> list[tuple[Task, str | None, int]]:
    """(Task, primary_concept_code, module_number) za SVE aktivne taskove, po id-u."""
    tasks = (
        session.execute(select(Task).where(Task.is_active.is_(True)).order_by(Task.id))
        .scalars()
        .all()
    )
    primary = dict(
        session.execute(
            select(TaskConcept.task_id, Concept.code)
            .join(Concept, Concept.id == TaskConcept.concept_id)
            .where(TaskConcept.is_primary.is_(True))
        ).all()
    )
    modules = dict(session.execute(select(Module.id, Module.number)).all())
    return [(t, primary.get(t.id), modules.get(t.module_id, -1)) for t in tasks]


def run_sweep() -> list[TaskRow]:
    runner = SandboxRunner(_sandbox_conn_string())
    out: list[TaskRow] = []
    with SessionLocal() as session:
        for task, primary, module_number in _load_tasks(session):
            outcome = evaluate(task, task.expected_query, runner, primary)
            out.append(
                TaskRow(
                    task_id=task.id,
                    title=task.title,
                    difficulty=task.difficulty,
                    module_number=module_number,
                    primary_concept=primary,
                    is_correct=outcome.is_correct,
                    error_type=outcome.error_type,
                    detail=outcome.detail,
                    rows_returned=outcome.rows_returned,
                )
            )
    return out


def deep_compare(task_id: int) -> dict:
    """DOSLOVNA usporedba: expected_query rezultat vs expected_result."""
    runner = SandboxRunner(_sandbox_conn_string())
    with SessionLocal() as session:
        task = session.get(Task, task_id)
        if task is None:
            return {"task_id": task_id, "error": "task not found"}
        res = runner.execute(task.expected_query, schema=task.sandbox_schema, dml=False)
        expected: list[dict] = task.expected_result or []
        return {
            "task_id": task_id,
            "title": task.title,
            "expected_query": task.expected_query,
            "exec_success": res.success,
            "exec_error": res.error,
            "actual_row_count": len(res.rows),
            "expected_row_count": len(expected),
            "actual_columns": sorted(res.column_names),
            "expected_columns": sorted(expected[0].keys()) if expected else [],
            "actual_first3": res.rows[:3],
            "expected_first3": expected[:3],
        }


def _summarize(rows: list[TaskRow]) -> dict:
    failures = [r for r in rows if not r.is_correct]
    by_design = [
        r for r in failures if (r.primary_concept or "") in _BY_DESIGN_UNSUPPORTED
    ]
    genuine = [r for r in failures if r not in by_design]
    return {
        "total_active_tasks": len(rows),
        "passing": len(rows) - len(failures),
        "failing_total": len(failures),
        "failing_by_design_unsupported": len(by_design),
        "failing_genuine": len(genuine),
        "failing_by_error_type": dict(Counter(r.error_type or "?" for r in failures)),
        "genuine_by_error_type": dict(Counter(r.error_type or "?" for r in genuine)),
        "genuine_by_difficulty": dict(Counter(r.difficulty for r in genuine)),
        "genuine_difficulty_4_5": sum(1 for r in genuine if r.difficulty >= 4),
        "genuine_by_module": dict(Counter(r.module_number for r in genuine)),
        "genuine_task_ids": [r.task_id for r in genuine],
    }


def _print_table(rows: list[TaskRow]) -> None:
    failures = [r for r in rows if not r.is_correct]
    print(f"\n{'=' * 100}")
    print("SWEEP INTEGRITETA ZADATAKA — referentni upit na vlastitom tasku")
    print(f"{'=' * 100}")
    print(f"Aktivnih taskova: {len(rows)} | PROLAZI: {len(rows) - len(failures)} | PADA: {len(failures)}")
    if not failures:
        print("\nSvi referentni upiti reproduciraju expected_result. ✓")
        return
    print(f"\n{'id':>4}  {'mod':>3}  {'dif':>3}  {'error_type':<18}  {'primary_concept':<22}  title")
    print("-" * 100)
    for r in sorted(failures, key=lambda x: (x.error_type or "", x.task_id)):
        print(
            f"{r.task_id:>4}  {r.module_number:>3}  {r.difficulty:>3}  "
            f"{(r.error_type or '?'):<18}  {(r.primary_concept or '-'):<22}  {r.title[:40]}"
        )
    print("\nDETALJI padova:")
    for r in sorted(failures, key=lambda x: (x.error_type or "", x.task_id)):
        print(f"  [{r.task_id}] {r.error_type}: {r.detail[:160]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only sweep integriteta taskova.")
    parser.add_argument("--json", action="store_true", help="samo JSON sažetak")
    parser.add_argument("--deep", type=int, default=0, help="duboka usporedba za N prvih padova")
    args = parser.parse_args()

    rows = run_sweep()
    summary = _summarize(rows)

    if not args.json:
        _print_table(rows)

    if args.deep:
        genuine_ids = summary["genuine_task_ids"][: args.deep]
        print(f"\n{'=' * 100}\nDUBOKA USPOREDBA (prvih {len(genuine_ids)} stvarnih padova)\n{'=' * 100}")
        for tid in genuine_ids:
            d = deep_compare(tid)
            print(json.dumps(d, ensure_ascii=False, indent=2, default=str))

    print("\n--- JSON SAŽETAK ---")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
