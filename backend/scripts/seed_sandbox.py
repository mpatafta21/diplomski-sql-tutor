"""Reproducibilan seed sandbox baze (ecommerce_v1).

Pokretanje:
    cd backend && uv run python -m scripts.seed_sandbox

Veličine i invariante prema §7.4 dokumenta `faza-1-domenski-model.md`.
Seedovi: Faker.seed(42), random.seed(42) — svaki run daje iste podatke.
"""

from __future__ import annotations

import random
from datetime import timezone
from decimal import Decimal
from itertools import count

import psycopg
from faker import Faker

from app.core.config import SANDBOX_DATABASE_URL

# --- Konfiguracija veličina (§7.4) ---
N_CATEGORIES = 15
N_SUPPLIERS = 30
N_PRODUCTS = 100
N_CUSTOMERS = 200
N_EMPLOYEES = 50
N_ORDERS = 1000
N_ORDER_ITEMS = 3000
N_REVIEWS = 500

# --- Invariante (§7.4 edge cases) ---
CUSTOMERS_WITHOUT_ORDERS = 25
PRODUCTS_WITHOUT_REVIEWS = 12
ORDER_EMPLOYEE_NULL_RATIO = 0.30
STATUS_DISTRIBUTION = [
    ("delivered", 0.50),
    ("shipped", 0.20),
    ("processing", 0.15),
    ("pending", 0.10),
    ("cancelled", 0.05),
]

CATEGORY_NAMES = [
    "Electronics", "Books", "Sports", "Home", "Garden",
    "Toys", "Clothing", "Beauty", "Automotive", "Music",
    "Movies", "Office", "Pet Supplies", "Tools", "Health",
]
DEPARTMENTS = ["Sales", "Engineering", "Support", "Marketing", "Operations"]
SUPPLIER_COUNTRIES = ["Croatia", "Germany", "Italy", "USA"]

TABLES_IN_TRUNCATE_ORDER = [
    "reviews", "order_items", "orders",
    "products", "employees", "customers", "suppliers", "categories",
]


def _connect() -> psycopg.Connection:
    if not SANDBOX_DATABASE_URL:
        raise RuntimeError("SANDBOX_DATABASE_URL nije postavljen u .env")
    # SQLAlchemy URL `postgresql+psycopg://...` → psycopg očekuje `postgresql://...`
    url = SANDBOX_DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)
    # statement_timeout=0 — bulk seed može trajati duže od dev 5s limita
    return psycopg.connect(
        url, options="-c search_path=ecommerce_v1 -c statement_timeout=0"
    )


def _truncate(cur: psycopg.Cursor) -> None:
    cur.execute(
        "TRUNCATE TABLE "
        + ", ".join(TABLES_IN_TRUNCATE_ORDER)
        + " RESTART IDENTITY CASCADE"
    )


def _seed_categories(cur, fake: Faker) -> None:
    rows = [(name, fake.sentence(nb_words=8)) for name in CATEGORY_NAMES]
    cur.executemany(
        "INSERT INTO categories (name, description) VALUES (%s, %s)", rows
    )


def _seed_suppliers(cur, fake: Faker) -> None:
    rows = []
    for i in range(N_SUPPLIERS):
        country = SUPPLIER_COUNTRIES[i % len(SUPPLIER_COUNTRIES)]
        rows.append((
            fake.company(),
            country,
            fake.company_email(),
            round(random.uniform(2.5, 5.0), 2),
        ))
    cur.executemany(
        "INSERT INTO suppliers (name, country, contact_email, rating) "
        "VALUES (%s, %s, %s, %s)",
        rows,
    )


def _seed_products(cur, fake: Faker) -> None:
    rows = []
    for _ in range(N_PRODUCTS):
        rows.append((
            fake.catch_phrase()[:200],
            random.randint(1, N_CATEGORIES),
            random.randint(1, N_SUPPLIERS),
            round(random.uniform(5.0, 999.0), 2),
            random.randint(0, 500),
            random.random() < 0.05,
            fake.date_time_between(start_date="-2y", tzinfo=timezone.utc),
        ))
    cur.executemany(
        """INSERT INTO products
           (name, category_id, supplier_id, price, stock, is_discontinued, created_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        rows,
    )


def _seed_customers(cur) -> None:
    """Miks hr_HR (70%) i en_US (30%) lokala."""
    fake_hr = Faker("hr_HR")
    fake_us = Faker("en_US")
    Faker.seed(42)
    used_emails: set[str] = set()
    rows = []
    email_counter = count(1)
    for i in range(N_CUSTOMERS):
        f = fake_hr if i % 10 < 7 else fake_us
        first = f.first_name()
        last = f.last_name()
        base_email = f.unique.email() if hasattr(f, "unique") else f.email()
        email = base_email
        while email in used_emails:
            email = f"user{next(email_counter)}_{base_email}"
        used_emails.add(email)
        rows.append((
            first, last, email,
            f.country() if f is fake_us else "Croatia",
            f.city(),
            f.date_time_between(start_date="-3y", tzinfo=timezone.utc),
        ))
    cur.executemany(
        """INSERT INTO customers
           (first_name, last_name, email, country, city, registered_at)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        rows,
    )


def _seed_employees(cur, fake: Faker) -> None:
    """Hijerarhija: 1 CEO + 4 VP + 10 manager + 35 rep = 50."""
    rows: list[tuple] = []
    rows.append((
        fake.first_name(), fake.last_name(), "ceo@tutor.example",
        None, "Executive",
        round(random.uniform(15000, 25000), 2),
        fake.date_between(start_date="-15y", end_date="-10y"),
    ))
    for i in range(4):
        rows.append((
            fake.first_name(), fake.last_name(), f"vp{i}@tutor.example",
            1, random.choice(DEPARTMENTS),
            round(random.uniform(8000, 14000), 2),
            fake.date_between(start_date="-10y", end_date="-7y"),
        ))
    for i in range(10):
        rows.append((
            fake.first_name(), fake.last_name(), f"mgr{i}@tutor.example",
            random.randint(2, 5), random.choice(DEPARTMENTS),
            round(random.uniform(4000, 7500), 2),
            fake.date_between(start_date="-7y", end_date="-3y"),
        ))
    for i in range(N_EMPLOYEES - 15):
        rows.append((
            fake.first_name(), fake.last_name(), f"rep{i}@tutor.example",
            random.randint(6, 15), random.choice(DEPARTMENTS),
            round(random.uniform(1500, 3500), 2),
            fake.date_between(start_date="-5y", end_date="-1y"),
        ))
    cur.executemany(
        """INSERT INTO employees
           (first_name, last_name, email, manager_id, department, salary, hired_at)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        rows,
    )


def _pick_status() -> str:
    r = random.random()
    cumulative = 0.0
    for status, weight in STATUS_DISTRIBUTION:
        cumulative += weight
        if r < cumulative:
            return status
    return STATUS_DISTRIBUTION[-1][0]


def _seed_orders(cur, fake: Faker) -> list[int]:
    eligible_customers = N_CUSTOMERS - CUSTOMERS_WITHOUT_ORDERS
    rows = []
    for _ in range(N_ORDERS):
        customer_id = random.randint(1, eligible_customers)
        employee_id = (
            None if random.random() < ORDER_EMPLOYEE_NULL_RATIO
            else random.randint(1, N_EMPLOYEES)
        )
        rows.append((
            customer_id, employee_id,
            fake.date_time_between(start_date="-1y", tzinfo=timezone.utc),
            _pick_status(),
            Decimal("0"),
        ))
    cur.executemany(
        """INSERT INTO orders
           (customer_id, employee_id, order_date, status, total_amount)
           VALUES (%s, %s, %s, %s, %s)""",
        rows,
    )
    return list(range(1, N_ORDERS + 1))


def _seed_order_items(cur, order_ids: list[int]) -> None:
    seen: set[tuple[int, int]] = set()
    rows: list[tuple] = []
    for oid in order_ids:
        pid = random.randint(1, N_PRODUCTS)
        seen.add((oid, pid))
        rows.append((oid, pid, random.randint(1, 5),
                     round(random.uniform(5, 999), 2)))
    while len(rows) < N_ORDER_ITEMS:
        oid = random.choice(order_ids)
        pid = random.randint(1, N_PRODUCTS)
        if (oid, pid) in seen:
            continue
        seen.add((oid, pid))
        rows.append((oid, pid, random.randint(1, 5),
                     round(random.uniform(5, 999), 2)))
    cur.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
        "VALUES (%s, %s, %s, %s)",
        rows,
    )


def _update_order_totals(cur) -> None:
    cur.execute("""
        UPDATE orders o
        SET total_amount = sub.total
        FROM (
            SELECT order_id, SUM(quantity * unit_price) AS total
            FROM order_items
            GROUP BY order_id
        ) sub
        WHERE o.id = sub.order_id
    """)


def _seed_reviews(cur, fake: Faker) -> None:
    eligible_products = N_PRODUCTS - PRODUCTS_WITHOUT_REVIEWS
    seen: set[tuple[int, int]] = set()
    rows: list[tuple] = []
    while len(rows) < N_REVIEWS:
        pid = random.randint(1, eligible_products)
        cid = random.randint(1, N_CUSTOMERS)
        if (pid, cid) in seen:
            continue
        seen.add((pid, cid))
        rows.append((
            pid, cid, random.randint(1, 5),
            fake.sentence(nb_words=12),
            fake.date_time_between(start_date="-1y", tzinfo=timezone.utc),
        ))
    cur.executemany(
        """INSERT INTO reviews
           (product_id, customer_id, rating, comment, created_at)
           VALUES (%s, %s, %s, %s, %s)""",
        rows,
    )


def main() -> None:
    """Glavna seed funkcija — idempotentna, reproducibilna."""
    Faker.seed(42)
    random.seed(42)
    fake = Faker("en_US")

    with _connect() as conn, conn.cursor() as cur:
        _truncate(cur)
        _seed_categories(cur, fake)
        _seed_suppliers(cur, fake)
        _seed_products(cur, fake)
        _seed_customers(cur)
        _seed_employees(cur, fake)
        order_ids = _seed_orders(cur, fake)
        _seed_order_items(cur, order_ids)
        _update_order_totals(cur)
        _seed_reviews(cur, fake)
        conn.commit()
    print("Seed gotov: 15/30/100/200/50/1000/3000/500 redova.")


if __name__ == "__main__":
    main()
