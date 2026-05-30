"""SQLite layer za task review decisions u 2B-1C validation toolu.

Single-source-of-truth za review odluke je SQLite file na disku
(`data/generated_tasks/manual_review.sqlite`). Task JSON-i ostaju immutable
na disku, ovaj DB store-uje samo odluku + bilješke + metadata za filtere.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Decision = Literal["pending", "approved", "rejected", "needs_fix"]

_VALID_DECISIONS = ("pending", "approved", "rejected", "needs_fix")


@dataclass(frozen=True)
class TaskReview:
    task_id: str
    decision: Decision
    notes: str
    reviewed_at: str
    concept_code: str
    module_number: int
    difficulty: int
    task_status: str
    failure_type: str | None


class ManualReviewDB:
    """Tanki SQLite wrapper. Sve operacije rade s parametriziranim upitima."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS task_reviews (
                    task_id TEXT PRIMARY KEY,
                    decision TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT '',
                    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    concept_code TEXT NOT NULL,
                    module_number INTEGER NOT NULL,
                    difficulty INTEGER NOT NULL,
                    task_status TEXT NOT NULL,
                    failure_type TEXT,
                    CHECK (decision IN ('pending', 'approved', 'rejected', 'needs_fix'))
                );

                CREATE INDEX IF NOT EXISTS idx_task_reviews_decision
                    ON task_reviews(decision);
                CREATE INDEX IF NOT EXISTS idx_task_reviews_concept
                    ON task_reviews(concept_code);
                CREATE INDEX IF NOT EXISTS idx_task_reviews_module
                    ON task_reviews(module_number);
                CREATE INDEX IF NOT EXISTS idx_task_reviews_failure
                    ON task_reviews(failure_type);
                """
            )

    def upsert_review(
        self,
        task_id: str,
        decision: Decision,
        notes: str,
        concept_code: str,
        module_number: int,
        difficulty: int,
        task_status: str,
        failure_type: str | None,
    ) -> None:
        """Insert ili update review entry. CHECK constraint validira decision."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO task_reviews (
                    task_id, decision, notes, reviewed_at,
                    concept_code, module_number, difficulty,
                    task_status, failure_type
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    decision = excluded.decision,
                    notes = excluded.notes,
                    reviewed_at = CURRENT_TIMESTAMP,
                    concept_code = excluded.concept_code,
                    module_number = excluded.module_number,
                    difficulty = excluded.difficulty,
                    task_status = excluded.task_status,
                    failure_type = excluded.failure_type
                """,
                (
                    task_id,
                    decision,
                    notes,
                    concept_code,
                    module_number,
                    difficulty,
                    task_status,
                    failure_type,
                ),
            )

    def get_review(self, task_id: str) -> TaskReview | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM task_reviews WHERE task_id = ?", (task_id,)
            ).fetchone()
        return _row_to_review(row) if row else None

    def list_reviews(
        self,
        decision: Decision | None = None,
        concept_code: str | None = None,
        module_number: int | None = None,
        failure_type: str | None = None,
    ) -> list[TaskReview]:
        clauses: list[str] = []
        params: list[object] = []
        if decision is not None:
            clauses.append("decision = ?")
            params.append(decision)
        if concept_code is not None:
            clauses.append("concept_code = ?")
            params.append(concept_code)
        if module_number is not None:
            clauses.append("module_number = ?")
            params.append(module_number)
        if failure_type is not None:
            clauses.append("failure_type = ?")
            params.append(failure_type)

        sql = "SELECT * FROM task_reviews"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY task_id"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_row_to_review(r) for r in rows]

    def get_stats(self) -> dict:
        """Agregirana statistika za stats page."""
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM task_reviews").fetchone()[0]
            reviewed = conn.execute(
                "SELECT COUNT(*) FROM task_reviews WHERE decision != 'pending'"
            ).fetchone()[0]
            by_decision = {
                row["decision"]: row["c"]
                for row in conn.execute(
                    "SELECT decision, COUNT(*) AS c FROM task_reviews GROUP BY decision"
                )
            }
            by_concept = {
                row["concept_code"]: row["c"]
                for row in conn.execute(
                    "SELECT concept_code, COUNT(*) AS c FROM task_reviews "
                    "GROUP BY concept_code"
                )
            }
            by_module = {
                row["module_number"]: row["c"]
                for row in conn.execute(
                    "SELECT module_number, COUNT(*) AS c FROM task_reviews "
                    "GROUP BY module_number"
                )
            }
            by_failure = {
                row["failure_type"]: row["c"]
                for row in conn.execute(
                    "SELECT failure_type, COUNT(*) AS c FROM task_reviews "
                    "WHERE failure_type IS NOT NULL GROUP BY failure_type"
                )
            }
        return {
            "total": total,
            "reviewed": reviewed,
            "by_decision": by_decision,
            "by_concept": by_concept,
            "by_module": by_module,
            "by_failure": by_failure,
        }


def _row_to_review(row: sqlite3.Row) -> TaskReview:
    return TaskReview(
        task_id=row["task_id"],
        decision=row["decision"],
        notes=row["notes"],
        reviewed_at=row["reviewed_at"],
        concept_code=row["concept_code"],
        module_number=row["module_number"],
        difficulty=row["difficulty"],
        task_status=row["task_status"],
        failure_type=row["failure_type"],
    )
