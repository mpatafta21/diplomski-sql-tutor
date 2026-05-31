"""Agregira per-module batch_report_M*.json fajlove u jedan batch_report.json.

Korišteno u Faza 2B-2 Korak 10 (LLM batch checkpoint) — kroz N modula generirano
je N+ pojedinačnih reportova; ovaj script ih merge-a u jedan globalni report.

Special-case: ako više reportova pokriva isti modul (npr. M6 partial + M6 indexonly_v2
nakon credit/detector fix-a), koncept-i se merge-aju iz najnovijeg za svaki koncept.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def aggregate(base_dir: Path) -> dict:
    report_paths = sorted(base_dir.glob("batch_report_M*.json"))
    aggregated: dict = {
        "phase": "2b-2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_reports": [p.name for p in report_paths],
        "modules": {},
        "total_cost_usd": 0.0,
        "total_validated": 0,
        "total_failed": 0,
    }

    for p in report_paths:
        data = json.loads(p.read_text(encoding="utf-8"))
        for mod_id, mod_data in data["modules"].items():
            if mod_id in aggregated["modules"]:
                existing = aggregated["modules"][mod_id]
                for cn, cd in mod_data["concepts"].items():
                    existing["concepts"][cn] = cd
            else:
                aggregated["modules"][mod_id] = {
                    "name": mod_data["name"],
                    "concepts": dict(mod_data["concepts"]),
                    "aborted": mod_data.get("aborted", False),
                }
        # Note: M2_attempt_aborted has 0 validated all-failed; M6_partial has explain_plan,
        # M6_indexonly_v2 has index_usage. Merge logic above adds both concepts to M6.

    # Recompute module-level totals from merged concepts
    for mod_data in aggregated["modules"].values():
        mod_data["validated"] = sum(c["validated"] for c in mod_data["concepts"].values())
        mod_data["failed"] = sum(c["failed"] for c in mod_data["concepts"].values())
        mod_data["module_cost_usd"] = sum(c["cost_usd"] for c in mod_data["concepts"].values())

    aggregated["total_cost_usd"] = sum(m["module_cost_usd"] for m in aggregated["modules"].values())
    aggregated["total_validated"] = sum(m["validated"] for m in aggregated["modules"].values())
    aggregated["total_failed"] = sum(m["failed"] for m in aggregated["modules"].values())

    return aggregated


def main(argv: list[str]) -> int:
    base_dir = Path(argv[1]) if len(argv) > 1 else Path("data/generated_tasks")
    report = aggregate(base_dir)
    out_path = base_dir / "batch_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Modules: {sorted(report['modules'].keys())}")
    print(
        f"Total: {report['total_validated']} validated, "
        f"{report['total_failed']} failed, "
        f"${report['total_cost_usd']:.4f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
