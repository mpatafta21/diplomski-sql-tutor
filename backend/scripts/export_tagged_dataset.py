"""2B-3 Export — tagged JSON manifest od approved zadataka.

Čita `manual_review.sqlite` (approved decisions) + task JSON fajlove →
generira `data/generated_tasks/final_dataset.json` s poljima:
  task_id, module, primary_concept, difficulty,
  approved_by_human, generation_method, recovery_applied,
  title, description, expected_query, expected_result,
  secondary_concepts, estimated_time_sec, sandbox_schema

Pokretanje (iz backend/):
    uv run python scripts/export_tagged_dataset.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from app.db.manual_review import ManualReviewDB

_REPO_ROOT = _BACKEND.parent
_TASKS_DIR = _REPO_ROOT / "data" / "generated_tasks"
_DB_PATH = _TASKS_DIR / "manual_review.sqlite"
_OUT_PATH = _TASKS_DIR / "final_dataset.json"

# Bilješka u SQLite koja označava da je expected_result bio editiran re-runom
_RECOVERY_MARKERS = ("expected_result updated via re-run", "re-run potvrđuje")


def _recovery_applied(notes: str) -> bool:
    return any(m in notes for m in _RECOVERY_MARKERS)


def _find_json(task_id: str) -> Path | None:
    for status in ("validated", "failed"):
        p = _TASKS_DIR / status / f"{task_id}.json"
        if p.exists():
            return p
    return None


def main() -> None:
    db = ManualReviewDB(_DB_PATH)
    approved = db.list_reviews(decision="approved")

    records: list[dict] = []
    missing: list[str] = []

    for review in sorted(approved, key=lambda r: (r.module_number, r.concept_code, r.difficulty)):
        json_path = _find_json(review.task_id)
        if json_path is None:
            missing.append(review.task_id)
            continue

        raw = json.loads(json_path.read_text(encoding="utf-8"))
        inner = raw.get("task", {})

        record: dict = {
            "task_id": review.task_id,
            "module": review.module_number,
            "primary_concept": review.concept_code,
            "difficulty": review.difficulty,
            "approved_by_human": True,
            "generation_method": raw.get("generation_method", "llm"),
            "recovery_applied": _recovery_applied(review.notes),
            "title": inner.get("title", ""),
            "description": inner.get("description", ""),
            "sandbox_schema": inner.get("sandbox_schema", "ecommerce_v1"),
            "expected_query": inner.get("expected_query", ""),
            "expected_result": inner.get("expected_result", []),
            "secondary_concepts": inner.get("secondary_concepts", []),
            "estimated_time_sec": inner.get("estimated_time_sec"),
        }
        records.append(record)

    output = {
        "version": "2b-3",
        "total": len(records),
        "missing_json": missing,
        "tasks": records,
    }

    _OUT_PATH.write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Exported {len(records)} taskova → {_OUT_PATH}")
    if missing:
        print(f"WARN: {len(missing)} approved taskova bez JSON fajla: {missing}")

    # Kratki sumarij
    from collections import Counter
    methods = Counter(r["generation_method"] for r in records)
    recovered = sum(1 for r in records if r["recovery_applied"])
    print(f"  generation_method: {dict(methods)}")
    print(f"  recovery_applied: {recovered}")
    print(f"  moduli: {sorted(set(r['module'] for r in records))}")


if __name__ == "__main__":
    main()
