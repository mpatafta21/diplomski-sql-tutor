"""Zajednički SQLAlchemy Base i metadata.

Sve modele deklariramo naslijeđivanjem iz `Base`. Alembic koristi
`Base.metadata` za autogenerate migracija.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
