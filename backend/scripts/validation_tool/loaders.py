"""Učitavanje generiranih taskova iz `data/generated_tasks/{validated,failed}/`
i mapiranje validation_failures na failure_type taxonomy za 2B-1C tool.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml

from app.db.manual_review import ManualReviewDB

_log = logging.getLogger(__name__)

# Mapping (validation_failures[0].level, validation_failures[0].code) → taxonomy
# Taxonomy iz plana §3.3 (failure_type column u manual_review.sqlite).
_LEVEL_CODE_MAP: dict[tuple[str, str], str] = {
    ("concept_coverage", "primary_concept_not_detected"): "concept_not_detected",
    ("concept_coverage", "detector_not_implemented"): "concept_not_detected",
    ("concept_coverage", "detector_crashed"): "concept_not_detected",
    ("result_match", "row_mismatch"): "row_mismatch",
    ("result_match", "execution_failed"): "sandbox_error",
    ("result_match", "runner_crashed"): "sandbox_error",
    ("result_match", "comparison_crashed"): "sandbox_error",
}


def load_all_tasks(generated_tasks_dir: Path) -> list[dict]:
    """Učitaj sve task JSON-ove iz korijenskih `validated/` i `failed/` subdir-a.

    Annotira svaki task s `_task_status`, `_source_path` i `_task_id` (filename stem).
    Malformed JSON se preskače (logira warning, ne ruši loader).
    """
    base = Path(generated_tasks_dir)
    tasks: list[dict] = []
    for status in ("validated", "failed"):
        subdir = base / status
        if not subdir.exists():
            continue
        for json_path in sorted(subdir.glob("*.json")):
            try:
                task = json.loads(json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                _log.warning("Skipped malformed JSON %s: %s", json_path.name, exc)
                continue
            task["_task_status"] = status
            task["_source_path"] = str(json_path)
            task["_task_id"] = json_path.stem
            tasks.append(task)
    return tasks


def extract_failure_type(task: dict) -> str | None:
    """Vrati failure_type taxonomy iz validation_failures[0].

    Validated tasks vraćaju None. Za failed tasks bez failures (edge case) → 'other'.
    """
    if task.get("_task_status") == "validated":
        return None
    failures = task.get("validation_failures") or []
    if not failures:
        return "other"
    first = failures[0]
    key = (first.get("level", ""), first.get("code", ""))
    return _LEVEL_CODE_MAP.get(key, "other")


def load_concept_module_map(concepts_dir: Path) -> dict[str, int]:
    """Pročitaj sve `*.yaml` u concepts dir-u i sastavi map concept_code → module_number.

    Ako dir ne postoji, vraća prazan dict (loader može graceful nastavit s module=0).
    """
    cdir = Path(concepts_dir)
    if not cdir.exists():
        return {}
    mapping: dict[str, int] = {}
    for yaml_path in sorted(cdir.glob("*.yaml")):
        try:
            data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            _log.warning("Failed to parse concept YAML %s: %s", yaml_path.name, exc)
            continue
        if not isinstance(data, dict):
            continue
        code = data.get("concept_code")
        module = data.get("module_number")
        if code and isinstance(module, int):
            mapping[code] = module
    return mapping


def bootstrap_pending_reviews(
    tasks: list[dict],
    db: ManualReviewDB,
    concept_module_map: dict[str, int],
) -> int:
    """Insert 'pending' review za sve nove tasks. Idempotent — postojeće odluke
    se ne diraju. Vraća broj novouvedenih entries."""
    added = 0
    for task in tasks:
        task_id = task["_task_id"]
        if db.get_review(task_id) is not None:
            continue
        inner = task.get("task", {})
        concept = inner.get("primary_concept", "unknown")
        difficulty = int(inner.get("difficulty", 0))
        module_number = concept_module_map.get(concept, 0)
        db.upsert_review(
            task_id=task_id,
            decision="pending",
            notes="",
            concept_code=concept,
            module_number=module_number,
            difficulty=difficulty,
            task_status=task["_task_status"],
            failure_type=extract_failure_type(task),
        )
        added += 1
    return added
