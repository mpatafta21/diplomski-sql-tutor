"""Runtime LLM klijent (Faza 5.1, D1) — bez ijednog stvarnog poziva.

🔴 Svaki test ovdje MOCKA `anthropic.Anthropic`. Nula potrošnje. Test koji bi
stvarno zvao providera ne smije ući u suite: `pytest` se pokreće prije evaluacije
(`make preflight` red), pa bi tiho trošio kredit i novac na svakom pokretanju.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from agents.hint_llm import (
    SYSTEM_PROMPT,
    HintLLMError,
    build_user_message,
    generate_hint,
)
from app.core import config

_PAYLOAD = {
    "task_description": "Za svaki category_id ispiši broj proizvoda.",
    "concept": "group_by",
    "mastery": "nisko",
    "error_type": "row_mismatch",
    "error_detail": "Row count mismatch: actual=30 vs expected=3",
}


def _fake_anthropic(text: str = "Provjeri GROUP BY klauzulu.") -> tuple:
    """Vrati (modul, klijent) s minimalnim SDK oblikom."""
    blok = types.SimpleNamespace(text=text)
    poruka = types.SimpleNamespace(
        content=[blok], usage=types.SimpleNamespace(input_tokens=120, output_tokens=40)
    )
    klijent = MagicMock()
    klijent.messages.create.return_value = poruka
    modul = types.ModuleType("anthropic")
    modul.Anthropic = MagicMock(return_value=klijent)
    return modul, klijent


# ---------------------------------------------------------------------------
# Poruka prema modelu
# ---------------------------------------------------------------------------


def test_user_message_carries_only_payload_fields() -> None:
    msg = build_user_message(_PAYLOAD)
    assert "group_by" in msg
    assert "nisko" in msg
    assert "Row count mismatch" in msg
    # Ono čega u payloadu nema ne smije se pojaviti ni u poruci.
    assert "SELECT" not in msg.upper().replace("ISPIŠI", "")


def test_system_prompt_forbids_giving_the_solution() -> None:
    assert "NIKAD ne piši gotov SQL upit" in SYSTEM_PROMPT
    assert "HRVATSKOM" in SYSTEM_PROMPT
    # 🔴 Modelu se izrijekom kaže da studentov upit NE dobiva — da ga ne izmišlja.
    assert "NE dobivaš studentov upit" in SYSTEM_PROMPT


def test_optional_fields_appear_only_when_present() -> None:
    bez = build_user_message({k: v for k, v in _PAYLOAD.items() if k != "error_detail"})
    assert "Pojedinost o grešci" not in bez

    sa_sqlstate = build_user_message({**_PAYLOAD, "sqlstate": "42703"})
    assert "42703" in sa_sqlstate

    sa_stupcima = build_user_message(
        {**_PAYLOAD, "expected_columns": ["broj_proizvoda", "category_id"]}
    )
    assert "broj_proizvoda, category_id" in sa_stupcima


# ---------------------------------------------------------------------------
# Ugovor poziva
# ---------------------------------------------------------------------------


def test_generate_hint_uses_no_retries_and_explicit_timeout() -> None:
    """🔴 Odluka 1 (`max_retries=0`) i granica prema GATEWAY_TIMEOUT-u.

    SDK default je 2 retryja i timeout od 10 minuta — oboje bi probilo budžet.
    """
    modul, klijent = _fake_anthropic()
    with patch.dict(sys.modules, {"anthropic": modul}):
        res = generate_hint(_PAYLOAD)

    kwargs = modul.Anthropic.call_args.kwargs
    assert kwargs["max_retries"] == 0
    assert kwargs["timeout"] == config.HINT_LLM_TIMEOUT
    assert config.HINT_LLM_TIMEOUT < config.GATEWAY_TIMEOUT
    assert klijent.messages.create.call_count == 1
    assert res.text == "Provjeri GROUP BY klauzulu."


def test_generate_hint_uses_configured_model() -> None:
    modul, klijent = _fake_anthropic()
    with patch.dict(sys.modules, {"anthropic": modul}):
        generate_hint(_PAYLOAD)
    assert klijent.messages.create.call_args.kwargs["model"] == config.HINT_LLM_MODEL
    assert "haiku" in config.HINT_LLM_MODEL


def test_failure_raises_and_does_not_retry() -> None:
    """Pad → jedan poziv, `HintLLMError`. Pozivatelj ide na fallback."""
    modul, klijent = _fake_anthropic()
    klijent.messages.create.side_effect = RuntimeError("503 overloaded")
    with patch.dict(sys.modules, {"anthropic": modul}), pytest.raises(HintLLMError):
        generate_hint(_PAYLOAD)
    assert klijent.messages.create.call_count == 1


def test_empty_response_is_a_failure_not_an_empty_hint() -> None:
    """Prazan tekst ne smije proći kao hint — student bi dobio prazan okvir."""
    modul, _ = _fake_anthropic(text="   ")
    with patch.dict(sys.modules, {"anthropic": modul}), pytest.raises(HintLLMError):
        generate_hint(_PAYLOAD)


def test_missing_api_key_fails_before_constructing_client() -> None:
    """Bez ključa nema ni pokušaja — nula odlaznih poziva."""
    modul, _ = _fake_anthropic()
    with patch.object(config, "ANTHROPIC_API_KEY", ""), patch.dict(
        sys.modules, {"anthropic": modul}
    ):
        with pytest.raises(HintLLMError, match="ANTHROPIC_API_KEY"):
            generate_hint(_PAYLOAD)
    modul.Anthropic.assert_not_called()
