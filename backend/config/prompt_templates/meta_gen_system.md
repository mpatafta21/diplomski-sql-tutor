# Meta-generation System Prompt Template

Ovaj dokument opisuje strategiju few-shot meta-generation-a za concept YAML config-ove.
Koristi se kao referenca — stvarni prompt se gradi dinamički u `scripts/lib/meta_gen.py`.

## Struktura prompta

### System prompt (cachiran — isti za sve 23 koncepta)

```
Ti si ekspert za SQL edukaciju koji generira YAML config fajlove za SQL koncepte.

Svaki config mora imati ova polja:
  - concept_code: snake_case, jedinstven identifikator koncepta
  - concept_name: puni naziv koncepta (npr. 'WHERE klauza')
  - module_number: broj modula (0-6)
  - module_name: naziv modula
  - tier: easy, medium ili hard
  - target_misconceptions: lista grešaka (min 1) s code, description, priority
  - domain_hints: lista savjeta vezanih uz sandbox shemu (min 1)
  - anti_patterns: lista čestih loših uzoraka (min 1)
  - required_for_high_difficulty: lista zahtjeva za teže verzije zadataka
  - few_shot_examples: lista primjera zadataka (min 1) s difficulty 1-5,
    title, description, expected_query, expected_concepts, targets_misconception
  - ast_validation_rules: lista pravila za AST provjeru (min 1)

Sandbox baza je PostgreSQL ecommerce_v1 s tablicama:
  customers (id, first_name, last_name, email, city, country, created_at)
  orders (id, customer_id, employee_id, order_date, status, total_amount)
  order_items (id, order_id, product_id, quantity, unit_price)
  products (id, name, category_id, price, stock_quantity, description)
  categories (id, name, description)
  employees (id, first_name, last_name, department, salary, manager_id, hire_date)

Hijerarhija zaposlenih: CEO (1) → VPs (4) → Managers (15) → Reps (30)
CEO nema managera (manager_id IS NULL).

Evo primjera dobro napisanih YAML config-ova:

--- PRIMJER: select_basic ---
[raw YAML iz config/concepts/select_basic.yaml]

--- PRIMJER: inner_join ---
[raw YAML iz config/concepts/inner_join.yaml]

[... svih 7 postojećih YAML-ova ...]
```

### User prompt (drugačiji po konceptu)

```
Generiraj YAML config za SQL koncept '{concept_code}'.

Meta informacije:
  module_number: {N}
  module_name: {naziv modula}
  tier: {easy|medium|hard}
  description: {kratak opis koncepta iz domenskog modela}

Obavezno:
  - concept_code mora biti točno: {concept_code}
  - module_number mora biti: {N}
  - module_name mora biti: {naziv modula}
  - tier mora biti: {easy|medium|hard}
  - expected_query u few_shot_examples mora biti validan SQL za ecommerce_v1 bazu
```

### Retry user prompt (ako schema validacija fail-a)

```
[Isti sadržaj kao gore, plus:]

⚠ SCHEMA ERROR iz prethodnog pokušaja — molim ispravi:
{error_message od ConceptConfig.model_validate()}

Generiraj ispravni config koji prolazi schema validaciju.
```

## Few-shot strategija

- Svih 7 postojećih YAML-ova (3 iz 2A + 4 iz 2B-1A) ubacuju se u system prompt
- System prompt se cachira (Anthropic prompt caching — isti za sve 23 generacije)
- Uštedak: ~90% input tokena od 2. generacije nadalje

## Trošak procjena

| Poziv | Input tokeni | Output tokeni | Cijena |
|-------|-------------|---------------|--------|
| 1. (fresh) | ~3500 | ~600 | ~$0.020 |
| 2.-23. (cached) | ~3500 cached + ~150 fresh | ~600 | ~$0.010 |
| Retry (s feedback) | ~3700 cached | ~600 | ~$0.010 |
| **Ukupno (23 + ~2 retry)** | | | **~$0.22** |

## Schema referenca

Puna schema se prosljeđuje kao `output_schema` u `generate_structured_output()`:
```python
schema = ConceptConfig.model_json_schema()
```

Anthropic tool-use API garantira da response odgovara ovoj schemi.
