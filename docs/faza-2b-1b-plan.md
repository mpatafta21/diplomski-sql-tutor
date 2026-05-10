# FAZA 2B-1B — Akcijski plan

**Diplomski rad:** Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju
**Sub-faza:** 2B-1B od 7 (druga sub-podsekcija Faze 2B-1)
**Cilj:** SandboxRunner DML refactor + tool-use API u AnthropicClient + meta-generation 23 concept YAML-a + pilot run (12 tasks) za prompt template validaciju
**Trajanje:** ~4-4.5h aktivnog rada (sa scope creep za DML refactor)
**Workflow:** TDD red-green-refactor, dva git tag-a kao checkpointi
**Predviđeni broj git commit-ova:** 12-15

---

## 1. Kontekst i ciljevi

### 1.1 Što ova sub-faza radi

2B-1B završava pripremu **svih 30 concept YAML config-ova** i validira prompt template kroz pilot run prije full generation run-a u 2B-2:

1. **SandboxRunner DML refactor** (scope creep iz Q2 odluke) — proširi `execute()` s `dml: bool` parametrom koji switch-a na `sandbox_readwrite` role. Potrebno za pilot run M4 zadataka (`insert`).
2. **Tool-use API u AnthropicClient** — nova metoda `generate_structured_output()` koja koristi Anthropic `tools=[]` + `tool_choice={"type":"tool"}` pattern za garantirani structured output. Schema je direktno `ConceptConfig.model_json_schema()`.
3. **Meta-generation skript** (`scripts/meta_generate_yamls.py`) — koristi tool-use API, few-shot s 7 postojećih YAML-ova (3 originala + 4 iz 2B-1A), generira 23 preostala YAML-a u jednom batch-u.
4. **Schema validacija svih 30 YAML-a** kroz `load_concept_config()` (integration test iz 2B-1A automatski hvata fail-ove).
5. **Pilot generation run** — 2 tasks po concept tipu × 6 tipova = 12 tasks, ~$0.10 trošak. Cilj: validacija prompt template-a za sve concept tipove (jedan po module-u). Reuse postojeće `generate_one()` funkcije iz 2A.
6. **Pilot analiza** — failure rate po concept tipu, distribucija retry-a, identifikacija prompt template problema (ako postoje).

### 1.2 Što ova sub-faza NE radi

- ❌ Full generation run za 105 zadataka (to je 2B-2)
- ❌ Validation tool (Streamlit + SQLite) — to je 2B-1C
- ❌ Prompt template fix-evi (ako pilot otkrije probleme) — fix se primjenjuje u 2B-2 prije batch-a, ne retroaktivno u 2B-1B
- ❌ Manualna validacija pilot tasks (jednostavna sanity check kroz validator — full review je 2B-3)
- ❌ Izmjena 2B-1A schema (`ConceptConfig`) ili 2A `task_validator.py`, `ast_analyzer.py` interfejsa

### 1.3 Strateške odluke (zaključene)

| # | Odluka | Vrijednost |
|---|---|---|
| 1 | Redoslijed | Meta-gen 23 YAML-a PRVO → pilot run → analiza → 2B-2 monitoring |
| 2 | SandboxRunner DML | Refactor u 2B-1B (proširi `execute(dml: bool = False)`) |
| 3 | Tool-use API | `generate_structured_output()` zasebna metoda u `AnthropicClient` |
| 4 | Sub-podjela | Dva taga: `faza-2b-1b-meta-gen-complete` + `faza-2b-1b-complete` |
| 5 | Meta-gen retry | 1× auto-retry s schema error feedback u prompt-u → manual fallback ako i drugi fail |
| 6 | Pilot scope | 2 tasks po concept tipu × 6 tipova = 12 tasks (~$0.10) |
| 7 | Pilot tipovi | `where_filter` (M1), `group_by` (M2), `right_join` (M3), `insert` (M4), `scalar_subquery` (M5), `explain_plan` (M6) — pokriva sve module osim transverzalnog (testira se kroz secondary u 2B-2) |

---

## 2. Deliverables

### 2.1 Kod (4 nova fajla + 2 modifikacije)

| Path | Status | LoC (procjena) | Odgovornost |
|---|---|---|---|
| `backend/scripts/lib/sandbox_runner.py` | **MODIFY** | +20 | Dodaj `dml: bool = False` parametar; switch role; rollback nakon evaluacije |
| `backend/scripts/lib/api_client.py` | **MODIFY** | +60 | `generate_structured_output()` metoda + `StructuredOutputResponse` dataclass |
| `backend/scripts/lib/meta_gen.py` | **NEW** | ~150 | Helper biblioteka: build_meta_gen_prompt, parse_response, retry s feedback |
| `backend/scripts/meta_generate_yamls.py` | **NEW** | ~120 | CLI entrypoint: iterira po listi koncepata, koristi `meta_gen.py`, piše YAML-ove |
| `backend/scripts/pilot_run.py` | **NEW** | ~100 | CLI entrypoint za pilot generation; reuse `generate_one()`, pilot-specific reporting |
| `backend/config/prompt_templates/meta_gen_system.md` | **NEW** | ~60 lines | System prompt za meta-gen (few-shot strategy, schema reference) |

### 2.2 Tests

| Test fajl | Status | Broj testova | Pokrivenost |
|---|---|---|---|
| `backend/tests/test_sandbox_runner.py` | **MODIFY** | +6 | DML path: insert/update/delete, rollback, role switch, regression za SELECT path |
| `backend/tests/test_api_client.py` | **MODIFY** | +5 | Structured output happy path, tool_use parse, retry s schema feedback, model-agnostic, error cases |
| `backend/tests/test_meta_gen.py` | **NEW** | ~8 | Prompt construction, response parsing, schema fail retry logic, manual fallback path |
| `backend/tests/test_pilot_run_smoke.py` | **NEW** | ~3 | Smoke test (mock API) — pipeline end-to-end, reporter output format |

**Test count target:** 189 (baseline iz 2B-1A) + ~22 nova = **~211 testova** prolaze.

### 2.3 Generirani output (van git-a)

| Path | Status | Sadržaj |
|---|---|---|
| `backend/config/concepts/from_clause.yaml` ... (23 fajla) | **NEW** (van git-a tijekom razvoja, commit-aju se nakon manual review) | Meta-generirani concept YAML config-ovi |
| `data/generated_tasks/pilot/` | **NEW directory** | Pilot run output: 12 tasks (validated + failed subdirs) |
| `data/generated_tasks/pilot/pilot_report.json` | **NEW** | Sažetak: per-concept failure rate, total cost, retry distribucija |

### 2.4 Git artefakti

| Tag | Što označava | Kraj kojeg koraka iz §7 |
|---|---|---|
| `faza-2b-1b-meta-gen-complete` | SandboxRunner DML radi, tool-use API u AnthropicClient, 23 nova YAML-a u repu, svih 30 prolaze schema | Korak 6 |
| `faza-2b-1b-complete` | Pilot run završen, pilot_report.json generiran, analiza dokumentirana | Korak 9 |

### 2.5 Verification (Milestone)

- [ ] `SandboxRunner.execute(dml=True)` radi za INSERT/UPDATE/DELETE, rollback radi
- [ ] `AnthropicClient.generate_structured_output(schema=ConceptConfig.model_json_schema())` vraća validan `ConceptConfig` instance
- [ ] 23 nova YAML-a postoje u `backend/config/concepts/`
- [ ] Svih 30 YAML-a prolaze `test_all_concept_yamls_validate` (integration test iz 2B-1A)
- [ ] Pilot run generira 12 tasks (validated + failed), `pilot_report.json` postoji
- [ ] ~211 testova prolazi
- [ ] Tagovi `faza-2b-1b-meta-gen-complete` i `faza-2b-1b-complete` push-ani

---

## 3. Dizajn — SandboxRunner DML refactor

### 3.1 Trenutno stanje (iz dump-a)

`SandboxRunner.execute(query: str)` hardcoded-a `SET ROLE sandbox_readonly`. Samo SELECT podržan.

### 3.2 Cilj

```python
# backend/scripts/lib/sandbox_runner.py (modified)
class SandboxRunner:
    def execute(
        self,
        query: str,
        dml: bool = False,
        timeout_ms: int = 5000,
    ) -> SandboxResult:
        """
        Izvršava SQL upit u sandbox PostgreSQL bazi.

        Args:
            query: SQL upit za izvršavanje.
            dml: Ako True, koristi sandbox_readwrite role i wrap-a sve u
                 transakciju s ROLLBACK na kraju (DML changes ne perzistiraju).
                 Ako False (default), koristi sandbox_readonly i nema rollback-a.
            timeout_ms: Statement timeout (default 5s).

        Returns:
            SandboxResult s (success, rows, error, exec_time_ms).
        """
        role = "sandbox_readwrite" if dml else "sandbox_readonly"

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SET ROLE {role}")
                cur.execute(f"SET LOCAL statement_timeout = {timeout_ms}")

                try:
                    if dml:
                        # Wrap u savepoint za eksplicit rollback
                        cur.execute("SAVEPOINT dml_execution")
                    cur.execute(query)
                    rows = cur.fetchall() if cur.description else []
                    result = SandboxResult(success=True, rows=rows, ...)
                except (errors.QueryCanceled, errors.DataError, ...) as exc:
                    result = SandboxResult(success=False, error=str(exc), ...)
                finally:
                    if dml:
                        # Uvijek rollback DML promjene
                        cur.execute("ROLLBACK TO SAVEPOINT dml_execution")
                        cur.execute("RELEASE SAVEPOINT dml_execution")

        return result
```

### 3.3 Ključne dizajn odluke

| Odluka | Razlog |
|---|---|
| `dml: bool = False` parametar (ne `mode: Literal["read","write"]`) | Backward compat — postojeći call-site (`task_validator.py`, `test_sandbox_runner.py`) ne mijenja se |
| SAVEPOINT + ROLLBACK pattern, ne ROLLBACK na transaction level | Ako postoji outer transaction (npr. test fixture), savepoint je lokalan; ne corrupt-amo outer state |
| `SET ROLE` per call (ne per connection) | Connection se može pool-ati za SELECT-ove (read-only); za DML role mora biti switch-an svaki put |
| Greška pri ROLLBACK je swallowed | Ako rollback fail-a, connection se zatvara svejedno — sandbox je destructible |
| Bez `concurrent.futures` ili async | Iz scope-a 2B-1B; current sandbox je sync, pilot tasks ne trebaju paralelizam |

### 3.4 Backward compatibility

**Critical:** Sva 7 postojećih testova u `test_sandbox_runner.py` MORA prolaziti bez izmjena. Default `dml=False` znači postojeći call-site se ne mijenja.

**Default `task_validator.py` call-site:** `runner.execute(query)` — implicit `dml=False`, identično prošlom ponašanju.

**Novi call-site za pilot M4:** `runner.execute(query, dml=True)` — eksplicitan, koristi se u `task_validator.py` (proširenje) ili u pilot run skripti direktno (vidi §6.3).

---

## 4. Dizajn — Tool-use API u AnthropicClient

### 4.1 Trenutno stanje (iz dump-a)

`AnthropicClient.generate(system, user_message, ...)` — free-text output, parse-a se kroz `json_extract.py`. Nema structured output podrške.

### 4.2 Cilj

```python
# backend/scripts/lib/api_client.py (extended)

@dataclass(frozen=True)
class StructuredOutputResponse:
    """Response od structured output poziva (tool_use pattern)."""
    parsed: dict  # Validated structured data iz tool_use bloka
    input_tokens: int
    output_tokens: int
    cached_tokens: int


class AnthropicClient:
    # ... postojeće metode ...

    def generate_structured_output(
        self,
        system: str,
        user_message: str,
        output_schema: dict,
        tool_name: str = "generate_output",
        tool_description: str = "Generate structured output matching the schema.",
        max_tokens: int = 8192,
    ) -> StructuredOutputResponse:
        """
        Strukturirani output kroz Anthropic tool_use pattern.

        Garantira da output match-a output_schema (Pydantic v2 JSON schema).
        Schema se prosljeđuje kao tool.input_schema; tool_choice forsira tool
        upotrebu, što garantira parseabilan structured output.

        Args:
            system: System prompt (cache-iran).
            user_message: User prompt.
            output_schema: JSON Schema dict (npr. ConceptConfig.model_json_schema()).
            tool_name: Naziv tool-a (defaults to 'generate_output').
            tool_description: Opis tool-a (vidi se u model context).
            max_tokens: Token limit (default 8192 jer YAML-ovi mogu biti veći).

        Returns:
            StructuredOutputResponse s parsed dict i token statistikom.

        Raises:
            StructuredOutputError: Ako model ne koristi tool ili response nije parseable.
            anthropic.APIError, anthropic.RateLimitError: Standardne SDK iznimke.
        """
        tool = {
            "name": tool_name,
            "description": tool_description,
            "input_schema": output_schema,
        }

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=[
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ],
            messages=[{"role": "user", "content": user_message}],
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_name},
        )

        # Parse response: tool_use block content je dict matching schema
        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"),
            None,
        )
        if tool_use_block is None:
            raise StructuredOutputError(
                f"Model did not invoke tool '{tool_name}'. "
                f"Stop reason: {response.stop_reason}"
            )

        return StructuredOutputResponse(
            parsed=tool_use_block.input,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cached_tokens=getattr(response.usage, "cache_read_input_tokens", 0),
        )


class StructuredOutputError(Exception):
    """Raised when structured output response is malformed."""
```

### 4.3 Ključne dizajn odluke

| Odluka | Razlog |
|---|---|
| Zasebna metoda (ne extend `generate()`) | Različit return type, različita prompt strategy, čista separation of concerns |
| `tool_choice={"type":"tool", "name":...}` (ne `"any"`) | Forsira upotrebu tog konkretnog tool-a — garantira parseabilan output. `"any"` može switch-ati između free-text i tool_use. |
| `max_tokens=8192` default | YAML-ovi mogu biti dugi (target_misconceptions × 3-4 + few_shot_examples × 1-2). 4096 je rizično. |
| `StructuredOutputResponse` dataclass (ne dict) | Type-safe, eksplicitna struktura, lakše assertati u testovima |
| Bez retry-a u metodi (ostavlja se caller-u) | Retry strategy je different per use case (meta-gen ima schema-feedback retry, drugi pozivi možda nemaju). SDK retry (`max_retries=2`) ostaje. |
| `cache_control` na system | Reuse postojeći prompt caching pattern iz `generate()` — kritično za meta-gen (23 YAML-a × isti system prompt) |

### 4.4 Tests za structured output

```python
# test_api_client.py (extended)

def test_generate_structured_output_happy_path(mock_anthropic_client):
    """Verify happy path: tool_use response → parsed dict."""
    mock_anthropic_client._mock_response_tool_use = {
        "concept_code": "test_concept",
        # ... ostatak validan ConceptConfig
    }
    response = mock_anthropic_client.generate_structured_output(
        system="Test system",
        user_message="Generate a concept config",
        output_schema=ConceptConfig.model_json_schema(),
    )
    assert response.parsed["concept_code"] == "test_concept"
    assert response.cached_tokens == 0


def test_generate_structured_output_no_tool_use_raises(mock_anthropic_client):
    """If model returns text instead of tool_use, raise StructuredOutputError."""
    mock_anthropic_client._mock_response_text_only = "I cannot generate that"
    with pytest.raises(StructuredOutputError, match="did not invoke tool"):
        mock_anthropic_client.generate_structured_output(...)
```

---

## 5. Dizajn — Meta-generation pipeline

### 5.1 Strategija

**Few-shot meta-generation:**
- 7 postojećih YAML-ova kao few-shot examples u system prompt
- Per-concept user prompt s konkretnim `concept_code` + module info iz §5 dump-a
- Tool-use guarantee: output je valid `ConceptConfig` JSON
- Auto-retry s schema error feedback ako prvi pokušaj fail-a

### 5.2 `scripts/lib/meta_gen.py` — biblioteka

```python
# backend/scripts/lib/meta_gen.py
"""
Meta-generation helpers — generira concept YAML config kroz Anthropic
tool-use API koristeći postojeće YAML-ove kao few-shot.
"""

from pathlib import Path
import yaml
from app.schemas.concept_config import (
    ConceptConfig,
    ConceptConfigError,
    load_concept_config,
)
from scripts.lib.api_client import AnthropicClient, StructuredOutputResponse


def collect_few_shot_yamls(concepts_dir: Path) -> dict[str, str]:
    """Učitava sve postojeće YAML-ove (7 iz 2A + 2B-1A) kao raw text za few-shot."""
    examples = {}
    for path in sorted(concepts_dir.glob("*.yaml")):
        examples[path.stem] = path.read_text(encoding="utf-8")
    return examples


def build_meta_gen_prompts(
    target_concept_code: str,
    target_concept_meta: dict,  # iz Prolog ontology / faza-1-domenski-model.md §2.2
    few_shot_examples: dict[str, str],
    schema_error_feedback: str | None = None,
) -> tuple[str, str]:
    """
    Builds (system, user) prompts za jedan concept YAML.

    Args:
        target_concept_code: e.g. "from_clause"
        target_concept_meta: {
            "module_number": 1, "module_name": "Osnove SELECT-a",
            "tier": "easy",
            "description": "...iz Prolog ontology ili Faze 1 doc...",
        }
        few_shot_examples: dict[concept_code, raw_yaml_text]
        schema_error_feedback: Ako je prvi pokušaj fail-ao, ovdje
            ide error message za retry feedback.
    """
    # System prompt: meta-gen rules + few-shot examples
    # User prompt: target concept opis + (optional) schema error feedback
    ...


def parse_and_validate(
    response_parsed: dict,
    output_dir: Path,
) -> tuple[ConceptConfig | None, str | None]:
    """
    Parse-a strukturirani output, validira kroz ConceptConfig,
    piše YAML ako prolazi.

    Returns:
        (config, None) ako prolazi
        (None, error_message) ako schema fail-a
    """
    try:
        config = ConceptConfig.model_validate(response_parsed)
    except Exception as exc:
        return None, f"Schema validation failed: {exc}"

    # Piši YAML
    yaml_path = output_dir / f"{config.concept_code}.yaml"
    yaml_text = yaml.safe_dump(
        config.model_dump(),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
    yaml_path.write_text(yaml_text, encoding="utf-8")

    # Verify load roundtrip — paranoia check
    reloaded = load_concept_config(yaml_path)
    assert reloaded.concept_code == config.concept_code

    return config, None


def generate_one_yaml(
    client: AnthropicClient,
    concept_code: str,
    concept_meta: dict,
    few_shot_examples: dict[str, str],
    output_dir: Path,
    max_retries: int = 1,  # 1× auto-retry s schema feedback
) -> dict:
    """
    Generira jedan YAML config. Retry s schema feedback ako fail-a.

    Returns:
        {"status": "success" | "manual_review", "concept_code": ..., 
         "attempts": N, "cost_usd": ..., "error": str | None}
    """
    schema = ConceptConfig.model_json_schema()
    error_feedback = None
    total_cost = 0.0

    for attempt in range(max_retries + 1):
        system, user = build_meta_gen_prompts(
            concept_code, concept_meta, few_shot_examples,
            schema_error_feedback=error_feedback,
        )
        response = client.generate_structured_output(
            system=system,
            user_message=user,
            output_schema=schema,
        )
        total_cost += estimate_cost(response.input_tokens, response.output_tokens,
                                     response.cached_tokens)

        config, err = parse_and_validate(response.parsed, output_dir)
        if config is not None:
            return {"status": "success", "concept_code": concept_code,
                    "attempts": attempt + 1, "cost_usd": total_cost, "error": None}

        # Schema fail — prepare feedback za retry
        error_feedback = err

    return {"status": "manual_review", "concept_code": concept_code,
            "attempts": max_retries + 1, "cost_usd": total_cost,
            "error": error_feedback}
```

### 5.3 `scripts/meta_generate_yamls.py` — CLI

```python
"""
Meta-generation CLI: generira sve concept YAML-ove koji nedostaju u
backend/config/concepts/ koristeći Anthropic tool-use API.
"""

# Standardni argparse setup
# --concepts: comma-separated list (default: all missing)
# --output-dir: where to write YAML-ove (default: config/concepts)
# --max-retries: auto-retry count (default: 1)
# --dry-run: simuliraj, ne piši YAML-ove

# Lista 23 koncepta koji nedostaju (iz dump-a §6)
MISSING_CONCEPTS = [
    "from_clause", "where_filter", "order_by", "limit_offset", "distinct",
    "group_by", "having_filter", "agg_count", "agg_sum_avg", "agg_min_max",
    "right_join", "full_outer_join", "cross_join",
    "insert", "update", "delete",
    "scalar_subquery", "in_subquery", "exists_subquery",
    "explain_plan",
    "null_handling",
]

# Concept meta dictionary — manualno popunjen iz faza-1-domenski-model.md §2.2
# (Bolje od Prolog query-ja: ne dodajemo zavisnost na pyswip u meta-gen skript)
CONCEPT_META = {
    "from_clause": {
        "module_number": 1, "module_name": "Osnove SELECT-a", "tier": "easy",
        "description": "FROM klauza — identifikacija tablice...",
    },
    # ... 22 ostala
}


def main():
    args = parse_args()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = AnthropicClient(api_key=api_key)

    concepts_dir = Path(args.output_dir)
    few_shot = collect_few_shot_yamls(concepts_dir)

    targets = args.concepts or MISSING_CONCEPTS
    results = []

    for concept_code in targets:
        if concept_code not in CONCEPT_META:
            print(f"⚠ Skipping {concept_code}: no meta info")
            continue

        result = generate_one_yaml(
            client, concept_code, CONCEPT_META[concept_code],
            few_shot, concepts_dir, max_retries=args.max_retries,
        )
        results.append(result)

        status_icon = "✓" if result["status"] == "success" else "⚠"
        print(f"{status_icon} {concept_code}: {result['attempts']} attempts, "
              f"${result['cost_usd']:.4f}")

    # Summary
    n_success = sum(1 for r in results if r["status"] == "success")
    n_manual = len(results) - n_success
    total_cost = sum(r["cost_usd"] for r in results)
    print(f"\n=== META-GEN COMPLETE ===")
    print(f"Success: {n_success}/{len(results)}")
    print(f"Manual review: {n_manual}/{len(results)}")
    print(f"Total cost: ${total_cost:.4f}")

    if n_manual > 0:
        print("\nKoncepti za manual review:")
        for r in results:
            if r["status"] == "manual_review":
                print(f"  - {r['concept_code']}: {r['error']}")
```

### 5.4 Procjena troškova meta-gen-a

| Stavka | Vrijednost | Kalkulacija |
|---|---|---|
| Input tokens po pozivu (fresh, prvi) | ~3500 | 7 YAML examples × ~400 tokens + base prompt |
| Input tokens po pozivu (cached, 2.-23.) | ~3500 cached, ~50 fresh | Prompt caching radi |
| Output tokens po pozivu | ~600 | Validni YAML config = ~500-700 tokens |
| Cijena po pozivu (cached) | ~$0.009 | Cached input × $0.30/M + output × $15/M |
| 23 koncepta × 1.1 retry rate | ~25 poziva | 10% fail rate procjena |
| **Ukupna cijena meta-gen-a** | **~$0.22** | Within budget |

---

## 6. Dizajn — Pilot run

### 6.1 Pilot scope (iz Q7 odluke)

**6 koncepata × 2 tasks = 12 tasks ukupno**, ~$0.10:

| Module | Concept | Težina pilot tasks | Sandbox mode |
|---|---|---|---|
| 1 | `where_filter` | d=1, d=2 | SELECT (default) |
| 2 | `group_by` | d=2, d=3 | SELECT |
| 3 | `right_join` | d=2, d=3 | SELECT |
| 4 | `insert` | d=1, d=2 | **DML** (write role) |
| 5 | `scalar_subquery` | d=2, d=3 | SELECT |
| 6 | `explain_plan` | d=3, d=4 | SELECT (placeholder validation, vidi 2A errata) |

**Zašto baš ovi koncepti:** Po 1 koncept iz svakog module-a, izabran kao "tipičan" za module (najjednostavniji za testirati prompt behavior). `null_handling` (transverzalni) testiramo u 2B-2 kroz secondary_concepts u SELECT zadacima, ne kao zaseban pilot.

### 6.2 `scripts/pilot_run.py` — CLI

```python
"""
Pilot run: 2 tasks po pilot concept tipu, koristeći generate_one() iz
generate_tasks.py. Sažeti report nakon completiona.
"""

from scripts.generate_tasks import generate_one, _build_pipeline, estimate_cost_usd

PILOT_CONFIG = [
    {"concept": "where_filter", "difficulties": [1, 2]},
    {"concept": "group_by", "difficulties": [2, 3]},
    {"concept": "right_join", "difficulties": [2, 3]},
    {"concept": "insert", "difficulties": [1, 2], "dml": True},  # NEW flag
    {"concept": "scalar_subquery", "difficulties": [2, 3]},
    {"concept": "explain_plan", "difficulties": [3, 4]},
]


def main():
    output_dir = Path("data/generated_tasks/pilot")
    output_dir.mkdir(parents=True, exist_ok=True)

    builder, api, validator = _build_pipeline(...)

    report = {"per_concept": {}, "total_cost": 0.0, "started_at": now_iso()}

    for entry in PILOT_CONFIG:
        concept = entry["concept"]
        report["per_concept"][concept] = []

        for difficulty in entry["difficulties"]:
            meta, raw_responses = generate_one(
                builder, api, validator,
                concept=concept, difficulty=difficulty,
                output_dir=output_dir,
                max_retries=3,  # standard 2A behavior
            )

            result = {
                "concept": concept,
                "difficulty": difficulty,
                "status": "validated" if meta and meta.status == "validated" else "failed",
                "attempts": len(raw_responses),
                "error": meta.validation_summary.error_type if meta else "no_meta",
                "cost_usd": sum(estimate_cost_usd(...) for r in raw_responses),
            }
            report["per_concept"][concept].append(result)
            report["total_cost"] += result["cost_usd"]

            print(f"{'✓' if result['status']=='validated' else '✗'} "
                  f"{concept} d={difficulty}: {result['attempts']} attempts, "
                  f"${result['cost_usd']:.4f}")

    # Save report
    (output_dir / "pilot_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Print analiza
    print_pilot_analysis(report)


def print_pilot_analysis(report):
    """Failure rate by concept, total cost, retry distribution."""
    ...
```

### 6.3 DML support u pilot — task_validator.py mock approach

**Problem:** `task_validator.py` poziva `runner.execute(query)` (implicit `dml=False`). Za INSERT pilot, mora znati switch-ati.

**Rješenje:** Pilot run **direktno koristi** SandboxRunner s `dml=True` flag (bypass-a validator level 3 za M4 koncepte). Validator levels 1+2 (syntax + AST coverage) ostaju.

```python
# Modify validator: dodaj is_dml param
def validate_task(self, task: GeneratedTask, dml: bool = False) -> ValidationResult:
    """
    Args:
        dml: Ako True, sandbox koristi readwrite role i rollback.
    """
    # ... level 1, 2 nepromijenjeni ...
    # Level 3: sandbox execution
    sandbox_result = self.runner.execute(task.expected_query, dml=dml)
    # ... ostatak isto ...
```

**Pilot prepoznaje DML iz PILOT_CONFIG entry-ja:** `if entry.get("dml"): validator.validate_task(task, dml=True)`.

### 6.4 Pilot success kriteriji

Pilot run je **success** ako:
- Svih 12 tasks generirano (s ili bez validacije)
- Pilot report generiran
- **Bez** zahtjeva za 100% pass rate — pilot je signal, ne acceptance test

**Što triggera akciju u 2B-2:**
- Failure rate > 50% za neki concept tip → prompt template fix prije 2B-2 batch-a za taj module
- Token usage > 2× procjene → review max_tokens i prompt verbosity
- DML tasks fail-aju s rollback errorom → SandboxRunner refactor bug (rollback u 2B-1B)

---

## 7. Implementacijski redoslijed (TDD)

**Workflow:** Striktni TDD. Commit po koraku. Nakon svakog koraka — `cd backend && uv run pytest -q`, target zelena.

### Korak 1: SandboxRunner DML refactor (test-first)

**Branch:** `faza-2b-1b-implementation`

1. Napiši test `test_execute_dml_insert_rollbacks` (RED — `dml` param ne postoji)
2. Napiši `test_execute_dml_role_switch` (RED)
3. Napiši `test_execute_default_select_path_unchanged` (regression — MORA prolaziti)
4. Modify `sandbox_runner.py`: dodaj `dml` parametar, SAVEPOINT/ROLLBACK logic
5. Run `uv run pytest backend/tests/test_sandbox_runner.py` → 13 testova (7 baseline + 6 novih) PROLAZI
6. **Commit:** `feat(2b-1b): SandboxRunner DML support s rollback + 6 testova`

### Korak 2: AnthropicClient structured output (test-first)

1. Napiši test `test_generate_structured_output_happy_path` s mock SDK response
2. Napiši test `test_generate_structured_output_no_tool_use_raises`
3. Napiši test `test_structured_output_uses_cache_control`
4. Napiši test `test_structured_output_model_agnostic`
5. Napiši test `test_structured_output_token_usage_extracted`
6. Implementiraj `generate_structured_output()` u `api_client.py`
7. Implementiraj `StructuredOutputResponse` dataclass + `StructuredOutputError`
8. Run tests → 14 testova (9 baseline + 5 novih) prolaze
9. **Commit:** `feat(2b-1b): generate_structured_output() tool-use API + 5 testova`

### Korak 3: Code review checkpoint #1

**Pokrenuti code review skill** na sandbox + api_client izmjenama. Fokus:
- Rollback edge cases (rollback fail dok prethodni statement fail-ao?)
- Tool-use response parsing (mixed content block scenarios)
- Cache control compatibility s tools=[...]
- Test mock setup robustness

Ako review pronađe HIGH severity, fix commit prije nastavka.

### Korak 4: meta_gen.py library (test-first)

1. Napiši test `test_collect_few_shot_yamls`
2. Napiši test `test_build_meta_gen_prompts_no_feedback`
3. Napiši test `test_build_meta_gen_prompts_with_schema_feedback`
4. Napiši test `test_parse_and_validate_schema_pass`
5. Napiši test `test_parse_and_validate_schema_fail_returns_error`
6. Napiši test `test_generate_one_yaml_retry_on_schema_fail`
7. Napiši test `test_generate_one_yaml_manual_review_after_max_retries`
8. Implementiraj `meta_gen.py`
9. Napiši `meta_gen_system.md` template (manual file)
10. Run tests → ~219 prolaze (~211 baseline + ~8 novih)
11. **Commit:** `feat(2b-1b): meta_gen.py library s 1× auto-retry + 8 testova`

### Korak 5: Generate 23 YAML-a (live API call)

1. Napiši `scripts/meta_generate_yamls.py` CLI
2. Popuni `CONCEPT_META` dict (manualno iz `faza-1-domenski-model.md` §2.2)
3. **Live API run:**
   ```bash
   cd backend
   uv run python -m scripts.meta_generate_yamls --output-dir config/concepts
   ```
4. Pregledaj summary: `Success: 21/23, Manual review: 2/23` (očekivana raspodjela)
5. Manual fix za 2 fail-ana koncepta (kopiraj closest YAML, edit)
6. Run integration test:
   ```bash
   uv run pytest backend/tests/test_concept_config.py::test_all_concept_yamls_validate -v
   ```
7. Test mora reći `30 YAML files validated`
8. **Commit:** `feat(2b-1b): 23 meta-generirana YAML-a + manual fix za 2 koncepta`
9. **Tag:** `git tag faza-2b-1b-meta-gen-complete && git push origin faza-2b-1b-meta-gen-complete`

### Korak 6: pilot_run.py skript (test-first za smoke)

1. Napiši test `test_pilot_run_smoke_mock_api` — full pipeline s mock API
2. Napiši test `test_pilot_report_format`
3. Napiši test `test_pilot_dml_flag_propagation`
4. Implementiraj `pilot_run.py` CLI
5. Run tests → ~222 prolaze
6. **Commit:** `feat(2b-1b): pilot_run.py CLI + smoke tests`

### Korak 7: task_validator.py DML param

1. Modify `task_validator.py` — dodaj `dml: bool = False` u `validate_task()`
2. Test: `test_validator_dml_path` (existing tests = regression net)
3. **Commit:** `feat(2b-1b): task_validator DML support pass-through`

### Korak 8: Pilot run live

1. Run pilot live:
   ```bash
   cd backend
   uv run python -m scripts.pilot_run
   ```
2. Očekivani output: 12 tasks, ~$0.10 trošak, ~70-90% pass rate
3. Pregledaj `pilot_report.json`
4. Document findings u commit message (npr. "DML rollback works, scalar_subquery failed 2/2 — needs prompt fix in 2B-2")
5. **Commit:** `feat(2b-1b): pilot run complete + report.json`

### Korak 9: Code review checkpoint #2 + final

1. Pokreni code review na pilot_run + meta_gen
2. Adresiraj findings
3. Final test suite run: `uv run pytest -q` → **~222 testova prolaze**
4. **Tag:** `git tag faza-2b-1b-complete && git push origin faza-2b-1b-complete`

---

## 8. Entry kriteriji (start 2B-1B)

- [x] 2B-1A zaključena, tag `faza-2b-1a-complete` push-an
- [x] 189 testova baseline prolaze
- [x] 7 YAML-ova u `backend/config/concepts/`
- [x] `ConceptConfig.model_json_schema()` radi
- [x] `anthropic>=0.97.0`, `pydantic>=2.0`, `pyyaml>=6.0` u deps
- [x] Sandbox kontejner running (postgres-sandbox port 5433)
- [x] `ANTHROPIC_API_KEY` u `.env`
- [x] Budget: ~$0.40 (meta-gen ~$0.22 + pilot ~$0.10 + retry buffer ~$0.08)

## 9. Exit kriteriji (kraj 2B-1B)

- [ ] SandboxRunner podržava DML mode s rollback-om
- [ ] AnthropicClient ima `generate_structured_output()` metodu
- [ ] 30 concept YAML-ova u `backend/config/concepts/`, svi prolaze schema
- [ ] Pilot run generirao 12 tasks, report-iran u `data/generated_tasks/pilot/pilot_report.json`
- [ ] **~222 testova prolaze** (189 baseline + ~22 novih + ~11 modificiranih ali u istom skup-u)
- [ ] **0 promjena** u `prompt_builder.py`, `ast_analyzer.py` core interfejsima
- [ ] Tagovi `faza-2b-1b-meta-gen-complete` i `faza-2b-1b-complete` push-ani
- [ ] Pilot findings dokumentirani (u commit message ili kratki sažetak u repo)

---

## 10. Risk register

| Rizik | Vjerojatnost | Impact | Mitigacija |
|---|---|---|---|
| Meta-gen LLM ne prati schema strict (npr. tier mismatch) | Medium | Low | Schema validation u `parse_and_validate` + auto-retry s feedback |
| `tool_choice` ne radi kao očekivano (model proizvedi text umjesto tool_use) | Low | Medium | Default `tool_choice={"type":"tool","name":...}` je strogi mode; testirano u Anthropic SDK ≥0.97 |
| Meta-gen trošak premašuje $0.40 buffer | Low | Low | Per-concept cost log; abort ako kumulativni cost > $0.50 (hard cap u skripti) |
| SandboxRunner DML rollback fail-a u edge case-u (npr. nested transaction) | Medium | Medium | SAVEPOINT pattern (ne ROLLBACK na transaction level) izolira lokalno; +6 testova pokriva tipične scenarije |
| Pilot run otkriva systemic prompt template bug → 2B-2 zahtijeva veći fix | Medium | Medium | Po definiciji to je svrha pilot run-a — fix se primjenjuje u 2B-2 pre-batch, nije blocker za 2B-1B exit |
| Task validator regression u DML pass-through | Low | High | Existing 11 validator testova = regression net; novi `test_validator_dml_path` |
| Meta-gen produces semantic garbage (passes schema, ali sadržaj loše) | Medium | Low | Manual sanity review po YAML-u (~5 min × 23 = 2h overhead — accepted) |

---

## 11. Tehnološki dug i otvorena pitanja za 2B-2

| Stavka | Status | Rok |
|---|---|---|
| Prompt template fix (ako pilot otkrije problem) | TBD pilot results | 2B-2 |
| `--from-matrix` CLI flag za `generate_tasks.py` | Iz 2A errata, još uvijek defer | 2B-2 |
| Manual sanity review 23 meta-generated YAML-a | Soft requirement (~2h) | 2B-1B post-tag (može i nakon `meta-gen-complete` tag-a) |
| `index_usage` AST detector placeholder | 2A errata, plan kaže defer u Fazu 6 | Faza 6 |
| `null_handling` zaseban pilot test | Skipped iz pilot-a (testira se kroz secondary u 2B-2) | 2B-2 monitoring |

---

## 12. Reference

- `docs/faza-2b-1-context-dump.md` — original context dump za 2B-1A
- `docs/faza-2b-1b-context-dump.md` — kontekst za 2B-1B (CLI struktura, SDK API, schema)
- `docs/faza-2a-plan.md` §2 — distribucijska matrica 105 zadataka
- `docs/faza-2a-wrapup.md` §4 errata + §5 tech debt
- `docs/faza-1-domenski-model.md` §2.2 — concept descriptions za CONCEPT_META dict
- `backend/app/schemas/concept_config.py` — schema iz 2B-1A
- `backend/scripts/lib/api_client.py` — postojeća `generate()` metoda
- `backend/scripts/lib/sandbox_runner.py` — postojeća `execute()` metoda
- Anthropic SDK docs: tools + tool_choice — https://docs.claude.com/en/docs/build-with-claude/tool-use

---

## 13. Što slijedi nakon 2B-1B

**2B-1C — Validation tool (Streamlit + SQLite):**
- Dodati `streamlit` u `pyproject.toml`
- Streamlit web UI s filtrom (module/concept/decision), description + query preview, run query button, decision buttons (approve/reject/needs_fix), notes textarea
- SQLite persistence (`data/generated_tasks/manual_review.sqlite`)
- Završetak Faze 2B-1 (svi 30 YAML-ova + tool ready za 2B-3)

**2B-2 — Full generation run za 105 zadataka:**
- Refactor `generate_tasks.py` da podržava `--from-matrix` flag
- Batchevi po modulu s checkpoint između
- Apply prompt template fixes iz 2B-1B pilot findings (ako su otkriveni)
- Target: ~90/105 validated, ~15/105 failed

---

*Plan kraj. Start point: `git checkout main && git pull && git checkout -b faza-2b-1b-implementation && cd backend && uv run pytest -q` (verify clean baseline od 189 testova).*
