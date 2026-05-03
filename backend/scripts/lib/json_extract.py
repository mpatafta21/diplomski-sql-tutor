"""Helper za izvlačenje JSON-a iz LLM tekst response-a."""

import re


class JsonExtractionError(ValueError):
    """Bačeno kad u tekstu nema parsabilnog JSON objekta."""


_CODEBLOCK_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)
_BARE_OBJECT_RE = re.compile(r"(\{.*\})", re.DOTALL)


def extract_json(text: str) -> str:
    """Vrati raw JSON string iz LLM odgovora.

    Pravila redoslijeda:
      1. Markdown ```json ... ``` codeblock
      2. Unlabeled ``` ... ``` codeblock
      3. Prvi balansirani { ... } u tekstu
      4. Inače JsonExtractionError
    """
    if not text or not text.strip():
        raise JsonExtractionError("Prazan tekst — nema JSON-a")

    match = _CODEBLOCK_RE.search(text)
    if match:
        return match.group(1).strip()

    match = _BARE_OBJECT_RE.search(text)
    if match:
        return match.group(1).strip()

    raise JsonExtractionError(f"Nema JSON objekta u tekstu: {text[:80]}...")
