"""Testovi za loaders u 2B-1C validation toolu."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.db.manual_review import ManualReviewDB
from scripts.validation_tool.loaders import (
    bootstrap_pending_reviews,
    extract_failure_type,
    load_all_tasks,
    load_concept_module_map,
)


def _write_task(
    base: Path,
    status: str,
    filename: str,
    *,
    primary_concept: str = "where_filter",
    difficulty: int = 2,
    validation_failures: list[dict] | None = None,
) -> Path:
    subdir = base / status
    subdir.mkdir(parents=True, exist_ok=True)
    payload = {
        "task": {
            "title": "Test zadatak za loader",
            "description": "Opis zadatka koji ima dovoljnu duljinu da prođe Pydantic.",
            "primary_concept": primary_concept,
            "secondary_concepts": [],
            "difficulty": difficulty,
            "estimated_time_sec": 120,
            "sandbox_schema": "ecommerce_v1",
            "expected_query": "SELECT 1;",
            "expected_result": [],
        },
        "generation_id": "x",
        "api_input_tokens": 1,
        "api_output_tokens": 1,
        "api_cached_tokens": 0,
        "retries": 0,
        "validation_passed": status == "validated",
        "validation_failures": validation_failures or [],
        "generated_at": "2026-01-01T00:00:00+00:00",
        "model_used": "test",
        "extended_thinking": False,
    }
    path = subdir / filename
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_all_tasks_from_validated_and_failed(tmp_path: Path) -> None:
    _write_task(tmp_path, "validated", "where_filter_d2_aaa.json")
    _write_task(
        tmp_path,
        "failed",
        "group_by_d3_bbb.json",
        primary_concept="group_by",
        difficulty=3,
        validation_failures=[
            {
                "level": "result_match",
                "code": "row_mismatch",
                "message": "rows differ",
                "details": {},
            }
        ],
    )
    tasks = load_all_tasks(tmp_path)
    assert len(tasks) == 2
    statuses = {t["_task_status"] for t in tasks}
    assert statuses == {"validated", "failed"}
    # Annotated paths
    assert all("_source_path" in t for t in tasks)
    assert all("_task_id" in t for t in tasks)


def test_load_all_tasks_handles_malformed_json(tmp_path: Path) -> None:
    (tmp_path / "validated").mkdir()
    (tmp_path / "validated" / "bad.json").write_text("not json{{{", encoding="utf-8")
    _write_task(tmp_path, "validated", "good.json")
    tasks = load_all_tasks(tmp_path)
    # Loš se preskoče, dobar se učita
    assert len(tasks) == 1
    assert tasks[0]["_task_id"] == "good"


def test_load_all_tasks_empty_dir(tmp_path: Path) -> None:
    assert load_all_tasks(tmp_path) == []


def test_load_all_tasks_skips_pilot_subdir(tmp_path: Path) -> None:
    """Loader gleda samo `validated/` i `failed/` korijena, ne pilot podstabla."""
    _write_task(tmp_path, "validated", "main_a.json")
    # pilot dir ne smije biti slučajno učitan kao validated
    pilot_validated = tmp_path / "pilot" / "validated"
    pilot_validated.mkdir(parents=True)
    (pilot_validated / "pilot_a.json").write_text("{}", encoding="utf-8")
    tasks = load_all_tasks(tmp_path)
    assert {t["_task_id"] for t in tasks} == {"main_a"}


def test_extract_failure_type_mapping() -> None:
    # Validated → None
    assert (
        extract_failure_type({"_task_status": "validated", "validation_failures": []})
        is None
    )
    # concept_coverage level → concept_not_detected
    assert (
        extract_failure_type(
            {
                "_task_status": "failed",
                "validation_failures": [
                    {"level": "concept_coverage", "code": "primary_concept_not_detected"}
                ],
            }
        )
        == "concept_not_detected"
    )
    # result_match + row_mismatch
    assert (
        extract_failure_type(
            {
                "_task_status": "failed",
                "validation_failures": [
                    {"level": "result_match", "code": "row_mismatch"}
                ],
            }
        )
        == "row_mismatch"
    )
    # result_match + execution_failed → sandbox_error
    assert (
        extract_failure_type(
            {
                "_task_status": "failed",
                "validation_failures": [
                    {"level": "result_match", "code": "execution_failed"}
                ],
            }
        )
        == "sandbox_error"
    )
    # syntax level → other (van plana taxonomy)
    assert (
        extract_failure_type(
            {
                "_task_status": "failed",
                "validation_failures": [
                    {"level": "syntax", "code": "parse_failed"}
                ],
            }
        )
        == "other"
    )
    # failed s praznim failures (edge case) → other
    assert (
        extract_failure_type(
            {"_task_status": "failed", "validation_failures": []}
        )
        == "other"
    )


def test_bootstrap_pending_reviews_idempotent(tmp_path: Path) -> None:
    db = ManualReviewDB(tmp_path / "rev.sqlite")
    _write_task(tmp_path, "validated", "where_filter_d2_aaa.json")
    _write_task(
        tmp_path,
        "failed",
        "group_by_d3_bbb.json",
        primary_concept="group_by",
        difficulty=3,
        validation_failures=[
            {"level": "result_match", "code": "row_mismatch", "message": "", "details": {}}
        ],
    )
    tasks = load_all_tasks(tmp_path)

    concept_map = {"where_filter": 2, "group_by": 3}
    added = bootstrap_pending_reviews(tasks, db, concept_map)
    assert added == 2

    # Drugi run ne smije ništa dodati niti pretumbati postojeće odluke
    db.upsert_review(
        task_id="where_filter_d2_aaa",
        decision="approved",
        notes="prethodno",
        concept_code="where_filter",
        module_number=2,
        difficulty=2,
        task_status="validated",
        failure_type=None,
    )
    added_again = bootstrap_pending_reviews(tasks, db, concept_map)
    assert added_again == 0
    assert db.get_review("where_filter_d2_aaa").decision == "approved"

    # Failed task ima ispravan failure_type
    failed_review = db.get_review("group_by_d3_bbb")
    assert failed_review is not None
    assert failed_review.failure_type == "row_mismatch"
    assert failed_review.module_number == 3


def test_load_concept_module_map_reads_yaml_dir(tmp_path: Path) -> None:
    concepts_dir = tmp_path / "concepts"
    concepts_dir.mkdir()
    (concepts_dir / "alpha.yaml").write_text(
        "concept_code: alpha\nmodule_number: 1\n", encoding="utf-8"
    )
    (concepts_dir / "beta.yaml").write_text(
        "concept_code: beta\nmodule_number: 4\n", encoding="utf-8"
    )
    mapping = load_concept_module_map(concepts_dir)
    assert mapping == {"alpha": 1, "beta": 4}


def test_load_concept_module_map_missing_dir_returns_empty(tmp_path: Path) -> None:
    assert load_concept_module_map(tmp_path / "nope") == {}
