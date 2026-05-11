"""Smoke testovi za pilot_run.py — puna pipeline s mock API-jem."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.pilot_run import PILOT_CONFIG, run_pilot


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_fake_meta(concept: str, difficulty: int):
    """Vraća MagicMock koji imitira GeneratedTaskMeta."""
    meta = MagicMock()
    meta.task.primary_concept = concept
    meta.task.difficulty = difficulty
    meta.validation_passed = True
    meta.validation_failures = []
    meta.api_input_tokens = 500
    meta.api_output_tokens = 200
    meta.api_cached_tokens = 400
    meta.generation_id = "aabbccdd"
    meta.model_dump_json.return_value = "{}"
    return meta


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_pilot_run_smoke_mock_api(tmp_path: Path):
    """Puna pipeline s mock generate_one: 12 tasks generirano, report kreiran."""
    builder = MagicMock()
    api = MagicMock()
    validator = MagicMock()

    # Svaki poziv generate_one vraća validan meta
    with patch("scripts.pilot_run.generate_one") as mock_gen:
        mock_gen.side_effect = lambda builder, api, validator, concept, difficulty, **kw: (
            _make_fake_meta(concept, difficulty),
            [],
        )
        report = run_pilot(builder, api, validator, tmp_path)

    # 12 tasks (6 koncepta × 2 težine)
    total_tasks = sum(len(v) for v in report["per_concept"].values())
    assert total_tasks == 12
    assert len(report["per_concept"]) == 6

    # pilot_report.json mora biti kreiran
    report_path = tmp_path / "pilot_report.json"
    assert report_path.exists()


def test_pilot_report_format(tmp_path: Path):
    """pilot_report.json sadrži per_concept, total_cost, started_at ključeve."""
    builder, api, validator = MagicMock(), MagicMock(), MagicMock()

    with patch("scripts.pilot_run.generate_one") as mock_gen:
        mock_gen.side_effect = lambda builder, api, validator, concept, difficulty, **kw: (
            _make_fake_meta(concept, difficulty),
            [],
        )
        report = run_pilot(builder, api, validator, tmp_path)

    assert "per_concept" in report
    assert "total_cost" in report
    assert "started_at" in report
    assert isinstance(report["total_cost"], float)

    # Svaki concept entry sadrži status i cost_usd
    for concept_results in report["per_concept"].values():
        for entry in concept_results:
            assert "status" in entry
            assert "cost_usd" in entry
            assert "difficulty" in entry


def test_pilot_dml_flag_propagation():
    """PILOT_CONFIG ima dml=True za 'insert' koncept."""
    insert_entries = [e for e in PILOT_CONFIG if e["concept"] == "insert"]
    assert len(insert_entries) == 1, "insert mora biti u PILOT_CONFIG"
    assert insert_entries[0].get("dml") is True, "insert mora imati dml=True"

    # Ostali koncepti ne smiju imati dml=True (SELECT koncepti)
    non_dml = [e for e in PILOT_CONFIG if e["concept"] != "insert"]
    for entry in non_dml:
        assert not entry.get("dml"), f"{entry['concept']} ne smije imati dml=True"
