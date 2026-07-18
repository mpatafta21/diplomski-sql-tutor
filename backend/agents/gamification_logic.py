"""Čista logika GamificationAgenta — XP, leveli, mastery, streak, badge eval.

Faza 3D.1: ZERO I/O. Bez DB, SPADE, Prologa, mreže. Sve funkcije su čiste i
determinističke (samo stdlib: datetime, math, dataclasses, typing, frozenset).
SPADE omotač, DB upsert i diff protiv već-zarađenih badgeva su posao 3D.2.

Odluka (zaključana): badge-evaluacija se radi u Pythonu (Opcija A), NE u
Prologu — `badges.pl` ostaje placeholder. Pravila ovdje moraju semantički
odgovarati seedanim `badges.rule` tekstovima (app/db/seed_data.py BADGES).

Konstante su FINALIZIRANE (flag #5 zatvoren, mentor potvrdio postojeće
vrijednosti) — racional po konstanti stoji uz blok KONSTANTE ispod. Testovi
asertiraju kompoziciju preko konstanti + ANCHOR primjere iz §3.4.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

# ======================================================================
# KONSTANTE — FINALNE (flag #5 zatvoren; mentor potvrdio vrijednosti)
# ======================================================================
# Racional po konstanti (bivši TODO(mentor F2a-F2d) markeri):
#
# F2a XP_BASE_BY_DIFFICULTY — linearna skala u difficulty 1..5 (omjer 1:2:3:4:5).
#     Skala je tasks.difficulty (razina MODULA, ne concept-tier). [1]=10 je
#     anchor deriviran iz §3.4 worked examplea (citabilno u tezi).
#
# F2b VERDICT_FACTOR — partial=0.5 je REZERVIRAN/dormant: ERRATA #8 (attempts
#     nema verdict kolonu) znači da se "partial" trenutno NE generira; faktor
#     postoji da buduća migracija verdicta ne mijenja formulu.
#
# F2c FIRST_ATTEMPT_BONUS — 1.pokušaj ×2.0, 2. ×1.5, 3+ floor ×1.0. Bonus opada
#     NA bazu, ne ispod nje: ustrajnost i dalje nosi punu bazu (poravnato s
#     "Comeback Kid" duhom §3.4, bez kažnjavanja ponovnih pokušaja).
#
# F2d LEVEL_STEP — linearno, 100 XP = +1 level. Rastuća krivulja svjesno
#     ODBAČENA: na eval-skali (tjedni, deseci zadataka) ne daje ništa osim
#     kompliciranije formule; usklađeno s master planom (docx §4.3).
#
# Nota: streak NAMJERNO ne množi XP — XP ostaje čist proxy za učinak-u-učenju
# (streak se nagrađuje kroz streak_7 badge). Badge XP (seed_data.py xp_reward)
# se u persistenceu STAKUJE u isti xp_delta kao attempt XP.

# Bazni XP po difficulty (tasks.difficulty ∈ 1..5); [1]=10 anchor iz §3.4.
XP_BASE_BY_DIFFICULTY: dict[int, int] = {
    1: 10,
    2: 20,
    3: 30,
    4: 40,
    5: 50,
}

# Faktor točnosti po Evaluatorovom verdiktu (agents/evaluation.py).
# partial=0.5 dormant do verdict migracije (ERRATA #8).
VERDICT_FACTOR: dict[str, float] = {
    "correct": 1.0,
    "partial": 0.5,
    "incorrect": 0.0,
}

# Bonus multiplikator po attempt_number. Prvi pokušaj nosi najviše;
# §3.4 primjer (linija 442): ×1.5 ide DRUGOM pokušaju.
FIRST_ATTEMPT_BONUS: dict[int, float] = {
    1: 2.0,
    2: 1.5,
}
# Za attempt_number >= 3 (bonus opada na bazu, ne ispod).
FIRST_ATTEMPT_BONUS_FLOOR: float = 1.0

# Level prag: linearno, svaki LEVEL_STEP XP = +1 level (rastuće odbačeno).
LEVEL_STEP: int = 100

# Prag savladanosti koncepta — MORA biti identičan rules.pl:11 `mastery_threshold(0.85)`.
MASTERY_THRESHOLD: float = 0.85

# Badge skupovi (semantika seedanih badges.rule tekstova).
JOIN_CONCEPTS: frozenset[str] = frozenset({"inner_join", "left_join", "right_join"})
# explorer: kriterij je DINAMIČAN (NALAZ #22, Faza 4.4-0f) — skup modula koji
# STVARNO imaju aktivne zadatke, a ne hardkodiranih {1..6}. Razlog: modul 6 je
# od 4.4-0e izvan opsega (NALAZ #19, taskovi is_active=False), pa je fiksni
# kriterij "svih 6 modula" učinio bedž NEDOSTIŽNIM svakom studentu — a galerija
# bedževa (4.4a) i dalje ga je prikazivala s kriterijem koji se ne može ispuniti.
# Skup se injektira kroz BadgeFacts.evaluable_modules (eval_badges ostaje čist),
# pa se automatski proširi ako M6 ikad postane evaluabilan.
# Modul 0 ("Transverzalni") i dalje NIJE dio kriterija — vidi 3D nalaz #6.


# ======================================================================
# XP
# ======================================================================


def compute_xp(difficulty: int, verdict: str, attempt_number: int) -> int:
    """Izračunaj XP za jedan pokušaj.

    xp = round_half_up(base * verdict_factor * attempt_bonus)

    Args:
        difficulty: tasks.difficulty (1..5).
        verdict: Evaluatorov verdict ("correct"|"partial"|"incorrect").
        attempt_number: redni broj pokušaja (>=1); 1 i 2 nose bonus, 3+ floor.

    Returns:
        Nenegativan cijeli broj XP-a (round-half-up). incorrect → 0.

    Raises:
        ValueError: nepoznat difficulty ili verdict.
    """
    if difficulty not in XP_BASE_BY_DIFFICULTY:
        raise ValueError(f"Nepoznat difficulty: {difficulty!r}")
    if verdict not in VERDICT_FACTOR:
        raise ValueError(f"Nepoznat verdict: {verdict!r}")

    base = XP_BASE_BY_DIFFICULTY[difficulty]
    factor = VERDICT_FACTOR[verdict]
    bonus = FIRST_ATTEMPT_BONUS.get(attempt_number, FIRST_ATTEMPT_BONUS_FLOOR)

    # Eksplicitni round-half-up (NE round() koji radi banker's rounding).
    return math.floor(base * factor * bonus + 0.5)


# ======================================================================
# LEVEL
# ======================================================================


def level_for_xp(xp: int) -> int:
    """Level iz ukupnog XP-a: 1 + xp // LEVEL_STEP (linearno, počinje od 1)."""
    return 1 + xp // LEVEL_STEP


def progress_to_next_level(xp: int) -> tuple[int, int, int]:
    """Vrati (level, xp_unutar_levela, xp_do_iduceg_levela).

    Invarijanta: xp_unutar_levela + xp_do_iduceg == LEVEL_STEP.
    """
    level = level_for_xp(xp)
    xp_in_level = xp % LEVEL_STEP
    xp_to_next = LEVEL_STEP - xp_in_level
    return (level, xp_in_level, xp_to_next)


# ======================================================================
# MASTERY
# ======================================================================


def mastered_concepts(snapshot: dict[str, float]) -> frozenset[str]:
    """Skup koncepata s P(L) >= MASTERY_THRESHOLD (prag uključen)."""
    return frozenset(
        code for code, p_l in snapshot.items() if p_l >= MASTERY_THRESHOLD
    )


# ======================================================================
# STREAK
# ======================================================================


def streak_from_active_dates(
    active_dates: set[date], today: date
) -> tuple[int, int]:
    """Izračunaj (current_streak, longest_streak) iz skupa aktivnih dana.

    PRETPOSTAVKA: `today` je u `active_dates` (evaluacija se uvijek događa na
    današnji attempt). Datumi su VEĆ u ciljnoj zoni (Europe/Zagreb) — ova
    funkcija je tz-agnostična, konverzija je posao 3D.2 wrappera.

    Args:
        active_dates: skup datuma s barem jednim pokušajem.
        today: današnji datum (mora biti u active_dates).

    Returns:
        (current, longest):
          current  — duljina neprekidnog niza koji ZAVRŠAVA na today.
          longest  — najduži neprekidni niz bilo gdje u active_dates.

    Raises:
        AssertionError: ako today nije u active_dates.
    """
    assert today in active_dates, "today mora biti u active_dates"

    # current: brojimo unatrag od danas dok su dani uzastopni.
    current = 0
    cursor = today
    while cursor in active_dates:
        current += 1
        cursor -= timedelta(days=1)

    # longest: prođi sortirane datume, broji uzastopne nizove.
    longest = 0
    run = 0
    prev: date | None = None
    for d in sorted(active_dates):
        if prev is not None and d - prev == timedelta(days=1):
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        prev = d

    return (current, longest)


# ======================================================================
# BADGES
# ======================================================================


@dataclass(frozen=True)
class BadgeFacts:
    """Predagregirane činjenice za badge evaluaciju (sastavlja ih 3D.2 iz DB)."""

    has_correct: bool
    mastered: frozenset[str]
    current_streak: int
    attempted_modules: frozenset[int]
    #: Brojevi modula (bez 0) koji imaju BAREM JEDAN aktivan zadatak — kriterij
    #: za `explorer`. Prazan skup → bedž se ne dodjeljuje (fail-closed).
    evaluable_modules: frozenset[int]


def eval_badges(facts: BadgeFacts) -> frozenset[str]:
    """Vrati skup KODOVA badgeva koje činjenice zadovoljavaju.

    Semantika prati seedane badges.rule tekstove (Opcija A — eval u Pythonu).
    Diff protiv već-zarađenih badgeva i insert su posao 3D.2 wrappera.
    """
    earned: set[str] = set()

    if facts.has_correct:
        earned.add("first_correct")
    if JOIN_CONCEPTS <= facts.mastered:
        earned.add("join_master")
    if "null_handling" in facts.mastered:
        earned.add("null_ninja")
    if facts.current_streak >= 7:
        earned.add("streak_7")
    # Fail-closed: prazan skup evaluabilnih modula NE dodjeljuje bedž
    # (inače bi prazan podskup trivijalno zadovoljio <=).
    if facts.evaluable_modules and facts.evaluable_modules <= facts.attempted_modules:
        earned.add("explorer")

    return frozenset(earned)
