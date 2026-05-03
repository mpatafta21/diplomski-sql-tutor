"""3-razinska validacija generiranog SQL zadatka."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

import sqlparse

from app.schemas.generated_task import GeneratedTask
from scripts.lib.ast_analyzer import AstAnalyzer
from scripts.lib.sandbox_runner import SandboxRunner


@dataclass
class ValidationFailure:
    level: Literal["syntax", "concept_coverage", "result_match"]
    code: str
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    passed: bool
    failures: list[ValidationFailure] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# Belt-and-suspenders blacklist. SandboxRunner already runs queries kao
# sandbox_readonly role pa write-ovi puknu na razini Postgres-a. Ovi pattern-i
# fail-aju brže s jasnijim error code-om za debug. Module 4 (insert/update/delete)
# zadatci su legitimni — NE blanket-blockaj DML, samo destructive DDL.
_DANGEROUS_PATTERNS = [
    r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b",
    r"\bTRUNCATE\b",
]


class TaskValidator:
    def __init__(
        self,
        sandbox_runner: SandboxRunner,
        ast_analyzer: AstAnalyzer,
    ) -> None:
        self.runner = sandbox_runner
        self.analyzer = ast_analyzer

    def validate(self, task: GeneratedTask) -> ValidationResult:
        # razina 1
        syntax_failure = self._check_syntax(task.expected_query)
        if syntax_failure:
            return ValidationResult(passed=False, failures=[syntax_failure])

        # razina 2
        coverage_failure = self._check_concept_coverage(task)
        if coverage_failure:
            return ValidationResult(passed=False, failures=[coverage_failure])

        # razina 3
        result_failure = self._check_result_match(task)
        if result_failure:
            return ValidationResult(passed=False, failures=[result_failure])

        return ValidationResult(passed=True)

    def _check_syntax(self, query: str) -> ValidationFailure | None:
        if not query.strip():
            return ValidationFailure(
                level="syntax", code="empty_query", message="Query je prazan"
            )
        try:
            parsed = sqlparse.parse(query)
            if not parsed or all(stmt.tokens == [] for stmt in parsed):
                return ValidationFailure(
                    level="syntax",
                    code="parse_failed",
                    message="sqlparse vratio prazan AST",
                )
        except Exception as e:  # pragma: no cover
            return ValidationFailure(
                level="syntax", code="parse_exception", message=str(e)
            )

        for pat in _DANGEROUS_PATTERNS:
            if re.search(pat, query, re.IGNORECASE):
                return ValidationFailure(
                    level="syntax",
                    code="dangerous_pattern",
                    message=f"Query sadrži potencijalno destruktivan pattern: {pat}",
                )
        return None

    def _check_concept_coverage(
        self, task: GeneratedTask
    ) -> ValidationFailure | None:
        try:
            r = self.analyzer.detects_concept(
                task.expected_query, task.primary_concept
            )
        except NotImplementedError as e:
            return ValidationFailure(
                level="concept_coverage",
                code="detector_not_implemented",
                message=str(e),
            )
        except Exception as e:
            # Bilo koja crash u AstAnalyzer-u (malformed SQL, sqlparse bug)
            # pretvori u ValidationFailure umjesto da propagira u CLI.
            return ValidationFailure(
                level="concept_coverage",
                code="detector_crashed",
                message=f"AstAnalyzer raised {type(e).__name__}: {e}",
                details={"exception_type": type(e).__name__},
            )
        if not r.detected:
            return ValidationFailure(
                level="concept_coverage",
                code="primary_concept_not_detected",
                message=(
                    f"Primarni koncept '{task.primary_concept}' nije pronađen u "
                    f"expected_query"
                ),
                details={
                    "is_in_comment": r.is_in_comment,
                    "is_in_string": r.is_in_string,
                    **r.extra_info,
                },
            )
        return None

    def _check_result_match(
        self, task: GeneratedTask
    ) -> ValidationFailure | None:
        try:
            actual = self.runner.execute(task.expected_query)
        except Exception as e:
            # Defense — runner trebao bi vratiti ExecutionResult(success=False)
            # ali ako baci, ne ruši cijeli batch.
            return ValidationFailure(
                level="result_match",
                code="runner_crashed",
                message=f"SandboxRunner raised {type(e).__name__}: {e}",
                details={"exception_type": type(e).__name__},
            )

        if not actual.success:
            return ValidationFailure(
                level="result_match",
                code="execution_failed",
                message=f"Sandbox execution fail: {actual.error}",
            )

        try:
            cmp = self.runner.compare(
                actual, task.expected_result, query=task.expected_query
            )
        except Exception as e:
            return ValidationFailure(
                level="result_match",
                code="comparison_crashed",
                message=f"compare() raised {type(e).__name__}: {e}",
                details={"exception_type": type(e).__name__},
            )

        if not cmp.matches:
            return ValidationFailure(
                level="result_match",
                code="row_mismatch",
                message=cmp.diff_summary,
                details={
                    "actual_count": cmp.actual_count,
                    "expected_count": cmp.expected_count,
                    "first_mismatch": cmp.first_mismatch,
                },
            )
        return None
