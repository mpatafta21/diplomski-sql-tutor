"""Logika hinta bez agenta i bez HTTP-a (Faza 5.1, §D) — čiste DB funkcije.

Pokriva četiri odluke iz §C plana 5.0:
  C.1 limit 5 / +1 po 4 h, izveden PRI ČITANJU; `unavailable` NE troši kredit
  C.2 idempotencija po `after_attempt_id`
  C.3 otključavanje: zadnji pokušaj na zadatku mora biti netočan
  C.4 `remaining` + `next_refill_at`

🔴 Vrijeme se NE mjeri satom nego se ubrizgava (`now=`), inače bi test ovisio o
trenutku pokretanja. Isti razlog zbog kojeg `created_at` u fixturama postavljamo
eksplicitno umjesto da čekamo.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, select

from agents.hint_logic import (
    fallback_hint,
    hint_credit,
    existing_request,
    primary_concept,
    unlocking_attempt,
)
from app.core import config
from app.db.models import Attempt, Hint, HintRequest, Task, User
from app.db.session import SessionLocal

_NOW = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def hint_user():
    """Committed user + zadatak; teardown briše hint_requests → attempts → user."""
    with SessionLocal() as s:
        u = User(
            username="hint_logic_51",
            email="hint-logic-51@test.example",
            password_hash="dummy_hash_51",
        )
        s.add(u)
        s.commit()
        uid = u.id
        task_id = s.scalar(select(Task.id).where(Task.is_active.is_(True)).limit(1))
    assert task_id is not None, "tasks moraju biti seedani"

    yield {"user_id": uid, "task_id": task_id}

    with SessionLocal() as s:
        s.execute(delete(HintRequest).where(HintRequest.user_id == uid))
        s.execute(delete(Attempt).where(Attempt.user_id == uid))
        s.execute(delete(User).where(User.id == uid))
        s.commit()


@pytest.fixture
def drugi_user():
    """Drugi committed korisnik — za tvrdnju „kredit je PO KORISNIKU".

    Vlastiti, a ne zatečeni redak iz `users`: suita dijeli bazu s aplikacijom
    (ERRATA #40), pa bi „bilo koji drugi korisnik" značilo mjeriti stvarne
    podatke `admina` ili sudionika.
    """
    with SessionLocal() as s:
        s.execute(delete(User).where(User.username == "hint_logic_51_drugi"))
        s.commit()
        u = User(
            username="hint_logic_51_drugi",
            email="hint-logic-51-drugi@test.example",
            password_hash="dummy_hash_51b",
        )
        s.add(u)
        s.commit()
        uid = u.id

    yield uid

    with SessionLocal() as s:
        s.execute(delete(HintRequest).where(HintRequest.user_id == uid))
        s.execute(delete(Attempt).where(Attempt.user_id == uid))
        s.execute(delete(User).where(User.id == uid))
        s.commit()


def _attempt(uid: int, task_id: int, *, n: int, correct: bool, et: str | None) -> int:
    with SessionLocal() as s:
        a = Attempt(
            user_id=uid,
            task_id=task_id,
            submitted_query="SELECT 1;",
            is_correct=correct,
            error_type=et,
            attempt_number=n,
        )
        s.add(a)
        s.commit()
        return a.id


def _request(uid: int, task_id: int, attempt_id: int, *, source: str, at: datetime) -> int:
    with SessionLocal() as s:
        r = HintRequest(
            user_id=uid,
            task_id=task_id,
            after_attempt_id=attempt_id,
            error_type="row_mismatch",
            source=source,
            hint_text=None if source == "unavailable" else "tekst",
            created_at=at,
        )
        s.add(r)
        s.commit()
        return r.id


# ---------------------------------------------------------------------------
# C.3 — otključavanje
# ---------------------------------------------------------------------------


def test_unlock_requires_an_incorrect_last_attempt(hint_user) -> None:
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    assert unlocking_attempt(SessionLocal(), uid, tid) is None  # nijedan pokušaj

    _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    with SessionLocal() as s:
        a = unlocking_attempt(s, uid, tid)
    assert a is not None and a.error_type == "row_mismatch"


def test_unlock_closes_after_a_correct_attempt(hint_user) -> None:
    """🔴 Zadnji pokušaj, ne bilo koji: nakon točnog rješenja hint se zaključava."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    _attempt(uid, tid, n=2, correct=True, et=None)
    with SessionLocal() as s:
        assert unlocking_attempt(s, uid, tid) is None


def test_unlock_is_per_task(hint_user) -> None:
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    with SessionLocal() as s:
        other = s.scalar(select(Task.id).where(Task.id != tid).limit(1))
        assert unlocking_attempt(s, uid, other) is None


# ---------------------------------------------------------------------------
# C.2 — idempotencija
# ---------------------------------------------------------------------------


def test_existing_request_found_by_attempt(hint_user) -> None:
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    with SessionLocal() as s:
        assert existing_request(s, aid) is None
    _request(uid, tid, aid, source="llm", at=_NOW)
    with SessionLocal() as s:
        r = existing_request(s, aid)
    assert r is not None and r.source == "llm" and r.hint_text == "tekst"


def test_unavailable_request_is_not_replayed(hint_user) -> None:
    """🔴 Zahtjev koji ništa nije vratio NIJE odgovor koji se ponavlja.

    Redak postoji zbog telemetrije (mjeri se rupa u katalogu), ali ponovni klik
    mora smjeti pokušati ponovno — inače bi jedan pad providera trajno zaključao
    hint na tom pokušaju.
    """
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    _request(uid, tid, aid, source="unavailable", at=_NOW)
    with SessionLocal() as s:
        assert existing_request(s, aid) is None


# ---------------------------------------------------------------------------
# C.1 / C.4 — kredit
# ---------------------------------------------------------------------------


def test_fresh_user_has_full_credit(hint_user) -> None:
    with SessionLocal() as s:
        rem, refill = hint_credit(s, hint_user["user_id"], now=_NOW)
    assert rem == config.HINT_MAX
    assert refill is None, "pun bucket nema sljedeću nadopunu"


def test_each_served_hint_costs_one(hint_user) -> None:
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    for i in range(3):
        _request(uid, tid, aid, source="llm", at=_NOW - timedelta(minutes=10 - i))
    with SessionLocal() as s:
        rem, refill = hint_credit(s, uid, now=_NOW)
    assert rem == config.HINT_MAX - 3
    assert refill is not None and refill > _NOW


def test_unavailable_does_not_cost_credit(hint_user) -> None:
    """🔴 C.1: student nije dobio ništa — ne smije platiti."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    for i in range(4):
        _request(uid, tid, aid, source="unavailable", at=_NOW - timedelta(minutes=i + 1))
    with SessionLocal() as s:
        rem, _ = hint_credit(s, uid, now=_NOW)
    assert rem == config.HINT_MAX


def test_credit_refills_one_per_window(hint_user) -> None:
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    # Pet potrošenih u kratkom nizu → bucket prazan.
    base = _NOW - timedelta(hours=config.HINT_REFILL_HOURS)
    for i in range(config.HINT_MAX):
        _request(uid, tid, aid, source="llm", at=base - timedelta(minutes=i))

    with SessionLocal() as s:
        rem_odmah, _ = hint_credit(s, uid, now=base)
        rem_nakon_1, _ = hint_credit(s, uid, now=_NOW)
        rem_nakon_3, _ = hint_credit(
            s, uid, now=base + timedelta(hours=3 * config.HINT_REFILL_HOURS)
        )
    assert rem_odmah == 0
    assert rem_nakon_1 == 1, "nakon jednog prozora točno jedan hint"
    assert rem_nakon_3 == 3


def test_credit_never_exceeds_max(hint_user) -> None:
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    _request(uid, tid, aid, source="llm", at=_NOW - timedelta(days=30))
    with SessionLocal() as s:
        rem, refill = hint_credit(s, uid, now=_NOW)
    assert rem == config.HINT_MAX
    assert refill is None


def test_next_refill_is_when_the_counter_actually_moves(hint_user) -> None:
    """C.4: `next_refill_at` mora biti trenutak u kojem `remaining` poraste za 1."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    _request(uid, tid, aid, source="llm", at=_NOW - timedelta(hours=1))

    with SessionLocal() as s:
        rem, refill = hint_credit(s, uid, now=_NOW)
        assert rem == config.HINT_MAX - 1
        assert refill is not None
        # U tom trenutku brojka mora biti veća — provjereno ponovnim izračunom.
        rem_tada, _ = hint_credit(s, uid, now=refill + timedelta(seconds=1))
    assert rem_tada == rem + 1
    # 1 h je već proteklo od potrošnje → preostaje ~3 h.
    assert timedelta(hours=2.9) < (refill - _NOW) < timedelta(hours=3.1)


def test_credit_is_per_user(hint_user, drugi_user) -> None:
    """Potrošnja jednog korisnika ne dira kredit drugoga.

    🔴 Drugi korisnik je VLASTITI, ne „bilo koji drugi redak iz `users`". Ranija
    izvedba uzimala je `select(User.id).where(User.id != uid).limit(1)` — bez
    `ORDER BY`, dakle proizvoljan redak (mehanizam ERRATE #60), koji je u živoj
    `tutor_main` (ERRATA #40) znao biti `admin` sa stvarnim hint zapisima. Test
    je time mjerio tuđe podatke umjesto vlastite tvrdnje.
    """
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    _request(uid, tid, aid, source="llm", at=_NOW - timedelta(minutes=5))

    with SessionLocal() as s:
        assert hint_credit(s, uid, now=_NOW)[0] == config.HINT_MAX - 1
        assert hint_credit(s, drugi_user, now=_NOW)[0] == config.HINT_MAX


def test_future_request_counts_but_credit_never_goes_negative(hint_user) -> None:
    """🔴 Zahtjev noviji od `now` se BROJI, ali ne smije obarati bucket u minus.

    `level += (now - prev) / refill` s negativnim razmakom davao je `remaining = -8`
    za `now` dva dana u prošlosti. To je rušilo `test_credit_is_per_user` u punoj
    suiti, a brojka se pogoršavala s vremenom (−6 → −7 → −8).

    🔴 Popravak je KLAMP prirasta, ne izbacivanje retka filtrom `created_at <= now`.
    `hint_credit` je gate za 429: `now` se uzima u Pythonu prije upita, a
    `created_at` dolazi iz PG `now()`, pa istovremena druga predaja može leći s
    `created_at > now`. Filtar bi je isključio iz računice i pustio hint PREKO
    limita; klamp je i dalje broji.
    """
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    _request(uid, tid, aid, source="llm", at=_NOW + timedelta(days=2))

    with SessionLocal() as s:
        remaining, _ = hint_credit(s, uid, now=_NOW)

    assert remaining == config.HINT_MAX - 1, (
        f"budući zahtjev se mora BROJITI, a ne izbaciti → remaining={remaining}"
    )
    assert remaining >= 0, "bucket nikad ispod nule"


# ---------------------------------------------------------------------------
# Fallback iz kataloga
# ---------------------------------------------------------------------------


def test_fallback_matches_error_type_and_concept() -> None:
    with SessionLocal() as s:
        cid = s.scalar(select(Hint.concept_id).where(Hint.error_type == "row_mismatch").limit(1))
        h = fallback_hint(s, "row_mismatch", cid)
    assert h is not None and h.error_type == "row_mismatch" and h.concept_id == cid


def test_fallback_is_empty_when_catalog_has_no_row() -> None:
    """🔴 Rupa u katalogu vraća None — ne izmišlja se generički tekst."""
    with SessionLocal() as s:
        assert fallback_hint(s, "timeout", None) is None
        cid = s.scalar(select(Hint.concept_id).limit(1))
        assert fallback_hint(s, "syntax_error", cid) is None


def test_primary_concept_of_task() -> None:
    with SessionLocal() as s:
        tid = s.scalar(select(Task.id).where(Task.is_active.is_(True)).limit(1))
        cid, code = primary_concept(s, tid)
    assert cid is not None and isinstance(code, str) and code
