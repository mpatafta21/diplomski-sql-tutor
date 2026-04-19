% ============================================================
% ontology.pl — činjenice o SQL konceptima i njihovim svojstvima
% Sub-faza 1B: 30 koncepata, 7 modula (1..6 + 0 transverzalni),
%              30 in_module mapping, 30 tier, 38 prerequisite
% ============================================================

% --- Moduli (7: 1..6 + 0 transverzalni) ---
module_name(0, 'Transverzalni').
module_name(1, 'Osnove SELECT-a').
module_name(2, 'Agregacije i grupiranje').
module_name(3, 'JOIN-ovi').
module_name(4, 'DML operacije').
module_name(5, 'Podupiti').
module_name(6, 'Optimizacija i indeksi').

% --- Koncepti (30) ---
% Modul 1 — Osnove SELECT-a (6)
concept(select_basic).
concept(from_clause).
concept(where_filter).
concept(order_by).
concept(limit_offset).
concept(distinct).

% Modul 2 — Agregacije (5)
concept(group_by).
concept(having_filter).
concept(agg_count).
concept(agg_sum_avg).
concept(agg_min_max).

% Modul 3 — JOIN-ovi (7)
concept(inner_join).
concept(left_join).
concept(right_join).
concept(full_outer_join).
concept(cross_join).
concept(self_join).
concept(multi_table_join).

% Modul 4 — DML (3)
concept(insert).
concept(update).
concept(delete).

% Modul 5 — Podupiti (4)
concept(scalar_subquery).
concept(in_subquery).
concept(exists_subquery).
concept(correlated_subquery).

% Modul 6 — Optimizacija (2)
concept(explain_plan).
concept(index_usage).

% Transverzalni (3) — modul 0
concept(null_handling).
concept(column_alias).
concept(join_condition).

% --- Mapping koncept → modul (30) ---
in_module(select_basic, 1).
in_module(from_clause, 1).
in_module(where_filter, 1).
in_module(order_by, 1).
in_module(limit_offset, 1).
in_module(distinct, 1).

in_module(group_by, 2).
in_module(having_filter, 2).
in_module(agg_count, 2).
in_module(agg_sum_avg, 2).
in_module(agg_min_max, 2).

in_module(inner_join, 3).
in_module(left_join, 3).
in_module(right_join, 3).
in_module(full_outer_join, 3).
in_module(cross_join, 3).
in_module(self_join, 3).
in_module(multi_table_join, 3).

in_module(insert, 4).
in_module(update, 4).
in_module(delete, 4).

in_module(scalar_subquery, 5).
in_module(in_subquery, 5).
in_module(exists_subquery, 5).
in_module(correlated_subquery, 5).

in_module(explain_plan, 6).
in_module(index_usage, 6).

in_module(null_handling, 0).
in_module(column_alias, 0).
in_module(join_condition, 0).

% --- Tier (za BKT default parametre) (30) ---
tier(select_basic, easy).
tier(from_clause, easy).
tier(where_filter, easy).
tier(order_by, easy).
tier(limit_offset, easy).
tier(distinct, easy).
tier(column_alias, easy).
tier(insert, easy).

tier(group_by, medium).
tier(having_filter, medium).
tier(agg_count, medium).
tier(agg_sum_avg, medium).
tier(agg_min_max, medium).
tier(inner_join, medium).
tier(join_condition, medium).
tier(null_handling, medium).
tier(update, medium).
tier(delete, medium).
tier(scalar_subquery, medium).
tier(in_subquery, medium).
tier(exists_subquery, medium).

tier(left_join, hard).
tier(right_join, hard).
tier(full_outer_join, hard).
tier(cross_join, hard).
tier(self_join, hard).
tier(multi_table_join, hard).
tier(correlated_subquery, hard).
tier(explain_plan, hard).
tier(index_usage, hard).

% --- Prerequisites (38 rubova, prema §3.2 dokumenta) ---
prerequisite(from_clause, select_basic).
prerequisite(where_filter, from_clause).
prerequisite(order_by, where_filter).
prerequisite(limit_offset, where_filter).
prerequisite(distinct, select_basic).
prerequisite(column_alias, select_basic).
prerequisite(null_handling, where_filter).
prerequisite(group_by, where_filter).
prerequisite(group_by, column_alias).
prerequisite(having_filter, group_by).
prerequisite(agg_count, group_by).
prerequisite(agg_count, null_handling).
prerequisite(agg_sum_avg, group_by).
prerequisite(agg_min_max, group_by).
prerequisite(join_condition, from_clause).
prerequisite(inner_join, join_condition).
prerequisite(cross_join, join_condition).
prerequisite(left_join, inner_join).
prerequisite(left_join, null_handling).
prerequisite(right_join, inner_join).
prerequisite(full_outer_join, left_join).
prerequisite(full_outer_join, right_join).
prerequisite(self_join, inner_join).
prerequisite(multi_table_join, inner_join).
prerequisite(multi_table_join, where_filter).
prerequisite(insert, select_basic).
prerequisite(insert, from_clause).
prerequisite(update, where_filter).
prerequisite(delete, where_filter).
prerequisite(scalar_subquery, where_filter).
prerequisite(scalar_subquery, select_basic).
prerequisite(in_subquery, scalar_subquery).
prerequisite(in_subquery, null_handling).
prerequisite(exists_subquery, scalar_subquery).
prerequisite(correlated_subquery, scalar_subquery).
prerequisite(explain_plan, multi_table_join).
prerequisite(explain_plan, group_by).
prerequisite(index_usage, explain_plan).

% --- Covers (placeholder za Fazu 2) ---
% covers(TaskID, [Concept1, Concept2, ...])
% Primjer: covers(task_001, [select_basic, from_clause, where_filter]).

% --- Difficulty (placeholder za Fazu 2) ---
% difficulty(TaskID, Level) where Level in 1..5
% Primjer: difficulty(task_001, 1).
