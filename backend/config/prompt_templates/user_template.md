Generiraj 1 SQL zadatak za sljedeću specifikaciju:

**Concept:** {{concept_code}} ({{concept_name}})
**Težina:** {{difficulty}} (skala 1-5)
**Modul:** {{module_number}} - {{module_name}}

## Targeted misconceptions (ovaj zadatak mora vježbati barem jedan critical):

{{misconceptions_block}}

## Domain hints (preporučeni dijelovi sandbox sheme):

{{domain_hints_block}}

## Anti-patterns (NE radi ovo):

{{anti_patterns_block}}

## Few-shot examples za ovaj koncept:

{{few_shot_block}}

{{high_difficulty_block}}

## IMPORTANT CONSTRAINTS:
- `secondary_concepts` MUST contain at most 2 concept codes (NOT more)
- `secondary_concepts` MUST NOT include the primary concept (no duplicates)
- `secondary_concepts` MUST be different concepts that the task ALSO exercises

## VERIFICATION CHECKLIST (use your thinking block — `<thinking>` tags or extended thinking budget — to work through ALL of these BEFORE writing the JSON):

1. **Write out `expected_query` step-by-step.** What rows match the WHERE/JOIN conditions? Walk row-by-row against SAMPLE ROWS and KEY INVARIANTS. If aggregation, compute it explicitly (e.g. "5 customers from Croatia × 1 order avg = 5 rows").

2. **Derive `expected_result` from THAT execution.** Do NOT guess. Do NOT use placeholder rows. If you can't enumerate the result deterministically from the schema/sample data, **rewrite the query to be deterministic** (add `ORDER BY id LIMIT N`, switch to a COUNT/SUM that's invariant-based).

3. **Verify `expected_query` syntactically USES `{{concept_code}}`.**
   - For SQL keyword concepts (RIGHT JOIN, GROUP BY, EXPLAIN): the literal keyword(s) MUST appear in the query (not in comments/strings — in actual SQL position).
   - For pattern concepts (scalar_subquery, correlated_subquery): the structural pattern MUST be present (e.g. scalar_subquery = `(SELECT ... FROM ... WHERE ...)` in SELECT list or comparison).
   - For `explain_plan`: query MUST start with `EXPLAIN` or `EXPLAIN (ANALYZE, ...)`.
   - If you wrote a query that gives a correct answer but uses a DIFFERENT concept → rewrite using `{{concept_code}}`, even if less elegant.

4. **Confirm the concept is essential, not incidental.** Would the same `expected_result` come out if you swapped `{{concept_code}}` for an alternative (e.g. INNER JOIN instead of LEFT JOIN)? If yes, change the data filter so the concept becomes load-bearing.

**OUTPUT FORMAT (strict — applies to the FINAL response, not the thinking block):**
Respond with ONLY a valid JSON object matching the schema above.
- DO NOT wrap the JSON in markdown code blocks (no ```json ... ``` fences)
- DO NOT include any explanation, preamble, or "reasoning" before/after the JSON
- DO NOT include comments inside the JSON
- The first character of your response MUST be `{` and the last character MUST be `}`
- All checklist work above belongs in your thinking block, NOT in the response


