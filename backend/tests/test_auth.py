"""Auth core testovi — Faza 4.0b.1 (ADITIVNO).

Pokriva: /register, /login, /me, security.get_current_user / require_admin, te
conftest.auth_header helper. Postojeće rute se NE gate-aju u ovom komadu — ove
testove zanima samo nova auth infrastruktura.

DB obrazac: register/login pišu committano u users → cleanup po username prefiksu.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select

from app.core.security import (
    create_access_token,
    decode_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)
from app.db.models import User
from app.db.session import SessionLocal
from app.main import create_app
from tests.conftest import auth_header

_PREFIX = "auth_401b_"


@asynccontextmanager
async def _client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as c:
        yield c


@pytest.fixture
def cleanup_users():
    """Obriši sve usere s test-prefiksom nakon testa (username LIKE 'auth_401b_%')."""
    yield
    with SessionLocal() as s:
        s.execute(delete(User).where(User.username.like(f"{_PREFIX}%")))
        s.commit()


def _make_real_user(username: str, password: str, *, role: str = "student") -> int:
    """Committani user s PRAVIM bcrypt hashom (za login testove)."""
    with SessionLocal() as s:
        u = User(
            username=username,
            email=f"{username}@test.example",
            password_hash=hash_password(password),
            role=role,
        )
        s.add(u)
        s.commit()
        return u.id


# ===========================================================================
# POST /register
# ===========================================================================


@pytest.mark.asyncio
async def test_register_valid_returns_student_token(cleanup_users):
    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/register",
            json={
                "username": f"{_PREFIX}reg_ok",
                "email": f"{_PREFIX}reg_ok@test.example",
                "password": "s3cret-pw",
            },
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    payload = decode_token(body["access_token"])
    assert payload["role"] == "student"

    with SessionLocal() as s:
        uid = s.scalar(select(User.id).where(User.username == f"{_PREFIX}reg_ok"))
    assert payload["sub"] == str(uid)


@pytest.mark.asyncio
async def test_register_duplicate_username_409(cleanup_users):
    _make_real_user(f"{_PREFIX}dup_uname", "pw")
    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/register",
            json={
                "username": f"{_PREFIX}dup_uname",
                "email": f"{_PREFIX}dup_uname_other@test.example",
                "password": "pw2",
            },
        )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "username_taken"


@pytest.mark.asyncio
async def test_register_duplicate_email_409(cleanup_users):
    with SessionLocal() as s:
        s.add(
            User(
                username=f"{_PREFIX}dup_email_a",
                email=f"{_PREFIX}shared@test.example",
                password_hash=hash_password("pw"),
            )
        )
        s.commit()

    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/register",
            json={
                "username": f"{_PREFIX}dup_email_b",
                "email": f"{_PREFIX}shared@test.example",
                "password": "pw2",
            },
        )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "email_taken"


@pytest.mark.asyncio
async def test_register_ignores_admin_role_in_body(cleanup_users):
    """role u bodyju se IGNORIRA — uvijek se kreira student."""
    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/register",
            json={
                "username": f"{_PREFIX}role_inject",
                "email": f"{_PREFIX}role_inject@test.example",
                "password": "pw",
                "role": "admin",  # pokušaj injekcije
            },
        )
    assert resp.status_code == 200, resp.text
    payload = decode_token(resp.json()["access_token"])
    assert payload["role"] == "student"

    with SessionLocal() as s:
        role = s.scalar(
            select(User.role).where(User.username == f"{_PREFIX}role_inject")
        )
    assert role == "student"


# ===========================================================================
# POST /login (OAuth2PasswordRequestForm)
# ===========================================================================


@pytest.mark.asyncio
async def test_login_correct_returns_token(cleanup_users):
    uid = _make_real_user(f"{_PREFIX}login_ok", "correct-horse")
    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/login",
            data={"username": f"{_PREFIX}login_ok", "password": "correct-horse"},
        )
    assert resp.status_code == 200, resp.text
    payload = decode_token(resp.json()["access_token"])
    assert payload["sub"] == str(uid)
    assert payload["role"] == "student"


@pytest.mark.asyncio
async def test_login_wrong_password_401(cleanup_users):
    _make_real_user(f"{_PREFIX}login_wrongpw", "right-pw")
    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/login",
            data={"username": f"{_PREFIX}login_wrongpw", "password": "WRONG"},
        )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_login_unknown_user_401(cleanup_users):
    app = create_app()
    async with _client(app) as client:
        resp = await client.post(
            "/login",
            data={"username": f"{_PREFIX}nonexistent", "password": "whatever"},
        )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "invalid_credentials"


# ===========================================================================
# GET /me
# ===========================================================================


@pytest.mark.asyncio
async def test_me_valid_token(cleanup_users):
    uid = _make_real_user(f"{_PREFIX}me_ok", "pw")
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/me", headers=auth_header(uid))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == uid
    assert body["username"] == f"{_PREFIX}me_ok"
    assert body["role"] == "student"


@pytest.mark.asyncio
async def test_me_no_token_401():
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token_401():
    app = create_app()
    async with _client(app) as client:
        resp = await client.get(
            "/me", headers={"Authorization": "Bearer not.a.real.token"}
        )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "invalid_token"


# ===========================================================================
# security unit — get_current_user (expired) + require_admin
# ===========================================================================


def test_get_current_user_expired_token_401():
    token = create_access_token("1", "student", expires_minutes=-1)
    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token)
    assert exc.value.status_code == 401


def test_require_admin_rejects_student():
    student = User(id=1, username="s", email="s@x.y", password_hash="h", role="student")
    with pytest.raises(HTTPException) as exc:
        require_admin(user=student)
    assert exc.value.status_code == 403
    assert exc.value.detail == "admin_required"


def test_require_admin_allows_admin():
    admin = User(id=2, username="a", email="a@x.y", password_hash="h", role="admin")
    assert require_admin(user=admin) is admin


def test_verify_password_roundtrip_and_bad_hash():
    hashed = hash_password("hunter2")
    assert verify_password("hunter2", hashed) is True
    assert verify_password("nope", hashed) is False
    # ne-bcrypt dummy hash (stare fixture) → False, ne baca
    assert verify_password("x", "dummy_hash_not_bcrypt") is False


# ===========================================================================
# conftest.auth_header helper — mint direktno, get_current_user ga prihvaća
# ===========================================================================


@pytest.mark.asyncio
async def test_auth_header_helper_accepted_via_me(cleanup_users):
    uid = _make_real_user(f"{_PREFIX}helper", "pw")
    app = create_app()
    async with _client(app) as client:
        resp = await client.get("/me", headers=auth_header(uid, role="student"))
    assert resp.status_code == 200
    assert resp.json()["id"] == uid
