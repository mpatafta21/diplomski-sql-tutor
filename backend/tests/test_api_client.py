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
