/**
 * Statička shema sandbox baze `ecommerce_v1` (Faza 4.3a).
 *
 * ⚠️ IZVOR: docker/postgres-sandbox/init.sql (zamrznuta shema,
 * manifest SHA-256: 82fd7f51ccf59854488a4b4ec59b86a3bbbc480b603d15e4b25ac6ed4d304aa3).
 * Ovo je NAMJERNO duplicirano u frontend (odluka D-ER: statički prikaz, bez
 * /schema rute). AKO SE SANDBOX SHEMA PROMIJENI, OVA DATOTEKA SE MORA
 * AŽURIRATI (i SHA u ovom komentaru).
 *
 * Prepisano 1:1 iz init.sql — tablice, stupci, tipovi, PK/FK/UNIQUE.
 * Bez sample redaka (podaci su Faker seed, nisu u init.sql).
 */

export interface SchemaColumn {
  name: string
  /** SQL tip kako ga student piše (VARCHAR(100), NUMERIC(10,2), ...). */
  type: string
  pk?: boolean
  /** FK meta: "tablica.stupac" (self-FK uključen: employees.manager_id). */
  fk?: string
  notNull?: boolean
  unique?: boolean
}

export interface SchemaTable {
  name: string
  columns: SchemaColumn[]
  /** Kompozitni UNIQUE constrainti (prikaz u footeru tablice). */
  uniques?: string[]
}

export const SANDBOX_SCHEMA_NAME = "ecommerce_v1"

export const SANDBOX_TABLES: SchemaTable[] = [
  {
    name: "categories",
    columns: [
      { name: "id", type: "SERIAL", pk: true },
      { name: "name", type: "VARCHAR(100)", notNull: true, unique: true },
      { name: "description", type: "TEXT" },
    ],
  },
  {
    name: "suppliers",
    columns: [
      { name: "id", type: "SERIAL", pk: true },
      { name: "name", type: "VARCHAR(150)", notNull: true },
      { name: "country", type: "VARCHAR(50)", notNull: true },
      { name: "contact_email", type: "VARCHAR(255)" },
      { name: "rating", type: "NUMERIC(3,2)" },
    ],
  },
  {
    name: "products",
    columns: [
      { name: "id", type: "SERIAL", pk: true },
      { name: "name", type: "VARCHAR(200)", notNull: true },
      { name: "category_id", type: "INTEGER", fk: "categories.id" },
      { name: "supplier_id", type: "INTEGER", fk: "suppliers.id" },
      { name: "price", type: "NUMERIC(10,2)", notNull: true },
      { name: "stock", type: "INTEGER", notNull: true },
      { name: "is_discontinued", type: "BOOLEAN", notNull: true },
      { name: "created_at", type: "TIMESTAMPTZ", notNull: true },
    ],
  },
  {
    name: "customers",
    columns: [
      { name: "id", type: "SERIAL", pk: true },
      { name: "first_name", type: "VARCHAR(100)", notNull: true },
      { name: "last_name", type: "VARCHAR(100)", notNull: true },
      { name: "email", type: "VARCHAR(255)", notNull: true, unique: true },
      { name: "country", type: "VARCHAR(50)" },
      { name: "city", type: "VARCHAR(100)" },
      { name: "registered_at", type: "TIMESTAMPTZ", notNull: true },
    ],
  },
  {
    name: "employees",
    columns: [
      { name: "id", type: "SERIAL", pk: true },
      { name: "first_name", type: "VARCHAR(100)", notNull: true },
      { name: "last_name", type: "VARCHAR(100)", notNull: true },
      { name: "email", type: "VARCHAR(255)", notNull: true, unique: true },
      { name: "manager_id", type: "INTEGER", fk: "employees.id" },
      { name: "department", type: "VARCHAR(50)", notNull: true },
      { name: "salary", type: "NUMERIC(10,2)", notNull: true },
      { name: "hired_at", type: "DATE", notNull: true },
    ],
  },
  {
    name: "orders",
    columns: [
      { name: "id", type: "SERIAL", pk: true },
      {
        name: "customer_id",
        type: "INTEGER",
        notNull: true,
        fk: "customers.id",
      },
      { name: "employee_id", type: "INTEGER", fk: "employees.id" },
      { name: "order_date", type: "TIMESTAMPTZ", notNull: true },
      { name: "status", type: "VARCHAR(20)", notNull: true },
      { name: "total_amount", type: "NUMERIC(10,2)", notNull: true },
    ],
  },
  {
    name: "order_items",
    columns: [
      { name: "id", type: "SERIAL", pk: true },
      { name: "order_id", type: "INTEGER", notNull: true, fk: "orders.id" },
      { name: "product_id", type: "INTEGER", notNull: true, fk: "products.id" },
      { name: "quantity", type: "INTEGER", notNull: true },
      { name: "unit_price", type: "NUMERIC(10,2)", notNull: true },
    ],
    uniques: ["(order_id, product_id)"],
  },
  {
    name: "reviews",
    columns: [
      { name: "id", type: "SERIAL", pk: true },
      { name: "product_id", type: "INTEGER", notNull: true, fk: "products.id" },
      {
        name: "customer_id",
        type: "INTEGER",
        notNull: true,
        fk: "customers.id",
      },
      { name: "rating", type: "INTEGER", notNull: true },
      { name: "comment", type: "TEXT" },
      { name: "created_at", type: "TIMESTAMPTZ", notNull: true },
    ],
    uniques: ["(product_id, customer_id)"],
  },
]
