# FAZA 5.0 — WRAPUP: preduvjeti za HintAgenta

Grana `faza-5-hintagent`. Plan: [`faza-5-korak-0.md`](faza-5-korak-0.md).
Commiti: `b083ed8` (sekcija B), `bd07c2d` (sekcija C).

**Status: sekcije A, A1-dop, B, C isporučene. Sekcija D (tekst suglasnosti) ČEKA
potvrdu — tag `faza-5-0-preduvjeti` zato NIJE postavljen.**

---

## 1. Što je isporučeno

### Migracija `15a84352666f`
Jedna Alembic revizija, tri promjene:

| objekt | oblik |
|---|---|
| `hint_requests` | 17. tablica; `hint_text` NULL-abilan + `CHECK (source='unavailable' OR hint_text IS NOT NULL)`; `CHECK source IN ('llm','fallback','unavailable')`; `user_id` i `after_attempt_id` ON DELETE CASCADE, `task_id` i `hint_id` bez; indeks `(user_id, created_at DESC)` |
| `attempts.sqlstate` | `VARCHAR(5) NULL`, **prazan u 5.0** — puni ga 5.1 |
| `ck_attempts_error_type_when_incorrect` | `is_correct = true OR error_type IS NOT NULL` |

### Katalog hintova
32 retka (8 koncepata × 4 koncept-ovisna tipa), `row_mismatch` blok prvi.
Izvor: [`hints_data.py`](../backend/app/db/hints_data.py); seeder:
[`seed_hints.py`](../backend/scripts/seed_hints.py).

### Novi testovi
`test_hint_requests.py` (11), `test_purge_demo_users.py` (2), `test_hints_seed.py` (165),
proširen `test_db_schema.py` (16 → 20 testova, 17 tablica).

---

## 2. Što je izmjereno (a ne pročitano)

### A1 — `detail` po tipu greške
Živa baza, 13 redaka s `detail`om. **Dva tipa propuštaju studentov upit:**

- `execution_error` — PG `LINE n:` kontekst nosi **doslovni redak upita**. Jedan živi
  uzorak sadrži i zaostali komentar iz editora: `ORDER BY category_id ASC;- Napiši svoj
  SQL upit ovdje`.
- `wrong_columns` — nabraja **studentove aliase** (`product_count`, `count`) uz očekivane
  stupce.

Čisti su `row_mismatch` (samo brojevi i indeks retka, sve 4 varijante), `empty_result`
(broj), `syntax_error` i `unsupported_eval` (konstante). `timeout` nema nijedan živi
uzorak → tretiran kao nedokazano čist.

**Presuda: selektivni B+**, uži od pretpostavke u planu. Za `wrong_columns` se očekivani
stupci u 5.1 **rekonstruiraju** iz `task.expected_result[0].keys()`, a pohranjeni
`detail` string se **ne prosljeđuje**.

### A1-dop-1 — `sqlstate`
`psycopg.Error.sqlstate` je dohvatljiv pri hvatanju i gubi se u `str(e)` (`'42703' in
str(e)` → `False`). Osam sondi nad živim sandboxom potvrdilo je da su kodovi zatvoren
šifrarnik bez studentovih znakova, i da `42803` (`GroupingError`) pogađa `group_by` i
`having_filter`, a `42702` (`AmbiguousColumn`) `multi_table_join` i `inner_join` — četiri
od osam top koncepata. Kolona dodana u 5.0, puni se u 5.1.

### A2 — pisci `attempts`
Svih 7 mjesta koja konstruiraju `Attempt(...)` + `seed_demo_user.py` (ide kroz HTTP
`POST /attempt`) postavljaju `error_type` kad je ishod netočan. Živa baza: **0 kršenja**
(13 netočnih svi s tipom, 21 točan svi bez). CHECK je siguran.

### A3 — otključavanje bez reloada
Playwright, presretanje mreže, netočna predaja na `/task/15`:

```
+ 8200 ms  GET /task/15   → 200   (montiranje)
+10339 ms  POST /attempt  → 200
+10376 ms  GET /task/15   → 200   ← refetch
```

Pečat instance stranice nepromijenjen, URL nepromijenjen → **nema reloada**. Radi jer je
`["task", taskId]` već u `invalidateQueries` listi `useSubmitAttempt` (dodano u 4.3c radi
`solved` indikatora) i `TaskPage` drži aktivan `useTask` observer.

🔴 **Razlika od 37 ms je svojstvo LOKALNOG mjerenja, ne sustava.** Vite dev server i
backend na `localhost`, bez HTTPS-a. Na VPS-u s TLS handshakeom i agentskim lancem prozor
je bitno veći. Brojka se u radu smije navesti isključivo uz kvalifikaciju „mjereno
lokalno", i posljedica joj je provjera u ruti (§C.3), a ne zaključak „prozor je zanemariv".

---

## 3. Gdje su A1–A3 promijenili plan

| plan je pretpostavljao | mjerenje je pokazalo | posljedica |
|---|---|---|
| „pun B+ ili selektivni, npr. `detail` za `wrong_columns` i `row_mismatch`" | `wrong_columns` je **najgori** tip — nosi studentove aliase | selektivni B+ isključuje `wrong_columns` string; šalju se samo rekonstruirani ključevi |
| `execution_error` bi ostao bez signala | `sqlstate` je čist i koncept-specifičan | nova kolona `attempts.sqlstate` u istoj migraciji (odluka korisnika) |
| CHECK bi mogao srušiti testove | svi pisci postavljaju tip; jedina zamka je default u tvornici `_outcome()` | tvornica stegnuta u istom commitu |
| otključavanje bi moglo tražiti izmjenu u 5.2 | invalidacija već postoji | 5.2 ne mora dodati ništa za `["task", taskId]`; mora paziti samo ako brojač limita uvede vlastiti query key (§C.4) |

---

## 4. Odstupanja od plana, sva namjerna

1. **`attempts.sqlstate` nije bio u planu §B.** Dodan na temelju A1-dop-1, uz izričitu
   potvrdu korisnika, jer druga revizija nad `attempts` u 5.1 košta više od jedne kolone
   sada.
2. **Indeks je `(user_id, created_at DESC)` kako je traženo**, iako bi PG isti plan dobio
   i iz ASC indeksa — btree se skenira u oba smjera. Forma, ne dobitak; zapisano u modelu.
3. **`hints` nije dobio UNIQUE nad `(error_type, concept_id)`** jer plan traži jednu
   reviziju. Jedinstvenost drži seeder, provjerava je test. Kandidat za 5.1 (§C.8).
4. **`feedback.ts:26` nije ispravljen** iako citira zastarjeli redak — 5.0 ne dira
   `frontend/src/`. Za 5.2.

---

## 5. Što ostaje otvoreno

### 5.1 🔴 Preporučivač nema determinističan tie-break (NOVO, nije iz faze 5)
Nađeno pri izvođenju exit kriterija „`pytest` zelen". Dokazano da nije uzrokovano fazom 5
— reproducirano na starom kodu i staroj shemi (`git stash` + `alembic downgrade`).

`load_concept_code_map` čita koncepte **bez `ORDER BY`**; `inject_mastery` asertira Prolog
fakte redoslijedom dobivenog dicta; Prolog vraća prvo rješenje. `test_seed.py` pokreće
`run_seed()` dvaput, seed radi `on_conflict_do_update`, i fizički poredak heapa se mijenja.

⇒ **Pokretanje `pytest`-a mijenja koncept koji preporučivač vrati živom studentu.**
`inner_join` i `scalar_subquery` imaju isti `order_index` (1) i isti `p_l` (0.15), pa
odlučuje poredak redaka iz PostgreSQL-a. Neovisno o `PYTHONHASHSEED`.

Padaju `test_recommender_logic::test_advanced_recommends_inner_join` i
`test_recommender_agent::test_concurrent_recommends_serialized_and_correct`. Detalji u
[§D.4 plana](faza-5-korak-0.md).

### 5.2 RIZIK: nema odvojene test baze
`pg_database` sadrži samo `tutor_main`. `pytest` piše u istu bazu koju koristi aplikacija,
pa je svaka nova shemska invarijanta odmah i produkcijska. Isti korijen kao ERRATA #40/#46.
Nalaz 5.1 gore je izravna posljedica tog rizika.

### 5.3 Sekcija D — tekst suglasnosti
ERRATA #59 i dopuna `participation.ts` čekaju potvrdu. Blokator za puštanje hinta u eval,
**ne** za gradnju iza `USE_LLM_HINTS=false`.

### 5.4 Sekcija E — usklađivanje dokumenata s odlukom o provideru
`CLAUDE.md:17` i `faza-3-plan.md:240` još tvrde OpenAI/GPT-4o-mini. Nije izvedeno u ovom
prolazu.

---

## 6. Brojke

| mjera | vrijednost |
|---|---|
| tablica u `public` (bez `alembic_version`) | 18 (17 iz plana + `skill_mastery_history`) |
| redaka u `hints` | 32 s konceptom, 0 bez |
| novih testova | 182 (17 u sekciji B, 165 u sekciji C) |
| `pytest` | 670 prolazi, 2 padaju (v. §5.1), 1 preskočen |
| `attempts` koji krše novi CHECK | 0 |
