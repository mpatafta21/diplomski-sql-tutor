# FAZA 5.0 — WRAPUP: preduvjeti za HintAgenta

Grana `faza-5-hintagent`. Plan: [`faza-5-korak-0.md`](faza-5-korak-0.md).
Commiti: `b083ed8` (sekcija B), `bd07c2d` (sekcija C).

**Status: sekcije A, A1-dop, B, C, D, D-dop i E isporučene. Tag `faza-5-0-preduvjeti`
postavljen.**

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

### D — tekst suglasnosti
Odobreni odlomak umetnut na indeks 2 `SUDJELOVANJE_ODLOMCI`, odmah iza bilježenja.
Izmjereno renderom (Playwright), ne grepom: **350 znakova, znak-po-znak identično** na
`/register` i na Profilu → jedan izvor, ne dvije kopije. `npm run e2e` zelen.

🔴 **Zvjezdice iz odobrenog teksta su uklonjene.** Oba mjesta renderiraju odlomak kao
`<p>{odlomak}</p>` bez markdown parsera, pa bi `**Tekst tvog upita se ne šalje.**` prikazao
doslovne zvjezdice. Riječi su prenesene doslovno, podebljanje nije. Ako je naglasak
potreban, traži strukturnu izmjenu u oba renderera — v. §5.6.

Zaglavlje `participation.ts` dopunjeno: popis „namjerno nije ovdje" sada izrijekom kaže da
se **ne** tvrdi kako o studentovom radu ništa ne izlazi — brojčani pokazatelji izlaze.

## 4. Odstupanja od plana, sva namjerna

1. **`attempts.sqlstate` nije bio u planu §B.** Dodan na temelju A1-dop-1, uz izričitu
   potvrdu korisnika, jer druga revizija nad `attempts` u 5.1 košta više od jedne kolone
   sada.
2. **Indeks je `(user_id, created_at DESC)` kako je traženo**, iako bi PG isti plan dobio
   i iz ASC indeksa — btree se skenira u oba smjera. Forma, ne dobitak; zapisano u modelu.
3. **`hints` nije dobio UNIQUE nad `(error_type, concept_id)`** jer plan traži jednu
   reviziju. Jedinstvenost drži seeder, provjerava je test. Kandidat za 5.1 (§C.8).
4. **`feedback.ts:26` nije ispravljen** iako citira zastarjeli redak — sitnica u komentaru,
   nije dirana uz izmjenu teksta suglasnosti da diff ostane čitljiv. Za 5.2.
5. **Podebljanje u tekstu suglasnosti nije izvedeno** (v. §D gore) — riječi doslovno,
   markup ne.
6. **Tvrdnja „plan §2.5 kaže da se Anthropic SDK ne koristi u runtime sustavu" nije
   pronađena** ni u `faza-3-plan.md` (koji nema numerirane sekcije) ni igdje drugdje u
   `docs/`. Ispravljen je ekvivalentan netočan navod koji **postoji** — `CLAUDE.md:17`,
   gdje je Claude API bio opisan kao „offline task gen". Ako je mišljen neki drugi redak,
   nije izmijenjen jer nije nađen.

---

## 5. Što ostaje otvoreno

### 5.1 Preporučivač nema determinističan tie-break → **POPRAVLJENO drugdje, ERRATA #60**
Nađeno pri izvođenju exit kriterija „`pytest` zelen". Dokazano da nije uzrokovano fazom 5
— reproducirano na starom kodu i staroj shemi (`git stash` + `alembic downgrade`).

`load_concept_code_map` čitao je koncepte **bez `ORDER BY`**; `inject_mastery` asertira
Prolog fakte redoslijedom dobivenog dicta; `recommend_next/2` reže prvim rješenjem.
`run_seed()` prepisuje sve koncepte `on_conflict_do_update`om pri **svakom bootu**
(`make db-seed`), pa se preporuka mijenjala bez ijedne izmjene koda.

⇒ **Preporuka se mijenjala između pokretanja**, i to na živom sustavu, ne samo u testovima.

🔴 **Ispravak tvrdnje iz ranije verzije ovog dokumenta:** pisalo je da dva testa
preporučivača „padaju". Ne padaju stabilno — **flaky su**, jer ih zatekne poredak koji je
ostavio prethodni seed. Kvar je time gori nego što je bio opisan.

Popravljeno na grani `fix-recommender-determinizam` (s `main`a): kanonski
`ORDER BY modules.order_index, concepts.order_index, concepts.id`. **Ne ulazi u ovaj tag** —
blokira deployment neovisno o Fazi 5, pa ide zasebnim PR-om **prije** ovoga. Puna analiza,
produkcijski trag i odluka o promjeni ponašanja: `docs/errata.md` #60.

### 5.2 RIZIK: nema odvojene test baze
`pg_database` sadrži samo `tutor_main`. `pytest` piše u istu bazu koju koristi aplikacija,
pa je svaka nova shemska invarijanta odmah i produkcijska. Isti korijen kao ERRATA #40/#46.
Nalaz 5.1 gore je izravna posljedica tog rizika.

### 5.3 ERRATA #59 ostaje otvorena
Odlomak o vanjskoj usluzi **informira**, ali suglasnost se i dalje **ne bilježi** —
nosilac pristanka je čin registracije. Prije puštanja hinta u eval treba odluka: je li
informacija dovoljna ili traži zaseban, bilježen pristanak (nova kolona → migracija).
**Nije blokator** za gradnju iza `USE_LLM_HINTS=false`.

### 5.4 🔴 `attempts.sqlstate` je prazna obveza dok je 5.1 ne popuni
Izmjereno: kolona **nema nijednog pisca**, 0 od 35 pokušaja ima vrijednost. Isti obrazac
kao `hint_requested` (tvrdo kodiran na `False` od Faze 1, 0 `true` u bazi, a i dalje se
servira kroz `/attempts` i izvozi u `export_eval_data.py`).

Razlika je što `sqlstate` ima **imenovanog pisca i rok**: 5.1, lanac
`sandbox_runner → EvaluationOutcome → persist_attempt`. **Ako ga 5.1 ne popuni, kolona se
briše, ne ostavlja.** Detalji: [§C.6a plana](faza-5-korak-0.md).

### 5.6 Naglasak u ključnoj rečenici suglasnosti
„Tekst tvog upita se ne šalje." stoji kao obična rečenica. `SUDJELOVANJE_ODLOMCI` je polje
plain stringova koje oba renderera mapiraju identično, pa podebljanje traži strukturnu
izmjenu na obje površine. Odluka korisnika je li vrijedna.

### 5.5 `admin` (user_id 1) skuplja retke iz testova
Zapaženo usput: `attempts` je narastao s 34 na 35, `skill_mastery` 13 → 14, `streaks`
4 → 5, i svi novi redci pripadaju useru `admin`. Nijedan nije siroče — neki test koristi
zatečenog `admin` usera umjesto vlastitog i ne čisti za sobom. Izravna posljedica rizika
iz §5.2. Nije istraženo do kraja jer je izvan opsega 5.0.

---

## 6. Brojke

| mjera | vrijednost |
|---|---|
| tablica u `public` (bez `alembic_version`) | 18 (17 iz plana + `skill_mastery_history`) |
| redaka u `hints` | 32 s konceptom, 0 bez |
| novih testova | 182 (17 u sekciji B, 165 u sekciji C) |
| `pytest` | 670 prolazi, 2 padaju (v. §5.1), 1 preskočen |
| `attempts` koji krše novi CHECK | 0 |
