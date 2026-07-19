"""Seed dev demo user + realistična povijest (Faza 4.4-0, KORAK 2).

Dev-only alat za pripremu podataka Faze 4.4 (Profil & Stats). NIJE dio produkcije.

Pokreni iz ``backend/`` (gateway MORA vrtjeti na BASE_URL)::

    uv run python -m scripts.seed_demo_user
    uv run python -m scripts.seed_demo_user --base-url http://localhost:8000

🔴 INTEGRITET BKT PODATAKA (zaključano pravilo):
  - SVI attempti idu kroz PRAVI ``POST /attempt`` pipeline (HTTP). NIŠTA se
    NE inserta ručno u ``skill_mastery`` ni ``skill_mastery_history`` —
    p_l vrijednosti su 100 % produkt BKT update-a u agentskom toku.
  - Skripta SMIJE ČITATI ``tasks.expected_query`` iz baze (seed alat, ne API
    klijent) da bi znala točan upit. Netočni upiti deriviraju se DETERMINISTIČKI
    iz točnog (wrap-subquery / dodatni stupac / nepostojeća tablica).

Idempotentnost: DELETE-then-recreate. Na startu zove ``purge_demo_users``
(briše sve ``demo44_`` usere) pa seeda iznova → ponovni run daje isti dataset.

created_at: svi attempti nastaju u JEDNOM run-u pa su timestampi unutar iste
minute (backend postavlja ``now()``; razmicanje kroz dane zahtijevalo bi ili
izravan DB upis timestampa ili izmjenu backenda — oboje je zabranjeno u ovom
koraku). Vidi izvještaj skripte.
"""

from __future__ import annotations

import argparse
import logging
import os

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Module, Task
from app.db.session import SessionLocal
from scripts.purge_demo_users import purge_demo_users

logger = logging.getLogger("seed_demo_user")

DEFAULT_BASE_URL = os.environ.get("SEED_BASE_URL", "http://localhost:8000")
HTTP_TIMEOUT = 30.0

# Sentinel identitet (mora dijeliti prefiks s purge_demo_users.SENTINEL).
DEMO_USERNAME = "demo44_student"
DEMO_EMAIL = "demo44_student@mailinator.com"
DEMO_PASSWORD = "demo44_pw_Str0ng!"  # dev-only, ne perzistira se nigdje osim hash-a

# Raspon očekivanih redaka za taskove pogodne za "partial" transform:
# wrap+LIMIT 1 daje row_mismatch SAMO ako original vraća > 1 red.
_MIN_ROWS, _MAX_ROWS = 2, 8


# ---------------------------------------------------------------------------
# Deterministički generatori upita iz točnog expected_query
# ---------------------------------------------------------------------------


def _strip(q: str) -> str:
    """Skini razmake i trailing ';' (radi umetanja u subquery)."""
    return q.strip().rstrip(";").strip()


def q_correct(expected: str) -> str:
    return _strip(expected)


def q_partial(expected: str) -> str:
    """row_mismatch: isti stupci, MANJE redaka (LIMIT 1 nad omotanim originalom)."""
    return f"SELECT * FROM (\n{_strip(expected)}\n) _seed_sub LIMIT 1"


def q_wrong_columns(expected: str) -> str:
    """wrong_columns: isti redci, ali VIŠAK stupca (zzz_seed_extra)."""
    return f"SELECT *, 42 AS zzz_seed_extra FROM (\n{_strip(expected)}\n) _seed_sub"


def q_error(_expected: str) -> str:
    """execution_error: nepostojeća tablica (deterministički PG error)."""
    return "SELECT * FROM zzz_no_such_table_seed_demo"


_QUERY_FOR_KIND = {
    "correct": q_correct,
    "partial": q_partial,
    "wrong_columns": q_wrong_columns,
    "error": q_error,
}


# ---------------------------------------------------------------------------
# Izbor taskova iz baze (deterministički: najmanji id-evi)
# ---------------------------------------------------------------------------


def _tasks_for_module(
    session: Session,
    number: int,
    *,
    limit: int,
    rows_bounded: bool,
) -> list[tuple[int, str]]:
    """(task_id, expected_query) za aktivne taskove modula ``number``, po id-u.

    ``rows_bounded`` → filtrira na expected_result duljine [_MIN_ROWS, _MAX_ROWS]
    (za partial-eligible taskove). Inače uzima bilo koji aktivan task (explorer).
    """
    stmt = (
        select(Task.id, Task.expected_query)
        .join(Module, Module.id == Task.module_id)
        .where(Task.is_active.is_(True), Module.number == number)
    )
    if rows_bounded:
        stmt = stmt.where(
            func.jsonb_array_length(Task.expected_result).between(_MIN_ROWS, _MAX_ROWS)
        )
    stmt = stmt.order_by(Task.id).limit(limit)
    return [(tid, q) for tid, q in session.execute(stmt).all()]


def build_plan(session: Session) -> list[tuple[int, str, str]]:
    """Sastavi plan attempta: lista (task_id, kind, expected_query) u redu izvršavanja.

    Ciljani volumen ~28 attempta, ~60/20/20 (correct/partial/ostalo), kroz module
    1,2,3,4,5,6 (explorer) i ≥8 koncepata. Fokus-krivulja: jedan task modula 1
    ponovljen 10× (8 correct + 2 partial) → duga, uspinjuća krivulja za KORAK 3.
    """
    focus = _tasks_for_module(session, 1, limit=1, rows_bounded=True)
    m2 = _tasks_for_module(session, 2, limit=2, rows_bounded=True)
    m3 = _tasks_for_module(session, 3, limit=2, rows_bounded=True)
    m5 = _tasks_for_module(session, 5, limit=2, rows_bounded=True)
    m4 = _tasks_for_module(session, 4, limit=1, rows_bounded=False)
    m6 = _tasks_for_module(session, 6, limit=1, rows_bounded=False)

    # 🔴 Modul 6 je NAMJERNO izvan opsega od 4.4-0e (NALAZ #19): njegovi taskovi
    # su is_active=False jer ih evaluacijska jezgra ne zna ocijeniti. Zato NIJE
    # u obaveznom popisu — ako nema aktivnih taskova, preskače se.
    # POSLJEDICA: bedž `explorer` (traži pokušaj u SVIH 6 modula) je NEDOSTIŽAN
    # dok je M6 izvan opsega; demo user zato osvaja samo `first_correct`.
    missing = [
        name
        for name, sel, need in [
            ("modul1-focus", focus, 1),
            ("modul2", m2, 2),
            ("modul3", m3, 2),
            ("modul5", m5, 2),
            ("modul4", m4, 1),
        ]
        if len(sel) < need
    ]
    if missing:
        raise RuntimeError(
            f"Nedovoljno aktivnih taskova za seed plan: {missing}. "
            "Provjeri da je baza seedana (make db-seed / import_dataset)."
        )

    focus_id, focus_q = focus[0]
    plan: list[tuple[int, str, str]] = []

    # Fokus-krivulja (modul 1): C C P C C C P C C C
    focus_seq = [
        "correct", "correct", "partial", "correct", "correct",
        "correct", "partial", "correct", "correct", "correct",
    ]
    plan += [(focus_id, kind, focus_q) for kind in focus_seq]

    # Modul 2: A(C,C,P) B(C,error,error)
    (m2a_id, m2a_q), (m2b_id, m2b_q) = m2[0], m2[1]
    plan += [
        (m2a_id, "correct", m2a_q), (m2a_id, "correct", m2a_q), (m2a_id, "partial", m2a_q),
        (m2b_id, "correct", m2b_q), (m2b_id, "error", m2b_q), (m2b_id, "error", m2b_q),
    ]

    # Modul 3 (JOIN-ovi): A(C,C,P) B(C,wrong_columns,C)
    (m3a_id, m3a_q), (m3b_id, m3b_q) = m3[0], m3[1]
    plan += [
        (m3a_id, "correct", m3a_q), (m3a_id, "correct", m3a_q), (m3a_id, "partial", m3a_q),
        (m3b_id, "correct", m3b_q), (m3b_id, "wrong_columns", m3b_q), (m3b_id, "correct", m3b_q),
    ]

    # Modul 5: A(C,P) B(C,error)
    (m5a_id, m5a_q), (m5b_id, m5b_q) = m5[0], m5[1]
    plan += [
        (m5a_id, "correct", m5a_q), (m5a_id, "partial", m5a_q),
        (m5b_id, "correct", m5b_q), (m5b_id, "error", m5b_q),
    ]

    # Modul 4: 1 attempt (error) — širina pokrivenosti.
    plan.append((m4[0][0], "error", m4[0][1]))
    # Modul 6 samo AKO ima aktivnih taskova (vidi napomenu o NALAZ #19 gore).
    if m6:
        plan.append((m6[0][0], "error", m6[0][1]))

    return plan


# ---------------------------------------------------------------------------
# HTTP tok: register/login → POST /attempt
# ---------------------------------------------------------------------------


def _register_or_login(client: httpx.Client, base_url: str) -> str:
    """Registriraj demo usera; ako već postoji (409), loginaj. Vrati bearer token."""
    r = client.post(
        f"{base_url}/register",
        json={"username": DEMO_USERNAME, "email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    if r.status_code == 200:
        return r.json()["access_token"]
    if r.status_code != 409:
        raise RuntimeError(f"/register neočekivan status {r.status_code}: {r.text}")
    # fallback (ne bi se trebalo dogoditi nakon purge-a)
    r = client.post(
        f"{base_url}/login",
        data={"username": DEMO_USERNAME, "password": DEMO_PASSWORD},
    )
    r.raise_for_status()
    return r.json()["access_token"]


def _verdict(is_correct: bool | None, error_type: str | None) -> str:
    """Ista derivacija kao frontend lib/feedback.ts (jedinstveni izvor istine)."""
    if is_correct is True:
        return "correct"
    if is_correct is False:
        return "partial" if error_type == "row_mismatch" else "incorrect"
    return "unknown"


def run_seed(base_url: str) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # 1) idempotentnost: obriši postojeće demo44_ usere
    with SessionLocal() as session:
        purged = purge_demo_users(session)
    logger.info("Purge prije seeda: %s", purged)

    # 2) plan iz baze
    with SessionLocal() as session:
        plan = build_plan(session)
    logger.info("Plan: %d attempta.", len(plan))

    verdict_counts: dict[str, int] = {}
    error_type_counts: dict[str, int] = {}
    all_badges: list[str] = []

    with httpx.Client(timeout=HTTP_TIMEOUT) as client:
        token = _register_or_login(client, base_url)
        headers = {"Authorization": f"Bearer {token}"}
        me = client.get(f"{base_url}/me", headers=headers).json()
        logger.info("Demo user: id=%s username=%s", me["id"], me["username"])

        for i, (task_id, kind, expected_q) in enumerate(plan, start=1):
            query = _QUERY_FOR_KIND[kind](expected_q)
            resp = client.post(
                f"{base_url}/attempt",
                json={"task_id": task_id, "submitted_query": query},
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            fb = data["feedback"]
            v = _verdict(fb.get("is_correct"), fb.get("error_type"))
            verdict_counts[v] = verdict_counts.get(v, 0) + 1
            et = fb.get("error_type")
            if et:
                error_type_counts[et] = error_type_counts.get(et, 0) + 1
            for b in data.get("new_badges") or []:
                all_badges.append(b)
            logger.info(
                "  [%02d/%d] task=%s plan=%-13s -> verdict=%-9s error_type=%-14s xp_delta=%s%s",
                i, len(plan), task_id, kind, v, et or "-", data.get("xp_delta"),
                f" badges+={data['new_badges']}" if data.get("new_badges") else "",
            )

        # 3) završni snapshot iz živog API-ja
        profile = client.get(f"{base_url}/profile", headers=headers).json()
        history = client.get(f"{base_url}/mastery-history", headers=headers).json()

    concepts = sorted({p["concept"] for p in history})
    per_concept: dict[str, int] = {}
    for p in history:
        per_concept[p["concept"]] = per_concept.get(p["concept"], 0) + 1

    logger.info("\n===== SEED IZVJEŠTAJ =====")
    logger.info("Attempta ukupno: %d", len(plan))
    logger.info("Verdict distribucija: %s", verdict_counts)
    logger.info("error_type distribucija: %s", error_type_counts)
    logger.info("Bedževi (kumulativno kroz run): %s", all_badges)
    logger.info("Profil badges (finalno): %s", profile.get("badges"))
    logger.info("Profil xp=%s level=%s streak=%s/%s",
                profile.get("xp"), profile.get("level"),
                profile.get("current_streak"), profile.get("longest_streak"))
    logger.info("Mastery-history točaka: %d", len(history))
    logger.info("Različitih koncepata: %d -> %s", len(concepts), concepts)
    logger.info("Točaka po konceptu: %s", dict(sorted(per_concept.items(), key=lambda kv: -kv[1])))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo44_ user + BKT povijest (dev-only).")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"Gateway URL (default {DEFAULT_BASE_URL})")
    args = parser.parse_args()
    run_seed(args.base_url)


if __name__ == "__main__":
    main()
