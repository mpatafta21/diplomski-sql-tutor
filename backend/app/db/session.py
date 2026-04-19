"""Sync SQLAlchemy engine i session factory.

Async engine dodaje se u Fazi 3 kad ga endpoint-i zahtijevaju.
Za migracije, seed i skripte sync je dovoljan.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True, echo=False, pool_pre_ping=True)
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)
