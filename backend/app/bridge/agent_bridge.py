"""AgentBridge — korelacijski registry između HTTP requesta i XMPP odgovora.

Čista async komponenta ISPOD Coordinator FSM-a (Faza 3E.2a). Drži mapiranje
`correlation_id → asyncio.Future` tako da HTTP handler može sinkrono čekati
asinkroni FIPA odgovor:

    HTTP → bridge.register() → (cid, future)
         → FIPA poruka Coordinatoru (s cid u metadata)
         → Coordinator FSM obradi → FIPA inform natrag (isti cid)
         → bridge.resolve(cid, result)  → future.set_result
         → bridge.wait(cid, timeout)    → HTTP dobije rezultat

Registry je AGNOSTIČAN na sadržaj — ne zna što je "attempt-result" ni koja je
ontologija; drži isključivo correlation_id → Future.

--------------------------------------------------------------------------------
EVENT-LOOP MODEL (KORAK 0 nalaz, 3E.2a)
--------------------------------------------------------------------------------
SPADE 4.1.2 koristi JEDAN dijeljeni asyncio loop (singleton Container; loop se
posvaja preko asyncio.get_running_loop() pri kreiranju Containera). Svi agenti i
njihovi behaviouri teku kao taskovi na tom istom loopu — nema per-agent threada.

Kad u Fazi 3E.3 uvicorn (FastAPI) i SPADE agenti žive u istom procesu i agenti se
startaju UNUTAR uvicornovog loopa (FastAPI lifespan/startup), Container posvaja
uvicornov loop. Tada su:
  - HTTP handler koji čeka future (bridge.wait), i
  - Coordinatorov behaviour koji rezolvira future (bridge.resolve)
na ISTOM loopu → `future.set_result(...)` izravno je siguran (Case A, plain async).

PREDUVJET koji 3E.3 mora poštovati: SPADE agente startati unutar uvicornovog
event loopa. Ako bi se ikad SPADE pokretao u zasebnom threadu/loopu (Case B),
resolve/reject treba prebaciti na loop Futurea:
    future.get_loop().call_soon_threadsafe(future.set_result, result)
To je jedina izmjena potrebna za thread-safe varijantu; API ostaje isti.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any


class AgentBridge:
    """Korelacijski registry: correlation_id → asyncio.Future (plain async, Case A).

    Centralni invariant — LEAK GUARD: nakon što `wait()` završi BILO KAKO
    (rezultat / TimeoutError / re-raised exc), correlation_id se UVIJEK ukloni iz
    `_pending`. Bez toga bi dugotrajni server curio po jedan red na svaki
    timeoutani ili orphaned request.
    """

    def __init__(self) -> None:
        self._pending: dict[str, asyncio.Future[Any]] = {}

    def register(self) -> tuple[str, asyncio.Future[Any]]:
        """Generiraj jedinstven correlation_id + Future na tekućem (dijeljenom) loopu.

        Mora se pozvati iz async konteksta (running loop postoji) — Future se veže
        na loop na kojem HTTP handler čeka, što je isti loop na kojem Coordinatorov
        behaviour rezolvira (KORAK 0, Case A).

        Returns:
            (correlation_id, future) — pozivatelj šalje cid u FIPA poruci i await-a
            rezultat preko `wait(cid, timeout)`.
        """
        correlation_id = str(uuid.uuid4())
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending[correlation_id] = future
        return correlation_id, future

    def resolve(self, correlation_id: str, result: Any) -> bool:
        """Rezolviraj Future za dani cid rezultatom.

        Returns:
            True ako je Future rezolviran; False ako cid ne postoji ili je Future
            već dovršen (npr. dvostruki resolve, ili već timeoutan). Ne baca.
        """
        future = self._pending.get(correlation_id)
        if future is None or future.done():
            return False
        future.set_result(result)
        return True

    def reject(self, correlation_id: str, exc: BaseException) -> bool:
        """Postavi iznimku na Future za dani cid.

        Returns:
            True ako je iznimka postavljena; False ako cid ne postoji ili je Future
            već dovršen. Ne baca.
        """
        future = self._pending.get(correlation_id)
        if future is None or future.done():
            return False
        future.set_exception(exc)
        return True

    async def wait(self, correlation_id: str, timeout: float) -> Any:
        """Čekaj rezultat za dani cid do `timeout` sekundi.

        LEAK GUARD: cid se uklanja iz `_pending` u `finally` — bezuvjetno, na
        svakom izlazu (rezultat, asyncio.TimeoutError, re-raised exc).

        Raises:
            KeyError: ako cid nije registriran (programska greška).
            asyncio.TimeoutError: ako timeout istekne prije resolve/reject.
            BaseException: re-raise one koju je postavio `reject()`.
        """
        future = self._pending.get(correlation_id)
        if future is None:
            raise KeyError(f"correlation_id {correlation_id!r} nije registriran")
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            self._pending.pop(correlation_id, None)

    def pending_count(self) -> int:
        """Broj trenutno neriješenih korelacija (introspekcija / leak testovi)."""
        return len(self._pending)
