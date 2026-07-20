"""Čisti baseline za evaluacijsku sesiju — briše dev/demo/test tragove.

🔴 OVA SKRIPTA BRIŠE PODATKE. ``--dry-run`` je DEFAULT; stvarno brisanje traži
izričit ``--confirm``.

Pokreni iz ``backend/``::

    uv run python -m scripts.prepare_eval_baseline              # dry-run (default)
    uv run python -m scripts.prepare_eval_baseline --confirm    # stvarno briše

Što ZADRŽAVA
------------
* admin RAČUN (``config.ADMIN_USERNAME``) — ali ne i njegovu dev aktivnost
* task bank (85 zadataka), koncepte, module, bedževe, prerequisite
* sandbox bazu (druga instanca Postgresa — ova skripta je uopće ne dira)

Što BRIŠE
---------
* usere sa sentinel prefiksom (``demo44_`` i dr.) + sve njihove ovisne retke
* **aktivnost admin računa** (attempts, BKT, XP, bedževi, streakovi) —
  račun ostaje, povijest ne
* ``agent_messages_log`` u cijelosti — vidi „Zašto i FIPA logovi" niže

Zašto se čisti i admin
----------------------
Admin je tijekom razvoja rješavao zadatke radi testiranja (zatečeno: 7
attempta). Ti redci nisu evaluacijski podaci, ali ulaze u ISTE tablice: kvare
ljestvicu, ulaze u agregate i čine da baseline nije nula. Brisanjem samog
računa izgubio bi se pristup admin sučelju, pa se briše samo AKTIVNOST —
račun, njegova rola i lozinka ostaju netaknuti.

🔴 Nepoznati studenti se NE BRIŠU
---------------------------------
Student koji NEMA sentinel prefiks je nepoznat ovoj skripti. Takav se
**prijavljuje i preskače**, nikad ne briše nagađanjem — mogao bi biti stvarni
sudionik prethodne sesije čiji su podaci nenadoknadivi (NALAZ #37). Ako ga
stvarno treba obrisati, navodi se poimence: ``--also-user <username>``.
Posljedica je namjerna: baseline provjera na kraju PADNE dok takav user ima
attempte, pa se odluka mora donijeti svjesno.

Zašto i FIPA logovi
-------------------
``agent_messages_log`` nema ``user_id`` (provjereno u shemi) → brisanje usera
ga NE dira, pa dev promet preživljava kao „zaostatak". Za obranu rada to je
štetno: admin viewer (4.5b) bi tijekom evala miješao dev tokove sa stvarnima,
a `correlation_id` filter je ionako jedini upotrebljiv ulaz zbog capa od 200
zapisa (NALAZ #36). Baseline ga zato prazni.

FK red brisanja (izmjeren iz ``information_schema``, ne pretpostavljen)
----------------------------------------------------------------------
* ``attempts.user_id`` = NO ACTION → ``attempts`` ide ručno PRIJE ``users``
* ``skill_mastery_history.attempt_id`` i ``xp_log.attempt_id`` = NO ACTION
  → ta dva idu PRIJE ``attempts``
* ostalo (``misconceptions``, ``recommendations_log``, ``skill_mastery``,
  ``streaks``, ``user_badges``) = ON DELETE CASCADE → padne s ``users``

Isti red koristi i ``scripts/purge_demo_users.py``; ovdje je proširen na više
prefiksa i na FIPA logove.
"""

from __future__ import annotations

import argparse
import logging
import sys

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.core import config
from app.db.models import (
    Attempt,
    Concept,
    SkillMasteryHistory,
    Task,
    User,
    XpLog,
)
from app.db.session import SessionLocal

logger = logging.getLogger("prepare_eval_baseline")

#: Prefiksi po kojima se prepoznaje dev/demo/test user (username ILI email).
#: Provjera je ``str.startswith`` u Pythonu, NE SQL ``LIKE`` — u ``LIKE`` bi se
#: ``_`` u prefiksu tumačio kao wildcard i pogodio previše (isti razlog kao u
#: ``purge_demo_users.py``).
#:
#: ``rival_`` je naveden u planu faze, ali GREP nad ``scripts/``, ``app/`` i
#: ``tests/`` (2026-07-20) ne nalazi nijedno njegovo pojavljivanje — ostaje u
#: popisu kao bezopasan (ništa ne pogađa), da se ne izgubi ako se ikad uvede.
SENTINEL_PREFIXES: tuple[str, ...] = (
    "demo44_",
    "rival_",
    "test_",
    "e2e_",
    "smoke_",
)


def find_dev_users(
    session: Session, extra_usernames: set[str]
) -> tuple[list[tuple], list[tuple]]:
    """Podijeli usere na (za brisanje, nepoznati studenti).

    Admin (``config.ADMIN_USERNAME``) se nikad ne dira i nikad ne prijavljuje
    kao nepoznat.
    """
    rows = session.execute(
        select(User.id, User.username, User.email, User.role).order_by(User.id)
    ).all()

    to_delete: list[tuple] = []
    unknown: list[tuple] = []
    for uid, username, email, role in rows:
        if username == config.ADMIN_USERNAME:
            continue
        matched = any(
            (username or "").startswith(p) or (email or "").startswith(p)
            for p in SENTINEL_PREFIXES
        )
        if matched or username in extra_usernames:
            to_delete.append((uid, username, email, role))
        else:
            unknown.append((uid, username, email, role))
    return to_delete, unknown


def dependent_counts(session: Session, ids: list[int]) -> dict[str, int]:
    """Koliko ovisnih redaka nose zadani useri (za ispis PRIJE brisanja)."""
    if not ids:
        return {}
    return {
        "attempts": session.scalar(
            select(func.count()).select_from(Attempt).where(Attempt.user_id.in_(ids))
        )
        or 0,
        "skill_mastery_history": session.scalar(
            select(func.count())
            .select_from(SkillMasteryHistory)
            .where(SkillMasteryHistory.user_id.in_(ids))
        )
        or 0,
        "xp_log": session.scalar(
            select(func.count()).select_from(XpLog).where(XpLog.user_id.in_(ids))
        )
        or 0,
    }


def clear_user_activity(session: Session, uid: int) -> dict[str, int]:
    """Obriši AKTIVNOST usera, ali zadrži sam račun.

    Koristi se za admina: račun mora preživjeti (inače nema pristupa admin
    sučelju tijekom evala), a njegovi dev attempti ne smiju ući u evaluacijske
    podatke. Isti FK red kao kod brisanja usera, samo bez zadnjeg koraka.
    ``skill_mastery``, ``streaks``, ``user_badges``, ``misconceptions`` i
    ``recommendations_log`` ovdje NE padaju CASCADE-om (user ostaje) → brišu
    se izrijekom.
    """
    counts: dict[str, int] = {
        "skill_mastery_history": session.execute(
            delete(SkillMasteryHistory).where(SkillMasteryHistory.user_id == uid)
        ).rowcount,
        "xp_log": session.execute(delete(XpLog).where(XpLog.user_id == uid)).rowcount,
        "attempts": session.execute(
            delete(Attempt).where(Attempt.user_id == uid)
        ).rowcount,
    }
    for table in (
        "skill_mastery",
        "streaks",
        "user_badges",
        "misconceptions",
        "recommendations_log",
    ):
        counts[table] = session.execute(
            text(f"DELETE FROM {table} WHERE user_id = :uid"), {"uid": uid}
        ).rowcount
    return counts


def admin_activity_counts(session: Session, uid: int) -> dict[str, int]:
    """Koliko aktivnosti admin nosi (za ispis PRIJE brisanja)."""
    return {
        "attempts": session.scalar(
            select(func.count()).select_from(Attempt).where(Attempt.user_id == uid)
        )
        or 0,
        "skill_mastery_history": session.scalar(
            select(func.count())
            .select_from(SkillMasteryHistory)
            .where(SkillMasteryHistory.user_id == uid)
        )
        or 0,
        "xp_log": session.scalar(
            select(func.count()).select_from(XpLog).where(XpLog.user_id == uid)
        )
        or 0,
    }


def delete_users(session: Session, ids: list[int]) -> dict[str, int]:
    """Obriši usere + ovisne retke u FK-safe redu (vidi docstring modula)."""
    counts: dict[str, int] = {}
    counts["skill_mastery_history"] = session.execute(
        delete(SkillMasteryHistory).where(SkillMasteryHistory.user_id.in_(ids))
    ).rowcount
    counts["xp_log"] = session.execute(
        delete(XpLog).where(XpLog.user_id.in_(ids))
    ).rowcount
    counts["attempts"] = session.execute(
        delete(Attempt).where(Attempt.user_id.in_(ids))
    ).rowcount
    counts["users"] = session.execute(delete(User).where(User.id.in_(ids))).rowcount
    return counts


def print_baseline_state(session: Session) -> bool:
    """Ispiši stanje baze i vrati True ako je baseline ČIST."""
    users = session.scalar(select(func.count()).select_from(User)) or 0
    admins = (
        session.scalar(
            select(func.count()).select_from(User).where(User.role == "admin")
        )
        or 0
    )
    attempts = session.scalar(select(func.count()).select_from(Attempt)) or 0
    bkt = session.scalar(select(func.count()).select_from(SkillMasteryHistory)) or 0
    xp = session.scalar(select(func.count()).select_from(XpLog)) or 0
    tasks = session.scalar(select(func.count()).select_from(Task)) or 0
    tasks_active = (
        session.scalar(
            select(func.count()).select_from(Task).where(Task.is_active.is_(True))
        )
        or 0
    )
    concepts = session.scalar(select(func.count()).select_from(Concept)) or 0
    logs = session.scalar(text("SELECT count(*) FROM agent_messages_log")) or 0

    logger.info("")
    logger.info("═══ BASELINE STANJE ═══")
    logger.info("  useri:              %d  (admina: %d)", users, admins)
    logger.info(
        "  attempti:           %d  %s",
        attempts,
        "✓" if attempts == 0 else "🔴 MORA BITI 0",
    )
    logger.info(
        "  BKT točaka:         %d  %s", bkt, "✓" if bkt == 0 else "🔴 MORA BITI 0"
    )
    logger.info(
        "  XP zapisa:          %d  %s", xp, "✓" if xp == 0 else "🔴 MORA BITI 0"
    )
    logger.info(
        "  FIPA logova:        %d  %s", logs, "✓" if logs == 0 else "🔴 MORA BITI 0"
    )
    logger.info("  zadataka:           %d  (aktivnih: %d)", tasks, tasks_active)
    logger.info("  koncepata:          %d", concepts)

    clean = attempts == 0 and bkt == 0 and xp == 0 and logs == 0
    logger.info("")
    if clean:
        logger.info("✅ BASELINE ČIST — spreman za evaluacijsku sesiju.")
        logger.info(
            "   Sljedeće: pokreni backend pa `make preflight` (mora biti ZELEN)."
        )
    else:
        logger.info("🔴 BASELINE NIJE ČIST — vidi retke označene gore.")
    return clean


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(
        description="Pripremi čist baseline za eval. DEFAULT je dry-run."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="🔴 STVARNO obriši. Bez ove zastavice skripta samo ispisuje plan.",
    )
    parser.add_argument(
        "--also-user",
        action="append",
        default=[],
        metavar="USERNAME",
        help="dodatno obriši imenovanog usera (za nepoznate; može se ponoviti)",
    )
    parser.add_argument(
        "--keep-agent-logs",
        action="store_true",
        help="ne prazni agent_messages_log (default: prazni se)",
    )
    args = parser.parse_args()

    dry_run = not args.confirm
    extra = set(args.also_user)

    with SessionLocal() as session:
        logger.info("═══════════════════════════════════════════════════")
        logger.info(
            " PRIPREMA EVAL BASELINE-a  [%s]",
            "DRY-RUN" if dry_run else "🔴 STVARNO BRISANJE",
        )
        logger.info("═══════════════════════════════════════════════════")

        to_delete, unknown = find_dev_users(session, extra)

        # --- što se briše ---
        logger.info("")
        logger.info("▸ Useri za brisanje (%d):", len(to_delete))
        if not to_delete:
            logger.info("    (nijedan — nema dev/demo/test tragova)")
        for uid, username, email, role in to_delete:
            logger.info("    id=%-4s %-20s %-32s [%s]", uid, username, email, role)

        deps = dependent_counts(session, [u[0] for u in to_delete])
        if deps:
            logger.info("  ovisni redci koji padaju s njima:")
            for tbl, n in deps.items():
                logger.info("    %-24s %d", tbl, n)
            logger.info(
                "    %-24s %s",
                "(+ CASCADE)",
                "skill_mastery, streaks, user_badges, misconceptions, recommendations_log",
            )

        # --- admin: račun ostaje, aktivnost pada ---
        admin_id = session.scalar(
            select(User.id).where(User.username == config.ADMIN_USERNAME)
        )
        admin_acts = admin_activity_counts(session, admin_id) if admin_id else {}
        logger.info("")
        if admin_id and any(admin_acts.values()):
            logger.info(
                "▸ Admin %r (id=%s): RAČUN OSTAJE, dev aktivnost se briše:",
                config.ADMIN_USERNAME,
                admin_id,
            )
            for tbl, n in admin_acts.items():
                logger.info("    %-24s %d", tbl, n)
            logger.info(
                "    %-24s %s",
                "(+ izrijekom)",
                "skill_mastery, streaks, user_badges, misconceptions, recommendations_log",
            )
        elif admin_id:
            logger.info(
                "▸ Admin %r (id=%s): račun ostaje, nema dev aktivnosti.",
                config.ADMIN_USERNAME,
                admin_id,
            )
        else:
            logger.info(
                "🔴 Admin %r NE POSTOJI — pokreni `make db-seed`.",
                config.ADMIN_USERNAME,
            )

        # --- što se NE briše ---
        logger.info("")
        logger.info(
            "▸ ZADRŽANO: admin račun, task bank, koncepti, moduli, bedževi, sandbox baza"
        )

        if unknown:
            logger.info("")
            logger.info(
                "🔴 NEPOZNATI USERI — NE BRIŠU SE (mogli bi biti stvarni sudionici):"
            )
            for uid, username, email, role in unknown:
                n = session.scalar(
                    select(func.count())
                    .select_from(Attempt)
                    .where(Attempt.user_id == uid)
                )
                logger.info(
                    "    id=%-4s %-20s %-32s [%s]  attempta: %s",
                    uid,
                    username,
                    email,
                    role,
                    n,
                )
            logger.info("")
            logger.info("    Ako ih stvarno treba obrisati, navedi ih poimence:")
            for _, username, _, _ in unknown:
                logger.info("      --also-user %s", username)

        # --- FIPA logovi ---
        log_count = session.scalar(text("SELECT count(*) FROM agent_messages_log")) or 0
        logger.info("")
        if args.keep_agent_logs:
            logger.info(
                "▸ agent_messages_log: %d zapisa — ZADRŽANO (--keep-agent-logs)",
                log_count,
            )
        else:
            logger.info(
                "▸ agent_messages_log: %d zapisa → briše se (dev promet)", log_count
            )

        # --- izvršenje ---
        if dry_run:
            logger.info("")
            logger.info("═══════════════════════════════════════════════════")
            logger.info(" DRY-RUN — NIŠTA NIJE OBRISANO.")
            logger.info(" Za stvarno brisanje ponovi s  --confirm")
            logger.info("═══════════════════════════════════════════════════")
            print_baseline_state(session)
            return 0

        # 🔴 Zadnja brana prije nepovratnog brisanja.
        nothing_to_do = (
            not to_delete
            and not any(admin_acts.values())
            and (args.keep_agent_logs or log_count == 0)
        )
        if nothing_to_do:
            logger.info("")
            logger.info("Nema što obrisati — baza je već čista.")
            return 0 if print_baseline_state(session) else 1

        logger.info("")
        logger.info("▸ Brišem...")
        if to_delete:
            counts = delete_users(session, [u[0] for u in to_delete])
            for tbl, n in counts.items():
                logger.info("    %-24s -%d", tbl, n)
        if admin_id and any(admin_acts.values()):
            logger.info("    — admin aktivnost (račun ostaje):")
            for tbl, n in clear_user_activity(session, admin_id).items():
                if n:
                    logger.info("    %-24s -%d", tbl, n)
        if not args.keep_agent_logs:
            session.execute(text("TRUNCATE TABLE agent_messages_log RESTART IDENTITY"))
            logger.info("    %-24s -%d", "agent_messages_log", log_count)
        session.commit()
        logger.info("  ✓ commit")

        clean = print_baseline_state(session)
        return 0 if clean else 1


if __name__ == "__main__":
    sys.exit(main())
