# FAZA 2A — Infrastruktura generatora SQL zadataka

**Diplomski rad:** Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju
**Faza:** 2A od 7 (Sub-faza A od Faze 2)
**Trajanje:** 2-3 dana
**Preduvjeti:** Faza 1 zaključena (`faza-1-complete` tag), sandbox baza s 4895 redaka radi, 30 koncepata seedani
**Milestone:** Generiranje 1 zadatka prolazi cijeli pipeline (API → parse → validate → JSON file output) bez upisa u bazu

---

## 1. Cilj Faze 2A

Izgraditi **infrastrukturu** za pozivanje Anthropic Claude API-ja, parsing odgovora, automatsku validaciju (sintaksa + concept coverage + result match) i strukturirano spremanje generiranih zadataka. Ne pokreće full generation run — to je Faza 2B.

Faza 2A je "alat radi i znamo da radi". Faza 2B je "alat producira zadatke". Faza 2C je "zadaci ulaze u bazu i Prolog".

### 1.1 Što je out-of-scope za 2A

- Pokretanje generacije za svih 105 zadataka (Faza 2B)
- Ručna validacija od strane korisnika (Faza 2B)
- Upis u `tasks` i `task_concepts` tablice (Faza 2C)
- Ažuriranje Prolog `covers/2` i `difficulty/2` činjenica (Faza 2C)

### 1.2 Strateške odluke iz prethodnih chatova (zaključeno)

| Odluka | Vrijednost |
|---|---|
| Ukupno zadataka (target Faza 2B) | 105 dediciranih (buffer za odbijene) |
| Strategija koncept-po-zadatku | Primary + 1-2 secondary |
| Modul 6 zadataka | 6 (3 explain_plan + 3 index_usage) |
| Transverzalni KC | null_handling 5 dediciranih, column_alias/join_condition samo secondary |
| Validacijski workflow | Inline validacija s regenerate na fail (max 3 retry) |
| Ručna validacija | Sve 105 prolazi korisnik (Faza 2B) |
| LLM model | `claude-sonnet-4-6` |
| Extended thinking | Da, za težinu 4-5 |
| API access | $5 starter credit (~$2 stvarni trošak Faze 2) |
| Per-concept config | YAML/JSON sa svih 30 koncepata |
| Sandbox kontekst u promptu | Full schema + invariante iz Faze 1 |
| Jezik task descriptiona | Hrvatski s engleskim SQL terminima |
| Concept coverage validacija | AST + semantika (sqlparse) |

---

## 2. Distribucijska matrica zadataka (referenca za Fazu 2B)

| # | Concept | Module | Tier | Ded. | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | select_basic | 1 | easy | 4 | 2 | 1 | 1 | 0 | 0 |
| 2 | from_clause | 1 | easy | 3 | 2 | 1 | 0 | 0 | 0 |
| 3 | where_filter | 1 | easy | 5 | 2 | 2 | 1 | 0 | 0 |
| 4 | order_by | 1 | easy | 3 | 1 | 1 | 1 | 0 | 0 |
| 5 | limit_offset | 1 | easy | 3 | 1 | 1 | 1 | 0 | 0 |
| 6 | distinct | 1 | easy | 3 | 1 | 1 | 1 | 0 | 0 |
| 7 | group_by | 2 | medium | 5 | 1 | 1 | 2 | 1 | 0 |
| 8 | having_filter | 2 | medium | 4 | 0 | 1 | 2 | 1 | 0 |
| 9 | agg_count | 2 | medium | 4 | 1 | 1 | 1 | 1 | 0 |
| 10 | agg_sum_avg | 2 | medium | 3 | 0 | 1 | 1 | 1 | 0 |
| 11 | agg_min_max | 2 | medium | 3 | 1 | 1 | 1 | 0 | 0 |
| 12 | inner_join | 3 | medium | 5 | 1 | 1 | 2 | 1 | 0 |
| 13 | left_join | 3 | hard | 6 | 0 | 1 | 2 | 2 | 1 |
| 14 | right_join | 3 | hard | 3 | 0 | 1 | 1 | 1 | 0 |
| 15 | full_outer_join | 3 | hard | 3 | 0 | 0 | 1 | 1 | 1 |
| 16 | cross_join | 3 | hard | 2 | 0 | 1 | 1 | 0 | 0 |
| 17 | self_join | 3 | hard | 4 | 0 | 0 | 1 | 2 | 1 |
| 18 | multi_table_join | 3 | hard | 5 | 0 | 0 | 2 | 2 | 1 |
| 19 | insert | 4 | easy | 3 | 1 | 1 | 1 | 0 | 0 |
| 20 | update | 4 | medium | 4 | 0 | 1 | 2 | 1 | 0 |
| 21 | delete | 4 | medium | 4 | 0 | 1 | 2 | 1 | 0 |
| 22 | scalar_subquery | 5 | medium | 4 | 0 | 1 | 2 | 1 | 0 |
| 23 | in_subquery | 5 | medium | 4 | 0 | 1 | 1 | 2 | 0 |
| 24 | exists_subquery | 5 | medium | 3 | 0 | 1 | 1 | 1 | 0 |
| 25 | correlated_subquery | 5 | hard | 4 | 0 | 0 | 1 | 2 | 1 |
| 26 | explain_plan | 6 | hard | 3 | 0 | 0 | 1 | 1 | 1 |
| 27 | index_usage | 6 | hard | 3 | 0 | 0 | 1 | 1 | 1 |
| 28 | null_handling | 0 | medium | 5 | 1 | 1 | 2 | 1 | 0 |
| 29 | column_alias | 0 | easy | 0 | — | — | — | — | — |
| 30 | join_condition | 0 | medium | 0 | — | — | — | — | — |

**Total: 105 dediciranih zadataka.** Ova matrica je referenca za Fazu 2B; Faza 2A ne pokreće generation, samo testira pipeline na 1-2 sample zadatka.

---

## 3. Arhitektura komponenti

### 3.1 File structure

```
backend/
├── scripts/
│   ├── generate_tasks.py           # CLI entrypoint (Faza 2A)
│   └── lib/
│       ├── __init__.py
│       ├── api_client.py           # Anthropic SDK wrapper
│       ├── prompt_builder.py       # Assembly prompta iz YAML config-a
│       ├── task_validator.py       # Inline validacija (3 razine)
│       ├── sandbox_runner.py       # Izvršavač queryja u sandbox-u
│       └── ast_analyzer.py         # AST + semantika analiza s sqlparse
├── config/
│   ├── concepts/                   # YAML config po konceptu (30 fajlova)
│   │   ├── select_basic.yaml
│   │   ├── from_clause.yaml
│   │   ├── ...
│   │   └── join_condition.yaml
│   ├── sandbox_context.yaml        # Schema + invariante za prompt
│   └── prompt_templates/
│       ├── system_static.md        # Cacheable system prompt (anti-halucinacija, format)
│       └── user_template.md        # Per-task user message template
├── app/
│   └── schemas/
│       └── generated_task.py       # Pydantic schema za LLM output (NOVO)
└── tests/
    ├── test_api_client.py
    ├── test_prompt_builder.py
    ├── test_task_validator.py
    ├── test_sandbox_runner.py
    └── test_ast_analyzer.py
```

### 3.2 Pipeline overview

```
generate_tasks.py --concept inner_join --difficulty 3 --count 1 --dry-run
    │
    ├─→ prompt_builder.build(concept_yaml, sandbox_context, difficulty)
    │       └─→ system + user messages
    │
    ├─→ api_client.generate(messages, model=sonnet-4-6, extended_thinking=False)
    │       └─→ raw response (JSON in text)
    │
    ├─→ TaskGenerationOutput.model_validate_json(...)   # Pydantic schema
    │
    ├─→ task_validator.validate(parsed_task)
    │       ├─→ syntax_check (sqlparse)
    │       ├─→ concept_coverage_check (ast_analyzer)
    │       └─→ result_match_check (sandbox_runner)
    │
    ├─→ if pass: save to data/generated_tasks/raw/{concept}_{difficulty}_{uuid}.json
    │   if fail: log to data/generated_tasks/failed/ + retry (max 3)
    │
    └─→ summary stats: success_count, failure_reasons, retries
```

---

## 4. Komponente — interface specifikacije

### 4.1 `api_client.py`

**Odgovornost:** Tanak wrapper oko Anthropic SDK-a. Retry logika, prompt caching, extended thinking conditional, error handling.

**Public interface:**

```python
class AnthropicClient:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6") -> None: ...

    def generate(
        self,
        system: str,                        # Cacheable system prompt
        user_message: str,                  # Per-task user message
        extended_thinking: bool = False,    # True za težinu 4-5
        max_tokens: int = 4096,
    ) -> AnthropicResponse:
        """
        Vraća strukturirani response s text content + token usage.
        Raises AnthropicAPIError ako API fail (rate limit, auth, network).
        """
        ...

@dataclass
class AnthropicResponse:
    content: str                # Plain text iz response.content[0].text
    input_tokens: int
    output_tokens: int
    cached_tokens: int          # Tokens read from cache
    stop_reason: str            # "end_turn" | "max_tokens" | ...
```

**Implementation napomene:**

- Koristi `anthropic` Python SDK (`pip install anthropic`)
- System prompt ide kroz `system` parametar s `cache_control={"type": "ephemeral"}` na zadnjem bloku — to omogućuje 90% off na cached input
- Extended thinking enable preko `thinking={"type": "enabled", "budget_tokens": 2000}` (samo za težinu 4-5)
- Retry logika: 3 retry-eva s exponential backoff (1s, 2s, 4s) za rate limit (429) i transient errors (5xx)
- API ključ čita iz `os.environ["ANTHROPIC_API_KEY"]` (učitan kroz python-dotenv)

**Test coverage (test_api_client.py):**

- Mock `anthropic.Anthropic` klijent (koristi `pytest-mock` ili `unittest.mock`)
- Test 1: Uspješan poziv vraća AnthropicResponse s ispravnim poljima
- Test 2: Rate limit (429) trigger-a retry, treći put uspjeva
- Test 3: Auth error (401) NE trigger-a retry, raise odmah
- Test 4: Cached tokens se ispravno parse-aju iz response-a
- Test 5: Extended thinking flag dodaje `thinking` parameter

---

### 4.2 `prompt_builder.py`

**Odgovornost:** Sastavlja system + user prompt iz YAML config-a po konceptu i sandbox context-a.

**Public interface:**

```python
class PromptBuilder:
    def __init__(
        self,
        concepts_config_dir: Path,          # backend/config/concepts/
        sandbox_context_path: Path,          # backend/config/sandbox_context.yaml
        templates_dir: Path,                 # backend/config/prompt_templates/
    ) -> None: ...

    def build(
        self,
        concept_code: str,                  # npr. "left_join"
        difficulty: int,                    # 1-5
    ) -> PromptPair:
        """
        Učita concept YAML, sandbox context, render-a templates.
        Vraća (system, user) tuple.
        """
        ...

@dataclass
class PromptPair:
    system: str                 # Cacheable, ~1500-2000 tokena
    user: str                   # Per-task, ~600-1000 tokena
```

**System prompt sadržaj (cacheable):**

```
[ROLE]
Ti si SQL pedagoški generator zadataka za adaptivno e-learning sustav.

[ANTI-HALLUCINATION RULES]
- expected_result MORA biti rezultat koji se DOBIJE iz expected_query izvršenog
  na sandbox shemi koja ti je dana, ne nešto što ti zvuči realno
- Ako nisi siguran u expected_result, OBAVEZNO mentalno izvršiš query na shemi
- Ne izmišljaj imena, brojke, datume — koristi distribuciju iz "key invariants"

[OUTPUT FORMAT]
Vraćaj samo validan JSON koji prati ovaj schema:
{schema_definition}

[SANDBOX SCHEMA]
{full_DDL_8_tables}

[KEY INVARIANTS]
- 25 kupaca BEZ ijedne narudžbe
- 30% orders.employee_id su NULL (self-service)
- ~5 narudžbi po kupcu u prosjeku
- Categories: 15, Products: 100, Orders: 1000, Order items: 3000
- Hijerarhija employees: 4 razine (CEO → VP → Manager → Rep)
- Faker seed=42 (reproducibilno)

[LANGUAGE]
- Title i description: hrvatski s engleskim SQL terminima
- Naslov: < 100 znakova, descriptive
- Description: 2-3 rečenice, jasan, bez ambiguity-ja

[GENERAL ANTI-PATTERNS]
- Ne traži SELECT * kao očekivano rješenje (osim ako koncept to opravdava)
- Ne pisuj zadatke gdje LIMIT bez ORDER BY (nedeterministički)
- Pazi na multiple valid solutions — opisuj eksplicitno koju strukturu očekuješ
```

**User prompt sadržaj (per-task):**

```
Generiraj 1 SQL zadatak za sljedeću specifikaciju:

Concept: {concept_code} ({concept_name})
Težina: {difficulty} (skala 1-5)
Modul: {module_number} - {module_name}

Targeted misconceptions koje ovaj zadatak mora vježbati:
{misconceptions_list}

Domain hints (preporučeni dijelovi sandbox sheme):
{domain_hints}

Anti-patterns (NE radi ovo):
{anti_patterns}

Few-shot examples za ovaj koncept:
{few_shot_examples_yaml}

[ako je težina ≥ 4]
Dodatni zahtjevi za težinu 4-5:
{required_for_high_difficulty}

PRIJE NEGO VRATIŠ JSON:
1. Mentalno izvrši svoj expected_query na sandbox shemi
2. Provjeri da expected_result odgovara stvarnom rezultatu
3. Provjeri da expected_query stvarno koristi {concept_code} koncept
   (ne smije biti samo komentar, mora biti u FROM/JOIN/WHERE kontekstu)
4. Provjeri da koncept nije samo slučajno prisutan zbog drugog rješenja
   (npr. INNER JOIN slučajno daje isti rezultat kao LEFT JOIN za neke podatke)
```

**Test coverage (test_prompt_builder.py):**

- Test 1: build("inner_join", 2) vraća non-empty system + user
- Test 2: System prompt sadrži sandbox DDL i invariante
- Test 3: User prompt sadrži misconceptions iz YAML config-a
- Test 4: Težina 4-5 dodaje "Dodatni zahtjevi" sekciju
- Test 5: Težina 1-3 ne dodaje "Dodatni zahtjevi"
- Test 6: Few-shot examples se renderaju iz YAML-a
- Test 7: build() raise ako concept_code ne postoji u config-u
- Test 8: build() raise ako difficulty out-of-range (< 1 or > 5)

---

### 4.3 `task_validator.py`

**Odgovornost:** Inline validacija LLM outputa kroz 3 razine. Vraća strukturiran ValidationResult.

**Public interface:**

```python
class TaskValidator:
    def __init__(
        self,
        sandbox_runner: SandboxRunner,
        ast_analyzer: AstAnalyzer,
    ) -> None: ...

    def validate(
        self,
        task: GeneratedTask,            # Pydantic-validated LLM output
    ) -> ValidationResult:
        """
        Pokreće 3 razine validacije u redoslijedu.
        Stops on prvi fail (cijenovno učinkovito).
        """
        ...

@dataclass
class ValidationResult:
    passed: bool
    failures: list[ValidationFailure]   # Praznje ako passed=True
    warnings: list[str]                 # Non-blocking issues

@dataclass
class ValidationFailure:
    level: Literal["syntax", "concept_coverage", "result_match"]
    code: str                           # "wrong_join_type", "result_row_mismatch"
    message: str                        # Detaljno za logging
    details: dict                       # Debug info
```

**Tri razine validacije (po redu):**

**Razina 1 — Syntax check**
- `sqlparse.parse(expected_query)` parses without error
- Query nije prazan
- Query nema SQL injection patterns (DROP, TRUNCATE bez WHERE — security paranoia)

**Razina 2 — Concept coverage check** (delegira na `ast_analyzer`)
- Primarni koncept eksplicitno prisutan u SQL kontekstu (ne komentar/string)
- Provjera per-concept pravila (vidi 4.5)

**Razina 3 — Result match check** (delegira na `sandbox_runner`)
- Izvrši `expected_query` u sandbox-u s timeout-om 5s
- Usporedi rezultat s `expected_result` iz LLM outputa
- Tolerance: točno isti broj redova, točno iste vrijednosti (case-sensitive za string-ove)
- Order matters samo ako query ima ORDER BY

**Test coverage (test_task_validator.py):**

- Test 1: Validan zadatak (sve 3 razine pass) → ValidationResult(passed=True, failures=[])
- Test 2: Sintaktička greška → fail na razini 1, ostale razine ne pokreću
- Test 3: Coverage fail → fail na razini 2
- Test 4: Result mismatch → fail na razini 3
- Test 5: Edge case — prazan rezultat (0 redova) je validan ako expected_result je prazan
- Test 6: Edge case — TIMESTAMPTZ vrijednosti normaliziraju se (ne ovise o timezone-u runtime-a)

---

### 4.4 `sandbox_runner.py`

**Odgovornost:** Izvršavanje SQL queryja u sandbox-u s timeout-om i izolacijom.

**Public interface:**

```python
class SandboxRunner:
    def __init__(
        self,
        connection_string: str,         # postgresql://app_user:pass@localhost:5433/sandbox
        timeout_seconds: int = 5,
    ) -> None: ...

    def execute(
        self,
        query: str,
        schema: str = "ecommerce_v1",
    ) -> ExecutionResult:
        """
        Izvršava query u sandbox bazi pod role-om sandbox_readonly.
        Vraća strukturiran rezultat.
        """
        ...

    def compare(
        self,
        actual: ExecutionResult,
        expected: list[dict],           # iz expected_result LLM outputa
        order_matters: bool = False,
    ) -> ComparisonResult:
        """
        Usporedba dva rezultata. Order_matters auto-detektira (postoji ORDER BY?).
        """
        ...

@dataclass
class ExecutionResult:
    success: bool
    rows: list[dict]                    # Lista redova kao dict (column_name -> value)
    column_names: list[str]
    execution_time_ms: int
    error: str | None                   # Ako success=False

@dataclass
class ComparisonResult:
    matches: bool
    diff_summary: str                   # Human-readable za logging
    actual_count: int
    expected_count: int
    first_mismatch: dict | None         # Prvi red gdje se razlikuju
```

**Implementation napomene:**

- Koristi `psycopg` 3.x (već u dependency listi iz Faze 1)
- `SET ROLE sandbox_readonly` prije svakog query-ja (defense-in-depth)
- `SET statement_timeout = 5000` za 5s hard kill
- `SET search_path TO ecommerce_v1` za schema isolation
- Connection per call (ne reuseaj — sigurnije za sandbox)
- Rezultate normalizira: TIMESTAMPTZ → ISO string, NUMERIC → str(decimal)
- `compare()` koristi sets ako `order_matters=False`, lists ako `True`
- Auto-detekcija order_matters: regex `\bORDER\s+BY\b` u query-ju

**Test coverage (test_sandbox_runner.py):**

- Test 1: Trivial SELECT vraća 15 kategorija
- Test 2: Timeout — `SELECT pg_sleep(10)` raise timeout
- Test 3: Privilege error — `INSERT INTO ...` raise (read-only role)
- Test 4: compare() match — identični rezultati pass
- Test 5: compare() mismatch — različiti row counts fail
- Test 6: compare() order detection — query s ORDER BY treba red. matter
- Test 7: NULL vrijednosti se ispravno usporedjuju

---

### 4.5 `ast_analyzer.py`

**Odgovornost:** AST-based analiza SQL queryja za concept coverage validaciju. Sprječava halucinacije gdje keyword postoji u komentaru ali ne u stvarnom SQL kontekstu.

**Public interface:**

```python
class AstAnalyzer:
    def detects_concept(
        self,
        query: str,
        concept_code: str,              # "left_join", "group_by", ...
    ) -> ConceptDetectionResult:
        """
        Provjerava da query stvarno koristi concept_code u semantičkom kontekstu.
        """
        ...

@dataclass
class ConceptDetectionResult:
    detected: bool
    location: str | None                # Gdje je pronađen ("FROM clause", "WHERE clause", ...)
    is_in_comment: bool                 # True ako je samo u komentaru
    is_in_string: bool                  # True ako je samo u string literalu
    extra_info: dict                    # Per-concept specifični details
```

**Per-concept detekcijska pravila:**

| Concept code | Detekcija pravila |
|---|---|
| `select_basic` | Top-level `SELECT` token postoji (bez `WHERE/JOIN/GROUP BY` minimalno) |
| `from_clause` | `FROM` token postoji |
| `where_filter` | `WHERE` token na DML-level (ne unutar subquery samo) |
| `order_by` | `ORDER BY` token postoji |
| `limit_offset` | `LIMIT` ili `OFFSET` token |
| `distinct` | `DISTINCT` token nakon SELECT-a |
| `group_by` | `GROUP BY` token postoji |
| `having_filter` | `HAVING` token postoji |
| `agg_count` | `COUNT(...)` funkcija u SELECT-u |
| `agg_sum_avg` | `SUM(...)` ili `AVG(...)` u SELECT-u |
| `agg_min_max` | `MIN(...)` ili `MAX(...)` u SELECT-u |
| `inner_join` | `INNER JOIN` ili `JOIN` (bez OUTER prefix) u FROM-u |
| `left_join` | `LEFT JOIN` ili `LEFT OUTER JOIN` u FROM-u |
| `right_join` | `RIGHT JOIN` ili `RIGHT OUTER JOIN` u FROM-u |
| `full_outer_join` | `FULL JOIN` ili `FULL OUTER JOIN` u FROM-u |
| `cross_join` | `CROSS JOIN` u FROM-u |
| `self_join` | Ista tablica u FROM-u 2x s različitim alias-ima |
| `multi_table_join` | ≥ 3 tablice u FROM/JOIN |
| `insert` | `INSERT INTO ...` |
| `update` | `UPDATE ... SET ...` |
| `delete` | `DELETE FROM ...` |
| `scalar_subquery` | Subquery u SELECT-u ili WHERE-u koji vraća skalar |
| `in_subquery` | `IN (SELECT ...)` ili `NOT IN (SELECT ...)` |
| `exists_subquery` | `EXISTS (...)` ili `NOT EXISTS (...)` |
| `correlated_subquery` | Subquery koja referira outer table alias |
| `explain_plan` | `EXPLAIN` na početku |
| `index_usage` | Query koristi `WHERE col = X` na indexed column (semantic check kasnije) |
| `null_handling` | `IS NULL`, `IS NOT NULL`, `COALESCE`, `NULLIF` |
| `column_alias` | `AS` ili implicitan alias na expression |
| `join_condition` | `ON ...` clause u JOIN-u |

**Implementation napomene:**

- Koristi `sqlparse` (već u Faze 1 dependency listi)
- Za svaki koncept, traverse-aj AST tree i provjeri konkretne uvjete
- Komentari (`-- ...`, `/* ... */`) i string literali (`'...'`) se IGNORIRAJU u svim provjerama
- `correlated_subquery` zahtijeva special logic: parse outer query → collect aliases → parse subquery → check if any alias referenced
- `self_join` zahtijeva FROM clause analysis: jedna tablica spomenuta 2+ puta s različitim alias-ima

**Test coverage (test_ast_analyzer.py):**

Najmanje 1 pozitivan + 1 negativan test po konceptu (60+ test cases). Primjeri:

```python
def test_left_join_detected_in_from():
    query = "SELECT c.*, o.* FROM customers c LEFT JOIN orders o ON c.id = o.customer_id;"
    result = analyzer.detects_concept(query, "left_join")
    assert result.detected
    assert result.location == "FROM clause"

def test_left_join_NOT_detected_when_only_in_comment():
    query = "-- This is a LEFT JOIN example\nSELECT * FROM customers c JOIN orders o ON c.id = o.customer_id;"
    result = analyzer.detects_concept(query, "left_join")
    assert not result.detected
    assert result.is_in_comment

def test_correlated_subquery_detected():
    query = """
        SELECT p.name FROM products p
        WHERE p.price > (SELECT AVG(p2.price) FROM products p2 WHERE p2.category_id = p.category_id);
    """
    result = analyzer.detects_concept(query, "correlated_subquery")
    assert result.detected
    assert "p.category_id" in result.extra_info["outer_references"]

def test_correlated_subquery_NOT_detected_for_uncorrelated():
    query = "SELECT name FROM products WHERE price > (SELECT AVG(price) FROM products);"
    result = analyzer.detects_concept(query, "correlated_subquery")
    assert not result.detected
```

---

### 4.6 `app/schemas/generated_task.py`

**Odgovornost:** Pydantic schema za LLM output. Strukturna validacija prije nego ide u TaskValidator.

```python
from pydantic import BaseModel, Field
from typing import Literal

class GeneratedTask(BaseModel):
    """
    Output schema za jedan generirani SQL zadatak.
    LLM mora vratiti JSON koji točno prati ovu strukturu.
    """

    title: str = Field(..., min_length=10, max_length=255)
    description: str = Field(..., min_length=20, max_length=2000)

    primary_concept: str                # mora biti u 30 koncepata
    secondary_concepts: list[str] = Field(default_factory=list, max_length=2)

    difficulty: int = Field(..., ge=1, le=5)
    estimated_time_sec: int = Field(..., ge=30, le=600)

    sandbox_schema: Literal["ecommerce_v1"] = "ecommerce_v1"
    expected_query: str = Field(..., min_length=10)
    expected_result: list[dict]          # Lista redova; prazna lista = expected 0 rows

    targets_misconception: str | None = None    # Optional: kod misconceptiona iz §2.2
    pedagogical_notes: str | None = None        # Optional: za ručnu validaciju

class GeneratedTaskMeta(BaseModel):
    """Metapodaci o generaciji (nije iz LLM-a, dodaje generator)."""

    task: GeneratedTask
    generation_id: str                  # UUID
    api_input_tokens: int
    api_output_tokens: int
    api_cached_tokens: int
    retries: int                        # Koliko retry-eva trebalo
    validation_passed: bool
    validation_failures: list[dict]
    generated_at: str                   # ISO timestamp
    model_used: str
    extended_thinking: bool
```

---

### 4.7 `generate_tasks.py` (CLI entrypoint)

**Odgovornost:** Top-level orkestracija. CLI args, dependency injection, output handling.

**CLI interface:**

```bash
# Faza 2A — generiranje 1 zadatka, ne piše u bazu
python scripts/generate_tasks.py \
    --concept inner_join \
    --difficulty 2 \
    --count 1 \
    --dry-run \
    --output-dir data/generated_tasks/

# Faza 2B (kasnije) — full run iz matrice
python scripts/generate_tasks.py \
    --from-matrix \
    --output-dir data/generated_tasks/ \
    --max-retries 3

# Help
python scripts/generate_tasks.py --help
```

**CLI args:**

- `--concept CONCEPT`: konkretan KC code (mutually exclusive s `--from-matrix`)
- `--difficulty {1,2,3,4,5}`: težina (default: 2)
- `--count N`: koliko zadataka generirati (default: 1)
- `--from-matrix`: pokreni full distribucijsku matricu (Faza 2B)
- `--output-dir DIR`: gdje spremiti rezultate (default: `data/generated_tasks/`)
- `--max-retries N`: koliko retry-eva po fail-u (default: 3)
- `--dry-run`: ne piše u bazu (Faza 2A default; Faza 2C-ready ne)
- `--verbose`: detaljno logiranje
- `--no-extended-thinking`: force disable extended thinking (debug)

**Pipeline za jedan zadatak:**

```python
def generate_one(concept: str, difficulty: int, retries: int = 0) -> GeneratedTaskMeta:
    prompt = prompt_builder.build(concept, difficulty)

    use_thinking = difficulty >= 4
    response = api_client.generate(
        system=prompt.system,
        user_message=prompt.user,
        extended_thinking=use_thinking,
    )

    try:
        task = GeneratedTask.model_validate_json(extract_json(response.content))
    except ValidationError as e:
        if retries < MAX_RETRIES:
            log_failure("schema_validation", e)
            return generate_one(concept, difficulty, retries + 1)
        raise

    validation = task_validator.validate(task)

    if not validation.passed:
        if retries < MAX_RETRIES:
            log_failure(validation.failures, retries)
            return generate_one(concept, difficulty, retries + 1)
        save_to_failed(task, validation, response)
        raise ValidationFailedAfterRetries(...)

    save_to_validated(task, response, retries)
    return GeneratedTaskMeta(...)
```

---

## 5. Per-concept YAML config — primjer

Za svaki od 30 koncepata, jedan YAML fajl u `backend/config/concepts/`:

```yaml
# backend/config/concepts/left_join.yaml

concept_code: left_join
concept_name: "LEFT OUTER JOIN"
module_number: 3
module_name: "JOIN-ovi"
tier: hard

target_misconceptions:
  - code: "left_join_vs_inner_with_null"
    description: "INNER JOIN umjesto LEFT JOIN - zadatak ne smije raditi s INNER JOIN-om"
    priority: critical    # priority: critical | high | medium - barem critical mora biti pokriven
  - code: "filter_in_on_vs_where"
    description: "Filter u ON klauzi vs WHERE klauzi mijenja semantiku LEFT JOIN-a"
    priority: high
  - code: "anti_join_pattern"
    description: "LEFT JOIN + IS NULL za 'kupci bez narudžbi' tip zadataka"
    priority: critical

domain_hints:
  - "Anti-join scenariji: customers BEZ orders (25 takvih u sandboxu)"
  - "Anti-join scenariji: products BEZ reviews"
  - "LEFT JOIN s agregacijom: 'broj narudžbi po kupcu, uključujući 0'"
  - "Filter u ON vs WHERE distinkcija (težina 4-5)"

anti_patterns:
  - "Ne piši zadatak gdje INNER JOIN slučajno daje isti rezultat kao LEFT JOIN"
  - "Ne koristi RIGHT JOIN umjesto LEFT JOIN bez razloga"
  - "expected_result MORA sadržavati NULL ili 0 vrijednosti gdje to ima smisla"

required_for_high_difficulty:    # Težina ≥ 4
  - "Filter u ON vs WHERE distinkcija (zadatak demonstrira razliku)"
  - "LEFT JOIN s 3+ tablica (multi-table aspect)"
  - "Ili: LEFT JOIN + agregacija + HAVING kombinacija"

few_shot_examples:
  - difficulty: 2
    title: "Svi kupci s brojem narudžbi (uključujući one bez)"
    description: |
      Za svakog kupca prikaži first_name, last_name i ukupan broj njegovih narudžbi.
      Kupci bez narudžbi trebaju imati 0 u stupcu order_count.
    expected_query: |
      SELECT c.first_name, c.last_name, COUNT(o.id) AS order_count
      FROM customers c
      LEFT JOIN orders o ON c.id = o.customer_id
      GROUP BY c.id, c.first_name, c.last_name
      ORDER BY order_count DESC, c.last_name;
    expected_concepts: [left_join, agg_count, group_by, null_handling, column_alias]
    targets_misconception: null

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

**Napomena za Fazu 2A**: Ne moramo imati svih 30 YAML fajlova spremnih za Fazu 2A. Dovoljno je **2-3 reprezentativna** (npr. `select_basic.yaml`, `inner_join.yaml`, `left_join.yaml`) da testiramo pipeline. Preostalih 27 fajlova se popunjavaju u Fazi 2B prije pokretanja generation run-a.

---

## 6. Test plan

### 6.1 TDD pristup po komponenti

Slijedeći pattern Faze 1 (test-driven implementation):

1. Napišeš test (red)
2. Napišeš minimalni kod da pass-a (green)
3. Refactor (refactor)

Order implementacije:

1. **`ast_analyzer.py`** — najjednostavniji, čista logika, no external deps
2. **`sandbox_runner.py`** — vanjska zavisnost (DB), ali jednostavan interface
3. **`prompt_builder.py`** — depends na config files
4. **`api_client.py`** — Anthropic SDK wrapper, mockable
5. **`task_validator.py`** — kompozitni, koristi sve gornje
6. **`generate_tasks.py`** — CLI orkestracija, integration test

### 6.2 Integration test (Milestone Faze 2A)

```python
# tests/test_generate_tasks_integration.py

def test_generate_one_inner_join_difficulty_2(monkeypatch, tmp_path):
    """
    Pokreće cijeli pipeline za jedan zadatak.
    Mock-ira Anthropic API (vraća pre-recorded successful response).
    Validira da output JSON file postoji s ispravnom strukturom.
    """
    # Setup
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")
    fake_response = load_fixture("fixtures/api_response_inner_join_d2.json")
    monkeypatch.setattr(AnthropicClient, "generate", lambda *a, **kw: fake_response)

    # Run
    result = subprocess.run([
        "python", "scripts/generate_tasks.py",
        "--concept", "inner_join",
        "--difficulty", "2",
        "--count", "1",
        "--dry-run",
        "--output-dir", str(tmp_path),
    ], capture_output=True)

    # Assert
    assert result.returncode == 0
    output_files = list(tmp_path.glob("validated/*.json"))
    assert len(output_files) == 1

    with open(output_files[0]) as f:
        meta = GeneratedTaskMeta.model_validate_json(f.read())

    assert meta.task.primary_concept == "inner_join"
    assert meta.task.difficulty == 2
    assert meta.validation_passed
    assert "INNER JOIN" in meta.task.expected_query.upper() or "JOIN" in meta.task.expected_query.upper()
```

### 6.3 Live API test (manual, nije u CI)

Jedan ručni test koji troši ~$0.02 starter credita:

```bash
# Pokreni s pravim API ključem
python scripts/generate_tasks.py --concept select_basic --difficulty 1 --count 1 --dry-run

# Provjeri:
# - data/generated_tasks/validated/*.json postoji
# - JSON sadrži valid task
# - Sandbox runner može izvršiti expected_query
# - expected_result se podudara
```

Ako live test pass-a → Faza 2A je completed.

---

## 7. Deliverables checklist

### Code

- [ ] `backend/scripts/generate_tasks.py` — CLI entrypoint
- [ ] `backend/scripts/lib/api_client.py`
- [ ] `backend/scripts/lib/prompt_builder.py`
- [ ] `backend/scripts/lib/task_validator.py`
- [ ] `backend/scripts/lib/sandbox_runner.py`
- [ ] `backend/scripts/lib/ast_analyzer.py`
- [ ] `backend/app/schemas/generated_task.py` — Pydantic schema

### Config

- [ ] `backend/config/sandbox_context.yaml` — schema + invariante
- [ ] `backend/config/prompt_templates/system_static.md`
- [ ] `backend/config/prompt_templates/user_template.md`
- [ ] `backend/config/concepts/select_basic.yaml` (sample)
- [ ] `backend/config/concepts/inner_join.yaml` (sample)
- [ ] `backend/config/concepts/left_join.yaml` (sample)

### Tests

- [ ] `backend/tests/test_api_client.py` (5 test cases)
- [ ] `backend/tests/test_prompt_builder.py` (8 test cases)
- [ ] `backend/tests/test_task_validator.py` (6 test cases)
- [ ] `backend/tests/test_sandbox_runner.py` (7 test cases)
- [ ] `backend/tests/test_ast_analyzer.py` (60+ test cases — 2 po konceptu)
- [ ] `backend/tests/test_generate_tasks_integration.py` (1 integration test)

### Infrastructure

- [ ] `backend/.env.example` updated s `ANTHROPIC_API_KEY=sk-ant-api03-...`
- [ ] `backend/pyproject.toml` updated s `anthropic`, `pyyaml`, `python-dotenv` deps (ako nedostaju)
- [ ] `data/generated_tasks/` directory s `.gitkeep`-ovima za `raw/`, `validated/`, `failed/` poddirektorije
- [ ] `data/generated_tasks/.gitignore` (ne commitamo generirane zadatke u 2A — to je 2B)

### Verification (Milestone)

- [ ] Svi unit testovi prolaze (target: 41 baseline iz Faze 1 + ~85 novi = ~126 ukupno)
- [ ] Integration test prolazi (mock API)
- [ ] Live API test prolazi (1 zadatak generiran, validiran, spremljen)
- [ ] `data/generated_tasks/validated/` sadrži minimum 1 JSON fajl s validnim taskom
- [ ] Token cost log: < $0.05 ukupno za sve testne run-ove

### Git

- [ ] Branch: `faza-2a-infrastruktura`
- [ ] Commit-ovi po komponenti (slijedeć TDD red-green-refactor pattern)
- [ ] Tag: `faza-2a-complete` na finishing commit-u
- [ ] PR description: links to ovaj plan dokument

---

## 8. Entry kriteriji (start Faza 2A)

- [x] Faza 1 zaključena (tag `faza-1-complete` postoji)
- [x] Sandbox baza s 4895 redaka radi (port 5433)
- [x] 30 koncepata seedani u bazu
- [x] Prolog ontologija (30 koncepata + 38 prerequisites) consultable
- [ ] Anthropic API ključ pribavljen (`console.anthropic.com → Settings → API Keys`)
- [ ] `.env` fajl u backend/ dir-u s `ANTHROPIC_API_KEY` postavljen
- [ ] Provjera $5 starter credit-a na Anthropic accountu
- [ ] WSL Ubuntu environment ready (kao Faza 1)

---

## 9. Exit kriteriji (end Faza 2A)

- [ ] Svi deliverables iz §7 čekirano
- [ ] `pytest backend/tests/` prolazi 100% (zero regresije iz Faze 1)
- [ ] Live API test pass-a (1 zadatak generiran end-to-end)
- [ ] Output JSON ima validan format (Pydantic schema)
- [ ] `git tag faza-2a-complete` postavljen
- [ ] Token usage log pokazuje < $0.10 utrošeno (testovi + 1 live)

**Sljedeći korak nakon 2A:** Faza 2B — pokretanje generation run-a za svih 105 zadataka iz distribucijske matrice, popunjavanje preostalih 27 YAML config fajlova, ručna validacija od strane korisnika.

---

## 10. Rizici i mitigacije

| Rizik | Vjerojatnost | Utjecaj | Mitigacija |
|---|---|---|---|
| API rate limit (429) tijekom testova | Niska | Niski | Retry s backoff već u api_client.py |
| sqlparse ne prepoznaje neke PostgreSQL extension keywords | Srednja | Srednji | Fallback na regex match s warning, manual review u Fazi 2B |
| Sandbox baza ne radi (Docker kontejner down) | Niska | Visok | Pre-flight check u sandbox_runner.py: SELECT 1 prije generiranja |
| LLM vraća JSON s extra text oko (npr. markdown ```) | Visoka | Niski | `extract_json()` helper koji parse-a iz code block-a ili plain JSON |
| Extended thinking troši puno tokena | Srednja | Srednji | Limit budget_tokens=2000, samo za difficulty ≥ 4 |
| Cached tokens ne rade (prvi poziv = cache miss) | 100% | Niski | Očekivano; cache hit nakon 1. poziva, 90% off na ostatku |
| Self-validation prompt produžuje response time | Srednja | Niski | Ne blokira, samo dodaje 2-3s latency po zadatku |

---

## 11. Reference

- `faza-1-domenski-model.md` — kompletan domenski model (30 koncepata, BKT, sheme baza)
- `faza-1-wrapup.md` — status zaključenja Faze 1
- `diplomski-plan.docx` — Section 6, Faza 2 specifikacija
- Anthropic API docs: https://docs.claude.com/en/api/messages
- Anthropic prompt caching: https://docs.claude.com/en/docs/build-with-claude/prompt-caching
- `sqlparse` docs: https://sqlparse.readthedocs.io/

---

*Dokument kraj. Sljedeći korak: Claude Code bootstrap prompt (`faza-2a-claude-code-prompt.md`) za novi WSL session.*
