"""
Meta-generation helpers — generira concept YAML config kroz Anthropic
tool-use API koristeći postojeće YAML-ove kao few-shot primjere.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.schemas.concept_config import ConceptConfig, load_concept_config
from scripts.lib.api_client import AnthropicClient, StructuredOutputResponse

# Cost mirrored from api_client.py constants
_INPUT_COST_PER_MTOK = 3.0
_OUTPUT_COST_PER_MTOK = 15.0
_CACHE_READ_DISCOUNT = 0.10


def _estimate_cost(input_tokens: int, output_tokens: int, cached_tokens: int) -> float:
    uncached = max(0, input_tokens - cached_tokens)
    return (
        uncached * _INPUT_COST_PER_MTOK / 1_000_000
        + cached_tokens * _INPUT_COST_PER_MTOK * _CACHE_READ_DISCOUNT / 1_000_000
        + output_tokens * _OUTPUT_COST_PER_MTOK / 1_000_000
    )


def collect_few_shot_yamls(concepts_dir: Path) -> dict[str, str]:
    """Učitava sve *.yaml iz concepts_dir kao {stem: raw_text} za few-shot."""
    return {
        p.stem: p.read_text(encoding="utf-8")
        for p in sorted(concepts_dir.glob("*.yaml"))
    }


def build_meta_gen_prompts(
    target_concept_code: str,
    target_concept_meta: dict[str, Any],
    few_shot_examples: dict[str, str],
    schema_error_feedback: str | None = None,
) -> tuple[str, str]:
    """
    Gradi (system, user) prompt par za jedan concept YAML.

    Args:
        target_concept_code: Šifra koncepta koji se generira (npr. "where_filter").
        target_concept_meta: Dict s module_number, module_name, tier, description.
        few_shot_examples: {concept_code: raw_yaml_text} — ubacuju se u system prompt.
        schema_error_feedback: Ako je prethodni pokušaj fail-ao, ovdje ide error
            poruka za retry guidance.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    few_shot_block = "\n\n".join(
        f"--- PRIMJER: {code} ---\n{yaml_text.rstrip()}"
        for code, yaml_text in few_shot_examples.items()
    )

    system = (
        "Ti si ekspert za SQL edukaciju koji generira YAML config fajlove za SQL koncepte.\n\n"
        "Svaki config mora imati ova polja:\n"
        "  - concept_code: snake_case, jedinstven identifikator koncepta\n"
        "  - concept_name: puni naziv koncepta (npr. 'WHERE klauza')\n"
        "  - module_number: broj modula (0-6)\n"
        "  - module_name: naziv modula\n"
        "  - tier: easy, medium ili hard\n"
        "  - target_misconceptions: lista grešaka (min 1) s code, description, priority\n"
        "  - domain_hints: lista savjeta vezanih uz sandbox shemu (min 1)\n"
        "  - anti_patterns: lista čestih loših uzoraka (min 1)\n"
        "  - required_for_high_difficulty: lista zahtjeva za teže verzije zadataka\n"
        "  - few_shot_examples: lista primjera zadataka (min 1) s difficulty 1-5,\n"
        "    title, description, expected_query, expected_concepts, targets_misconception\n"
        "  - ast_validation_rules: lista pravila za AST provjeru (min 1)\n\n"
        "Sandbox baza je PostgreSQL ecommerce_v1 s tablicama: customers, orders, "
        "order_items, products, categories, employees (s manager_id self-referencom).\n\n"
        "Evo primjera dobro napisanih YAML config-ova — prati istu strukturu i razinu detalja:\n\n"
        f"{few_shot_block}"
    )

    meta_lines = "\n".join(f"  {k}: {v}" for k, v in target_concept_meta.items())
    user = (
        f"Generiraj YAML config za SQL koncept '{target_concept_code}'.\n\n"
        f"Meta informacije:\n{meta_lines}\n\n"
        f"Obavezno:\n"
        f"  - concept_code mora biti točno: {target_concept_code}\n"
        f"  - module_number mora biti: {target_concept_meta.get('module_number', '?')}\n"
        f"  - module_name mora biti: {target_concept_meta.get('module_name', '?')}\n"
        f"  - tier mora biti: {target_concept_meta.get('tier', '?')}\n"
        f"  - expected_query u few_shot_examples mora biti validan SQL za ecommerce_v1 bazu"
    )

    if schema_error_feedback is not None:
        user += (
            f"\n\n⚠ SCHEMA ERROR iz prethodnog pokušaja — molim ispravi:\n"
            f"{schema_error_feedback}\n\n"
            "Generiraj ispravni config koji prolazi schema validaciju."
        )

    return system, user


def parse_and_validate(
    response_parsed: dict,
    output_dir: Path,
) -> tuple[ConceptConfig | None, str | None]:
    """
    Validira parsed dict kroz ConceptConfig, piše YAML fajl ako prolazi.

    Returns:
        (config, None) ako validan; (None, error_msg) ako schema fail-a.

    Note:
        Drugi exception tipovi (RuntimeError, OSError, ...) propagiraju —
        ne ulaze u retry loop kao "Schema validation failed". Roundtrip-check
        piše u temp fajl pa atomic-rename → corrupt YAML nikad ne ostaje na disku.
    """
    try:
        config = ConceptConfig.model_validate(response_parsed)
    except ValidationError as exc:
        return None, f"Schema validation failed: {exc}"

    yaml_path = output_dir / f"{config.concept_code}.yaml"
    tmp_path = yaml_path.with_suffix(".yaml.tmp")
    yaml_text = yaml.safe_dump(
        config.model_dump(),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    tmp_path.write_text(yaml_text, encoding="utf-8")

    try:
        # Paranoia roundtrip — potvrđuje da YAML prolazi load_concept_config
        reloaded = load_concept_config(tmp_path)
        assert reloaded.concept_code == config.concept_code, (
            f"roundtrip mismatch: {reloaded.concept_code} != {config.concept_code}"
        )
    except BaseException:
        # Bilo koja greška (AssertionError, parser fail, ...) → očisti temp
        tmp_path.unlink(missing_ok=True)
        raise

    tmp_path.replace(yaml_path)  # atomic na POSIX-u
    return config, None


def generate_one_yaml(
    client: AnthropicClient,
    concept_code: str,
    concept_meta: dict,
    few_shot_examples: dict[str, str],
    output_dir: Path,
    max_retries: int = 1,
) -> dict:
    """
    Generira jedan YAML config. 1× auto-retry s schema feedback ako fail-a.

    Returns:
        {
            "status": "success" | "manual_review",
            "concept_code": str,
            "attempts": int,
            "cost_usd": float,
            "error": str | None,
        }
    """
    schema = ConceptConfig.model_json_schema()
    error_feedback: str | None = None
    total_cost = 0.0

    for attempt in range(max_retries + 1):
        system, user = build_meta_gen_prompts(
            concept_code,
            concept_meta,
            few_shot_examples,
            schema_error_feedback=error_feedback,
        )
        resp: StructuredOutputResponse = client.generate_structured_output(
            system=system,
            user_message=user,
            output_schema=schema,
        )
        total_cost += _estimate_cost(resp.input_tokens, resp.output_tokens, resp.cached_tokens)

        config, err = parse_and_validate(resp.parsed, output_dir)
        if config is not None:
            return {
                "status": "success",
                "concept_code": concept_code,
                "attempts": attempt + 1,
                "cost_usd": total_cost,
                "error": None,
            }

        error_feedback = err

    return {
        "status": "manual_review",
        "concept_code": concept_code,
        "attempts": max_retries + 1,
        "cost_usd": total_cost,
        "error": error_feedback,
    }
