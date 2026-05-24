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

## INTERNI CHECKLIST (provedi mentalno PRIJE generiranja JSON-a — NE piši ovo u response):
1. Mentalno izvrši svoj `expected_query` na sandbox shemi
2. Provjeri da `expected_result` odgovara stvarnom rezultatu
3. Provjeri da `expected_query` stvarno koristi `{{concept_code}}` koncept (ne samo komentar/string, mora biti u FROM/JOIN/WHERE kontekstu)
4. Provjeri da koncept nije slučajno prisutan zbog drugog rješenja (npr. INNER JOIN slučajno daje isti rezultat kao LEFT JOIN za ovaj dataset)

**OUTPUT FORMAT (strict):**
Respond with ONLY a valid JSON object matching the schema above.
- DO NOT wrap the JSON in markdown code blocks (no ```json ... ``` fences)
- DO NOT include any explanation, preamble, or "reasoning" before/after the JSON
- DO NOT include comments inside the JSON
- The first character of your response MUST be `{` and the last character MUST be `}`
- If you need to think through the problem, do so internally — only the final JSON is your response

