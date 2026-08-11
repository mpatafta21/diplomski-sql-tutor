"""Preporuka NE SMIJE ovisiti o fizičkom poretku redaka u `concepts` (ERRATA #60).

🔴 Ovaj test tvrdi DETERMINIZAM, ne konkretan koncept. Testovi koji tvrde konkretan
koncept (`test_advanced_recommends_inner_join`) su pošteni i ostaju — ali oni padaju
tek KAD se poredak slučajno promijeni, a ovaj pada UVIJEK dok uzrok postoji.

Mehanizam koji se brani:
  `load_concept_code_map` → dict → `build_mastery_snapshot` → `inject_mastery`
  asertira `mastery/3` tim redom → `recommend_next/2` reže prvim rješenjem (`!`).
Bez `ORDER BY` prvi je korak fizički poredak heapa, koji `run_seed()` prepisuje pri
svakom bootu.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, text

from agents.db_helpers import load_concept_code_map
from agents.recommender_logic import recommend
from app.db.models import SkillMastery, User
from app.db.session import SessionLocal
from app.prolog.prolog_engine import PrologEngine
from tests.test_recommender_synthetic import M1_CONCEPTS, M2_CONCEPTS

_USERNAME = "det_test_user_r1"
_EMAIL = "det_r1@test.example"

#: Profil s VIŠE kandidata iste težine — bez toga bi test bio prazan hod.
#: M1+M2+null_handling mastered ostavlja pet weak koncepata s ispunjenim
#: prereq-ima (cross_join, delete, inner_join, scalar_subquery, update), pa
#: redoslijed stvarno odlučuje.
_PROFIL = list(M1_CONCEPTS) + list(M2_CONCEPTS) + ["null_handling"]

#: Koncepti koje Prolog za `_PROFIL` vraća kao `weak` s ispunjenim prereq-ima —
#: izmjereno upitom `weak(U, C), prereqs_met(U, C)`. Točno među njima `!` u
#: `recommend_next/2` bira prvog PO REDOSLIJEDU ASERCIJE, pa je ovo skup nad
#: kojim fizički poredak odlučuje. Kanonski poredak daje `inner_join` (modul 3).
_KANDIDATI = ("cross_join", "delete", "inner_join", "scalar_subquery", "update")


def _fizicki_poredak(session) -> list[str]:
    """Poredak redaka u heapu. `ctid` je izravna mjera — ne ovisi o planeru."""
    return list(
        session.scalars(text("SELECT code FROM concepts ORDER BY ctid")).all()
    )


def _forsiraj_poredak(session, smjer: str) -> list[str]:
    """Fizički presloži `concepts` u `code ASC`/`DESC`. Vrati postignuti poredak.

    🔴 Dva FORSIRANA poretka, ne jedno nasumično prepisivanje: `code ASC` i
    `code DESC` daju abecedno prvog odnosno zadnjeg kandidata, pa na pokvarenom
    kodu nužno daju dva različita ishoda. Prvi pokušaj je samo invertirao
    zatečeni poredak, pa je ishod ovisio o tome gdje je heap slučajno bio.

    🔴 `CLUSTER`, ne `UPDATE`. `UPDATE ... SET name = name` je bio prirodniji
    izbor (točno ono što `run_seed()` radi), ali NE JAMČI poredak: uz 30 redaka
    u dvije stranice PostgreSQL nove verzije smjesti u slobodan prostor iste
    stranice (HOT), pa se poredak jedva pomakne — izmjereno, guard je to i
    uhvatio. `CLUSTER` prepisuje heap u poretku indeksa, bez iznimke.
    """
    assert smjer in ("ASC", "DESC")
    if smjer == "ASC":
        session.execute(text("CLUSTER concepts USING idx_concepts_code"))
    else:
        # DESC indeks ne postoji u shemi — pravi se privremeno pa briše.
        session.execute(
            text("CREATE INDEX ix_tmp_concepts_desc ON concepts (code DESC)")
        )
        session.execute(text("CLUSTER concepts USING ix_tmp_concepts_desc"))
        session.execute(text("DROP INDEX ix_tmp_concepts_desc"))
    session.commit()
    return _fizicki_poredak(session)


@pytest.fixture
def det_env():
    with SessionLocal() as s:
        user = User(username=_USERNAME, email=_EMAIL, password_hash="dummy_det")
        s.add(user)
        s.commit()
        uid = user.id
        cmap = load_concept_code_map(s)
        for code in _PROFIL:
            s.add(SkillMastery(user_id=uid, concept_id=cmap[code], p_l=0.9))
        s.commit()

    yield uid

    with SessionLocal() as cleanup:
        cleanup.execute(delete(SkillMastery).where(SkillMastery.user_id == uid))
        cleanup.execute(delete(User).where(User.id == uid))
        cleanup.commit()


def _preporuci(uid: int) -> dict:
    with PrologEngine() as eng, SessionLocal() as s:
        return recommend(s, eng, uid)


def test_recommendation_survives_physical_row_reordering(det_env) -> None:
    """Isti mastery snapshot → ista preporuka pod dva suprotna fizička poretka."""
    uid = det_env

    with SessionLocal() as s:
        poredak_asc = _forsiraj_poredak(s, "ASC")
    prva = _preporuci(uid)

    with SessionLocal() as s:
        poredak_desc = _forsiraj_poredak(s, "DESC")
    druga = _preporuci(uid)

    # 🔴 Bez ove tvrdnje test prolazi prazan. Ne traži se savršena abeceda —
    # PostgreSQL dio prepisanih redaka smjesti u slobodan prostor ranijih
    # stranica, pa forsirani poredak nije čist (izmjereno). Traži se JEDINO ono
    # o čemu ishod ovisi: da se PRVI KANDIDAT u fizičkom poretku razlikuje.
    # Ako se ne razlikuje, test ne bi razlikovao popravljen kod od pokvarenog.
    prvi_asc = next(c for c in poredak_asc if c in _KANDIDATI)
    prvi_desc = next(c for c in poredak_desc if c in _KANDIDATI)
    assert prvi_asc != prvi_desc, (
        "Oba forsirana poretka stavljaju istog kandidata prvog "
        f"({prvi_asc}) — test bi bio prazan hod."
    )

    assert druga == prva, (
        "Preporuka se promijenila samo zato što su redci fizički premješteni.\n"
        f"  pod code ASC:  {prva}\n"
        f"  pod code DESC: {druga}"
    )


def test_code_map_order_is_canonical_not_physical(det_env) -> None:
    """`load_concept_code_map` vraća kanonski poredak i nakon prepisivanja heapa.

    Ovo je jedinična protuteža gornjem integracijskom testu: kad padne, pokazuje
    TOČAN korak u lancu, bez Prologa i bez profila.
    """
    with SessionLocal() as s:
        # 🔴 Očekivanje se IZRAČUNAVA iz sheme, ne snima iz zatečenog stanja —
        # snimljeni poredak bi na pokvarenom kodu bio jednak fizičkom, pa bi test
        # uspoređivao kvar sam sa sobom (poučak #57).
        ocekivani = list(
            s.scalars(
                text(
                    "SELECT c.code FROM concepts c JOIN modules m ON m.id = c.module_id "
                    "ORDER BY m.order_index, c.order_index, c.id"
                )
            ).all()
        )
        fizicki = _forsiraj_poredak(s, "DESC")

    assert fizicki != ocekivani, (
        "Fizički poredak je slučajno JEDNAK kanonskom — test ne bi razlikovao "
        "popravljen kod od pokvarenog."
    )
    with SessionLocal() as s:
        assert list(load_concept_code_map(s)) == ocekivani
