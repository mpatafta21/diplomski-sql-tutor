"""DB logika hinta — otključavanje, kredit, idempotencija, fallback (Faza 5.1, §D).

Odvojeno od `hint_agent.py` iz istog razloga zbog kojeg `recommender_logic` stoji
odvojeno od `recommender_agent`: odluke se moraju moći testirati bez XMPP-a,
Prosodyja i event loopa. Ovdje nema nijednog odlaznog poziva — sve je čitanje baze.

🔴 `hints` se ovdje SAMO ČITA. Nijedna funkcija u ovom modulu ne piše u taj katalog
(H2.2a); jedini upisivač je `scripts/seed_hints.py`.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import config
from app.db.models import (
    Attempt,
    Concept,
    Hint,
    HintRequest,
    SkillMastery,
    TaskConcept,
)

#: Ishodi koji troše kredit. `unavailable` NE troši — student nije dobio ništa
#: (odluka C.1 plana 5.0).
CONSUMING_SOURCES = ("llm", "fallback")


def unlocking_attempt(session: Session, user_id: int, task_id: int) -> Attempt | None:
    """Vrati ZADNJI pokušaj na zadatku ako otključava hint, inače ``None``.

    🔴 Odluka 5.0: otključava ga *zadnji* pokušaj i to samo ako je netočan.
    `row_mismatch` se broji kao netočan jer `is_correct` ondje već stoji false —
    ne provjerava se `error_type`, nego istinitost.

    🔴 C.3: ovo je provjera koja se NE smije osloniti na UI. `aria-disabled` gumb
    ostaje klikabilan, a prozor između predaje i osvježenog `TaskDetailResponse`a
    je izmjeren (A3) i stvaran.
    """
    attempt = session.scalars(
        select(Attempt)
        .where(Attempt.user_id == user_id, Attempt.task_id == task_id)
        .order_by(Attempt.attempt_number.desc(), Attempt.id.desc())
        .limit(1)
    ).first()
    if attempt is None or attempt.is_correct:
        return None
    return attempt


def existing_request(session: Session, after_attempt_id: int) -> HintRequest | None:
    """Već isporučen hint za taj pokušaj (C.2 — idempotencija), ili ``None``.

    🔴 `source='unavailable'` se NE vraća: taj redak znači „pokušali smo i nismo
    imali što dati". Vratiti ga kao odgovor značilo bi da jedan pad providera
    trajno zaključa hint na tom pokušaju. Redak ostaje u telemetriji, ali ne
    blokira novi pokušaj.
    """
    return session.scalars(
        select(HintRequest)
        .where(
            HintRequest.after_attempt_id == after_attempt_id,
            HintRequest.source.in_(CONSUMING_SOURCES),
        )
        .order_by(HintRequest.created_at.desc(), HintRequest.id.desc())
        .limit(1)
    ).first()


def hint_credit(
    session: Session, user_id: int, *, now: datetime | None = None
) -> tuple[int, datetime | None]:
    """Izračunaj (preostalo, sljedeća_nadopuna) iz povijesti — bez crona (C.1).

    Model je token bucket kapaciteta ``HINT_MAX`` koji se puni brzinom jedan token
    po ``HINT_REFILL_HOURS``. Stanje se ne pohranjuje nego se REKONSTRUIRA iz
    `hint_requests` pri svakom čitanju: nema reda koji bi mogao odlutati od
    istine, i nema posla koji bi netko morao zakazati.

    🔴 Prozor čitanja je ``HINT_MAX * HINT_REFILL_HOURS``, i to nije aproksimacija:
    toliko vremena puni bucket od nule do vrha, pa stariji zahtjevi ne mogu utjecati
    na rezultat. Upit ide po `idx_hint_requests_user_created`.

    Returns:
        ``(remaining, next_refill_at)``. ``next_refill_at`` je ``None`` kad je
        bucket pun — inače je to trenutak u kojem ``remaining`` poraste za 1.
    """
    now = now or datetime.now(timezone.utc)
    refill = timedelta(hours=config.HINT_REFILL_HOURS)
    window_start = now - refill * config.HINT_MAX

    times = list(
        session.scalars(
            select(HintRequest.created_at)
            .where(
                HintRequest.user_id == user_id,
                HintRequest.source.in_(CONSUMING_SOURCES),
                HintRequest.created_at > window_start,
            )
            .order_by(HintRequest.created_at.asc())
        ).all()
    )

    level = float(config.HINT_MAX)
    prev: datetime | None = None
    for t in times:
        if prev is not None:
            level = min(float(config.HINT_MAX), level + (t - prev) / refill)
        level = max(0.0, level - 1.0)
        prev = t
    if prev is not None:
        level = min(float(config.HINT_MAX), level + (now - prev) / refill)

    remaining = int(math.floor(level))
    if remaining >= config.HINT_MAX:
        return config.HINT_MAX, None
    return remaining, now + refill * (remaining + 1 - level)


def primary_concept(session: Session, task_id: int) -> tuple[int | None, str | None]:
    """(concept_id, code) primarnog koncepta zadatka; (None, None) ako ga nema."""
    row = session.execute(
        select(Concept.id, Concept.code)
        .join(TaskConcept, TaskConcept.concept_id == Concept.id)
        .where(TaskConcept.task_id == task_id, TaskConcept.is_primary.is_(True))
        .limit(1)
    ).first()
    return (row[0], row[1]) if row else (None, None)


def mastery_p_l(session: Session, user_id: int, concept_id: int | None) -> float | None:
    """BKT procjena znanja koncepta, ili ``None`` ako student još nema stanje."""
    if concept_id is None:
        return None
    return session.scalar(
        select(SkillMastery.p_l).where(
            SkillMastery.user_id == user_id, SkillMastery.concept_id == concept_id
        )
    )


def fallback_hint(
    session: Session, error_type: str, concept_id: int | None
) -> Hint | None:
    """Katalog-hint za (tip greške, koncept), ili ``None`` kad ga katalog nema.

    🔴 Ne izmišlja generički tekst kad pogotka nema. Katalog pokriva 8 koncepata ×
    4 tipa greške; sve izvan toga vraća ``None`` i završava kao 503
    (`source='unavailable'`). Rupa se time MJERI umjesto da se zakrpa praznom
    frazom koja ne pomaže.
    """
    if concept_id is None:
        return None
    return session.scalars(
        select(Hint)
        .where(Hint.error_type == error_type, Hint.concept_id == concept_id)
        .order_by(Hint.id)
        .limit(1)
    ).first()
