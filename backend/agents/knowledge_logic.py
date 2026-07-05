"""BKT update logika za KnowledgeModelAgent — čist modul bez SPADE ovisnosti.

Ulaz:  attempt payload (user_id, concepts: list[code], is_correct)
Izlaz: dict[concept_code, novi_p_l] za sve uspješno obrađene koncepte

D3 — tier-based lazy init: pri prvom attemptu za par (user, concept) agent
radi lazy init kroz create_bkt_for_concept(concept, engine) s Prolog tier-om.
DB default 0.15 se NE koristi.

pyswip je synchronous; pozivi su omotani u asyncio.to_thread da ne blokiraju
SPADE event loop.

Nepoznati koncepti (nema DB zapisa ili nema Prolog tier) se GLASNO preskaču
(WARNING log) — tihi fallback bi maskirao desinkronizaciju ontologije.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from agents.db_helpers import load_concept_code_map
from app.db.models import SkillMastery, SkillMasteryHistory
from bkt.model import BKT
from bkt.parameters import create_bkt_for_concept

if TYPE_CHECKING:
    from app.prolog.prolog_engine import PrologEngine

_log = logging.getLogger(__name__)


async def update_mastery_for_attempt(
    session: Session,
    engine: "PrologEngine",
    user_id: int,
    concepts: list[str],
    is_correct: bool,
    attempt_id: int | None = None,
) -> dict[str, float]:
    """BKT posterior update za sve koncepte attempta.

    Args:
        session: SQLAlchemy session — bit će commitana unutar ove funkcije.
        engine:  PrologEngine instanca za get_tier() pozive (singleton VM).
        user_id: FK na users.id (mora već postojati).
        concepts: lista concept code-ova iz attempt payloada (D2-čisti).
        is_correct: je li attempt bio točan.
        attempt_id: FK na attempts.id koji je izazvao update — snapshotira se u
            skill_mastery_history. None ako nije poznat (lazy paths / testovi).

    Returns:
        dict[concept_code, novi_p_l] za sve obrađene koncepte.
        Preskočeni koncepti (nema DB zapisa ili nema Prolog tier) NISU u dictu.

    Side-effect: za SVAKI upsertan koncept dodaje se skill_mastery_history snapshot
    na ISTU sesiju → ulazi u isti commit (atomarno s mastery upsertom). Preskočeni
    koncepti (continue) NEMAJU history red.
    """
    code_map = load_concept_code_map(session)
    result: dict[str, float] = {}

    for code in concepts:
        if code not in code_map:
            _log.warning(
                "update_mastery: koncept %r nije u concepts tablici — preskacem", code
            )
            continue

        concept_id = code_map[code]

        try:
            bkt_init: BKT = await asyncio.to_thread(create_bkt_for_concept, code, engine)
        except ValueError:
            _log.warning(
                "update_mastery: koncept %r nema Prolog tier — preskacem (ne degradiram na medium)",
                code,
            )
            continue

        row = session.get(SkillMastery, (user_id, concept_id))

        if row is None:
            # D3: lazy init s tier-based parametrima, NE DB server_default 0.15
            row = SkillMastery(
                user_id=user_id,
                concept_id=concept_id,
                p_l=bkt_init.p_l,
                p_t=bkt_init.p_t,
                p_g=bkt_init.p_g,
                p_s=bkt_init.p_s,
                attempts_count=0,
                correct_count=0,
            )
            session.add(row)
            bkt = bkt_init
        else:
            # Rekonstruiraj BKT iz row.p_l (trenutno stanje), NE iz p_l0.
            # BKT(p_l0=row.p_l) postavlja self.p_l = p_l0 = row.p_l — update
            # kreće od trenutnog stanja, ne od pocetnog priora.
            bkt = BKT(
                p_l0=row.p_l,
                p_t=row.p_t,
                p_g=row.p_g,
                p_s=row.p_s,
            )

        new_p_l = bkt.update(is_correct)

        row.p_l = new_p_l
        row.attempts_count += 1
        row.correct_count += 1 if is_correct else 0
        row.last_updated = datetime.now(timezone.utc)

        result[code] = new_p_l

        # Atoman snapshot: ulazi u isti session.commit() kao mastery upsert.
        session.add(
            SkillMasteryHistory(
                user_id=user_id,
                concept_id=concept_id,
                p_l=new_p_l,
                attempt_id=attempt_id,
            )
        )

    session.commit()
    return result
