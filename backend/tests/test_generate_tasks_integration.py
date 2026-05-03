"""End-to-end integration test za generate_tasks pipeline (mocked Anthropic API)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.generate_tasks import main


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "api_response_inner_join_d2.json"


@pytest.fixture
def fake_api_message():
    """Mock anthropic.types.Message based on recorded fixture."""
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    msg = MagicMock()
    msg.content = [MagicMock(text=raw["content"])]
    msg.usage = MagicMock(
        input_tokens=raw["input_tokens"],
        output_tokens=raw["output_tokens"],
        cache_read_input_tokens=raw["cached_tokens"],
    )
    msg.stop_reason = raw["stop_reason"]
    return msg


def test_inner_join_d2_pipeline_end_to_end(
    fake_api_message, tmp_path, monkeypatch, sandbox_connection_string
):
    """Pipeline radi end-to-end: PromptBuilder -> mock API -> Pydantic -> Validator -> save_meta.

    Validation će fail-ati na result_match jer fixture ima placeholder vrijednosti
    koje ne podudaraju stvarni sandbox output. Output ide u failed/ subdir, što je
    očekivano — pipeline nije srušen, JSON je serijaliziran, struktura je kompletna.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    monkeypatch.setenv("SANDBOX_DATABASE_URL", sandbox_connection_string)

    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fake_api_message

        exit_code = main([
            "--concept", "inner_join",
            "--difficulty", "2",
            "--count", "1",
            "--output-dir", str(tmp_path),
            "--dry-run",
            "--max-retries", "1",
        ])

    # Pipeline mora producirat 1 JSON output (validated/ ili failed/, ne važno).
    all_outputs = list(tmp_path.rglob("*.json"))
    assert len(all_outputs) == 1, f"Expected 1 JSON output, got {len(all_outputs)}"

    meta = json.loads(all_outputs[0].read_text(encoding="utf-8"))
    assert meta["task"]["primary_concept"] == "inner_join"
    assert meta["task"]["difficulty"] == 2
    assert "INNER JOIN" in meta["task"]["expected_query"].upper()
    assert meta["model_used"] == "claude-sonnet-4-6"
    # exit_code may be 1 ako validation fail-a (placeholder rows mismatch);
    # to je očekivano za sintetički fixture.
    assert exit_code in (0, 1)
