"""`purge_demo_users.py` × `hint_requests` (Faza 5.0, exit B).

🔴 Tvrdnja koja se dokazuje: nova tablica se čisti **CASCADE-om, bez ijedne izmjene
skripte**. Skripta briše `attempts` ručno prije `users`; `hint_requests.after_attempt_id`
je ON DELETE CASCADE, pa redci padnu s pokušajem.

🔴 Verificirano u OBA smjera (poučak #39): briše kad treba **i** ne dira tuđe. Test koji
provjeri samo prvi smjer prolazi i za skriptu koja obriše cijelu tablicu.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, func, insert, select

from app.db.models import Attempt, HintRequest, Module, Task, User
from app.db.session import SessionLocal
from scripts.purge_demo_users import SENTINEL, find_demo_user_ids, purge_demo_users

_MODULE_NUMBER = 9804
_DEMO_USERNAME = f"{SENTINEL}purge_test_50"
_KEEP_USERNAME = "purge_control_user_50"


@pytest.fixture
def purge_env():
    """Dva usera — jedan sentinel, jedan kontrolni — svaki s attemptom i hint_requestom."""
    with SessionLocal() as sess:
        preexisting = find_demo_user_ids(sess)
        if preexisting:
            pytest.skip(
                f"U bazi već postoji {len(preexisting)} `{SENTINEL}` usera — test ih "
                "ne smije obrisati kao usputnu štetu (pokreni purge ručno pa ponovi)."
            )

        mod = Module(
            number=_MODULE_NUMBER,
            name="Test modul purge 5.0",
            difficulty="beginner",
            order_index=_MODULE_NUMBER,
        )
        sess.add(mod)
        sess.flush()

        task = Task(
            module_id=mod.id,
            title="Test task purge 5.0",
            description="Purge test task",
            sandbox_schema="ecommerce_v1",
            expected_query="SELECT 1",
            expected_result=[],
            difficulty=1,
        )
        sess.add(task)
        sess.flush()

        ids = {"module_id": mod.id, "task_id": task.id}
        for key, username in (("demo", _DEMO_USERNAME), ("keep", _KEEP_USERNAME)):
            user = User(
                username=username,
                email=f"{username}@example.invalid",
                password_hash="dummy_hash",
            )
            sess.add(user)
            sess.flush()
            attempt = Attempt(
                user_id=user.id,
                task_id=task.id,
                submitted_query="SELECT 1",
                is_correct=False,
                error_type="wrong_columns",
                attempt_number=1,
            )
            sess.add(attempt)
            sess.flush()
            sess.execute(
                insert(HintRequest).values(
                    user_id=user.id,
                    task_id=task.id,
                    after_attempt_id=attempt.id,
                    error_type="wrong_columns",
                    source="fallback",
                    hint_text="Provjeri imena stupaca.",
                )
            )
            ids[f"{key}_user_id"] = user.id
        sess.commit()

    yield ids

    with SessionLocal() as cleanup:
        uids = [ids["demo_user_id"], ids["keep_user_id"]]
        cleanup.execute(delete(HintRequest).where(HintRequest.user_id.in_(uids)))
        cleanup.execute(delete(Attempt).where(Attempt.user_id.in_(uids)))
        cleanup.execute(delete(User).where(User.id.in_(uids)))
        cleanup.execute(delete(Task).where(Task.id == ids["task_id"]))
        cleanup.execute(delete(Module).where(Module.id == ids["module_id"]))
        cleanup.commit()


def _hint_count(session, user_id: int) -> int:
    return session.scalar(
        select(func.count()).select_from(HintRequest).where(HintRequest.user_id == user_id)
    )


def test_purge_removes_hint_requests_via_cascade(purge_env) -> None:
    """Smjer 1 — sentinel userov hint_request nestaje, iako ga skripta ne spominje."""
    with SessionLocal() as sess:
        assert _hint_count(sess, purge_env["demo_user_id"]) == 1
        counts = purge_demo_users(sess)

    assert counts["users_matched"] == 1
    assert counts["attempts"] == 1
    # 🔴 Skripta NE broji hint_requests — nema ga u povratnom diktu. To je i poanta:
    # tablica se čisti bazom, ne kodom.
    assert "hint_requests" not in counts

    with SessionLocal() as sess:
        assert _hint_count(sess, purge_env["demo_user_id"]) == 0
        assert sess.get(User, purge_env["demo_user_id"]) is None


def test_purge_leaves_other_users_hint_requests_intact(purge_env) -> None:
    """Smjer 2 — kontrolni user je netaknut. Bez ovoga bi i `DELETE FROM hint_requests` prošao."""
    with SessionLocal() as sess:
        purge_demo_users(sess)

    with SessionLocal() as sess:
        assert _hint_count(sess, purge_env["keep_user_id"]) == 1
        assert sess.get(User, purge_env["keep_user_id"]) is not None
        assert sess.scalar(
            select(func.count())
            .select_from(Attempt)
            .where(Attempt.user_id == purge_env["keep_user_id"])
        ) == 1
