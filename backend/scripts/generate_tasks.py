"""CLI entrypoint za generator SQL zadataka — Faza 2A.

Usage:
    cd backend && uv run python -m scripts.generate_tasks \\
        --concept inner_join --difficulty 2 --count 1 --dry-run \\
        --output-dir ../data/generated_tasks/
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from app.schemas.generated_task import GeneratedTask, GeneratedTaskMeta
from scripts.lib.api_client import (
    CACHE_READ_DISCOUNT,
    INPUT_COST_PER_MTOK,
    OUTPUT_COST_PER_MTOK,
    AnthropicAPIError,
    AnthropicClient,
)
from scripts.lib.ast_analyzer import AstAnalyzer
from scripts.lib.json_extract import JsonExtractionError, extract_json
from scripts.lib.prompt_builder import PromptBuilder
from scripts.lib.sandbox_runner import SandboxRunner
from scripts.lib.task_validator import TaskValidator


MAX_RETRIES_DEFAULT = 3
MODEL_DEFAULT = "claude-sonnet-4-6"


def _build_pipeline(backend_root: Path, api_key: str, model: str):
    builder = PromptBuilder(
        concepts_config_dir=backend_root / "config" / "concepts",
        sandbox_context_path=backend_root / "config" / "sandbox_context.yaml",
        templates_dir=backend_root / "config" / "prompt_templates",
    )
    api = AnthropicClient(api_key=api_key, model=model)
    sandbox_url = os.environ.get(
        "SANDBOX_DATABASE_URL",
        "postgresql+psycopg://sandbox_admin:sandbox_dev_password@localhost:5433/sandbox",
    ).replace("postgresql+psycopg://", "postgresql://")
    runner = SandboxRunner(connection_string=sandbox_url, timeout_seconds=5)
    analyzer = AstAnalyzer()
    validator = TaskValidator(sandbox_runner=runner, ast_analyzer=analyzer)
    return builder, api, validator


def generate_one(
    builder: PromptBuilder,
    api: AnthropicClient,
    validator: TaskValidator,
    concept: str,
    difficulty: int,
    extended_thinking: bool | None = None,
    max_retries: int = MAX_RETRIES_DEFAULT,
    logger: logging.Logger | None = None,
) -> tuple[GeneratedTaskMeta | None, list[dict]]:
    """Generira 1 zadatak. Vraća (meta, list-of-failure-records)."""
    log = logger or logging.getLogger(__name__)
    use_thinking = (
        extended_thinking if extended_thinking is not None else (difficulty >= 4)
    )

    failures: list[dict] = []
    last_meta: GeneratedTaskMeta | None = None

    for attempt in range(max_retries):
        log.info(
            "Attempt %d/%d for %s d=%d", attempt + 1, max_retries, concept, difficulty
        )
        prompt = builder.build(concept, difficulty)

        try:
            response = api.generate(
                system=prompt.system,
                user_message=prompt.user,
                extended_thinking=use_thinking,
            )
        except AnthropicAPIError as e:
            failures.append({"attempt": attempt, "stage": "api", "error": str(e)})
            log.error("API error on attempt %d: %s", attempt, e)
            continue

        try:
            raw_json = extract_json(response.content)
            task = GeneratedTask.model_validate_json(raw_json)
        except (JsonExtractionError, ValidationError) as e:
            failures.append(
                {"attempt": attempt, "stage": "schema", "error": str(e)[:500]}
            )
            log.warning("Schema/parse error on attempt %d: %s", attempt, e)
            continue

        validation = validator.validate(task)
        meta = GeneratedTaskMeta(
            task=task,
            generation_id=str(uuid.uuid4()),
            api_input_tokens=response.input_tokens,
            api_output_tokens=response.output_tokens,
            api_cached_tokens=response.cached_tokens,
            retries=attempt,
            validation_passed=validation.passed,
            validation_failures=[
                {
                    "level": f.level,
                    "code": f.code,
                    "message": f.message,
                    "details": f.details,
                }
                for f in validation.failures
            ],
            generated_at=datetime.now(timezone.utc).isoformat(),
            model_used=api.model,
            extended_thinking=use_thinking,
        )
        last_meta = meta

        if validation.passed:
            log.info("Validation PASSED on attempt %d", attempt)
            return meta, failures

        failures.append(
            {
                "attempt": attempt,
                "stage": "validation",
                "errors": meta.validation_failures,
            }
        )
        log.warning(
            "Validation FAILED on attempt %d: %s",
            attempt,
            meta.validation_failures,
        )

    return last_meta, failures


def estimate_cost_usd(
    input_tokens: int, output_tokens: int, cached_tokens: int
) -> float:
    """Procjena USD troška za jedan API call (Sonnet 4.6 cijene)."""
    fresh_input = max(0, input_tokens - cached_tokens)
    return (
        fresh_input * INPUT_COST_PER_MTOK / 1e6
        + cached_tokens * INPUT_COST_PER_MTOK * CACHE_READ_DISCOUNT / 1e6
        + output_tokens * OUTPUT_COST_PER_MTOK / 1e6
    )


def save_meta(meta: GeneratedTaskMeta, output_dir: Path, status: str) -> Path:
    """Sprema meta u {output_dir}/{status}/{concept}_d{difficulty}_{uuid}.json."""
    target_dir = output_dir / status
    target_dir.mkdir(parents=True, exist_ok=True)
    fname = (
        f"{meta.task.primary_concept}_d{meta.task.difficulty}_"
        f"{meta.generation_id[:8]}.json"
    )
    path = target_dir / fname
    path.write_text(meta.model_dump_json(indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generator SQL zadataka (Faza 2A)")
    parser.add_argument("--concept", required=True, help="Concept code (npr. inner_join)")
    parser.add_argument("--difficulty", type=int, choices=[1, 2, 3, 4, 5], default=2)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/generated_tasks")
    )
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES_DEFAULT)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip DB write (Faza 2A default — ne piše u tasks tablicu)",
    )
    parser.add_argument("--no-extended-thinking", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--model", default=MODEL_DEFAULT)
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    log = logging.getLogger("generate_tasks")

    backend_root = Path(__file__).resolve().parents[1]
    load_dotenv(backend_root / ".env")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY nije postavljen u .env")
        return 2

    builder, api, validator = _build_pipeline(backend_root, api_key, args.model)

    extended = None if not args.no_extended_thinking else False

    success_count = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cached_tokens = 0

    for i in range(args.count):
        log.info(
            "=== Generating task %d/%d (%s, d=%d) ===",
            i + 1,
            args.count,
            args.concept,
            args.difficulty,
        )
        meta, _failures = generate_one(
            builder=builder,
            api=api,
            validator=validator,
            concept=args.concept,
            difficulty=args.difficulty,
            extended_thinking=extended,
            max_retries=args.max_retries,
            logger=log,
        )

        if meta is None:
            log.error(
                "Task %d: no meta produced after %d retries", i, args.max_retries
            )
            continue

        total_input_tokens += meta.api_input_tokens
        total_output_tokens += meta.api_output_tokens
        total_cached_tokens += meta.api_cached_tokens
        task_cost = estimate_cost_usd(
            meta.api_input_tokens, meta.api_output_tokens, meta.api_cached_tokens
        )
        log.info(
            "Task %d cost ~$%.4f (in=%d out=%d cached=%d)",
            i + 1,
            task_cost,
            meta.api_input_tokens,
            meta.api_output_tokens,
            meta.api_cached_tokens,
        )

        if meta.validation_passed:
            path = save_meta(meta, args.output_dir, "validated")
            log.info("[OK] Saved to %s", path)
            success_count += 1
        else:
            path = save_meta(meta, args.output_dir, "failed")
            log.warning("[FAIL] Failed validation; saved to %s", path)

    total_cost = estimate_cost_usd(
        total_input_tokens, total_output_tokens, total_cached_tokens
    )
    log.info("=" * 60)
    log.info("SUMMARY: %d/%d success", success_count, args.count)
    log.info(
        "Tokens: input=%d output=%d cached=%d",
        total_input_tokens,
        total_output_tokens,
        total_cached_tokens,
    )
    log.info(
        "Estimated total cost: $%.4f (avg $%.4f/task)",
        total_cost,
        total_cost / max(args.count, 1),
    )
    return 0 if success_count == args.count else 1


if __name__ == "__main__":
    sys.exit(main())
