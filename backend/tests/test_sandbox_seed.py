"""Invariante reproducibilnog seed-a sandbox baze (§7.4 + edge cases)."""

from __future__ import annotations

import os

import psycopg
import pytest

_RAW_URL = os.getenv("SANDBOX_DATABASE_URL")
SANDBOX_URL = (
    _RAW_URL.replace("postgresql+psycopg://", "postgresql://", 1)
    if _RAW_URL else None
)
EXPECTED_COUNTS = {
    "categories": 15,
    "suppliers": 30,
    "products": 100,
    "customers": 200,
    "employees": 50,
    "orders": 1000,
    "order_items": 3000,
    "reviews": 500,
}


@pytest.fixture(scope="module")
def conn():
    if not SANDBOX_URL:
        pytest.skip("SANDBOX_DATABASE_URL nije postavljen")
    with psycopg.connect(
        SANDBOX_URL,
        options="-c search_path=ecommerce_v1",
        autocommit=True,
    ) as c:
        yield c


@pytest.mark.parametrize("table,expected", list(EXPECTED_COUNTS.items()))
def test_row_counts(conn, table, expected):
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        assert cur.fetchone()[0] == expected


def test_at_least_20_customers_without_orders(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM customers c
            LEFT JOIN orders o ON o.customer_id = c.id
            WHERE o.id IS NULL
        """)
        assert cur.fetchone()[0] >= 20


def test_at_least_10_products_without_reviews(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM products p
            LEFT JOIN reviews r ON r.product_id = p.id
            WHERE r.id IS NULL
        """)
        assert cur.fetchone()[0] >= 10


def test_exactly_one_ceo(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM employees WHERE manager_id IS NULL")
        assert cur.fetchone()[0] == 1


def test_orders_employee_id_null_ratio(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
              SUM(CASE WHEN employee_id IS NULL THEN 1 ELSE 0 END)::float / COUNT(*)
            FROM orders
        """)
        ratio = float(cur.fetchone()[0])
        assert 0.25 <= ratio <= 0.35, f"NULL ratio = {ratio:.3f}, expected ≈ 0.30"


def test_orders_status_distribution(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
        dist = {row[0]: row[1] for row in cur.fetchall()}
    assert set(dist) == {"pending", "processing", "shipped", "delivered", "cancelled"}
    assert dist["delivered"] >= 400


def test_reproducibility(conn):
    """Pokreni seed dvaput, count-ovi i jedan sample row identični."""
    from scripts.seed_sandbox import main as seed_main

    seed_main()
    with conn.cursor() as cur:
        cur.execute("SELECT email FROM customers ORDER BY id LIMIT 1")
        first_email_run1 = cur.fetchone()[0]

    seed_main()
    with conn.cursor() as cur:
        for table, expected in EXPECTED_COUNTS.items():
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            assert cur.fetchone()[0] == expected, table
        cur.execute("SELECT email FROM customers ORDER BY id LIMIT 1")
        assert cur.fetchone()[0] == first_email_run1
