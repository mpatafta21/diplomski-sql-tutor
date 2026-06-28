"""Testovi za AgentBridge — korelacijski registry (Faza 3E.2a).

Čisti asyncio testovi (pytest-asyncio, auto mode) — bez HTTP servera, bez SPADE.
Fokus: korektnost korelacije + LEAK GUARD (pending_count == 0 na svakom ishodu).
"""

from __future__ import annotations

import asyncio
import uuid

import pytest

from app.bridge.agent_bridge import AgentBridge


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_generates_unique_uuid_and_pending_future():
    """register() vraća jedinstven UUID4, Future je pending, pending_count raste."""
    bridge = AgentBridge()
    assert bridge.pending_count() == 0

    cid1, fut1 = bridge.register()
    cid2, fut2 = bridge.register()

    # validan UUID4 i jedinstvenost
    assert uuid.UUID(cid1).version == 4
    assert uuid.UUID(cid2).version == 4
    assert cid1 != cid2

    # Future pending dok nije rezolviran
    assert not fut1.done()
    assert not fut2.done()
    assert bridge.pending_count() == 2

    # cleanup da izbjegnemo "Future was never retrieved" — rezolviraj i pokupi
    bridge.resolve(cid1, None)
    bridge.resolve(cid2, None)
    await bridge.wait(cid1, timeout=1)
    await bridge.wait(cid2, timeout=1)


# ---------------------------------------------------------------------------
# resolve / wait redoslijed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resolve_before_wait_returns_result_immediately():
    """resolve prije wait → wait odmah vrati rezultat (Future već done)."""
    bridge = AgentBridge()
    cid, _ = bridge.register()

    assert bridge.resolve(cid, {"xp": 42}) is True
    result = await bridge.wait(cid, timeout=1)

    assert result == {"xp": 42}
    assert bridge.pending_count() == 0


@pytest.mark.asyncio
async def test_wait_then_resolve_releases_waiter():
    """wait blokira u tasku → resolve ga otpusti s rezultatom."""
    bridge = AgentBridge()
    cid, _ = bridge.register()

    waiter = asyncio.create_task(bridge.wait(cid, timeout=5))
    await asyncio.sleep(0)  # pusti waiter da uđe u wait_for
    assert not waiter.done()

    assert bridge.resolve(cid, "done") is True
    result = await waiter

    assert result == "done"
    assert bridge.pending_count() == 0


# ---------------------------------------------------------------------------
# 🔴 LEAK GUARD — sva tri ishoda čiste _pending
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_timeout_raises_and_cleans_pending():
    """🔴 wait bez resolve → TimeoutError I pending_count == 0 (leak guard)."""
    bridge = AgentBridge()
    cid, _ = bridge.register()
    assert bridge.pending_count() == 1

    with pytest.raises(asyncio.TimeoutError):
        await bridge.wait(cid, timeout=0.05)

    assert bridge.pending_count() == 0, "timeoutani cid mora biti uklonjen iz _pending"


@pytest.mark.asyncio
async def test_success_cleans_pending():
    """🔴 nakon uspješnog wait-a → pending_count == 0."""
    bridge = AgentBridge()
    cid, _ = bridge.register()

    bridge.resolve(cid, 1)
    await bridge.wait(cid, timeout=1)

    assert bridge.pending_count() == 0


@pytest.mark.asyncio
async def test_reject_reraises_and_cleans_pending():
    """🔴 reject → wait re-raisa exc, pending_count == 0."""
    bridge = AgentBridge()
    cid, _ = bridge.register()

    sentinel = RuntimeError("agent failure")
    assert bridge.reject(cid, sentinel) is True

    with pytest.raises(RuntimeError, match="agent failure"):
        await bridge.wait(cid, timeout=1)

    assert bridge.pending_count() == 0


# ---------------------------------------------------------------------------
# Idempotencija / robusnost — ne baca
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_double_resolve_second_returns_false():
    """Dvostruki resolve istog cid → drugi vrati False (Future done), ne baca; prvi pobjeđuje."""
    bridge = AgentBridge()
    cid, _ = bridge.register()

    assert bridge.resolve(cid, "first") is True
    assert bridge.resolve(cid, "second") is False

    result = await bridge.wait(cid, timeout=1)
    assert result == "first"
    assert bridge.pending_count() == 0


@pytest.mark.asyncio
async def test_resolve_and_reject_unknown_cid_return_false():
    """resolve/reject nepostojećeg cid → False, ne baca."""
    bridge = AgentBridge()

    assert bridge.resolve("nepostojeci", 123) is False
    assert bridge.reject("nepostojeci", RuntimeError("x")) is False
    assert bridge.pending_count() == 0


@pytest.mark.asyncio
async def test_wait_unknown_cid_raises_keyerror():
    """wait nad neregistriranim cid → KeyError (programska greška), bez leak-a."""
    bridge = AgentBridge()
    with pytest.raises(KeyError):
        await bridge.wait("nepostojeci", timeout=1)
    assert bridge.pending_count() == 0


# ---------------------------------------------------------------------------
# Concurrency — nema cross-talka
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_register_wait_resolve_no_crosstalk():
    """50 paralelnih register+wait, svaki rezolviran svojim rezultatom — bez cross-talka."""
    bridge = AgentBridge()
    n = 50

    cids = [bridge.register()[0] for _ in range(n)]
    assert bridge.pending_count() == n

    waiters = {cid: asyncio.create_task(bridge.wait(cid, timeout=5)) for cid in cids}
    await asyncio.sleep(0)  # pusti sve waitere u wait_for

    # rezolviraj u izmiješanom redoslijedu (obrnuto) da dokažemo da nema redoslijed-ovisnosti
    for idx, cid in reversed(list(enumerate(cids))):
        assert bridge.resolve(cid, f"result-{idx}") is True

    results = await asyncio.gather(*(waiters[cid] for cid in cids))

    for idx, res in enumerate(results):
        assert res == f"result-{idx}", f"cross-talk: cid {idx} dobio {res!r}"

    assert bridge.pending_count() == 0
