"""TDD testovi za scripts/import_dataset.py.

Svaki test dobiva svježi `db_session` koji rollbacka na kraju —
tasks tablica ostaje čista između testova.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Concept, Module, Task, TaskConcept


# ---------------------------------------------------------------------------
# Pomoćna funkcija za gradnju minimalnog task dict-a
# ---------------------------------------------------------------------------


def _task(
    task_id: str = "test_task_abc123",
    module: int = 1,
    primary_concept: str = "select_basic",
    secondary_concepts: list[str] | None = None,
    **extra,
) -> dict:
    return {
        "task_id": task_id,
        "module": module,
        "primary_concept": primary_concept,
        "difficulty": 2,
        "title": f"Testni zadatak {task_id}",
        "description": "Opis testnog zadatka.",
        "sandbox_schema": "ecommerce_v1",
        "expected_query": "SELECT 1",
        "expected_result": [{"?column?": 1}],
        "secondary_concepts": secondary_concepts
        if secondary_concepts is not None
        else [],
        "estimated_time_sec": None,
        **extra,
    }


# ---------------------------------------------------------------------------
# T1 — module→module_id mapping
# ---------------------------------------------------------------------------


def test_module_mapping(db_session: Session) -> None:
    """module=0 i module=3 dobivaju točan module_id iz modules tablice."""
    from scripts.import_dataset import import_tasks

    tasks = [
        _task(task_id="m0_task", module=0, primary_concept="null_handling"),
        _task(task_id="m3_task", module=3, primary_concept="inner_join"),
    ]
    result = import_tasks(db_session, tasks)

    assert result.processed == 2
    assert result.errors == []

    t0 = db_session.execute(
        select(Task).where(Task.source_id == "m0_task")
    ).scalar_one()
    t3 = db_session.execute(
        select(Task).where(Task.source_id == "m3_task")
    ).scalar_one()

    m0_id = db_session.execute(select(Module.id).where(Module.number == 0)).scalar_one()
    m3_id = db_session.execute(select(Module.id).where(Module.number == 3)).scalar_one()

    assert t0.module_id == m0_id
    assert t3.module_id == m3_id


# ---------------------------------------------------------------------------
# T2 — primary_concept hard-fail
# ---------------------------------------------------------------------------


def test_primary_concept_hard_fail(db_session: Session) -> None:
    """Task s nepostojećim primary_concept ne upisuje se; ostali prolaze."""
    from scripts.import_dataset import import_tasks

    tasks = [
        _task(task_id="valid_task", primary_concept="select_basic"),
        _task(
            task_id="bad_task", primary_concept="aggregate_functions"
        ),  # nepostoji u DB
    ]
    result = import_tasks(db_session, tasks)

    assert result.processed == 1
    assert len(result.errors) == 1
    assert "bad_task" in result.errors[0]
    assert "aggregate_functions" in result.errors[0]

    all_source_ids = db_session.execute(select(Task.source_id)).scalars().all()
    assert "valid_task" in all_source_ids
    assert "bad_task" not in all_source_ids


# ---------------------------------------------------------------------------
# T3 — secondary_concepts filter (3 različita nepoznata koda)
# ---------------------------------------------------------------------------


def test_secondary_concepts_filter(db_session: Session) -> None:
    """Nepoznati sekundarni kodovi se preskaču; validni se upisuju; import ne puca."""
    from scripts.import_dataset import import_tasks

    tasks = [
        _task(
            task_id="t_sec",
            module=3,
            primary_concept="inner_join",
            secondary_concepts=[
                "select_basic",  # validan
                "aggregation",  # NEVALIDAN
                "subquery",  # NEVALIDAN
                "returning_clause",  # NEVALIDAN
                "group_by_having",  # NEVALIDAN
            ],
        )
    ]
    result = import_tasks(db_session, tasks)

    assert result.processed == 1
    assert result.errors == []
    # Sva 4 nevalidna koda moraju biti u skupu preskočenih
    assert {"aggregation", "subquery", "returning_clause", "group_by_having"}.issubset(
        result.skipped_secondary_codes
    )

    t = db_session.execute(select(Task).where(Task.source_id == "t_sec")).scalar_one()
    tc_rows = (
        db_session.execute(select(TaskConcept).where(TaskConcept.task_id == t.id))
        .scalars()
        .all()
    )
    # primary (inner_join) + 1 validan sekundarni (select_basic) = 2 redaka
    assert len(tc_rows) == 2


# ---------------------------------------------------------------------------
# T4 — is_primary flag
# ---------------------------------------------------------------------------


def test_is_primary_flag(db_session: Session) -> None:
    """primary_concept → is_primary=True; sekundarni → is_primary=False."""
    from scripts.import_dataset import import_tasks

    tasks = [
        _task(
            task_id="t_prim",
            module=3,
            primary_concept="inner_join",
            secondary_concepts=["left_join", "select_basic"],
        )
    ]
    result = import_tasks(db_session, tasks)
    assert result.processed == 1

    t = db_session.execute(select(Task).where(Task.source_id == "t_prim")).scalar_one()
    tc_rows = (
        db_session.execute(select(TaskConcept).where(TaskConcept.task_id == t.id))
        .scalars()
        .all()
    )

    primary_rows = [r for r in tc_rows if r.is_primary]
    secondary_rows = [r for r in tc_rows if not r.is_primary]

    assert len(primary_rows) == 1
    assert len(secondary_rows) == 2

    inner_join_id = db_session.execute(
        select(Concept.id).where(Concept.code == "inner_join")
    ).scalar_one()
    assert primary_rows[0].concept_id == inner_join_id


# ---------------------------------------------------------------------------
# T5 — idempotentnost (dvostruki import)
# ---------------------------------------------------------------------------


def test_idempotency(db_session: Session) -> None:
    """Dvostruki import istog dataseta → count(tasks) i count(task_concepts) identičan."""
    from scripts.import_dataset import import_tasks

    tasks = [
        _task(task_id="idem1", primary_concept="select_basic"),
        _task(
            task_id="idem2",
            module=3,
            primary_concept="inner_join",
            secondary_concepts=["left_join"],
        ),
    ]

    result1 = import_tasks(db_session, tasks)
    count1_tasks = db_session.execute(
        select(func.count()).select_from(Task)
    ).scalar_one()
    count1_tc = db_session.execute(
        select(func.count()).select_from(TaskConcept)
    ).scalar_one()

    result2 = import_tasks(db_session, tasks)
    count2_tasks = db_session.execute(
        select(func.count()).select_from(Task)
    ).scalar_one()
    count2_tc = db_session.execute(
        select(func.count()).select_from(TaskConcept)
    ).scalar_one()

    assert result1.errors == result2.errors == []
    assert count1_tasks == count2_tasks, "Dvostruki import duplicirao tasks"
    assert count1_tc == count2_tc, "Dvostruki import duplicirao task_concepts"


# ---------------------------------------------------------------------------
# T6 — task bez secondary_concepts
# ---------------------------------------------------------------------------


def test_no_secondary_concepts(db_session: Session) -> None:
    """Task bez sekundarnih (None ili []) upiše samo primary red u task_concepts."""
    from scripts.import_dataset import import_tasks

    tasks = [
        _task(task_id="no_sec_none", secondary_concepts=None),
        _task(task_id="no_sec_empty", secondary_concepts=[]),
    ]
    result = import_tasks(db_session, tasks)

    assert result.processed == 2
    assert result.errors == []

    for source_id in ["no_sec_none", "no_sec_empty"]:
        t = db_session.execute(
            select(Task).where(Task.source_id == source_id)
        ).scalar_one()
        tc_rows = (
            db_session.execute(select(TaskConcept).where(TaskConcept.task_id == t.id))
            .scalars()
            .all()
        )
        assert len(tc_rows) == 1, (
            f"{source_id}: očekivano 1 task_concept red, dobiveno {len(tc_rows)}"
        )
        assert tc_rows[0].is_primary is True
