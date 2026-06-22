"""TDD testovi za agents/knowledge_logic.py — 3B.1.

Testiraju BKT update logiku i SkillMastery upsert bez SPADE omotača.

Koncepti iz ontologije (provjeri ontology.pl):
  left_join  → hard   (p_l0=0.05, p_t=0.10, p_g=0.10, p_s=0.15)
  agg_count  → medium (p_l0=0.15, p_t=0.20, p_g=0.20, p_s=0.10)
  group_by   → medium (p_l0=0.15, p_t=0.20, p_g=0.20, p_s=0.10)

Cleanup strategija: knowledge_env kreira committed usera i briše ga
(CASCADE na skill_mastery) u teardown-u. Svaki test koristi svježi
SessionLocal() za poziv update_mastery_for_attempt (koji interno commita).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy import delete, select

from agents.db_helpers import load_concept_code_map
from agents.knowledge_logic import update_mastery_for_attempt
from app.db.models import Concept, SkillMastery, User
from app.db.session import SessionLocal
from app.prolog.prolog_engine import PrologEngine

# ---------------------------------------------------------------------------
# Konstante
# ---------------------------------------------------------------------------

_KM_USERNAME = "km_test_user_3b1"
_KM_EMAIL = "km_3b1@test.example"


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def knowledge_env():
    """Kreira committed test usera. Teardown briše usera (CASCADE → skill_mastery).

    Koncepti su već seedani u bazi — ne trebamo ih kreirati.
    """
    user_id = None

    with SessionLocal() as sess:
        user = User(
            username=_KM_USERNAME,
            email=_KM_EMAIL,
            password_hash="dummy_hash_3b1",
        )
        sess.add(user)
        sess.commit()
        user_id = user.id

    yield {"user_id": user_id}

    with SessionLocal() as cleanup:
        cleanup.execute(delete(SkillMastery).where(SkillMastery.user_id == user_id))
        cleanup.execute(delete(User).where(User.id == user_id))
        cleanup.commit()


@pytest.fixture
def prolog_engine():
    """PrologEngine instanca s automatskim cleanup-om mastery fakata."""
    with PrologEngine() as engine:
        yield engine


# ---------------------------------------------------------------------------
# Pomoćna funkcija za dohvat concept_id iz koda
# ---------------------------------------------------------------------------


def _concept_id(code: str) -> int:
    with SessionLocal() as sess:
        cid = sess.scalar(select(Concept.id).where(Concept.code == code))
    assert cid is not None, f"Koncept {code!r} nije seedan u bazi"
    return cid


# ---------------------------------------------------------------------------
# T1 — Lazy init je tier-based (D3 KLJUČNI test)
# ---------------------------------------------------------------------------


async def test_lazy_init_hard_concept_uses_tier_params(knowledge_env, prolog_engine):
    """D3: novi (user, left_join) [hard] dobiva p_l0=0.05 i p_t=0.10, NE DB default.

    DB server_default je 0.15/0.20/0.20/0.10 (medium). Tier-based init
    za hard treba dati p_l0=0.05, p_t=0.10, p_g=0.10, p_s=0.15.
    Provjeravamo pohranjene p_t/p_g/p_s jer su razlikovni od DB defaulta.
    """
    user_id = knowledge_env["user_id"]

    with SessionLocal() as sess:
        result = await update_mastery_for_attempt(
            sess, prolog_engine, user_id, ["left_join"], is_correct=True
        )

    assert "left_join" in result

    with SessionLocal() as verify:
        row = verify.get(SkillMastery, (user_id, _concept_id("left_join")))

    assert row is not None
    # Hard-tier parametri (razlikuju se od DB default medium)
    assert row.p_t == pytest.approx(0.10), "p_t mora biti 0.10 (hard), ne 0.20 (medium DB default)"
    assert row.p_g == pytest.approx(0.10), "p_g mora biti 0.10 (hard), ne 0.20 (medium DB default)"
    assert row.p_s == pytest.approx(0.15), "p_s mora biti 0.15 (hard), ne 0.10 (medium DB default)"
    # p_l je nakon jednog correct update-a (krece od p_l0=0.05)
    # Ocekivano: ~0.3782 (izracunato iz BKT formule za hard)
    assert row.p_l == pytest.approx(0.37818182, rel=1e-4), (
        f"p_l={row.p_l} ne odgovara BKT hard tier update (ocekivano ~0.378)"
    )


# ---------------------------------------------------------------------------
# T2 — Update mijenja p_l u ispravnom smjeru
# ---------------------------------------------------------------------------


async def test_correct_attempt_increases_p_l(knowledge_env, prolog_engine):
    """correct attempt → p_l raste od p_l0."""
    user_id = knowledge_env["user_id"]

    with SessionLocal() as sess:
        result = await update_mastery_for_attempt(
            sess, prolog_engine, user_id, ["agg_count"], is_correct=True
        )

    # medium: p_l0=0.15, after 1x correct ≈ 0.5541
    assert result["agg_count"] == pytest.approx(0.55409836, rel=1e-4)
    assert result["agg_count"] > 0.15


async def test_incorrect_attempt_lowers_p_l(knowledge_env, prolog_engine):
    """incorrect attempt → p_l pada od p_l0 (za medium, uz slip factor p_s=0.10)."""
    user_id = knowledge_env["user_id"]

    with SessionLocal() as sess:
        result = await update_mastery_for_attempt(
            sess, prolog_engine, user_id, ["agg_count"], is_correct=False
        )

    # medium: p_l0=0.15, after 1x incorrect ≈ 0.2173 (raste malo zbog transition)
    # Ali je manji od correct puta (0.5541)
    assert result["agg_count"] == pytest.approx(0.21726619, rel=1e-4)
    assert result["agg_count"] < 0.55  # nije kao correct


# ---------------------------------------------------------------------------
# T3 — Update kreće od TRENUTNOG p_l, ne od p_l0
# ---------------------------------------------------------------------------


async def test_second_update_starts_from_persisted_p_l(knowledge_env, prolog_engine):
    """Dva uzastopna correct attempta: drugi kreće od p_l prvog, ne od p_l0.

    Ako bi agent resetirao na p_l0=0.15, drugi correct bi dao ≈0.5541 (isto kao prvi).
    Ispravno: drugi kreće od ≈0.5541 → daje ≈0.8786.
    """
    user_id = knowledge_env["user_id"]

    with SessionLocal() as sess:
        await update_mastery_for_attempt(
            sess, prolog_engine, user_id, ["agg_count"], is_correct=True
        )

    with SessionLocal() as sess:
        result = await update_mastery_for_attempt(
            sess, prolog_engine, user_id, ["agg_count"], is_correct=True
        )

    # Ako je krivo resetirao na p_l0: ≈0.5541 (isti kao prvi)
    # Ispravno (krece od p_l1=0.5541): ≈0.8786
    assert result["agg_count"] == pytest.approx(0.87863915, rel=1e-4), (
        "Drugi update mora krecem od p_l prvog (0.5541), ne od p_l0 (0.15). "
        f"Dobiveno: {result['agg_count']:.6f}"
    )


# ---------------------------------------------------------------------------
# T4 — Svi koncepti iz lists[] su updateani
# ---------------------------------------------------------------------------


async def test_all_concepts_in_list_are_updated(knowledge_env, prolog_engine):
    """Task s dva koncepta → oba dobivaju SkillMastery red."""
    user_id = knowledge_env["user_id"]

    with SessionLocal() as sess:
        result = await update_mastery_for_attempt(
            sess, prolog_engine, user_id, ["agg_count", "group_by"], is_correct=True
        )

    assert "agg_count" in result
    assert "group_by" in result

    agg_id = _concept_id("agg_count")
    grp_id = _concept_id("group_by")

    with SessionLocal() as verify:
        agg_row = verify.get(SkillMastery, (user_id, agg_id))
        grp_row = verify.get(SkillMastery, (user_id, grp_id))

    assert agg_row is not None, "SkillMastery red za agg_count mora postojati"
    assert grp_row is not None, "SkillMastery red za group_by mora postojati"


# ---------------------------------------------------------------------------
# T5 — Nepoznat Prolog tier → glasan SKIP, nema SkillMastery reda
# ---------------------------------------------------------------------------


async def test_unknown_prolog_tier_skips_without_creating_row(knowledge_env, prolog_engine):
    """Koncept koji je u DB ali nema Prolog tier → SKIP + nema SkillMastery reda.

    Mockamo create_bkt_for_concept da digne ValueError za agg_count,
    ali pusti group_by da prode normalno.
    Dokazuje glasan preskok (ne tihi medium fallback).
    """
    user_id = knowledge_env["user_id"]
    agg_id = _concept_id("agg_count")

    original_create = __import__(
        "bkt.parameters", fromlist=["create_bkt_for_concept"]
    ).create_bkt_for_concept

    def mock_create(concept: str, engine):
        if concept == "agg_count":
            raise ValueError(f"Koncept {concept!r} nema tier u ontologiji")
        return original_create(concept, engine)

    with patch("agents.knowledge_logic.create_bkt_for_concept", side_effect=mock_create):
        with SessionLocal() as sess:
            result = await update_mastery_for_attempt(
                sess, prolog_engine, user_id, ["agg_count", "group_by"], is_correct=True
            )

    # agg_count preskocen → nema u rezultatu i nema u DB
    assert "agg_count" not in result, "Preskoceni koncept ne smije biti u rezultatu"
    assert "group_by" in result, "group_by (poznat tier) mora proci normalno"

    with SessionLocal() as verify:
        agg_row = verify.get(SkillMastery, (user_id, agg_id))
    assert agg_row is None, "Preskoceni koncept ne smije imati SkillMastery red"


# ---------------------------------------------------------------------------
# T6 — attempts_count i correct_count točni
# ---------------------------------------------------------------------------


async def test_attempts_and_correct_count_increments(knowledge_env, prolog_engine):
    """3 attempta (2 correct, 1 incorrect) → attempts_count=3, correct_count=2."""
    user_id = knowledge_env["user_id"]
    concept_id = _concept_id("group_by")

    for is_correct in [True, False, True]:
        with SessionLocal() as sess:
            await update_mastery_for_attempt(
                sess, prolog_engine, user_id, ["group_by"], is_correct=is_correct
            )

    with SessionLocal() as verify:
        row = verify.get(SkillMastery, (user_id, concept_id))

    assert row is not None
    assert row.attempts_count == 3, f"Ocekivano 3, dobiveno {row.attempts_count}"
    assert row.correct_count == 2, f"Ocekivano 2, dobiveno {row.correct_count}"


# ---------------------------------------------------------------------------
# T7 — load_concept_code_map vraća sve koncepte
# ---------------------------------------------------------------------------


def test_load_concept_code_map_covers_all_concepts():
    """load_concept_code_map vraca dict s 30 konceptima (seedano u seed.py)."""
    with SessionLocal() as sess:
        code_map = load_concept_code_map(sess)

    assert "left_join" in code_map
    assert "agg_count" in code_map
    assert "group_by" in code_map
    assert len(code_map) == 30, f"Ocekivano 30 konceptima, dobiveno {len(code_map)}"
    assert all(isinstance(k, str) and isinstance(v, int) for k, v in code_map.items())
