"""Export evaluacijskih podataka u CSV za analizu — PSEUDONIMIZIRANO.

Pokreni iz ``backend/``::

    uv run python -m scripts.export_eval_data
    uv run python -m scripts.export_eval_data --out ../exports

Izlaz: ``exports/eval_YYYYMMDD_HHMMSS/`` (gitignoriran) sa:

===========================  ==========================================
datoteka                     sadržaj
===========================  ==========================================
``attempts.csv``             jezgra evaluacije, uz ``source_id`` (#21)
``skill_mastery_history.csv``BKT krivulje po konceptu
``skill_mastery.csv``        završno stanje P(L) po konceptu
``xp_log.csv``               XP transakcije
``user_badges.csv``          osvojeni bedževi + ``earned_at``
``streaks.csv``              dnevna aktivnost
``participants.csv``         SAMO ``pseudonym`` + ``role`` (bez identiteta)
``tasks.csv``                metapodaci zadataka za join
``concepts.csv``             šifrarnik koncepata
``_pseudonym_map.csv``       🔴 id → pseudonim — NE COMMITATI, NE U RAD
===========================  ==========================================

🔴 PSEUDONIMIZACIJA JE DEFAULT, NE OPCIJA
-----------------------------------------
``username`` i ``email`` NE IZLAZE ni u jednu datoteku osim ``_pseudonym_map.csv``.
Ta je mapa jedina poveznica pseudonima sa stvarnim identitetom sudionika —
čuva se odvojeno, ne commita se i ne prilaže radu. Bez nje su ostale datoteke
same po sebi anonimne.

Skripta na kraju SAMA provjeri izlaz: pročita svaki generirani CSV i padne s
ne-nul kodom ako u njemu nađe ijedan živi username ili email iz baze. Tvrdnja
„identitet nije u izlazu" tako nije obećanje nego provjera (🔒 DOC politika).

``submitted_query`` je NAMJERNO IZOSTAVLJEN
--------------------------------------------
Tekst studentovog upita je osobni podatak (veže se uz osobu) i nije potreban
za kvantitativnu analizu (točnost, BKT, XP). Ako zatreba za kvalitativnu
analizu grešaka, vadi se iz backupa uz izričitu odluku i suglasnost sudionika.

Napomene
--------
* Bez novih dependencija — samo stdlib ``csv`` (parquet bi tražio ``pyarrow``).
* Idempotentno: svaki run piše u NOVI timestampirani direktorij, ne prepisuje.
* Pseudonimi su determinirani rastućim ``users.id`` → P01, P02, … Isti skup
  korisnika daje isti raspored pseudonima u svakom runu.
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import SessionLocal

logger = logging.getLogger("export_eval_data")

#: Kolone koje ne smiju izaći ni u jednoj datoteci osim mape pseudonima.
FORBIDDEN_COLUMNS = {"username", "email", "password_hash", "submitted_query"}

#: Ime datoteke s mapom identiteta — jedina koja smije sadržavati identitet.
PSEUDONYM_MAP_FILE = "_pseudonym_map.csv"


# ---------------------------------------------------------------------------
# Upiti
# ---------------------------------------------------------------------------
# Svaki upit vraća `user_pseudonym` umjesto `user_id`; join na `users` služi
# SAMO za dohvat id-a koji se u Pythonu prevodi u pseudonim.

QUERIES: dict[str, str] = {
    # `source_id` uz svaki `task_id` — NALAZ #21: task_id je nestabilan preko
    # reseeda, source_id je kanonski ključ. Analiza mora koristiti source_id.
    "attempts": """
        SELECT a.id, a.user_id, a.task_id, t.source_id, a.is_correct,
               a.error_type, a.xp_awarded, a.attempt_number,
               a.execution_time_ms, a.rows_returned, a.hint_requested,
               a.created_at
        FROM attempts a
        JOIN tasks t ON t.id = a.task_id
        ORDER BY a.user_id, a.created_at, a.id
    """,
    "skill_mastery_history": """
        SELECT h.id, h.user_id, c.code AS concept, h.p_l, h.attempt_id,
               h.created_at
        FROM skill_mastery_history h
        JOIN concepts c ON c.id = h.concept_id
        ORDER BY h.user_id, c.code, h.created_at, h.id
    """,
    "skill_mastery": """
        SELECT s.user_id, c.code AS concept, s.p_l, s.p_t, s.p_g, s.p_s,
               s.attempts_count, s.correct_count, s.last_updated
        FROM skill_mastery s
        JOIN concepts c ON c.id = s.concept_id
        ORDER BY s.user_id, c.code
    """,
    "xp_log": """
        SELECT x.id, x.user_id, x.attempt_id, x.delta, x.reason, x.created_at
        FROM xp_log x
        ORDER BY x.user_id, x.created_at, x.id
    """,
    # NALAZ #14: `earned_at` postoji SAMO ovdje (API ga ne izlaže) — zato je
    # ovaj export jedini izvor za vremensku analizu osvajanja bedževa.
    "user_badges": """
        SELECT ub.user_id, b.code AS badge, b.xp_reward, ub.earned_at
        FROM user_badges ub
        JOIN badges b ON b.id = ub.badge_id
        ORDER BY ub.user_id, ub.earned_at
    """,
    "streaks": """
        SELECT s.user_id, s.date, s.attempts_count
        FROM streaks s
        ORDER BY s.user_id, s.date
    """,
    # Metapodaci zadataka za join. `expected_query`/`expected_result` NE IZLAZE
    # (rješenja zadataka — vidi sigurnosni sken 4.5 §9).
    "tasks": """
        SELECT t.id AS task_id, t.source_id, m.number AS module,
               t.title, t.difficulty, t.is_active,
               pc.code AS primary_concept,
               (SELECT string_agg(c2.code, '|' ORDER BY c2.code)
                  FROM task_concepts tc2 JOIN concepts c2 ON c2.id = tc2.concept_id
                 WHERE tc2.task_id = t.id AND tc2.is_primary = FALSE) AS secondary_concepts
        FROM tasks t
        JOIN modules m ON m.id = t.module_id
        LEFT JOIN task_concepts tc ON tc.task_id = t.id AND tc.is_primary = TRUE
        LEFT JOIN concepts pc ON pc.id = tc.concept_id
        ORDER BY t.source_id
    """,
    "concepts": """
        SELECT c.code, c.name, c.tier, m.number AS module, c.order_index
        FROM concepts c
        JOIN modules m ON m.id = c.module_id
        ORDER BY m.number, c.order_index
    """,
}

#: Tablice bez `user_id` — ne pseudonimiziraju se (nemaju osobni podatak).
NON_USER_TABLES = {"tasks", "concepts"}


# ---------------------------------------------------------------------------
# Pseudonimizacija
# ---------------------------------------------------------------------------
def build_pseudonym_map(session: Session) -> dict[int, str]:
    """Mapa ``users.id -> 'P01'``, determinirana rastućim id-om.

    Admin dobiva pseudonim kao i svi ostali (u ``participants.csv`` ostaje
    stupac ``role`` pa ga analiza može filtrirati) — tako nijedan izlaz ne
    mora sadržavati ``username`` da bi se admin razlikovao od studenta.
    """
    ids = list(session.scalars(select(User.id).order_by(User.id)))
    width = max(2, len(str(len(ids))))
    return {uid: f"P{i:0{width}d}" for i, uid in enumerate(ids, start=1)}


def pseudonymize(
    rows: list[dict[str, Any]], pmap: dict[int, str]
) -> list[dict[str, Any]]:
    """Zamijeni ``user_id`` s ``user_pseudonym`` na prvom mjestu u retku."""
    out: list[dict[str, Any]] = []
    for row in rows:
        uid = row.pop("user_id")
        out.append({"user_pseudonym": pmap.get(uid, f"UNKNOWN_{uid}"), **row})
    return out


# ---------------------------------------------------------------------------
# Pisanje
# ---------------------------------------------------------------------------
def write_csv(path: Path, rows: list[dict[str, Any]]) -> int:
    """Zapiši retke u CSV. Prazan skup daje datoteku SAMO sa zaglavljem
    ako je poznato, inače praznu datoteku (da izostanak bude vidljiv)."""
    if not rows:
        path.write_text("", encoding="utf-8")
        return 0
    leaked = FORBIDDEN_COLUMNS & set(rows[0])
    if leaked:  # obrana u dubinu — upit se ne smije tiho promijeniti
        raise RuntimeError(f"{path.name}: zabranjene kolone u izlazu: {sorted(leaked)}")
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def fetch(session: Session, sql: str) -> list[dict[str, Any]]:
    result = session.execute(text(sql))
    return [dict(r) for r in result.mappings()]


# ---------------------------------------------------------------------------
# 🔴 Verifikacija izlaza
# ---------------------------------------------------------------------------
def verify_no_identity(out_dir: Path, session: Session) -> None:
    """Pročitaj SVAKI generirani CSV i padni ako sadrži živi username/email.

    Ovo nije formalnost: pseudonimizacija se lako pokvari dodavanjem stupca u
    upit. Provjera hvata takvu regresiju odmah, umjesto da identitet završi u
    prilogu diplomskog rada.

    Usporedba ide po ĆELIJI, ne po sirovom tekstu datoteke. Razlog je konkretan:
    admin se zove ``admin``, a ``participants.csv`` ima stupac ``role`` s
    vrijednošću ``admin`` — sirovi ``substring`` pretraživanjem to prijavljuje
    kao curenje identiteta, što nije. ``role`` je ZATVOREN šifrarnik
    (``student``/``admin``) koji generira ova skripta, ne korisnik, pa se
    izuzima imenom. Svaki drugi stupac se provjerava.

    Neovisno o šifrarnicima, ćelija koja izgleda kao e-mail (sadrži ``@``) je
    curenje uvijek i bezuvjetno — taj oblik ne može doći ni iz jednog
    legitimnog stupca u izlazu.
    """
    #: Stupci sa zatvorenim skupom vrijednosti koje NE dolaze od korisnika.
    #: Izuzimaju se jer se mogu slučajno poklopiti s username-om (npr. "admin").
    enum_columns = {"role"}

    identities: set[str] = set()
    for username, email in session.execute(select(User.username, User.email)).all():
        if username:
            identities.add(username.lower())
        if email:
            identities.add(email.lower())

    problems: list[str] = []
    scanned = 0
    for csv_path in sorted(out_dir.glob("*.csv")):
        if csv_path.name == PSEUDONYM_MAP_FILE:
            continue  # jedina datoteka koja SMIJE sadržavati identitet
        scanned += 1
        if not csv_path.read_text(encoding="utf-8").strip():
            continue  # prazna tablica
        with csv_path.open(encoding="utf-8", newline="") as fh:
            for line_no, row in enumerate(csv.DictReader(fh), start=2):
                for column, value in row.items():
                    if value is None:
                        continue
                    cell = value.strip().lower()
                    if "@" in cell:
                        problems.append(
                            f"{csv_path.name}:{line_no} stupac '{column}' "
                            f"izgleda kao e-mail: {value!r}"
                        )
                    if column in enum_columns:
                        continue
                    if cell and cell in identities:
                        problems.append(
                            f"{csv_path.name}:{line_no} stupac '{column}' "
                            f"sadrži identitet: {value!r}"
                        )

    if problems:
        for p in problems[:20]:
            logger.error("🔴 CURENJE IDENTITETA — %s", p)
        raise SystemExit("🔴 EXPORT ODBAČEN: identitet je procurio u izlaz.")

    logger.info(
        "  ✓ %d CSV datoteka provjereno ćeliju-po-ćeliju protiv %d živih "
        "identiteta (username + email) — 0 pogodaka",
        scanned,
        len(identities),
    )
    logger.info("  ✓ 0 ćelija u obliku e-maila")


# ---------------------------------------------------------------------------
# Glavni tok
# ---------------------------------------------------------------------------
def run_export(out_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = out_root / f"eval_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as session:
        pmap = build_pseudonym_map(session)
        logger.info("Sudionika (svi useri): %d", len(pmap))

        counts: dict[str, int] = {}
        for name, sql in QUERIES.items():
            rows = fetch(session, sql)
            if name not in NON_USER_TABLES:
                rows = pseudonymize(rows, pmap)
            counts[name] = write_csv(out_dir / f"{name}.csv", rows)
            logger.info("  %-24s %6d redaka", f"{name}.csv", counts[name])

        # participants.csv — pseudonim + rola, BEZ identiteta.
        participants = [
            {"user_pseudonym": pmap[uid], "role": role, "created_at": created}
            for uid, role, created in session.execute(
                select(User.id, User.role, User.created_at).order_by(User.id)
            ).all()
        ]
        counts["participants"] = write_csv(out_dir / "participants.csv", participants)
        logger.info("  %-24s %6d redaka", "participants.csv", counts["participants"])

        # 🔴 Mapa identiteta — ZASEBNA datoteka, ne commita se, ne ide u rad.
        map_rows = [
            {
                "user_id": uid,
                "pseudonym": pmap[uid],
                "username": username,
                "email": email,
            }
            for uid, username, email in session.execute(
                select(User.id, User.username, User.email).order_by(User.id)
            ).all()
        ]
        with (out_dir / PSEUDONYM_MAP_FILE).open(
            "w", encoding="utf-8", newline=""
        ) as fh:
            writer = csv.DictWriter(
                fh, fieldnames=["user_id", "pseudonym", "username", "email"]
            )
            writer.writeheader()
            writer.writerows(map_rows)
        logger.info(
            "  %-24s %6d redaka  🔴 NE COMMITATI", PSEUDONYM_MAP_FILE, len(map_rows)
        )

        # --- sanity ispis ---
        logger.info("")
        logger.info("═══ SANITY ═══")
        span = session.execute(
            text("SELECT min(created_at)::date, max(created_at)::date FROM attempts")
        ).first()
        students = sum(1 for p in participants if p["role"] == "student")
        active_users = session.execute(
            text("SELECT count(DISTINCT user_id) FROM attempts")
        ).scalar_one()
        logger.info("  sudionika ukupno:       %d (studenata: %d)", len(pmap), students)
        logger.info("  s barem jednim attemptom: %d", active_users)
        logger.info("  attempta:               %d", counts["attempts"])
        logger.info("  BKT točaka:             %d", counts["skill_mastery_history"])
        logger.info("  XP zapisa:              %d", counts["xp_log"])
        logger.info("  bedževa osvojeno:       %d", counts["user_badges"])
        logger.info("  zadataka (svi):         %d", counts["tasks"])
        logger.info(
            "  raspon datuma:          %s",
            f"{span[0]} … {span[1]}" if span and span[0] else "(nema attempta)",
        )

        logger.info("")
        logger.info("═══ PROVJERA PRIVATNOSTI ═══")
        verify_no_identity(out_dir, session)

    return out_dir


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(
        description="Export evaluacijskih podataka u CSV (pseudonimizirano)."
    )
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parents[2] / "exports"),
        help="korijenski direktorij za export (default: <repo>/exports)",
    )
    args = parser.parse_args()

    out_dir = run_export(Path(args.out))

    logger.info("")
    logger.info("✅ EXPORT GOTOV → %s", out_dir)
    logger.info("")
    logger.info("🔴 %s sadrži identitet sudionika:", PSEUDONYM_MAP_FILE)
    logger.info("   – NE commitati (exports/ je u .gitignore)")
    logger.info("   – NE prilagati radu")
    logger.info("   – čuvati odvojeno od ostalih CSV-ova")


if __name__ == "__main__":
    sys.exit(main())
