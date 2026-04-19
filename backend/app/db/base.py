"""Zajednički SQLAlchemy Base i metadata.

Sve modele deklariramo naslijeđivanjem iz `Base`. Alembic koristi
`Base.metadata` za autogenerate migracija.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import svih modela — osigurava da Base.metadata ima sve tablice
# prije nego što Alembic pozove autogenerate.
from app.db import models  # noqa: E402, F401
