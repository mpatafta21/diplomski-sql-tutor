"""Testovi za AnthropicClient — mock SDK calls."""

from unittest.mock import MagicMock, patch

import pytest

from scripts.lib.api_client import (
    AnthropicClient,
    AnthropicResponse,
    AnthropicAPIError,
)


@pytest.fixture
def fake_sdk_response():
    """Mock anthropic.types.Message response."""
    msg = MagicMock()
    msg.content = [MagicMock(text='{"foo": "bar"}')]
    msg.usage = MagicMock(
        input_tokens=100, output_tokens=50, cache_read_input_tokens=80
    )
    msg.stop_reason = "end_turn"
    return msg


def test_generate_returns_anthropic_response(fake_sdk_response):
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fake_sdk_response

        client = AnthropicClient(api_key="fake", model="claude-sonnet-4-6")
        resp = client.generate(system="sys", user_message="usr")

        assert isinstance(resp, AnthropicResponse)
        assert resp.content == '{"foo": "bar"}'
        assert resp.input_tokens == 100
        assert resp.output_tokens == 50
        assert resp.cached_tokens == 80
        assert resp.stop_reason == "end_turn"


def test_rate_limit_triggers_retry_then_succeeds(fake_sdk_response):
    from anthropic import RateLimitError as RLE

    rate_err = RLE(message="rate", response=MagicMock(status_code=429), body=None)

    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.side_effect = [
            rate_err,
            rate_err,
            fake_sdk_response,
        ]
        with patch("scripts.lib.api_client.time.sleep"):
            client = AnthropicClient(api_key="fake")
            resp = client.generate(system="s", user_message="u")
            assert resp.content == '{"foo": "bar"}'


def test_auth_error_raises_immediately():
    from anthropic import APIStatusError

    auth_err = APIStatusError(
        message="unauthorized", response=MagicMock(status_code=401), body=None
    )

    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.side_effect = auth_err
        client = AnthropicClient(api_key="fake")
        with pytest.raises(AnthropicAPIError, match="401"):
            client.generate(system="s", user_message="u")


def test_extended_thinking_adds_thinking_param(fake_sdk_response):
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fake_sdk_response
        client = AnthropicClient(api_key="fake")
        client.generate(system="s", user_message="u", extended_thinking=True)

        kwargs = MockSDK.return_value.messages.create.call_args.kwargs
        assert "thinking" in kwargs
        assert kwargs["thinking"]["budget_tokens"] == 2000


def test_system_prompt_is_cached(fake_sdk_response):
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fake_sdk_response
        client = AnthropicClient(api_key="fake")
        client.generate(system="cacheable_sys", user_message="u")

        kwargs = MockSDK.return_value.messages.create.call_args.kwargs
        sys_block = kwargs["system"][0]
        assert sys_block["cache_control"] == {"type": "ephemeral"}


# ============================================================
# generate_structured_output() — Korak 2 iz 2B-1B
# ============================================================

from scripts.lib.api_client import StructuredOutputResponse, StructuredOutputError


@pytest.fixture
def fake_tool_use_response():
    """Mock Anthropic response s tool_use blokom."""
    block = MagicMock()
    block.type = "tool_use"
    block.input = {"concept_code": "test_concept", "tier": "easy"}

    msg = MagicMock()
    msg.content = [block]
    msg.usage = MagicMock(
        input_tokens=200, output_tokens=100, cache_read_input_tokens=150
    )
    msg.stop_reason = "tool_use"
    return msg


@pytest.fixture
def fake_text_only_response():
    """Mock Anthropic response s text blokom (nema tool_use)."""
    block = MagicMock()
    block.type = "text"

    msg = MagicMock()
    msg.content = [block]
    msg.usage = MagicMock(input_tokens=50, output_tokens=20, cache_read_input_tokens=0)
    msg.stop_reason = "end_turn"
    return msg


def test_generate_structured_output_happy_path(fake_tool_use_response):
    """Tool_use response → StructuredOutputResponse s parsed dict."""
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fake_tool_use_response
        client = AnthropicClient(api_key="fake")
        resp = client.generate_structured_output(
            system="sys",
            user_message="generate",
            output_schema={"type": "object"},
        )
        assert isinstance(resp, StructuredOutputResponse)
        assert resp.parsed == {"concept_code": "test_concept", "tier": "easy"}
        assert resp.input_tokens == 200
        assert resp.output_tokens == 100
        assert resp.cached_tokens == 150


def test_generate_structured_output_no_tool_use_raises(fake_text_only_response):
    """Ako model ne pozove tool, diže StructuredOutputError."""
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fake_text_only_response
        client = AnthropicClient(api_key="fake")
        with pytest.raises(StructuredOutputError, match="did not invoke tool"):
            client.generate_structured_output(
                system="sys",
                user_message="generate",
                output_schema={"type": "object"},
            )


def test_structured_output_uses_cache_control(fake_tool_use_response):
    """System prompt se šalje s cache_control ephemeral."""
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fake_tool_use_response
        client = AnthropicClient(api_key="fake")
        client.generate_structured_output(
            system="cached_sys", user_message="u", output_schema={}
        )
        kwargs = MockSDK.return_value.messages.create.call_args.kwargs
        sys_block = kwargs["system"][0]
        assert sys_block["cache_control"] == {"type": "ephemeral"}
        assert sys_block["text"] == "cached_sys"


def test_structured_output_model_agnostic(fake_tool_use_response):
    """generate_structured_output koristi self.model (ne hardcode)."""
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fake_tool_use_response
        client = AnthropicClient(api_key="fake", model="claude-opus-4-7")
        client.generate_structured_output(
            system="s", user_message="u", output_schema={}
        )
        kwargs = MockSDK.return_value.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-opus-4-7"


def test_structured_output_tool_choice_forced(fake_tool_use_response):
    """tool_choice je forced na konkretni tool_name — garantira structured output."""
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = fake_tool_use_response
        client = AnthropicClient(api_key="fake")
        client.generate_structured_output(
            system="s",
            user_message="u",
            output_schema={},
            tool_name="my_tool",
        )
        kwargs = MockSDK.return_value.messages.create.call_args.kwargs
        assert kwargs["tool_choice"] == {"type": "tool", "name": "my_tool"}
        assert kwargs["tools"][0]["name"] == "my_tool"


def test_structured_output_api_error_wrapped_as_anthropic_api_error():
    """APIStatusError iz SDK-a se wrap-a u AnthropicAPIError."""
    from anthropic import APIStatusError

    api_err = APIStatusError(
        message="server error", response=MagicMock(status_code=500), body=None
    )
    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.side_effect = api_err
        client = AnthropicClient(api_key="fake")
        with pytest.raises(AnthropicAPIError, match="500"):
            client.generate_structured_output(
                system="s", user_message="u", output_schema={}
            )


def test_structured_output_mixed_content_extracts_tool_use():
    """Content lista s text + tool_use blokom — tool_use se ispravno parsira."""
    text_block = MagicMock()
    text_block.type = "text"

    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {"key": "value"}

    msg = MagicMock()
    msg.content = [text_block, tool_block]
    msg.usage = MagicMock(input_tokens=100, output_tokens=50, cache_read_input_tokens=0)
    msg.stop_reason = "tool_use"

    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = msg
        client = AnthropicClient(api_key="fake")
        resp = client.generate_structured_output(
            system="s", user_message="u", output_schema={}
        )
        assert resp.parsed == {"key": "value"}


def test_generate_skips_thinking_block_extracts_text():
    """ThinkingBlock kao content[0] ne smije puknut — uzima prvi blok s .text."""
    thinking_block = MagicMock(spec=[])  # nema .text atribut
    text_block = MagicMock()
    text_block.text = '{"result": 42}'

    msg = MagicMock()
    msg.content = [thinking_block, text_block]
    msg.usage = MagicMock(input_tokens=50, output_tokens=30, cache_read_input_tokens=0)
    msg.stop_reason = "end_turn"

    with patch("scripts.lib.api_client.Anthropic") as MockSDK:
        MockSDK.return_value.messages.create.return_value = msg
        client = AnthropicClient(api_key="fake")
        resp = client.generate(system="s", user_message="u")
        assert resp.content == '{"result": 42}'
