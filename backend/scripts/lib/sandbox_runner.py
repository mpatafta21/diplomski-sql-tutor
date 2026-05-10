"""Sandbox SQL runner — read-only i DML execution u ecommerce_v1 schemi."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

import psycopg


_ORDER_BY_RE = re.compile(r"\bORDER\s+BY\b", re.IGNORECASE)


@dataclass
class ExecutionResult:
    success: bool
    rows: list[dict] = field(default_factory=list)
    column_names: list[str] = field(default_factory=list)
    execution_time_ms: int = 0
    error: str | None = None


@dataclass
class ComparisonResult:
    matches: bool
    diff_summary: str
    actual_count: int
    expected_count: int
    first_mismatch: dict | None = None


def _normalize_value(v):
    """TIMESTAMPTZ → ISO string, Decimal → str, ostalo nepromijenjeno."""
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return str(v)
    return v


class SandboxRunner:
    def __init__(self, connection_string: str, timeout_seconds: int = 5) -> None:
        self.connection_string = connection_string
        self.timeout_ms = timeout_seconds * 1000

    def execute(
        self,
        query: str,
        schema: str = "ecommerce_v1",
        dml: bool = False,
    ) -> ExecutionResult:
        """
        Izvršava SQL upit u sandbox PostgreSQL bazi.

        Args:
            query: SQL upit za izvršavanje.
            dml: Ako True, koristi sandbox_readwrite role i uvijek rollback-a
                 transakciju na kraju (DML promjene ne perzistiraju).
                 Ako False (default), koristi sandbox_readonly.
            schema: PostgreSQL schema (default: ecommerce_v1).
        """
        start = time.perf_counter()
        role = "sandbox_readwrite" if dml else "sandbox_readonly"

        try:
            with psycopg.connect(self.connection_string, autocommit=not dml) as conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute(f"SET search_path TO {schema}")
                        cur.execute(f"SET statement_timeout = {self.timeout_ms}")
                        cur.execute(f"SET ROLE {role}")
                        cur.execute(query)
                        if cur.description is None:
                            return ExecutionResult(
                                success=True,
                                execution_time_ms=int(
                                    (time.perf_counter() - start) * 1000
                                ),
                            )
                        cols = [d.name for d in cur.description]
                        rows = [
                            {c: _normalize_value(v) for c, v in zip(cols, r)}
                            for r in cur.fetchall()
                        ]
                        return ExecutionResult(
                            success=True,
                            rows=rows,
                            column_names=cols,
                            execution_time_ms=int(
                                (time.perf_counter() - start) * 1000
                            ),
                        )
                except psycopg.errors.QueryCanceled as e:
                    return ExecutionResult(
                        success=False,
                        error=f"Statement timeout after {self.timeout_ms}ms: {e}",
                        execution_time_ms=int((time.perf_counter() - start) * 1000),
                    )
                except psycopg.Error as e:
                    return ExecutionResult(
                        success=False,
                        error=str(e),
                        execution_time_ms=int((time.perf_counter() - start) * 1000),
                    )
                finally:
                    if dml:
                        try:
                            conn.rollback()
                        except Exception:
                            pass  # connection close will rollback anyway
                # Invariant: each execute() call opens and closes its own connection.
                # The per-call rollback is safe only because no outer transaction exists.
                # If a connection pool is introduced, switch to SAVEPOINT pattern.
        except psycopg.Error as e:
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time_ms=int((time.perf_counter() - start) * 1000),
            )

    def compare(
        self,
        actual: ExecutionResult,
        expected: list[dict],
        order_matters: bool | None = None,
        query: str | None = None,
    ) -> ComparisonResult:
        if not actual.success:
            return ComparisonResult(
                matches=False,
                diff_summary=f"Actual execution failed: {actual.error}",
                actual_count=0,
                expected_count=len(expected),
            )

        if order_matters is None and query is not None:
            order_matters = bool(_ORDER_BY_RE.search(query))
        order_matters = bool(order_matters)

        actual_rows = [
            {k: _normalize_value(v) for k, v in r.items()} for r in actual.rows
        ]
        expected_rows = [
            {k: _normalize_value(v) for k, v in r.items()} for r in expected
        ]

        if len(actual_rows) != len(expected_rows):
            return ComparisonResult(
                matches=False,
                diff_summary=(
                    f"Row count mismatch: actual={len(actual_rows)} "
                    f"vs expected={len(expected_rows)}"
                ),
                actual_count=len(actual_rows),
                expected_count=len(expected_rows),
                first_mismatch=actual_rows[0] if actual_rows else None,
            )

        if order_matters:
            for i, (a, e) in enumerate(zip(actual_rows, expected_rows)):
                if a != e:
                    return ComparisonResult(
                        matches=False,
                        diff_summary=f"Row {i} differs",
                        actual_count=len(actual_rows),
                        expected_count=len(expected_rows),
                        first_mismatch={"actual": a, "expected": e},
                    )
        else:
            actual_set = {tuple(sorted(r.items())) for r in actual_rows}
            expected_set = {tuple(sorted(r.items())) for r in expected_rows}
            if actual_set != expected_set:
                missing = expected_set - actual_set
                return ComparisonResult(
                    matches=False,
                    diff_summary=(
                        f"Set diff: {len(missing)} expected rows missing from actual"
                    ),
                    actual_count=len(actual_rows),
                    expected_count=len(expected_rows),
                    first_mismatch=dict(next(iter(missing))) if missing else None,
                )

        return ComparisonResult(
            matches=True,
            diff_summary="OK",
            actual_count=len(actual_rows),
            expected_count=len(expected_rows),
        )
