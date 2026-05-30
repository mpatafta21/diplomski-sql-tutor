"""Testovi za ManualReviewDB SQLite layer (2B-1C)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db.manual_review import ManualReviewDB, TaskReview


@pytest.fixture()
def db(tmp_path: Path) -> ManualReviewDB:
    return ManualReviewDB(tmp_path / "subdir" / "manual_review.sqlite")


def _seed(
    db: ManualReviewDB,
    task_id: str,
    *,
    decision: str = "pending",
    notes: str = "",
    concept_code: str = "where_filter",
    module_number: int = 2,
    difficulty: int = 2,
    task_status: str = "validated",
    failure_type: str | None = None,
) -> None:
    db.upsert_review(
        task_id=task_id,
        decision=decision,  # type: ignore[arg-type]
        notes=notes,
        concept_code=concept_code,
        module_number=module_number,
        difficulty=difficulty,
        task_status=task_status,
        failure_type=failure_type,
    )


def test_schema_init_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "x.sqlite"
    ManualReviewDB(db_path)
    # Drugi poziv ne smije baciti (CREATE IF NOT EXISTS)
    ManualReviewDB(db_path)
    assert db_path.exists()


def test_upsert_new_review(db: ManualReviewDB) -> None:
    _seed(db, "where_filter_d2_aaa", decision="approved", notes="ok")
    r = db.get_review("where_filter_d2_aaa")
    assert r is not None
    assert isinstance(r, TaskReview)
    assert r.decision == "approved"
    assert r.notes == "ok"
    assert r.concept_code == "where_filter"
    assert r.module_number == 2
    assert r.difficulty == 2
    assert r.task_status == "validated"
    assert r.failure_type is None


def test_upsert_overwrite_existing(db: ManualReviewDB) -> None:
    _seed(db, "t1", decision="pending")
    _seed(db, "t1", decision="rejected", notes="bad rows")
    r = db.get_review("t1")
    assert r is not None
    assert r.decision == "rejected"
    assert r.notes == "bad rows"


def test_get_review_not_found_returns_none(db: ManualReviewDB) -> None:
    assert db.get_review("does_not_exist") is None


def test_list_reviews_filter_by_decision(db: ManualReviewDB) -> None:
    _seed(db, "a", decision="approved")
    _seed(db, "b", decision="rejected")
    _seed(db, "c", decision="approved")
    approved = db.list_reviews(decision="approved")
    assert {r.task_id for r in approved} == {"a", "c"}


def test_list_reviews_filter_by_concept(db: ManualReviewDB) -> None:
    _seed(db, "a", concept_code="where_filter")
    _seed(db, "b", concept_code="group_by")
    _seed(db, "c", concept_code="where_filter")
    res = db.list_reviews(concept_code="where_filter")
    assert {r.task_id for r in res} == {"a", "c"}


def test_list_reviews_filter_by_failure_type(db: ManualReviewDB) -> None:
    _seed(db, "a", task_status="failed", failure_type="row_mismatch")
    _seed(db, "b", task_status="failed", failure_type="concept_not_detected")
    _seed(db, "c", task_status="validated", failure_type=None)
    res = db.list_reviews(failure_type="row_mismatch")
    assert {r.task_id for r in res} == {"a"}


def test_list_reviews_filter_by_module(db: ManualReviewDB) -> None:
    _seed(db, "a", module_number=1)
    _seed(db, "b", module_number=2)
    _seed(db, "c", module_number=1)
    res = db.list_reviews(module_number=1)
    assert {r.task_id for r in res} == {"a", "c"}


def test_list_reviews_no_filters_returns_all(db: ManualReviewDB) -> None:
    _seed(db, "a")
    _seed(db, "b")
    _seed(db, "c")
    assert len(db.list_reviews()) == 3


def test_get_stats_aggregation(db: ManualReviewDB) -> None:
    _seed(db, "a", decision="approved", concept_code="where_filter", module_number=2)
    _seed(db, "b", decision="approved", concept_code="group_by", module_number=3)
    _seed(db, "c", decision="rejected", concept_code="where_filter", module_number=2)
    _seed(db, "d", decision="pending", concept_code="where_filter", module_number=2)

    stats = db.get_stats()
    assert stats["total"] == 4
    assert stats["reviewed"] == 3  # pending ne računa kao reviewed
    assert stats["by_decision"]["approved"] == 2
    assert stats["by_decision"]["rejected"] == 1
    assert stats["by_decision"]["pending"] == 1
    assert stats["by_concept"]["where_filter"] == 3
    assert stats["by_concept"]["group_by"] == 1
    assert stats["by_module"][2] == 3
    assert stats["by_module"][3] == 1


def test_invalid_decision_rejected(db: ManualReviewDB) -> None:
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        _seed(db, "x", decision="bogus")  # type: ignore[arg-type]
