"""Pydantic v2 request/response sheme za HTTP gateway.

Auth (Faza 4.0b): zaštićene rute deriviraju user_id iz JWT tokena
(get_current_user), NE iz body/query — klijent ga više ne bira. AttemptRequest
zato više ne nosi user_id.
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, EmailStr


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class AttemptRequest(BaseModel):
    # user_id NAMJERNO uklonjen (Faza 4.0b.2) — derivira se iz JWT tokena, klijent ga ne bira.
    task_id: int
    submitted_query: str


# ---------------------------------------------------------------------------
# Auth (Faza 4.0b) — /register, /login, /me
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    #: Faza 5.1 (§B.4.3): je li značajka hintova uopće uključena na ovom poslužitelju.
    #: 🔴 Stoji na `/me`, a ne se otkriva tek klikom, jer stanje `unavailable` traži
    #: da se gumb TIHO SAKRIJE. Da se saznaje s rute, student bi vidio gumb → kliknuo
    #: → dobio grešku, što je suprotno od „tiho sakrij". `/me` se dohvaća pri prijavi,
    #: dakle prije prvog rendera Task ekrana.
    hints_enabled: bool = False


# ---------------------------------------------------------------------------
# Zajedničke pod-sheme
# ---------------------------------------------------------------------------


class FeedbackModel(BaseModel):
    """`detail` (Faza 4.3 Stage 0b) = EvaluationOutcome.detail, persistiran u
    attempts.detail — pedagoški opis greške (imena stupaca / broj redova / PG
    poruka studentovog upita). NIKAD expected_query ni sadržaj očekivanih
    redaka. NULL za correct."""

    is_correct: bool | None = None
    error_type: str | None = None
    detail: str | None = None


class RecommendationModel(BaseModel):
    task_id: int | None = None
    concept: str | None = None
    reason: str | None = None


class MasteryItem(BaseModel):
    concept: str
    p_l: float


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class AttemptResponse(BaseModel):
    feedback: FeedbackModel
    xp_delta: int
    xp: int
    level: int
    current_streak: int
    new_badges: list[str]
    recommendation: RecommendationModel
    #: True ako je task bio VEĆ točno riješen prije ovog pokušaja → attempt-XP se
    #: NE dodjeljuje (first-solve gate). UI prikazuje „već riješeno, bez XP-a".
    already_solved: bool = False


class NextTaskResponse(BaseModel):
    task_id: int | None = None
    concept: str | None = None
    reason: str | None = None


class TaskForConceptResponse(BaseModel):
    """Odgovor `GET /task-for-concept/{code}` — zadatak koncepta za OVOG korisnika.

    Za razliku od `entry_task_id` u `/modules`, koji je statičan katalog bez
    korisničkog konteksta, ovdje se riješeni zadaci preskaču.
    """

    task_id: int
    concept: str
    repeat: bool = False


class HintRequestBody(BaseModel):
    """Tijelo `POST /hint` — SAMO `task_id`.

    🔴 `submitted_query` NAMJERNO NIJE ovdje. Varijanta A (slanje upita LLM-u) je
    odbijena u 5.0; pod selektivnim B+ studentov upit ne napušta sustav, pa ga ruta
    ne smije ni primiti — polje koje ne postoji ne može se slučajno proslijediti.
    `user_id` se izvodi iz tokena (obrazac `AttemptRequest`, Faza 4.0b.2).
    """

    task_id: int


class HintResponse(BaseModel):
    """Odgovor na `POST /hint`.

    🔴 `remaining`/`next_refill_at` postoje da prazan bucket ne bude neobjašnjen
    (C.4). Brojač NIKAD ne ide u natpis gumba (§G7.2) — to je uputa za UI, ovdje se
    samo isporučuje podatak.

    🔴 Broj traženih hintova NIJE mjera potražnje (C.5): odozgo je ograničen
    dizajnom (5 / 4 h). Ta rečenica mora stajati svugdje gdje se brojka spominje.
    """

    hint_text: str
    #: 'llm' (model) ili 'fallback' (katalog `hints`). Ista riječ kao u
    #: `hint_requests.source` — v. §B.4.2 odstupanje u wrapupu 5.1.
    source: str
    concept: str | None = None
    remaining: int | None = None
    next_refill_at: datetime | None = None


class HintCreditResetResponse(BaseModel):
    """Odgovor na `POST /admin/hint-credit/reset` (Faza 5.2).

    🔴 `remaining` i `next_refill_at` dolaze iz `hint_logic.hint_credit`, iste
    funkcije koju zovu `/hint` i `/profile` — ne iz pretpostavke „nakon brisanja
    je puno". Da se računa ovdje, imali bismo treću implementaciju istog pravila
    (mehanizam N-8).
    """

    remaining: int | None = None
    next_refill_at: datetime | None = None
    #: Koliko je redaka obrisano — akcija koja briše mora reći KOLIKO je obrisala.
    deleted: int


class ProfileResponse(BaseModel):
    """Polja level-progresa i konstante (Faza 4.2) su tu da ih frontend NE
    hardkodira — izvor: gamification_logic (progress_to_next_level, LEVEL_STEP,
    MASTERY_THRESHOLD = mirror rules.pl mastery_threshold)."""

    xp: int
    level: int
    xp_in_level: int
    xp_to_next: int
    level_step: int
    mastery_threshold: float
    current_streak: int
    longest_streak: int
    mastery: list[MasteryItem]
    badges: list[str]

    # ── Kredit za hintove (Faza 5.2, C.3.2) ────────────────────────────────
    #: Preostali hintovi. 🔴 `None` = značajka je isključena (`USE_LLM_HINTS=false`),
    #: NIJE isto što i `0` (bucket potrošen, puni se čekanjem). Isti izvor kao
    #: `HintResponse.remaining` — `hint_logic.hint_credit`, ne druga formula.
    remaining: int | None = None
    #: Trenutak u kojem `remaining` poraste za 1; `None` kad je bucket pun ILI
    #: kad je značajka isključena. Razliku nosi `remaining`.
    next_refill_at: datetime | None = None


# ---------------------------------------------------------------------------
# Statički read endpointi (Faza 4.0a-1) — /task/{id}, /modules, /badges
# ---------------------------------------------------------------------------


class ConceptRef(BaseModel):
    code: str
    name: str
    is_primary: bool


class TaskDetailResponse(BaseModel):
    """Detalj zadatka za studenta. NAMJERNO bez expected_query / expected_result /
    sandbox_schema — rješenje se NE izlaže kroz ovaj endpoint."""

    id: int
    title: str
    description: str
    difficulty: int
    estimated_time_sec: int | None
    module_id: int
    concepts: list[ConceptRef]
    #: True ako je trenutni korisnik već točno riješio ovaj task (bilo koji raniji
    #: is_correct pokušaj). UI prikazuje „Riješeno" + da ponovni Submit ne nosi XP.
    solved: bool = False
    #: Faza 5.1: `error_type` ZADNJEG pokušaja na ovom zadatku, ili None ako pokušaja
    #: nema ili je zadnji bio točan. Iz njega UI zna je li hint otključan — ista
    #: istina koju ruta `/hint` provjerava, samo unaprijed.
    #: 🔴 Ovo je NAGOVJEŠTAJ, ne ovlaštenje (C.3): između čitanja i klika student može
    #: predati točan upit, pa `/hint` istu provjeru radi ponovno i vraća 409.
    last_attempt_error_type: str | None = None


class ConceptNode(BaseModel):
    """`primary_task_count` (Faza 4.3 Stage 0, NALAZ #10) = broj AKTIVNIH PRIMARY
    taskova koncepta — ista semantika kao recommender_logic._concept_task_stats.
    UI iz njega zrcali Recommenderove kategorije (0 = glue · <2 = subfloor · >=2)."""

    id: int
    code: str
    name: str
    tier: str
    order_index: int
    prerequisites: list[str]
    primary_task_count: int
    #: Reprezentativan AKTIVAN primary zadatak koncepta (najlakši prvi) — meta za
    #: klik na koncept u Module overviewu → `/task/<id>`. None ⟺ koncept nema
    #: vlastitih aktivnih primary zadataka (glue/izvan opsega) → UI ne nudi klik.
    entry_task_id: int | None = None


class ModuleNode(BaseModel):
    id: int
    number: int
    name: str
    description: str | None
    difficulty: str
    order_index: int
    concepts: list[ConceptNode]


class BadgeCatalogItem(BaseModel):
    """Katalog bedževa — bez `rule` (Prolog kriterij se ne izlaže klijentu)."""

    code: str
    name: str
    description: str | None
    icon: str | None
    xp_reward: int


# ---------------------------------------------------------------------------
# Paginacijski envelope (Faza 4.0a-2) — generički, reusan (/attempts, /leaderboard, …)
# ---------------------------------------------------------------------------


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# User read endpointi (Faza 4.0a-2) — /attempts, /leaderboard
# ---------------------------------------------------------------------------


class AttemptItem(BaseModel):
    id: int
    task_id: int
    task_title: str
    submitted_query: str
    is_correct: bool
    error_type: str | None
    detail: str | None
    execution_time_ms: int | None
    rows_returned: int | None
    xp_awarded: int
    hint_requested: bool
    attempt_number: int
    created_at: datetime


class LeaderboardItem(BaseModel):
    """`xp` je score za dani scope (global = User.xp, weekly = SUM(delta) u prozoru).
    `level` je uvijek trenutni User.level."""

    rank: int
    username: str
    xp: int
    level: int


class MasteryHistoryPoint(BaseModel):
    """Jedna točka BKT krivulje (snapshot p_l pri updateu)."""

    concept: str
    p_l: float
    attempt_id: int | None
    created_at: datetime


# ---------------------------------------------------------------------------
# POST /run — čisti sandbox exec (Faza 4.0a-4)
# ---------------------------------------------------------------------------


class RunRequest(BaseModel):
    task_id: int | None = None  # opcionalni kontekst; NE mijenja izvršavanje
    query: str


class RunResponse(BaseModel):
    columns: list[str]
    rows: list[dict]
    exec_ms: int
    error: str | None = None  # None == uspjeh; inače SQL/timeout poruka (nije HTTP greška)


# ---------------------------------------------------------------------------
# GET /admin/agent-logs — FIPA-ACL log (Faza 4.0a-4)
# ---------------------------------------------------------------------------


class AgentLogItem(BaseModel):
    id: int
    sender: str
    receiver: str
    performative: str
    content: dict | None
    correlation_id: str | None
    created_at: datetime
