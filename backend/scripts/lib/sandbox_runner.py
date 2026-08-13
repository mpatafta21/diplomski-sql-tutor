"""Sandbox SQL runner — read-only i DML execution u ecommerce_v1 schemi."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import psycopg


_log = logging.getLogger(__name__)
_ORDER_BY_RE = re.compile(r"\bORDER\s+BY\b", re.IGNORECASE)


@dataclass
class ExecutionResult:
    success: bool
    rows: list[dict] = field(default_factory=list)
    column_names: list[str] = field(default_factory=list)
    execution_time_ms: int = 0
    error: str | None = None
    #: PG SQLSTATE uhvaćene greške (Faza 5.1) — zatvoren šifrarnik od 5 znakova
    #: (42703, 42601, 42P01, 42803…), BEZ ijednog znaka studentovog upita.
    #: 🔴 `error` (poruka) nosi doslovni redak upita i NE smije van; `sqlstate`
    #: smije. Do 5.1 se gubio jer je hvatanje radilo samo `str(e)`.
    sqlstate: str | None = None


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


def _as_decimal(v) -> Decimal | None:
    """Pretvara numeričku vrijednost u Decimal za usporedbu. bool se ne tretira kao broj."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float, Decimal)):
        return Decimal(
            str(v)
        )  # kroz str() da sačuva precision (Decimal(726.7) je garbage)
    if isinstance(v, str):
        try:
            return Decimal(v)
        except (InvalidOperation, ValueError):
            return None
    return None


def _values_equal(a, b) -> bool:
    """Uspoređuje dvije vrijednosti uz numeričku toleranciju.

    Numerička grana se aktivira ako je BAR JEDNA strana pravi numerički tip
    (int/float/Decimal, ne bool). Dva čista stringa ('007' vs '7') ne ulaze
    u numeričku granu pa ostaju različiti — štiti zip/id kodove s leading zeros.
    """
    a_num = isinstance(a, (int, float, Decimal)) and not isinstance(a, bool)
    b_num = isinstance(b, (int, float, Decimal)) and not isinstance(b, bool)
    if a_num or b_num:
        da, db = _as_decimal(a), _as_decimal(b)
        if da is not None and db is not None:
            return da == db
    return _normalize_value(a) == _normalize_value(b)


def _rows_equal(row_a: dict, row_b: dict) -> bool:
    """Uspoređuje dva reda koristeći _values_equal po svakoj koloni."""
    if row_a.keys() != row_b.keys():
        return False
    return all(_values_equal(row_a[k], row_b[k]) for k in row_a)


#: Gornja granica trajanja JEDNOG studentskog upita (PG `statement_timeout`).
#: 🔴 Imenovana je zato što o njoj ovisi tuđa odluka: Coordinatorov UPDATE prozor
#: izvodi se IZ NJE (`coordinator.DEFAULT_UPDATE_TIMEOUT`), a ne iz vlastite
#: konstante — dvije nevezane petice su bile uzrok ERRATE #63.
DEFAULT_STATEMENT_TIMEOUT_S = 5


class SandboxRunner:
    def __init__(
        self, connection_string: str, timeout_seconds: int = DEFAULT_STATEMENT_TIMEOUT_S
    ) -> None:
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
                            execution_time_ms=int((time.perf_counter() - start) * 1000),
                        )
                except psycopg.errors.QueryCanceled as e:
                    return ExecutionResult(
                        success=False,
                        error=f"Statement timeout after {self.timeout_ms}ms: {e}",
                        execution_time_ms=int((time.perf_counter() - start) * 1000),
                        sqlstate=e.sqlstate,
                    )
                except psycopg.Error as e:
                    return ExecutionResult(
                        success=False,
                        error=str(e),
                        execution_time_ms=int((time.perf_counter() - start) * 1000),
                        sqlstate=e.sqlstate,
                    )
                finally:
                    if dml:
                        try:
                            conn.rollback()
                        except Exception as rb_exc:
                            # Konekcija je vjerojatno već mrtva (statement_timeout je
                            # ubio session). Zatvaranje konekcije će svejedno rollback-ati
                            # neuspjelu transakciju. Logiramo da invarijanta "DML promjene
                            # ne perzistiraju" ne bude tiha pretpostavka.
                            _log.warning(
                                "Sandbox DML rollback failed (connection close will retry): %s",
                                rb_exc,
                            )
                # Invariant: each execute() call opens and closes its own connection.
                # The per-call rollback is safe only because no outer transaction exists.
                # If a connection pool is introduced, switch to SAVEPOINT pattern.
        except psycopg.Error as e:
            # Vanjski catch: greška pri samom spajanju (connect/SET ROLE), ne pri upitu.
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time_ms=int((time.perf_counter() - start) * 1000),
                sqlstate=e.sqlstate,
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
                if not _rows_equal(a, e):
                    return ComparisonResult(
                        matches=False,
                        diff_summary=f"Row {i} differs",
                        actual_count=len(actual_rows),
                        expected_count=len(expected_rows),
                        first_mismatch={"actual": a, "expected": e},
                    )
        else:
            # O(n²) greedy matching — potrebno jer float vs str nije hashabilno konzistentno
            remaining = list(expected_rows)
            first_unmatched: dict | None = None
            for a_row in actual_rows:
                for i, e_row in enumerate(remaining):
                    if _rows_equal(a_row, e_row):
                        remaining.pop(i)
                        break
                else:
                    first_unmatched = a_row
                    break

            if first_unmatched is not None or remaining:
                n_missing = len(remaining)
                return ComparisonResult(
                    matches=False,
                    diff_summary=(
                        f"Set diff: {n_missing} expected rows missing from actual"
                    ),
                    actual_count=len(actual_rows),
                    expected_count=len(expected_rows),
                    first_mismatch=first_unmatched or remaining[0],
                )

        return ComparisonResult(
            matches=True,
            diff_summary="OK",
            actual_count=len(actual_rows),
            expected_count=len(expected_rows),
        )
