# M6 plan-presence + `column_alias` — wrapup

**Datum:** 2026-08-14 · **Grana:** `m6-plan-presence` (s `main`a, `5a192c8`)
**Plan:** `docs/m6-transverzalni-korak-0.md` · **Nalazi:** ERRATA #66–#72

| commit | sadržaj |
|---|---|
| `1e48bbb` | `make backup` nikad nije radio iz čistog klona (#67) |
| `b5cdd11` | plan-presence evaluacija + gate stabilnosti plana |
| `06a6f5f` | potpis plana nosi imena indeksa — `uses_index` sam po sebi laže |
| `56067bf` | M6 aktiviran s ispravnim zadacima; `column_alias` dobio zadatke |
| `8807288` | nalazi code reviewa — taksonomija razdvojena, poruke ispravljene (§G2) |
| `ed0a34d` | `plan_unavailable` prestaje biti ishod pokušaja — 503 (§G3) |

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
| `pytest` | ✅ **872 passed, 1 skipped, 0 failed** (bilo 783) |
| `make preflight` — sweep | ✅ **88/88**, 0 nestabilnih planova |
| `make preflight` — smoke | ✅ pun agentski lanac |
| `npm run e2e` | ✅ **4 passed**, teardown čist |
| `npm run build` (tsc + vite) | ✅ |
| `prettier --check` · `oxlint` | ✅ (samo zatečena `only-export-components` upozorenja) |
| `make backup` | ✅ (nakon popravka #67), restore verificiran |
| `code-review` (high) | ✅ 9 nalaza, svi popravljeni — v. §G2 |
| namjerni kvarovi | ✅ **6 testova viđeno kako pada** — v. §G3.4 i ERRATA #69 |

Novi testovi (oba kruga): `test_plan_signature`, `test_plan_stability`,
`test_sandbox_explain`, `test_evaluation_plan`, `test_m6_reachability`,
`test_plan_unavailable_flow`, `test_error_taxonomy_contract` — **91 tvrdnja**.

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
- **(drugi krug)** `agents/messages.py` — `ERROR_PLAN_UNAVAILABLE` (protokolna riječ koju
  dijele Evaluator i Coordinator)
- **(drugi krug)** `agents/evaluator_agent.py` — rani izlaz + `_refuse_plan_unavailable`
- **(drugi krug)** `agents/coordinator.py` — grana na **performativ** u UPDATE, uvjet u
  RESPOND. 🔴 Mehanika tokova (utori, dispatcher, `_open_flow`/`_release_flow`,
  `_flow_template`) **nije dirana** — dokazano izvršenjem, ne argumentom (§G3.4)
- **(drugi krug)** `app/api/routes.py` — 503 uz `coordinator_busy`

`plan_mismatch` je **konceptualni** signal pa namjerno NIJE u `_MECHANICAL_ERRORS` —
anti-pattern je stvarna zabluda, ne omaška.

---

# G2 — Code review: 9 nalaza, svi popravljeni (`8807288`)

Recenzija je čitala `main...HEAD` i **provjeravala hipoteze nad živom bazom**, ne
rezoniranjem — time je jedan sumnjivi nalaz i oborila (zatečeni aktivni zadatak 81 *ipak*
razlikuje svoj anti-pattern).

**Najozbiljniji nalaz je bio u frontendu, ne u novoj logici.** `plan_mismatch` nije bio ni u
`ERROR_TEXT` ni u `TEXT_DETAIL_TYPES`, pa je student na anti-pattern vidio *„Ocjenjivanje
nije uspjelo — pokušaj ponovno predati rješenje"*, a jedinu upotrebljivu uputu — pedagoški
detalj — u sivom mono bloku za tehničke ispise. 🔴 Poruka je tvrdila **kvar sustava** ondje
gdje je student napisao ispravan SQL. Backend je bio točan cijelo vrijeme; isporuka nije.

Ostali nalazi po klasama:

| # | nalaz | zašto je bitno |
|---|---|---|
| 2 | EXPLAIN guard posuđivao `plan_mismatch` | konceptualni signal nosi misconception + BKT kaznu; zalijepljen EXPLAIN je omaška → vlastiti `explain_submitted` |
| 3 | neuspjeh EXPLAIN-a → `unsupported_eval` | sweep tvrdi da ih ima **točno nula** → jedan prolazni timeout trajno obori `make preflight` → `plan_unavailable` |
| 4 | `_plan_mismatch_detail` nije gledao `index_names` | grana zbog koje su imena indeksa i uvedena degradirala je na „plan izvedbe se razlikuje" |
| 5 | `_BY_DESIGN_UNSUPPORTED` ostao jednak M6 konceptima | 🔴 od aktivacije bi se **svaki M6 pad tiho izuzimao iz gatea** |
| 6 | `plan_mismatch` izvan `DETAIL_SAFE_TYPES` | LLM ne bi dobio jedini koristan podatak o grešci |
| 7 | `is_active` parsiranje nije fail-closed | nepoznata vrijednost tiho znači NEAKTIVAN → zadatak nestane bez poruke |
| 8 | komentar tvrdio da zastavice „samo dodaju opcije" | netočno: `enable_seqscan=off` prevrće `uses_index`; stvarna restrikcija sada zapisana |
| 9 | zastarjeli docstring modula | opisivao uklonjenu granu i nepostojeću konstantu |

🔴 **Obrazac vrijedan bilježenja:** nalazi 2, 3 i 5 su svi ista greška — **novo ponašanje
ugurano u zatečenu kategoriju** (`plan_mismatch` za dvije različite stvari,
`unsupported_eval` za treću, M6 koncepti i dalje „by design unsupported"). Svaki put je
posljedica bila da neki uzvodni potrošač tiho radi krivu stvar. Taksonomija grešaka je
ugovor s pet potrošača (frontend, misconceptions, hint payload, hint LLM, sweep); dodavanje
ponašanja bez novog imena znači da barem jedan od njih dobije laž.

---

# G3 — Drugi krug: `plan_unavailable` prestaje biti ishod pokušaja (#69–#72)

## G3.1 Nalaz je nastao iz revizije vlastitog popravka

Nalaz 3 iz §G2 uveo je `plan_unavailable` da bi razdvojio infrastrukturnu smetnju od
`unsupported_eval`. Revizija tog imena otkrila je da je **cijela kategorija cijelo vrijeme
pisala kvar sustava u `attempts`** — samo pod drugim imenom. Nalaz nije uveden ovom granom;
učinjen je vidljivim.

Puni brojevi: **ERRATA #69**. Najjača brojka za rad: student s `p_l = 0.80` pada na
**0.46** umjesto da naraste na 0.97 — dakle jedna smetnja košta više usred učenja nego na
početku.

## G3.2 Odluka: opcija 1 (503), i zašto je 2 odbijena

`plan_unavailable` **ne stvara pokušaj**. Odbijena je opcija „perzistiraj, preskoči BKT i
kredit" jer bi tražila da `attempts` nosi **dvije uloge** — zapis o studentovom radu i zapis
o kvaru sustava. Isti obrazac je na ovoj grani već bio uzrok kvara (`_BLOCK_VALUE`: jedna
maska za dva razloga) i razlog uklanjanja `entry_task_id`. **Podatak o smetnji ide u log, ne
u instrument.** Kategorija je jednočlana: `plan_unavailable` je jedini `error_type` gdje
nije zakazao student.

## G3.3 🔴 Zašto proširenje `_flow_template` NIJE bilo aditivno

Prva razmatrana izvedba dodavala je `attempt-result` granu u korelacijski router. Odbijena:
**nije aditivna u učinku**. `task_not_found` je također `attempt-result` koji danas ne
stiže do toka, pa bi ga ista grana usput promijenila — a njegovo zatečeno ponašanje u tom
trenutku **nije bilo izmjereno**, i jedino što se o njemu znalo bilo je da je prethodna
tvrdnja o njemu netočna. Grana bi time isporučila izmjenu na neizmjerenom putu.

Izvedeno je umjesto toga `refuse(model-updated)`: ontologija koju tok **već sluša**, pa se
router ne dira; razlikuje ih **performativ**. Izmjereno da `_flow_template` performativ ne
ograničava.

🔴 **Granananje ide na performativ, ne na sadržaj payloada.** `if payload.get("error")` bio
bi točno obrazac iz §G2 — novo ponašanje bez novog imena — i sutrašnji legitiman
`inform(model-updated)` s poljem `error` tiho bi prekidao tok. Ontologija je tema,
performativ je govorni čin.

## G3.4 Invarijanta o konkurentnosti dokazana IZVRŠENJEM

Tvrdnja „ne dira mehaniku tokova" nije smjela ostati argument: #62 je bila invarijanta
zapisana komentarom, neistinita tri mjeseca, koju 737 testova nije uhvatilo. Zato pet
tvrdnji, **svaka dokazana namjernim kvarom** — tablica je u ERRATI #69.

Najvrjednija: **10 utora procurilo od 10 smetnji** kad se preskoči `_release_flow`. Uz
`MAX_CONCURRENT_FLOWS = 64` to bi se očitovalo tek nakon 64 smetnje — usred evala, kao
„sve predaje odjednom vraćaju 503".

**Zatečeni `test_coordinator_concurrency.py` ostao je zelen bez ijedne izmjene** (6 passed).
To je bio uvjet da se tvrdnja o nedirnutoj mehanici uopće smije izgovoriti.

## G3.5 Ugovorni test taksonomije (#71)

Ista greška se u ovoj grani ponovila tri puta (§G2, nalazi 2/3/5), a kad je novo ime
konačno uvedeno, `plan_mismatch` nije bio registriran u frontendu — pa je student na
**ispravan SQL** vidio *„Ocjenjivanje nije uspjelo"*. Nijedan od 819 testova to nije
uhvatio jer je svaki gledao **jedan** sloj.

`tests/test_error_taxonomy_contract.py` (**48 tvrdnji**) zaključava ugovor s pet potrošača:
poruka u `ERROR_TEXT`, točno jedan skup prezentacije detalja, svjesna misconception-odluka,
točno jedna politika hint payloada, opis za LLM. 🔴 Skup tipova se **čita iz izvora**
`evaluation.py` regexom — popis prepisan u test zastario bi tiho, a upravo je tiho
zastarjevanje ono što test treba spriječiti.

Uz to tvrdi **novu granicu**: koji tipovi **smiju** biti ishod pokušaja, a koji ne. Bez nje
bi se `plan_unavailable` sljedećom izmjenom mogao tiho vratiti u `attempts`.

Dokazan namjernim kvarom: uklanjanje `plan_mismatch` iz `ERROR_TEXT` obara test **s imenom
tog tipa u poruci**.

## G3.6 „Ispravno slučajno" — dva primjerka u istom krugu (#71)

`plan_unavailable` je prije registracije padao na `FALLBACK_ERROR_TEXT`, a taj je tekst
*„pokušaj ponovno predati"* — **semantički točan** za prolaznu smetnju. Ali točnost je bila
posljedica fallbacka, ne odluke: nijedan test nije mogao pasti jer veza nije ni bila
uspostavljena.

Drugi primjerak: `unsupported_eval` attempti su bili **0** ne zato što je put bio siguran,
nego zato što je **maska Kat. C slučajno štitila i od toga** — svi M6 zadaci bili su
`is_active=False`, pa do predaje nikad nije došlo. Provjera C iz ovog kruga (0 zagađenih
redaka) time je dobra vijest s krivim obrazloženjem ako se ne navede uzrok.

**Za rad:** „radi ispravno" i „ispravnost je zajamčena" nisu ista tvrdnja. Razlika se vidi
tek kad se pita KOJI test pada ako se ponašanje pokvari.

## G3.7 Halucinacija iz gole klasifikacije (#72)

Model je na `plan_unavailable` — **bez ijednog detalja, samo klasifikacija** — proizveo
konkretnu i netočnu dijagnozu studentovog ispravnog upita. To je **stroža tvrdnja od #64**:
minimalan payload ne ograničava halucinaciju. Posljedica za odluku o selektivnom B+ (5.0):
rizik po studenta seli se **iz privatnosti u točnost**, a te su se dvije mjere dosad čitale
kao ista os.

## G3.8 Ispravak koji je morao u erratu (#70)

Tvrdnja da `task_not_found` daje degradiran 200 bila je **netočna**, izvedena iz
`build_response_payload` bez provjere da poruka dotle dolazi. Izmjereno: **504
`evaluation_timeout` nakon 9.09 s**, utori uredno oslobođeni.

**KOD KOJI PODNOSI STANJE NIJE DOKAZ DA TO STANJE NASTAJE.**

---

# H — Otvoreno

- 🔴 **Dokaz iz `fix-koncept-zadatak-wrapup.md` §A.5 je PRECIZIRAN, ne oboren — i uz njega
  sada stoji mjerenje.** Prvo mjerenje ovog kruga (2026-08-18) izbrojalo je **tri korijena**
  u podgrafu bez maskiranih čvorova (`select_basic`, `cross_join`, `inner_join`) i iz toga
  zaključilo da uvjet iz §A.5 više ne vrijedi. **To je bilo prebrzo.** Maskiranje mijenja
  **vrijednosti čvorova**, ne bridove: `prereqs_met/2` (`rules.pl:58-60`) pita nemaskirani
  `prerequisite/2`, pa „korijen podgrafa" nije ulazna točka preporučivača. `join_condition`
  je uz to **prozirna** maska, ne trajna blokada — `build_mastery_snapshot` korak 4
  ([`recommender_logic.py:258-264`](../backend/agents/recommender_logic.py)) postavi ga na
  0.99 čim su mu **vlastiti** prereqs savladani (jedini mu je `from_clause`), pa
  `inner_join`/`cross_join` nisu ulazi nego **vrata**. Za novaka je stoga jedini koncept s
  `prereqs_met` i dalje **`select_basic`** — nema izjednačenja koje bi poredak morao
  razriješiti.
- **Izmjereno kroz pun lanac** (`/register` → `/next-task`, bez ijednog pokušaja):
  **5/5 novih računa → `select_basic`, task 15 (`select_basic_d1_526db098`),
  reason `partial_continuation`**, deterministički. Novak **nije** „sav weak": tier prior
  daje M1 konceptima `p_l = 0.300`, a `weak_threshold(0.30)` je strogi `<`, pa su oni
  **partial** — zato `partial_continuation`, a ne `weak_with_prereqs_met`. Poredak injekcije
  je kanonski **pedagoški** (`_KANONSKI_POREDAK = (Module.order_index, Concept.order_index,
  Concept.id)`, [`db_helpers.py:27`](../backend/agents/db_helpers.py)), **nije abecedni** —
  `select_basic` je prvi.
- **Falsifikacija (ostaje):** 2 × 1500 nasumičnih stanja, sjemena **20260814** i **20260818**
  (ukupno 3000), **0 povreda P1–P4**, ~30 s po sjemenu, kroz stvarni Prolog motor, svako
  stanje u `SAVEPOINT`/rollback (devet brojki prije i poslije identično). `exhausted` **0×**;
  `repeat_practice` pogođena **63×** odnosno **46×**, pa P3 nije prošao zbog neizvršenog puta.
  Instrument uzorkuje prostor mastery vektora i **ne pokriva točku u kojoj svi počinju** —
  zato mjerenje novaka gore stoji uz njega, ne umjesto njega.
- 🟡 **OTVORENO, nije uzrokovano ovom granom:** simulacija savršenog studenta od stanja
  novaka daje redoslijed u kojem **spojevi dolaze prije `where_filter`** — koraci 3–6 su
  `inner_join`, `right_join`, `cross_join`, `self_join` (modul 3), a `where_filter` (modul 1)
  tek korak 7. Uzrok je kombinacija koju ova grana **nije dirala** (`git diff main...HEAD`
  za `backend/prolog/` i `backend/bkt/` je **prazan**): `join_condition` traži samo
  `from_clause`, tier prior čini M1 koncepte `partial` a sve ostalo `weak`, a klauzula za
  `weak` stoji **prije** klauzule za `partial` (`rules.pl:91-97`). Put ipak **nije ćorsokak** —
  svih 29 preporučivih koncepata obiđe se u 29 koraka, pa `no_recommendation`.
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

# I — Gate diskriminacije: zašto NE u sweep, i dokle je stigla zamjena

**Odluka 2026-08-18: gate diskriminacije ostaje pri autorstvu, u `manual_tasks_m6.py`.**
Ondje je katalog u kodu ispravan jer **skripta jest katalog**.

## I.1 Zašto B (prijenos u sweep) nije izabran

Uvoz `TASKS` iz autorske skripte vezao bi `sweep_task_integrity` — dakle i `preflight` —
uz **7 hardkodiranih SQL stringova**, dok `is_active`, `expected_query` i sam popis
zadataka žive **u bazi**. To je konstanta koju je `m6-transverzalni-korak-0.md` §C.1 već
odbio (*„sadržaj kataloga u evaluacijskoj jezgri; može zastarjeti tiho, ista klasa kao
docstring iz ERRATE #45"*) — samo **uvezena umjesto prepisana**, što ne mijenja hazard.

Uz to bi rupa ostala: gate se grana na `anti is None` i tada **tiho vraća**, pa bi
**zadatak 81** (`index_usage_d3_41c8280e`, došao kroz `import_dataset`, bez anti-patterna)
prošao klasificiran kao „nije M6". Od 5 aktivnih `PLAN_CHECKED` zadataka anti-pattern imaju
**4**. V. ERRATA #78.

🔴 **Cijena nije bila razlog.** Izmjereno: 2 × `EXPLAIN` + 1 × `execute` nad svih 5 zadataka
= **0,18 s** (pojedinačni `EXPLAIN` 10–20 ms), uz zatečeni gate stabilnosti od 0,17 s.

## I.2 Zašto O (svojstvo iz `description`)

§C.2 je već ustanovio da **zadatak nosi svoju tvrdnju** — ondje kroz `expected_query`.
O je isto načelo primijenjeno na `description`: svojstvo plana koje zadatak izgovara mora
se pojaviti u potpisu referentnog plana. Nula kataloga u kodu, imena indeksa se provjeravaju
prema `pg_indexes`, i pokriva **i zadatak 81**.

Izmjereno nad imenima indeksa (0,06 s nad svih 9 M6 zadataka):

| zadatak | aktivan | opis imenuje | plan daje | ishod |
|---|---|---|---|---|
| 81 | ✅ | `idx_orders_customer` | isto | ✅ |
| **83** | ne | `idx_orders_customer` | **`orders_pkey`** | 🔴 **PAO — traženi kvar** |
| 3782 | ✅ | `idx_order_items_order` | isto | ✅ |
| 3783 | ✅ | `idx_reviews_product` | isto | ✅ |
| 3785 | ✅ | `idx_orders_customer` | + `idx_order_items_order` | ✅ |

## I.3 🔴 ZAUSTAVLJENO: generalizacija na metode spoja

Za `explain_plan` gate bi trebao čitati metodu spoja iz proze. **Ne može, bez parsiranja
osjetljivijeg od traženja doslovnog niza** — a to je granica koju je korisnik postavio
izrijekom (*„regex nad hrvatskim tekstom koji može promašiti gori je od gatea koji ne
postoji"*).

Razlog: oba aktivna `explain_plan` zadatka imenuju **obje** metode — onu koju uče i onu
pred kojom upozoravaju — u istom odlomku, a referentni plan ima **samo `Nested Loop`**:

| zadatak | opis imenuje | broj spominjanja | referentni plan |
|---|---|---|---|
| 3784 | `Hash Join`, `Nested Loop` | Hash Join **2×**, Nested Loop 1× | `Nested Loop` |
| 3785 | `Hash Join`, `Nested Loop` | Hash Join 1×, Nested Loop 1× | `Nested Loop` |

Pravilo „sve imenovano mora biti u planu" tada **lažno obara oba**; pravilo „bilo što
imenovano" ne tvrdi ništa. Razlikovanje traži razumijevanje hrvatske rečenice — 3784:
*„spaja ih preko **Hash Joina**"* (loš slučaj) … *„— **Nested Loop**"* (dobar) … *„plan se
vraća na **Hash Join**"* (anti-pattern); 3785: *„prelazi s **Nested Loopa** na **Hash
Join**"*. Smjer prijelaza nosi značenje, ne prisutnost niza.

**3785 imenuje OBOJE** (indeks i metode spoja), pa bi gate morao tvrditi oboje — i pao bi
na `Hash Join` koji je u opisu upravo ono što se ne smije dogoditi.

`tasks` nema polje koje bi tvrdnju nosilo strojno čitljivo (nema `pedagogical_notes`;
kolona = migracija sheme, ista klasa koju je §C.1 odbio). **Čeka odluku korisnika:** ili se
opisi 3784/3785 dopunjuju dogovorenom formulacijom, ili gate pokriva samo imena indeksa a
`explain_plan` zadaci izlaze iz njegova dosega — uz tvrdo pravilo protiv šutnje to znači da
bi 3784 (koji ne imenuje nijedan indeks) morao pasti dok mu se opis ne dopuni.

## I.4 🔴 Spojna grana je SLABIJA od indeksne — i to je svojstvo koncepta, ne rupa

**Odluka 2026-08-18: pravilo po konceptu. Nijedan opis se ne uređuje** — opisi su prošli
`sql-task-validator` i student ih vidi, pa se gate prilagođava zadacima, ne obrnuto.

| koncept | što gate tvrdi | jačina |
|---|---|---|
| `index_usage` | indeks imenovan u `description` **mora biti** u `index_names` referentnog plana | jaka — imenuje **koji** |
| `explain_plan` | `join_methods` referentnog plana **ne smije biti prazan** | 🔴 slaba — tvrdi **da postoji**, ne **koja** |

Spojna grana je §C.4 („potpis referentnog upita nije prazan") primijenjen na polje koje taj
koncept poučava. **Nema parsiranja proze.**

### Zašto jača tvrdnja nije izvediva iz opisa

Pedagogija `explain_plan`-a je **kontrastivna po konstrukciji**: da bi poučavao razliku,
opis **mora imenovati oba plana** — onaj koji se traži i onaj pred kojim upozorava. Zato
opis nikad ne može biti izvor jednoznačne tvrdnje o **referentnom** planu.

Dokaz, doslovno iz `description`, uz referentni plan koji u oba slučaja ima **samo
`Nested Loop`**:

**3784** (`explain_plan_d3_manual_c6ed9b8c`) — `Hash Join` 2×, `Nested Loop` 1×:

> *„Kad spajaš orders i order_items BEZ filtra, baza mora pročitati obje tablice u cijelosti
> i spaja ih preko **Hash Joina**. Selektivan filtar na customer_id mijenja račun: baza
> indeksom nađe nekoliko narudžbi tog kupca, pa za svaku indeksom potraži stavke —
> **Nested Loop**. Ako filtar napišeš tako da poništi indeks (npr. CAST(o.customer_id AS
> TEXT) = '42'), rezultat ostaje isti, ali se plan vraća na **Hash Join** uz puno čitanje
> obje tablice."*

**3785** (`explain_plan_d4_manual_1e09ba01`) — `Hash Join` 1×, `Nested Loop` 1×:

> *„…indeks idx_orders_customer se ne može upotrijebiti, pa baza čita cijelu tablicu
> narudžbi i **prelazi s Nested Loopa na Hash Join**."*

Značenje nosi **smjer rečenice** (*„vraća se na"*, *„prelazi s … na"*), ne prisutnost niza.
Pravilo „sve imenovano mora biti u planu" lažno bi oborilo **oba aktivna** `explain_plan`
zadatka; pravilo „bilo što imenovano" ne bi tvrdilo ništa. Razlikovanje traži razumijevanje
hrvatske rečenice — a *regex nad hrvatskim tekstom koji može promašiti gori je od gatea koji
ne postoji*.

**Što slabija grana ipak hvata:** zadatak `explain_plan` koji uopće **ne spaja** (79, 80 su
jednotablični) ili čiji je spoj nestao iz plana. Ne hvata zamjenu jedne strategije drugom.

🔴 **Diskriminacija za 3784/3785 ostaje pokrivena gateom B pri autorstvu**, u
`manual_tasks_m6.py`, gdje su oba i nastala — ondje je katalog u kodu ispravan jer skripta
**jest** katalog. Nepokriven ostaje jedino slučaj „zadatak je prestao razlikovati nakon
autorstva" za `explain_plan`; za `index_usage` taj slučaj hvata upravo ovaj gate (zadatak
83, dokazano).

### Tvrdo pravilo protiv šutnje

`PLAN_CHECKED` zadatak koji ne potpada ni pod jedno pravilo **pada s vlastitim `source_id`**
— uključujući nepoznat koncept u `PLAN_CHECKED_CONCEPTS`. Tiho preskakanje je točno mana
zbog koje varijanta B nije prenesena u sweep (ERRATA #78), pa je ovaj gate ne smije
ponoviti.

### Cijena i dokazi

Dodatak na preflight: **0,081 s** (medijan od 3; zatečeni gate stabilnosti 0,183 s).
Imena indeksa dolaze iz `pg_indexes` preko `current_schema()`, ne iz popisa u kodu.
Doslovan niz je dovoljan — izmjereno da **nijedno od 21 imena indeksa nije podniz drugog**,
pa križni pogodak nije moguć, i da se `in` i `\b`-regex slažu nad svih 9 opisa.

Četiri namjerna kvara, svaki viđen kako pada pa vraćen:

| kvar | razina | ishod |
|---|---|---|
| **a** 83 aktivan | sweep, `rc=1` | *„opis obećava ['idx_orders_customer'], a plan koristi ['orders_pkey']"* |
| **b** 79/80 aktivan | funkcija | *„join_methods referentnog plana je PRAZAN"* — na razini sweepa ih ranije presretne **gate stabilnosti**, pa je grana dokazana unit testom |
| **c** opis 3782 bez imena indeksa | sweep, `rc=1` | *„opis ne imenuje nijedan indeks"* |
| **d** `column_alias` ubačen u `PLAN_CHECKED_CONCEPTS` | funkcija | *„koncept … nema pravilo — ne zna što tvrditi"* |
