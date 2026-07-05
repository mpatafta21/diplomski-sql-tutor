"""JWT auth infrastruktura (Faza 4.0b).

Sadrži: bcrypt hash/verify, mint/decode access tokena (python-jose),
te FastAPI dependencyje `get_current_user` / `require_admin`.

Hashing ide IZRAVNO kroz `bcrypt` (ne passlib): spade→pyjabber tvrdi bcrypt>=4.3,
a passlib 1.7.4 (zadnji release, napušten 2020.) je nekompatibilan s bcrypt>=4.1
(uklonjen `__about__`, promijenjeno >72B ponašanje). bcrypt je ionako hard
tranzitivni dep, pa izravna upotreba ne uvodi ništa novo.

Dependencyji rade sinkroni DB read kroz SessionLocal() (kratko, izvan to_thread puta —
NE uvodimo async engine). Greške prate postojeći HTTPException(detail="snake_string")
obrazac iz routes.py; 401 nosi standardni `WWW-Authenticate: Bearer` header (OAuth2).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core import config
from app.db.models import User
from app.db.session import SessionLocal

# ---------------------------------------------------------------------------
# Password hashing (bcrypt izravno)
# ---------------------------------------------------------------------------

# bcrypt uzima u obzir samo prvih 72 bajta — truncamo eksplicitno da bcrypt>=5.0
# ne baca ValueError na dulje lozinke (isto ponašanje kao povijesni bcrypt).
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(plain: str) -> bytes:
    return plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    """Vrati bcrypt hash lozinke (utf-8 string)."""
    return bcrypt.hashpw(_to_bcrypt_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """True ako `plain` odgovara `hashed`. Neispravan/ne-bcrypt hash → False (ne baca)."""
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain), hashed.encode("utf-8"))
    except ValueError:
        # npr. dummy (ne-bcrypt) hash iz starih test fixtura → tretiraj kao promašaj
        return False


# ---------------------------------------------------------------------------
# JWT mint / decode
# ---------------------------------------------------------------------------


def create_access_token(sub: str, role: str, expires_minutes: int | None = None) -> str:
    """Potpiši access token. `sub` = str(user_id), `role` = student|admin.

    exp = utcnow + (expires_minutes ili config.ACCESS_TOKEN_EXPIRE_MINUTES).
    """
    minutes = (
        expires_minutes
        if expires_minutes is not None
        else config.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload = {"sub": str(sub), "role": role, "exp": expire}
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Dekodiraj i verificiraj token. Baca `JWTError` na invalid/expired potpis."""
    return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# FastAPI dependencyji
# ---------------------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="invalid_token",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Dekodiraj token → user_id (sub) → dohvati User. 401 na bilo koji promašaj."""
    try:
        payload = decode_token(token)
    except JWTError:
        raise _CREDENTIALS_EXC

    sub = payload.get("sub")
    if sub is None:
        raise _CREDENTIALS_EXC
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise _CREDENTIALS_EXC

    with SessionLocal() as session:
        user = session.get(User, user_id)
    if user is None:
        raise _CREDENTIALS_EXC
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Propusti samo admina. Student → 403 admin_required."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="admin_required"
        )
    return user
