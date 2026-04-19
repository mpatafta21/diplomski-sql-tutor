"""Konfiguracija iz .env fajla.

Učitava environment varijable preko python-dotenv i izlaže ih kao
modul-level konstante. Iznimka se baca rano ako DATABASE_URL nedostaje.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_DIR / ".env")


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Obavezna env varijabla nedostaje: {name}")
    return value


DATABASE_URL: str = _required("DATABASE_URL")
SANDBOX_DATABASE_URL: str | None = os.getenv("SANDBOX_DATABASE_URL")
