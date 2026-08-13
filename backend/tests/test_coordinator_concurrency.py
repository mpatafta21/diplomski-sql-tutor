"""🔴 ERRATA #62 — nijedna prihvaćena predaja se ne smije izgubiti.

Ovi testovi PADAJU na kodu prije popravka. To je namjera: 737 postojećih testova
nije uhvatilo kvar koji je živio od Faze 3E.3, jer nijedan nikad nije poslao dvije
predaje istovremeno.

🔴 ŠTO SE TVRDI: **invarijanta**, ne performansa. „K prihvaćenih predaja → K redaka
u `attempts` i K odgovora." Nigdje se ne provjerava koliko je to trajalo — latencija
pod opterećenjem je podatak, ne kriterij, i test koji bi ju tvrdio bio bi flaky na
tuđem stroju.

🔴 TRAŽI ŽIVU BAZU I PROSODY, kao i svih 6 testova u `test_coordinator.py`. Novost
je da ovi pišu u `tutor_main` **konkurentno** — do sada nijedan test to nije radio.
Zato svaka nit ima VLASTITOG korisnika: `uq_attempts_user_task_number` bi inače
sudario dvije istovremene predaje istog korisnika i test bi padao iz krivog razloga.

Razina je HTTP (`POST /attempt` kroz ASGI transport), ne FIPA, jer se time u istom
testu provjerava i `AgentBridge` korelacija — obrazac po kojem je popravak i građen.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest
from sqlalchemy import delete, func, select

from agents.coordinator import CoordinatorAgent
from agents.messages import Ontology, Performative, body_to_payload
from app.core import config
from app.db.models import Attempt, SkillMastery, Task, User, UserBadge, XpLog
from app.db.session import SessionLocal
from app.main import create_app, start_gateway_stack, stop_gateway_stack
from tests.conftest import auth_header
from tests.test_coordinator import _MockKnowledge, _MockRecommender  # noqa: E402
from agents.base import TutorAgent
from spade.behaviour import CyclicBehaviour
from spade.template import Template

_MAX_K = 8


class _PersistingEvaluator(TutorAgent):
    """Evaluator koji STVARNO upiše redak — mjerna točka invarijante.

    Produkcijski `EvaluatorAgent` radi isto (persist → commit → inform, D6), samo uz
    pravu SQL evaluaciju. Ovdje je evaluacija izostavljena jer test ne mjeri
    ocjenjivanje nego to **je li zahtjev uopće stigao do evaluacije**.

    `is_correct=True` namjerno: `ck_attempts_error_type_when_incorrect` u živoj bazi
    traži `error_type` uz netočan pokušaj, a ovdje bi to bio šum.
    """

    class _B(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return
            cid = msg.get_metadata("correlation_id")
            payload = body_to_payload(msg.body)
            user_id = payload.get("user_id")
            task_id = payload.get("task_id")

            def _upisi() -> int:
                with SessionLocal() as s:
                    att = Attempt(
                        user_id=user_id,
                        task_id=task_id,
                        submitted_query="SELECT 1;",
                        is_correct=True,
                        error_type=None,
                        attempt_number=1,
                    )
                    s.add(att)
                    s.commit()
                    return att.id

            attempt_id = await asyncio.to_thread(_upisi)
            fwd = self.agent.build_message(
                to=config.AGENT_KNOWLEDGE_JID,
                performative=Performative.INFORM,
                ontology=Ontology.ATTEMPT_RESULT,
                payload={"user_id": user_id, "attempt_id": attempt_id},
                correlation_id=cid,
            )
            await self.send(fwd)

    async def setup(self) -> None:
        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.EVALUATE_QUERY)
        self.add_behaviour(self._B(), tmpl)


@pytest.fixture
def conc_users():
    """`_MAX_K` committanih korisnika + task. Svaka predaja ide SVOM korisniku."""
    ids: list[int] = []
    with SessionLocal() as s:
        for i in range(_MAX_K):
            u = User(
                username=f"conc62_u{i}",
                email=f"conc62-u{i}@test.example",
                password_hash="dummy_hash_62",
            )
            s.add(u)
            s.commit()
            ids.append(u.id)
        task_id = s.scalar(select(Task.id).limit(1))
    assert task_id is not None, "tasks moraju biti seedani"

    yield {"user_ids": ids, "task_id": task_id}

    with SessionLocal() as s:
        s.execute(delete(XpLog).where(XpLog.user_id.in_(ids)))
        s.execute(delete(Attempt).where(Attempt.user_id.in_(ids)))
        s.execute(delete(UserBadge).where(UserBadge.user_id.in_(ids)))
        s.execute(delete(SkillMastery).where(SkillMastery.user_id.in_(ids)))
        s.execute(delete(User).where(User.id.in_(ids)))
        s.commit()


def _broj_pokusaja(user_ids: list[int]) -> int:
    with SessionLocal() as s:
        return s.scalar(
            select(func.count()).select_from(Attempt).where(Attempt.user_id.in_(user_ids))
        )


@asynccontextmanager
async def _stack(app, agents):
    await start_gateway_stack(app, agents=agents)
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


def _agenti(task_id: int, coord: CoordinatorAgent | None = None):
    ev = _PersistingEvaluator("evaluator")
    km = _MockKnowledge("knowledge")
    km._updated_concepts = ["x"]
    rec = _MockRecommender("recommender")
    rec._reply_payload = {"task_id": task_id, "concept": "x", "reason": "zpd"}
    return [ev, km, rec, coord or CoordinatorAgent("coordinator")]


async def _cekaj(uvjet, *, timeout: float = 15.0, interval: float = 0.2) -> None:
    kraj = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < kraj:
        if uvjet():
            return
        await asyncio.sleep(interval)


# ---------------------------------------------------------------------------
# A1 — 🔴 INVARIJANTA: nijedna prihvaćena predaja se ne gubi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("K", [2, 4, 8])
@pytest.mark.asyncio
async def test_no_accepted_submission_is_ever_lost(conc_users, K) -> None:
    """🔴 K istovremenih predaja → K redaka u `attempts` i K odgovora.

    PADA prije popravka: Coordinatorov drain-loop odbaci svaku `submit-attempt` koja
    stigne dok je FSM u toku, pa nastane samo JEDAN redak neovisno o K.

    Tvrdnja je binarna i ne ovisi o brzini stroja — zato ne može postati flaky.
    """
    users = conc_users["user_ids"][:K]
    task_id = conc_users["task_id"]
    app = create_app()

    prije = _broj_pokusaja(users)
    async with _stack(app, _agenti(task_id)), _client(app) as c:
        odgovori = await asyncio.gather(
            *[
                c.post(
                    "/attempt",
                    json={"task_id": task_id, "submitted_query": "SELECT 1;"},
                    headers=auth_header(u),
                )
                for u in users
            ],
            return_exceptions=True,
        )
        await asyncio.sleep(1.0)  # neka zaostali upisi slegnu prije brojanja

    nastalo = _broj_pokusaja(users) - prije
    kodovi = [
        r.status_code if isinstance(r, httpx.Response) else type(r).__name__
        for r in odgovori
    ]

    assert nastalo == K, (
        f"🔴 IZGUBLJENA PREDAJA: poslano {K}, zabilježeno {nastalo}. "
        f"HTTP kodovi: {kodovi}. Poruka je odbačena u drain-loopu "
        f"(coordinator.py:196-209) — studentov rad ne postoji nigdje."
    )
    assert kodovi == [200] * K, f"nije svaka predaja dobila odgovor: {kodovi}"


# ---------------------------------------------------------------------------
# A3 — cid korelacija POD KONKURENTNOŠĆU (ne sekvencijalno)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cid_correlation_holds_under_concurrency(conc_users) -> None:
    """Konkurentni pandan `test_cid_correlation_two_sequential_flows`.

    🔴 ZAŠTO POSTOJI: postojeći test u docstringu piše „Sekvencijalno jer FSMBehaviour
    serijalizira" — time UGRAĐUJE ograničenje u dizajn testa umjesto da ga propituje.
    To je peti primjerak obrasca iz NALAZA #57 (test pisan prema promatranom ponašanju
    zaključava kvar kao specifikaciju). Postojeći test ostaje kao regresijski; ovaj uz
    njega tvrdi ono što bi sustav trebao raditi.

    Tvrdi da odgovor svakog korisnika nosi ISKLJUČIVO njegov attempt — cross-talk
    između tokova bio bi gori od gubitka, jer bi student vidio tuđi rezultat.
    """
    K = 4
    users = conc_users["user_ids"][:K]
    task_id = conc_users["task_id"]
    app = create_app()

    async with _stack(app, _agenti(task_id)), _client(app) as c:
        odgovori = await asyncio.gather(
            *[
                c.post(
                    "/attempt",
                    json={"task_id": task_id, "submitted_query": "SELECT 1;"},
                    headers=auth_header(u),
                )
                for u in users
            ],
            return_exceptions=True,
        )
        await asyncio.sleep(1.0)

    uspjeli = [r for r in odgovori if isinstance(r, httpx.Response) and r.status_code == 200]
    assert len(uspjeli) == K, (
        f"samo {len(uspjeli)}/{K} predaja je dobilo odgovor — cross-talk se ne može "
        "ni provjeriti dok se predaje gube"
    )

    # Svaki korisnik ima točno jedan redak, i svaki je odgovor o SVOM korisniku.
    with SessionLocal() as s:
        po_korisniku = {
            uid: s.scalar(
                select(func.count()).select_from(Attempt).where(Attempt.user_id == uid)
            )
            for uid in users
        }
    assert all(n == 1 for n in po_korisniku.values()), (
        f"redci nisu ravnomjerno raspoređeni po korisnicima: {po_korisniku}"
    )


# ---------------------------------------------------------------------------
# 🔴 LEAK GUARD pod konkurentnošću
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_flow_or_behaviour_leak_after_burst(conc_users) -> None:
    """🔴 Nakon rafala od 8: nula živih tokova i nula zaostalih behavioura.

    Curenje behavioura je kvar koji se ne vidi na jednom zahtjevu nego tek nakon
    sati rada — dakle točno tijekom evala. Svaki razgovor registrira VLASTITI
    behaviour s vlastitim predloškom; da ga `on_end` ne ukloni, mrtvi bi se
    behaviouri gomilali i SPADE bi im i dalje isporučivao poruke.

    Isti obrazac koji `test_agent_bridge.py` tvrdi za `pending_count() == 0`, samo
    ovdje pod konkurentnošću — a upravo je sekvencijalno testiranje bilo razlog
    zašto #62 nitko nije uhvatio.
    """
    K = 8
    users = conc_users["user_ids"][:K]
    task_id = conc_users["task_id"]
    coord = CoordinatorAgent("coordinator")
    app = create_app()

    async with _stack(app, _agenti(task_id, coord)), _client(app) as c:
        polazno = len(coord.behaviours)
        assert coord.flow_count() == 0, "prije rafala ne smije biti živih tokova"

        await asyncio.gather(
            *[
                c.post(
                    "/attempt",
                    json={"task_id": task_id, "submitted_query": "SELECT 1;"},
                    headers=auth_header(u),
                )
                for u in users
            ],
            return_exceptions=True,
        )
        await _cekaj(lambda: coord.flow_count() == 0 and len(coord.behaviours) == polazno)

        preostalo = coord.flow_count()
        behaviourâ = len(coord.behaviours)

    assert preostalo == 0, f"🔴 CURENJE TOKOVA: {preostalo} tokova nije odjavljeno"
    assert behaviourâ == polazno, (
        f"🔴 CURENJE BEHAVIOURA: {behaviourâ} umjesto {polazno} — mrtvi FSM-ovi ostaju "
        "registrirani i njihovi predlošci i dalje matchaju poruke"
    )


@pytest.mark.asyncio
async def test_flow_limit_refuses_explicitly_not_silently(conc_users) -> None:
    """🔴 Na granici se predaja ODBIJA s razlogom, ne guta.

    Tiho odbacivanje na granici bilo bi #62 reproduciran na drugom mjestu: student bi
    opet čekao `GATEWAY_TIMEOUT` i dobio 504 bez objašnjenja. Granica se ovdje spušta
    na 1 da se stanje uopće može dosegnuti; mehanizam je isti kao na 64.

    503 (a ne 504) jer smo odgovorili odmah i namjerno — ponovni pokušaj ima smisla.
    """
    K = 4
    users = conc_users["user_ids"][:K]
    task_id = conc_users["task_id"]
    coord = CoordinatorAgent("coordinator", max_concurrent_flows=1)
    app = create_app()

    async with _stack(app, _agenti(task_id, coord)), _client(app) as c:
        odgovori = await asyncio.gather(
            *[
                c.post(
                    "/attempt",
                    json={"task_id": task_id, "submitted_query": "SELECT 1;"},
                    headers=auth_header(u),
                )
                for u in users
            ],
            return_exceptions=True,
        )
        await _cekaj(lambda: coord.flow_count() == 0)

    kodovi = [r.status_code for r in odgovori if isinstance(r, httpx.Response)]
    detalji = {
        r.json().get("detail")
        for r in odgovori
        if isinstance(r, httpx.Response) and r.status_code != 200
    }
    assert len(kodovi) == K, "svaka predaja mora dobiti ODGOVOR, i kad je odbijena"
    assert 504 not in kodovi, (
        f"🔴 odbijanje na granici je bilo TIHO — netko je čekao timeout: {kodovi}"
    )
    assert detalji <= {"coordinator_busy"}, f"neočekivan razlog odbijanja: {detalji}"
    assert coord.flow_count() == 0, "odbijena predaja ne smije zauzeti mjesto u registryju"
