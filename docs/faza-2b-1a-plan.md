# FAZA 2B-1A — Akcijski plan

**Diplomski rad:** Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju
**Sub-faza:** 2B-1A od 7 (prva sub-podsekcija Faze 2B-1)
**Cilj:** Pydantic schema za concept YAML config + 4 ručno napisana YAML-a za najteže koncepte
**Trajanje:** ~2-3h aktivnog rada
**Workflow:** TDD red-green-refactor, code-review skill nakon glavnih komponenti
**Predviđeni broj git commit-ova:** 6-8

---

## 1. Kontekst i ciljevi

### 1.1 Što ova sub-faza radi

Sub-faza 2B-1A pripreme osnove za meta-generation 23 YAML-a u 2B-1B. Konkretno:

1. **Pydantic schema** (`ConceptConfig`) — minimalna ali strict validacija za sva 30 YAML config-a. Hvata typos, missing required fields, krivi tier values prije nego što idu u prompt builder ili meta-generation.
2. **Backfill 3 postojeća YAML-a** (`select_basic`, `inner_join`, `left_join`) ako schema otkrije nedostatke (očekivano: 0 promjena, već su konzistentni — ali validira se).
3. **4 ručno napisana YAML-a** za najteže koncepte: `correlated_subquery`, `multi_table_join`, `self_join`, `index_usage`. Ovi 4 služe i kao **dodatni few-shot examples** za 2B-1B meta-generation (3 sample → 7 sample = bolja kvaliteta meta-gen outputa).

### 1.2 Što ova sub-faza NE radi

- ❌ Meta-generation ostalih 23 YAML-a (to je 2B-1B)
- ❌ Validation tool (Streamlit + SQLite) — to je 2B-1C
- ❌ Pilot run za prompt template review — to je 2B-1B
- ❌ Bilo kakva izmjena postojećih `prompt_builder.py`, `task_validator.py`, `ast_analyzer.py` interface-a (samo opcionalno: dodati schema validation u prompt_builder, vidi §3.4)

### 1.3 Strateške odluke (zaključene, NE preispituje se)

| # | Odluka | Vrijednost |
|---|---|---|
| 1 | Schema strogost | Hibrid — minimalna schema, `extra="forbid"` za catch typos |
| 2 | `tier` i `ast_validation_rules` | **Required** (sve 3 postojeća YAML-a ih imaju, force-aj na nove) |
| 3 | Pydantic v2 stil | `BaseModel` + `Field` constraints + PEP 604 unions; `ConfigDict(extra="forbid")` IZNIMNO za concept config (catch typos) |
| 4 | YAML loader | `yaml.safe_load` (već u repu, ne uvodimo `ruamel.yaml`) |
| 5 | Backward compatibility | `prompt_builder.py` mora nastaviti raditi — sva strict access pattern (`concept["concept_code"]` etc.) ostaju identična |

---

## 2. Deliverables

### 2.1 Kod (3 fajla)

| Path | LoC (procjena) | Odgovornost |
|---|---|---|
| `backend/app/schemas/concept_config.py` | ~80 | `ConceptConfig`, `Misconception`, `FewShotExample` Pydantic modeli + helper `load_concept_config(path)` |
| `backend/scripts/lib/concept_loader.py` | ~40 | Wrapper koji `prompt_builder.py` može koristiti za schema-validated load (alternativa: inline u prompt_builder, vidi §3.4) |
| `backend/tests/test_concept_config.py` | ~150 | 12-15 testova: positive happy path, missing required keys, krivi tier value, duplicate misconception codes, negative whole-yaml |

### 2.2 YAML config-ovi (4 nova + 3 validirana)

| Path | Status | Tier | Source |
|---|---|---|---|
| `backend/config/concepts/select_basic.yaml` | **Validate only** (no changes) | easy | Postojeći iz 2A |
| `backend/config/concepts/inner_join.yaml` | **Validate only** | medium | Postojeći iz 2A |
| `backend/config/concepts/left_join.yaml` | **Validate only** | hard | Postojeći iz 2A |
| `backend/config/concepts/correlated_subquery.yaml` | **NEW** | hard | Ručno (ja pišem) |
| `backend/config/concepts/multi_table_join.yaml` | **NEW** | hard | Ručno |
| `backend/config/concepts/self_join.yaml` | **NEW** | hard | Ručno |
| `backend/config/concepts/index_usage.yaml` | **NEW** | hard | Ručno |

**Naming konvencija:** `<concept_code>.yaml` (snake_case, mapira 1:1 na Prolog `concept_code`).

### 2.3 Tests

- **12-15 unit testova** u `test_concept_config.py` (vidi §4 za detalje)
- **1 integration test** u `test_concept_config.py` koji loadira sve YAML-ove iz `backend/config/concepts/` kroz schemu i provjerava da svaki prolazi (sanity check da ne breakamo backward compat)
- **0 izmjena** na postojećim 132 testovima iz Faze 2A — sve moraju nastaviti raditi

### 2.4 Git artefakti

| Tag | Što označava |
|---|---|
| `faza-2b-1a-schema` | Schema + 12-15 testova prolaze, 3 postojeća YAML-a validirana |
| `faza-2b-1a-yamls` | 4 ručna YAML-a napisana i validirana kroz schemu |
| `faza-2b-1a-complete` | Final tag — sve gotovo, sve testovi prolaze (target: 132 + 13-16 novi = ~145-148) |

### 2.5 Verification (Milestone)

- [ ] Schema datoteka postoji (`app/schemas/concept_config.py`)
- [ ] Sva 7 YAML-a (`backend/config/concepts/*.yaml`) prolaze kroz schemu
- [ ] `pytest tests/test_concept_config.py` — 12-15 testova prolaze
- [ ] `pytest` ukupno — 145-148 testova prolaze (132 baseline + novi)
- [ ] `prompt_builder.py` nastavlja raditi unchanged (existing testovi `test_prompt_builder.py` prolaze)
- [ ] Tag `faza-2b-1a-complete` postavljen i push-an

---

## 3. Dizajn schema

### 3.1 `ConceptConfig` Pydantic model

```python
# backend/app/schemas/concept_config.py
"""
Pydantic schema za concept YAML config-ove (backend/config/concepts/*.yaml).

Validira strukturu, tipove, i required keys za sve concept config-ove
prije nego što idu u prompt builder ili meta-generation pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================
# Nested models
# ============================================================

class Misconception(BaseModel):
    """
    Jedna ciljana zabluda (target_misconception) za koncept.

    Primjer:
        code: "select_star_overuse"
        description: "Korištenje SELECT * umjesto eksplicitnih kolona"
        priority: "critical"
    """
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=3, max_length=80)
    description: str = Field(min_length=10, max_length=300)
    priority: Literal["critical", "high", "medium", "low"]


class FewShotExample(BaseModel):
    """
    Jedan few-shot primjer zadatka koji se ubacuje u user prompt
    kao referenca za stil/strukturu output-a.
    """
    model_config = ConfigDict(extra="forbid")

    difficulty: int = Field(ge=1, le=5)
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10)
    expected_query: str = Field(min_length=10)
    expected_concepts: list[str] = Field(min_length=1)
    targets_misconception: str = Field(min_length=3)


# ============================================================
# Top-level model
# ============================================================

class ConceptConfig(BaseModel):
    """
    Schema za jedan concept YAML config (backend/config/concepts/<code>.yaml).

    Required fields (sve, jer extra="forbid" — typos će raise-ati ValidationError):
      - concept_code, concept_name
      - module_number, module_name
      - tier (easy/medium/hard, mapira na BKT tier defaults)
      - target_misconceptions (>= 1)
      - domain_hints (>= 1)
      - anti_patterns (>= 1)
      - required_for_high_difficulty (može biti prazna lista)
      - few_shot_examples (>= 1)
      - ast_validation_rules (>= 1)
    """
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    concept_code: str = Field(min_length=3, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    concept_name: str = Field(min_length=3, max_length=100)
    module_number: int = Field(ge=0, le=6)  # 0 = transverzalni, 1-6 = moduli
    module_name: str = Field(min_length=3, max_length=100)
    tier: Literal["easy", "medium", "hard"]

    target_misconceptions: list[Misconception] = Field(min_length=1)
    domain_hints: list[str] = Field(min_length=1)
    anti_patterns: list[str] = Field(min_length=1)
    required_for_high_difficulty: list[str] = Field(default_factory=list)
    few_shot_examples: list[FewShotExample] = Field(min_length=1)
    ast_validation_rules: list[str] = Field(min_length=1)

    @field_validator("target_misconceptions")
    @classmethod
    def _unique_misconception_codes(cls, v: list[Misconception]) -> list[Misconception]:
        codes = [m.code for m in v]
        if len(codes) != len(set(codes)):
            raise ValueError("target_misconceptions sadrži duplikate u 'code' polju")
        return v


# ============================================================
# Loader helper
# ============================================================

class ConceptConfigError(Exception):
    """Raised when YAML doesn't conform to ConceptConfig schema."""


def load_concept_config(path: Path) -> ConceptConfig:
    """
    Učitava i validira concept YAML kroz ConceptConfig schemu.

    Args:
        path: Apsolutna putanja do YAML fajla.

    Returns:
        Validirani ConceptConfig instance.

    Raises:
        FileNotFoundError: Ako YAML fajl ne postoji.
        ConceptConfigError: Ako YAML ne prolazi schema validaciju.
    """
    if not path.exists():
        raise FileNotFoundError(f"Concept config not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ConceptConfigError(
            f"Concept config {path.name} mora biti YAML mapping (dict), "
            f"a ne {type(raw).__name__}"
        )

    try:
        return ConceptConfig.model_validate(raw)
    except Exception as exc:
        raise ConceptConfigError(
            f"Validation failed for {path.name}: {exc}"
        ) from exc
```

### 3.2 Ključne dizajn odluke

| Odluka | Razlog |
|---|---|
| `extra="forbid"` na svim modelima | Hvata typos kao `target_misconception` (singular) ili `domain_hint` umjesto `domain_hints`. Bez toga, typo postaje ignored field i schema lažno prolazi. |
| `pattern=r"^[a-z][a-z0-9_]*$"` na `concept_code` | Force snake_case — match-a Prolog atom konvenciju. Catch-uje krivi case (`InnerJoin`) ili razmake. |
| `module_number: int = Field(ge=0, le=6)` | 0 za transverzalne (`null_handling`, `column_alias`, `join_condition`), 1-6 za standardne module. Match-a `in_module/2` Prolog činjenice iz Faze 1. |
| `priority: Literal[...]` umjesto `str` | Hvata krivi value (`"hi"` umjesto `"high"`) na schema razini, ne u runtime check-u. |
| `str_strip_whitespace=True` | Whitespace u YAML-u (npr. trailing space u `concept_code`) se silently strip-uje. Pragmatično za hand-written YAML-ove. |
| `_unique_misconception_codes` validator | Duplicate `code` u `target_misconceptions` ne bi raise-ao bez ovoga (Pydantic ne dedup-a list itemse). |
| Bez validacije `expected_query` SQL syntax-a | Performance reason — to je posao `task_validator.py` u 2A, ne concept config schema. Ovdje samo `min_length`. |
| Bez validacije `expected_concepts` protiv Prolog ontology | Iz scope-a 2B-1A. Mogući future improvement: cross-validate s `concept/1` Prolog činjenicama (vidi §6 tech debt). |

### 3.3 Što schema NE valida (intentional out-of-scope)

| Stvar | Razlog | Gdje se valida (ako uopće) |
|---|---|---|
| SQL syntax u `expected_query` few-shot examples | `task_validator.py` već to radi | Faza 2A `task_validator.py` |
| Postoji li `concept_code` u Prolog ontology | Cross-system check, dodaje complexity | Future tech debt; manual check za sad |
| `expected_concepts` referencu valid concept codes | Isto kao gore | Future tech debt |
| `targets_misconception` postoji u `target_misconceptions` lista (cross-reference) | Korisno ali ne kritično | Mogu dodati validator ako se javi pattern bug-ova |

### 3.4 Integracija s `prompt_builder.py` — DEFER

**Odluka:** NE mijenjamo `prompt_builder.py` u 2B-1A. Schema je standalone, koristi se samo eksplicitno (npr. u testovima ili meta-generation skriptu).

**Razlog:** Prompt builder već radi (132 testa prolaze). Refactor da koristi `load_concept_config()` umjesto raw `yaml.safe_load` je 30 min rada + risk od regresija. Vrijednost (catch typos in YAMLs) ostvaruje se kroz nova test integracija (§4.4) — sva 7 YAML-a se loadiraju kroz schemu u test suite-u, što je dovoljan safety net.

**Ako u 2B-1B / 2B-2 zafali:** Refactor u tom trenutku, ne preventivno.

---

## 4. Tests (TDD plan)

### 4.1 Test struktura (`test_concept_config.py`)

Pratiti red-green-refactor: **prvo napiši failing test, pa minimalan code da prođe, pa cleanup**.

| # | Test ime | Što testira | Severity |
|---|---|---|---|
| 1 | `test_minimal_valid_config_loads` | Happy path — minimal valid YAML s svim required keys | Critical |
| 2 | `test_select_basic_yaml_loads` | Postojeći `select_basic.yaml` prolazi schemu (backward compat) | Critical |
| 3 | `test_inner_join_yaml_loads` | Postojeći `inner_join.yaml` prolazi | Critical |
| 4 | `test_left_join_yaml_loads` | Postojeći `left_join.yaml` prolazi | Critical |
| 5 | `test_missing_concept_code_raises` | Missing required `concept_code` → `ConceptConfigError` | High |
| 6 | `test_invalid_tier_raises` | `tier: "extreme"` → `ValidationError` (Literal mismatch) | High |
| 7 | `test_invalid_module_number_raises` | `module_number: 7` (out of 0-6) → error | High |
| 8 | `test_invalid_concept_code_pattern_raises` | `concept_code: "InnerJoin"` (PascalCase) → error | High |
| 9 | `test_extra_field_raises` | YAML s typos kao `target_misconception` (singular) → `ValidationError` | High |
| 10 | `test_empty_misconceptions_raises` | `target_misconceptions: []` → error (`min_length=1`) | Medium |
| 11 | `test_duplicate_misconception_codes_raises` | Dva misconceptiona s istim `code` → custom validator error | Medium |
| 12 | `test_invalid_priority_raises` | `priority: "hi"` → Literal mismatch | Medium |
| 13 | `test_few_shot_difficulty_out_of_range_raises` | `difficulty: 6` → `ValidationError` | Medium |
| 14 | `test_load_nonexistent_file_raises` | Path ne postoji → `FileNotFoundError` | Low |
| 15 | `test_load_yaml_list_raises` | YAML je list umjesto dict → `ConceptConfigError` | Low |
| 16 (integration) | `test_all_concept_yamls_validate` | Svi YAML-ovi u `backend/config/concepts/` prolaze schemu | **Critical** (regression net) |

### 4.2 Test fixtures

**Strategija:** Inline dict fixtures za negative tests (jer su mali), file-based za positive existing-YAML tests (jer testiramo backward compat).

```python
# tests/test_concept_config.py
import pytest
from pathlib import Path
from app.schemas.concept_config import ConceptConfig, ConceptConfigError, load_concept_config


CONCEPTS_DIR = Path(__file__).parent.parent / "config" / "concepts"


@pytest.fixture
def minimal_valid_config() -> dict:
    """Minimalan validan dict za happy path test."""
    return {
        "concept_code": "test_concept",
        "concept_name": "Test Concept",
        "module_number": 1,
        "module_name": "Test Module",
        "tier": "easy",
        "target_misconceptions": [
            {
                "code": "test_misconception",
                "description": "A test misconception for validation testing",
                "priority": "high",
            }
        ],
        "domain_hints": ["Test hint 1"],
        "anti_patterns": ["Test anti-pattern 1"],
        "required_for_high_difficulty": [],
        "few_shot_examples": [
            {
                "difficulty": 1,
                "title": "Test example",
                "description": "Test description for example",
                "expected_query": "SELECT 1;",
                "expected_concepts": ["test_concept"],
                "targets_misconception": "test_misconception",
            }
        ],
        "ast_validation_rules": ["Mock validation rule"],
    }
```

### 4.3 Postojeći testovi koji ne smiju puknuti

Nakon implementacije, run full test suite:

```bash
cd backend
uv run pytest -q
```

Očekivano: 132 baseline + 12-15 novi = **~145-148 prolaze**, **0 fails**.

Posebno paziti na:
- `tests/test_prompt_builder.py` (loadira prave produkcijske YAML-ove) — ako schema otkrije nedostatak u tim YAML-ima, treba popraviti YAML, ne schema.

### 4.4 Integration test pattern

```python
def test_all_concept_yamls_validate():
    """Regression net: svi production YAML-ovi prolaze schema."""
    yaml_files = list(CONCEPTS_DIR.glob("*.yaml"))
    assert len(yaml_files) >= 3, f"Expected ≥3 concept YAMLs, found {len(yaml_files)}"

    for yaml_path in yaml_files:
        try:
            config = load_concept_config(yaml_path)
            assert config.concept_code, f"Empty concept_code in {yaml_path.name}"
        except ConceptConfigError as e:
            pytest.fail(f"{yaml_path.name} failed schema validation: {e}")
```

Ovaj test će automatski uhvatiti probleme nakon dodavanja 4 nova YAML-a (§5).

---

## 5. Plan za 4 ručna YAML-a

### 5.1 Strategija pisanja

**Workflow po YAML-u (procjena 15-20 min):**
1. Pročitaj `faza-1-domenski-model.md` §2.2 za concept opis
2. Identificiraj 3-5 target_misconceptions iz literature ili iskustva
3. Napiši 1-2 few-shot examples koji **EXPLICITLY** demonstriraju jedan od misconceptiona u expected_query (counter-example pattern)
4. Lokalno testiraj: `uv run python -c "from app.schemas.concept_config import load_concept_config; from pathlib import Path; print(load_concept_config(Path('config/concepts/correlated_subquery.yaml')).concept_code)"`
5. Commit

### 5.2 Specifične napomene per concept

#### 5.2.1 `correlated_subquery.yaml` (tier: hard)

**Najteži koncept iz Faze 1 (§2.2):** "izvršavanje red-po-red, performance implikacije".

**Preporučeni sadržaj:**
- `target_misconceptions`:
  - `correlated_vs_uncorrelated_confusion` (critical) — student ne razumije razliku
  - `correlated_in_select_clause` (high) — koristi correlated subquery u SELECT umjesto JOIN-a
  - `forgot_outer_reference` (critical) — napiše uncorrelated subquery slučajno
- `few_shot_examples`: 2 (jedan d=4, jedan d=5)
  - d=4: "Pronađi sve narudžbe čija je `total_amount` veća od prosječne narudžbe tog kupca" (klasičan correlated)
  - d=5: "Top 3 najprodavanija proizvoda po kategoriji" (correlated u WHERE s LIMIT)
- `domain_hints`:
  - "Korelacija između outer i inner upit kroz alias outer tablice"
  - "Per-row evaluation — sandbox ima 200 customers + 1000 orders, performance treba paziti"
- `anti_patterns`:
  - "Ne napisi correlated subquery koji se može trivijalno zamijeniti JOIN+GROUP BY (anti-pattern u praksi)"
- `required_for_high_difficulty`:
  - "Korelacija eksplicitno preko outer alias (npr. `WHERE x.id = outer.id`)"

#### 5.2.2 `multi_table_join.yaml` (tier: hard)

**Iz Faze 1 (§2.2):** "krivi redoslijed JOIN-ova, krivi ON uvjeti, eksplozija kardinaliteta".

**Preporučeni sadržaj:**
- `target_misconceptions`:
  - `cardinality_explosion` (critical) — 4 tablice JOIN bez razumijevanja da svaki JOIN umnožava redove
  - `wrong_join_order_with_outer` (high) — kombinacija INNER + LEFT u krivom redoslijedu mijenja rezultat
  - `missing_join_for_filter_table` (critical) — student dodaje WHERE filter na tablicu koju nije JOIN-ao
- `few_shot_examples`: 2 (d=4, d=5)
  - d=4: "Imena kupaca, naziv proizvoda i kategorija za sve narudžbe iz 2024." (4 tablice: customers + orders + order_items + products + categories)
  - d=5: Kompliciraniji s 5+ tablica i mješovitim JOIN tipovima
- `required_for_high_difficulty`:
  - "Minimum 3 tablice u FROM klauzi"
  - "Barem jedan agregacijski stupac (COUNT, SUM) — testira da student razumije gdje GROUP BY ide"

#### 5.2.3 `self_join.yaml` (tier: hard)

**Iz Faze 1 (§2.2):** "alias management + self-reference (npr. zaposlenici i njihovi managerji)".

**Sandbox podrška:** `employees.manager_id` self-reference iz Faze 1 (§7.3).

**Preporučeni sadržaj:**
- `target_misconceptions`:
  - `missing_alias_in_self_join` (critical) — zaboravi alias, dobiva ambiguous column error
  - `self_join_without_join_keyword` (high) — koristi `FROM employees, employees` (implicit cross join)
  - `wrong_self_join_direction` (medium) — zamijeni manager i employee u ON klauzi
- `few_shot_examples`: 2
  - d=3: "Imena svih zaposlenika i imena njihovih managera"
  - d=5: "Pronađi sve zaposlenike koji zarađuju više od svog managera" (kombinira self-join + WHERE comparison)
- `domain_hints`:
  - "Sandbox ima `employees` tablicu s 50 zaposlenika i 4-razinskom hijerarhijom (CEO → VP → Manager → Rep)"
  - "Korisi alias-e `e` i `m` (employee, manager)"

#### 5.2.4 `index_usage.yaml` (tier: hard)

**Iz Faze 1 (§2.2):** "kada indeks pomaže, kada ne (npr. funkcija u WHERE klauzi poništava indeks)".

**Posebnost:** AST detector je placeholder iz 2A (vidi `faza-2a-wrapup.md` §4 errata). Tasks za ovaj koncept će se manualno validirati u 2B-3 (semantic check kroz EXPLAIN ANALYZE je izvan scope-a 2A).

**Preporučeni sadržaj:**
- `target_misconceptions`:
  - `function_on_indexed_column` (critical) — `WHERE LOWER(email) = ...` poništava indeks
  - `leading_wildcard_like` (high) — `WHERE name LIKE '%foo'` ne koristi indeks
  - `or_clause_index_loss` (medium) — `WHERE indexed_col = 1 OR other_col = 2` često ne koristi indeks
- `few_shot_examples`: 2 (oboje d=5, jer je tier expert)
  - d=5: "Napiši EXPLAIN za upit koji dohvaća sve narudžbe za kupca s ID 42, i objasni je li korišten indeks." (sandbox `idx_orders_customer` postoji)
  - d=5: Kontrast: "Napiši upit s `WHERE LOWER(email) = 'foo@bar.com'` i objasni zašto NE koristi indeks."
- `anti_patterns`:
  - "Ne piši zadatke koji zahtijevaju EXPLAIN ANALYZE output kao expected_result — sandbox runner ne podržava parsing plan output-a (out-of-scope za 2A AST analyzer)"
- `ast_validation_rules`:
  - "expected_query mora biti SELECT s WHERE klauzom na indexed column (vidi `docker/postgres-sandbox/init.sql` za listu indeksa)"
  - "**Napomena:** AST detector za index_usage je placeholder u 2A — manual review obavezan u 2B-3"

### 5.3 Validation workflow nakon pisanja svakog YAML-a

```bash
cd backend

# Single YAML test
uv run python -c "
from app.schemas.concept_config import load_concept_config
from pathlib import Path
config = load_concept_config(Path('config/concepts/correlated_subquery.yaml'))
print(f'✓ Loaded: {config.concept_code} ({config.tier})')
print(f'  Misconceptions: {len(config.target_misconceptions)}')
print(f'  Examples: {len(config.few_shot_examples)}')
"

# Full integration check
uv run pytest tests/test_concept_config.py::test_all_concept_yamls_validate -v
```

---

## 6. Tehnološki dug i out-of-scope items

### 6.1 Što namjerno ostavljamo za buduće faze

| Stavka | Razlog defer-a | Rok |
|---|---|---|
| `prompt_builder.py` refactor da koristi `load_concept_config()` | Risk od regresija; 132 testa već prolaze; integration test je dovoljan safety net | 2B-1B ako zafali, inače Faza 3 |
| Cross-validation `concept_code` protiv Prolog `concept/1` | Cross-system check, dodaje complexity; manual verify za sad | Faza 3 ili po potrebi |
| Cross-validation `expected_concepts` protiv Prolog ontology | Isto kao gore | Faza 3 |
| Cross-validation `targets_misconception` ⊆ `target_misconceptions[].code` | Korisno ali ne kritično, dodajem ako se javi pattern bugova | Reactive |
| AST detector za `index_usage` | Iz 2A errata — placeholder, EXPLAIN ANALYZE parsing je posao Modul 6 / Faza 6 | Faza 6 |
| `secondary_concepts` field u concept config | Nije postojao u 2A YAML-ima; unclear use case | Faza 2B-2 ako pattern emergne iz generation run-a |

### 6.2 Otvorene odluke koje će 2B-1B trebati

- Hoće li meta-generation skript (`scripts/meta_generate_yamls.py`) koristiti `ConceptConfig.model_json_schema()` kao structured output spec? Vrlo vjerojatno DA, ali to se odlučuje u 2B-1B planu.
- Treba li dodati `Field(description=...)` na svaki field kako bi LLM imao bolji kontekst u structured output? Trade-off između schema verbosity i meta-gen kvalitete.

---

## 7. Implementacijski redoslijed (TDD)

**Workflow:** Striktno TDD. Svaki korak je commit. Nakon svakog koraka — `uv run pytest -q`, target zelena.

### Korak 1: Schema skeleton + happy path test

**Branch:** `faza-2b-1a-schema`

1. Napiši test `test_minimal_valid_config_loads` (RED — fail jer schema ne postoji)
2. Napiši `app/schemas/concept_config.py` s `ConceptConfig`, `Misconception`, `FewShotExample` — minimal version (GREEN)
3. Refactor: dodaj docstring-e, type hints
4. Commit: `feat(2b-1a): ConceptConfig Pydantic schema + minimal happy path test`

### Korak 2: Backward compat — postojeći YAML-ovi loadiraju

1. Napiši `test_select_basic_yaml_loads`, `test_inner_join_yaml_loads`, `test_left_join_yaml_loads` (RED ako schema fali nešto što YAML-ovi imaju)
2. Adjust schema dok sva 3 ne prolaze (GREEN)
3. **Critical decision point:** ako YAML-ovi imaju nešto što schema ne podržava, **adjust schema**, ne YAML — backward compat je sveti gral u ovoj fazi
4. Commit: `feat(2b-1a): backward compat — sva 3 postojeća YAML-a prolaze schemu + 3 testa`

### Korak 3: Negative tests + custom validator

1. Napiši preostale negative testove (testovi 5-15 iz §4.1) — svi RED na početku
2. Implementiraj `_unique_misconception_codes` validator
3. Implementiraj `load_concept_config` helper s `ConceptConfigError`
4. GREEN za sve testove
5. Commit: `feat(2b-1a): negative tests + duplicate codes validator + loader helper`

### Korak 4: Integration test (regression net)

1. Napiši `test_all_concept_yamls_validate` (PASS jer trenutno samo 3 YAML-a prolaze)
2. Commit: `test(2b-1a): integration test za sve concept YAML-ove`
3. **Tag:** `git tag faza-2b-1a-schema && git push origin faza-2b-1a-schema`

### Korak 5: Code review checkpoint

**Pokrenuti code review skill** na schema kodu prije pisanja YAML-ova. Fokus:
- Edge cases u `_unique_misconception_codes` (empty list?)
- Error message kvaliteta u `load_concept_config` (jasan path + razlog?)
- Pydantic v2 best practices (koristim li `field_validator` ispravno?)
- Concurrency (ne treba — nije concern)

Ako review pronađe HIGH severity findings, napravi cleanup commit prije nastavka.

### Korak 6: Pisanje 4 ručna YAML-a

**Branch (isti):** `faza-2b-1a-schema`

Po YAML-u:
1. Pročitaj relevantnu sekciju iz `faza-1-domenski-model.md` §2.2
2. Pogledaj jedan postojeći YAML kao template (npr. `left_join.yaml` za hard tier)
3. Napiši YAML prema preporukama iz §5.2 ovog plana
4. Lokalno validate: `uv run python -c "..."` (vidi §5.3)
5. Run full test suite: `uv run pytest -q` — `test_all_concept_yamls_validate` mora prolaziti
6. Commit per YAML: `feat(2b-1a): correlated_subquery.yaml — hard tier, 3 misconceptions, 2 examples`

Redoslijed: `correlated_subquery` → `multi_table_join` → `self_join` → `index_usage` (od najsličnijeg s postojećim do najdrugačijeg).

### Korak 7: Final tag

1. Run full test suite: `uv run pytest -q` — verificiraj **145-148 prolazi**
2. Update `faza-2a-wrapup.md` errata? (Optional — možda dodaj kratku napomenu da je schema dodana)
3. Push svi commit-ovi
4. **Tag:** `git tag faza-2b-1a-complete && git push origin faza-2b-1a-complete`

---

## 8. Entry kriteriji (start 2B-1A)

- [x] Faza 2A zaključena (tag `faza-2a-complete`)
- [x] 173 testova prolazi baseline (41 + 132)
- [x] Postojeća 3 YAML-a u `backend/config/concepts/`
- [x] `pyyaml`, `pydantic>=2.0` u deps
- [x] WSL Ubuntu environment ready
- [x] Git radni direktorij čist (`git status` clean)
- [x] Trenutni branch: `main`

## 9. Exit kriteriji (kraj 2B-1A)

- [ ] `app/schemas/concept_config.py` napisan i pokriven testovima
- [ ] 4 nova YAML-a (`correlated_subquery`, `multi_table_join`, `self_join`, `index_usage`) napisana i validirana
- [ ] Sva 7 YAML-ova prolazi `test_all_concept_yamls_validate`
- [ ] **145-148 testova prolazi** (vs. 173 baseline... wait, 173 - 41 = 132 baseline 2A... revidirana brojka: ~145 ako računamo sve, jer 41 baseline iz 1 + 132 iz 2A = 173 ukupno + 12-15 novi = 185-188)
- [ ] Tagovi `faza-2b-1a-schema` i `faza-2b-1a-complete` postavljeni i push-ani
- [ ] **0 promjena** u `prompt_builder.py`, `task_validator.py`, `ast_analyzer.py` interfaces

**Korekcija test broja:** Baseline na startu 2B-1A je **173 testova** (41 iz Faze 1 + 132 iz Faze 2A). Nakon 2B-1A očekivano: **185-188 testova prolazi**.

---

## 10. Risk register

| Rizik | Vjerojatnost | Impact | Mitigacija |
|---|---|---|---|
| Postojeći 3 YAML-a ne prolaze schemu (npr. `description` prekratak) | Low | Medium | Adjust schema constraints (npr. `min_length=10` → `min_length=5`); ne mijenjati YAML |
| `prompt_builder.py` testovi puknu zbog whitespace strip-anja | Low | Medium | `str_strip_whitespace=True` može mijenjati exact string match-eve. Jednostavni fix: ukloniti tu opciju ako razbije test |
| 4 nova YAML-a ne mogu pokriti sve potrebne misconceptione | Medium | Low | OK je imati 2-3 misconceptiona po YAML-u. Više se može dodavati u 2B-2 ako se uoči |
| Pisanje 4 YAML-a traje >2h | Medium | Low | Akceptabilno; cap je 4h ukupno za sub-fazu |
| Code review pronađe HIGH findings koji zahtijevaju veći refactor | Low | Medium | Buffer u koraku 5 je već uračunat |

---

## 11. Reference

- `faza-1-domenski-model.md` §2.2 — concept descriptions, misconception kandidati za 4 ručna YAML-a
- `faza-2a-wrapup.md` §4 errata + §5 tech debt — kontekst za prompt template review (ne radi se ovdje)
- `faza-2b-1-context-dump.md` — stvarna struktura postojećih YAML-a, schema usage, Pydantic style guide
- `backend/app/schemas/generated_task.py` — referenca za Pydantic v2 stil u repu
- Pydantic v2 dokumentacija — `ConfigDict`, `field_validator`, `Literal` za Pydantic enums

---

## 12. Što slijedi nakon 2B-1A

**2B-1B — Pilot run + meta-gen 23 YAML-a:**
- Napisati `scripts/meta_generate_yamls.py` koji koristi `ConceptConfig.model_json_schema()` za structured output
- Pilot run: 2 tasks po concept tipu (~12 tasks total, ~$0.10) za prompt template review
- Meta-generation 23 YAML-a koristeći 7 sample-a (3 postojeća + 4 ručna iz 2B-1A) kao few-shot
- Schema validation svih 23 generated YAML-a kroz `load_concept_config()`
- Manual cleanup gdje treba

**2B-1C — Validation tool (Streamlit + SQLite):**
- Streamlit web UI s decisions buttons + filter + run query button
- SQLite persistence za review decisions
- Dependency: dodati `streamlit` u `pyproject.toml`

---

*Plan kraj. Korak za pokrenuti 2B-1A: `git checkout -b faza-2b-1a-schema && uv run pytest -q` (verify clean baseline).*
