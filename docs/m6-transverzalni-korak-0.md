# M6 + transverzalni koncepti — KORAK 0 (plan)

**Datum:** 2026-08-14 · **Grana:** `m6-plan-presence` (s `main`a, `5a192c8`)
**Status:** čeka odobrenje

---

# A — Zatečena pretpostavka je PALA (mjereno, ne pročitano)

TODO je tri dana stajao na tvrdnji „M6 je neevaluabilan jer jezgra ocjenjuje po rezultatu".
Ta tvrdnja je **točna, ali nije bila cijeli problem**. Mjerenje nad živim sandboxom
2026-08-14:

## A.1 Rezultatska evaluacija stvarno ne razlikuje A od B — potvrđeno

Anti-pattern iz zadatka 79 (`WHERE LOWER(email) = LOWER('skodamartina@example.org')`)
vraća **bajt-identičan redak** kao index-friendly verzija. Da se M6 samo aktivirao, student
koji napiše upravo ono što zadatak zabranjuje dobio bi „točno". To je ERRATA #29 u
najoštrijem obliku: ondje je alternativna formulacija nuspojava, ovdje je **predmet
poučavanja**.

## A.2 🔴 Gore: 3 od 5 M6 zadataka tvrde neistinu o ovoj bazi

`EXPLAIN (FORMAT JSON)` nad **referentnim** upitima svih 5 zadataka:

| task | koncept | plan referentnog upita | opis zadatka tvrdi |
|---|---|---|---|
| 79 | `explain_plan` | 🔴 **Seq Scan** | „PostgreSQL … izvesti Index Scan" |
| 80 | `explain_plan` | 🔴 **Seq Scan** | Index Scan |
| 81 | `index_usage` | Bitmap Index Scan ✅ | slaže se |
| 82 | `index_usage` | 🔴 **Seq Scan** | Index Scan |
| 83 | `index_usage` | Index Scan ✅ | slaže se |

Referentno rješenje tri zadatka **ne bi prošlo vlastitu provjeru**. Plan-presence
evaluacija sama, bez diranja zadataka, ne bi bila dovoljna — bila bi samo mehanizam koji
tri zadatka proglasi netočnima.

## A.3 Uzrok NIJE kvar — planer je u pravu

`customers_email_key` postoji i upotrebljiv je: uz `enable_seqscan=off` plan prelazi na
Index Scan. Cijene: **Seq Scan 5.50 vs Index Scan 8.16** na 200 redaka. Na tako maloj
tablici sekvencijalni prolaz *jest* jeftiniji.

🔴 **Sva tri pokvarena zadatka gađaju `customers` (200 redaka).** Oba ispravna gađaju veće
tablice. To nije slučajnost nego pravilo, i ono je ključ izvedivosti:

| oblik upita | tablica (redaka) | plan |
|---|---|---|
| `customers WHERE email = …` | 200 | 🔴 Seq Scan |
| `orders WHERE customer_id = 42` | 1000 | Bitmap Index Scan ✅ |
| `orders WHERE customer_id::text = '42'` | 1000 | Seq Scan (anti-pattern ✅) |
| `order_items WHERE order_id = 500` | 3000 | Bitmap Index Scan ✅ |
| `orders ORDER BY order_date DESC LIMIT 10` | 1000 | Index Scan ✅ |
| `orders LIMIT 10` (bez ORDER BY) | 1000 | Seq Scan (kontrast ✅) |
| `reviews WHERE product_id = 3` | 500 | Bitmap Index Scan ✅ |

⇒ **Zadatke JE moguće napisati** — samo ne nad `customers`.

## A.4 `explain_plan` dobiva vlastiti identitet (također mjereno)

Da `explain_plan` ne bi bio duplikat `index_usage`, treba mu svojstvo plana koje nije
„koristi li indeks". **Strategija spoja je kontrolirana i stabilna:**

| upit | plan |
|---|---|
| `orders ⋈ order_items` bez filtra | **Hash Join** + Seq Scan |
| isti spoj uz `WHERE o.customer_id = 42` | **Nested Loop** + Bitmap Index Scan |

Time je `explain_plan` = „kako filtar mijenja strategiju spoja", `index_usage` = „kako
oblik uvjeta odlučuje hoće li se indeks upotrijebiti". Dva različita cilja učenja.

---

# B — Odluke (korisnik, 2026-08-14)

1. **M6:** plan-presence evaluacija **+ prepisivanje zadataka**.
2. **Transverzalni:** zadatke dobiva **samo `column_alias`**; `join_condition` ostaje
   Kat. A bez zadataka.

---

# C — Dizajn evaluacije: potpis plana, BEZ nove kolone

## C.1 Odbačeno: pohraniti tvrdnju o planu uz zadatak

Prva ideja bila je nova kolona (`tasks.plan_assertion JSONB`) ili konstanta u kodu s
popisom po `source_id`. Oboje odbačeno:

- **kolona** = migracija sheme (CLAUDE.md traži pitanje prije toga) tjedan prije evala,
- **konstanta u kodu** = sadržaj kataloga u evaluacijskoj jezgri; može zastarjeti tiho,
  ista klasa kao docstring iz ERRATE #45.

## C.2 Odabrano: usporedba potpisa referentnog i predanog plana

Zadatak **već nosi** tvrdnju o planu — to je njegov `expected_query`. Evaluacija zato
EXPLAIN-a **oba** upita i uspoređuje potpise:

```
plan_signature(plan) = (koristi_indeks: bool, metode_spoja: frozenset[str])

INDEX_ACCESS_NODES = {"Index Scan", "Index Only Scan", "Bitmap Index Scan"}
JOIN_METHOD_NODES  = {"Nested Loop", "Hash Join", "Merge Join"}
```

Predani upit prolazi ako mu je potpis **jednak** potpisu referentnog upita (uz redovnu
usporedbu redaka, koja ostaje netaknuta).

**Zašto je to bolje od pohranjene tvrdnje:**

- **ne može zastarjeti** — referentni upit i tvrdnja su isti objekt,
- **nula promjena sheme, nula podataka u kodu**,
- **sam bi uhvatio zatečeni kvar**: za zadatke 79/80/82 potpis referentnog upita je
  „ne koristi indeks", pa tvrdnja postaje prazna → uvozni gate (§C.4) ih odbija,
- **preživljava reseed sandboxa** — obje strane se mjere u istom trenutku nad istim
  podacima, pa se pomiču zajedno.

🔴 **Ne uspoređuju se goli skupovi čvorova.** `Sort`, `Limit`, `Aggregate`, `Hash` i
`Bitmap Heap Scan` variraju s formulacijom i nisu predmet ovih koncepata; `Index Scan` i
`Bitmap Index Scan` su za cilj učenja **isti ishod** (indeks je upotrijebljen). Zato
potpis, a ne jednakost skupova.

## C.3 Opseg i sigurnost

- Grana se izvodi **isključivo** za `primary_concept_code in PLAN_CHECKED_CONCEPTS`.
  Nijedan zadatak M1–M5 je ne dodiruje → **dokazivo nula regresije** na 80 aktivnih
  zadataka.
- `EXPLAIN` **bez `ANALYZE`** — plan se ne izvršava. Potvrđeno da radi pod
  `sandbox_readonly` (mjereno).
- Guard: ako je predani upit sam `EXPLAIN …`, vraća se uputa umjesto `EXPLAIN EXPLAIN`
  sintaksne greške.
- DML zadatak ne može ući u plan-provjeru (M6 je SELECT-only); tvrdi se testom.
- Cijena: **2 dodatna EXPLAIN-a po pokušaju**, samo na M6.

## C.4 Uvozni gate (ovo je trajni dobitak)

`sweep_task_integrity.py` dobiva provjeru: **M6 zadatak je ispravan samo ako potpis
njegovog referentnog upita nije prazan** (koristi indeks, ili ima određenu metodu spoja).
Tri zatečena pokvarena zadatka su dokaz da gate treba postojati — dodaje se **s njima kao
negativnim testom**.

---

# D — Katalog zadataka

| koncept | zadatak | radnja |
|---|---|---|
| `index_usage` | 81 (Bitmap Index Scan) | **ZADRŽAN**, aktivira se |
| `index_usage` | 83 (Index Scan) | **ZADRŽAN**, aktivira se |
| `index_usage` | 82 (Seq Scan) | **ostaje deaktiviran** + zabilježen kao netočan |
| `explain_plan` | 79, 80 (Seq Scan) | **ostaju deaktivirani** + zabilježeni kao netočni |
| `explain_plan` | 2 nova | **ručno autorska** (Hash Join vs Nested Loop, §A.4) |

⇒ oba koncepta završavaju s **2 aktivna primarna zadatka** = prag izlaska iz subfloora
(#27). Zadaci 79/80/82 se **ne brišu** — ostaju u katalogu kao dokaz nalaza, kao i 5
deaktiviranih dosad.

🔴 Prije aktivacije **provjeriti opise 81 i 83**: 81 stvarno daje *Bitmap* Index Scan, a
opis možda tvrdi „Index Scan". Po politici iz #33 (tvrdnja nosi izmjerenu brojku) opis
mora odgovarati mjerenju.

Novi zadaci pišu se obrascem `manual_tasks_2b2.py` (`generation_method=manual`), **ne**
kroz LLM — #20 zabranjuje regeneraciju bez izričite odluke.

---

# E — `column_alias`

**3 nova ručno autorska zadatka**, tier easy, modul 0.

🔴 **Tri, ne dva — i to je posljedica analize, ne opreza.** Čim dobije zadatke,
`column_alias` ispada iz Kat. A (`transversal_concepts` traži count == 0). Kako je modul 0,
**subfloor ga ne hvata** (Kat. B traži modul ≠ 0) → postaje običan koncept s tier priorom
0.30. Nizvodni `group_by` tada traži `column_alias ≥ 0.85`.

**Rizik koji to otvara:** ako student riješi sve zadatke a ostane ispod 0.85,
`concepts_with_available_tasks` ga ispusti (nema neriješenih), a `group_by` ostaje
zaključan. Postoji rezerva (`concepts_with_tasks` dopušta ponavljanje riješenog), ali
ponavljanje nosi 0 XP (#41). Treći zadatak i 4 postojeća sekundarna pojavljivanja spuštaju
vjerojatnost tog stanja.

**Obavezan gate:** simulacija u stilu #25/#27 — student koji točno rješava sve ponuđeno
mora dovesti `column_alias` iznad 0.85 **i** otključati `group_by`. Ako simulacija to ne
pokaže, odluka se vraća korisniku (opcija: `column_alias` vratiti u Kat. A).

`join_condition` se **ne dira** — ostaje Kat. A, 0 zadataka.

---

# F — Testovi koje ovo mijenja

`UNSUPPORTED_CONCEPTS` prestaje biti „neevaluabilni" i postaje `PLAN_CHECKED_CONCEPTS`.
Zatečeni potrošači koje treba prepisati:

| datoteka | što tvrdi danas |
|---|---|
| `test_evaluation.py:195,207` | explain_plan/index_usage → `unsupported_eval` |
| `test_recommender_logic.py:178` | `subfloor == set(UNSUPPORTED_CONCEPTS)` |
| `test_recommender_logic.py:212,550,573,577,588,603,616,628` | maska i ćorsokak |
| `test_recommender_no_dead_end.py:173` | maskirani skup |
| `test_api_task_for_concept.py:197` | 404 za M6 koncepte |
| `test_api_read_endpoints.py:373` | komentar o 0 XP + BKT kazni |
| `test_hint_payload.py:33,44` · `test_misconception_logic.py:103` | `unsupported_eval` kao mehanička greška |

🔴 **`unsupported_eval` se NE briše iz taksonomije** — ostaje kao ishod za slučaj da
plan-provjera ne uspije (npr. EXPLAIN padne). Hint sloj (`hint_llm.py:73`,
`hint_agent.py:76`) time ostaje ispravan bez izmjene.

Novi testovi (TDD, prvo crveni):
1. potpis plana: index vs anti-pattern (`::text`, `LOWER()`) — anti-pattern **pada**
2. potpis plana: Hash Join vs Nested Loop
3. točni redci + pogrešan plan → **incorrect** (jezgra nalaza A.1)
4. `EXPLAIN …` kao predani upit → uputa, ne 500
5. M1–M5 zadatak nikad ne ulazi u plan-granu
6. uvozni gate odbija zadatke 79/80/82 (negativan smjer, poučak #39)
7. simulacija: `column_alias` prelazi 0.85 i otključava `group_by`

---

# G — Gateovi prije mergea

`pytest` (783 + novi) · `make preflight` · `sql-task-validator` nad svim novim zadacima ·
`npm run e2e` · `code-review` plugin.

🔴 **`make backup` PRIJE prvog pokretanja** — mijenja se katalog zadataka u živoj
`tutor_main` (#37).

---

# H — Što ovaj plan NE tvrdi

- Ne tvrdi da će itko u evalu doći do M6: `prerequisite(index_usage, explain_plan)` i
  `prerequisite(explain_plan, {multi_table_join, group_by})` znače da je M6 nizvodno od
  savladanog M2+M3. **Vrijednost je u potpunosti sustava i u nalazu, ne u eval podacima.**
- Ne tvrdi da je potpis plana otporan na promjenu PostgreSQL verzije. Vezan je uz PG 16 i
  zatečeni Faker seed; obje strane usporedbe mjere se istovremeno, pa se pomak dogodi
  zajedno — ali **kombinacija koja bi obje strane pomaknula različito nije isključena**.
- Ne dira `join_condition`, `_BLOCK_VALUE`, ni jedan zadatak M1–M5.
