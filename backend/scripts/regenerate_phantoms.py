"""Faza 2B-2.5 Korak 2 — regenerate phantom failures.

Čita `data/generated_tasks/phantoms_to_regenerate.json` (output Koraka 1) i
za svaki (module, concept, difficulty) pokušava generirati 1 task kroz
`generate_one()` iz `generate_tasks.py`. Sandbox running + ANTHROPIC_API_KEY
required.

Budget cap (hard abort):
- $0.50 target
- $0.75 hard abort threshold

Output:
- Save validated → data/generated_tasks/validated/
- Save failed → data/generated_tasks/failed/
- Print pass-rate summary

Pokretanje:
    cd backend && uv run python -m scripts.regenerate_phantoms
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from scripts.generate_tasks import (
    MAX_RETRIES_AGGREGATIONS,
    MAX_RETRIES_DEFAULT,
    _build_pipeline,
    estimate_cost_usd,
    generate_one,
    save_meta,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("regenerate_phantoms")

BUDGET_TARGET_USD = 0.50
BUDGET_ABORT_USD = 0.75

# Koji koncepti trebaju --dml=True flag (insert/update/delete u M4)
DML_CONCEPTS = {"insert", "update", "delete"}


def main() -> int:
    backend_root = Path(__file__).resolve().parents[1]
    repo_root = backend_root.parent
    load_dotenv(backend_root / ".env")

    phantoms_path = repo_root / "data" / "generated_tasks" / "phantoms_to_regenerate.json"
    if not phantoms_path.exists():
        log.error("phantoms_to_regenerate.json not found at %s", phantoms_path)
        log.error("Pokreni prvo: uv run python -m scripts.identify_phantom_failures")
        return 1

    phantoms = json.loads(phantoms_path.read_text(encoding="utf-8"))
    log.info("Loaded %d phantoms to regenerate", len(phantoms))

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY nije postavljen u .env")
        return 2

    output_dir = repo_root / "data" / "generated_tasks"
    builder, api, validator = _build_pipeline(backend_root, api_key, "claude-sonnet-4-6")

    total_cost = 0.0
    validated_count = 0
    failed_count = 0
    aborted = False

    for i, ph in enumerate(phantoms, 1):
        if total_cost >= BUDGET_ABORT_USD:
            log.warning(
                "⚠ HARD ABORT: cost $%.4f >= $%.2f. Stopping regeneration.",
                total_cost,
                BUDGET_ABORT_USD,
            )
            aborted = True
            break

        mod_id = ph["module"]
        concept = ph["concept"]
        difficulty = ph["difficulty"]
        is_dml = concept in DML_CONCEPTS
        max_retries = MAX_RETRIES_AGGREGATIONS if mod_id == 2 else MAX_RETRIES_DEFAULT

        log.info(
            "[%d/%d] M%d / %s / d%d (dml=%s, max_retries=%d, cost so far $%.4f)",
            i,
            len(phantoms),
            mod_id,
            concept,
            difficulty,
            is_dml,
            max_retries,
            total_cost,
        )

        meta, _failures = generate_one(
            builder=builder,
            api=api,
            validator=validator,
            concept=concept,
            difficulty=difficulty,
            max_retries=max_retries,
            logger=log,
            dml=is_dml,
        )

        if meta is None:
            log.error("  → no meta after %d retries (phantom remains)", max_retries)
            failed_count += 1
            continue

        task_cost = estimate_cost_usd(
            meta.api_input_tokens, meta.api_output_tokens, meta.api_cached_tokens
        )
        total_cost += task_cost
        status = "validated" if meta.validation_passed else "failed"
        save_meta(meta, output_dir, status)
        log.info(
            "  → %s ($%.4f, %d retries)", status, task_cost, meta.retries
        )

        if meta.validation_passed:
            validated_count += 1
        else:
            failed_count += 1

    log.info("=" * 60)
    log.info(
        "REGEN TOTAL: %d validated, %d failed, $%.4f cost%s",
        validated_count,
        failed_count,
        total_cost,
        " (ABORTED)" if aborted else "",
    )
    if total_cost > BUDGET_TARGET_USD:
        log.warning("⚠ Cost $%.4f over target $%.2f", total_cost, BUDGET_TARGET_USD)

    return 0 if not aborted else 1


if __name__ == "__main__":
    sys.exit(main())
