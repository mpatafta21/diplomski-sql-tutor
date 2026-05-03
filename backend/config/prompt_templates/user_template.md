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

## PRIJE NEGO VRATIŠ JSON:
1. Mentalno izvrši svoj `expected_query` na sandbox shemi
2. Provjeri da `expected_result` odgovara stvarnom rezultatu
3. Provjeri da `expected_query` stvarno koristi `{{concept_code}}` koncept (ne samo komentar/string, mora biti u FROM/JOIN/WHERE kontekstu)
4. Provjeri da koncept nije slučajno prisutan zbog drugog rješenja (npr. INNER JOIN slučajno daje isti rezultat kao LEFT JOIN za ovaj dataset)
