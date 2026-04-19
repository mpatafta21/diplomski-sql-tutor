"""Pytest fixtures za testiranje sheme.

`db_inspector` daje SQLAlchemy Inspector protiv `tutor_main` baze
koju Alembic migracije trebaju imati popunjenu. Fixture SAM NE kreira
schemu — tests očekuju da je operator prethodno pokrenuo
`alembic upgrade head` (to je dio test zahtjeva).
"""

from __future__ import annotations

import pytest
from sqlalchemy import Inspector, inspect

from app.db.session import engine


@pytest.fixture(scope="session")
def db_inspector() -> Inspector:
    return inspect(engine)
