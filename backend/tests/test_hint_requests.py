"""Testovi za `hint_requests` (Faza 5.0, sekcija B) — CHECK-ovi i CASCADE.

🔴 Tablica je SAMO telemetrija. Ovdje se ne testira nijedan LLM poziv niti ruta;
u 5.0 rute ni agenta nema. Testira se da shema odbija retke koje ne smije primiti
i da brisanje roditelja povuče djecu.

Dokazi su izvedeni podmetnutim retkom (INSERT koji MORA pasti), ne čitanjem DDL-a —
CHECK koji postoji a ne hvata jednak je CHECK-u koji ne postoji.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, insert, select, text
from sqlalchemy.exc import IntegrityError

from app.db.models import Attempt, Hint, HintRequest, Module, Task, User
from app.db.session import SessionLocal

_MODULE_NUMBER = 9803  # ne kolidira s pravim modulima (0-6) ni s 9801/9802
_USERNAME = "hintreq_test_user_50"
_EMAIL = "hintreq_test_50@example.invalid"


@pytest.fixture
def hint_env():
    """Committed module + task + user + JEDAN netočan attempt. Teardown briše sve."""
    with SessionLocal() as sess:
        mod = Module(
            number=_MODULE_NUMBER,
            name="Test modul hint_requests 5.0",
            difficulty="beginner",
            order_index=_MODULE_NUMBER,
        )
        sess.add(mod)
        sess.flush()

        task = Task(
            module_id=mod.id,
            title="Test task hint_requests 5.0",
            description="Hint requests test task",
            sandbox_schema="ecommerce_v1",
            expected_query="SELECT 1",
            expected_result=[],
            difficulty=1,
        )
        sess.add(task)
        sess.flush()

        user = User(username=_USERNAME, email=_EMAIL, password_hash="dummy_hash")
        sess.add(user)
        sess.flush()

        attempt = Attempt(
            user_id=user.id,
            task_id=task.id,
            submitted_query="SELECT 1",
            is_correct=False,
            error_type="row_mismatch",
            attempt_number=1,
        )
        sess.add(attempt)
        sess.commit()

        env = {
            "user_id": user.id,
            "task_id": task.id,
            "attempt_id": attempt.id,
            "module_id": mod.id,
        }

    yield env

    with SessionLocal() as cleanup:
        cleanup.execute(delete(HintRequest).where(HintRequest.user_id == env["user_id"]))
        cleanup.execute(delete(Attempt).where(Attempt.user_id == env["user_id"]))
        cleanup.execute(delete(User).where(User.id == env["user_id"]))
        cleanup.execute(delete(Task).where(Task.id == env["task_id"]))
        cleanup.execute(delete(Module).where(Module.id == env["module_id"]))
        cleanup.commit()


def _row(env, **overrides) -> dict:
    base = {
        "user_id": env["user_id"],
        "task_id": env["task_id"],
        "after_attempt_id": env["attempt_id"],
        "error_type": "row_mismatch",
        "source": "llm",
        "hint_text": "Provjeri GROUP BY.",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# CHECK ck_hint_requests_text_or_unavailable
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("source", ["llm", "fallback"])
def test_source_with_text_is_accepted(hint_env, source) -> None:
    with SessionLocal() as sess:
        sess.execute(insert(HintRequest).values(**_row(hint_env, source=source)))
        sess.commit()
        assert sess.scalar(
            select(HintRequest).where(HintRequest.user_id == hint_env["user_id"])
        )


def test_unavailable_without_text_is_accepted(hint_env) -> None:
    """503 zahtjev nema teksta — mora se moći zabilježiti, inače se rupa ne mjeri."""
    with SessionLocal() as sess:
        sess.execute(
            insert(HintRequest).values(
                **_row(hint_env, source="unavailable", hint_text=None)
            )
        )
        sess.commit()


@pytest.mark.parametrize("source", ["llm", "fallback"])
def test_null_text_rejected_when_source_is_not_unavailable(hint_env, source) -> None:
    """🔴 Podmetnut redak: 'llm'/'fallback' bez teksta MORA pasti."""
    with SessionLocal() as sess, pytest.raises(IntegrityError) as exc:
        sess.execute(
            insert(HintRequest).values(**_row(hint_env, source=source, hint_text=None))
        )
        sess.commit()
    assert "ck_hint_requests_text_or_unavailable" in str(exc.value)


def test_unknown_source_rejected(hint_env) -> None:
    """`source` je zatvoren skup — nepoznata vrijednost ne smije proći."""
    with SessionLocal() as sess, pytest.raises(IntegrityError) as exc:
        sess.execute(insert(HintRequest).values(**_row(hint_env, source="llm_v2")))
        sess.commit()
    assert "ck_hint_requests_source" in str(exc.value)


# ---------------------------------------------------------------------------
# CHECK ck_attempts_error_type_when_incorrect (H3.1, A2 ga je odobrio)
# ---------------------------------------------------------------------------


def test_incorrect_attempt_without_error_type_rejected(hint_env) -> None:
    """🔴 Podmetnut redak: is_correct=False bez error_type MORA pasti."""
    with SessionLocal() as sess, pytest.raises(IntegrityError) as exc:
        sess.add(
            Attempt(
                user_id=hint_env["user_id"],
                task_id=hint_env["task_id"],
                submitted_query="SELECT 1",
                is_correct=False,
                error_type=None,
                attempt_number=2,
            )
        )
        sess.commit()
    assert "ck_attempts_error_type_when_incorrect" in str(exc.value)


def test_correct_attempt_without_error_type_accepted(hint_env) -> None:
    """Druga strana CHECK-a: točan pokušaj bez tipa greške je legitiman."""
    with SessionLocal() as sess:
        sess.add(
            Attempt(
                user_id=hint_env["user_id"],
                task_id=hint_env["task_id"],
                submitted_query="SELECT 1",
                is_correct=True,
                error_type=None,
                attempt_number=3,
            )
        )
        sess.commit()


# ---------------------------------------------------------------------------
# CASCADE
# ---------------------------------------------------------------------------


def test_deleting_attempt_cascades_hint_request(hint_env) -> None:
    with SessionLocal() as sess:
        sess.execute(insert(HintRequest).values(**_row(hint_env)))
        sess.commit()

    with SessionLocal() as sess:
        sess.execute(delete(Attempt).where(Attempt.id == hint_env["attempt_id"]))
        sess.commit()

    with SessionLocal() as sess:
        left = sess.scalars(
            select(HintRequest).where(HintRequest.user_id == hint_env["user_id"])
        ).all()
    assert left == [], "hint_requests nije CASCADE-ao uz obrisan attempt"


def test_hint_id_survives_hint_row_deletion_as_null(hint_env) -> None:
    """`hint_text` je SNIMKA — brisanje/dotjerivanje `hints` retka je ne dira (H1.2).

    FK na `hints` je bez CASCADE-a, pa se `hints` redak koji je u upotrebi ne može
    ni obrisati; tekst zahtjeva ostaje netaknut bez obzira na sudbinu kataloga.
    """
    with SessionLocal() as sess:
        hint = Hint(error_type="row_mismatch", hint_text="Katalog hint", concept_id=None)
        sess.add(hint)
        sess.flush()
        hint_id = hint.id
        sess.execute(
            insert(HintRequest).values(**_row(hint_env, hint_id=hint_id, source="fallback"))
        )
        sess.commit()

    try:
        with SessionLocal() as sess, pytest.raises(IntegrityError):
            sess.execute(delete(Hint).where(Hint.id == hint_id))
            sess.commit()

        with SessionLocal() as sess:
            snapshot = sess.scalar(
                select(HintRequest.hint_text).where(
                    HintRequest.user_id == hint_env["user_id"]
                )
            )
        assert snapshot == "Provjeri GROUP BY."
    finally:
        with SessionLocal() as cleanup:
            cleanup.execute(
                delete(HintRequest).where(HintRequest.user_id == hint_env["user_id"])
            )
            cleanup.execute(delete(Hint).where(Hint.id == hint_id))
            cleanup.commit()


def test_index_is_actually_used_for_limit_query(hint_env) -> None:
    """Indeks nije ukras — plan za upit limita mora ga koristiti.

    Na praznoj tablici PG bira seq scan bez obzira na indeks, pa se plan traži uz
    `enable_seqscan = off`: dokazuje da je indeks PRIMJENJIV na taj upit
    (poredak stupaca odgovara), ne da ga planer danas bira.
    """
    with SessionLocal() as sess:
        sess.execute(text("SET LOCAL enable_seqscan = off"))
        plan = sess.execute(
            text(
                "EXPLAIN SELECT count(*) FROM hint_requests "
                "WHERE user_id = :uid AND created_at > now() - interval '4 hours'"
            ),
            {"uid": hint_env["user_id"]},
        ).scalars().all()
    assert any("idx_hint_requests_user_created" in line for line in plan), (
        "Upit limita ne može koristiti idx_hint_requests_user_created:\n"
        + "\n".join(plan)
    )
