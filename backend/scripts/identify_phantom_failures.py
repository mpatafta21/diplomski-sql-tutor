"""Faza 2B-2.5 — identify phantom failures iz batch_report-a.

Phantom = task counted as "failed" u batch_report.json, ali bez matching JSON-a
u `data/generated_tasks/failed/`. Uzrok: `meta=None` (svi retries fail s API
errorima ili schema/parse failures koji ne produciraju meta), pa `save_meta`
nije pozvan.

Output: list of (module, concept, difficulty) tuples i per-modul counts —
input za Korak 2 selective regeneration.

Pokretanje:
    cd backend && uv run python -m scripts.identify_phantom_failures
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def load_aggregated_report(base_dir: Path) -> dict:
    """Load batch_report.json (aggregated, expected after Korak 10)."""
    path = base_dir / "batch_report.json"
    if not path.exists():
        raise FileNotFoundError(f"Aggregated report not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def count_saved_failed(base_dir: Path) -> Counter:
    """Count failed JSON files on disk po (concept, difficulty). Filename pattern:
    <concept>_d<digit>_<uuid8>.json (LLM) ili <concept>_d<digit>_manual_<uuid8>.json (manual).
    """
    failed_dir = base_dir / "failed"
    counts: Counter = Counter()
    if not failed_dir.exists():
        return counts
    for f in failed_dir.glob("*.json"):
        stem = f.stem
        # extract concept and difficulty from filename
        # pattern: <concept>_d<N>_<rest>
        parts = stem.split("_d")
        if len(parts) < 2:
            continue
        concept = parts[0]
        # difficulty is first char(s) after "_d", before "_"
        diff_and_rest = parts[1]
        diff_str = diff_and_rest.split("_")[0]
        try:
            difficulty = int(diff_str)
        except ValueError:
            continue
        counts[(concept, difficulty)] += 1
    return counts


def count_expected_failed_per_concept_diff(report: dict, base_dir: Path) -> dict:
    """Iz batch report-a: koliko se OČEKIVALO failed po (module, concept, difficulty).
    Report ne sadrži per-difficulty stats, samo per-concept failed_count. Da identificiramo
    phantom-e per difficulty, trebamo cross-reference s task_distribution.yaml matricom.

    Vraća dict: {(module, concept, difficulty): expected_attempts}.
    """
    import yaml

    matrix_path = base_dir.parent.parent / "backend" / "config" / "task_distribution.yaml"
    matrix = yaml.safe_load(matrix_path.read_text(encoding="utf-8"))

    expected = {}
    for mod_id, mod_data in matrix["modules"].items():
        for concept, concept_data in mod_data["concepts"].items():
            for diff, count in concept_data.get("distribution", {}).items():
                if count > 0:
                    expected[(mod_id, concept, int(diff))] = count
    return expected


def main(argv: list[str]) -> int:
    base_dir = Path(argv[1]) if len(argv) > 1 else Path("data/generated_tasks")
    base_dir = base_dir.resolve()

    print(f"Loading report from: {base_dir}")
    report = load_aggregated_report(base_dir)

    # Step 1: From report, per (module, concept) count failed_count
    report_failed_per_concept: dict[tuple[int, str], int] = {}
    for mod_id_str, mod_data in report["modules"].items():
        mod_id = int(mod_id_str)
        for concept, concept_data in mod_data["concepts"].items():
            report_failed_per_concept[(mod_id, concept)] = concept_data["failed"]

    # Step 2: Per concept, count saved JSON files
    saved_per_concept_diff = count_saved_failed(base_dir)
    # Sum per concept
    saved_per_concept: Counter = Counter()
    for (concept, diff), c in saved_per_concept_diff.items():
        saved_per_concept[concept] += c

    # Step 3: Compute phantom = report_failed - saved per concept
    print("\n=== Phantom failure analysis ===")
    print(f"{'Module':<8} {'Concept':<25} {'Report':>8} {'Saved':>8} {'Phantom':>9}")
    print("-" * 60)
    total_report = 0
    total_saved = 0
    total_phantom = 0
    phantom_per_concept: list[tuple[int, str, int]] = []
    for (mod_id, concept), reported_failed in sorted(report_failed_per_concept.items()):
        saved = saved_per_concept.get(concept, 0)
        phantom = max(0, reported_failed - saved)
        total_report += reported_failed
        total_saved += saved
        total_phantom += phantom
        if reported_failed > 0 or saved > 0:
            print(f"M{mod_id:<7} {concept:<25} {reported_failed:>8} {saved:>8} {phantom:>9}")
        if phantom > 0:
            phantom_per_concept.append((mod_id, concept, phantom))
    print("-" * 60)
    print(f"{'TOTAL':<8} {'':<25} {total_report:>8} {total_saved:>8} {total_phantom:>9}")

    # Step 4: Find difficulty allocation for phantoms (using matrix distribution + saved counts)
    expected_per_concept_diff = count_expected_failed_per_concept_diff(report, base_dir)

    print("\n=== Phantom (module, concept, difficulty) for regeneration ===")
    phantoms_for_regen: list[tuple[int, str, int]] = []
    for mod_id, concept, n_phantoms in phantom_per_concept:
        # For each difficulty, expected count from matrix minus (validated + saved-failed)
        # Hmm — simpler: difficulties for which we don't have saved file but matrix expects.
        diffs_in_matrix = [
            d
            for (mid, c, d) in expected_per_concept_diff.keys()
            if mid == mod_id and c == concept
        ]
        # Saved files (validated + failed) per difficulty for this concept
        validated_dir = base_dir / "validated"
        saved_diffs_count: Counter = Counter()
        for sub in ("validated", "failed"):
            d = base_dir / sub
            if not d.exists():
                continue
            for f in d.glob(f"{concept}_d*_*.json"):
                stem = f.stem
                parts = stem.split("_d")
                if len(parts) >= 2:
                    diff_str = parts[1].split("_")[0]
                    try:
                        diff = int(diff_str)
                        saved_diffs_count[diff] += 1
                    except ValueError:
                        continue
        # For each difficulty in matrix, find shortfall
        for diff in diffs_in_matrix:
            expected = expected_per_concept_diff[(mod_id, concept, diff)]
            on_disk = saved_diffs_count.get(diff, 0)
            shortfall = max(0, expected - on_disk)
            for _ in range(shortfall):
                phantoms_for_regen.append((mod_id, concept, diff))

    for mod_id, concept, diff in phantoms_for_regen:
        print(f"  M{mod_id} / {concept} / d{diff}")
    print(f"\nTotal phantoms to regenerate: {len(phantoms_for_regen)}")

    # Per-module summary for regen
    by_module: dict[int, int] = defaultdict(int)
    for mod_id, _, _ in phantoms_for_regen:
        by_module[mod_id] += 1
    print("\nPer-module counts:")
    for mid in sorted(by_module):
        print(f"  M{mid}: {by_module[mid]} phantom(s)")

    # Output as JSON for downstream Korak 2 script
    out_path = base_dir / "phantoms_to_regenerate.json"
    out_path.write_text(
        json.dumps(
            [{"module": m, "concept": c, "difficulty": d} for m, c, d in phantoms_for_regen],
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSaved JSON list: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
