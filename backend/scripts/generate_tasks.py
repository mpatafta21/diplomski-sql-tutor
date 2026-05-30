"""CLI entrypoint za generator SQL zadataka — Faza 2A.

Usage:
    cd backend && uv run python -m scripts.generate_tasks \\
        --concept inner_join --difficulty 2 --count 1 --dry-run \\
        --output-dir ../data/generated_tasks/
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
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
MAX_RETRIES_AGGREGATIONS = 5  # M2 (per 2B-1E memory note)
MODULE_BUDGET_USD_DEFAULT = 1.50
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
    dml: bool = False,
) -> tuple[GeneratedTaskMeta | None, list[dict]]:
    """Generira 1 zadatak. Vraća (meta, list-of-failure-records).

    Args:
        dml: True za INSERT/UPDATE/DELETE koncepte. Propagira u
            validator.validate(..., dml=True) → SandboxRunner.execute(..., dml=True)
            → SET ROLE sandbox_readwrite + rollback. Default False (SELECT path,
            sandbox_readonly role).
    """
    log = logger or logging.getLogger(__name__)
    # 2B-1E: always-on default (lessons learned iz 2B-1D Iter 2 — 5x improvement).
    # Eksplicitan extended_thinking=False ostaje supported (npr. za testove ili
    # ako se kasnije pokaže da je trošak previsok za d=1 batch).
    use_thinking = extended_thinking if extended_thinking is not None else True

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

        validation = validator.validate(task, dml=dml)
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


# ─── Batch mode (2B-2) ────────────────────────────────────────────────────────


def load_distribution_matrix(matrix_path: Path) -> dict[str, Any]:
    """Učitaj distribucijsku matricu iz YAML-a.

    Returns dict with structure: {"modules": {0: {"name": str, "concepts": {code: {tier, distribution, dml?}}}}}
    Throws yaml.YAMLError ili FileNotFoundError ako fajl ne postoji ili je malformed.
    """
    raw = yaml.safe_load(Path(matrix_path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "modules" not in raw:
        raise ValueError(f"Matrix YAML mora imati top-level 'modules' ključ: {matrix_path}")
    return raw


def _iter_matrix_plan(
    matrix: dict[str, Any],
    only_module: int | None,
    skip_concepts: set[str],
) -> list[tuple[int, str, dict[str, Any], int, int]]:
    """Razviju matricu u plan: [(module_num, concept_code, concept_data, difficulty, count_idx), ...].

    Filtrira po `only_module` (None = svi) i `skip_concepts` (set kodova za skip).
    Concept-i s `dml: true` se propagiraju kroz concept_data.
    """
    plan: list[tuple[int, str, dict[str, Any], int, int]] = []
    modules = matrix["modules"]
    module_nums = [only_module] if only_module is not None else sorted(modules.keys())

    for mod_num in module_nums:
        if mod_num not in modules:
            continue
        mod_data = modules[mod_num]
        for concept_code, concept_data in mod_data["concepts"].items():
            if concept_code in skip_concepts:
                continue
            distribution = concept_data.get("distribution", {})
            for difficulty in sorted(distribution.keys()):
                count = distribution[difficulty]
                for i in range(count):
                    plan.append((mod_num, concept_code, concept_data, int(difficulty), i))
    return plan


def batch_generate_from_matrix(
    builder: PromptBuilder,
    api: AnthropicClient,
    validator: TaskValidator,
    matrix: dict[str, Any],
    output_dir: Path,
    only_module: int | None = None,
    skip_concepts: set[str] | None = None,
    module_budget_usd: float = MODULE_BUDGET_USD_DEFAULT,
    logger: logging.Logger | None = None,
    interactive: bool = True,
) -> dict[str, Any]:
    """Batch generation kroz distribucijsku matricu.

    Per-modul soft cap (module_budget_usd) — abort modul ako trošak pređe,
    pause na interactive=True (`input()` waits for user).

    Returns batch_report dict s per-modul stats + global totals.
    """
    log = logger or logging.getLogger("batch_generate")
    skip_concepts = skip_concepts or set()

    report: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "matrix_module_filter": only_module,
        "skip_concepts": sorted(skip_concepts),
        "module_budget_usd": module_budget_usd,
        "modules": {},
        "total_cost_usd": 0.0,
        "total_validated": 0,
        "total_failed": 0,
    }

    modules = matrix["modules"]
    module_nums = [only_module] if only_module is not None else sorted(modules.keys())

    for mod_num in module_nums:
        if mod_num not in modules:
            log.warning("Module %s nije u matrici, preskačem", mod_num)
            continue
        mod_data = modules[mod_num]
        mod_report: dict[str, Any] = {
            "name": mod_data["name"],
            "concepts": {},
            "module_cost_usd": 0.0,
            "validated": 0,
            "failed": 0,
            "aborted": False,
        }
        # M2 (agregacije) dobiju veći retry budget (per 2B-1E memory note)
        max_retries = MAX_RETRIES_AGGREGATIONS if mod_num == 2 else MAX_RETRIES_DEFAULT

        log.info("=" * 60)
        log.info("Module %d — %s (max_retries=%d)", mod_num, mod_data["name"], max_retries)
        log.info("=" * 60)

        for concept_code, concept_data in mod_data["concepts"].items():
            if concept_code in skip_concepts:
                log.info("⊘ Skipping %s (--skip-concepts)", concept_code)
                continue
            distribution = concept_data.get("distribution", {})
            dml = bool(concept_data.get("dml", False))
            concept_stats = {"validated": 0, "failed": 0, "cost_usd": 0.0}

            for difficulty in sorted(distribution.keys()):
                count = distribution[difficulty]
                for i in range(count):
                    if mod_report["module_cost_usd"] >= module_budget_usd:
                        log.warning(
                            "⚠ Module %d cost $%.4f ≥ cap $%.2f. Aborting module.",
                            mod_num,
                            mod_report["module_cost_usd"],
                            module_budget_usd,
                        )
                        mod_report["aborted"] = True
                        break

                    log.info(
                        "[M%d/%s/d%d/%d] generating...",
                        mod_num,
                        concept_code,
                        difficulty,
                        i + 1,
                    )
                    meta, _failures = generate_one(
                        builder=builder,
                        api=api,
                        validator=validator,
                        concept=concept_code,
                        difficulty=int(difficulty),
                        max_retries=max_retries,
                        logger=log,
                        dml=dml,
                    )

                    if meta is None:
                        log.error(
                            "[M%d/%s/d%d/%d] no meta after %d retries",
                            mod_num,
                            concept_code,
                            difficulty,
                            i + 1,
                            max_retries,
                        )
                        concept_stats["failed"] += 1
                        mod_report["failed"] += 1
                        continue

                    task_cost = estimate_cost_usd(
                        meta.api_input_tokens,
                        meta.api_output_tokens,
                        meta.api_cached_tokens,
                    )
                    concept_stats["cost_usd"] += task_cost
                    mod_report["module_cost_usd"] += task_cost

                    status = "validated" if meta.validation_passed else "failed"
                    save_meta(meta, output_dir, status)
                    log.info(
                        "[M%d/%s/d%d/%d] %s ($%.4f, %d retries)",
                        mod_num,
                        concept_code,
                        difficulty,
                        i + 1,
                        status,
                        task_cost,
                        meta.retries,
                    )

                    if meta.validation_passed:
                        concept_stats["validated"] += 1
                        mod_report["validated"] += 1
                    else:
                        concept_stats["failed"] += 1
                        mod_report["failed"] += 1
                if mod_report["aborted"]:
                    break
            if mod_report["aborted"]:
                break

            mod_report["concepts"][concept_code] = concept_stats

        report["modules"][mod_num] = mod_report
        report["total_cost_usd"] += mod_report["module_cost_usd"]
        report["total_validated"] += mod_report["validated"]
        report["total_failed"] += mod_report["failed"]

        # Per-module summary
        attempted = mod_report["validated"] + mod_report["failed"]
        pass_rate = mod_report["validated"] / attempted if attempted else 0.0
        log.info(
            "--- Module %d summary: %d/%d validated (%.1f%%), $%.4f ---",
            mod_num,
            mod_report["validated"],
            attempted,
            pass_rate * 100,
            mod_report["module_cost_usd"],
        )
        if mod_report["aborted"] and interactive and only_module is None:
            input(
                f"⚠ Module {mod_num} aborted. Press Enter to continue to next module, "
                "Ctrl+C to abort all..."
            )

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report_path = output_dir / "batch_report.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log.info("=" * 60)
    log.info(
        "BATCH TOTAL: %d validated, %d failed, $%.4f",
        report["total_validated"],
        report["total_failed"],
        report["total_cost_usd"],
    )
    log.info("Report saved to %s", report_path)
    return report


def _print_dry_run_plan(plan: list[tuple[int, str, dict[str, Any], int, int]]) -> None:
    """Print plan na stdout za --dry-run --from-matrix sanity check."""
    by_module: dict[int, dict[str, list[int]]] = {}
    for mod_num, concept, _, diff, _i in plan:
        by_module.setdefault(mod_num, {}).setdefault(concept, []).append(diff)
    total = 0
    for mod_num in sorted(by_module):
        mod_total = sum(len(v) for v in by_module[mod_num].values())
        total += mod_total
        print(f"\n=== Module {mod_num} ({mod_total} tasks) ===")
        for concept, diffs in by_module[mod_num].items():
            diff_str = ", ".join(f"d{d}" for d in diffs)
            print(f"  {concept}: {len(diffs)} ({diff_str})")
    print(f"\nTOTAL planned: {total} tasks")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generator SQL zadataka (Faza 2A/2B-2)")
    # Single-task mode (Faza 2A) — --concept required ako --from-matrix nije zadan
    parser.add_argument("--concept", help="Concept code (npr. inner_join)")
    parser.add_argument("--difficulty", type=int, choices=[1, 2, 3, 4, 5], default=2)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/generated_tasks")
    )
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES_DEFAULT)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip API/DB; u --from-matrix mode ispiše plan i izlazi.",
    )
    parser.add_argument("--no-extended-thinking", action="store_true")
    parser.add_argument(
        "--dml",
        action="store_true",
        help="Koristi sandbox_readwrite role (INSERT/UPDATE/DELETE koncepti, M4).",
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--model", default=MODEL_DEFAULT)

    # Batch mode (Faza 2B-2)
    parser.add_argument(
        "--from-matrix",
        type=Path,
        help="Put do distribucijske matrice YAML. Triggera batch mode.",
    )
    parser.add_argument(
        "--module",
        type=int,
        choices=[0, 1, 2, 3, 4, 5, 6],
        help="Filtriraj na jedan modul (samo u --from-matrix mode).",
    )
    parser.add_argument(
        "--skip-concepts",
        type=str,
        default="",
        help="Comma-separated concept codes za skip (npr. 'group_by').",
    )
    parser.add_argument(
        "--module-budget-usd",
        type=float,
        default=MODULE_BUDGET_USD_DEFAULT,
        help=f"Per-modul soft cap u USD (default ${MODULE_BUDGET_USD_DEFAULT:.2f}).",
    )

    args = parser.parse_args(argv)

    # Argument cross-validation
    if not args.from_matrix and not args.concept:
        parser.error("Mora se zadati ili --concept (single-task) ili --from-matrix (batch).")

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    log = logging.getLogger("generate_tasks")

    backend_root = Path(__file__).resolve().parents[1]
    load_dotenv(backend_root / ".env")

    # Batch mode: --from-matrix
    if args.from_matrix:
        matrix = load_distribution_matrix(args.from_matrix)
        skip_set = {c.strip() for c in args.skip_concepts.split(",") if c.strip()}

        if args.dry_run:
            plan = _iter_matrix_plan(matrix, args.module, skip_set)
            _print_dry_run_plan(plan)
            return 0

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            log.error("ANTHROPIC_API_KEY nije postavljen u .env")
            return 2

        builder, api, validator = _build_pipeline(backend_root, api_key, args.model)
        report = batch_generate_from_matrix(
            builder=builder,
            api=api,
            validator=validator,
            matrix=matrix,
            output_dir=args.output_dir,
            only_module=args.module,
            skip_concepts=skip_set,
            module_budget_usd=args.module_budget_usd,
            logger=log,
        )
        # Exit 0 ako nema aborted modules, 1 ako jest
        return 0 if not any(m.get("aborted") for m in report["modules"].values()) else 1

    # Single-task mode (Faza 2A)
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
            dml=args.dml,
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
