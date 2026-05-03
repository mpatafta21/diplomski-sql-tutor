"""Tanak wrapper oko Anthropic SDK-a."""

from __future__ import annotations

import time
from dataclasses import dataclass

from anthropic import Anthropic, APIError, APIStatusError, RateLimitError


class AnthropicAPIError(RuntimeError):
    """Raise-a se nakon iscrpljivanja retry-eva ili na non-retriable greške."""


@dataclass
class AnthropicResponse:
    content: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    stop_reason: str


class AnthropicClient:
    DEFAULT_MAX_RETRIES = 3
    BACKOFF_BASE_SECONDS = 1.0

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def generate(
        self,
        system: str,
        user_message: str,
        extended_thinking: bool = False,
        max_tokens: int = 4096,
    ) -> AnthropicResponse:
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            "messages": [{"role": "user", "content": user_message}],
        }
        if extended_thinking:
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": 2000}

        last_error: Exception | None = None
        for attempt in range(self.DEFAULT_MAX_RETRIES):
            try:
                msg = self.client.messages.create(**kwargs)
                return AnthropicResponse(
                    content=msg.content[0].text if msg.content else "",
                    input_tokens=getattr(msg.usage, "input_tokens", 0),
                    output_tokens=getattr(msg.usage, "output_tokens", 0),
                    cached_tokens=getattr(msg.usage, "cache_read_input_tokens", 0)
                    or 0,
                    stop_reason=msg.stop_reason or "unknown",
                )
            except RateLimitError as e:
                last_error = e
                time.sleep(self.BACKOFF_BASE_SECONDS * (2**attempt))
                continue
            except APIStatusError as e:
                if 500 <= e.status_code < 600:
                    last_error = e
                    time.sleep(self.BACKOFF_BASE_SECONDS * (2**attempt))
                    continue
                raise AnthropicAPIError(f"API error {e.status_code}: {e}") from e
            except APIError as e:
                raise AnthropicAPIError(f"API error: {e}") from e

        raise AnthropicAPIError(
            f"Exhausted {self.DEFAULT_MAX_RETRIES} retries; last error: {last_error}"
        )
