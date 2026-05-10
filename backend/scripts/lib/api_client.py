"""Tanak wrapper oko Anthropic SDK-a."""

from __future__ import annotations

import time
from dataclasses import dataclass

from anthropic import Anthropic, APIError, APIStatusError, RateLimitError


class AnthropicAPIError(RuntimeError):
    """Raise-a se nakon iscrpljivanja retry-eva ili na non-retriable greške."""


class StructuredOutputError(Exception):
    """Raised kada model ne pozove tool ili response nije parseable."""


@dataclass
class AnthropicResponse:
    content: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    stop_reason: str


@dataclass(frozen=True)
class StructuredOutputResponse:
    """Response od structured output poziva (tool_use pattern)."""

    parsed: dict
    input_tokens: int
    output_tokens: int
    cached_tokens: int


# Sonnet 4.6 cijene (USD per 1M tokena). Korišteno za cost estimate u CLI.
INPUT_COST_PER_MTOK = 3.0
OUTPUT_COST_PER_MTOK = 15.0
CACHE_READ_DISCOUNT = 0.10  # cached read = 10% input cijene


class AnthropicClient:
    # CLI-level retry. SDK ima eksplicitno postavljen max_retries=2 (3 ukupno),
    # pa je layered worst case 3 SDK x 3 CLI = 9 poziva. CLI retry je primarno
    # za schema/validation failure-e, ne za API rate-limit (to SDK pokriva).
    DEFAULT_MAX_RETRIES = 3
    BACKOFF_BASE_SECONDS = 1.0

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None:
        # Eksplicitno postavi SDK retry cap-a — default je 2, ali make-ing intent jasan.
        self.client = Anthropic(api_key=api_key, max_retries=2)
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

    def generate_structured_output(
        self,
        system: str,
        user_message: str,
        output_schema: dict,
        tool_name: str = "generate_output",
        tool_description: str = "Generate structured output matching the schema.",
        max_tokens: int = 8192,
    ) -> StructuredOutputResponse:
        """
        Strukturirani output kroz Anthropic tool_use pattern.

        tool_choice={"type":"tool","name":tool_name} forsira upotrebu konkretnog
        tool-a — garantira parseabilan structured JSON output bez retry-a na
        format razini. Retry strategiju određuje caller.

        Raises:
            StructuredOutputError: Ako model ne pozove tool.
            AnthropicAPIError: Na API greške (propagira iz SDK-a).
        """
        tool = {
            "name": tool_name,
            "description": tool_description,
            "input_schema": output_schema,
        }

        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_name},
        )

        tool_use_block = next(
            (b for b in msg.content if b.type == "tool_use"),
            None,
        )
        if tool_use_block is None:
            raise StructuredOutputError(
                f"Model did not invoke tool '{tool_name}'. "
                f"Stop reason: {msg.stop_reason}"
            )

        return StructuredOutputResponse(
            parsed=tool_use_block.input,
            input_tokens=getattr(msg.usage, "input_tokens", 0),
            output_tokens=getattr(msg.usage, "output_tokens", 0),
            cached_tokens=getattr(msg.usage, "cache_read_input_tokens", 0) or 0,
        )
