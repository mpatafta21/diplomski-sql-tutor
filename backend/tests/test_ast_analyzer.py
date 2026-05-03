"""Testovi za AstAnalyzer — concept detection u SQL queryjima."""

import pytest

from scripts.lib.ast_analyzer import AstAnalyzer, ConceptDetectionResult


@pytest.fixture
def analyzer() -> AstAnalyzer:
    return AstAnalyzer()


# ============================================================================
# TRIVIAL DETECTORS
# ============================================================================

def test_select_basic_positive(analyzer):
    r = analyzer.detects_concept("SELECT id, name FROM categories;", "select_basic")
    assert r.detected
    assert not r.extra_info["select_star_only"]


def test_select_basic_star_flagged(analyzer):
    r = analyzer.detects_concept("SELECT * FROM categories;", "select_basic")
    assert r.detected
    assert r.extra_info["select_star_only"]


def test_from_clause_positive(analyzer):
    r = analyzer.detects_concept("SELECT 1 FROM categories;", "from_clause")
    assert r.detected


def test_from_clause_only_in_comment(analyzer):
    r = analyzer.detects_concept("-- needs FROM later\nSELECT 1;", "from_clause")
    assert not r.detected
    assert r.is_in_comment


def test_where_filter_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT 1 FROM categories WHERE id > 0;", "where_filter"
    )
    assert r.detected


def test_where_filter_only_in_string(analyzer):
    r = analyzer.detects_concept(
        "SELECT 'WHERE clause' FROM categories;", "where_filter"
    )
    assert not r.detected


def test_order_by_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT id FROM categories ORDER BY id;", "order_by"
    )
    assert r.detected


def test_order_by_in_comment(analyzer):
    r = analyzer.detects_concept(
        "-- ORDER BY would go here\nSELECT id FROM categories;", "order_by"
    )
    assert not r.detected


def test_limit_offset_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT id FROM categories LIMIT 5;", "limit_offset"
    )
    assert r.detected


def test_limit_offset_only_in_string(analyzer):
    r = analyzer.detects_concept(
        "SELECT 'no LIMIT here' FROM categories;", "limit_offset"
    )
    assert not r.detected


def test_distinct_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT DISTINCT category_id FROM products;", "distinct"
    )
    assert r.detected


def test_distinct_in_comment(analyzer):
    r = analyzer.detects_concept(
        "-- DISTINCT\nSELECT category_id FROM products;", "distinct"
    )
    assert not r.detected


def test_group_by_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT category_id, COUNT(*) FROM products GROUP BY category_id;",
        "group_by",
    )
    assert r.detected


def test_group_by_in_comment(analyzer):
    r = analyzer.detects_concept(
        "-- GROUP BY\nSELECT category_id FROM products;", "group_by"
    )
    assert not r.detected


def test_having_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT cat FROM x GROUP BY cat HAVING COUNT(*) > 5;", "having_filter"
    )
    assert r.detected


def test_having_in_string(analyzer):
    r = analyzer.detects_concept("SELECT 'HAVING' FROM x;", "having_filter")
    assert not r.detected


def test_agg_count_positive(analyzer):
    r = analyzer.detects_concept("SELECT COUNT(*) FROM customers;", "agg_count")
    assert r.detected


def test_agg_count_in_comment(analyzer):
    r = analyzer.detects_concept(
        "-- COUNT here\nSELECT id FROM customers;", "agg_count"
    )
    assert not r.detected


def test_agg_sum_avg_positive(analyzer):
    r = analyzer.detects_concept("SELECT SUM(price) FROM products;", "agg_sum_avg")
    assert r.detected
    r2 = analyzer.detects_concept("SELECT AVG(price) FROM products;", "agg_sum_avg")
    assert r2.detected


def test_agg_sum_avg_in_string(analyzer):
    r = analyzer.detects_concept("SELECT 'SUM' FROM x;", "agg_sum_avg")
    assert not r.detected


def test_agg_min_max_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT MIN(price), MAX(price) FROM products;", "agg_min_max"
    )
    assert r.detected


def test_agg_min_max_in_comment(analyzer):
    r = analyzer.detects_concept("-- MIN MAX\nSELECT 1;", "agg_min_max")
    assert not r.detected


def test_insert_positive(analyzer):
    r = analyzer.detects_concept(
        "INSERT INTO categories (name) VALUES ('X');", "insert"
    )
    assert r.detected


def test_insert_in_comment(analyzer):
    r = analyzer.detects_concept("-- INSERT INTO x\nSELECT 1;", "insert")
    assert not r.detected


def test_update_positive(analyzer):
    r = analyzer.detects_concept(
        "UPDATE categories SET name = 'Y' WHERE id = 1;", "update"
    )
    assert r.detected


def test_update_in_string(analyzer):
    r = analyzer.detects_concept("SELECT 'UPDATE x SET y = 1' FROM t;", "update")
    assert not r.detected


def test_delete_positive(analyzer):
    r = analyzer.detects_concept("DELETE FROM categories WHERE id = 1;", "delete")
    assert r.detected


def test_delete_in_comment(analyzer):
    r = analyzer.detects_concept("-- DELETE FROM x\nSELECT 1;", "delete")
    assert not r.detected


def test_explain_plan_positive(analyzer):
    r = analyzer.detects_concept("EXPLAIN SELECT * FROM categories;", "explain_plan")
    assert r.detected


def test_explain_plan_not_at_start(analyzer):
    r = analyzer.detects_concept("SELECT 'EXPLAIN' FROM x;", "explain_plan")
    assert not r.detected


def test_null_handling_is_null(analyzer):
    r = analyzer.detects_concept(
        "SELECT id FROM orders WHERE employee_id IS NULL;", "null_handling"
    )
    assert r.detected


def test_null_handling_coalesce(analyzer):
    r = analyzer.detects_concept(
        "SELECT COALESCE(country, 'Unknown') FROM customers;", "null_handling"
    )
    assert r.detected


def test_null_handling_only_in_comment(analyzer):
    r = analyzer.detects_concept("-- IS NULL\nSELECT 1;", "null_handling")
    assert not r.detected


def test_column_alias_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT id AS customer_id FROM customers;", "column_alias"
    )
    assert r.detected


def test_column_alias_in_string(analyzer):
    r = analyzer.detects_concept("SELECT 'foo AS bar' FROM x;", "column_alias")
    assert not r.detected


def test_unknown_concept_raises_not_implemented(analyzer):
    with pytest.raises(NotImplementedError):
        analyzer.detects_concept("SELECT 1;", "totally_fake_concept_xyz")


# ============================================================================
# JOIN DETECTORS
# ============================================================================

def test_inner_join_explicit(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a INNER JOIN b ON a.id = b.a_id;", "inner_join"
    )
    assert r.detected


def test_inner_join_bare_join(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a JOIN b ON a.id = b.a_id;", "inner_join"
    )
    assert r.detected


def test_inner_join_NOT_when_left_join(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a LEFT JOIN b ON a.id = b.a_id;", "inner_join"
    )
    assert not r.detected


def test_left_join_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a LEFT JOIN b ON a.id = b.a_id;", "left_join"
    )
    assert r.detected


def test_left_outer_join_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a LEFT OUTER JOIN b ON a.id = b.a_id;", "left_join"
    )
    assert r.detected


def test_left_join_in_comment_only(analyzer):
    r = analyzer.detects_concept(
        "-- LEFT JOIN example\nSELECT * FROM a JOIN b ON a.id = b.a_id;",
        "left_join",
    )
    assert not r.detected


def test_right_join_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a RIGHT JOIN b ON a.id = b.a_id;", "right_join"
    )
    assert r.detected


def test_right_join_NOT_when_left(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a LEFT JOIN b ON a.id = b.a_id;", "right_join"
    )
    assert not r.detected


def test_right_outer_join_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a RIGHT OUTER JOIN b ON a.id = b.a_id;", "right_join"
    )
    assert r.detected


def test_full_outer_join_positive(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a FULL OUTER JOIN b ON a.id = b.a_id;", "full_outer_join"
    )
    assert r.detected


def test_full_join_short_form(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a FULL JOIN b ON a.id = b.a_id;", "full_outer_join"
    )
    assert r.detected


def test_full_outer_NOT_when_left(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a LEFT OUTER JOIN b ON a.id = b.a_id;", "full_outer_join"
    )
    assert not r.detected


def test_cross_join_positive(analyzer):
    r = analyzer.detects_concept("SELECT * FROM a CROSS JOIN b;", "cross_join")
    assert r.detected


def test_cross_join_NOT_when_inner(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a INNER JOIN b ON a.id = b.a_id;", "cross_join"
    )
    assert not r.detected


def test_cross_join_only_in_comment(analyzer):
    r = analyzer.detects_concept(
        "-- CROSS JOIN example\nSELECT * FROM a JOIN b ON 1=1;", "cross_join"
    )
    assert not r.detected


def test_join_condition_present(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a JOIN b ON a.id = b.a_id;", "join_condition"
    )
    assert r.detected


def test_join_condition_missing(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a, b WHERE a.id = b.a_id;", "join_condition"
    )
    assert not r.detected


def test_join_condition_only_in_comment(analyzer):
    r = analyzer.detects_concept(
        "-- ON a.id = b.id is the join condition\nSELECT 1 FROM x;",
        "join_condition",
    )
    assert not r.detected


def test_multi_table_join_3_tables(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a JOIN b ON a.id = b.a_id JOIN c ON b.id = c.b_id;",
        "multi_table_join",
    )
    assert r.detected
    assert r.extra_info["table_count"] == 3


def test_multi_table_join_NOT_when_2_tables(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a JOIN b ON a.id = b.a_id;", "multi_table_join"
    )
    assert not r.detected


def test_multi_table_join_4_tables(analyzer):
    r = analyzer.detects_concept(
        "SELECT * FROM a JOIN b ON a.id=b.a_id JOIN c ON b.id=c.b_id JOIN d ON c.id=d.c_id;",
        "multi_table_join",
    )
    assert r.detected
    assert r.extra_info["table_count"] == 4
