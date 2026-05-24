"""
Pilot run: 2 zadatka po concept tipu × 6 koncepta = 12 zadataka.

Reuse generate_one() iz generate_tasks.py. Pilot validira prompt template
i DML pipeline za sve module (1 koncept po modulu). Output: pilot_report.json.

Usage:
    cd backend && uv run python -m scripts.pilot_run
    cd backend && uv run python -m scripts.pilot_run --output-dir ../data/generated_tasks/pilot
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from scripts.generate_tasks import (
    _build_pipeline,
    estimate_cost_usd,
    generate_one,
    save_meta,
)

log = logging.getLogger(__name__)

# 1 koncept po modulu — validira sve module-specific behaviore i DML path
PILOT_CONFIG: list[dict] = [
    {"concept": "where_filter", "difficulties": [1, 2]},       # M1 SELECT
    {"concept": "group_by", "difficulties": [2, 3]},            # M2 agregacija
    {"concept": "right_join", "difficulties": [2, 3]},          # M3 JOIN
    {"concept": "insert", "difficulties": [1, 2], "dml": True}, # M4 DML
    {"concept": "scalar_subquery", "difficulties": [2, 3]},     # M5 podupit
    {"concept": "explain_plan", "difficulties": [3, 4]},        # M6 optimizacija
]


def run_pilot(
    builder,
    api,
    validator,
    output_dir: Path,
    concepts: list[str] | None = None,
    output_suffix: str = "",
) -> dict:
    """
    Core pilot logika — testabilna bez CLI args.

    Args:
        concepts: ako zadan, filtrira PILOT_CONFIG samo na koncepte iz liste.
        output_suffix: ako zadan, report path → pilot_report_<suffix>.json.

    Returns:
        report dict s per_concept, total_cost, started_at.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    report: dict = {
        "per_concept": {},
        "total_cost": 0.0,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }

    if concepts:
        wanted = set(concepts)
        active_config = [e for e in PILOT_CONFIG if e["concept"] in wanted]
        missing = wanted - {e["concept"] for e in PILOT_CONFIG}
        if missing:
            raise ValueError(
                f"Nepoznati koncepti za pilot: {sorted(missing)}. "
                f"Dostupni: {sorted(e['concept'] for e in PILOT_CONFIG)}"
            )
    else:
        active_config = PILOT_CONFIG

    for entry in active_config:
        concept = entry["concept"]
        is_dml = entry.get("dml", False)
        report["per_concept"][concept] = []

        for difficulty in entry["difficulties"]:
            log.info("Pilot: %s d=%d (dml=%s)", concept, difficulty, is_dml)

            meta, failures = generate_one(
                builder,
                api,
                validator,
                concept=concept,
                difficulty=difficulty,
                dml=is_dml,
                extended_thinking=True,
            )

            if meta is not None:
                status = "validated" if meta.validation_passed else "failed"
                cost = estimate_cost_usd(
                    meta.api_input_tokens,
                    meta.api_output_tokens,
                    meta.api_cached_tokens,
                )
                save_meta(meta, output_dir, status)
            else:
                status = "failed"
                cost = 0.0

            entry_result = {
                "concept": concept,
                "difficulty": difficulty,
                "status": status,
                "dml": is_dml,
                "attempts": len(failures) + (1 if meta is not None else 0),
                "cost_usd": cost,
                "failures": failures,
            }
            report["per_concept"][concept].append(entry_result)
            report["total_cost"] += cost

    # Spremi report (s opcionalnim suffix-om za iteration history)
    report_name = f"pilot_report_{output_suffix}.json" if output_suffix else "pilot_report.json"
    report_path = output_dir / report_name
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def _print_analysis(report: dict) -> None:
    """Ispiši summary analizu pilot run-a."""
    total = sum(len(v) for v in report["per_concept"].values())
    validated = sum(
        1
        for results in report["per_concept"].values()
        for r in results
        if r["status"] == "validated"
    )
    pct = (100 * validated // total) if total else 0
    print(f"\n{'='*55}")
    print(f"PILOT ANALIZA")
    print(f"  Ukupno zadataka:  {total}")
    print(f"  Validated:        {validated}/{total} ({pct}%)")
    print(f"  Ukupni trošak:    ${report['total_cost']:.4f}")
    print()
    print(f"{'Koncept':<20} {'d=1':>5} {'d=2':>5} {'d=3':>5} {'d=4':>5}")
    print("-" * 40)
    for concept, results in report["per_concept"].items():
        row_cells = {}
        for r in results:
            icon = "✓" if r["status"] == "validated" else "✗"
            row_cells[r["difficulty"]] = icon
        row = "  ".join(row_cells.get(d, " ") for d in [1, 2, 3, 4])
        print(f"  {concept:<18} {row}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pilot run: 12 zadataka, 6 koncepta.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="../data/generated_tasks/pilot",
        help="Direktorij za pilot output (default: ../data/generated_tasks/pilot)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-6",
        help="Anthropic model (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--concepts",
        type=str,
        default=None,
        help=(
            "Comma-separated lista koncepata iz PILOT_CONFIG (npr. "
            "'where_filter,group_by'). Default: svi koncepti iz PILOT_CONFIG."
        ),
    )
    parser.add_argument(
        "--output-suffix",
        type=str,
        default="",
        help=(
            "Suffix za pilot_report fajl (npr. 'iter1' → pilot_report_iter1.json). "
            "Default: nema suffix-a, fajl je pilot_report.json."
        ),
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv()
    args = parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY nije postavljen.", file=sys.stderr)
        sys.exit(1)

    backend_root = Path(__file__).parent.parent
    builder, api, validator = _build_pipeline(
        backend_root=backend_root,
        api_key=api_key,
        model=args.model,
    )

    output_dir = Path(args.output_dir)
    concepts_list = (
        [c.strip() for c in args.concepts.split(",") if c.strip()]
        if args.concepts
        else None
    )
    if concepts_list:
        print(f"Pilot run → {output_dir} (koncepti: {', '.join(concepts_list)})")
    else:
        print(f"Pilot run → {output_dir}")

    report = run_pilot(
        builder,
        api,
        validator,
        output_dir,
        concepts=concepts_list,
        output_suffix=args.output_suffix,
    )

    _print_analysis(report)
    report_name = (
        f"pilot_report_{args.output_suffix}.json" if args.output_suffix else "pilot_report.json"
    )
    print(f"\nReport: {output_dir / report_name}")


if __name__ == "__main__":
    main()
