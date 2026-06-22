"""2B-3 Salvage skripta — automatski popravlja needs_fix taskove.

Kategorije:
  direct_approve  — validator bug; task je ispravan, samo approve u SQLite
  re_run          — query OK, expected_result kriv; re-run → update JSON → approve
  description_fix — samo typo u opisu; fix u JSON → approve (bez sandbox re-runa)
  skip            — treba ljudsku odluku; samo report

Pokretanje (iz backend/):
    uv run python scripts/salvage_needs_fix.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# backend/ je u sys.path
_BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND))

from dotenv import load_dotenv

load_dotenv(_BACKEND / ".env")

from app.db.manual_review import ManualReviewDB
from scripts.lib.sandbox_runner import SandboxRunner

_REPO_ROOT = _BACKEND.parent
_TASKS_DIR = _REPO_ROOT / "data" / "generated_tasks"
_DB_PATH = _TASKS_DIR / "manual_review.sqlite"

# Psycopg DSN (bez SQLAlchemy prefix)
_SANDBOX_URL = os.getenv("SANDBOX_DATABASE_URL", "").replace(
    "postgresql+psycopg://", "postgresql://"
)

# ---------------------------------------------------------------------------
# Klasifikacija taskova
# ---------------------------------------------------------------------------

# Validator bug — task je točan, samo approve; NE mijenjamo JSON
DIRECT_APPROVE: dict[str, str] = {
    "scalar_subquery_d3_63bcf0bf": "validator-bug: type mismatch string vs number — task ispravan",
    "index_usage_d3_41c8280e": "validator type-bug: string '3832.15' vs number — task ispravan",
}

# Samo typo/wording fix u task.description (ne diramo expected_result)
# Format: task_id → (polje, staro, novo)
DESCRIPTION_FIX: dict[str, tuple[str, str, str]] = {
    "having_filter_d4_manual_6da34957": (
        "description",
        "200 NOVAČA",
        "200",
    ),
}

# Preskačemo — treba ručna intervencija
SKIP: dict[str, str] = {
    "right_join_d2_5421a8f5": "semantički mismatch title↔query (dobavljači vs kupci) — treba redesign",
    "insert_d1_a134804d": "INSERT bez RETURNING → wrong_values_order nedektektabilan — treba redesign",
    "insert_d3_c604e855": "RETURNING serial PK non-deterministic pod rollbackom — treba fix",
    "in_subquery_d4_d28a7503": "empty result — treba ubaciti data point ili demo tretman",
    "order_by_d1_c81bf828": "pedagoška formulacija nedostatna — treba ručni rewrite opisa",
}

# Svi ostali needs_fix idu na re_run (query OK, expected_result kriv)
# DML taskovi (delete, update, insert) dobivaju dml=True automatski


def _is_dml(query: str) -> bool:
    q = query.strip().upper()
    return q.startswith(("INSERT", "UPDATE", "DELETE", "MERGE"))


def _find_json(task_id: str) -> Path | None:
    for status in ("validated", "failed"):
        p = _TASKS_DIR / status / f"{task_id}.json"
        if p.exists():
            return p
    return None


def _load_task(task_id: str) -> tuple[dict, Path] | tuple[None, None]:
    p = _find_json(task_id)
    if p is None:
        return None, None
    return json.loads(p.read_text(encoding="utf-8")), p


# ---------------------------------------------------------------------------
# Salvage operacije
# ---------------------------------------------------------------------------


def do_direct_approve(
    task_id: str,
    note: str,
    db: ManualReviewDB,
    dry_run: bool,
) -> str:
    review = db.get_review(task_id)
    if review is None:
        return "ERROR: not in SQLite"
    if not dry_run:
        db.upsert_review(
            task_id=task_id,
            decision="approved",
            notes=note,
            concept_code=review.concept_code,
            module_number=review.module_number,
            difficulty=review.difficulty,
            task_status=review.task_status,
            failure_type=review.failure_type,
        )
    return f"{'[DRY]' if dry_run else 'OK'} direct_approve"


def do_description_fix(
    task_id: str,
    field: str,
    old_text: str,
    new_text: str,
    db: ManualReviewDB,
    dry_run: bool,
) -> str:
    task_data, json_path = _load_task(task_id)
    if task_data is None:
        return "ERROR: JSON not found"
    inner = task_data.get("task", {})
    val = inner.get(field, "")
    if old_text not in val:
        return f"WARN: '{old_text}' not found in {field} — možda već popravljeno"
    if not dry_run:
        inner[field] = val.replace(old_text, new_text, 1)
        json_path.write_text(
            json.dumps(task_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        review = db.get_review(task_id)
        db.upsert_review(
            task_id=task_id,
            decision="approved",
            notes=f"salvage: typo fix '{old_text}' → '{new_text}' u {field}",
            concept_code=review.concept_code,
            module_number=review.module_number,
            difficulty=review.difficulty,
            task_status=review.task_status,
            failure_type=review.failure_type,
        )
    return f"{'[DRY]' if dry_run else 'OK'} description_fix"


def do_re_run(
    task_id: str,
    runner: SandboxRunner,
    db: ManualReviewDB,
    dry_run: bool,
) -> str:
    task_data, json_path = _load_task(task_id)
    if task_data is None:
        return "ERROR: JSON not found"
    inner = task_data.get("task", {})
    query = inner.get("expected_query", "")
    if not query:
        return "ERROR: no expected_query"

    dml = _is_dml(query)
    result = runner.execute(query, dml=dml)

    if not result.success:
        return f"FAIL: sandbox error — {result.error}"

    old_expected = inner.get("expected_result", [])
    new_expected = result.rows  # već normalizirano u SandboxRunner

    # Provjeri je li se nešto uopće promijenilo
    changed = old_expected != new_expected
    if not changed:
        # expected_result je već točan → samo approve
        if not dry_run:
            review = db.get_review(task_id)
            db.upsert_review(
                task_id=task_id,
                decision="approved",
                notes="salvage: re-run potvrđuje expected_result točan — approve",
                concept_code=review.concept_code,
                module_number=review.module_number,
                difficulty=review.difficulty,
                task_status=review.task_status,
                failure_type=review.failure_type,
            )
        return f"{'[DRY]' if dry_run else 'OK'} re_run (expected_result nepromijenjen, samo approve)"

    rows_info = f"{len(old_expected)}→{len(new_expected)} redaka"
    if not dry_run:
        inner["expected_result"] = new_expected
        json_path.write_text(
            json.dumps(task_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        review = db.get_review(task_id)
        db.upsert_review(
            task_id=task_id,
            decision="approved",
            notes=f"salvage: expected_result updated via re-run ({rows_info})",
            concept_code=review.concept_code,
            module_number=review.module_number,
            difficulty=review.difficulty,
            task_status=review.task_status,
            failure_type=review.failure_type,
        )
    return f"{'[DRY]' if dry_run else 'OK'} re_run (updated {rows_info})"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="2B-3 salvage script")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Samo prikaži što bi se napravilo, ne mijenjaj ništa",
    )
    args = parser.parse_args()
    dry_run: bool = args.dry_run

    db = ManualReviewDB(_DB_PATH)
    runner = SandboxRunner(_SANDBOX_URL)

    needs_fix = db.list_reviews(decision="needs_fix")
    nf_ids = {r.task_id for r in needs_fix}

    print(f"\n=== 2B-3 SALVAGE {'(DRY RUN)' if dry_run else ''} ===")
    print(f"Ukupno needs_fix: {len(needs_fix)}\n")

    results: dict[str, str] = {}

    # 1. direct_approve
    for task_id, note in DIRECT_APPROVE.items():
        if task_id not in nf_ids:
            results[task_id] = "SKIP: nije u needs_fix"
            continue
        r = do_direct_approve(task_id, note, db, dry_run)
        results[task_id] = f"direct_approve → {r}"

    # 2. description_fix
    for task_id, (field, old, new) in DESCRIPTION_FIX.items():
        if task_id not in nf_ids:
            results[task_id] = "SKIP: nije u needs_fix"
            continue
        r = do_description_fix(task_id, field, old, new, db, dry_run)
        results[task_id] = f"description_fix → {r}"

    # 3. skip
    for task_id, reason in SKIP.items():
        results[task_id] = f"SKIP: {reason}"

    # 4. re_run — sve što još nije klasificirano
    handled = set(DIRECT_APPROVE) | set(DESCRIPTION_FIX) | set(SKIP)
    for review in sorted(needs_fix, key=lambda x: (x.module_number, x.task_id)):
        if review.task_id in handled:
            continue
        r = do_re_run(review.task_id, runner, db, dry_run)
        results[review.task_id] = f"re_run → {r}"

    # Ispis rezultata
    print(f"{'TASK_ID':<45} {'REZULTAT'}")
    print("-" * 100)
    ok_count = 0
    for task_id, outcome in sorted(results.items()):
        icon = "✓" if "OK" in outcome or "[DRY]" in outcome else ("~" if "SKIP" in outcome else "✗")
        print(f"  {icon}  {task_id:<45} {outcome}")
        if "OK" in outcome:
            ok_count += 1

    print(f"\n--- Sumarij ---")
    print(f"  Salvaged (OK):  {ok_count}")
    print(f"  Skip/manual:    {sum(1 for v in results.values() if 'SKIP' in v)}")
    print(f"  Greške:         {sum(1 for v in results.values() if 'FAIL' in v or 'ERROR' in v)}")

    if not dry_run:
        stats = db.get_stats()
        print(f"\n  Approved ukupno: {stats['by_decision'].get('approved', 0)}")
        print(f"  Needs_fix ostalo: {stats['by_decision'].get('needs_fix', 0)}")
        print(f"  Gap do 80: {max(0, 80 - stats['by_decision'].get('approved', 0))}")


if __name__ == "__main__":
    main()
