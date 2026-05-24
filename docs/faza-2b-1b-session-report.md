# Faza 2B-1B — Session report (11.05.2026)

## Commtiano (branch: `faza-2b-1b-implementation`)

| Commit | Što |
|--------|-----|
| `66c4c94` | SandboxRunner DML support s rollback (6 testova) |
| `3acccd3` | `generate_structured_output()` tool-use API (5 testova) |
| `eacd186` | Code review #1 fix — error wrapping + 2 testa |
| `e1bd3fd` | meta_gen.py library s 1× auto-retry (8 testova) |
| `a6e2358` | 23 meta-generirana YAML-a + meta_generate_yamls.py CLI |
| `bba4b21` | pilot_run.py + smoke testovi + task_validator dml fix |
| `ecc7e7b` | fix: ThinkingBlock u generate() — skip non-text content blocks |

Tag `faza-2b-1b-meta-gen-complete` postoji lokalno, **nije push-an na remote**.

## Što je napravljeno u ovoj sesiji

- Popravljen bug u `task_validator.py`: `_check_result_match()` nije primala `dml` parametar
- Pokrenuta dva pilot run-a (live API, ~$0.15 ukupno)
- Otkriven i popravljen crash bug: **`ThinkingBlock` u `api_client.py`** — `content[0].text` pucalo kad Claude koristi extended thinking za kompleksne upite
- Dodan test `test_generate_skips_thinking_block_extracts_text` (13/13 pass)

## Pilot run findings

Pilot je pokrenuo 12 zadataka (2 × 6 koncepta). Svi su failali. Otkrivena 4 problema:

### 1. `secondary_concepts` max=2 — 100% fail rate

**Uzrok:** `GeneratedTask` schema ima `max_length=2` na `secondary_concepts` polju, ali `user_template.md` to ne komunicira LLM-u. LLM uvijek vraća 3-4 stavke.

**Fix za 2B-2:** Dodati u `user_template.md`:
```
"secondary_concepts": ["max 2 items — only the 2 most relevant"]
```

### 2. Plain tekst umjesto JSON

**Uzrok:** Za koncepte `right_join`, `scalar_subquery`, `explain_plan` — LLM piše analizu na hrvatskom/engleskom umjesto JSON outputa. Prompt ne forsira JSON output dovoljno jako.

**Fix za 2B-2:** Dodati na kraj `user_template.md`:
```
Output ONLY the JSON object. Do not explain, do not think out loud. Start with { and end with }.
```

### 3. INSERT DML — "permission denied"

**Uzrok:** Docker sandbox volumen je inicijaliziran **prije** nego je `sandbox_readwrite` role dodan u `docker/postgres-sandbox/init.sql`. PostgreSQL `init.sql` se izvršava samo jednom (pri prvom pokretanju s praznim volumenom), pa grantovi nikad nisu primijenjeni.

**Fix za 2B-2:** Ručni grant u sandbox kontejneru:
```bash
docker exec -it sql-tutor-pg-sandbox psql -U sandbox_admin -c \
  "GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ecommerce_v1 TO sandbox_readwrite;"
```

### 4. ThinkingBlock crash — POPRAVLJENO

**Uzrok:** `api_client.py` linija 83 pretpostavljala `msg.content[0]` uvijek `TextBlock`. Claude koristi extended thinking za kompleksne upite (`explain_plan d=4`) i vraća `ThinkingBlock` kao prvi element.

**Fix (committan u `ecc7e7b`):**
```python
# Prije:
content=msg.content[0].text if msg.content else ""

# Poslije:
content=next((b.text for b in msg.content if hasattr(b, "text")), "")
```

## Što preostaje do kraja faze 2B-1B

### Korak 8 (djelomično): Pokrenuti pilot i dobiti pilot_report.json

```bash
# 1. Fix DML permissions
docker exec -it sql-tutor-pg-sandbox psql -U sandbox_admin -c \
  "GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ecommerce_v1 TO sandbox_readwrite;"

# 2. Pokrenuti pilot
cd /root/projects/diplomski-sql-tutor/backend
uv run python -m scripts.pilot_run
```

Pilot će i dalje failati na secondary_concepts i plain-text problemima, ali će **završiti** i generirati `pilot_report.json`.

### Korak 9: Code review #2 + final

```bash
# Code review pilot_run.py + meta_gen.py
# Final test suite run (~222 testova)
uv run pytest -q

# Tag i push
git tag faza-2b-1b-complete
git push origin faza-2b-1b-implementation
git push origin faza-2b-1b-meta-gen-complete faza-2b-1b-complete
```

### PR na main

Nakon taga, otvoriti PR `faza-2b-1b-implementation → main`.
