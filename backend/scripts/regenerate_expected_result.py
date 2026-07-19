"""Regeneracija `tasks.expected_result` iz živog sandboxa (Faza 4.4-0e, KORAK 4).

Pokreni iz ``backend/``::

    uv run python -m scripts.regenerate_expected_result --task-id 25
    uv run python -m scripts.regenerate_expected_result --task-id 25 --task-id 29 --sync-dataset
    uv run python -m scripts.regenerate_expected_result --task-id 25 --dry-run

Čemu služi: `expected_result` je SNIMKA rezultata koja zastarijeva kad se sandbox
reseeda. Od 4.4-0e seed je determinističan (fiksni `SEED_BASE_DATE`), pa je ovo
alat za JEDNOKRATNO usklađivanje zapisa koji su zaostali iz doba wall-clock seeda.

🔴 GUARD (4.4-0e §4b) — rezultat se upisuje SAMO ako upit:
   1. izvrši BEZ greške, i
   2. vrati ≥ 1 redak.
Prazan rezultat se NIKAD ne upisuje: time bi se pokvaren task zacementirao kao
"točan" (referentni upit bi trivijalno prolazio protiv praznog očekivanja).

DML taskovi: izvršavaju se kroz `sandbox_readwrite` uz ROLLBACK (isti put kao
evaluacija, `DML_CONCEPTS`) — RETURNING redci su legitiman expected_result.

`--sync-dataset` uz DB upisuje i u `data/generated_tasks/final_dataset.json`
(po `source_id`) — bez toga bi sljedeći `scripts.import_dataset` vratio staru
snimku i poništio popravak.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.evaluation import DML_CONCEPTS
from agents.evaluator_agent import _sandbox_conn_string
from app.db.models import Concept, Task, TaskConcept
from app.db.session import SessionLocal
from scripts.lib.sandbox_runner import SandboxRunner

logger = logging.getLogger("regenerate_expected_result")

DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "generated_tasks"
    / "final_dataset.json"
)


def _primary_concept(session: Session, task_id: int) -> str | None:
    return session.scalar(
        select(Concept.code)
        .join(TaskConcept, TaskConcept.concept_id == Concept.id)
        .where(TaskConcept.task_id == task_id, TaskConcept.is_primary.is_(True))
    )


def regenerate(
    session: Session,
    runner: SandboxRunner,
    task_id: int,
    *,
    dry_run: bool = False,
) -> list[dict] | None:
    """Vrati nove retke ako su prošli guard (i upiše ih), inače None."""
    task = session.get(Task, task_id)
    if task is None:
        logger.error("task %s ne postoji", task_id)
        return None

    primary = _primary_concept(session, task_id)
    is_dml = primary in DML_CONCEPTS
    result = runner.execute(
        task.expected_query, schema=task.sandbox_schema, dml=is_dml
    )

    # GUARD 1 — izvršavanje mora uspjeti
    if not result.success:
        logger.error(
            "task %s: upit NIJE uspio (%s) — ODBIJAM upis", task_id, result.error
        )
        return None

    # GUARD 2 — prazan rezultat se NE upisuje
    if not result.rows:
        logger.error(
            "task %s: upit vratio 0 redaka — ODBIJAM upis (prazno očekivanje bi "
            "pokvaren task učinilo trivijalno 'točnim')",
            task_id,
        )
        return None

    old_n = len(task.expected_result or [])
    logger.info(
        "task %s (%s, dml=%s): %d -> %d redaka",
        task_id,
        task.source_id,
        is_dml,
        old_n,
        len(result.rows),
    )
    if dry_run:
        logger.info("  --dry-run: ništa nije upisano")
        return result.rows

    task.expected_result = result.rows
    session.commit()
    return result.rows


def sync_dataset(updates: dict[str, list[dict]]) -> int:
    """Upiši nove expected_result u final_dataset.json po source_id. Vrati broj izmjena."""
    if not DATASET_PATH.exists():
        logger.warning("dataset nije pronađen: %s — preskačem sync", DATASET_PATH)
        return 0
    data = json.loads(DATASET_PATH.read_text())
    changed = 0
    for entry in data.get("tasks", []):
        rows = updates.get(entry.get("task_id"))
        if rows is not None:
            entry["expected_result"] = rows
            changed += 1
    if changed:
        DATASET_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        )
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regeneriraj tasks.expected_result iz živog sandboxa."
    )
    parser.add_argument(
        "--task-id", type=int, action="append", required=True,
        help="ID taska (može se ponoviti)",
    )
    parser.add_argument(
        "--sync-dataset", action="store_true",
        help="upiši i u final_dataset.json (inače ga sljedeći import prepiše)",
    )
    parser.add_argument("--dry-run", action="store_true", help="samo ispiši, ne upisuj")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    runner = SandboxRunner(_sandbox_conn_string())

    updates: dict[str, list[dict]] = {}
    failed: list[int] = []
    with SessionLocal() as session:
        for task_id in args.task_id:
            rows = regenerate(session, runner, task_id, dry_run=args.dry_run)
            if rows is None:
                failed.append(task_id)
                continue
            task = session.get(Task, task_id)
            if task is not None and task.source_id:
                updates[task.source_id] = rows

    if args.sync_dataset and not args.dry_run and updates:
        n = sync_dataset(updates)
        logger.info("final_dataset.json: ažurirano %d zapisa", n)

    if failed:
        logger.error("Guard odbio %d task(ova): %s", len(failed), failed)
        raise SystemExit(1)
    logger.info("Gotovo: %d task(ova) regenerirano.", len(updates))


if __name__ == "__main__":
    main()
