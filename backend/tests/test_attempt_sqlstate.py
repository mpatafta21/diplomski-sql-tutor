"""`attempts.sqlstate` se stvarno popunjava (Faza 5.1, B1).

🔴 Zašto zaseban upis, a ne polje u `persist_attempt`: `persistence.py` je zamrznut
(odluka 8 plana 5.1), a `persist_attempt` gradi `Attempt(...)` sa zatvorenim popisom
polja — nema načina da `sqlstate` uđe kroz njega bez izmjene te datoteke. Odluka
korisnika 2026-08-12: zaseban `UPDATE` u `evaluator_agent.py`, koji nije zamrznut.

🔴 Kolona je isporučena PRAZNA u 5.0 uz izričit rok (§C.6a): ako je 5.1 ne popuni,
briše se. Ovi testovi su dokaz da je rok ispunjen — i čuvar da obrazac
`hint_requested` (kolona koju nitko ne piše, a izvozi se) ne dobije drugo izdanje.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete, select

from agents.evaluation import evaluate
from agents.evaluator_agent import persist_sqlstate
from agents.persistence import persist_attempt
from app.db.models import Attempt, Module, Task, User
from app.db.session import SessionLocal

_MODULE_NUMBER = 9805
_USERNAME = "sqlstate_test_user_51"
_EMAIL = "sqlstate_51@test.example"


@pytest.fixture
def sqlstate_env():
    with SessionLocal() as s:
        mod = Module(
            number=_MODULE_NUMBER,
            name="Test modul sqlstate 5.1",
            difficulty="beginner",
            order_index=_MODULE_NUMBER,
        )
        s.add(mod)
        s.flush()
        task = Task(
            module_id=mod.id,
            title="Test task sqlstate 5.1",
            description="sqlstate test task",
            sandbox_schema="ecommerce_v1",
            expected_query="SELECT id FROM products ORDER BY id LIMIT 2",
            expected_result=[{"id": 1}, {"id": 2}],
            difficulty=1,
        )
        s.add(task)
        s.flush()
        user = User(username=_USERNAME, email=_EMAIL, password_hash="dummy")
        s.add(user)
        s.commit()
        env = {"user_id": user.id, "task_id": task.id, "module_id": mod.id}

    yield env

    with SessionLocal() as c:
        c.execute(delete(Attempt).where(Attempt.user_id == env["user_id"]))
        c.execute(delete(User).where(User.id == env["user_id"]))
        c.execute(delete(Task).where(Task.id == env["task_id"]))
        c.execute(delete(Module).where(Module.id == env["module_id"]))
        c.commit()


def _run(env, query: str, sandbox_runner) -> int:
    """Odigraj put evaluatora: evaluate → persist_attempt → persist_sqlstate."""
    with SessionLocal() as s:
        task = s.get(Task, env["task_id"])
        outcome = evaluate(task, query, sandbox_runner)
        attempt_id = persist_attempt(
            s, env["user_id"], env["task_id"], query, outcome
        )
        persist_sqlstate(s, attempt_id, outcome.sqlstate)
    return attempt_id


def test_execution_error_writes_sqlstate(sqlstate_env, sandbox_runner) -> None:
    """🔴 Glavni zahtjev B1: poznata greška 42703 završi u retku."""
    aid = _run(sqlstate_env, "SELECT nepostojeci FROM products", sandbox_runner)

    with SessionLocal() as s:
        row = s.get(Attempt, aid)
        assert row.error_type == "execution_error"
        assert row.sqlstate == "42703"
        # `detail` i dalje nosi studentov tekst — zato i ne ide LLM-u.
        assert "nepostojeci" in row.detail


def test_grouping_error_writes_sqlstate(sqlstate_env, sandbox_runner) -> None:
    """42803 je koncept-nosivi kod (`group_by`, `having_filter`)."""
    aid = _run(
        sqlstate_env,
        "SELECT category_id, name, COUNT(*) FROM products GROUP BY category_id",
        sandbox_runner,
    )
    with SessionLocal() as s:
        assert s.get(Attempt, aid).sqlstate == "42803"


def test_correct_attempt_leaves_sqlstate_null(sqlstate_env, sandbox_runner) -> None:
    aid = _run(
        sqlstate_env, "SELECT id FROM products ORDER BY id LIMIT 2", sandbox_runner
    )
    with SessionLocal() as s:
        row = s.get(Attempt, aid)
        assert row.is_correct is True
        assert row.sqlstate is None


def test_result_mismatch_leaves_sqlstate_null(sqlstate_env, sandbox_runner) -> None:
    """Baza nije odbila upit → nema SQLSTATE-a. Guard protiv upisivanja smeća."""
    aid = _run(sqlstate_env, "SELECT id FROM products ORDER BY id LIMIT 5", sandbox_runner)
    with SessionLocal() as s:
        row = s.get(Attempt, aid)
        assert row.is_correct is False
        assert row.sqlstate is None


def test_persist_sqlstate_is_noop_without_code(sqlstate_env) -> None:
    """`persist_sqlstate(None)` ne smije ni dirati redak — bez UPDATE-a po pokušaju.

    Živo je samo ~3/13 pokušaja `execution_error`, pa bezuvjetni UPDATE bio bi
    trošak na svakom `POST /attempt` bez ijedne dobiti.
    """
    with SessionLocal() as s:
        att = Attempt(
            user_id=sqlstate_env["user_id"],
            task_id=sqlstate_env["task_id"],
            submitted_query="SELECT 1",
            is_correct=False,
            error_type="row_mismatch",
            attempt_number=99,
        )
        s.add(att)
        s.commit()
        aid = att.id
        assert persist_sqlstate(s, aid, None) is False

    with SessionLocal() as s:
        assert s.get(Attempt, aid).sqlstate is None


def test_persistence_module_is_untouched() -> None:
    """🔴 Odluka 8: `persist_attempt` NE zna za sqlstate.

    Ovo je izvršni oblik tvrdnje „persistence.py je byte-identičan" — `git diff`
    je izvan dosega testa, ali tvrdnja o SADRŽAJU nije.
    """
    import inspect

    import agents.persistence as p

    assert "sqlstate" not in inspect.getsource(p), (
        "persistence.py spominje sqlstate — zamrznuti put je diran (odluka 8)"
    )
