"""Smoke test: dokazuje da snapshot čuva expected_result kao izvor istine.

Izvršava expected_query kroz SandboxRunner na snapshot stanju sandboxa i
uspoređuje s expected_result iz baze. 5 determinističkih taskova koji pokrivaju:
  - NUMERIC/Decimal koercion (SUM/AVG total_amount, price)
  - JOIN (inner, multi-table)
  - Agregacija s HAVING
  - Visoka težina (d=4, d=5)

Pokretanje:
    uv run python -m scripts.smoke_test_dataset
"""

from __future__ import annotations

import logging
import os
import sys

from sqlalchemy import select

from app.db.models import Task
from app.db.session import SessionLocal
from scripts.lib.sandbox_runner import SandboxRunner

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("smoke_test")

# 5 deterministički odabranih taskova — pokrivenost:
#   1. agg_sum_avg_d3: SUM(total_amount) → NUMERIC/Decimal koercion
#   2. inner_join_d4: INNER JOIN + SUM(unit_price) → d=4 + NUMERIC
#   3. having_filter_d4: agregacija + HAVING + AVG(price) → d=4
#   4. multi_table_join_d5: 3-way JOIN → d=5
#   5. agg_count_d3: GROUP BY + COUNT → čista agregacija
SMOKE_TASK_IDS = [
    "agg_sum_avg_d3_manual_f239bc99",
    "inner_join_d4_17bb7fc0",
    "having_filter_d4_manual_6da34957",
    "multi_table_join_d5_480aec3f",
    "agg_count_d3_manual_9cbaf74e",
]

SANDBOX_URL_RAW = os.environ.get(
    "SANDBOX_DATABASE_URL",
    "postgresql+psycopg://sandbox_admin:sandbox_dev_password@localhost:5433/sandbox",
)
SANDBOX_CONN = SANDBOX_URL_RAW.replace("postgresql+psycopg://", "postgresql://")


def main() -> None:
    runner = SandboxRunner(SANDBOX_CONN)
    passed = 0
    failed = 0

    with SessionLocal() as session:
        for source_id in SMOKE_TASK_IDS:
            task = session.execute(
                select(Task).where(Task.source_id == source_id)
            ).scalar_one_or_none()

            if task is None:
                log.error("NIJE PRONAĐEN: %s — provjeri import.", source_id)
                failed += 1
                continue

            actual = runner.execute(task.expected_query, schema="ecommerce_v1")
            if not actual.success:
                log.error(
                    "EXECUTION ERROR [%s]: %s",
                    source_id,
                    actual.error,
                )
                failed += 1
                continue

            cmp = runner.compare(
                actual, task.expected_result, query=task.expected_query
            )
            if cmp.matches:
                log.info(
                    "OK  [%s] — %d redaka, %dms",
                    source_id,
                    cmp.actual_count,
                    actual.execution_time_ms,
                )
                passed += 1
            else:
                log.error(
                    "MISMATCH [%s]: %s",
                    source_id,
                    cmp.diff_summary,
                )
                log.error(
                    "  actual  (prvih 3): %s",
                    actual.rows[:3],
                )
                log.error(
                    "  expected (prvih 3): %s",
                    task.expected_result[:3] if task.expected_result else [],
                )
                if cmp.first_mismatch:
                    log.error("  first_mismatch: %s", cmp.first_mismatch)
                failed += 1

    log.info("--- Rezultat: %d/5 prošlo ---", passed)
    if failed > 0:
        log.error("%d taskova nije prošlo smoke test.", failed)
        sys.exit(1)


if __name__ == "__main__":
    main()
