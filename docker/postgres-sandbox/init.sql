-- ==========================================================
-- docker/postgres-sandbox/init.sql
-- Sandbox shema za SQL tutor — e-commerce domena (8 tablica).
-- Izvor istine: docs/faza-1-domenski-model.md §7.3.
-- ==========================================================

CREATE SCHEMA IF NOT EXISTS ecommerce_v1;
SET search_path TO ecommerce_v1;

-- ----------------------------------------------------------
-- Role-ovi
-- ----------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sandbox_readonly') THEN
        CREATE ROLE sandbox_readonly NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sandbox_readwrite') THEN
        CREATE ROLE sandbox_readwrite NOINHERIT;
    END IF;
END$$;

-- ----------------------------------------------------------
-- Tablice
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE,
    description     TEXT
);

CREATE TABLE IF NOT EXISTS suppliers (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    country         VARCHAR(50) NOT NULL,
    contact_email   VARCHAR(255),
    rating          NUMERIC(3,2) CHECK (rating BETWEEN 0 AND 5)
);

CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    category_id     INTEGER REFERENCES categories(id),
    supplier_id     INTEGER REFERENCES suppliers(id),
    price           NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    stock           INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    is_discontinued BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS customers (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    country         VARCHAR(50),
    city            VARCHAR(100),
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employees (
    id              SERIAL PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    manager_id      INTEGER REFERENCES employees(id),
    department      VARCHAR(50) NOT NULL,
    salary          NUMERIC(10,2) NOT NULL CHECK (salary >= 0),
    hired_at        DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    employee_id     INTEGER REFERENCES employees(id),
    order_date      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),
    total_amount    NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0)
);

CREATE TABLE IF NOT EXISTS order_items (
    id              SERIAL PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),
    UNIQUE(order_id, product_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    rating          INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment         TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(product_id, customer_id)
);

-- ----------------------------------------------------------
-- Indeksi (Modul 6 — EXPLAIN zadaci)
-- ----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_orders_customer      ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_employee      ON orders(employee_id) WHERE employee_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_orders_date          ON orders(order_date DESC);
CREATE INDEX IF NOT EXISTS idx_order_items_order    ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product  ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_products_category    ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_supplier    ON products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product      ON reviews(product_id);

-- ----------------------------------------------------------
-- Grants
-- ----------------------------------------------------------
GRANT USAGE ON SCHEMA ecommerce_v1 TO sandbox_readonly, sandbox_readwrite;

GRANT SELECT ON ALL TABLES IN SCHEMA ecommerce_v1 TO sandbox_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA ecommerce_v1
    GRANT SELECT ON TABLES TO sandbox_readonly;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ecommerce_v1 TO sandbox_readwrite;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ecommerce_v1 TO sandbox_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA ecommerce_v1
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sandbox_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA ecommerce_v1
    GRANT USAGE, SELECT ON SEQUENCES TO sandbox_readwrite;
