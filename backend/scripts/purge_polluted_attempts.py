"""Čišćenje zagađenih attempta + pripadajućeg BKT traga (Faza 4.4-0e, KORAK 6).

Pokreni iz ``backend/``::

    uv run python -m scripts.purge_polluted_attempts --dry-run
    uv run python -m scripts.purge_polluted_attempts
    uv run python -m scripts.purge_polluted_attempts --allow-tail-truncate

Default meta: attempti s ``error_type='unsupported_eval'`` (0 XP + BKT KAZNA za
zadatak koji sustav ne zna ocijeniti — vidi 4.4-0c B5). Drugi tip: ``--error-type``.

═══════════════════════════════════════════════════════════════════════════════
🔴 NALAZ #18 — BKT `skill_mastery_history` JE REKURZIVAN LANAC
═══════════════════════════════════════════════════════════════════════════════
Svaka točka je posteriorni update IZRAČUNAT IZ PRETHODNE (`BKT(p_l0=row.p_l)`),
a ne nezavisan uzorak. Posljedice za čišćenje:

  • Brisanje točke iz SREDINE lanca INVALIDIRA sve kasnije točke tog koncepta —
    one su izračunate iz zagađenog priora i ostaju krive i nakon brisanja.
  • "Vrati `skill_mastery.p_l` na zadnji preostali snapshot" je ISPRAVNO SAMO
    ako je zagađena točka bila ZADNJA u lancu tog (user, concept) para.
  • Legitimno čišćenje sredine lanca je ILI
      (i)  brisanje REPA od zagađene točke nadalje (ovaj alat: --allow-tail-truncate),
      ILI (ii) potpuni re-run BKT-a nad preostalim attemptima kronološki.

Zato ovaj alat po defaultu ODBIJA brisanje iz sredine lanca. Zastavica
``--allow-tail-truncate`` je eksplicitan pristanak na strategiju (i).

(Čišćenje u 4.4-0d bilo je ispravno: provjereno je da je zagađena točka bila
ZADNJA u lancu za `where_filter` — attempt je bio 28/28 u seed runu.)
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import logging
from collections import defaultdict

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Attempt, Concept, SkillMastery, SkillMasteryHistory, User, XpLog
from app.db.session import SessionLocal

logger = logging.getLogger("purge_polluted_attempts")


def _polluted_attempt_ids(session: Session, error_type: str) -> list[int]:
    return list(
        session.execute(
            select(Attempt.id).where(Attempt.error_type == error_type)
        ).scalars()
    )


def analyze(session: Session, attempt_ids: list[int]) -> dict:
    """Za svaki (user, concept) utvrdi je li zagađena točka ZADNJA u lancu.

    Vraća {"tail": [...], "mid": [...]} — parovi s repom nakon zagađene točke
    su `mid` (opasni), ostali su `tail` (sigurni za restore-na-zadnji).
    """
    rows = session.execute(
        select(
            SkillMasteryHistory.user_id,
            SkillMasteryHistory.concept_id,
            SkillMasteryHistory.id,
            SkillMasteryHistory.created_at,
        ).where(SkillMasteryHistory.attempt_id.in_(attempt_ids))
    ).all()

    polluted_by_pair: dict[tuple[int, int], list] = defaultdict(list)
    for user_id, concept_id, hid, created in rows:
        polluted_by_pair[(user_id, concept_id)].append((created, hid))

    tail, mid = [], []
    for (user_id, concept_id), points in polluted_by_pair.items():
        oldest_created, oldest_id = min(points)
        # Postoji li LEGITIMNA (nezagađena) točka NAKON najstarije zagađene?
        later = session.scalar(
            select(SkillMasteryHistory.id)
            .where(
                SkillMasteryHistory.user_id == user_id,
                SkillMasteryHistory.concept_id == concept_id,
                SkillMasteryHistory.attempt_id.notin_(attempt_ids),
                SkillMasteryHistory.created_at > oldest_created,
            )
            .limit(1)
        )
        (mid if later is not None else tail).append((user_id, concept_id, len(points)))
    return {"tail": tail, "mid": mid}


def purge(
    session: Session,
    attempt_ids: list[int],
    *,
    allow_tail_truncate: bool,
    dry_run: bool,
) -> dict:
    plan = analyze(session, attempt_ids)
    counts: dict[str, int] = {
        "attempts": len(attempt_ids),
        "pairs_tail": len(plan["tail"]),
        "pairs_mid": len(plan["mid"]),
    }

    if plan["mid"] and not allow_tail_truncate:
        code_of = dict(session.execute(select(Concept.id, Concept.code)).all())
        for user_id, concept_id, n in plan["mid"]:
            logger.error(
                "  SREDINA LANCA: user=%s concept=%s (%d zagađenih točaka) — "
                "postoje KASNIJE legitimne točke izračunate iz zagađenog priora",
                user_id, code_of.get(concept_id, concept_id), n,
            )
        raise SystemExit(
            "🔴 ODBIJENO (NALAZ #18): brisanje iz SREDINE BKT lanca invalidira sve "
            "kasnije točke tih koncepata. Pokreni s --allow-tail-truncate (briše i "
            "rep od zagađene točke nadalje) ili napravi potpuni re-run BKT-a."
        )

    if dry_run:
        logger.info("--dry-run: ništa nije upisano. Plan: %s", counts)
        return counts

    affected_pairs = [(u, c) for u, c, _ in plan["tail"] + plan["mid"]]

    # (i) tail-truncate: ukloni i KASNIJE točke zagađenih parova (rep)
    if allow_tail_truncate and plan["mid"]:
        for user_id, concept_id, _ in plan["mid"]:
            oldest = session.scalar(
                select(SkillMasteryHistory.created_at)
                .where(
                    SkillMasteryHistory.user_id == user_id,
                    SkillMasteryHistory.concept_id == concept_id,
                    SkillMasteryHistory.attempt_id.in_(attempt_ids),
                )
                .order_by(SkillMasteryHistory.created_at.asc())
                .limit(1)
            )
            session.execute(
                delete(SkillMasteryHistory).where(
                    SkillMasteryHistory.user_id == user_id,
                    SkillMasteryHistory.concept_id == concept_id,
                    SkillMasteryHistory.created_at >= oldest,
                )
            )

    session.execute(
        delete(SkillMasteryHistory).where(
            SkillMasteryHistory.attempt_id.in_(attempt_ids)
        )
    )
    session.execute(delete(XpLog).where(XpLog.attempt_id.in_(attempt_ids)))
    session.execute(delete(Attempt).where(Attempt.id.in_(attempt_ids)))

    # Rekalkulacija: p_l = zadnja PREOSTALA točka; bez ijedne → koncept netaknut
    # (redak se briše pa vrijedi tier prior, točno pred-zagađeno stanje).
    for user_id, concept_id in affected_pairs:
        last_p_l = session.scalar(
            select(SkillMasteryHistory.p_l)
            .where(
                SkillMasteryHistory.user_id == user_id,
                SkillMasteryHistory.concept_id == concept_id,
            )
            .order_by(
                SkillMasteryHistory.created_at.desc(), SkillMasteryHistory.id.desc()
            )
            .limit(1)
        )
        sm = session.get(SkillMastery, (user_id, concept_id))
        if sm is None:
            continue
        if last_p_l is None:
            session.delete(sm)
        else:
            sm.p_l = last_p_l

    session.commit()
    logger.info("Očišćeno: %s", counts)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Očisti zagađene attempte + BKT trag.")
    parser.add_argument("--error-type", default="unsupported_eval")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--allow-tail-truncate",
        action="store_true",
        help="dopusti čišćenje iz SREDINE lanca brisanjem repa (NALAZ #18)",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    with SessionLocal() as session:
        ids = _polluted_attempt_ids(session, args.error_type)
        if not ids:
            logger.info("Nema attempta s error_type=%r — ništa za čistiti.", args.error_type)
            return
        logger.info("Pronađeno %d attempta s error_type=%r.", len(ids), args.error_type)
        purge(
            session,
            ids,
            allow_tail_truncate=args.allow_tail_truncate,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
