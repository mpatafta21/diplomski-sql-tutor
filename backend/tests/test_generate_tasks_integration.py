"""End-to-end integration testovi za generate_tasks pipeline (mocked Anthropic API)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.generate_tasks import main
from scripts.lib.sandbox_runner import ComparisonResult


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "api_response_inner_join_d2.json"


def _make_mock_message(text: str, input_tokens=1850, output_tokens=320, cached=0):
    msg = MagicMock()
    msg.content = [MagicMock(text=text)]
    msg.usage = MagicMock(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cached,
    )
    msg.stop_reason = "end_turn"
    return msg


@pytest.fixture
def fixture_message():
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return _make_mock_message(
        raw["content"],
        raw["input_tokens"],
        raw["output_tokens"],
        raw["cached_tokens"],
    )


def _run_cli(monkeypatch, sandbox_url, output_dir, extra_args=None):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    monkeypatch.setenv("SANDBOX_DATABASE_URL", sandbox_url)
    args = [
        "--concept", "inner_join",
        "--difficulty", "2",
        "--count", "1",
        "--output-dir", str(output_dir),
        "--dry-run",
        "--max-retries", "1",
    ]
    if extra_args:
        args.extend(extra_args)
    return main(args)


def test_failed_routing_when_validation_fails(
    fixture_message, tmp_path, monkeypatch, sandbox_connection_string
):
    """Fixture s placeholder vrijednostima -> result_match fail -> failed/ subdir."""
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fixture_message
        exit_code = _run_cli(monkeypatch, sandbox_connection_string, tmp_path)

        assert MockSDK.return_value.messages.create.call_count == 1, (
            "max_retries=1 should produce exactly 1 API call"
        )

    failed_files = list((tmp_path / "failed").glob("*.json"))
    validated_files = (
        list((tmp_path / "validated").glob("*.json"))
        if (tmp_path / "validated").exists()
        else []
    )
    assert len(failed_files) == 1, f"Expected 1 failed JSON, got {failed_files}"
    assert len(validated_files) == 0
    assert exit_code == 1


def test_validated_routing_when_compare_matches(
    fixture_message, tmp_path, monkeypatch, sandbox_connection_string
):
    """compare() monkey-patched to always match -> validated/ subdir + exit 0."""
    with patch("scripts.lib.api_client.Anthropic") as MockSDK, patch(
        "scripts.lib.sandbox_runner.SandboxRunner.compare",
        return_value=ComparisonResult(
            matches=True, diff_summary="OK", actual_count=1, expected_count=1
        ),
    ):
        MockSDK.return_value.messages.create.return_value = fixture_message
        exit_code = _run_cli(monkeypatch, sandbox_connection_string, tmp_path)

    validated_files = list((tmp_path / "validated").glob("*.json"))
    failed_files = (
        list((tmp_path / "failed").glob("*.json"))
        if (tmp_path / "failed").exists()
        else []
    )
    assert len(validated_files) == 1, f"Expected 1 validated JSON, got {validated_files}"
    assert len(failed_files) == 0
    assert exit_code == 0


def test_max_retries_1_does_not_retry_on_schema_failure(
    tmp_path, monkeypatch, sandbox_connection_string
):
    """Malformed JSON response, max_retries=1 -> točno 1 API call (no CLI retry)."""
    bad_msg = _make_mock_message("ovo nije valjani JSON jednostavno tekst")
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = bad_msg
        exit_code = _run_cli(monkeypatch, sandbox_connection_string, tmp_path)

        assert MockSDK.return_value.messages.create.call_count == 1, (
            "Schema failure s max_retries=1 ne smije retry-ati"
        )
    assert exit_code == 1


def test_schema_retry_then_success(
    fixture_message, tmp_path, monkeypatch, sandbox_connection_string
):
    """Bad response na 1. attempt, valid na 2. -> točno 2 API calls, validated output."""
    bad_msg = _make_mock_message("totalno nije JSON")
    with patch("scripts.lib.api_client.Anthropic") as MockSDK, patch(
        "scripts.lib.sandbox_runner.SandboxRunner.compare",
        return_value=ComparisonResult(
            matches=True, diff_summary="OK", actual_count=1, expected_count=1
        ),
    ):
        MockSDK.return_value.messages.create.side_effect = [bad_msg, fixture_message]
        # Override max_retries=2 to allow second attempt
        monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
        monkeypatch.setenv("SANDBOX_DATABASE_URL", sandbox_connection_string)
        exit_code = main([
            "--concept", "inner_join",
            "--difficulty", "2",
            "--count", "1",
            "--output-dir", str(tmp_path),
            "--max-retries", "2",
        ])

        assert MockSDK.return_value.messages.create.call_count == 2

    assert exit_code == 0
    assert len(list((tmp_path / "validated").glob("*.json"))) == 1


def test_croatian_characters_roundtrip_utf8(
    fixture_message, tmp_path, monkeypatch, sandbox_connection_string
):
    """Croatian dijakritike (ž, č, š) moraju ostati pravi UTF-8 byte-ovi, ne \\uXXXX."""
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fixture_message
        _run_cli(monkeypatch, sandbox_connection_string, tmp_path)

    all_outputs = list(tmp_path.rglob("*.json"))
    assert len(all_outputs) == 1
    raw_bytes = all_outputs[0].read_bytes()

    # Fixture title sadrži "Narudžbe" — ž mora biti UTF-8 (\xc5\xbe), ne ž escape.
    assert "ž".encode("utf-8") in raw_bytes, (
        "Croatian ž mora biti UTF-8 byte-ovan, ne ASCII escape (Pydantic ensure_ascii=False)"
    )
    assert b"\\u017e" not in raw_bytes


def test_generate_one_propagates_dml_to_validator(fixture_message, tmp_path):
    """generate_one(dml=True) mora pozvati validator.validate(task, dml=True).

    Regression: pilot_run je propustio proslijediti dml flag, pa su svi INSERT
    zadaci pucali permission denied iako je sandbox_readwrite imao GRANT-ove.
    """
    from scripts.generate_tasks import generate_one
    from scripts.lib.api_client import AnthropicResponse

    builder = MagicMock()
    prompt = MagicMock(system="sys", user="user")
    builder.build.return_value = prompt

    api = MagicMock()
    # generate_one koristi api.generate() — ne SDK direktno
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    api.generate.return_value = AnthropicResponse(
        content=raw["content"],
        input_tokens=raw["input_tokens"],
        output_tokens=raw["output_tokens"],
        cached_tokens=raw["cached_tokens"],
        stop_reason="end_turn",
    )
    api.model = "claude-sonnet-4-6"

    validator = MagicMock()
    from scripts.lib.task_validator import ValidationResult
    validator.validate.return_value = ValidationResult(passed=True)

    meta, _ = generate_one(
        builder=builder,
        api=api,
        validator=validator,
        concept="insert",
        difficulty=1,
        dml=True,
        max_retries=1,
    )

    assert meta is not None and meta.validation_passed
    # Bitno: validator.validate mora biti pozvan s dml=True
    call = validator.validate.call_args
    assert call.kwargs.get("dml") is True or (len(call.args) >= 2 and call.args[1] is True), (
        f"validator.validate mora biti pozvan s dml=True, dobio: args={call.args}, kwargs={call.kwargs}"
    )


def test_generate_one_extended_thinking_always_on_default(fixture_message, tmp_path):
    """2B-1E: generate_one bez explicit extended_thinking enable-a thinking za sve difficulty levele.

    Regression za 2B-1D root cause: prije je default bio difficulty>=4, pa su d=1-3
    zadaci dobili thinking OFF i halucinirali expected_result u 19/27 fail-ova.
    """
    from scripts.generate_tasks import generate_one
    from scripts.lib.api_client import AnthropicResponse

    builder = MagicMock()
    builder.build.return_value = MagicMock(system="sys", user="user")

    api = MagicMock()
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    api.generate.return_value = AnthropicResponse(
        content=raw["content"],
        input_tokens=raw["input_tokens"],
        output_tokens=raw["output_tokens"],
        cached_tokens=raw["cached_tokens"],
        stop_reason="end_turn",
    )
    api.model = "claude-sonnet-4-6"

    validator = MagicMock()
    from scripts.lib.task_validator import ValidationResult
    validator.validate.return_value = ValidationResult(passed=True)

    for difficulty in [1, 2, 3, 4, 5]:
        api.generate.reset_mock()
        generate_one(
            builder=builder,
            api=api,
            validator=validator,
            concept="select_basic",
            difficulty=difficulty,
            max_retries=1,
        )
        call = api.generate.call_args
        assert call.kwargs.get("extended_thinking") is True, (
            f"d={difficulty}: extended_thinking mora biti True po default-u, "
            f"dobio: {call.kwargs.get('extended_thinking')}"
        )


def test_generate_one_extended_thinking_explicit_false_respected(fixture_message, tmp_path):
    """generate_one(extended_thinking=False) eksplicitno mora biti respektiran (escape hatch)."""
    from scripts.generate_tasks import generate_one
    from scripts.lib.api_client import AnthropicResponse

    builder = MagicMock()
    builder.build.return_value = MagicMock(system="sys", user="user")

    api = MagicMock()
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    api.generate.return_value = AnthropicResponse(
        content=raw["content"],
        input_tokens=raw["input_tokens"],
        output_tokens=raw["output_tokens"],
        cached_tokens=raw["cached_tokens"],
        stop_reason="end_turn",
    )
    api.model = "claude-sonnet-4-6"

    validator = MagicMock()
    from scripts.lib.task_validator import ValidationResult
    validator.validate.return_value = ValidationResult(passed=True)

    generate_one(
        builder=builder,
        api=api,
        validator=validator,
        concept="select_basic",
        difficulty=3,
        extended_thinking=False,
        max_retries=1,
    )
    call = api.generate.call_args
    assert call.kwargs.get("extended_thinking") is False, (
        f"explicit extended_thinking=False mora biti respektiran, "
        f"dobio: {call.kwargs.get('extended_thinking')}"
    )


def test_generate_one_default_dml_false(fixture_message, tmp_path):
    """generate_one() bez dml arg-a mora propagirati dml=False (default behavior za SELECT)."""
    from scripts.generate_tasks import generate_one
    from scripts.lib.api_client import AnthropicResponse

    builder = MagicMock()
    builder.build.return_value = MagicMock(system="sys", user="user")

    api = MagicMock()
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    api.generate.return_value = AnthropicResponse(
        content=raw["content"],
        input_tokens=raw["input_tokens"],
        output_tokens=raw["output_tokens"],
        cached_tokens=raw["cached_tokens"],
        stop_reason="end_turn",
    )
    api.model = "claude-sonnet-4-6"

    validator = MagicMock()
    from scripts.lib.task_validator import ValidationResult
    validator.validate.return_value = ValidationResult(passed=True)

    generate_one(
        builder=builder,
        api=api,
        validator=validator,
        concept="select_basic",
        difficulty=1,
        max_retries=1,
    )

    call = validator.validate.call_args
    dml_arg = call.kwargs.get("dml", call.args[1] if len(call.args) >= 2 else False)
    assert dml_arg is False, f"default dml mora biti False, dobio: {dml_arg}"
