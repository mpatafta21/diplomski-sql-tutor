"""HTTP rute gatewaya (Faza 3E.3).

Tok /attempt: HTTP → bridge.register(cid,future) → gateway šalje submit-attempt
Coordinatoru → FSM → attempt-response natrag na gateway → bridge.resolve → HTTP.

/next-task: lakši put — gateway šalje recommend-next IZRAVNO Recommenderu (sender-based
reply već radi, 3C), bez punog FSM-a. Ne gradi se drugi FSM.

/profile: ČISTI DB read (users + skill_mastery + user_badges), bez agenata/bridgea —
kroz to_thread (sync SQLAlchemy ne smije blokirati event loop).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased

from agents.coordinator import (
    ERROR_COORDINATOR_BUSY,
    ERROR_EVALUATION_TIMEOUT,
    ONTOLOGY_SUBMIT_ATTEMPT,
)
from agents.evaluator_agent import _sandbox_conn_string
from agents.gamification_logic import (
    LEVEL_STEP,
    MASTERY_THRESHOLD,
    progress_to_next_level,
)
from agents.hint_agent import REASON_NOT_UNLOCKED
from agents.hint_logic import (
    CONSUMING_SOURCES,
    existing_request,
    hint_credit,
    primary_concept,
    unlocking_attempt,
)
from agents.messages import Ontology
from app.api.schemas import (
    AgentLogItem,
    AttemptItem,
    AttemptRequest,
    AttemptResponse,
    BadgeCatalogItem,
    HintCreditResetResponse,
    HintRequestBody,
    HintResponse,
    LeaderboardItem,
    MasteryHistoryPoint,
    MeResponse,
    ModuleNode,
    NextTaskResponse,
    Page,
    ProfileResponse,
    RegisterRequest,
    RunRequest,
    RunResponse,
    TaskDetailResponse,
    TokenResponse,
)
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)
from app.core import config
from app.db.models import (
    AgentMessageLog,
    Attempt,
    Badge,
    Concept,
    ConceptPrerequisite,
    HintRequest,
    Module,
    SkillMastery,
    SkillMasteryHistory,
    Task,
    TaskConcept,
    User,
    UserBadge,
    XpLog,
)
from app.db.session import SessionLocal
from scripts.lib.sandbox_runner import SandboxRunner

# Sidrenje tjednog prozora — ista zona kao streak logika (gamification_persistence._TZ).
_ZAGREB = ZoneInfo("Europe/Zagreb")
_LIMIT_MAX = 100
_LIMIT_DEFAULT = 20

_log = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth (Faza 4.0b) — /register, /login, /me. ADITIVNO: postojeće rute nedirnute.
# ---------------------------------------------------------------------------


def _create_student(username: str, email: str, password: str) -> int:
    """Sinkroni insert studenta. Vraća user_id. Baca HTTPException(409) na duplikat.

    role je UVIJEK 'student' — admin se ne registrira (seeda se).
    """
    with SessionLocal() as session:
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="student",
        )
        session.add(user)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            # username ILI email zauzet — razluči po tome što već postoji
            taken = session.scalar(
                select(User.username).where(User.username == username)
            )
            detail = "username_taken" if taken else "email_taken"
            raise HTTPException(status_code=409, detail=detail)
        return user.id


@router.post("/register", response_model=TokenResponse)
async def post_register(req: RegisterRequest) -> TokenResponse:
    user_id = await asyncio.to_thread(
        _create_student, req.username, str(req.email), req.password
    )
    token = create_access_token(str(user_id), "student")
    return TokenResponse(access_token=token)


def _authenticate(username: str, password: str) -> tuple[int, str] | None:
    """Sinkroni login check. Vraća (user_id, role) ili None (nema usera / kriva šifra)."""
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.username == username))
        if user is None or not verify_password(password, user.password_hash):
            return None
        return user.id, user.role


@router.post("/login", response_model=TokenResponse)
async def post_login(
    form: OAuth2PasswordRequestForm = Depends(),
) -> TokenResponse:
    result = await asyncio.to_thread(_authenticate, form.username, form.password)
    if result is None:
        # NE otkrivamo je li promašaj username ili password
        raise HTTPException(status_code=401, detail="invalid_credentials")
    user_id, role = result
    token = create_access_token(str(user_id), role)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
async def get_me(user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        # Faza 5.1: zastavica se čita iz konfiguracije poslužitelja, ne iz korisnika —
        # značajka je uključena za sve ili ni za koga.
        hints_enabled=config.USE_LLM_HINTS,
    )


# ---------------------------------------------------------------------------
# Mapiranje Coordinator payloada → AttemptResponse
# ---------------------------------------------------------------------------


def _to_attempt_response(result: dict) -> AttemptResponse:
    feedback = result.get("feedback") or {}
    gam = result.get("gamification") or {}
    rec = result.get("recommendation") or {}
    return AttemptResponse(
        feedback={
            "is_correct": feedback.get("is_correct"),
            "error_type": feedback.get("error_type"),
            "detail": feedback.get("detail"),
        },
        xp_delta=int(gam.get("xp_delta") or 0),
        xp=int(gam.get("xp") or 0),
        level=int(gam.get("level") or 1),
        current_streak=int(gam.get("current_streak") or 0),
        new_badges=list(gam.get("new_badges") or []),
        recommendation={
            "task_id": rec.get("task_id"),
            "concept": rec.get("concept"),
            "reason": rec.get("reason"),
        },
        already_solved=bool(gam.get("already_solved")),
    )


# ---------------------------------------------------------------------------
# POST /attempt — puni orkestrirani FSM tok
# ---------------------------------------------------------------------------


@router.post("/attempt", response_model=AttemptResponse)
async def post_attempt(
    req: AttemptRequest,
    request: Request,
    user: User = Depends(get_current_user),
) -> AttemptResponse:
    bridge = request.app.state.bridge
    gateway = request.app.state.gateway

    cid, _future = bridge.register()
    # user_id se ubrizgava iz TOKENA (AttemptRequest ga više nema) — klijent ga ne bira.
    gateway.send_fipa(
        to=config.AGENT_COORDINATOR_JID,
        ontology=ONTOLOGY_SUBMIT_ATTEMPT,
        payload={**req.model_dump(), "user_id": user.id},
        cid=cid,
    )

    try:
        result = await bridge.wait(cid, timeout=config.GATEWAY_TIMEOUT)
    except (asyncio.TimeoutError, TimeoutError):
        # Coordinator se uopće nije javio u zadanom prozoru.
        raise HTTPException(status_code=504, detail="orchestration_timeout")

    # Coordinatorov definiran timeout-odgovor (UPDATE timeout) → 504 sa strukturom.
    if isinstance(result, dict) and result.get("error") == ERROR_EVALUATION_TIMEOUT:
        raise HTTPException(status_code=504, detail=ERROR_EVALUATION_TIMEOUT)

    # 🔴 #62: granica istovremenih tokova. 503, a NE 504 — 504 znači „nismo stigli
    # odgovoriti", a ovdje smo odgovorili odmah i namjerno. Razlika je vidljiva
    # studentu: ponovni pokušaj ima smisla, i to odmah.
    if isinstance(result, dict) and result.get("error") == ERROR_COORDINATOR_BUSY:
        raise HTTPException(status_code=503, detail=ERROR_COORDINATOR_BUSY)

    return _to_attempt_response(result)


# ---------------------------------------------------------------------------
# GET /next-task — izravan recommend-next kroz bridge (bez FSM-a)
# ---------------------------------------------------------------------------


@router.get("/next-task", response_model=NextTaskResponse)
async def get_next_task(
    request: Request,
    user: User = Depends(get_current_user),
) -> NextTaskResponse:
    bridge = request.app.state.bridge
    gateway = request.app.state.gateway

    cid, _future = bridge.register()
    gateway.send_fipa(
        to=config.AGENT_RECOMMENDER_JID,
        ontology=Ontology.RECOMMEND_NEXT,
        payload={"user_id": user.id},
        cid=cid,
    )

    try:
        result = await bridge.wait(cid, timeout=config.GATEWAY_TIMEOUT)
    except (asyncio.TimeoutError, TimeoutError):
        raise HTTPException(status_code=504, detail="recommender_timeout")

    return NextTaskResponse(
        task_id=result.get("task_id"),
        concept=result.get("concept"),
        reason=result.get("reason"),
    )


# ---------------------------------------------------------------------------
# POST /hint — izravan request-hint kroz bridge (bez FSM-a, presedan /next-task)
# ---------------------------------------------------------------------------


def _hint_gate(user_id: int, task_id: int) -> dict:
    """Sinkrone provjere prije buđenja agenta. Vraća opis ishoda, ne diže iznimke.

    🔴 REDOSLIJED JE DIO UGOVORA:
      1. otključanost (409) — ruta ne vjeruje klijentu (C.3),
      2. idempotencija (200 iz pohrane) — PRIJE limita, jer ponovljeni klik na isti
         pokušaj ne troši kredit (C.2) i mora raditi i s praznim bucketom,
      3. limit (429).

    Zamijeniti 2 i 3 značilo bi da student s potrošenim limitom ne može ponovno
    vidjeti hint koji je već platio.
    """
    with SessionLocal() as session:
        attempt = unlocking_attempt(session, user_id, task_id)
        if attempt is None:
            return {"gate": "not_unlocked"}

        prior = existing_request(session, attempt.id)
        if prior is not None:
            remaining, refill = hint_credit(session, user_id)
            _, concept_code = primary_concept(session, task_id)
            return {
                "gate": "replay",
                "hint_text": prior.hint_text,
                "source": prior.source,
                "concept": concept_code,
                "remaining": remaining,
                "next_refill_at": refill,
            }

        remaining, refill = hint_credit(session, user_id)
        if remaining <= 0:
            return {"gate": "rate_limited", "next_refill_at": refill}
        return {"gate": "ok"}


def _hint_credit_now(user_id: int) -> tuple[int, datetime | None]:
    with SessionLocal() as session:
        return hint_credit(session, user_id)


@router.post("/hint", response_model=HintResponse)
async def post_hint(
    req: HintRequestBody,
    request: Request,
    user: User = Depends(get_current_user),
) -> HintResponse:
    """Vrati hint za zadnji netočan pokušaj na zadatku.

    🔴 NE IDE KROZ COORDINATOROV FSM (§B.4.4): FSM je globalno serijaliziran, a LLM
    poziv traje sekunde — kroz njega bi jedan hint gurnuo tuđi `POST /attempt` u 504.
    Put je gateway → HintAgent → gateway, po presedanu `/next-task`.
    """
    # 1) Prekidač — prije svega ostalog, i BEZ ijednog odlaznog poziva.
    if not config.USE_LLM_HINTS:
        raise HTTPException(status_code=503, detail="hints_disabled")

    gate = await asyncio.to_thread(_hint_gate, user.id, req.task_id)

    # 2) Otključanost.
    if gate["gate"] == "not_unlocked":
        raise HTTPException(status_code=409, detail="hint_not_unlocked")

    # 3) Idempotencija — pohranjeni tekst, bez LLM poziva i bez novog retka (C.2).
    if gate["gate"] == "replay":
        return HintResponse(
            hint_text=gate["hint_text"],
            source=gate["source"],
            concept=gate["concept"],
            remaining=gate["remaining"],
            next_refill_at=gate["next_refill_at"],
        )

    # 4) Limit.
    if gate["gate"] == "rate_limited":
        raise HTTPException(status_code=429, detail="hint_rate_limited")

    # 5) Agent: LLM → katalog → ništa.
    bridge = request.app.state.bridge
    gateway = request.app.state.gateway
    cid, _future = bridge.register()
    gateway.send_fipa(
        to=config.AGENT_HINT_JID,
        ontology=Ontology.REQUEST_HINT,
        payload={"user_id": user.id, "task_id": req.task_id},
        cid=cid,
    )

    try:
        result = await bridge.wait(cid, timeout=config.HINT_TIMEOUT)
    except (asyncio.TimeoutError, TimeoutError):
        # 🔴 Agent je možda ipak potrošio poziv — njegov `hint_requests` redak to
        # bilježi neovisno o ovom timeoutu (v. `produce_hint`).
        raise HTTPException(status_code=504, detail="hint_timeout")

    if result.get("error") == REASON_NOT_UNLOCKED:
        # Student je riješio zadatak između provjere i agentovog čitanja.
        raise HTTPException(status_code=409, detail="hint_not_unlocked")
    if "hint_text" not in result:
        raise HTTPException(status_code=503, detail="hint_unavailable")

    remaining, refill = await asyncio.to_thread(_hint_credit_now, user.id)
    return HintResponse(
        hint_text=result["hint_text"],
        source=result["source"],
        concept=result.get("concept"),
        remaining=remaining,
        next_refill_at=refill,
    )


# ---------------------------------------------------------------------------
# POST /admin/hint-credit/reset — admin vraća SVOJ kredit za savjete
# ---------------------------------------------------------------------------


def _reset_hint_credit(user_id: int) -> dict:
    """Obriši retke koji troše kredit ovog korisnika i vrati novo stanje."""
    with SessionLocal() as session:
        deleted = session.execute(
            delete(HintRequest).where(
                HintRequest.user_id == user_id,
                HintRequest.source.in_(CONSUMING_SOURCES),
            )
        ).rowcount
        session.commit()
        remaining, refill = (
            hint_credit(session, user_id) if config.USE_LLM_HINTS else (None, None)
        )
        return {
            "remaining": remaining,
            "next_refill_at": refill,
            "deleted": int(deleted or 0),
        }


@router.post("/admin/hint-credit/reset", response_model=HintCreditResetResponse)
async def post_reset_hint_credit(
    admin: User = Depends(require_admin),
) -> HintCreditResetResponse:
    """Vrati adminov kredit za savjete na puno stanje.

    🔴 BRIŠE SAMO RETKE POZIVATELJA i NE PRIMA `user_id`. Adminovi
    `hint_requests` redci nisu telemetrija — admin je po dizajnu izvan analize
    (`/leaderboard` ga izrijekom isključuje). Studentovi jesu: oni su jedini
    izvor o potrošnji savjeta i rupama u katalogu, pa ih ova ruta ne može
    dohvatiti ni greškom. Parametar za ciljanog korisnika NIJE propust nego
    izostavljen namjerno — s njim bi jedna kriva vrijednost obrisala
    evaluacijske podatke sudionika.

    🔴 Briše se samo ono što TROŠI kredit (`CONSUMING_SOURCES`).
    `source='unavailable'` ostaje: taj redak ne troši ništa, a mjeri rupu u
    katalogu hintova.

    🔴 Ovo je RESET, ne izuzeće. Admin i dalje ima limit, pa mu stanje
    `hint_rate_limited` ostaje dosežno — a ono je jedno od sedam stanja koja
    rad dokumentira i demonstrira se upravo na adminu.
    """
    data = await asyncio.to_thread(_reset_hint_credit, admin.id)
    return HintCreditResetResponse(**data)



# ---------------------------------------------------------------------------
# GET /profile — čisti DB read (bez agenata)
# ---------------------------------------------------------------------------


def _read_profile(user_id: int) -> dict | None:
    """Sinkroni DB read profila — pozvan kroz to_thread."""
    with SessionLocal() as session:
        user = session.get(User, user_id)
        if user is None:
            return None

        mastery_rows = session.execute(
            select(Concept.code, SkillMastery.p_l)
            .join(SkillMastery, SkillMastery.concept_id == Concept.id)
            .where(SkillMastery.user_id == user_id)
            .order_by(Concept.code)
        ).all()

        badge_rows = session.execute(
            select(Badge.code)
            .join(UserBadge, UserBadge.badge_id == Badge.id)
            .where(UserBadge.user_id == user_id)
            .order_by(Badge.code)
        ).scalars()

        # level ostaje user.level (postojeće ponašanje); progres se izvodi iz XP-a
        # postojećom formulom — NE reimplementira se.
        _level, xp_in_level, xp_to_next = progress_to_next_level(user.xp)

        # Faza 5.2 (C.3.2): kredit za hintove živi ovdje jer je stanje PO KORISNIKU
        # koje se mijenja u vremenu — isti rod kao xp/level/streak — a `/profile` je
        # već u cacheu na Task ekranu (nula dodatnih poziva).
        # 🔴 Ista funkcija koju zove `POST /hint`, ne kopija formule (N-8 mehanizam).
        # 🔴 Flag isključen → oba polja `None`: brojač bez značajke je besmislen, a
        # `0` bi se čitalo kao „potrošeno" (stanje iz kojeg se izlazi čekanjem).
        hint_remaining, hint_refill = (
            hint_credit(session, user_id) if config.USE_LLM_HINTS else (None, None)
        )

        return {
            "xp": user.xp,
            "level": user.level,
            "xp_in_level": xp_in_level,
            "xp_to_next": xp_to_next,
            "level_step": LEVEL_STEP,
            "mastery_threshold": MASTERY_THRESHOLD,
            "current_streak": user.current_streak,
            "longest_streak": user.longest_streak,
            "mastery": [{"concept": code, "p_l": p_l} for code, p_l in mastery_rows],
            "badges": list(badge_rows),
            "remaining": hint_remaining,
            "next_refill_at": hint_refill,
        }


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    user: User = Depends(get_current_user),
) -> ProfileResponse:
    data = await asyncio.to_thread(_read_profile, user.id)
    if data is None:
        raise HTTPException(status_code=404, detail="user_not_found")
    return ProfileResponse(**data)


# ---------------------------------------------------------------------------
# GET /task/{task_id} — detalj zadatka (BEZ rješenja) — čisti DB read
# ---------------------------------------------------------------------------


def _read_task_detail(task_id: int, user_id: int) -> dict | None:
    """Sinkroni DB read detalja zadatka — pozvan kroz to_thread.

    NAMJERNO gradi dict eksplicitno po poljima: expected_query / expected_result /
    sandbox_schema se NIKAD ne uključuju (rješenje se ne izlaže).

    `solved` = ima li `user_id` barem jedan točan pokušaj ovog taska (indikator
    „Riješeno" + da ponovni Submit ne nosi XP). Izvedeno iz `attempts`.

    🔴 NEAKTIVAN task = 404, isto kao nepostojeći (NALAZ #19 dopuna, Faza 4.4-0f).
    Bez ovoga je izravan URL `/task/{id}` bio ZADNJI put do neevaluabilnog
    zadatka: recommender ga više ne nudi (Kat. C maska), ali student je mogao
    otvoriti M6 task ručno, predati rješenje i dobiti `unsupported_eval` —
    0 XP + BKT kaznu koja curi i na evaluabilne sekundarne koncepte.
    Oblik odgovora se NE mijenja (schemas.py nedirnut) — samo se neaktivan
    zadatak tretira kao nepostojeći.
    """
    with SessionLocal() as session:
        task = session.get(Task, task_id)
        if task is None or not task.is_active:
            return None

        concept_rows = session.execute(
            select(Concept.code, Concept.name, TaskConcept.is_primary)
            .join(TaskConcept, TaskConcept.concept_id == Concept.id)
            .where(TaskConcept.task_id == task_id)
            .order_by(TaskConcept.is_primary.desc(), Concept.code)
        ).all()

        solved = (
            session.scalar(
                select(Attempt.id)
                .where(
                    Attempt.user_id == user_id,
                    Attempt.task_id == task_id,
                    Attempt.is_correct.is_(True),
                )
                .limit(1)
            )
            is not None
        )

        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "difficulty": task.difficulty,
            "estimated_time_sec": task.estimated_time_sec,
            "module_id": task.module_id,
            "concepts": [
                {"code": code, "name": name, "is_primary": is_primary}
                for code, name, is_primary in concept_rows
            ],
            "solved": solved,
            # Faza 5.1: iz čega UI zna je li hint otključan. Ista funkcija koju
            # `POST /hint` koristi za provjeru — jedan izvor istine, ne dva pravila.
            "last_attempt_error_type": (
                a.error_type if (a := unlocking_attempt(session, user_id, task_id)) else None
            ),
        }


@router.get("/task/{task_id}", response_model=TaskDetailResponse)
async def get_task_detail(
    task_id: int = Path(...),
    user: User = Depends(get_current_user),
) -> TaskDetailResponse:
    data = await asyncio.to_thread(_read_task_detail, task_id, user.id)
    if data is None:
        raise HTTPException(status_code=404, detail="task_not_found")
    return TaskDetailResponse(**data)


# ---------------------------------------------------------------------------
# GET /modules — svi moduli + koncepti + prereq graf (po code-u) — čisti DB read
# ---------------------------------------------------------------------------


def _read_modules() -> list[dict]:
    """Sinkroni DB read svih modula s konceptima i preduvjetima.

    Prereq mapa i grupiranje po modulu grade se u Pythonu (bez N+1 upita):
    tri seta rows → modules, concepts (order_index), prereq bridovi (concept_id → code).
    """
    with SessionLocal() as session:
        modules = (
            session.execute(select(Module).order_by(Module.order_index)).scalars().all()
        )
        concepts = (
            session.execute(select(Concept).order_by(Concept.order_index))
            .scalars()
            .all()
        )

        prereq_concept = aliased(Concept)
        edge_rows = session.execute(
            select(ConceptPrerequisite.concept_id, prereq_concept.code).join(
                prereq_concept, prereq_concept.id == ConceptPrerequisite.prerequisite_id
            )
        ).all()

        # primary_task_count (Faza 4.3 Stage 0, NALAZ #10): ISTA semantika kao
        # recommender_logic._concept_task_stats (uvjeti u ON-klauzuli da koncepti
        # bez taskova daju 0) — helper je privatan pa se JOIN zrcali, ne importa.
        count_rows = session.execute(
            select(Concept.id, func.count(Task.id))
            .select_from(Concept)
            .outerjoin(
                TaskConcept,
                (TaskConcept.concept_id == Concept.id)
                & (TaskConcept.is_primary.is_(True)),
            )
            .outerjoin(
                Task,
                (Task.id == TaskConcept.task_id) & (Task.is_active.is_(True)),
            )
            .group_by(Concept.id)
        ).all()
        primary_counts: dict[int, int] = dict(count_rows)

        # entry_task_id (self-test fix 4.6-eval): reprezentativan ZADATAK za klik
        # na koncept u Module overviewu. STATIČKI (bez user-konteksta → /modules
        # ostaje čist katalog, cacheable): AKTIVAN PRIMARY zadatak, najlakši prvi
        # (difficulty ↑, pa id ↑ radi determinizma). Ista maska (is_primary +
        # is_active) kao primary_task_count → entry postoji točno kad je count>0.
        entry_rows = session.execute(
            select(TaskConcept.concept_id, Task.id)
            .join(Task, Task.id == TaskConcept.task_id)
            .where(TaskConcept.is_primary.is_(True), Task.is_active.is_(True))
            .order_by(TaskConcept.concept_id, Task.difficulty, Task.id)
        ).all()
        entry_task_by_concept: dict[int, int] = {}
        for concept_id, task_id in entry_rows:
            entry_task_by_concept.setdefault(concept_id, task_id)

    prereqs_by_concept: dict[int, list[str]] = {}
    for concept_id, prereq_code in edge_rows:
        prereqs_by_concept.setdefault(concept_id, []).append(prereq_code)
    for codes in prereqs_by_concept.values():
        codes.sort()

    concepts_by_module: dict[int, list[dict]] = {}
    for c in concepts:
        concepts_by_module.setdefault(c.module_id, []).append(
            {
                "id": c.id,
                "code": c.code,
                "name": c.name,
                "tier": c.tier,
                "order_index": c.order_index,
                "prerequisites": prereqs_by_concept.get(c.id, []),
                "primary_task_count": primary_counts.get(c.id, 0),
                "entry_task_id": entry_task_by_concept.get(c.id),
            }
        )

    return [
        {
            "id": m.id,
            "number": m.number,
            "name": m.name,
            "description": m.description,
            "difficulty": m.difficulty,
            "order_index": m.order_index,
            "concepts": concepts_by_module.get(m.id, []),
        }
        for m in modules
    ]


@router.get("/modules", response_model=list[ModuleNode])
async def get_modules(
    _user: User = Depends(get_current_user),
) -> list[ModuleNode]:
    data = await asyncio.to_thread(_read_modules)
    return [ModuleNode(**m) for m in data]


# ---------------------------------------------------------------------------
# GET /badges — katalog bedževa (bez `rule`) — čisti DB read
# ---------------------------------------------------------------------------


def _read_badges() -> list[dict]:
    """Sinkroni DB read kataloga bedževa. `rule` (Prolog kriterij) se NE dohvaća."""
    with SessionLocal() as session:
        rows = session.execute(
            select(
                Badge.code,
                Badge.name,
                Badge.description,
                Badge.icon,
                Badge.xp_reward,
            ).order_by(Badge.code)
        ).all()

    return [
        {
            "code": code,
            "name": name,
            "description": description,
            "icon": icon,
            "xp_reward": xp_reward,
        }
        for code, name, description, icon, xp_reward in rows
    ]


@router.get("/badges", response_model=list[BadgeCatalogItem])
async def get_badges(
    _user: User = Depends(get_current_user),
) -> list[BadgeCatalogItem]:
    data = await asyncio.to_thread(_read_badges)
    return [BadgeCatalogItem(**b) for b in data]


# ---------------------------------------------------------------------------
# Paginacijski helper
# ---------------------------------------------------------------------------


def _clamp_page(limit: int, offset: int) -> tuple[int, int]:
    """limit → [1, _LIMIT_MAX]; offset → >= 0. Clamp, ne odbijanje (nema 422)."""
    return max(1, min(limit, _LIMIT_MAX)), max(0, offset)


# ---------------------------------------------------------------------------
# GET /attempts — povijest pokušaja usera (paginirano) — čisti DB read
# ---------------------------------------------------------------------------


def _read_attempts(user_id: int, limit: int, offset: int) -> dict:
    """Sinkroni DB read povijesti pokušaja usera (iz tokena, pa je zajamčeno postojeći).

    task_title kroz JEDAN join attempts→tasks (bez N+1). total je COUNT neovisan
    o limit/offset. Redoslijed created_at DESC, id DESC (deterministički tie-break).
    Nepostojeći/prazan user → items=[] total=0 (bez 404 — user dolazi iz tokena).
    """
    with SessionLocal() as session:
        total = session.scalar(
            select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id)
        )

        rows = session.execute(
            select(
                Attempt.id,
                Attempt.task_id,
                Task.title,
                Attempt.submitted_query,
                Attempt.is_correct,
                Attempt.error_type,
                Attempt.detail,
                Attempt.execution_time_ms,
                Attempt.rows_returned,
                Attempt.xp_awarded,
                Attempt.hint_requested,
                Attempt.attempt_number,
                Attempt.created_at,
            )
            .join(Task, Task.id == Attempt.task_id)
            .where(Attempt.user_id == user_id)
            .order_by(Attempt.created_at.desc(), Attempt.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()

        items = [
            {
                "id": r.id,
                "task_id": r.task_id,
                "task_title": r.title,
                "submitted_query": r.submitted_query,
                "is_correct": r.is_correct,
                "error_type": r.error_type,
                "detail": r.detail,
                "execution_time_ms": r.execution_time_ms,
                "rows_returned": r.rows_returned,
                "xp_awarded": r.xp_awarded,
                "hint_requested": r.hint_requested,
                "attempt_number": r.attempt_number,
                "created_at": r.created_at,
            }
            for r in rows
        ]
        return {"items": items, "total": int(total or 0)}


@router.get("/attempts", response_model=Page[AttemptItem])
async def get_attempts(
    user: User = Depends(get_current_user),
    limit: int = Query(_LIMIT_DEFAULT),
    offset: int = Query(0),
) -> Page[AttemptItem]:
    limit, offset = _clamp_page(limit, offset)
    data = await asyncio.to_thread(_read_attempts, user.id, limit, offset)
    return Page[AttemptItem](
        items=[AttemptItem(**i) for i in data["items"]],
        total=data["total"],
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# GET /leaderboard — global (User.xp) | weekly (SUM delta, 7-dnevni prozor) — DB read
# ---------------------------------------------------------------------------


def _read_leaderboard_global(limit: int, offset: int) -> dict:
    """Global ljestvica — SAMO studenti (admin nije natjecatelj). count i rows dijele
    isti `role == 'student'` filter da total odgovara prikazanom skupu."""
    with SessionLocal() as session:
        total = session.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == "student")
        )
        rows = session.execute(
            select(User.username, User.xp, User.level)
            .where(User.role == "student")
            .order_by(User.xp.desc(), User.id.asc())
            .limit(limit)
            .offset(offset)
        ).all()
    items = [
        {
            "rank": offset + i + 1,
            "username": r.username,
            "xp": r.xp,
            "level": r.level,
        }
        for i, r in enumerate(rows)
    ]
    return {"items": items, "total": int(total or 0)}


def _read_leaderboard_weekly(limit: int, offset: int) -> dict:
    """Score = SUM(xp_log.delta) u zadnjih 7 dana; cutoff TZ-aware (Europe/Zagreb).

    Useri bez ijednog xp_log reda u prozoru se NE prikazuju. level = trenutni User.level.
    """
    cutoff = datetime.now(_ZAGREB) - timedelta(days=7)
    score = func.sum(XpLog.delta).label("score")
    with SessionLocal() as session:
        # count MORA joinati User da bi role filter radio → count i rows broje ISTI skup
        # (distinct studenti s xp_log redom u prozoru).
        total = session.scalar(
            select(func.count(func.distinct(XpLog.user_id)))
            .join(User, User.id == XpLog.user_id)
            .where(XpLog.created_at >= cutoff, User.role == "student")
        )
        rows = session.execute(
            select(User.username, score, User.level)
            .join(XpLog, XpLog.user_id == User.id)
            .where(XpLog.created_at >= cutoff, User.role == "student")
            .group_by(User.id, User.username, User.level)
            .order_by(score.desc(), User.id.asc())
            .limit(limit)
            .offset(offset)
        ).all()
    items = [
        {
            "rank": offset + i + 1,
            "username": r.username,
            "xp": int(r.score),
            "level": r.level,
        }
        for i, r in enumerate(rows)
    ]
    return {"items": items, "total": int(total or 0)}


@router.get("/leaderboard", response_model=Page[LeaderboardItem])
async def get_leaderboard(
    scope: Literal["global", "weekly"] = Query("global"),
    limit: int = Query(_LIMIT_DEFAULT),
    offset: int = Query(0),
    _user: User = Depends(get_current_user),
) -> Page[LeaderboardItem]:
    limit, offset = _clamp_page(limit, offset)
    reader = _read_leaderboard_weekly if scope == "weekly" else _read_leaderboard_global
    data = await asyncio.to_thread(reader, limit, offset)
    return Page[LeaderboardItem](
        items=[LeaderboardItem(**i) for i in data["items"]],
        total=data["total"],
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# GET /mastery-history — BKT krivulja usera (kronološki) — čisti DB read
# ---------------------------------------------------------------------------


def _read_mastery_history(user_id: int, concept: str | None) -> list[dict]:
    """Sinkroni DB read povijesti masteryja usera (iz tokena, zajamčeno postojeći).

    Join skill_mastery_history→concepts za code. Opcionalni filtar po Concept.code.
    ORDER BY created_at ASC (kronološki — za krivulju). Prazan user → [] (bez 404).
    """
    with SessionLocal() as session:
        stmt = (
            select(
                Concept.code,
                SkillMasteryHistory.p_l,
                SkillMasteryHistory.attempt_id,
                SkillMasteryHistory.created_at,
            )
            .join(Concept, Concept.id == SkillMasteryHistory.concept_id)
            .where(SkillMasteryHistory.user_id == user_id)
        )
        if concept is not None:
            stmt = stmt.where(Concept.code == concept)
        stmt = stmt.order_by(
            SkillMasteryHistory.created_at.asc(), SkillMasteryHistory.id.asc()
        )

        rows = session.execute(stmt).all()
        return [
            {
                "concept": code,
                "p_l": p_l,
                "attempt_id": attempt_id,
                "created_at": created_at,
            }
            for code, p_l, attempt_id, created_at in rows
        ]


@router.get("/mastery-history", response_model=list[MasteryHistoryPoint])
async def get_mastery_history(
    user: User = Depends(get_current_user),
    concept: str | None = Query(None),
) -> list[MasteryHistoryPoint]:
    data = await asyncio.to_thread(_read_mastery_history, user.id, concept)
    return [MasteryHistoryPoint(**p) for p in data]


# ---------------------------------------------------------------------------
# POST /run — čisti sandbox exec (reuse SandboxRunner, NIŠTA se ne perzistira)
# ---------------------------------------------------------------------------


def _run_query(query: str) -> RunResponse:
    """Sinkroni sandbox exec — pozvan kroz to_thread (SandboxRunner otvara psycopg konekciju).

    dml=False je HARDKODIRAN: endpoint NIKAD ne smije pokrenuti DML/DDL. readonly rola
    je druga linija obrane. SQL/timeout greška vraća se u `error` polju (success=False),
    NE kao HTTP greška — to je normalan "krivi upit" ishod.
    """
    runner = SandboxRunner(_sandbox_conn_string())
    result = runner.execute(query=query, schema="ecommerce_v1", dml=False)
    return RunResponse(
        columns=result.column_names,
        rows=result.rows,
        exec_ms=result.execution_time_ms,
        error=result.error,
    )


@router.post("/run", response_model=RunResponse)
async def post_run(
    req: RunRequest,
    _user: User = Depends(get_current_user),
) -> RunResponse:
    # task_id je samo kontekst — ne mijenja izvršavanje.
    return await asyncio.to_thread(_run_query, req.query)


# ---------------------------------------------------------------------------
# GET /admin/agent-logs — FIPA-ACL log (paginirano) — admin-only DB read
# ---------------------------------------------------------------------------

_AGENT_LOGS_LIMIT_MAX = 200
_AGENT_LOGS_LIMIT_DEFAULT = 50


def _read_agent_logs(
    correlation_id: uuid.UUID | None,
    sender: str | None,
    limit: int,
    offset: int,
) -> dict:
    with SessionLocal() as session:
        filters = []
        if correlation_id is not None:
            filters.append(AgentMessageLog.correlation_id == correlation_id)
        if sender is not None:
            filters.append(AgentMessageLog.sender == sender)

        total = session.scalar(
            select(func.count()).select_from(AgentMessageLog).where(*filters)
        )

        rows = session.execute(
            select(
                AgentMessageLog.id,
                AgentMessageLog.sender,
                AgentMessageLog.receiver,
                AgentMessageLog.performative,
                AgentMessageLog.content,
                AgentMessageLog.correlation_id,
                AgentMessageLog.created_at,
            )
            .where(*filters)
            .order_by(AgentMessageLog.created_at.desc(), AgentMessageLog.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()

    items = [
        {
            "id": r.id,
            "sender": r.sender,
            "receiver": r.receiver,
            "performative": r.performative,
            "content": r.content,
            "correlation_id": str(r.correlation_id) if r.correlation_id else None,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return {"items": items, "total": int(total or 0)}


@router.get("/admin/agent-logs", response_model=Page[AgentLogItem])
async def get_agent_logs(
    correlation_id: uuid.UUID | None = Query(None),
    sender: str | None = Query(None),
    limit: int = Query(_AGENT_LOGS_LIMIT_DEFAULT),
    offset: int = Query(0),
    _admin: User = Depends(require_admin),
) -> Page[AgentLogItem]:
    limit = max(1, min(limit, _AGENT_LOGS_LIMIT_MAX))
    offset = max(0, offset)
    data = await asyncio.to_thread(
        _read_agent_logs, correlation_id, sender, limit, offset
    )
    return Page[AgentLogItem](
        items=[AgentLogItem(**i) for i in data["items"]],
        total=data["total"],
        limit=limit,
        offset=offset,
    )
