"""`POST /hint` kroz ŽIVI FIPA lanac (Faza 5.1, §D2–D4).

Lanac je stvaran — gateway → XMPP → HintAgent → gateway → bridge — jer je upravo
tu bio rizik: da odgovor HintAgenta ne odgovara nijednom predlošku u `_Resolve` i
svaki `/hint` tiho postane 504. Mock bi to propustio.

🔴 LLM je MOCKAN u svakom testu (`agents.hint_agent.generate_hint`). Nula stvarne
potrošnje: `pytest` se pokreće prije evaluacije, pa bi stvarni poziv trošio novac
na svakom pokretanju suite.

Zahtijeva živi Prosody (5222) + `tutor_main` s registriranim `hint@localhost`.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from sqlalchemy import delete, func, select

from agents.hint_llm import HintLLMError, HintLLMResult
from app.core import config
from app.db.models import (
    AgentMessageLog,
    Attempt,
    Hint,
    HintRequest,
    Task,
    TaskConcept,
    User,
)
from app.db.session import SessionLocal
from app.main import create_app, start_gateway_stack, stop_gateway_stack
from tests.conftest import auth_header

_LLM_TEXT = "Razmisli koje retke GROUP BY sažima prije nego ih prebrojiš."


@asynccontextmanager
async def _stack(app):
    from agents.hint_agent import HintAgent

    await start_gateway_stack(app, agents=[HintAgent("hint")])
    await asyncio.sleep(0.6)  # XMPP presence/connect settle
    try:
        yield
    finally:
        await stop_gateway_stack(app)
        await asyncio.sleep(0.1)


@asynccontextmanager
async def _client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


def _covered_task() -> tuple[int, int]:
    """(task_id, concept_id) za zadatak čiji primarni koncept JEST u katalogu hintova.

    Bira se iz baze, ne hardkodira: katalog pokriva 8 koncepata, a koji ih zadatak
    nosi ovisi o seedu.
    """
    with SessionLocal() as s:
        row = s.execute(
            select(Task.id, TaskConcept.concept_id)
            .join(TaskConcept, TaskConcept.task_id == Task.id)
            .join(Hint, Hint.concept_id == TaskConcept.concept_id)
            .where(
                Task.is_active.is_(True),
                TaskConcept.is_primary.is_(True),
                Hint.error_type == "row_mismatch",
            )
            .order_by(Task.id)
            .limit(1)
        ).first()
    assert row is not None, "treba zadatak čiji je primarni koncept u katalogu hintova"
    return int(row[0]), int(row[1])


@pytest.fixture
def hint_user():
    with SessionLocal() as s:
        u = User(
            username="hint_route_51",
            email="hint-route-51@test.example",
            password_hash="dummy_hash_51r",
        )
        s.add(u)
        s.commit()
        uid = u.id
    task_id, concept_id = _covered_task()

    yield {"user_id": uid, "task_id": task_id, "concept_id": concept_id}

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
            submitted_query="SELECT county FROM suppliers;",
            is_correct=correct,
            error_type=et,
            detail="Row count mismatch: actual=30 vs expected=3",
            attempt_number=n,
        )
        s.add(a)
        s.commit()
        return a.id


def _rows(uid: int) -> list[HintRequest]:
    with SessionLocal() as s:
        return list(
            s.scalars(
                select(HintRequest)
                .where(HintRequest.user_id == uid)
                .order_by(HintRequest.id)
            ).all()
        )


@pytest.fixture
def llm_ok(monkeypatch):
    """LLM koji uspije; broji pozive."""
    calls: list[dict] = []

    def _fake(payload: dict) -> HintLLMResult:
        calls.append(payload)
        return HintLLMResult(text=_LLM_TEXT, input_tokens=386, output_tokens=42)

    monkeypatch.setattr("agents.hint_agent.generate_hint", _fake)
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "test-key-not-real")
    return calls


@pytest.fixture
def llm_down(monkeypatch):
    calls: list[dict] = []

    def _fake(payload: dict):
        calls.append(payload)
        raise HintLLMError("simulirani pad providera")

    monkeypatch.setattr("agents.hint_agent.generate_hint", _fake)
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "test-key-not-real")
    return calls


# ---------------------------------------------------------------------------
# 1) Prekidač
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flag_off_returns_503_without_touching_anything(hint_user, monkeypatch) -> None:
    """🔴 Exit: s `USE_LLM_HINTS=false` — 503 i NIJEDAN odlazni poziv.

    Dokaz da poziva nije bilo je strukturni, ne pretpostavka: `generate_hint` je
    zamijenjen funkcijom koja bi pala da je pozvana.
    """
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    _attempt(uid, tid, n=1, correct=False, et="row_mismatch")

    def _boom(payload):  # pragma: no cover — poziv bi bio bug
        raise AssertionError("LLM pozvan iako je USE_LLM_HINTS=false")

    monkeypatch.setattr("agents.hint_agent.generate_hint", _boom)
    monkeypatch.setattr(config, "USE_LLM_HINTS", False)

    app = create_app()
    async with _stack(app), _client(app) as c:
        r = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))

    assert r.status_code == 503
    assert r.json()["detail"] == "hints_disabled"
    assert _rows(uid) == [], "odbijeni zahtjev ne smije ostaviti redak"


@pytest.mark.asyncio
async def test_me_exposes_the_flag(hint_user, monkeypatch) -> None:
    """§B.4.3: gumb se sakriva PRIJE klika, pa zastavica mora biti na `/me`."""
    uid = hint_user["user_id"]
    app = create_app()
    async with _stack(app), _client(app) as c:
        monkeypatch.setattr(config, "USE_LLM_HINTS", False)
        off = await c.get("/me", headers=auth_header(uid))
        monkeypatch.setattr(config, "USE_LLM_HINTS", True)
        on = await c.get("/me", headers=auth_header(uid))

    assert off.json()["hints_enabled"] is False
    assert on.json()["hints_enabled"] is True


# ---------------------------------------------------------------------------
# 2) Otključavanje (C.3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_attempt_means_409(hint_user, llm_ok) -> None:
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    app = create_app()
    async with _stack(app), _client(app) as c:
        r = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))
    assert r.status_code == 409
    assert r.json()["detail"] == "hint_not_unlocked"
    assert llm_ok == [], "bez netočnog pokušaja LLM se ne smije pozvati"


@pytest.mark.asyncio
async def test_correct_last_attempt_locks_the_hint(hint_user, llm_ok) -> None:
    """🔴 Exit: zadatak bez netočnog pokušaja vraća 409, ne hint."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    _attempt(uid, tid, n=2, correct=True, et=None)

    app = create_app()
    async with _stack(app), _client(app) as c:
        r = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))
    assert r.status_code == 409
    assert llm_ok == []


@pytest.mark.asyncio
async def test_task_detail_announces_unlock(hint_user, llm_ok) -> None:
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    app = create_app()
    async with _stack(app), _client(app) as c:
        prazno = await c.get(f"/task/{tid}", headers=auth_header(uid))
        _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
        otkljucano = await c.get(f"/task/{tid}", headers=auth_header(uid))
        _attempt(uid, tid, n=2, correct=True, et=None)
        zakljucano = await c.get(f"/task/{tid}", headers=auth_header(uid))

    assert prazno.json()["last_attempt_error_type"] is None
    assert otkljucano.json()["last_attempt_error_type"] == "row_mismatch"
    assert zakljucano.json()["last_attempt_error_type"] is None


# ---------------------------------------------------------------------------
# 3) Sretan put + telemetrija (D3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_llm_hint_end_to_end(hint_user, llm_ok) -> None:
    """🔴 Exit: `/hint` vraća hint na živom lancu, i ostavlja točno jedan redak."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")

    app = create_app()
    async with _stack(app), _client(app) as c:
        r = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["hint_text"] == _LLM_TEXT
    assert body["source"] == "llm"
    assert body["remaining"] == config.HINT_MAX - 1
    assert body["next_refill_at"] is not None

    rows = _rows(uid)
    assert len(rows) == 1
    assert rows[0].after_attempt_id == aid
    assert rows[0].source == "llm"
    assert rows[0].hint_id is None
    assert rows[0].hint_text == _LLM_TEXT

    # Payload koji je otišao modelu prošao je kroz bijelu listu §C.
    assert len(llm_ok) == 1
    assert "county" not in str(llm_ok[0]), "studentov token ne smije doći do modela"


@pytest.mark.asyncio
async def test_second_request_replays_without_a_second_call(hint_user, llm_ok) -> None:
    """C.2: isti `after_attempt_id` → pohranjeni tekst, bez poziva, bez retka, bez troška."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    _attempt(uid, tid, n=1, correct=False, et="row_mismatch")

    app = create_app()
    async with _stack(app), _client(app) as c:
        prvi = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))
        drugi = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))

    assert prvi.status_code == drugi.status_code == 200
    assert prvi.json()["hint_text"] == drugi.json()["hint_text"]
    assert len(llm_ok) == 1, "drugi klik NE smije platiti drugi poziv"
    assert len(_rows(uid)) == 1
    assert drugi.json()["remaining"] == config.HINT_MAX - 1, "ponavljanje ne troši kredit"


@pytest.mark.asyncio
async def test_new_attempt_unlocks_a_new_hint(hint_user, llm_ok) -> None:
    """Idempotencija je vezana uz POKUŠAJ, ne uz zadatak — novi pokušaj, novi hint."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    _attempt(uid, tid, n=1, correct=False, et="row_mismatch")

    app = create_app()
    async with _stack(app), _client(app) as c:
        await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))
        _attempt(uid, tid, n=2, correct=False, et="row_mismatch")
        drugi = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))

    assert drugi.status_code == 200
    assert len(llm_ok) == 2
    assert len(_rows(uid)) == 2
    assert drugi.json()["remaining"] == config.HINT_MAX - 2


# ---------------------------------------------------------------------------
# 4) Fallback i rupa u katalogu
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_llm_failure_falls_back_to_catalog(hint_user, llm_down) -> None:
    """🔴 Exit: fallback dokazan padom LLM-a — bez ponavljanja poziva."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    _attempt(uid, tid, n=1, correct=False, et="row_mismatch")

    app = create_app()
    async with _stack(app), _client(app) as c:
        r = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))

    assert r.status_code == 200, r.text
    assert r.json()["source"] == "fallback"
    assert len(llm_down) == 1, "odluka 1: bez retryja"

    rows = _rows(uid)
    assert len(rows) == 1 and rows[0].source == "fallback"
    assert rows[0].hint_id is not None, "katalog-hint mora ostaviti analitički trag"


@pytest.mark.asyncio
async def test_catalog_gap_returns_503_and_is_recorded(hint_user, llm_down) -> None:
    """🔴 Rupa se MJERI: 503 + redak `unavailable` koji NE troši kredit."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    # `timeout` namjerno NIJE u katalogu (koncept-neovisan tip greške).
    _attempt(uid, tid, n=1, correct=False, et="timeout")

    app = create_app()
    async with _stack(app), _client(app) as c:
        r = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))
        me_poslije = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))

    assert r.status_code == 503
    assert r.json()["detail"] == "hint_unavailable"

    rows = _rows(uid)
    assert [x.source for x in rows] == ["unavailable", "unavailable"], (
        "neuspjeh se ne pamti kao odgovor — drugi klik smije pokušati ponovno"
    )
    assert all(x.hint_text is None for x in rows)
    assert me_poslije.status_code == 503


# ---------------------------------------------------------------------------
# 5) Limit (C.1)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exhausted_limit_returns_429(hint_user, llm_ok) -> None:
    """🔴 Exit: 429 nakon iscrpljenog limita — i BEZ LLM poziva."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    now = datetime.now(timezone.utc)
    with SessionLocal() as s:
        for i in range(config.HINT_MAX):
            s.add(
                HintRequest(
                    user_id=uid,
                    task_id=tid,
                    after_attempt_id=aid,
                    error_type="row_mismatch",
                    source="llm",
                    hint_text="raniji",
                    created_at=now - timedelta(minutes=30 + i),
                )
            )
        s.commit()
    # Novi pokušaj — inače bi ga pokupila idempotencija, ne limit.
    _attempt(uid, tid, n=2, correct=False, et="row_mismatch")

    app = create_app()
    async with _stack(app), _client(app) as c:
        r = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))

    assert r.status_code == 429
    assert r.json()["detail"] == "hint_rate_limited"
    assert llm_ok == [], "iscrpljen limit ne smije platiti poziv"


@pytest.mark.asyncio
async def test_replay_works_even_with_empty_bucket(hint_user, llm_ok) -> None:
    """🔴 Zato je idempotencija PRIJE limita: već plaćen hint ostaje dostupan."""
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    aid = _attempt(uid, tid, n=1, correct=False, et="row_mismatch")
    now = datetime.now(timezone.utc)
    with SessionLocal() as s:
        for i in range(config.HINT_MAX):
            s.add(
                HintRequest(
                    user_id=uid,
                    task_id=tid,
                    after_attempt_id=aid,
                    error_type="row_mismatch",
                    source="llm",
                    hint_text="vec placeni hint",
                    created_at=now - timedelta(minutes=30 + i),
                )
            )
        s.commit()

    app = create_app()
    async with _stack(app), _client(app) as c:
        r = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))

    assert r.status_code == 200
    assert r.json()["hint_text"] == "vec placeni hint"
    assert r.json()["remaining"] == 0
    assert llm_ok == []


@pytest.mark.asyncio
async def test_profile_remaining_matches_hint_response(hint_user, llm_ok) -> None:
    """🔴 Faza 5.2 §B.4: `/profile.remaining` == `HintResponse.remaining`.

    Ovo je test protiv N-8 mehanizma, ne protiv tipfelera: dvije rute računaju istu
    brojku i moraju je računati ISTOM funkcijom (`hint_logic.hint_credit`). Kopija
    formule bi ovdje pala prvi put kad se jedna strana promijeni.

    Mjeri se nakon ISTOG niza — prije hinta, poslije hinta i poslije ponovljenog
    (idempotentnog) hinta, koji kredit NE troši.
    """
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    _attempt(uid, tid, n=1, correct=False, et="row_mismatch")

    app = create_app()
    async with _stack(app), _client(app) as c:

        async def profil() -> dict:
            r = await c.get("/profile", headers=auth_header(uid))
            assert r.status_code == 200, r.text
            return r.json()

        prije = await profil()
        assert prije["remaining"] == config.HINT_MAX, "netaknut bucket je pun"
        assert prije["next_refill_at"] is None, "pun bucket nema što puniti"

        prvi = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))
        assert prvi.status_code == 200, prvi.text
        poslije = await profil()
        assert poslije["remaining"] == prvi.json()["remaining"] == config.HINT_MAX - 1
        assert poslije["next_refill_at"] is not None

        # Ponavljanje (C.2.2) — isti odgovor, kredit se NE troši ni u jednom izvoru.
        drugi = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))
        assert drugi.status_code == 200
        ponovno = await profil()
        assert ponovno["remaining"] == drugi.json()["remaining"] == config.HINT_MAX - 1


@pytest.mark.asyncio
async def test_profile_hides_credit_when_flag_off(hint_user, monkeypatch) -> None:
    """🔴 B3: isključena značajka → `remaining` je `null`, a ne `HINT_MAX`.

    Parnjak `test_flag_off_returns_503_without_touching_anything`: ruta koja odbija
    hint ne smije istovremeno oglašavati pun bucket na drugom endpointu.
    """
    uid = hint_user["user_id"]
    monkeypatch.setattr(config, "USE_LLM_HINTS", False)

    app = create_app()
    async with _client(app) as c:
        r = await c.get("/profile", headers=auth_header(uid))

    assert r.status_code == 200
    assert r.json()["remaining"] is None
    assert r.json()["next_refill_at"] is None


# ---------------------------------------------------------------------------
# 6) Invarijante nad tuđim tablicama
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hints_catalog_is_read_only_at_runtime(hint_user, monkeypatch) -> None:
    """🔴 Exit (H2.4): `count(*) FROM hints` identičan prije i poslije 10 hintova.

    Serija je 10, od čega 5 kroz LLM i 5 kroz katalog — obje grane pišu u
    `hint_requests`, pa obje moraju biti pod mjerenjem. `HINT_MAX` je podignut jer
    bi inače 6. zahtjev pao na 429 i serija ne bi bila serija; limit se dokazuje
    zasebnim testom, ovaj mjeri isključivo nepromjenjivost kataloga.
    """
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    llm_radi = {"da": True}

    def _fake(payload: dict) -> HintLLMResult:
        if not llm_radi["da"]:
            raise HintLLMError("simulirani pad providera")
        return HintLLMResult(text=_LLM_TEXT, input_tokens=386, output_tokens=42)

    monkeypatch.setattr("agents.hint_agent.generate_hint", _fake)
    monkeypatch.setattr(config, "USE_LLM_HINTS", True)
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "test-key-not-real")
    monkeypatch.setattr(config, "HINT_MAX", 20)

    with SessionLocal() as s:
        prije = s.scalar(select(func.count()).select_from(Hint))

    app = create_app()
    async with _stack(app), _client(app) as c:
        for n in range(1, 11):
            llm_radi["da"] = n <= 5
            _attempt(uid, tid, n=n, correct=False, et="row_mismatch")
            r = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))
            assert r.status_code == 200, f"{n}. hint: {r.text}"

    with SessionLocal() as s:
        poslije = s.scalar(select(func.count()).select_from(Hint))

    izvori = [x.source for x in _rows(uid)]
    assert izvori == ["llm"] * 5 + ["fallback"] * 5
    assert len(_rows(uid)) == 10, "🔴 Exit: 10 hintova → 10 redaka u hint_requests"

    # 🔴 Exit: svaki redak pokazuje na NETOČAN pokušaj — provjereno kroz FK, ne pretpostavljeno.
    with SessionLocal() as s:
        ciljevi = list(
            s.scalars(
                select(Attempt.is_correct).where(
                    Attempt.id.in_([x.after_attempt_id for x in _rows(uid)])
                )
            ).all()
        )
    assert ciljevi and not any(ciljevi), "hint zakačen na točan pokušaj"
    assert prije == poslije, "runtime je pisao u katalog — H2.2a prekršen"


@pytest.mark.asyncio
async def test_agent_log_carries_no_hint_text_or_query(hint_user, llm_ok) -> None:
    """🔴 Exit (D4): `agent_messages_log` ne sadrži ni `hint_text` ni studentov upit.

    Provjera je nad SADRŽAJEM loga u bazi, ne nad čitanjem koda.
    """
    uid, tid = hint_user["user_id"], hint_user["task_id"]
    _attempt(uid, tid, n=1, correct=False, et="row_mismatch")

    app = create_app()
    async with _stack(app), _client(app) as c:
        pocetak = datetime.now(timezone.utc) - timedelta(seconds=1)
        r = await c.post("/hint", json={"task_id": tid}, headers=auth_header(uid))
    assert r.status_code == 200

    with SessionLocal() as s:
        zapisi = list(
            s.scalars(
                select(AgentMessageLog.content).where(
                    AgentMessageLog.created_at >= pocetak
                )
            ).all()
        )
    blob = str(zapisi)
    assert zapisi, "hint mora ostaviti FIPA trag"
    assert _LLM_TEXT not in blob, "tekst hinta procurio u trajni log"
    assert "county" not in blob, "studentov upit procurio u trajni log"
    assert "hint_len" in blob, "redigirani zapis mora bilježiti bar duljinu"
