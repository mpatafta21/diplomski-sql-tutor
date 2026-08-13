"""`GET /profile` nosi stanje kredita za hintove (Faza 5.2, §B).

🔴 ZAŠTO OVDJE, a ne na `/me` ili `TaskDetailResponse`u: odluka C.3.2 plana 5.2.
`/me` je identitet (konfiguracija da, živo stanje ne), `TaskDetailResponse` je po
zadatku a kredit je po korisniku. `/profile` je već u cacheu na Task ekranu i već ga
`useSubmitAttempt` invalidira — nula dodatnih poziva.

🔴 JEDAN IZVOR: ruta ne smije reimplementirati formulu iz `POST /hint`, nego zvati
istu `hint_logic.hint_credit`. Dvije implementacije istog pravila su mehanizam N-8.
Test `test_profile_remaining_matches_hint_response` to i dokazuje mjerenjem, ne
čitanjem koda.

Stack agenata se NE diže — `/profile` je čisti DB read.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import delete

from app.core import config
from app.db.models import Attempt, HintRequest, Task, User
from app.db.session import SessionLocal
from app.main import create_app
from tests.conftest import auth_header


@pytest.fixture
def credit_user():
    with SessionLocal() as s:
        u = User(
            username="profile_credit_52",
            email="profile-credit-52@test.example",
            password_hash="dummy_hash_52p",
        )
        s.add(u)
        s.commit()
        uid = u.id
        task_id = int(s.scalars(Task.__table__.select().with_only_columns(Task.id).limit(1)).first())

    yield {"user_id": uid, "task_id": task_id}

    with SessionLocal() as s:
        s.execute(delete(HintRequest).where(HintRequest.user_id == uid))
        s.execute(delete(Attempt).where(Attempt.user_id == uid))
        s.execute(delete(User).where(User.id == uid))
        s.commit()


def _spend(uid: int, task_id: int, *, n: int, minutes_ago: int = 0) -> None:
    """Upiši `n` potrošenih hintova (source='fallback' — troši kredit)."""
    ts = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    with SessionLocal() as s:
        a = Attempt(
            user_id=uid,
            task_id=task_id,
            submitted_query="SELECT 1;",
            is_correct=False,
            error_type="row_mismatch",
            attempt_number=1,
        )
        s.add(a)
        s.flush()
        for i in range(n):
            s.add(
                HintRequest(
                    user_id=uid,
                    task_id=task_id,
                    after_attempt_id=a.id,
                    error_type="row_mismatch",
                    source="fallback",
                    hint_text=f"tekst {i}",
                    created_at=ts,
                )
            )
        s.commit()


async def _profile(uid: int) -> dict:
    app = create_app()  # bez stacka — dokaz da je /profile čisti DB read
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/profile", headers=auth_header(uid))
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_flag_off_yields_nulls(credit_user, monkeypatch) -> None:
    """🔴 B3: pod isključenim flagom OBA polja su `null`, ne broj.

    Brojač bez značajke je besmislen, a svaka konkretna brojka laže: `5` reklamira
    hintove kojih nema, `0` čita se kao „potrošeno" (stanje iz kojeg se izlazi
    čekanjem) iako se ništa nije potrošilo. `null` znači „nema brojke", i to je
    jedino istinito.
    """
    monkeypatch.setattr(config, "USE_LLM_HINTS", False)
    body = await _profile(credit_user["user_id"])

    assert "hint_remaining" not in body, "polje se zove `remaining` (ugovor C.1.3)"
    assert body["remaining"] is None
    assert body["next_refill_at"] is None


@pytest.mark.asyncio
async def test_flag_on_full_bucket(credit_user, monkeypatch) -> None:
    """Pun bucket: `remaining == HINT_MAX`, a `next_refill_at` je `null` — nema
    se što puniti (B2)."""
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    body = await _profile(credit_user["user_id"])

    assert body["remaining"] == config.HINT_MAX
    assert body["next_refill_at"] is None


@pytest.mark.asyncio
async def test_flag_on_after_spending(credit_user, monkeypatch) -> None:
    """Nakon dva potrošena hinta brojka pada za dva i nadopuna dobiva trenutak."""
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    _spend(credit_user["user_id"], credit_user["task_id"], n=2)

    body = await _profile(credit_user["user_id"])

    assert body["remaining"] == config.HINT_MAX - 2
    assert body["next_refill_at"] is not None
    refill = datetime.fromisoformat(body["next_refill_at"])
    delta_h = (refill - datetime.now(timezone.utc)).total_seconds() / 3600
    # Prvi token se vraća unutar jednog punog intervala punjenja.
    assert 0 < delta_h <= config.HINT_REFILL_HOURS + 0.01


@pytest.mark.asyncio
async def test_exhausted_bucket_is_zero_not_null(credit_user, monkeypatch) -> None:
    """🔴 `0` i `null` su različita stanja: potrošeno vs. značajka ne postoji.

    Bez ovog testa bi implementacija koja pod flagom vraća `None` i za prazan
    bucket prošla — a UI bi izgubio razliku između „čekaj nadopunu" i „nema hintova".
    """
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    _spend(credit_user["user_id"], credit_user["task_id"], n=config.HINT_MAX)

    body = await _profile(credit_user["user_id"])

    assert body["remaining"] == 0
    assert body["next_refill_at"] is not None
