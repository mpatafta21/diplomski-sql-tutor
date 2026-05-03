"""AST-based concept detection u SQL queryjima.

Public API: AstAnalyzer().detects_concept(query, concept_code) -> ConceptDetectionResult

Sekcije:
  1. TRIVIAL DETECTORS — single-keyword AST checks
  2. JOIN DETECTORS — FROM clause walk
  3. COMPLEX DETECTORS — subquery scope, alias resolution
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ConceptDetectionResult:
    detected: bool
    location: str | None = None
    is_in_comment: bool = False
    is_in_string: bool = False
    extra_info: dict = field(default_factory=dict)


def _strip_comments_and_strings(query: str) -> str:
    """Uklanja line comments, block comments i string literale za safe keyword search."""
    no_line = re.sub(r"--[^\n]*", "", query)
    no_block = re.sub(r"/\*.*?\*/", "", no_line, flags=re.DOTALL)
    no_strings = re.sub(r"'(?:[^'\\]|\\.)*'", "''", no_block)
    return no_strings


def _has_keyword(query: str, keyword_pattern: str) -> bool:
    """Case-insensitive keyword presence (whitespace-aware) u stripped query-ju."""
    stripped = _strip_comments_and_strings(query)
    return bool(re.search(rf"\b{keyword_pattern}\b", stripped, re.IGNORECASE))


def _keyword_only_in_comment(query: str, keyword_pattern: str) -> bool:
    """True ako keyword postoji u originalu ali ne u stripped verziji."""
    in_orig = bool(re.search(rf"\b{keyword_pattern}\b", query, re.IGNORECASE))
    in_stripped = _has_keyword(query, keyword_pattern)
    return in_orig and not in_stripped


# ============================================================================
# === TRIVIAL DETECTORS ======================================================
# ============================================================================

def _detect_select_basic(query: str) -> ConceptDetectionResult:
    if not _has_keyword(query, r"SELECT"):
        return ConceptDetectionResult(detected=False)
    stripped = _strip_comments_and_strings(query)
    has_star_only = bool(re.search(r"SELECT\s+\*\s+FROM", stripped, re.IGNORECASE))
    return ConceptDetectionResult(
        detected=True,
        location="top-level SELECT",
        extra_info={"select_star_only": has_star_only},
    )


def _detect_from_clause(query: str) -> ConceptDetectionResult:
    detected = _has_keyword(query, r"FROM")
    return ConceptDetectionResult(
        detected=detected,
        location="FROM clause" if detected else None,
        is_in_comment=(
            _keyword_only_in_comment(query, r"FROM") if not detected else False
        ),
    )


def _detect_where_filter(query: str) -> ConceptDetectionResult:
    detected = _has_keyword(query, r"WHERE")
    return ConceptDetectionResult(
        detected=detected,
        location="WHERE clause" if detected else None,
        is_in_comment=(
            _keyword_only_in_comment(query, r"WHERE") if not detected else False
        ),
    )


def _detect_order_by(query: str) -> ConceptDetectionResult:
    detected = _has_keyword(query, r"ORDER\s+BY")
    return ConceptDetectionResult(
        detected=detected, location="ORDER BY" if detected else None
    )


def _detect_limit_offset(query: str) -> ConceptDetectionResult:
    detected = _has_keyword(query, r"LIMIT") or _has_keyword(query, r"OFFSET")
    return ConceptDetectionResult(
        detected=detected, location="LIMIT/OFFSET" if detected else None
    )


def _detect_distinct(query: str) -> ConceptDetectionResult:
    stripped = _strip_comments_and_strings(query)
    detected = bool(re.search(r"SELECT\s+DISTINCT", stripped, re.IGNORECASE))
    return ConceptDetectionResult(
        detected=detected, location="SELECT DISTINCT" if detected else None
    )


def _detect_group_by(query: str) -> ConceptDetectionResult:
    detected = _has_keyword(query, r"GROUP\s+BY")
    return ConceptDetectionResult(
        detected=detected, location="GROUP BY" if detected else None
    )


def _detect_having_filter(query: str) -> ConceptDetectionResult:
    detected = _has_keyword(query, r"HAVING")
    return ConceptDetectionResult(
        detected=detected, location="HAVING" if detected else None
    )


def _detect_agg_count(query: str) -> ConceptDetectionResult:
    stripped = _strip_comments_and_strings(query)
    detected = bool(re.search(r"\bCOUNT\s*\(", stripped, re.IGNORECASE))
    return ConceptDetectionResult(
        detected=detected, location="COUNT()" if detected else None
    )


def _detect_agg_sum_avg(query: str) -> ConceptDetectionResult:
    stripped = _strip_comments_and_strings(query)
    detected = bool(re.search(r"\b(SUM|AVG)\s*\(", stripped, re.IGNORECASE))
    return ConceptDetectionResult(
        detected=detected, location="SUM/AVG()" if detected else None
    )


def _detect_agg_min_max(query: str) -> ConceptDetectionResult:
    stripped = _strip_comments_and_strings(query)
    detected = bool(re.search(r"\b(MIN|MAX)\s*\(", stripped, re.IGNORECASE))
    return ConceptDetectionResult(
        detected=detected, location="MIN/MAX()" if detected else None
    )


def _detect_insert(query: str) -> ConceptDetectionResult:
    detected = _has_keyword(query, r"INSERT\s+INTO")
    return ConceptDetectionResult(
        detected=detected, location="INSERT" if detected else None
    )


def _detect_update(query: str) -> ConceptDetectionResult:
    stripped = _strip_comments_and_strings(query)
    detected = bool(
        re.search(r"\bUPDATE\b.*\bSET\b", stripped, re.IGNORECASE | re.DOTALL)
    )
    return ConceptDetectionResult(
        detected=detected, location="UPDATE...SET" if detected else None
    )


def _detect_delete(query: str) -> ConceptDetectionResult:
    detected = _has_keyword(query, r"DELETE\s+FROM")
    return ConceptDetectionResult(
        detected=detected, location="DELETE" if detected else None
    )


def _detect_explain_plan(query: str) -> ConceptDetectionResult:
    stripped = _strip_comments_and_strings(query).lstrip()
    detected = stripped.upper().startswith("EXPLAIN")
    return ConceptDetectionResult(
        detected=detected, location="leading EXPLAIN" if detected else None
    )


def _detect_null_handling(query: str) -> ConceptDetectionResult:
    stripped = _strip_comments_and_strings(query)
    patterns = [
        r"\bIS\s+NULL\b",
        r"\bIS\s+NOT\s+NULL\b",
        r"\bCOALESCE\s*\(",
        r"\bNULLIF\s*\(",
    ]
    found = next((p for p in patterns if re.search(p, stripped, re.IGNORECASE)), None)
    return ConceptDetectionResult(
        detected=found is not None,
        location=f"NULL-handling: {found}" if found else None,
    )


def _detect_column_alias(query: str) -> ConceptDetectionResult:
    stripped = _strip_comments_and_strings(query)
    detected = bool(re.search(r"\b\w+\s+AS\s+\w+\b", stripped, re.IGNORECASE))
    return ConceptDetectionResult(
        detected=detected, location="AS alias" if detected else None
    )


# ============================================================================
# === JOIN DETECTORS =========================================================
# ============================================================================

def _join_keyword_present(query: str, prefix: str | None) -> bool:
    """Checks for `<prefix> JOIN` (or bare INNER/JOIN if prefix=None) in stripped query."""
    stripped = _strip_comments_and_strings(query)
    if prefix is None:
        # bare JOIN (INNER) — must NOT be preceded by LEFT/RIGHT/FULL/CROSS/OUTER
        for match in re.finditer(r"\bJOIN\b", stripped, re.IGNORECASE):
            start = max(0, match.start() - 30)
            preceding = stripped[start:match.start()]
            if not re.search(
                r"\b(LEFT|RIGHT|FULL|CROSS|OUTER)\s*$",
                preceding,
                re.IGNORECASE,
            ):
                return True
        return False
    pat = rf"\b{prefix}\s+(OUTER\s+)?JOIN\b"
    return bool(re.search(pat, stripped, re.IGNORECASE))


def _detect_inner_join(query: str) -> ConceptDetectionResult:
    detected = _join_keyword_present(query, prefix=None) or _join_keyword_present(
        query, prefix="INNER"
    )
    return ConceptDetectionResult(
        detected=detected, location="FROM clause" if detected else None
    )


def _detect_left_join(query: str) -> ConceptDetectionResult:
    detected = _join_keyword_present(query, prefix="LEFT")
    return ConceptDetectionResult(
        detected=detected, location="FROM clause" if detected else None
    )


def _detect_right_join(query: str) -> ConceptDetectionResult:
    detected = _join_keyword_present(query, prefix="RIGHT")
    return ConceptDetectionResult(
        detected=detected, location="FROM clause" if detected else None
    )


def _detect_full_outer_join(query: str) -> ConceptDetectionResult:
    detected = _join_keyword_present(query, prefix="FULL")
    return ConceptDetectionResult(
        detected=detected, location="FROM clause" if detected else None
    )


def _detect_cross_join(query: str) -> ConceptDetectionResult:
    stripped = _strip_comments_and_strings(query)
    detected = bool(re.search(r"\bCROSS\s+JOIN\b", stripped, re.IGNORECASE))
    return ConceptDetectionResult(
        detected=detected, location="FROM clause" if detected else None
    )


def _detect_join_condition(query: str) -> ConceptDetectionResult:
    stripped = _strip_comments_and_strings(query)
    detected = bool(
        re.search(r"\bJOIN\b.*?\bON\b", stripped, re.IGNORECASE | re.DOTALL)
    )
    return ConceptDetectionResult(
        detected=detected, location="JOIN ... ON ..." if detected else None
    )


def _detect_multi_table_join(query: str) -> ConceptDetectionResult:
    """Detect ≥3 tables in FROM/JOIN."""
    stripped = _strip_comments_and_strings(query)
    join_count = len(re.findall(r"\bJOIN\b", stripped, re.IGNORECASE))
    has_from = bool(re.search(r"\bFROM\b", stripped, re.IGNORECASE))
    table_count = (join_count + 1) if has_from else 0
    detected = table_count >= 3
    return ConceptDetectionResult(
        detected=detected,
        location=f"{table_count} tables in FROM/JOIN" if detected else None,
        extra_info={"table_count": table_count},
    )


# ============================================================================
# === COMPLEX DETECTORS (Sub-task 5C) ========================================
# ============================================================================
# placeholder — implementacija u Sub-task 5C


# ============================================================================
# === DISPATCH TABLE + PUBLIC API ============================================
# ============================================================================

_DETECTORS: dict[str, Callable[[str], ConceptDetectionResult]] = {
    # TRIVIAL
    "select_basic": _detect_select_basic,
    "from_clause": _detect_from_clause,
    "where_filter": _detect_where_filter,
    "order_by": _detect_order_by,
    "limit_offset": _detect_limit_offset,
    "distinct": _detect_distinct,
    "group_by": _detect_group_by,
    "having_filter": _detect_having_filter,
    "agg_count": _detect_agg_count,
    "agg_sum_avg": _detect_agg_sum_avg,
    "agg_min_max": _detect_agg_min_max,
    "insert": _detect_insert,
    "update": _detect_update,
    "delete": _detect_delete,
    "explain_plan": _detect_explain_plan,
    "null_handling": _detect_null_handling,
    "column_alias": _detect_column_alias,
    # JOIN
    "inner_join": _detect_inner_join,
    "left_join": _detect_left_join,
    "right_join": _detect_right_join,
    "full_outer_join": _detect_full_outer_join,
    "cross_join": _detect_cross_join,
    "join_condition": _detect_join_condition,
    "multi_table_join": _detect_multi_table_join,
    # COMPLEX dodaje se u Sub-task 5C
}


class AstAnalyzer:
    def detects_concept(
        self, query: str, concept_code: str
    ) -> ConceptDetectionResult:
        if concept_code not in _DETECTORS:
            raise NotImplementedError(
                f"Detector for concept '{concept_code}' not implemented yet"
            )
        return _DETECTORS[concept_code](query)
