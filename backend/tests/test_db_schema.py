"""Integration testovi sheme — provjeravaju da je Alembic migracija
primijenila svih 17 tablica prema §6.2 DDL iz faza-1-domenski-model.md.

17. tablica je ``hint_requests`` (Faza 5.0) — telemetrija zahtjeva za hintom.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, Inspector

EXPECTED_TABLES = {
    "users",
    "modules",
    "concepts",
    "concept_prerequisites",
    "tasks",
    "task_concepts",
    "attempts",
    "skill_mastery",
    "misconceptions",
    "badges",
    "user_badges",
    "xp_log",
    "streaks",
    "hints",
    "recommendations_log",
    "agent_messages_log",
    "hint_requests",
}


def test_all_17_tables_exist(db_inspector: Inspector) -> None:
    tables = set(db_inspector.get_table_names())
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Nedostaju tablice: {missing}"


def test_attempts_has_nullable_detail_column(db_inspector: Inspector) -> None:
    """attempts.detail (Faza 4.3 Stage 0b) — TEXT NULL; correct attempt nema detalj,
    stari redovi ostaju NULL (bez backfilla)."""
    cols = {c["name"]: c for c in db_inspector.get_columns("attempts")}
    assert "detail" in cols, "attempts.detail kolona nedostaje (migracija nije primijenjena?)"
    assert cols["detail"]["nullable"] is True


def test_users_has_unique_username_and_email(db_inspector: Inspector) -> None:
    unique_constraints = db_inspector.get_unique_constraints("users")
    indexes = db_inspector.get_indexes("users")
    unique_cols = {
        tuple(c["column_names"]) for c in unique_constraints
    } | {
        tuple(i["column_names"]) for i in indexes if i.get("unique")
    }
    assert ("username",) in unique_cols
    assert ("email",) in unique_cols


def test_concepts_code_is_unique(db_inspector: Inspector) -> None:
    unique_constraints = db_inspector.get_unique_constraints("concepts")
    indexes = db_inspector.get_indexes("concepts")
    unique_cols = {
        tuple(c["column_names"]) for c in unique_constraints
    } | {
        tuple(i["column_names"]) for i in indexes if i.get("unique")
    }
    assert ("code",) in unique_cols


def test_concept_prerequisites_composite_pk(db_inspector: Inspector) -> None:
    pk = db_inspector.get_pk_constraint("concept_prerequisites")
    assert set(pk["constrained_columns"]) == {"concept_id", "prerequisite_id"}


def test_task_concepts_composite_pk(db_inspector: Inspector) -> None:
    pk = db_inspector.get_pk_constraint("task_concepts")
    assert set(pk["constrained_columns"]) == {"task_id", "concept_id"}


def test_skill_mastery_composite_pk(db_inspector: Inspector) -> None:
    pk = db_inspector.get_pk_constraint("skill_mastery")
    assert set(pk["constrained_columns"]) == {"user_id", "concept_id"}


def test_user_badges_composite_pk(db_inspector: Inspector) -> None:
    pk = db_inspector.get_pk_constraint("user_badges")
    assert set(pk["constrained_columns"]) == {"user_id", "badge_id"}


def test_streaks_composite_pk(db_inspector: Inspector) -> None:
    pk = db_inspector.get_pk_constraint("streaks")
    assert set(pk["constrained_columns"]) == {"user_id", "date"}


def test_attempts_has_expected_indexes(db_inspector: Inspector) -> None:
    indexes = db_inspector.get_indexes("attempts")
    index_cols = [tuple(i["column_names"]) for i in indexes]
    assert ("user_id", "task_id") in index_cols
    assert ("user_id", "created_at") in index_cols


def test_users_xp_leaderboard_index(db_inspector: Inspector) -> None:
    indexes = db_inspector.get_indexes("users")
    assert any(
        tuple(i["column_names"]) == ("xp",) for i in indexes
    ), "Nedostaje index na users(xp) za leaderboard"


def test_agent_messages_log_bigint_pk(db_inspector: Inspector) -> None:
    cols = {c["name"]: c for c in db_inspector.get_columns("agent_messages_log")}
    # BigSerial u PG — reflektirani tip je instanca BigInteger bez obzira na repr
    assert isinstance(cols["id"]["type"], BigInteger)


# ---------------------------------------------------------------------------
# Faza 5.0 — hint_requests + attempts.sqlstate
# ---------------------------------------------------------------------------


def test_hint_requests_nullability(db_inspector: Inspector) -> None:
    """`hint_text` i `hint_id` su NULL-abilni, ostatak nije.

    🔴 `hint_text` MORA biti nullable: zahtjev koji je vratio 503 nema teksta, a
    upravo se te rupe mjere (`source='unavailable'`). CHECK ga veže uz `source`.
    """
    cols = {c["name"]: c for c in db_inspector.get_columns("hint_requests")}
    assert set(cols) == {
        "id",
        "user_id",
        "task_id",
        "after_attempt_id",
        "error_type",
        "source",
        "hint_id",
        "hint_text",
        "created_at",
    }
    nullable = {name: c["nullable"] for name, c in cols.items()}
    assert nullable["hint_text"] is True
    assert nullable["hint_id"] is True
    for required in ("user_id", "task_id", "after_attempt_id", "error_type", "source"):
        assert nullable[required] is False, f"{required} ne smije biti NULL-abilan"


def test_hint_requests_fk_ondelete(db_inspector: Inspector) -> None:
    """`user_id` i `after_attempt_id` CASCADE-aju; `task_id`/`hint_id` NE.

    CASCADE nosi brisanje demo usera BEZ izmjene `purge_demo_users.py`
    (v. test_purge_demo_users.py). `task_id` namjerno nema CASCADE — zadatak se
    ne briše ispod telemetrije.
    """
    fks = {
        tuple(fk["constrained_columns"]): fk
        for fk in db_inspector.get_foreign_keys("hint_requests")
    }
    assert fks[("user_id",)]["options"].get("ondelete") == "CASCADE"
    assert fks[("after_attempt_id",)]["options"].get("ondelete") == "CASCADE"
    assert not fks[("task_id",)]["options"].get("ondelete")
    assert not fks[("hint_id",)]["options"].get("ondelete")


def test_hint_requests_limit_index(db_inspector: Inspector) -> None:
    """Indeks (user_id, created_at DESC) — nosi izračun limita 5/4h pri čitanju."""
    by_cols = {
        tuple(i["column_names"]): i
        for i in db_inspector.get_indexes("hint_requests")
    }
    idx = by_cols.get(("user_id", "created_at"))
    assert idx is not None, f"Nema indeksa (user_id, created_at): {list(by_cols)}"
    assert idx["column_sorting"].get("created_at") == ("desc",)


def test_attempts_has_nullable_sqlstate_column(db_inspector: Inspector) -> None:
    """attempts.sqlstate (Faza 5.0, A1-dop-1) — VARCHAR(5) NULL, prazna do 5.1.

    Kolona stoji prazna: popunjava je tek 5.1 (sandbox_runner → EvaluationOutcome →
    persist_attempt). Ovdje se dokazuje samo da migracija ne treba drugu reviziju
    nad `attempts`.
    """
    cols = {c["name"]: c for c in db_inspector.get_columns("attempts")}
    assert "sqlstate" in cols, "attempts.sqlstate nedostaje"
    assert cols["sqlstate"]["nullable"] is True
    assert cols["sqlstate"]["type"].length == 5
