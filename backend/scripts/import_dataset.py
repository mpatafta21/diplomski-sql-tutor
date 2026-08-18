"""Import final_dataset.json → tasks + task_concepts.

Pokreni iz backend/ direktorija:
    uv run python -m scripts.import_dataset

Idempotentan: ON CONFLICT ON CONSTRAINT uq_tasks_source_id DO UPDATE.
Nepoznati primary_concept → hard-fail taska (skuplja u errors, na kraju ne-nula exit).
Nepoznati secondary_concepts → tiho preskakanje uz warning log.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import Concept, Module, Task, TaskConcept
from app.db.session import SessionLocal

logger = logging.getLogger("import_dataset")

DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "generated_tasks"
    / "final_dataset.json"
)


@dataclass
class ImportResult:
    processed: int = 0
    errors: list[str] = field(default_factory=list)
    skipped_secondary_codes: set[str] = field(default_factory=set)


def _parse_is_active(task_data: dict) -> bool:
    """`is_active` iz dataseta → bool, FAIL-CLOSED na nepoznatoj vrijednosti.

    🔴 Prihvaća samo `bool` i doslovne niske "true"/"false". Ranija verzija je
    radila `str(v).lower() == "true"`, pa bi svaka nepoznata vrijednost (broj 1,
    "yes", None) tiho značila NEAKTIVAN — zadatak bi nestao iz kataloga bez
    ijedne poruke. Nedostajuće polje znači AKTIVAN (zatečeni unosi ga nemaju).
    """
    raw = task_data.get("is_active", True)
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str) and raw.strip().lower() in {"true", "false"}:
        return raw.strip().lower() == "true"
    raise ValueError(
        f"{task_data.get('task_id')}: nevaljan is_active={raw!r} "
        "(dopušteno: bool ili \"true\"/\"false\")"
    )


def _build_module_map(session: Session) -> dict[int, int]:
    """Vraća mapu module.number → module.id iz DB-a (čitanje, bez seedanja)."""
    rows = session.execute(select(Module.number, Module.id)).all()
    return {number: id_ for number, id_ in rows}


def _build_concept_map(session: Session) -> dict[str, int]:
    """Vraća mapu concept.code → concept.id iz DB-a."""
    rows = session.execute(select(Concept.code, Concept.id)).all()
    return {code: id_ for code, id_ in rows}


def import_tasks(session: Session, tasks: list[dict]) -> ImportResult:
    """Importira listu task dict-ova u DB.

    Caller je odgovoran za commit (ili rollback u slučaju grešaka).
    Funkcija ne poziva session.commit() — čista separacija odgovornosti.
    """
    result = ImportResult()
    module_map = _build_module_map(session)
    concept_map = _build_concept_map(session)

    for task_data in tasks:
        task_id: str = task_data["task_id"]

        module_id = module_map.get(task_data["module"])
        if module_id is None:
            msg = f"{task_id}: nepoznat module number {task_data['module']}"
            result.errors.append(msg)
            logger.warning(msg)
            continue

        primary_concept_id = concept_map.get(task_data["primary_concept"])
        if primary_concept_id is None:
            msg = (
                f"{task_id}: nepoznat primary_concept '{task_data['primary_concept']}'"
            )
            result.errors.append(msg)
            logger.warning(msg)
            continue

        ins = insert(Task).values(
            source_id=task_id,
            module_id=module_id,
            title=task_data["title"],
            description=task_data["description"],
            sandbox_schema=task_data.get("sandbox_schema", "ecommerce_v1"),
            expected_query=task_data["expected_query"],
            expected_result=task_data["expected_result"],
            difficulty=int(task_data["difficulty"]),
            estimated_time_sec=task_data.get("estimated_time_sec"),
            # 🔴 ERRATA #66: `is_active` je od m6-plan-presence EKSPLICITAN po
            # zadatku, ne izveden iz koncepta.
            #
            # Dosad je vrijedio NALAZ #19: taskovi neevaluabilnih koncepata ulaze
            # neaktivni, izvedeno iz `UNSUPPORTED_CONCEPTS`. Taj kriterij je pao —
            # plan-presence evaluacija postoji, pa su M6 koncepti evaluabilni.
            # Neispravni su POJEDINI ZADACI (3 tvrde Index Scan a dobivaju Seq
            # Scan; 1 ne razlikuje anti-pattern), a to koncept ne može izraziti.
            #
            # Razlog deaktivacije stoji uz zadatak (`deactivation_reason` u
            # datasetu), pa preživljava re-import i ne živi samo u errati.
            is_active=_parse_is_active(task_data),
        )
        stmt = ins.on_conflict_do_update(
            constraint="uq_tasks_source_id",
            set_={
                "module_id": ins.excluded.module_id,
                "title": ins.excluded.title,
                "description": ins.excluded.description,
                "sandbox_schema": ins.excluded.sandbox_schema,
                "expected_query": ins.excluded.expected_query,
                "expected_result": ins.excluded.expected_result,
                "difficulty": ins.excluded.difficulty,
                "estimated_time_sec": ins.excluded.estimated_time_sec,
                "is_active": ins.excluded.is_active,
            },
        ).returning(Task.id)

        task_db_id: int = session.execute(stmt).scalar_one()

        # Rebuild task_concepts: DELETE + INSERT za čistu idempotentnost
        session.execute(delete(TaskConcept).where(TaskConcept.task_id == task_db_id))

        tc_rows: list[dict] = [
            {
                "task_id": task_db_id,
                "concept_id": primary_concept_id,
                "is_primary": True,
            }
        ]
        for sec_code in task_data.get("secondary_concepts") or []:
            sec_id = concept_map.get(sec_code)
            if sec_id is None:
                result.skipped_secondary_codes.add(sec_code)
                logger.debug("Preskačem sekundarni '%s' za %s", sec_code, task_id)
                continue
            tc_rows.append(
                {"task_id": task_db_id, "concept_id": sec_id, "is_primary": False}
            )

        session.execute(insert(TaskConcept).values(tc_rows))
        result.processed += 1

    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not DATASET_PATH.exists():
        logger.error("Dataset nije pronađen: %s", DATASET_PATH)
        sys.exit(1)

    data = json.loads(DATASET_PATH.read_text())
    tasks = data["tasks"]
    logger.info(
        "Učitano %d taskova iz dataseta (version=%s).", len(tasks), data.get("version")
    )

    with SessionLocal() as session:
        result = import_tasks(session, tasks)

        if result.errors:
            logger.error("--- %d hard-fail(ova) ---", len(result.errors))
            for err in result.errors:
                logger.error("  %s", err)
            session.rollback()
            logger.error("Import prekinut. Nula taskova upisano.")
            sys.exit(1)

        session.commit()

    logger.info("Import završen: %d taskova upisano/ažurirano.", result.processed)
    if result.skipped_secondary_codes:
        logger.info(
            "Preskočeni sekundarni kodovi (%d distinct): %s",
            len(result.skipped_secondary_codes),
            sorted(result.skipped_secondary_codes),
        )
    logger.info("Hard-failova: 0.")


if __name__ == "__main__":
    main()
