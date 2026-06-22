"""2B-3 Coverage report — matrica concept × difficulty s approved count-om.

Čita `manual_review.sqlite` → generira:
  - `data/generated_tasks/coverage_report.json`  (strojno čitljivo)
  - Markdown tablica na stdout (za wrapup dokument)

Oznake u matrici:
  broj  = approved count
  GAP   = ćelija s 0 approved (ali postoje taskovi)
  PHANTOM = ćelija bez taskova (poznati gap — nema čak ni candidate)
  -     = kombinacija ne postoji u datasetu

Permanently phantom (iz §11 faze 2B-2.5):
  correlated_subquery d5, explain_plan d5

Pokretanje (iz backend/):
    uv run python scripts/generate_coverage_report.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from app.db.manual_review import ManualReviewDB

_REPO_ROOT = _BACKEND.parent
_TASKS_DIR = _REPO_ROOT / "data" / "generated_tasks"
_DB_PATH = _TASKS_DIR / "manual_review.sqlite"
_OUT_PATH = _TASKS_DIR / "coverage_report.json"

# explain_plan d5 je jedini pravi phantom — generated task postoji ali je rejected
# i ne može se regenerirati. correlated_subquery d5 je salvaged → više nije phantom.
PHANTOM: set[tuple[str, int]] = {
    ("explain_plan", 5),
}

# Per-koncept minimum (iz plana §1 Q1)
FLOOR = 2


def _json_exists(task_id: str) -> bool:
    for status in ("validated", "failed"):
        if (_TASKS_DIR / status / f"{task_id}.json").exists():
            return True
    return False


def main() -> None:
    db = ManualReviewDB(_DB_PATH)
    all_reviews = db.list_reviews()

    # Isključi ghost entries (SQLite record bez JSON fajla na disku)
    ghost_ids = [r.task_id for r in all_reviews if not _json_exists(r.task_id)]
    if ghost_ids:
        print(f"WARN: {len(ghost_ids)} ghost entries (bez JSON) isključeni iz matrice: {ghost_ids}")

    real_reviews = [r for r in all_reviews if _json_exists(r.task_id)]

    # Approved count po (concept, difficulty)
    approved_matrix: dict[tuple[str, int], int] = defaultdict(int)
    # Svi taskovi po (concept, difficulty) — za GAP detekciju
    total_matrix: dict[tuple[str, int], int] = defaultdict(int)

    for r in real_reviews:
        key = (r.concept_code, r.difficulty)
        total_matrix[key] += 1
        if r.decision == "approved":
            approved_matrix[key] += 1

    # Sve kombinacije koncepti × difficulty koje postoje
    concepts = sorted({r.concept_code for r in real_reviews})
    difficulties = [1, 2, 3, 4, 5]

    # Per-concept approved total
    concept_totals = defaultdict(int)
    for (c, d), count in approved_matrix.items():
        concept_totals[c] += count

    # Gap lista — koncepti ispod floora
    below_floor = [
        {"concept": c, "approved": concept_totals[c], "gap": FLOOR - concept_totals[c]}
        for c in concepts
        if concept_totals[c] < FLOOR
    ]

    # Replacement candidates — ćelije bez approved ali s taskovima
    replacement_candidates = [
        {"concept": c, "difficulty": d, "total_tasks": total_matrix[(c, d)]}
        for (c, d), total in total_matrix.items()
        if approved_matrix[(c, d)] == 0 and (c, d) not in PHANTOM
    ]
    replacement_candidates.sort(key=lambda x: (x["concept"], x["difficulty"]))

    # Markdown tablica
    _print_markdown(concepts, difficulties, approved_matrix, total_matrix, concept_totals)

    # JSON output
    report = {
        "version": "2b-3",
        "summary": {
            "total_approved": sum(approved_matrix.values()),
            "ghost_entries_excluded": len(ghost_ids),
            "total_concepts": len(concepts),
            "concepts_below_floor": len(below_floor),
            "floor": FLOOR,
        },
        "below_floor": below_floor,
        "permanently_phantom": [
            {"concept": c, "difficulty": d} for c, d in sorted(PHANTOM)
        ],
        "replacement_candidates": replacement_candidates,
        "matrix": {
            c: {
                str(d): {
                    "approved": approved_matrix.get((c, d), 0),
                    "total": total_matrix.get((c, d), 0),
                    "phantom": (c, d) in PHANTOM,
                }
                for d in difficulties
                if total_matrix.get((c, d), 0) > 0 or (c, d) in PHANTOM
            }
            for c in concepts
        },
    }

    _OUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nJSON → {_OUT_PATH}")

    if below_floor:
        print(f"\nKoncepti ispod floora {FLOOR}:")
        for item in below_floor:
            print(f"  {item['concept']}: {item['approved']} approved (gap {item['gap']})")
    else:
        print(f"\nSvi koncepti ≥ {FLOOR} approved ✓")

    print(f"\nReplacement candidates ({len(replacement_candidates)}):")
    for rc in replacement_candidates:
        print(f"  {rc['concept']} d{rc['difficulty']} ({rc['total_tasks']} task(ova) u datasetu, sve non-approved)")


def _print_markdown(
    concepts: list[str],
    difficulties: list[int],
    approved: dict,
    total: dict,
    concept_totals: dict,
) -> None:
    # Header
    col_w = 28
    diff_w = 7
    header = f"| {'Koncept':<{col_w}} |"
    for d in difficulties:
        header += f" {'d'+str(d):^{diff_w}} |"
    header += f" {'UKUPNO':^7} |"
    sep = f"|{'-'*(col_w+2)}|" + f"{'-'*(diff_w+2)}|" * len(difficulties) + f"{'-'*9}|"

    print("\n## Coverage matrica (approved / taskova)")
    print()
    print(header)
    print(sep)

    for c in concepts:
        row = f"| {c:<{col_w}} |"
        for d in difficulties:
            key = (c, d)
            if key in PHANTOM:
                cell = "PHANTOM"
            elif total.get(key, 0) == 0:
                cell = "-"
            else:
                a = approved.get(key, 0)
                t = total[key]
                cell = f"{a}/{t}" if a < t else f"{a}"
                if a == 0:
                    cell = f"GAP({t})"
            row += f" {cell:^{diff_w}} |"
        total_approved = concept_totals.get(c, 0)
        flag = " ⚠" if total_approved < FLOOR else ""
        row += f" {total_approved:^7}{flag} |"
        print(row)

    print(sep)
    # Totals row
    total_row = f"| {'UKUPNO':<{col_w}} |"
    grand_total = 0
    for d in difficulties:
        col_sum = sum(approved.get((c, d), 0) for c in concepts)
        grand_total += col_sum
        total_row += f" {col_sum:^{diff_w}} |"
    total_row += f" {grand_total:^7} |"
    print(total_row)
    print()


if __name__ == "__main__":
    main()
