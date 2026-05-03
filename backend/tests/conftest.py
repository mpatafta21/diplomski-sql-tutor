"""Pytest fixtures za testiranje sheme.

`db_inspector` daje SQLAlchemy Inspector protiv `tutor_main` baze
koju Alembic migracije trebaju imati popunjenu. Fixture SAM NE kreira
schemu — tests očekuju da je operator prethodno pokrenuo
`alembic upgrade head` (to je dio test zahtjeva).
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import Inspector, inspect

from app.db.session import engine


@pytest.fixture(scope="session")
def db_inspector() -> Inspector:
    return inspect(engine)


@pytest.fixture(scope="session")
def sandbox_connection_string() -> str:
    """SANDBOX_DATABASE_URL iz .env, normaliziran za psycopg3."""
    raw = os.environ.get(
        "SANDBOX_DATABASE_URL",
        "postgresql+psycopg://sandbox_admin:sandbox_dev_password@localhost:5433/sandbox",
    )
    # psycopg3 ne podnosi SQLAlchemy dialect prefix
    return raw.replace("postgresql+psycopg://", "postgresql://")
