"""Testovi za --from-matrix batch mode u generate_tasks.py (Faza 2B-2)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from scripts.generate_tasks import (
    MAX_RETRIES_AGGREGATIONS,
    MAX_RETRIES_DEFAULT,
    _iter_matrix_plan,
    batch_generate_from_matrix,
    load_distribution_matrix,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def real_matrix_path() -> Path:
    """Vraća path do checkanog `backend/config/task_distribution.yaml`."""
    return Path(__file__).resolve().parents[1] / "config" / "task_distribution.yaml"


@pytest.fixture
def mini_matrix() -> dict:
    """Mala matrica za testove — 2 modula, 3 koncepta, totalno 4 zadataka."""
    return {
        "modules": {
            1: {
                "name": "Test M1",
                "concepts": {
                    "select_basic": {"tier": "easy", "distribution": {1: 2}},
                    "where_filter": {"tier": "easy", "distribution": {1: 1}},
                },
            },
            4: {
                "name": "Test M4 DML",
                "concepts": {
                    "insert": {"tier": "easy", "dml": True, "distribution": {1: 1}},
                },
            },
        }
    }


def _fake_meta(concept: str, difficulty: int, passed: bool = True, cost_tokens: int = 500):
    """Helper koji vraća MagicMock koji imitira GeneratedTaskMeta."""
    meta = MagicMock()
    meta.task.primary_concept = concept
    meta.task.difficulty = difficulty
    meta.validation_passed = passed
    meta.validation_failures = [] if passed else [{"level": "x", "code": "y"}]
    meta.api_input_tokens = cost_tokens
    meta.api_output_tokens = cost_tokens // 2
    meta.api_cached_tokens = 0
    meta.generation_id = f"fakeuuid-{concept}-d{difficulty}"
    meta.retries = 0
    meta.model_dump_json.return_value = "{}"
    return meta


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_load_real_distribution_matrix_has_expected_modules(real_matrix_path: Path):
    """Stvarni `task_distribution.yaml` mora imati 7 modula (0,1,2,3,4,5,6)."""
    matrix = load_distribution_matrix(real_matrix_path)
    assert "modules" in matrix
    assert set(matrix["modules"].keys()) == {0, 1, 2, 3, 4, 5, 6}


def test_load_real_distribution_matrix_total_is_105(real_matrix_path: Path):
    """Sumiranje svih distribution count-eva mora biti 105 (per faza-2a §2)."""
    matrix = load_distribution_matrix(real_matrix_path)
    total = 0
    for mod in matrix["modules"].values():
        for concept_data in mod["concepts"].values():
            total += sum(concept_data["distribution"].values())
    assert total == 105


def test_load_real_distribution_matrix_module_4_concepts_are_dml(real_matrix_path: Path):
    """Svi koncepti u M4 moraju imati `dml: true` (insert/update/delete)."""
    matrix = load_distribution_matrix(real_matrix_path)
    m4 = matrix["modules"][4]
    assert set(m4["concepts"].keys()) == {"insert", "update", "delete"}
    for concept_data in m4["concepts"].values():
        assert concept_data.get("dml") is True


def test_iter_matrix_plan_filters_module(mini_matrix: dict):
    """`_iter_matrix_plan` s only_module=1 vraća samo M1 zadatke."""
    plan = _iter_matrix_plan(mini_matrix, only_module=1, skip_concepts=set())
    assert all(mod == 1 for mod, *_ in plan)
    assert len(plan) == 3  # 2 select_basic + 1 where_filter


def test_iter_matrix_plan_skip_concepts_excludes_listed(mini_matrix: dict):
    """`_iter_matrix_plan` s skip_concepts={'select_basic'} preskoči te zadatke."""
    plan = _iter_matrix_plan(mini_matrix, only_module=None, skip_concepts={"select_basic"})
    concepts = {c for _, c, *_ in plan}
    assert "select_basic" not in concepts
    assert {"where_filter", "insert"}.issubset(concepts)


def test_batch_generate_calls_generate_one_per_planned_task(mini_matrix: dict, tmp_path: Path):
    """batch_generate_from_matrix mora pozvati generate_one tačno N puta (po planu)."""
    builder = MagicMock()
    api = MagicMock()
    validator = MagicMock()

    with patch("scripts.generate_tasks.generate_one") as mock_gen:
        mock_gen.side_effect = lambda *a, **kw: (
            _fake_meta(kw["concept"], kw["difficulty"]),
            [],
        )
        report = batch_generate_from_matrix(
            builder, api, validator, mini_matrix, tmp_path, interactive=False
        )

    # 4 task-a planirano (2+1+1)
    assert mock_gen.call_count == 4
    assert report["total_validated"] == 4
    assert report["total_failed"] == 0


def test_batch_generate_propagates_dml_flag_for_module_4(mini_matrix: dict, tmp_path: Path):
    """M4 koncepti (insert/update/delete) moraju biti pozvani s dml=True."""
    builder, api, validator = MagicMock(), MagicMock(), MagicMock()

    with patch("scripts.generate_tasks.generate_one") as mock_gen:
        mock_gen.side_effect = lambda *a, **kw: (
            _fake_meta(kw["concept"], kw["difficulty"]),
            [],
        )
        batch_generate_from_matrix(
            builder, api, validator, mini_matrix, tmp_path, interactive=False
        )

    # insert poziv mora imati dml=True
    insert_calls = [c for c in mock_gen.call_args_list if c.kwargs["concept"] == "insert"]
    assert len(insert_calls) == 1
    assert insert_calls[0].kwargs["dml"] is True

    # SELECT koncepti dml=False
    select_calls = [c for c in mock_gen.call_args_list if c.kwargs["concept"] != "insert"]
    for call in select_calls:
        assert call.kwargs.get("dml", False) is False


def test_batch_generate_uses_max_retries_5_for_module_2(tmp_path: Path):
    """Modul 2 (agregacije) mora dobiti max_retries=5, ostali default 3."""
    matrix = {
        "modules": {
            1: {"name": "M1", "concepts": {"select_basic": {"tier": "easy", "distribution": {1: 1}}}},
            2: {"name": "M2", "concepts": {"agg_count": {"tier": "medium", "distribution": {1: 1}}}},
        }
    }
    builder, api, validator = MagicMock(), MagicMock(), MagicMock()

    with patch("scripts.generate_tasks.generate_one") as mock_gen:
        mock_gen.side_effect = lambda *a, **kw: (
            _fake_meta(kw["concept"], kw["difficulty"]),
            [],
        )
        batch_generate_from_matrix(
            builder, api, validator, matrix, tmp_path, interactive=False
        )

    m1_calls = [c for c in mock_gen.call_args_list if c.kwargs["concept"] == "select_basic"]
    m2_calls = [c for c in mock_gen.call_args_list if c.kwargs["concept"] == "agg_count"]
    assert m1_calls[0].kwargs["max_retries"] == MAX_RETRIES_DEFAULT
    assert m2_calls[0].kwargs["max_retries"] == MAX_RETRIES_AGGREGATIONS


def test_batch_generate_aborts_module_when_budget_exceeded(tmp_path: Path):
    """Ako kumulativni trošak pređe module_budget_usd, modul se abort-a."""
    matrix = {
        "modules": {
            1: {
                "name": "M1",
                "concepts": {
                    "select_basic": {"tier": "easy", "distribution": {1: 10}},  # 10 tasks
                },
            }
        }
    }
    builder, api, validator = MagicMock(), MagicMock(), MagicMock()

    # Svaki task košta ~$0.30 (kroz visoki token count) — budget $0.50 → abort nakon 2 task-a
    high_cost_tokens = 100_000  # ~$0.30 (input 100k tokens × $3/MTok)

    with patch("scripts.generate_tasks.generate_one") as mock_gen:
        mock_gen.side_effect = lambda *a, **kw: (
            _fake_meta(kw["concept"], kw["difficulty"], cost_tokens=high_cost_tokens),
            [],
        )
        report = batch_generate_from_matrix(
            builder,
            api,
            validator,
            matrix,
            tmp_path,
            module_budget_usd=0.50,
            interactive=False,
        )

    # Module aborted, ali generate_one zvao < 10 puta
    assert report["modules"][1]["aborted"] is True
    assert mock_gen.call_count < 10  # abortano prije nego sve pozvano


def test_batch_generate_writes_report_json(mini_matrix: dict, tmp_path: Path):
    """batch_generate_from_matrix mora pisati batch_report.json u output_dir."""
    builder, api, validator = MagicMock(), MagicMock(), MagicMock()

    with patch("scripts.generate_tasks.generate_one") as mock_gen:
        mock_gen.side_effect = lambda *a, **kw: (
            _fake_meta(kw["concept"], kw["difficulty"]),
            [],
        )
        batch_generate_from_matrix(
            builder, api, validator, mini_matrix, tmp_path, interactive=False
        )

    report_path = tmp_path / "batch_report.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert "modules" in data
    assert "total_validated" in data
    assert data["total_validated"] == 4


def test_load_distribution_matrix_missing_modules_key_raises(tmp_path: Path):
    """Malformed YAML bez top-level 'modules' diže ValueError."""
    bad_path = tmp_path / "bad_matrix.yaml"
    bad_path.write_text("not_modules:\n  foo: bar\n", encoding="utf-8")
    with pytest.raises(ValueError, match="modules"):
        load_distribution_matrix(bad_path)
