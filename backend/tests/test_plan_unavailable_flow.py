"""🔴 `plan_unavailable` NE stvara pokušaj — 503, i utor se oslobađa.

**Odluka (2026-08-14):** `plan_unavailable` je jedini `error_type` gdje nije
zakazao student, nego sustav. Zapis o smetnji ide u log, ne u `attempts`.
Perzistirati ga značilo bi da `attempts` nosi dvije uloge — zapis o studentovom
radu i zapis o kvaru sustava — a taj je obrazac već bio uzrok kvara na ovoj grani
(`_BLOCK_VALUE`) i razlog uklanjanja `entry_task_id`.

Izmjereno prije odluke (pun lanac, stvarni pad EXPLAIN-a, ne mock): jedna smetnja
je studentu koji je predao ISPRAVAN upit upisala `is_correct=false`, BKT
ažuriranje s netočnim ishodom i potrošila hint kredit. Šteta po BKT-u ovisi o
polaznom znanju i najveća je usred učenja:

| polazni p_l | netočan | točan | šteta |
|---|---|---|---|
| 0.05 | 0.1078 | 0.3782 | −0.27 |
| 0.50 | 0.2286 | 0.9053 | **−0.68** |
| 0.80 | 0.4600 | 0.9743 | −0.51 |

🔴 **ZAŠTO OVAJ TEST POSTOJI, A NE ARGUMENT U WRAPUPU.** Tvrdnja „aditivna grana
ne dira mehaniku tokova" je invarijanta o konkurentnosti, a projekt ondje ima
dokazanu slijepu točku: ERRATA #62 je bila invarijanta zapisana komentarom,
neistinita tri mjeseca, koju 737 testova nije uhvatilo jer nijedan nikad nije
poslao dvije predaje istovremeno.

🔴 **Curenje utora se ne vidi u jednokratnom testu.** `MAX_CONCURRENT_FLOWS` je 64,
pa bi se procurjeli utor očitovao tek nakon 64 smetnje — dakle usred otvorenog
evala, kao „sve predaje odjednom vraćaju 503".

TRAŽI ŽIVU BAZU I PROSODY (kao `test_coordinator_concurrency.py`). Svaka predaja
ide SVOM korisniku — `uq_attempts_user_task_number` bi inače sudario dvije
istovremene predaje istog korisnika i test bi padao iz krivog razloga.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest
from sqlalchemy import delete, func, select, text

from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template

from agents.base import TutorAgent
from agents.coordinator import CoordinatorAgent, _flow_template
from agents.evaluator_agent import EvaluatorAgent
from agents.knowledge_agent import KnowledgeModelAgent
from agents.messages import Ontology, Performative, body_to_payload
from app.core import config
from app.db.models import (
    Attempt,
    Concept,
    HintRequest,
    Misconception,
    SkillMastery,
    SkillMasteryHistory,
    Task,
    TaskConcept,
    User,
    UserBadge,
    XpLog,
)
from app.db.session import SessionLocal
from app.main import create_app, start_gateway_stack, stop_gateway_stack
from tests.conftest import auth_header
from tests.test_coordinator import _MockRecommender

_N_SEKVENCIJALNO = 10
_K_ISTOVREMENO = 8

#: Referentni upit koji se NE MOŽE isplanirati → `EXPLAIN` pada stvarno.
#: 🔴 Nije mock: `plan_unavailable` se u produkciji rađa iz istog mjesta
#: (`runner.explain(...).success is False`), samo ondje iz timeouta.
_NEPLANIRAJUC = "SELECT id FROM _diag_nepostojeca_tablica_flow;"

#: Upit koji TOČNO reproducira `expected_result` pokvarenog zadatka. Mora se
#: poklopiti, inače tok padne na usporedbi redaka i NIKAD ne stigne do
#: plan-provjere — točno ta greška je prvu verziju ovog testa učinila zelenom
#: iz krivog razloga.
_ISPRAVAN_ZA_POKVAREN = (
    "SELECT id FROM orders WHERE customer_id = 42 ORDER BY id;"
)


@pytest.fixture
def plan_env():
    """Pokvaren M6 zadatak + ispravan zadatak + korisnici. Sve se briše u teardownu."""
    user_ids: list[int] = []
    with SessionLocal() as s:
        # Redci koje ispravan upit vraća — postaju `expected_result` pokvarenog
        # zadatka, pa se usporedba redaka POKLAPA i tok stigne do plan-provjere.
        redci = [
            {"id": r[0]}
            for r in s.execute(
                text(
                    "SELECT unnest(ARRAY[74, 259, 847]) AS id"
                )
            ).all()
        ]
        modul6 = s.scalar(text("SELECT id FROM modules WHERE number = 6"))
        broken = Task(
            module_id=modul6,
            title="_DIAG plan_unavailable tok",
            description="Privremeni zadatak: referentni upit je neplanirajuć.",
            sandbox_schema="ecommerce_v1",
            expected_query=_NEPLANIRAJUC,
            expected_result=redci,
            difficulty=3,
            is_active=True,
            source_id="_diag_plan_unavailable_flow",
        )
        s.add(broken)
        s.commit()
        broken_id = broken.id
        cid_index = s.scalar(select(Concept.id).where(Concept.code == "index_usage"))
        s.add(TaskConcept(task_id=broken_id, concept_id=cid_index, is_primary=True))

        for i in range(max(_N_SEKVENCIJALNO, _K_ISTOVREMENO)):
            u = User(
                username=f"planun_u{i}",
                email=f"planun-u{i}@test.example",
                password_hash="dummy_hash_planun",
            )
            s.add(u)
            s.commit()
            user_ids.append(u.id)

        zdrav_id = s.scalar(
            select(Task.id)
            .join(TaskConcept, TaskConcept.task_id == Task.id)
            .join(Concept, Concept.id == TaskConcept.concept_id)
            .where(
                Concept.code == "select_basic",
                TaskConcept.is_primary.is_(True),
                Task.is_active.is_(True),
            )
            .limit(1)
        )
        zdrav = s.get(Task, zdrav_id)
        zdrav_query = zdrav.expected_query
        s.commit()

    yield {
        "broken_task_id": broken_id,
        "zdrav_task_id": zdrav_id,
        "zdrav_query": zdrav_query,
        "user_ids": user_ids,
    }

    with SessionLocal() as s:
        s.execute(
            delete(SkillMasteryHistory).where(SkillMasteryHistory.user_id.in_(user_ids))
        )
        s.execute(delete(HintRequest).where(HintRequest.user_id.in_(user_ids)))
        s.execute(delete(XpLog).where(XpLog.user_id.in_(user_ids)))
        s.execute(delete(Misconception).where(Misconception.user_id.in_(user_ids)))
        s.execute(delete(Attempt).where(Attempt.user_id.in_(user_ids)))
        s.execute(delete(SkillMastery).where(SkillMastery.user_id.in_(user_ids)))
        s.execute(delete(UserBadge).where(UserBadge.user_id.in_(user_ids)))
        s.execute(delete(User).where(User.id.in_(user_ids)))
        s.execute(delete(TaskConcept).where(TaskConcept.task_id == broken_id))
        s.execute(delete(Task).where(Task.id == broken_id))
        s.commit()


@asynccontextmanager
async def _stack(app, agents):
    await start_gateway_stack(app, agents=agents)
    await asyncio.sleep(0.6)
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


def _agenti(coord: CoordinatorAgent):
    """Pravi Evaluator i KM — samo tako `evaluate()` doista proizvede plan_unavailable."""
    rec = _MockRecommender("recommender")
    rec._reply_payload = {"task_id": 1, "concept": "x", "reason": "zpd"}
    return [
        EvaluatorAgent("evaluator"),
        KnowledgeModelAgent("knowledge"),
        rec,
        coord,
    ]


def _broj_pokusaja(user_ids: list[int]) -> int:
    with SessionLocal() as s:
        return s.scalar(
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.user_id.in_(user_ids))
        )


def _broj_bkt(user_ids: list[int]) -> int:
    with SessionLocal() as s:
        return s.scalar(
            select(func.count())
            .select_from(SkillMasteryHistory)
            .where(SkillMasteryHistory.user_id.in_(user_ids))
        )


# ---------------------------------------------------------------------------
# 1 — smetnja ne postaje pokušaj, i utor se vraća
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_plan_unavailable_daje_503_i_ne_stvara_pokusaj(plan_env) -> None:
    """🔴 Jezgra odluke: ishod sustava i ishod u bazi se NE smiju razilaziti."""
    users = plan_env["user_ids"][:_N_SEKVENCIJALNO]
    tid = plan_env["broken_task_id"]
    app = create_app()
    coord = CoordinatorAgent("coordinator")

    prije_pokusaja = _broj_pokusaja(users)
    prije_bkt = _broj_bkt(users)

    async with _stack(app, _agenti(coord)), _client(app) as c:
        odgovori = []
        for u in users:
            r = await c.post(
                "/attempt",
                json={"task_id": tid, "submitted_query": _ISPRAVAN_ZA_POKVAREN},
                headers=auth_header(u),
            )
            odgovori.append(r)
        await asyncio.sleep(1.0)
        utori_na_kraju = coord.flow_count()

    statusi = [r.status_code for r in odgovori]
    assert statusi == [503] * _N_SEKVENCIJALNO, f"očekujem sve 503, dobio {statusi}"
    for r in odgovori:
        assert r.json()["detail"] == "plan_unavailable", r.text

    assert _broj_pokusaja(users) == prije_pokusaja, (
        "smetnja sustava je upisana kao studentov pokušaj — razred ERRATE #63"
    )
    assert _broj_bkt(users) == prije_bkt, (
        "BKT je ažuriran ishodom koji student nije prouzročio"
    )


@pytest.mark.asyncio
async def test_utor_se_oslobadja_na_svakoj_smetnji(plan_env) -> None:
    """🔴 Curenje utora vidi se tek nakon 64 smetnje — dakle usred evala.

    Zato se broji `flow_count()` PRIJE i POSLIJE N uzastopnih smetnji, umjesto da
    se vjeruje komentaru uz `on_end`. Dokazano namjernim kvarom: preskoči li se
    `_release_flow` na novom putu, ovaj test pada s brojem procurjelih utora.
    """
    users = plan_env["user_ids"][:_N_SEKVENCIJALNO]
    tid = plan_env["broken_task_id"]
    app = create_app()
    coord = CoordinatorAgent("coordinator")

    async with _stack(app, _agenti(coord)), _client(app) as c:
        utori_na_pocetku = coord.flow_count()
        for u in users:
            await c.post(
                "/attempt",
                json={"task_id": tid, "submitted_query": _ISPRAVAN_ZA_POKVAREN},
                headers=auth_header(u),
            )
        await asyncio.sleep(1.5)
        utori_na_kraju = coord.flow_count()

    assert utori_na_pocetku == 0
    assert utori_na_kraju == 0, (
        f"{utori_na_kraju} utor(a) procurilo nakon {_N_SEKVENCIJALNO} smetnji — "
        f"granica od 64 bila bi dosegnuta nakon ~{64 // max(utori_na_kraju, 1)} "
        "smetnji i SVE predaje bi počele vraćati 503"
    )


# ---------------------------------------------------------------------------
# 2 — konkurentnost: mješavina smetnji i normalnih predaja
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_istovremene_predaje_ne_mijesaju_ishode(plan_env) -> None:
    """K=8 istovremeno, pola na pokvaren zadatak: svatko dobije SVOJ ishod.

    Tvrdnja je o KORELACIJI, ne o brzini: nijedan korisnik ne smije dobiti tuđi
    odgovor, i nijedna predaja se ne smije izgubiti. Isti oblik kao ERRATA #62,
    samo s dva različita ishoda u istom naletu.
    """
    users = plan_env["user_ids"][:_K_ISTOVREMENO]
    smetnja = users[::2]  # parni → pokvaren zadatak
    zdravi = users[1::2]  # neparni → ispravan zadatak
    app = create_app()
    coord = CoordinatorAgent("coordinator")

    prije = _broj_pokusaja(users)

    async with _stack(app, _agenti(coord)), _client(app) as c:
        zadaci = [
            c.post(
                "/attempt",
                json={
                    "task_id": plan_env["broken_task_id"]
                    if u in smetnja
                    else plan_env["zdrav_task_id"],
                    "submitted_query": _ISPRAVAN_ZA_POKVAREN
                    if u in smetnja
                    else plan_env["zdrav_query"],
                },
                headers=auth_header(u),
            )
            for u in users
        ]
        odgovori = await asyncio.gather(*zadaci, return_exceptions=True)
        await asyncio.sleep(1.5)
        utori_na_kraju = coord.flow_count()

    iznimke = [o for o in odgovori if isinstance(o, Exception)]
    assert not iznimke, f"predaje su se izgubile kao iznimke: {iznimke}"

    po_korisniku = dict(zip(users, odgovori))
    for u in smetnja:
        assert po_korisniku[u].status_code == 503, (
            f"korisnik {u} je predao na pokvaren zadatak a dobio "
            f"{po_korisniku[u].status_code} — unakrsni odgovor"
        )
        assert po_korisniku[u].json()["detail"] == "plan_unavailable"
    for u in zdravi:
        assert po_korisniku[u].status_code == 200, (
            f"korisnik {u} je predao na ispravan zadatak a dobio "
            f"{po_korisniku[u].status_code} — smetnja je procurila na tuđi tok"
        )

    assert _broj_pokusaja(users) - prije == len(zdravi), (
        "broj pokušaja mora biti TOČNO broj zdravih predaja — smetnje ne upisuju "
        "redak, a nijedna zdrava predaja se ne smije izgubiti"
    )
    assert utori_na_kraju == 0, f"{utori_na_kraju} utor(a) procurilo pod opterećenjem"


# ---------------------------------------------------------------------------
# 4 — brana protiv ODBAČENE izvedbe (granananje na sadržaj payloada)
# ---------------------------------------------------------------------------


class _KMSErrorKljucem(TutorAgent):
    """KM koji šalje LEGITIMAN `inform(model-updated)` s poljem `error` u payloadu.

    🔴 Postoji da zaključa odluku, ne da opiše stvarnost. Razmatrana (i odbijena)
    izvedba granala je na `payload.get("error")`; pod njom bi ovakva poruka tiho
    prekinula tok i student bi na uredno perzistiran pokušaj dobio 503.

    `error` je ovdje polje kakvo bi KM legitimno mogao dobiti sutra (npr. „jedan
    koncept nije ažuriran"), a NE objava da toka nema — tu razliku nosi
    performativ, ne sadržaj.
    """

    class _B(CyclicBehaviour):
        async def run(self) -> None:
            msg = await self.receive(timeout=10)
            if msg is None:
                return
            cid = msg.get_metadata("correlation_id")
            payload = body_to_payload(msg.body)
            signal = self.agent.build_message(
                to=config.AGENT_COORDINATOR_JID,
                performative=Performative.INFORM,
                ontology=Ontology.MODEL_UPDATED,
                payload={
                    "user_id": payload.get("user_id"),
                    "attempt_id": payload.get("attempt_id"),
                    "updated_concepts": [],
                    "error": "koncept_nije_azuriran",
                },
                correlation_id=cid,
            )
            await self.send(signal)

    async def setup(self) -> None:
        tmpl = Template()
        tmpl.set_metadata("ontology", Ontology.ATTEMPT_RESULT)
        self.add_behaviour(self._B(), tmpl)


@pytest.mark.asyncio
async def test_inform_s_error_kljucem_NE_prekida_tok(plan_env) -> None:
    """🔴 Granananje ide na PERFORMATIV, nikad na sadržaj payloada.

    Dokazano namjernim kvarom: zamijeni li se uvjet u `UpdateState` iz
    `performative == REFUSE` u `payload.get("error")`, ovaj test pada s 503 na
    predaji koja je uredno perzistirana.
    """
    u = plan_env["user_ids"][0]
    app = create_app()
    coord = CoordinatorAgent("coordinator")
    rec = _MockRecommender("recommender")
    rec._reply_payload = {"task_id": 1, "concept": "x", "reason": "zpd"}
    agenti = [
        EvaluatorAgent("evaluator"),
        _KMSErrorKljucem("knowledge"),
        rec,
        coord,
    ]

    async with _stack(app, agenti), _client(app) as c:
        r = await c.post(
            "/attempt",
            json={
                "task_id": plan_env["zdrav_task_id"],
                "submitted_query": plan_env["zdrav_query"],
            },
            headers=auth_header(u),
        )
        await asyncio.sleep(0.5)

    assert r.status_code == 200, (
        f"legitiman inform s poljem `error` prekinuo je tok ({r.status_code}) — "
        "izvedba je pala natrag na granananje po sadržaju"
    )
    assert r.json()["feedback"]["is_correct"] is True


# ---------------------------------------------------------------------------
# 5 — korelacijska izolacija: tuđi cid ne ulazi u tok
# ---------------------------------------------------------------------------


def test_refuse_s_tudjim_cid_ne_ulazi_u_tok() -> None:
    """🔴 Novi put NE smije oslabiti korelacijski router (#62).

    Tvrdi se izravno nad `_flow_template`, bez agenata: to je JEDINI mehanizam
    korelacije (nema ručnog registryja Future-a), pa je predložak i jedino mjesto
    gdje se izolacija može izgubiti.

    Ujedno dokumentira zašto novi put NIJE tražio proširenje routera: `refuse`
    prolazi jer predložak ne ograničava performativ, dok `attempt-result` ne
    prolazi — i zato do toka ne stiže ni `task_not_found` (v. ERRATA #70).
    """
    moj = "11111111-2222-3333-4444-555555555555"
    tudji = "99999999-2222-3333-4444-555555555555"
    tmpl = _flow_template(moj)

    def _poruka(perf: str, ont: str, cid: str) -> Message:
        m = Message(to="coordinator@localhost")
        m.set_metadata("performative", perf)
        m.set_metadata("ontology", ont)
        m.set_metadata("correlation_id", cid)
        m.body = "{}"
        return m

    assert tmpl.match(_poruka(Performative.REFUSE, Ontology.MODEL_UPDATED, moj)), (
        "novi put ne bi radio: refuse(model-updated) mora ući u SVOJ tok"
    )
    assert not tmpl.match(_poruka(Performative.REFUSE, Ontology.MODEL_UPDATED, tudji)), (
        "🔴 tuđi cid je ušao u tok — korelacijska izolacija je probijena"
    )
    assert tmpl.match(_poruka(Performative.INFORM, Ontology.MODEL_UPDATED, moj))
    assert not tmpl.match(_poruka(Performative.INFORM, Ontology.ATTEMPT_RESULT, moj)), (
        "attempt-result NE smije ulaziti u tok — na tome počiva izbor ontologije"
    )
