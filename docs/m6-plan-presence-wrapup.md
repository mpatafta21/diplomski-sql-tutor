# M6 plan-presence + `column_alias` — wrapup

**Datum:** 2026-08-14 · **Grana:** `m6-plan-presence` (s `main`a, `5a192c8`)
**Plan:** `docs/m6-transverzalni-korak-0.md` · **Nalazi:** ERRATA #66, #67, #68

| commit | sadržaj |
|---|---|
| `1e48bbb` | `make backup` nikad nije radio iz čistog klona (#67) |
| `b5cdd11` | plan-presence evaluacija + gate stabilnosti plana |
| `06a6f5f` | potpis plana nosi imena indeksa — `uses_index` sam po sebi laže |
| `56067bf` | M6 aktiviran s ispravnim zadacima; `column_alias` dobio zadatke |

**Nula promjena sheme. Nula novih ovisnosti. Nula izmjena na M1–M5 zadacima.**

---

# A — Grana je krenula od pretpostavke koja je pala

TODO je tri dana stajao na „M6 je neevaluabilan jer jezgra ocjenjuje po rezultatu". Točno,
ali nedovoljno. Mjerenje je pokazalo da **od 5 zatečenih M6 zadataka samo 1 nije pokvaren**
— tri tvrde o bazi neistinu (referentni upit daje Seq Scan iako opis obećava Index Scan),
a četvrti ne razlikuje ništa (`ORDER BY id LIMIT 1` uvuče `orders_pkey`, pa i anti-pattern
„koristi indeks").

Puni nalaz s brojkama: **ERRATA #66**.

🔴 **Da je grana izvedena kako je TODO opisivao — samo aktivirati M6 uz plan-presence —
isporučila bi tri zadatka koja padaju na vlastitom referentnom rješenju i jedan koji
prihvaća ono što zabranjuje.**

---

# B — Što je isporučeno

## B.1 Evaluacija: tvrdnja o planu se NE pohranjuje

Odbačena nova kolona i odbačen popis po `source_id` u kodu. **Zadatak već nosi tvrdnju o
planu — to je njegov `expected_query`**, pa se oba upita EXPLAIN-aju istovremeno i
uspoređuju im se potpisi:

```
PlanSignature(uses_index: bool, index_names: frozenset, join_methods: frozenset)
```

Bez migracije; tvrdnja ne može zastarjeti; preživljava reseed. Plan-grana se izvodi **samo**
za `PLAN_CHECKED_CONCEPTS`, pa je regresija na 80 zatečenih aktivnih zadataka dokazivo
nemoguća (i tvrdi je test).

## B.2 Dva gatea

**Stabilnost** (`plan_is_stable`) — potpis mora ostati nepromijenjen pod
`enable_seqscan=off` i `enable_hashjoin=off`. 🔴 **Nije izveden iz teorije nego iz flaky
testa:** tvrdnja o zadatku 79 prošla je izolirano a pala u punoj datoteci, jer mrtvi redci
iz rollbackanog DML-a drugog testa podignu `relpages` i prevrnu izbor plana.

**Diskriminacija** (pri autorstvu, `manual_tasks_m6.py`) — deklarirani anti-pattern mora
vratiti **iste retke** a **drugi potpis**. Ovaj gate bi odbio zadatak 83.

Uvozni gate stabilnosti je i u `sweep_task_integrity`, dakle u `make preflight`.

## B.3 Katalog

| koncept | aktivnih | neaktivnih | napomena |
|---|---|---|---|
| `index_usage` | **3** | 2 | task 81 zadržan + 2 nova |
| `explain_plan` | **2** | 2 | oba nova (Nested Loop vs Hash Join) |
| `column_alias` | **3** | 0 | + 4 sekundarna pojavljivanja |
| `join_condition` | 0 | 0 | odluka: zadatke NE dobiva |

92 zadatka ukupno, **88 aktivnih** (bilo 85 / 80). Novi su ručno autorski, ne kroz LLM
(#20). Deaktivirani se **ne brišu** — dokaz nalaza i negativan primjer gatea (#39).

`is_active` je sada **eksplicitan po zadatku** uz `deactivation_reason`, ne izveden iz
koncepta: neispravni su POJEDINI zadaci, a to koncept ne može izraziti.

## B.4 Recommender: Kat. C uklonjena

Dok M6 nije bio evaluabilan, maska 0.99 bila je obrana od ćorsokaka. Sada bi bila
**blokada** — Prolog preskače koncepte iznad praga, pa zadaci nikad ne bi bili ponuđeni.
Subfloor je time **prazan**, što je jača tvrdnja od popisa: nijedan koncept modula ≠ 0 nije
pod-resursiran.

---

# C — Dosežnost je MJERENA, ne zaključena

Poučak #25: „2 zadatka po konceptu ⇒ bedž dostižan" bio je račun koji je previdio da
koncept nikad nije bio ponuđen. Zato simulacija savršenog studenta kroz **stvarni**
preporučivač (`tests/test_m6_reachability.py`, 46 zadataka):

| pitanje | odgovor |
|---|---|
| posjećeni moduli | **0, 1, 2, 3, 4, 5, 6** |
| je li M6 dosežan | ✅ **DA** — oba koncepta ponuđena |
| ostaje li bedž `explorer` dostižan | ✅ **DA** (kriterij je narastao na {1..6} sam) |
| blokira li `column_alias` nizvodni `group_by` | ✅ **NE** (0.9356 ≥ 0.85) |
| nudi li preporučivač `column_alias` | 🔴 **NE, nijednom** |

---

# D — 🔴 Što je isporučeno SLABIJE nego što je odlučeno

**`column_alias` je dobio zadatke koje preporučivač nikad ne nudi** (ERRATA #68).

Koncept saturira **iznad** praga (0.9356) prije nego dođe na red, jer ima 4 sekundarna
pojavljivanja a Prolog bira samo koncepte **ispod** praga. To je **ERRATA #35 (ZPD escape)
po drugi put**.

Strah iz plana bio je suprotan — bojao sam se da će zapeti **ispod** praga i zaključati M2.
To se nije dogodilo; dogodilo se ogledalo tog problema.

**Zadaci nisu mrtvi:** dosežni su klikom na koncept u pregledu Modula (`resolve_task_for_concept`,
put iz #42/#43), i to je stvarno poboljšanje u odnosu na zatečeno stanje (redak je prije bio
neklikabilan, „nema zadataka"). Ali kroz „Sljedeći zadatak" se ne nude.

**Ne popravlja se** — popravak traži da BKT razlikuje primarna od sekundarnih ažuriranja,
što je izmjena ugovora `/mastery-history` i jezgre modela; #35 to već navodi kao nemoguće
bez novog polja.

---

# E — Živi dokaz kroz `/attempt`

Registriran račun, predaje kroz pun agentski lanac (ne kroz test harness):

| predaja | ishod |
|---|---|
| `index_usage` referentno | `is_correct=true`, **60 XP** |
| `index_usage` anti-pattern (CAST) | `plan_mismatch`, **0 XP** |
| `explain_plan` referentno | `is_correct=true`, **45 XP** |
| `explain_plan` anti-pattern | `plan_mismatch`, **0 XP** |

Poruka za `explain_plan` anti-pattern nosi **oba** signala:

> „Rezultat je točan, ali upit ne koristi indeks, a rješenje ga koristi; strategija spoja je
> Hash Join, a traži se Nested Loop."

🔴 `detail` ide i u hint payload, pa je test tvrdi da **ne sadrži referentni upit** —
govori što plan radi, a to opis zadatka od studenta ionako traži.

---

# F — Gateovi

| gate | ishod |
|---|---|
| `pytest` | ✅ **819 passed, 1 skipped, 0 failed** (bilo 783) |
| `make preflight` — sweep | ✅ **88/88**, 0 nestabilnih planova |
| `make preflight` — smoke | ✅ pun agentski lanac |
| `make backup` | ✅ (nakon popravka #67), restore verificiran |

Novi testovi: `test_plan_signature`, `test_plan_stability`, `test_sandbox_explain`,
`test_evaluation_plan`, `test_m6_reachability` (36 tvrdnji).

⚠️ **`ruff` nije instaliran u okolini** i Makefile nema lint target, pa formatiranje nije
strojno provjereno — stil je usklađen ručno prema okolnom kodu. Nova ovisnost se ne dodaje
bez odluke (CLAUDE.md).

---

# G — Eskalacije zamrznutog backenda

Po 🔒 politici, uz izričito odobrenje korisnika (2026-08-14):

- `agents/evaluation.py` — plan-grana, `plan_signature`, `plan_is_stable`
- `scripts/lib/sandbox_runner.py` — `explain()` (bez `ANALYZE`, pod `sandbox_readonly`)
- `agents/recommender_logic.py` — uklonjena Kat. C
- `agents/hint_llm.py` — opis vrste greške `plan_mismatch`
- `scripts/import_dataset.py` — `is_active` po zadatku

`plan_mismatch` je **konceptualni** signal pa namjerno NIJE u `_MECHANICAL_ERRORS` —
anti-pattern je stvarna zabluda, ne omaška.

---

# H — Otvoreno

- **ERRATA #68** — `column_alias` nije nuđen preporukom (gore, §D). Ne popravlja se.
- **`explain_plan` i `index_usage` se preklapaju u mehanizmu.** Oba se ocjenjuju istim
  potpisom; razlikuju se po tome što opis traži da student promisli (pristupni put vs
  strategija spoja). Dva `explain_plan` zadatka su uz to **istog oblika** (spoj
  `orders × order_items` uz selektivan filtar), razlikuju se po zamci (CAST vs aritmetika) i
  težini. Šire različitih parova nije bilo: `products`/`categories` su premali pa im planovi
  nisu stabilni (izmjereno).
- **Sandbox veličina isključuje dio gradiva.** Na 200 redaka planer indeks ne bira ni kad
  postoji. Povećanje bi prepisalo `expected_result` svih aktivnih zadataka — ne radi se.
- **Zadaci 79/80/82/83 ostaju u katalogu deaktivirani**, namjerno.
- Nedirnuto: `join_condition`, `_BLOCK_VALUE`, svi zadaci M1–M5, frontend.
