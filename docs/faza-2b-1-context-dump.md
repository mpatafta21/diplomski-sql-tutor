# Faza 2B-1 — Context Dump (read-only snapshot, 2026-05-04 23:45 GMT+2)

## 1. YAML config sadržaj

### `backend/config/concepts/select_basic.yaml`
```yaml
concept_code: select_basic
concept_name: "Osnovni SELECT"
module_number: 1
module_name: "Osnove SELECT-a"
tier: easy

target_misconceptions:
  - code: "select_star_overuse"
    description: "Korištenje SELECT * umjesto eksplicitnih kolona"
    priority: critical
  - code: "missing_from"
    description: "Zaboravljen FROM clause"
    priority: high

domain_hints:
  - "Osnovni SELECT iz jedne tablice (categories, suppliers)"
  - "Eksplicitno biranje 2-3 kolona, ne SELECT *"
  - "Bez WHERE/JOIN-a (to su kasniji koncepti)"

anti_patterns:
  - "Ne pisi SELECT * kao očekivano rješenje"
  - "Ne dodavaj WHERE klauzu — to je where_filter koncept"
  - "Ne dodavaj ORDER BY — to je order_by koncept"

required_for_high_difficulty: []

few_shot_examples:
  - difficulty: 1
    title: "Naziv i opis svih kategorija"
    description: |
      Ispiši stupce name i description iz tablice categories.
    expected_query: |
      SELECT name, description FROM categories;
    expected_concepts: [select_basic, from_clause]
    targets_misconception: "select_star_overuse"

ast_validation_rules:
  - "expected_query mora imati top-level SELECT s eksplicitnim kolonama (ne *)"
  - "FROM klauza mora postojati"
```

### `backend/config/concepts/inner_join.yaml`
```yaml
concept_code: inner_join
concept_name: "INNER JOIN"
module_number: 3
module_name: "JOIN-ovi"
tier: medium

target_misconceptions:
  - code: "missing_join_condition"
    description: "JOIN bez ON klauze (Cartesian product)"
    priority: critical
  - code: "wrong_join_keys"
    description: "ON klauza koja spaja krive kolone (npr. customer.id = order.id)"
    priority: critical

domain_hints:
  - "Spajanje orders + customers preko customer_id"
  - "Spajanje order_items + products preko product_id"
  - "Spajanje products + categories preko category_id"

anti_patterns:
  - "Ne piši INNER JOIN gdje bi LEFT JOIN bio prirodniji (npr. 'svi kupci s narudžbama' isključuje 25 kupaca bez narudžbe — koristi LEFT JOIN za to)"
  - "Ne koristi implicitan join syntax (FROM a, b WHERE a.id = b.id) — eksplicitan JOIN"

required_for_high_difficulty:
  - "INNER JOIN preko 3+ tablica"
  - "INNER JOIN s agregacijom + GROUP BY"

few_shot_examples:
  - difficulty: 2
    title: "Narudžbe sa imenima kupaca"
    description: |
      Za svaku narudžbu ispiši order_id, order_date i ime kupca (first_name, last_name).
    expected_query: |
      SELECT o.id AS order_id, o.order_date, c.first_name, c.last_name
      FROM orders o
      INNER JOIN customers c ON o.customer_id = c.id
      ORDER BY o.id
      LIMIT 10;
    expected_concepts: [inner_join, from_clause, order_by, limit_offset, column_alias]
    targets_misconception: "missing_join_condition"

ast_validation_rules:
  - "expected_query mora sadržavati 'INNER JOIN' ili 'JOIN' (bez OUTER prefiksa) u FROM klauzi"
  - "ON klauza mora postojati"
```

### `backend/config/concepts/left_join.yaml`
```yaml
concept_code: left_join
concept_name: "LEFT OUTER JOIN"
module_number: 3
module_name: "JOIN-ovi"
tier: hard

target_misconceptions:
  - code: "left_join_vs_inner_with_null"
    description: "INNER JOIN umjesto LEFT JOIN — zadatak ne smije raditi s INNER JOIN-om"
    priority: critical
  - code: "filter_in_on_vs_where"
    description: "Filter u ON klauzi vs WHERE klauzi mijenja semantiku LEFT JOIN-a"
    priority: high
  - code: "anti_join_pattern"
    description: "LEFT JOIN + IS NULL za 'kupci bez narudžbi' tip zadataka"
    priority: critical

domain_hints:
  - "Anti-join scenariji: 25 customers BEZ orders (sandbox invariant)"
  - "Anti-join scenariji: products BEZ reviews"
  - "LEFT JOIN s agregacijom: 'broj narudžbi po kupcu, uključujući 0'"

anti_patterns:
  - "Ne piši zadatak gdje INNER JOIN slučajno daje isti rezultat kao LEFT JOIN"
  - "Ne koristi RIGHT JOIN umjesto LEFT JOIN bez razloga"
  - "expected_result MORA sadržavati NULL ili 0 vrijednosti gdje to ima smisla"

required_for_high_difficulty:
  - "Filter u ON vs WHERE distinkcija (zadatak demonstrira razliku)"
  - "LEFT JOIN s 3+ tablica (multi-table aspect)"
  - "Ili: LEFT JOIN + agregacija + HAVING kombinacija"

few_shot_examples:
  - difficulty: 4
    title: "Kupci bez ijedne narudžbe"
    description: |
      Pronađi sve kupce koji nikada nisu napravili narudžbu.
      Ispiši id, first_name, last_name i email.
    expected_query: |
      SELECT c.id, c.first_name, c.last_name, c.email
      FROM customers c
      LEFT JOIN orders o ON c.id = o.customer_id
      WHERE o.id IS NULL
      ORDER BY c.id;
    expected_concepts: [left_join, null_handling, where_filter]
    targets_misconception: "left_join_vs_inner_with_null"

ast_validation_rules:
  - "expected_query mora sadržavati 'LEFT JOIN' ili 'LEFT OUTER JOIN' u FROM klauzi"
  - "Za težinu ≥ 4: barem jedan od (IS NULL u WHERE, multi-table aspekt, filter u ON)"
```

### Keys tablica (top-level + nested)

| Key | Tip | Required | Nested keys | Prisutan u svim YAMLima? |
|-----|-----|----------|-------------|--------------------------|
| `concept_code` | str | da | — | da (sva 3) |
| `concept_name` | str | da | — | da |
| `module_number` | int | da | — | da |
| `module_name` | str | da | — | da |
| `tier` | str (`easy`/`medium`/`hard`) | da | — | da |
| `target_misconceptions` | list[obj] | da | `code`, `description`, `priority` (`critical`/`high`/...) | da |
| `domain_hints` | list[str] | da | — | da |
| `anti_patterns` | list[str] | da | — | da |
| `required_for_high_difficulty` | list[str] | da (može `[]`) | — | da |
| `few_shot_examples` | list[obj] | da | `difficulty` (int), `title` (str), `description` (str), `expected_query` (str), `expected_concepts` (list[str]), `targets_misconception` (str) | da |
| `ast_validation_rules` | list[str] | da | — | da, ali **nigdje nije konzumiran** (vidi §2) |

---

## 2. Schema usage analiza

### `backend/scripts/lib/prompt_builder.py` — concept YAML čitanja
| File:Line | Key čitan | Access pattern |
|-----------|-----------|----------------|
| `prompt_builder.py:46` | (file) | `self.concepts_dir / f"{concept_code}.yaml"` |
| `prompt_builder.py:50` | (load) | `yaml.safe_load(concept_path.read_text(...))` |
| `prompt_builder.py:89` | `target_misconceptions` | `concept.get("target_misconceptions", [])` → iterira po `m['priority']`, `m['code']`, `m['description']` |
| `prompt_builder.py:91` | `domain_hints` | `concept.get("domain_hints", [])` |
| `prompt_builder.py:92` | `anti_patterns` | `concept.get("anti_patterns", [])` |
| `prompt_builder.py:94` | `few_shot_examples` | `concept.get("few_shot_examples", [])` (yaml-dump-an inline u user prompt) |
| `prompt_builder.py:99–101` | `required_for_high_difficulty` | `concept.get("required_for_high_difficulty")` (truthy + d≥4 gate) |
| `prompt_builder.py:108` | `concept_code` | `concept["concept_code"]` (strict) |
| `prompt_builder.py:109` | `concept_name` | `concept["concept_name"]` (strict) |
| `prompt_builder.py:111` | `module_number` | `concept["module_number"]` (strict) |
| `prompt_builder.py:112` | `module_name` | `concept["module_name"]` (strict) |

`tier` i `ast_validation_rules` nisu konzumirani nigdje u pipeline-u (mrtve keys, ali prisutne u YAMLima).

### `backend/scripts/generate_tasks.py` — concept YAML loading
- Ne učitava YAML direktno. Sve ide kroz `PromptBuilder.build(concept, difficulty)` na liniji 81.
- CLI argument `--concept` je samo string (linija 175), bez whitelistanja — propušta se u builder gdje se podiže `ConceptNotFoundError` ako fajl ne postoji.
- **Nema validacije sadržaja YAML-a prije konzumacije** — ako neki key nedostaje, dobiva se ili `KeyError` (strict access za `concept_code`/`concept_name`/`module_*`) ili tihi prazni blok (`.get(...)` za misconceptions/hints/etc.).

### `backend/app/schemas/`
Sadrži samo `generated_task.py` (Pydantic schema za **LLM output**, ne za concept YAML).
- `app/schemas/concept_config.py`: **`<not found>`** ← 2B-1 ovo treba kreirati.

---

## 3. Test fixtures

### `backend/tests/test_prompt_builder.py`
- Loadira **prave** YAML-e iz `backend/config/concepts/` (ne mock):
  ```python
  PromptBuilder(
      concepts_config_dir=backend_root / "config" / "concepts",
      sandbox_context_path=backend_root / "config" / "sandbox_context.yaml",
      templates_dir=backend_root / "config" / "prompt_templates",
  )
  ```
- Pokriveni concepti: `inner_join` (d=2), `left_join` (d=2 i d=4), `nonexistent_concept` (negativni).
- Asertira sadržaj rendered prompt-a (npr. `"missing_join_condition" in pair.user`, `"Electronics" in pair.system`).
- **Nigdje nema inline dict fixture-a** za concept YAML — sve preko datoteke.

### `backend/tests/fixtures/`
- `__init__.py`
- `api_response_inner_join_d2.json` (mock LLM odgovora, koristi se u `test_generate_tasks_integration.py`)
- **Nema concept YAML fixture-a** — testovi koriste produkcijske YAML-e.

### `backend/tests/conftest.py`
- Definira `db_inspector` i `sandbox_connection_string` fixture. **Nema** YAML-related fixture-a.

---

## 4. `backend/config/sandbox_context.yaml` — struktura

| Top-level key | Tip | Veličina/sadržaj |
|---------------|-----|------------------|
| `schema_name` | str | `"ecommerce_v1"` |
| `tables` | list[obj] | 8 entry-ja (`categories`, `suppliers`, `products`, `customers`, `employees`, `orders`, `order_items`, `reviews`) — svaki ima `name`, `row_count` (int), `columns` (list[`{name, type}`]) |
| `key_invariants` | list[str] | 6 invariant-i (npr. "25 kupaca BEZ narudžbe", Faker seed=42) |
| `sample_rows` | dict[table_name → list[dict]] | po 3–5 redova za 8 tablica (Faker output) — **dodano u Fazi 2A za anti-halucinaciju** |
| `indexes` | list[str] | 8 string-ova (`idx_orders_customer ON ...`, ...) |

Komentari na vrhu označavaju izvor: `docker/postgres-sandbox/init.sql + scripts/seed_sandbox.py`.

---

## 5. Pydantic patterns u repu (`backend/app/schemas/`)

Jedini fajl: `generated_task.py`.

Patterni u upotrebi:
- **Pydantic v2 stil** (`pydantic>=2.0` u deps).
- `BaseModel` direktno (bez `model_config = ConfigDict(...)` — niti jedna postojeća schema ne koristi `ConfigDict`).
- `Field(..., min_length=N, max_length=N, ge=N, le=N)` — `min_length`/`max_length` (v2 ime, ne `min_items`).
- `Field(default_factory=list, max_length=2)` za list constraints.
- `Literal["ecommerce_v1"]` s default vrijednosti.
- Optional: `str | None = None` (PEP 604 syntax).
- Nested model: `GeneratedTaskMeta.task: GeneratedTask`.
- Validacija ulaza: `GeneratedTask.model_validate_json(raw_json)` (vidi `generate_tasks.py:97`).
- **Ne koristi se**: `Field(description=...)`, `model_validate` (samo `model_validate_json`), `field_validator`, `model_validator`, `ConfigDict`.

Style guide za novu `concept_config.py`: prati isti minimalan stil — `BaseModel`, `Field` constraints inline, PEP 604 unions, bez `ConfigDict` osim ako treba `extra="forbid"` (preporuka jer se YAML-ovi pišu ručno).

---

## 6. YAML tooling

| Stavka | Stanje |
|--------|--------|
| `pyyaml` u deps | da: `"pyyaml>=6.0"` u `[project].dependencies` |
| `ruamel.yaml` | `<not found>` u pyproject.toml |
| Loader | isključivo `yaml.safe_load` (`prompt_builder.py:30`, `prompt_builder.py:50`) |
| Dumper | `yaml.safe_dump(..., allow_unicode=True, sort_keys=False)` (`prompt_builder.py:93`) |
| Custom Loader | nema |
| Anchors/aliases | nigdje korišteni u postojeća 3 YAML-a |

---

## 7. Dependency check za 2B-1C (Streamlit)

- `streamlit` u `pyproject.toml`: **`<not found>`** (ni u `[project].dependencies`, ni u `[dependency-groups].dev`).
- Postojeći CLI tool kao referenca: `backend/scripts/generate_tasks.py` — argparse-based, no UI. **Nema** postojećeg Streamlit/UI tool-a u `backend/scripts/`.
- Drugi skripti u `backend/scripts/`: `generate_tasks.py`, `seed_sandbox.py`, `test_pyswip.py`, `test_spade.py`. Sve čiste CLI/skripte.

---

## 8. Git stanje

- Trenutni branch: **`main`**
- `git log faza-2a-complete..HEAD --oneline` (2 commita iza taga, oba post-2A housekeeping):
  ```
  97e6a7e feat(gitignore): add generated_tasks directory to .gitignore
  d58f664 Merge pull request #1 from mpatafta21/faza-2a-infrastruktura
  ```
- `git status`: `nothing to commit, working tree clean`
- Tagovi: `faza-1-complete`, `faza-1a-baza`, `faza-1b-prolog`, `faza-1c-bkt-sandbox`, `faza-2a-complete`.

---

## 9. Outputi 2A relevantni za 2B

`data/generated_tasks/`:
| Direktorij | Fajlovi (osim `.gitkeep`) |
|------------|---------------------------|
| `validated/` | `select_basic_d1_2fd7fa43.json` (1 task) |
| `failed/` | `select_basic_d1_7b5d1138.json`, `select_basic_d1_89fe430e.json` (2 taska) |
| `raw/` | (prazno) |

Ostalo:
- `data/generated_tasks/.gitignore` (postoji)
- `manual_review.sqlite`: **`<not found>`** (ne postoji)
- Cijeli direktorij `data/generated_tasks/` je gitignoran (commit `97e6a7e`) — JSON-ovi su lokalni artefakti, ne dijele se kroz git.

Naming pattern već uspostavljen: `{concept_code}_d{difficulty}_{uuid8}.json` (vidi `generate_tasks.py:165`).
