"""Integration testovi sheme — provjeravaju da je Alembic migracija
primijenila svih 16 tablica prema §6.2 DDL iz faza-1-domenski-model.md.
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
}


def test_all_16_tables_exist(db_inspector: Inspector) -> None:
    tables = set(db_inspector.get_table_names())
    missing = EXPECTED_TABLES - tables
    assert not missing, f"Nedostaju tablice: {missing}"


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
