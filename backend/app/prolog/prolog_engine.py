"""pyswip wrapper — apstrakcija Prolog upita za SPADE agente i testove.

Ovaj modul je jedini mjesto u backend-u koji direktno poziva pyswip.
Ostatak koda (agenti, API) koristi `PrologEngine` API.

Napomene o pyswip 0.3.x:
- `Prolog` klasa je singleton (class-level stanje). Višestruke instance
  dijele istu Prolog VM. Cleanup `mastery/3` fakata u `__exit__` je
  nužan da testovi ne cure stanje među sobom.
- `consult()` prima apsolutnu putanju do `rules.pl`. Relativni
  `:- consult('ontology.pl')` unutar rules.pl radi ispravno jer
  SWI-Prolog resolva relativne putanje od direktorija u kojemu se
  nalazi fajl koji se consult-a — nije potreban chdir.
- NE koristi async — pyswip je synchronous. Integracija sa SPADE-om
  (koji je async) doći će u Fazi 3 kroz thread-pool adapter.

Ugovor `inject_mastery`: pozivatelj je odgovoran ubaciti `mastery/3`
fakte za sve koncepte koje želi da `can_unlock/2` i `recommend_next/2`
razmatraju. Ako koncept nema injectan mastery fakt, `can_unlock` taj
koncept ne smatra kandidatom (pogledaj §4.4 rules.pl). Za puno
pokrivanje preporuča se injectati svih 30 koncepata.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from types import TracebackType

from pyswip import Prolog

# Apsolutna putanja do direktorija s Prolog fajlovima (backend/prolog/).
# __file__ = backend/app/prolog/prolog_engine.py → parents[2]/prolog
_PROLOG_DIR: Path = Path(__file__).resolve().parents[2] / "prolog"
_RULES_FILE: str = "rules.pl"


class PrologEngine:
    """Wrapper oko pyswip koji expose-a tipizirano API za preporuke.

    Koristi kao context manager:

        with PrologEngine() as engine:
            engine.inject_mastery("user_1", {"select_basic": 0.1, ...})
            result = engine.recommend_next("user_1")

    Nakon izlaska iz `with` bloka, svi `mastery/3` fakti se brišu.
    """

    def __init__(self) -> None:
        """Inicijalizira pyswip Prolog instance i consult-a rules.pl.

        Koristi apsolutnu putanju za consult kako bi Prolog mogao pronaći
        rules.pl bez obzira na cwd procesa. Relativni `:- consult('ontology.pl')`
        unutar rules.pl radi jer SWI-Prolog resolva relativne putanje od
        direktorija u kojem se nalazi fajl koji se consult-a.
        """
        self._injected_users: set[str] = set()
        self._prolog = Prolog()
        self._prolog.consult(str(_PROLOG_DIR / _RULES_FILE))

    def __enter__(self) -> "PrologEngine":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Čisti sve ubačene mastery fakte i globalne `recommendable/1` fakte."""
        for user_id in list(self._injected_users):
            self.clear_mastery(user_id)
        self.clear_recommendable()

    # --- Injekcija BKT snapshot-a ---------------------------------------

    def inject_mastery(
        self, user_id: str, mastery_snapshot: dict[str, float]
    ) -> None:
        """Ubacuje dinamičke `mastery(user_id, concept, p_l)` činjenice.

        Briše eventualne postojeće fakte za tog korisnika prije inserta
        (idempotentno). Vrijednosti se formatiraju kao Python floatovi
        (npr. `0.1`) — NE prosljeđuje se Python dict direktno.
        """
        self.clear_mastery(user_id)
        for concept, p_l in mastery_snapshot.items():
            # assertz vraća None u pyswip 0.3.x — ne wrappamo u list()
            self._prolog.assertz(f"mastery({user_id}, {concept}, {float(p_l)})")
        self._injected_users.add(user_id)

    def clear_mastery(self, user_id: str) -> None:
        """Retractall za sve `mastery/3` fakte danog user_id-a."""
        list(self._prolog.query(f"retractall(mastery({user_id}, _, _))"))
        self._injected_users.discard(user_id)

    # --- Injekcija skupa preporučivih koncepata --------------------------

    def inject_recommendable(self, concept_codes: Iterable[str]) -> None:
        """Ubacuje `recommendable/1` fakte — koncepti koji IMAJU aktivne zadatke.

        🔴 Za razliku od `mastery/3`, ovo NIJE po korisniku: skup je izveden iz
        kataloga zadataka i jednak je za sve. Zato je i `retractall` globalan, pa
        injekcija, upit i čišćenje MORAJU biti u istoj kritičnoj sekciji
        (`prolog_lock` u RecommenderAgentu) — inače bi jedan tok maknuo fakte
        drugome usred upita.

        🔴 Fail-closed: bez ijednog fakta `recommend_next/2` ne vraća NIŠTA.
        Propuštena injekcija se time vidi odmah (nula preporuka), umjesto da
        tiho vrati koncept bez zadataka — kvar zbog kojeg predikat i postoji.
        """
        self.clear_recommendable()
        for code in concept_codes:
            self._prolog.assertz(f"recommendable({code})")

    def clear_recommendable(self) -> None:
        """Retractall za sve `recommendable/1` fakte (globalno, nije po korisniku)."""
        list(self._prolog.query("retractall(recommendable(_))"))

    # --- Preporuke ------------------------------------------------------

    def recommend_next(self, user_id: str) -> tuple[str, str] | None:
        """Vraća (concept_code, reason) ili None ako preporuka ne postoji.

        Koristi `recommend_next/2` + `explain_recommendation/3` iz rules.pl.
        """
        rec_query = f"recommend_next({user_id}, Concept)"
        rec_solutions = list(self._prolog.query(rec_query, maxresult=1))
        if not rec_solutions:
            return None

        concept = str(rec_solutions[0]["Concept"])

        reason_query = f"explain_recommendation({user_id}, {concept}, Reason)"
        reason_solutions = list(self._prolog.query(reason_query, maxresult=1))
        reason = (
            str(reason_solutions[0]["Reason"]) if reason_solutions else "fallback"
        )

        return (concept, reason)

    # --- Graf upiti -----------------------------------------------------

    def all_prereqs(self, concept: str) -> list[str]:
        """Tranzitivni zatvarač prerequisite-a za dani koncept.

        Vraća sortirana lista (kao što `all_prereqs/2` u Prologu radi).
        """
        query = f"all_prereqs({concept}, Prereqs)"
        solutions = list(self._prolog.query(query, maxresult=1))
        if not solutions:
            return []
        prereqs = solutions[0]["Prereqs"]
        # pyswip vraća listu atoma kao Python list; svaki atom je str ili Atom
        return [str(p) for p in prereqs]

    def get_tier(self, concept: str) -> str:
        """Vraća tier ('easy'|'medium'|'hard') za dani koncept iz ontology.pl."""
        query = f"tier({concept}, Tier)"
        solutions = list(self._prolog.query(query, maxresult=1))
        if not solutions:
            raise ValueError(f"Koncept {concept!r} nema tier u ontologiji")
        return str(solutions[0]["Tier"])

    def is_ready_for(self, user_id: str, concept: str) -> bool:
        """True ako su svi prereqs koncepta mastered za user_id."""
        query = f"ready_for({user_id}, {concept})"
        solutions = list(self._prolog.query(query, maxresult=1))
        return bool(solutions)
