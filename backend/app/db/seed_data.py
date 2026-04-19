"""Master podaci za seed skriptu.

Izvor: docs/faza-1-domenski-model.md §2.2 (koncepti), §3.2 (prerequisite).
Redoslijed modula i koncepata replicira tablicu iz dokumenta.
"""

from __future__ import annotations

from typing import TypedDict


class ModuleSeed(TypedDict):
    number: int
    name: str
    description: str
    difficulty: str
    order_index: int


class ConceptSeed(TypedDict):
    code: str
    name: str
    module_number: int  # resolved u module_id preko query-a
    tier: str
    description: str
    order_index: int


class BadgeSeed(TypedDict):
    code: str
    name: str
    description: str
    icon: str
    rule: str
    xp_reward: int


MODULES: list[ModuleSeed] = [
    {
        "number": 0,
        "name": "Transverzalni",
        "description": "Koncepti koji prolaze kroz više modula (NULL handling, aliasi, ON klauza).",
        "difficulty": "cross_module",
        "order_index": 7,
    },
    {
        "number": 1,
        "name": "Osnove SELECT-a",
        "description": "Projekcija, FROM, WHERE, ORDER BY, LIMIT, DISTINCT.",
        "difficulty": "beginner",
        "order_index": 1,
    },
    {
        "number": 2,
        "name": "Agregacije i grupiranje",
        "description": "GROUP BY, HAVING, COUNT, SUM/AVG, MIN/MAX.",
        "difficulty": "intermediate",
        "order_index": 2,
    },
    {
        "number": 3,
        "name": "JOIN-ovi",
        "description": "INNER/LEFT/RIGHT/FULL/CROSS/SELF JOIN i multi-table join.",
        "difficulty": "intermediate",
        "order_index": 3,
    },
    {
        "number": 4,
        "name": "DML operacije",
        "description": "INSERT, UPDATE, DELETE.",
        "difficulty": "advanced",
        "order_index": 4,
    },
    {
        "number": 5,
        "name": "Podupiti",
        "description": "Skalarni, IN, EXISTS, korelirani podupit.",
        "difficulty": "advanced",
        "order_index": 5,
    },
    {
        "number": 6,
        "name": "Optimizacija",
        "description": "EXPLAIN plan, korištenje indeksa (bonus razina).",
        "difficulty": "expert",
        "order_index": 6,
    },
]


# 30 koncepata prema §2.2. order_index je redoslijed unutar modula.
CONCEPTS: list[ConceptSeed] = [
    # Modul 1
    {"code": "select_basic", "name": "Osnovni SELECT", "module_number": 1, "tier": "easy", "description": "Projekcija stupaca.", "order_index": 1},
    {"code": "from_clause", "name": "FROM klauzula", "module_number": 1, "tier": "easy", "description": "Identifikacija tablice.", "order_index": 2},
    {"code": "where_filter", "name": "WHERE filtriranje", "module_number": 1, "tier": "easy", "description": "Filtriranje redova.", "order_index": 3},
    {"code": "order_by", "name": "ORDER BY", "module_number": 1, "tier": "easy", "description": "Sortiranje rezultata.", "order_index": 4},
    {"code": "limit_offset", "name": "LIMIT / OFFSET", "module_number": 1, "tier": "easy", "description": "Paginacija.", "order_index": 5},
    {"code": "distinct", "name": "DISTINCT", "module_number": 1, "tier": "easy", "description": "Uklanjanje duplikata.", "order_index": 6},
    # Modul 2
    {"code": "group_by", "name": "GROUP BY", "module_number": 2, "tier": "medium", "description": "Grupiranje.", "order_index": 1},
    {"code": "having_filter", "name": "HAVING", "module_number": 2, "tier": "medium", "description": "Filtriranje grupa.", "order_index": 2},
    {"code": "agg_count", "name": "COUNT", "module_number": 2, "tier": "medium", "description": "Brojanje redova (i s NULL).", "order_index": 3},
    {"code": "agg_sum_avg", "name": "SUM / AVG", "module_number": 2, "tier": "medium", "description": "Numerička redukcija.", "order_index": 4},
    {"code": "agg_min_max", "name": "MIN / MAX", "module_number": 2, "tier": "medium", "description": "Ekstremne vrijednosti.", "order_index": 5},
    # Modul 3
    {"code": "inner_join", "name": "INNER JOIN", "module_number": 3, "tier": "medium", "description": "Najčešći JOIN.", "order_index": 1},
    {"code": "left_join", "name": "LEFT OUTER JOIN", "module_number": 3, "tier": "hard", "description": "OUTER JOIN s NULL-popunom lijeve strane.", "order_index": 2},
    {"code": "right_join", "name": "RIGHT OUTER JOIN", "module_number": 3, "tier": "hard", "description": "Simetričan LEFT-u.", "order_index": 3},
    {"code": "full_outer_join", "name": "FULL OUTER JOIN", "module_number": 3, "tier": "hard", "description": "Unija LEFT i RIGHT.", "order_index": 4},
    {"code": "cross_join", "name": "CROSS JOIN", "module_number": 3, "tier": "medium", "description": "Kartezijev produkt.", "order_index": 5},
    {"code": "self_join", "name": "SELF JOIN", "module_number": 3, "tier": "hard", "description": "JOIN tablice sa samom sobom.", "order_index": 6},
    {"code": "multi_table_join", "name": "JOIN 3+ tablica", "module_number": 3, "tier": "hard", "description": "Višestruki JOIN-ovi.", "order_index": 7},
    # Modul 4
    {"code": "insert", "name": "INSERT", "module_number": 4, "tier": "medium", "description": "Unos podataka.", "order_index": 1},
    {"code": "update", "name": "UPDATE", "module_number": 4, "tier": "medium", "description": "Izmjena podataka.", "order_index": 2},
    {"code": "delete", "name": "DELETE", "module_number": 4, "tier": "medium", "description": "Brisanje podataka.", "order_index": 3},
    # Modul 5
    {"code": "scalar_subquery", "name": "Skalarni podupit", "module_number": 5, "tier": "hard", "description": "Podupit koji vraća 1 vrijednost.", "order_index": 1},
    {"code": "in_subquery", "name": "IN / NOT IN", "module_number": 5, "tier": "hard", "description": "Membership test, 3-valued logika s NULL.", "order_index": 2},
    {"code": "exists_subquery", "name": "EXISTS / NOT EXISTS", "module_number": 5, "tier": "hard", "description": "Test egzistencije.", "order_index": 3},
    {"code": "correlated_subquery", "name": "Korelirani podupit", "module_number": 5, "tier": "hard", "description": "Vanjska referenca, izvršavanje red-po-red.", "order_index": 4},
    # Modul 6
    {"code": "explain_plan", "name": "EXPLAIN čitanje", "module_number": 6, "tier": "hard", "description": "Analiza query plana.", "order_index": 1},
    {"code": "index_usage", "name": "Korištenje indeksa", "module_number": 6, "tier": "hard", "description": "Kada indeks pomaže, kada ne.", "order_index": 2},
    # Transverzalni (module 0)
    {"code": "null_handling", "name": "NULL handling", "module_number": 0, "tier": "hard", "description": "IS NULL, COALESCE, NULLIF — prerequisite za LEFT JOIN, NOT IN, COUNT.", "order_index": 1},
    {"code": "column_alias", "name": "AS za stupce", "module_number": 0, "tier": "easy", "description": "Preimenovanje stupaca.", "order_index": 2},
    {"code": "join_condition", "name": "ON klauza", "module_number": 0, "tier": "medium", "description": "Semantika uvjeta spajanja; filter u ON vs WHERE.", "order_index": 3},
]


# Prerequisite rubovi prema §3.2. Format: (koncept, prerequisite).
PREREQUISITES: list[tuple[str, str]] = [
    ("from_clause", "select_basic"),
    ("where_filter", "from_clause"),
    ("order_by", "where_filter"),
    ("limit_offset", "where_filter"),
    ("distinct", "select_basic"),
    ("column_alias", "select_basic"),
    ("null_handling", "where_filter"),
    ("group_by", "where_filter"),
    ("group_by", "column_alias"),
    ("having_filter", "group_by"),
    ("agg_count", "group_by"),
    ("agg_count", "null_handling"),
    ("agg_sum_avg", "group_by"),
    ("agg_min_max", "group_by"),
    ("join_condition", "from_clause"),
    ("inner_join", "join_condition"),
    ("cross_join", "join_condition"),
    ("left_join", "inner_join"),
    ("left_join", "null_handling"),
    ("right_join", "inner_join"),
    ("full_outer_join", "left_join"),
    ("full_outer_join", "right_join"),
    ("self_join", "inner_join"),
    ("multi_table_join", "inner_join"),
    ("multi_table_join", "where_filter"),
    ("insert", "select_basic"),
    ("insert", "from_clause"),
    ("update", "where_filter"),
    ("delete", "where_filter"),
    ("scalar_subquery", "where_filter"),
    ("scalar_subquery", "select_basic"),
    ("in_subquery", "scalar_subquery"),
    ("in_subquery", "null_handling"),
    ("exists_subquery", "scalar_subquery"),
    ("correlated_subquery", "scalar_subquery"),
    ("explain_plan", "multi_table_join"),
    ("explain_plan", "group_by"),
    ("index_usage", "explain_plan"),
]


# 5 placeholder bedževa — stvarna pravila u Prolog-u dolaze u Fazi 3.
BADGES: list[BadgeSeed] = [
    {
        "code": "first_correct",
        "name": "Prvi uspjeh",
        "description": "Prvi točno riješen zadatak.",
        "icon": "star",
        "rule": "user_badge(UserID, first_correct) :- attempt(UserID, _, correct).",
        "xp_reward": 10,
    },
    {
        "code": "join_master",
        "name": "Majstor JOIN-ova",
        "description": "Ovladan svim JOIN konceptima (P(L) >= 0.85).",
        "icon": "link",
        "rule": "user_badge(UserID, join_master) :- forall(member(C, [inner_join, left_join, right_join]), mastered(UserID, C)).",
        "xp_reward": 50,
    },
    {
        "code": "streak_7",
        "name": "Tjedni streak",
        "description": "7 uzastopnih dana aktivnosti.",
        "icon": "fire",
        "rule": "user_badge(UserID, streak_7) :- current_streak(UserID, N), N >= 7.",
        "xp_reward": 30,
    },
    {
        "code": "null_ninja",
        "name": "NULL Ninja",
        "description": "Ovladano NULL handling — prerequisite za mnogo koncepata.",
        "icon": "ghost",
        "rule": "user_badge(UserID, null_ninja) :- mastered(UserID, null_handling).",
        "xp_reward": 25,
    },
    {
        "code": "explorer",
        "name": "Istraživač",
        "description": "Pokušao zadatke iz svih 6 modula.",
        "icon": "compass",
        "rule": "user_badge(UserID, explorer) :- forall(between(1, 6, M), attempted_in_module(UserID, M)).",
        "xp_reward": 40,
    },
]
