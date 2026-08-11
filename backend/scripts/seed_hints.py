"""Seed kataloga hintova (Faza 5.0, sekcija C) — 32 retka.

Pokreni iz ``backend/``::

    uv run python -m scripts.seed_hints

Idempotentno: ključ je par ``(error_type, concept_id)``. Postojeći redak se
AŽURIRA, ne duplicira. Tablica `hints` nema UNIQUE nad tim parom (dodavanje bi
tražilo drugu migraciju), pa se jedinstvenost čuva ovdje i provjerava testom;
nalaz je zapisan u docs/faza-5-korak-0.md §C kao kandidat za 5.1.

🔴 Skripta NE briše retke koje ne poznaje — ako se ikad pojavi hint izvan ovog
kataloga, prijavljuje ga i pada, umjesto da ga tiho ukloni.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.hints_data import HINTS
from app.db.models import Concept, Hint
from app.db.session import SessionLocal

logger = logging.getLogger("seed_hints")


def seed_hints(session: Session) -> dict[str, int]:
    """Upiši/ažuriraj 32 hinta. Vrati broj umetnutih i ažuriranih redaka."""
    code_to_id = {
        code: cid for code, cid in session.execute(select(Concept.code, Concept.id))
    }
    missing = {c for _, c, _ in HINTS} - set(code_to_id)
    if missing:
        raise RuntimeError(f"Koncepti ne postoje u bazi: {sorted(missing)}")

    counts = {"inserted": 0, "updated": 0, "unchanged": 0}
    for error_type, concept_code, hint_text in HINTS:
        concept_id = code_to_id[concept_code]
        existing = session.scalars(
            select(Hint).where(
                Hint.error_type == error_type, Hint.concept_id == concept_id
            )
        ).all()
        if len(existing) > 1:
            raise RuntimeError(
                f"Duplikat u `hints` za ({error_type}, {concept_code}): "
                f"{[h.id for h in existing]} — očisti ručno prije seedanja."
            )
        if existing:
            row = existing[0]
            if row.hint_text == hint_text:
                counts["unchanged"] += 1
            else:
                row.hint_text = hint_text
                counts["updated"] += 1
        else:
            session.add(
                Hint(
                    error_type=error_type,
                    concept_id=concept_id,
                    hint_text=hint_text,
                    language="hr",
                )
            )
            counts["inserted"] += 1

    session.commit()
    return counts


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    with SessionLocal() as session:
        counts = seed_hints(session)
    logger.info("Seed hintova — %s", counts)


if __name__ == "__main__":
    main()
