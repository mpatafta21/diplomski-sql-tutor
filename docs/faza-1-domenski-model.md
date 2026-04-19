# FAZA 1 — Domenski model i baza

**Diplomski rad:** Inteligentni agentski sustav za adaptivno učenje SQL-a uz igrifikaciju **Fakultet:** FOI, smjer Baze podataka i baze znanja **Faza:** 1 od 7 | **Trajanje:** 2 tjedna (travanj/svibanj) **Milestone:** Alembic migracije rade, Prolog vraća sensible preporuke za sintetičke korisnike

---

## 1\. Pregled Faze 1

### 1.1 Ciljevi

Faza 1 definira **domenski model** sustava — što korisnici uče, kako je to znanje strukturirano, i kako se reprezentira u bazi podataka te u Prolog ontologiji. Ovo je temelj na kojem se grade svi agenti u Fazama 3 i 4\.

Konkretni ciljevi faze:

1. Finalizirati popis atomskih SQL koncepata koje sustav tracira  
2. Definirati prerequisite graf (ovisnosti među konceptima)  
3. Napisati Prolog ontologiju (concepts \+ rules \+ badges placeholder)  
4. Dizajnirati shemu glavne PostgreSQL baze (users, tasks, attempts, skill\_mastery, itd.)  
5. Dizajnirati shemu sandbox PostgreSQL baze (e-commerce primjer)  
6. Postaviti Alembic migracije  
7. Definirati BKT default parametre i njihovo opravdanje  
8. Validirati Prolog preporuke na sintetičkim korisnicima

### 1.2 Deliverables

| Deliverable | Lokacija u repo-u | Status |
| :---- | :---- | :---- |
| Popis 30 koncepata \+ opravdanje | `docs/faza-1-domenski-model.md` (ovaj dokument) | — |
| Prolog ontology.pl | `backend/prolog/ontology.pl` | — |
| Prolog rules.pl | `backend/prolog/rules.pl` | — |
| Prolog badges.pl (placeholder) | `backend/prolog/badges.pl` | — |
| pyswip wrapper | `backend/prolog/prolog_engine.py` | — |
| Alembic setup \+ inicijalna migracija | `backend/alembic/versions/` | — |
| SQLAlchemy modeli | `backend/app/db/models.py` | — |
| Sandbox init.sql | `docker/postgres-sandbox/init.sql` | — |
| Seed skripta (koncepti \+ moduli \+ bedževi) | `backend/app/db/seed.py` | — |
| Test sintetičkih korisnika | `backend/tests/test_recommender_synthetic.py` | — |

### 1.3 Predviđeni ishodi

Na kraju Faze 1 sustav treba moći:

- Pokrenuti Alembic migracije koje kreiraju svih 15 tablica glavne baze bez grešaka  
- Seed-ati 30 koncepata, 6 modula i 5+ bedževa u bazu  
- Pokrenuti Prolog upit `recommend_next(user_1, Task)` i dobiti smislene preporuke za 3-5 sintetičkih korisnika s različitim BKT profilima  
- Pokrenuti sandbox PostgreSQL kontejner s 8 tablica e-commerce sheme i \~4900 redova seed podataka

---

## 2\. Popis 30 SQL koncepata

### 2.1 Opravdanje granulacije

Odluka o broju koncepata (30) temelji se na **trima istraživačkim ograničenjima** iz literature:

**a) Pedagoška validnost — Mitrovic SQL-Tutor** Mitrovic (1998, 2015\) u SQL-Tutoru koristi 530 constraintova u hijerarhiji od 530 čvorova, ali to je **constraint-based modeling** (CBM) pristup gdje svaki constraint pokriva jedno mikro-pravilo. Za BKT trebamo grublji nivo jer BKT tracira **skill mastery** (latent varijabla), a ne pojedinačne constraintove. Mitrovic sam u pedagoškom modulu koristi \~20-30 "topic areas" za odabir zadataka — to je referenca za našu granulaciju.

**b) Statistička održivost — Pelánek (2017) i Yudelson (2013)** Pelánek u pregledu learner modeling tehnika (2017) navodi da BKT zahtijeva **10-30 attempts po knowledge component (KC)** za pouzdanu procjenu P(L). S planiranih 20 studenata × \~80 zadataka × prosječno 1.5 pokušaja ≈ 2400 ukupnih pokušaja. Podijeljeno na 30 koncepata, očekujemo **\~55-80 attempts po konceptu** (ovisno o distribuciji), što je u gornjoj polovici preporučenog raspona.

**c) Sparse data problem — Piech (2015), Yudelson (2013)** Previše granularni skill-ovi (40+) vode u sparse data problem: nedovoljno opažanja za konvergenciju BKT parametara, rezultirajući degeneriranim procjenama P(L) ≈ P(L₀) (model "ne uči"). S druge strane, previše grubi skill-ovi (\<20) gube pedagošku diskriminaciju.

**Zaključak:** 30 koncepata je balans između pedagoške validnosti (Mitrovic), statističke pouzdanosti (Pelánek) i izbjegavanja sparse data (Piech).

### 2.2 Koncepti po modulima

#### Modul 1 — Osnove SELECT-a (6 koncepata)

| \# | Code | Naziv | Opravdanje atomičnosti \+ ključni misconceptions |
| :---- | :---- | :---- | :---- |
| 1 | `select_basic` | Osnovni SELECT | Projekcija stupaca. Prerequisite za sve upite. Misconception: `SELECT *` vs. eksplicitni stupci. |
| 2 | `from_clause` | FROM klauzula | Identifikacija tablice. Misconception: zaboravlja FROM, miješa nazive tablica i stupaca. |
| 3 | `where_filter` | WHERE filtriranje | Filtriranje redova. **Različit od HAVING** (česta konfuzija u literaturi). |
| 4 | `order_by` | ORDER BY | Sortiranje. Misconception: ORDER BY prije WHERE u logičkom mišljenju, ASC/DESC sintaksa. |
| 5 | `limit_offset` | LIMIT / OFFSET | Paginacija. Misconception: LIMIT bez ORDER BY (nedeterministički rezultat). |
| 6 | `distinct` | DISTINCT | Uklanjanje duplikata. Misconception: koristi se redundantno nakon GROUP BY, ne razumije performance cost. |

#### Modul 2 — Agregacije i grupiranje (5 koncepata)

| \# | Code | Naziv | Opravdanje atomičnosti \+ ključni misconceptions |
| :---- | :---- | :---- | :---- |
| 7 | `group_by` | GROUP BY | Grupiranje. Misconception: selektira nenagregirani stupac bez GROUP BY (SQL standard violation). |
| 8 | `having_filter` | HAVING | Filtriranje grupa. **Klasični misconception WHERE vs HAVING** — najčešći izvor grešaka u agregacijama. Mora biti zaseban KC. |
| 9 | `agg_count` | COUNT | COUNT(\*), COUNT(col), COUNT(DISTINCT col) — različita semantika s NULL vrijednostima. |
| 10 | `agg_sum_avg` | SUM / AVG | Numerička redukcija. Spojeni jer dijele NULL-handling semantiku i tipove misconceptiona. |
| 11 | `agg_min_max` | MIN / MAX | Ekstremne vrijednosti. Spojeni (ista logika, razlikuju se samo smjerom). |

*Napomena o spajanju SUM/AVG i MIN/MAX:* razdvajanje u 4 zasebna koncepta dalo bi sparse data — u praksi studenti koji savladaju SUM trivijalno savladaju AVG (iste jednadžbe ažuriranja BKT-a bi konvergirale na slične vrijednosti). Pedagoška vrijednost razdvajanja ne opravdava statističku cijenu.

#### Modul 3 — JOIN-ovi (7 koncepata) — maksimalna atomičnost

| \# | Code | Naziv | Opravdanje atomičnosti \+ ključni misconceptions |
| :---- | :---- | :---- | :---- |
| 12 | `inner_join` | INNER JOIN | Najčešći JOIN. Baseline za sve ostale. |
| 13 | `left_join` | LEFT OUTER JOIN | **Klasični misconception s NULL-ovima**: kombinira s IS NULL za "anti-join", ali tretira kao INNER JOIN. Najdokumentiraniji izvor grešaka. |
| 14 | `right_join` | RIGHT OUTER JOIN | Rijetko korišten u praksi, ali prerequisite za razumijevanje simetrije outer join-ova. |
| 15 | `full_outer_join` | FULL OUTER JOIN | Semantički različit od LEFT+RIGHT. Postgresova sintaksa. |
| 16 | `cross_join` | CROSS JOIN | Kartezijev produkt. Misconception: slučajno stvara CROSS JOIN kroz nedostajuću ON klauzulu. |
| 17 | `self_join` | SELF JOIN | JOIN tablice sa samom sobom. **Konceptualno najteži JOIN** — alias management \+ self-reference (npr. "zaposlenici i njihovi managerji"). |
| 18 | `multi_table_join` | JOIN 3+ tablica | Višestruki JOIN-ovi. Misconception: krivi redoslijed JOIN-ova, krivi ON uvjeti, eksplozija kardinaliteta. |

#### Modul 4 — DML operacije (3 koncepta)

| \# | Code | Naziv | Opravdanje atomičnosti \+ ključni misconceptions |
| :---- | :---- | :---- | :---- |
| 19 | `insert` | INSERT | Unos podataka. Misconception: krivi redoslijed vrijednosti, constraint violations, NULL u NOT NULL stupac. |
| 20 | `update` | UPDATE | Izmjena podataka. **Kritični misconception: UPDATE bez WHERE** (mijenja sve retke). |
| 21 | `delete` | DELETE | Brisanje podataka. **Kritični misconception: DELETE bez WHERE**, razlika od TRUNCATE i DROP TABLE. |

#### Modul 5 — Podupiti (4 koncepta)

| \# | Code | Naziv | Opravdanje atomičnosti \+ ključni misconceptions |
| :---- | :---- | :---- | :---- |
| 22 | `scalar_subquery` | Skalarni podupit | Vraća 1 vrijednost. Misconception: podupit vraća više od 1 reda, multiple rows returned error. |
| 23 | `in_subquery` | IN / NOT IN | Members\*\*hip test. **Kritični misconception: NOT IN \+ NULL** — vraća 0 redova umjesto očekivanih zbog 3-valued logike. |
| 24 | `exists_subquery` | EXISTS / NOT EXISTS | Test egzistencije. Alternativa IN-u, robusniji s NULL vrijednostima. |
| 25 | `correlated_subquery` | Korelirani podupit | Vanjska referenca. **Konceptualno najteži** — izvršavanje red-po-red, performance implikacije. |

*Odluka o CASE izrazu:* ne dodajem ga kao zaseban KC. U literaturi (Mitrovic constraint analiza) CASE nije među top izvorima misconceptiona. Pokriva se implicitno kroz `scalar_subquery` (isti kontekst upotrebe).

#### Modul 6 — Optimizacija (2 koncepta, "bonus" razina)

| \# | Code | Naziv | Opravdanje atomičnosti \+ ključni misconceptions |
| :---- | :---- | :---- | :---- |
| 26 | `explain_plan` | EXPLAIN čitanje | Analiza query plana. Prerequisite za sve optimizacije. Misconception: ne zna razliku Seq Scan vs Index Scan. |
| 27 | `index_usage` | Korištenje indeksa | Kada indeks pomaže, kada ne (npr. funkcija u WHERE klauzi poništava indeks). |

*Napomena o "bonus" statusu:* Modul 6 je u UI-ju označen kao bonus jer: (a) evaluacija optimizacija je djelomično subjektivna (više "dobrih" planova može postojati), (b) zahtijeva real-world veličine podataka koje sandbox ograničava. U BKT-u se ipak tracira zbog defensibilnosti u radu.

#### Transverzalni koncepti (3) — prolaze kroz više modula

| \# | Code | Naziv | Opravdanje atomičnosti \+ ključni misconceptions |
| :---- | :---- | :---- | :---- |
| 28 | `null_handling` | NULL handling | IS NULL, IS NOT NULL, COALESCE, NULLIF. **Prerequisite za LEFT JOIN, NOT IN, agregacije.** Jedan od najvećih izvora grešaka u SQL-u po literaturi. |
| 29 | `column_alias` | AS za stupce | Preimenovanje stupaca. Misconception: koristi alias u WHERE (ne može — redoslijed izvršavanja WHERE → SELECT). |
| 30 | `join_condition` | ON klauza | Semantika uvjeta spajanja. **Misconception: filter u ON vs WHERE kod LEFT JOIN-a** — potpuno mijenja rezultat (zadržava NULL-ove vs. pretvara u INNER JOIN). |

*Zašto `join_condition` kao zaseban KC:* literatura (Mitrovic SQL-Tutor constraint analiza, studija 2004\) pokazuje da je "filter u ON klauzi za LEFT JOIN" među top 5 misconceptiona koji se pojavljuju nezavisno od tipa JOIN-a. BKT ga tracira odvojeno: korisnik može znati INNER JOIN sintaksu (P(L) high) ali griješiti s join\_condition semantikom (P(L) low) — to je precizan signal za RecommenderAgent.

### 2.3 Sažetak distribucije

| Modul | \# koncepata | Kumulativno | Razina |
| :---- | :---- | :---- | :---- |
| M1 Osnove SELECT-a | 6 | 6 | Beginner |
| M2 Agregacije | 5 | 11 | Intermediate |
| M3 JOIN-ovi | 7 | 18 | Intermediate |
| M4 DML | 3 | 21 | Advanced |
| M5 Podupiti | 4 | 25 | Advanced |
| M6 Optimizacija (bonus) | 2 | 27 | Expert |
| Transverzalni | 3 | 30 | (cross-module) |
| **UKUPNO** | **30** | — | — |

---

## 3\. Prerequisite graf

### 3.1 Dijagram ovisnosti

graph TD

    select\_basic \--\> from\_clause

    from\_clause \--\> where\_filter

    where\_filter \--\> order\_by

    where\_filter \--\> limit\_offset

    select\_basic \--\> distinct

    where\_filter \--\> group\_by

    group\_by \--\> having\_filter

    group\_by \--\> agg\_count

    group\_by \--\> agg\_sum\_avg

    group\_by \--\> agg\_min\_max

    from\_clause \--\> join\_condition

    join\_condition \--\> inner\_join

    join\_condition \--\> cross\_join

    inner\_join \--\> left\_join

    inner\_join \--\> right\_join

    left\_join \--\> full\_outer\_join

    right\_join \--\> full\_outer\_join

    inner\_join \--\> self\_join

    inner\_join \--\> multi\_table\_join

    null\_handling \--\> left\_join

    null\_handling \--\> in\_subquery

    null\_handling \--\> agg\_count

    select\_basic \--\> insert

    where\_filter \--\> update

    where\_filter \--\> delete

    where\_filter \--\> scalar\_subquery

    scalar\_subquery \--\> in\_subquery

    scalar\_subquery \--\> exists\_subquery

    scalar\_subquery \--\> correlated\_subquery

    multi\_table\_join \--\> explain\_plan

    group\_by \--\> explain\_plan

    explain\_plan \--\> index\_usage

    column\_alias \--\> group\_by

### 3.2 Prerequisite tablica (izvor za Prolog činjenice)

| Koncept | Prerequisite(s) |
| :---- | :---- |
| `select_basic` | — (root) |
| `from_clause` | `select_basic` |
| `where_filter` | `from_clause` |
| `order_by` | `where_filter` |
| `limit_offset` | `where_filter` |
| `distinct` | `select_basic` |
| `column_alias` | `select_basic` |
| `null_handling` | `where_filter` |
| `group_by` | `where_filter`, `column_alias` |
| `having_filter` | `group_by` |
| `agg_count` | `group_by`, `null_handling` |
| `agg_sum_avg` | `group_by` |
| `agg_min_max` | `group_by` |
| `join_condition` | `from_clause` |
| `inner_join` | `join_condition` |
| `cross_join` | `join_condition` |
| `left_join` | `inner_join`, `null_handling` |
| `right_join` | `inner_join` |
| `full_outer_join` | `left_join`, `right_join` |
| `self_join` | `inner_join` |
| `multi_table_join` | `inner_join`, `where_filter` |
| `insert` | `select_basic`, `from_clause` |
| `update` | `where_filter` |
| `delete` | `where_filter` |
| `scalar_subquery` | `where_filter`, `select_basic` |
| `in_subquery` | `scalar_subquery`, `null_handling` |
| `exists_subquery` | `scalar_subquery` |
| `correlated_subquery` | `scalar_subquery` |
| `explain_plan` | `multi_table_join`, `group_by` |
| `index_usage` | `explain_plan` |

### 3.3 Opravdanje ključnih ovisnosti

- **`null_handling` → `left_join`**: LEFT JOIN bez razumijevanja NULL-ova vodi u klasičan misconception "anti-join" (IS NULL filter koji ne radi jer studentkoristi INNER JOIN).  
- **`null_handling` → `in_subquery`**: `NOT IN (SELECT ... WHERE col IS NULL)` vraća 0 redova zbog 3-valued logike. Bez razumijevanja NULL-ova ovaj misconception je neizbježan.  
- **`null_handling` → `agg_count`**: `COUNT(col)` ignorira NULL-ove, `COUNT(*)` ih broji — kritična razlika.  
- **`column_alias` → `group_by`**: u nekim dialekatima (PostgreSQL, MySQL) aliasi se mogu koristiti u GROUP BY, u drugima ne. Razumijevanje aliasa je prerequisite.  
- **`inner_join` → `left_join`**: svi OUTER JOIN-ovi semantički se definiraju kao "INNER JOIN \+ dodavanje NULL-popunjenih redova". Bez INNER JOIN-a nemoguće razumjeti OUTER.  
- **`multi_table_join` zahtijeva samo `inner_join` (ne sve JOIN tipove)**: multi-table join može se vježbati isključivo s INNER JOIN-ovima. LEFT/RIGHT/FULL su ortogonalne vještine.

---

*(Dokument se nastavlja u dijelu 2: Prolog ontologija, BKT model, sheme baza, Alembic setup.)*

---

## 4\. Prolog ontologija

### 4.1 Arhitektura datoteka

Prolog kod je podijeljen u **tri datoteke** unutar `backend/prolog/`:

backend/prolog/

├── ontology.pl         \# Činjenice: koncepti, moduli, prerequisite, covers, difficulty

├── rules.pl            \# Pravila preporuke: recommend\_next, can\_unlock, helper predikati

├── badges.pl           \# Placeholder u Fazi 1 (popunjava se u Fazi 3\)

└── prolog\_engine.py    \# pyswip wrapper za Python integraciju

Razlog tri fajla (a ne pet ili jedan): usklađenost s planom (Section 7 `diplomski-plan.docx`), minimalan overhead kod importa u pyswip, jasna pedagoška separacija (činjenice vs. pravila vs. gamifikacija).

### 4.2 Definicije predikata

| Predikat | Arnost | Tip | Opis |
| :---- | :---- | :---- | :---- |
| `concept/1` | 1 | fact | Registrira koncept (npr. `concept(left_join).`) |
| `module/2` | 2 | fact | `module(Concept, ModuleNumber)` — kojem modulu pripada |
| `prerequisite/2` | 2 | fact | `prerequisite(Concept, Prereq)` — ovisnost |
| `covers/2` | 2 | fact | `covers(TaskID, [Concept1, Concept2, ...])` — popunjava se u Fazi 2 |
| `difficulty/2` | 2 | fact | `difficulty(TaskID, Level)` — 1-5 |
| `mastery/3` | 3 | dynamic | `mastery(UserID, Concept, P_L)` — injecta Python iz BKT snapshota |
| `tier/2` | 2 | fact | `tier(Concept, Tier)` — easy / medium / hard (za BKT defaults) |
| `recommend_next/2` | 2 | rule | Glavno pravilo preporuke |
| `can_unlock/2` | 2 | rule | Može li korisnik otključati koncept |
| `mastered/2` | 2 | rule | Je li koncept savladan (P\_L \>= 0.85) |
| `weak/2` | 2 | rule | Je li koncept slab (P\_L \< 0.3) |
| `ready_for/2` | 2 | rule | Prerequisite-i su ispunjeni |

### 4.3 Skica `ontology.pl`

% \============================================================

% ontology.pl — činjenice o SQL konceptima i njihovim svojstvima

% \============================================================

% \--- Moduli \---

module\_name(1, 'Osnove SELECT-a').

module\_name(2, 'Agregacije i grupiranje').

module\_name(3, 'JOIN-ovi').

module\_name(4, 'DML operacije').

module\_name(5, 'Podupiti').

module\_name(6, 'Optimizacija i indeksi').

% \--- Koncepti (30) \---

% Modul 1 — Osnove SELECT-a

concept(select\_basic).

concept(from\_clause).

concept(where\_filter).

concept(order\_by).

concept(limit\_offset).

concept(distinct).

% Modul 2 — Agregacije

concept(group\_by).

concept(having\_filter).

concept(agg\_count).

concept(agg\_sum\_avg).

concept(agg\_min\_max).

% Modul 3 — JOIN-ovi

concept(inner\_join).

concept(left\_join).

concept(right\_join).

concept(full\_outer\_join).

concept(cross\_join).

concept(self\_join).

concept(multi\_table\_join).

% Modul 4 — DML

concept(insert).

concept(update).

concept(delete).

% Modul 5 — Podupiti

concept(scalar\_subquery).

concept(in\_subquery).

concept(exists\_subquery).

concept(correlated\_subquery).

% Modul 6 — Optimizacija

concept(explain\_plan).

concept(index\_usage).

% Transverzalni

concept(null\_handling).

concept(column\_alias).

concept(join\_condition).

% \--- Mapping koncept → modul \---

in\_module(select\_basic, 1).

in\_module(from\_clause, 1).

in\_module(where\_filter, 1).

in\_module(order\_by, 1).

in\_module(limit\_offset, 1).

in\_module(distinct, 1).

in\_module(group\_by, 2).

in\_module(having\_filter, 2).

in\_module(agg\_count, 2).

in\_module(agg\_sum\_avg, 2).

in\_module(agg\_min\_max, 2).

in\_module(inner\_join, 3).

in\_module(left\_join, 3).

in\_module(right\_join, 3).

in\_module(full\_outer\_join, 3).

in\_module(cross\_join, 3).

in\_module(self\_join, 3).

in\_module(multi\_table\_join, 3).

in\_module(insert, 4).

in\_module(update, 4).

in\_module(delete, 4).

in\_module(scalar\_subquery, 5).

in\_module(in\_subquery, 5).

in\_module(exists\_subquery, 5).

in\_module(correlated\_subquery, 5).

in\_module(explain\_plan, 6).

in\_module(index\_usage, 6).

in\_module(null\_handling, 0).    % 0 \= transverzalni

in\_module(column\_alias, 0).

in\_module(join\_condition, 0).

% \--- Tier (za BKT default parametre) \---

tier(select\_basic, easy).

tier(from\_clause, easy).

tier(where\_filter, easy).

tier(order\_by, easy).

tier(limit\_offset, easy).

tier(distinct, easy).

tier(column\_alias, easy).

tier(insert, easy).

tier(group\_by, medium).

tier(having\_filter, medium).

tier(agg\_count, medium).

tier(agg\_sum\_avg, medium).

tier(agg\_min\_max, medium).

tier(inner\_join, medium).

tier(join\_condition, medium).

tier(null\_handling, medium).

tier(update, medium).

tier(delete, medium).

tier(scalar\_subquery, medium).

tier(in\_subquery, medium).

tier(exists\_subquery, medium).

tier(left\_join, hard).

tier(right\_join, hard).

tier(full\_outer\_join, hard).

tier(cross\_join, hard).

tier(self\_join, hard).

tier(multi\_table\_join, hard).

tier(correlated\_subquery, hard).

tier(explain\_plan, hard).

tier(index\_usage, hard).

% \--- Prerequisites \---

prerequisite(from\_clause, select\_basic).

prerequisite(where\_filter, from\_clause).

prerequisite(order\_by, where\_filter).

prerequisite(limit\_offset, where\_filter).

prerequisite(distinct, select\_basic).

prerequisite(column\_alias, select\_basic).

prerequisite(null\_handling, where\_filter).

prerequisite(group\_by, where\_filter).

prerequisite(group\_by, column\_alias).

prerequisite(having\_filter, group\_by).

prerequisite(agg\_count, group\_by).

prerequisite(agg\_count, null\_handling).

prerequisite(agg\_sum\_avg, group\_by).

prerequisite(agg\_min\_max, group\_by).

prerequisite(join\_condition, from\_clause).

prerequisite(inner\_join, join\_condition).

prerequisite(cross\_join, join\_condition).

prerequisite(left\_join, inner\_join).

prerequisite(left\_join, null\_handling).

prerequisite(right\_join, inner\_join).

prerequisite(full\_outer\_join, left\_join).

prerequisite(full\_outer\_join, right\_join).

prerequisite(self\_join, inner\_join).

prerequisite(multi\_table\_join, inner\_join).

prerequisite(multi\_table\_join, where\_filter).

prerequisite(insert, select\_basic).

prerequisite(insert, from\_clause).

prerequisite(update, where\_filter).

prerequisite(delete, where\_filter).

prerequisite(scalar\_subquery, where\_filter).

prerequisite(scalar\_subquery, select\_basic).

prerequisite(in\_subquery, scalar\_subquery).

prerequisite(in\_subquery, null\_handling).

prerequisite(exists\_subquery, scalar\_subquery).

prerequisite(correlated\_subquery, scalar\_subquery).

prerequisite(explain\_plan, multi\_table\_join).

prerequisite(explain\_plan, group\_by).

prerequisite(index\_usage, explain\_plan).

% \--- Covers (placeholder za Fazu 2\) \---

% covers(TaskID, \[Concept1, Concept2, ...\])

% Primjer: covers(task\_001, \[select\_basic, from\_clause, where\_filter\]).

% \--- Difficulty (placeholder za Fazu 2\) \---

% difficulty(TaskID, Level) where Level in 1..5

% Primjer: difficulty(task\_001, 1).

### 4.4 Skica `rules.pl`

% \============================================================

% rules.pl — pravila za odlučivanje što korisniku preporučiti

% \============================================================

:- dynamic(mastery/3).  % Python injecta BKT snapshot: mastery(UserID, Concept, P\_L)

% \--- Pragovi \---

mastery\_threshold(0.85).    % P\_L \>= 0.85 → concept mastered

weak\_threshold(0.30).       % P\_L \< 0.30 → concept weak

% \--- Osnovne klasifikacije \---

mastered(User, Concept) :-

    mastery(User, Concept, P\_L),

    mastery\_threshold(Threshold),

    P\_L \>= Threshold.

weak(User, Concept) :-

    mastery(User, Concept, P\_L),

    weak\_threshold(Threshold),

    P\_L \< Threshold.

partial(User, Concept) :-

    mastery(User, Concept, P\_L),

    weak\_threshold(W),

    mastery\_threshold(M),

    P\_L \>= W,

    P\_L \< M.

% \--- Prerequisite-i savladani? \---

prereqs\_met(User, Concept) :-

    \\+ ( prerequisite(Concept, Prereq),

         \\+ mastered(User, Prereq) ).

% \--- Može li otključati koncept? \---

can\_unlock(User, Concept) :-

    concept(Concept),

    prereqs\_met(User, Concept),

    mastery(User, Concept, P\_L),

    mastery\_threshold(M),

    P\_L \< M.

% \--- Je li spreman za koncept (može rješavati zadatke)? \---

ready\_for(User, Concept) :-

    concept(Concept),

    prereqs\_met(User, Concept).

% \--- Glavno pravilo preporuke (Zone of Proximal Development) \---

% Prioriteti:

% 1\) Ako postoji slab koncept s ispunjenim prereq-ima → ojačaj ga

% 2\) Ako postoji partial koncept → nastavi raditi na njemu

% 3\) Otključaj novi koncept čiji su prereq-i ispunjeni

% 4\) Fallback: prvi unlockani koncept

recommend\_next(User, Concept) :-

    weak(User, Concept),

    prereqs\_met(User, Concept), \!.

recommend\_next(User, Concept) :-

    partial(User, Concept),

    prereqs\_met(User, Concept), \!.

recommend\_next(User, Concept) :-

    can\_unlock(User, Concept), \!.

recommend\_next(User, Concept) :-

    ready\_for(User, Concept),

    \\+ mastered(User, Concept), \!.

% \--- Lista svih prerequisite-a (tranzitivno) \---

all\_prereqs(Concept, Prereqs) :-

    findall(P, transitive\_prereq(Concept, P), Raw),

    sort(Raw, Prereqs).

transitive\_prereq(Concept, Prereq) :-

    prerequisite(Concept, Prereq).

transitive\_prereq(Concept, Prereq) :-

    prerequisite(Concept, Intermediate),

    transitive\_prereq(Intermediate, Prereq).

% \--- Obrazloženje preporuke (za logging i UI) \---

explain\_recommendation(User, Concept, Reason) :-

    weak(User, Concept), prereqs\_met(User, Concept),

    Reason \= weak\_with\_prereqs\_met, \!.

explain\_recommendation(User, Concept, Reason) :-

    partial(User, Concept), prereqs\_met(User, Concept),

    Reason \= partial\_continuation, \!.

explain\_recommendation(User, Concept, Reason) :-

    can\_unlock(User, Concept),

    Reason \= unlock\_new, \!.

explain\_recommendation(\_, \_, fallback).

### 4.5 Test sintetičkih korisnika (milestone validation)

Za validaciju Prolog pravila, Fazom 1 moramo dokazati da sustav daje **sensible preporuke** za 3 sintetička profila:

**Profil 1 — Početnik (`user_novice`)**

- Sve P\_L \= 0.1 (inicijalna vrijednost)  
- Očekivana preporuka: `select_basic` (root, nema prereq-a)

**Profil 2 — Stuck na JOIN-ovima (`user_join_stuck`)**

- Modul 1-2: svi P\_L \= 0.9 (mastered)  
- `inner_join`: P\_L \= 0.25 (weak)  
- `join_condition`: P\_L \= 0.8 (mastered)  
- `null_handling`: P\_L \= 0.7 (partial)  
- Očekivana preporuka: `inner_join` (weak \+ prereqs\_met)

**Profil 3 — Spreman za napredne (`user_advanced`)**

- Svi M1-M4: P\_L \>= 0.9  
- M5: svi P\_L \= 0.1  
- Očekivana preporuka: `scalar_subquery` (can\_unlock \+ root of M5)

Testovi se pišu u `backend/tests/test_recommender_synthetic.py` i pokreću pyswip queries protiv Prolog baze.

---

## 5\. BKT model

### 5.1 Uvod i opravdanje izbora

Bayesian Knowledge Tracing (Corbett & Anderson, 1995\) je najdokumentiraniji i najrobusniji student model u ITS literaturi. Iako moderne tehnike (Deep Knowledge Tracing, Transformer-based KT) pokazuju bolju predictive accuracy na velikim datasetovima (Piech 2015), za ovaj diplomski **BKT je prikladniji** iz tri razloga:

1. **Interpretabilnost** — P(L) vrijednosti su direktno objašnjive ("40% je šansa da korisnik zna LEFT JOIN"). Deep learning modeli su black-box, što otežava integraciju sa simboličkim Prolog rezoniranjem.  
2. **Low data requirement** — BKT radi s \~10-30 attempts po skill-u; DKT zahtijeva tisuće (Pelánek 2017). Naš dataset (\~2400 pokušaja ukupno) je premali za DKT.  
3. **Pedagoška tradicija** — BKT je standard u SQL-ITS literaturi (Mitrovic SQL-Tutor, Wagsuriya ontology-based tutor).

### 5.2 Četiri parametra

BKT za svaki koncept ima 4 parametra koji čine Hidden Markov Model:

| Parametar | Oznaka | Opis | Tipičan raspon |
| :---- | :---- | :---- | :---- |
| Prior knowledge | P(L₀) | Vjerojatnost da korisnik zna koncept PRIJE ijednog pokušaja | 0.01 – 0.50 |
| Learning rate | P(T) | Vjerojatnost da korisnik nauči koncept nakon jednog pokušaja (transition unlearned → learned) | 0.05 – 0.40 |
| Guess | P(G) | Vjerojatnost točnog odgovora kad korisnik NE zna koncept (pogađanje) | 0.05 – 0.30 |
| Slip | P(S) | Vjerojatnost netočnog odgovora kad korisnik ZNA koncept (slučajna greška) | 0.05 – 0.20 |

### 5.3 Jednadžbe ažuriranja

Nakon svakog pokušaja, P(L) se ažurira prema Bayes pravilu:

**Nakon točnog odgovora:**

P(Lₙ | correct) \= ( P(Lₙ₋₁) × (1 \- P(S)) ) / 

                  ( P(Lₙ₋₁) × (1 \- P(S)) \+ (1 \- P(Lₙ₋₁)) × P(G) )

**Nakon netočnog odgovora:**

P(Lₙ | incorrect) \= ( P(Lₙ₋₁) × P(S) ) / 

                    ( P(Lₙ₋₁) × P(S) \+ (1 \- P(Lₙ₋₁)) × (1 \- P(G)) )

**Korak učenja (primjenjuje se nakon Bayes update-a u oba slučaja):**

P(Lₙ) \= P(Lₙ | evidence) \+ (1 \- P(Lₙ | evidence)) × P(T)

**Predikcija točnog odgovora na sljedećem pokušaju:**

P(correct\_next) \= P(Lₙ) × (1 \- P(S)) \+ (1 \- P(Lₙ)) × P(G)

### 5.4 Tier-based default parametri

Svi koncepti inicijaliziraju se s default parametrima ovisno o tier-u (easy / medium / hard) iz Prolog `tier/2` predikata. Tier-based pristup je defensible u radu (referenca: Yudelson 2013 za skill-specific vs. uniform params), i izbjegava arbitrarno fine-tuning po konceptu bez empirijskih podataka.

| Tier | P(L₀) | P(T) | P(G) | P(S) | Obrazloženje |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **easy** | 0.30 | 0.30 | 0.25 | 0.08 | Laki koncepti se brzo uče, veća šansa pogađanja jednostavnih odgovora, mala šansa slip-a jer je materijal jednostavan. |
| **medium** | 0.15 | 0.20 | 0.20 | 0.10 | Standardni defaults iz Corbett & Anderson (1995). |
| **hard** | 0.05 | 0.10 | 0.10 | 0.15 | Teški koncepti — mala prior znanja, sporo učenje, malo pogađanja (teže je guessati), veća šansa slip-a jer sintaksa može biti kompleksna. |

### 5.5 Primjer izračuna

**Scenarij:** Korisnik "Marko" rješava prvi LEFT JOIN zadatak (tier: hard). Defaults: P(L₀)=0.05, P(T)=0.10, P(G)=0.10, P(S)=0.15.

**Pokušaj 1 — netočan:**

P(L | incorrect) \= (0.05 × 0.15) / (0.05 × 0.15 \+ 0.95 × 0.90)

                 \= 0.0075 / (0.0075 \+ 0.855) \= 0.0087

P(L₁) \= 0.0087 \+ (1 \- 0.0087) × 0.10 \= 0.107

(P(L) je pao, ali korak učenja djelomično kompenzira jer se pretpostavlja da je korisnik nešto naučio iz pokušaja.)

**Pokušaj 2 — točan:**

P(L | correct) \= (0.107 × 0.85) / (0.107 × 0.85 \+ 0.893 × 0.10)

               \= 0.0910 / (0.0910 \+ 0.0893) \= 0.504

P(L₂) \= 0.504 \+ (1 \- 0.504) × 0.10 \= 0.554

(Veliki skok jer točan odgovor kombiniran s prethodnim learning step-om jako podiže procjenu znanja.)

**Pokušaj 3 — točan:**

P(L | correct) \= (0.554 × 0.85) / (0.554 × 0.85 \+ 0.446 × 0.10)

               \= 0.471 / (0.471 \+ 0.0446) \= 0.913

P(L₃) \= 0.913 \+ (1 \- 0.913) × 0.10 \= 0.922

(Mastered\! P(L) \> 0.85.)

### 5.6 Problem identifikabilnosti i mitigacija

Beck & Chang (2007) i Hawkins et al. (2014) pokazuju da BKT parametri mogu biti **neidentifikabilni** — različiti skupovi parametara daju gotovo identične predikcije, vodeći do tzv. "degenerate" rješenja (npr. P(G) \> 0.5 što implicira da je pogađanje dominantno). Naše mitigacije:

1. **Fiksne granice parametara**: P(G) ∈ \[0.05, 0.30\], P(S) ∈ \[0.05, 0.20\] — onemogućuje degenerate vrijednosti.  
2. **Tier-based defaults**: svi korisnici kreću s istim parametrima po tier-u; ne fittamo individualno.  
3. **Napomena u radu**: u Fazi 6 (evaluacija) prikupljamo podatke i raspravljamo buduća poboljšanja kroz EM-based fitting ili iBKT (Yudelson 2013).

### 5.7 Integracija s Prologom

BKT izračun je u Pythonu (`backend/bkt/model.py`). Nakon svakog pokušaja:

1. `EvaluatorAgent` šalje rezultat `KnowledgeModelAgent`u  
2. `KnowledgeModelAgent` ažurira P(L) za sve koncepte koje task pokriva  
3. Prije svakog `recommend_next` upita, `RecommenderAgent` dohvaća snapshot BKT-a i **injecta ga u Prolog** kao dinamičke `mastery/3` činjenice:

\# Pseudocode

for (concept, p\_l) in bkt\_snapshot:

    prolog.assertz(f"mastery({user\_id}, {concept}, {p\_l})")

recommendation \= list(prolog.query(f"recommend\_next({user\_id}, Concept)"))\[0\]\['Concept'\]

\# Nakon upita očistimo dinamičke činjenice

prolog.retractall(f"mastery({user\_id}, \_, \_)")

Ovime kombiniramo vjerojatnosno rezoniranje (BKT) sa simboličkim (Prolog prerequisite graf \+ pravila).

---

## 6\. Shema glavne baze podataka

### 6.1 ERD dijagram

erDiagram

    USERS ||--o{ ATTEMPTS : submits

    USERS ||--o{ SKILL\_MASTERY : has

    USERS ||--o{ USER\_BADGES : earns

    USERS ||--o{ XP\_LOG : accumulates

    USERS ||--o{ MISCONCEPTIONS : exhibits

    USERS ||--o{ STREAKS : maintains

    USERS ||--o{ RECOMMENDATIONS\_LOG : receives

    MODULES ||--o{ CONCEPTS : contains

    MODULES ||--o{ TASKS : groups

    CONCEPTS ||--o{ SKILL\_MASTERY : tracked\_by

    CONCEPTS ||--o{ TASK\_CONCEPTS : covered\_by

    CONCEPTS ||--o{ HINTS : targets

    TASKS ||--o{ ATTEMPTS : attempted\_in

    TASKS ||--o{ TASK\_CONCEPTS : covers

    TASKS ||--o{ RECOMMENDATIONS\_LOG : recommended

    ATTEMPTS ||--o{ XP\_LOG : generates

    BADGES ||--o{ USER\_BADGES : awarded\_as

### 6.2 SQL DDL (konsolidirani)

Slijedi finalni DDL za sve tablice glavne baze. DDL je revidiran na temelju plana (Section 8 `diplomski-plan.docx`) s dodatnim indeksima i constraintovima.

\-- \============================================================

\-- USERS — korisnici sustava

\-- \============================================================

CREATE TABLE users (

    id              SERIAL PRIMARY KEY,

    username        VARCHAR(50) UNIQUE NOT NULL,

    email           VARCHAR(255) UNIQUE NOT NULL,

    password\_hash   VARCHAR(255) NOT NULL,

    xp              INTEGER NOT NULL DEFAULT 0 CHECK (xp \>= 0),

    level           INTEGER NOT NULL DEFAULT 1 CHECK (level \>= 1),

    current\_streak  INTEGER NOT NULL DEFAULT 0 CHECK (current\_streak \>= 0),

    longest\_streak  INTEGER NOT NULL DEFAULT 0 CHECK (longest\_streak \>= 0),

    last\_active\_at  TIMESTAMPTZ,

    role            VARCHAR(20) NOT NULL DEFAULT 'student'

                    CHECK (role IN ('student', 'admin')),

    created\_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE INDEX idx\_users\_xp\_desc ON users(xp DESC);  \-- leaderboard

\-- \============================================================

\-- MODULES — 6 modula \+ transverzalni (0)

\-- \============================================================

CREATE TABLE modules (

    id              SERIAL PRIMARY KEY,

    number          INTEGER NOT NULL UNIQUE,  \-- 0 (transverzalni), 1-6

    name            VARCHAR(100) NOT NULL,

    description     TEXT,

    difficulty      VARCHAR(20) NOT NULL

                    CHECK (difficulty IN ('beginner', 'intermediate', 'advanced', 'expert', 'cross\_module')),

    order\_index     INTEGER NOT NULL

);

\-- \============================================================

\-- CONCEPTS — 30 SQL koncepata

\-- \============================================================

CREATE TABLE concepts (

    id              SERIAL PRIMARY KEY,

    code            VARCHAR(50) UNIQUE NOT NULL,

    name            VARCHAR(100) NOT NULL,

    module\_id       INTEGER NOT NULL REFERENCES modules(id),

    tier            VARCHAR(10) NOT NULL CHECK (tier IN ('easy', 'medium', 'hard')),

    description     TEXT,

    order\_index     INTEGER NOT NULL  \-- redoslijed unutar modula

);

CREATE INDEX idx\_concepts\_module ON concepts(module\_id);

CREATE INDEX idx\_concepts\_code ON concepts(code);

\-- \============================================================

\-- CONCEPT\_PREREQUISITES — M:N (koncept ovisi o konceptu)

\-- Dupliciramo Prolog činjenice u SQL za query performance

\-- \============================================================

CREATE TABLE concept\_prerequisites (

    concept\_id      INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,

    prerequisite\_id INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,

    PRIMARY KEY (concept\_id, prerequisite\_id),

    CHECK (concept\_id \!= prerequisite\_id)

);

\-- \============================================================

\-- TASKS — SQL zadaci

\-- \============================================================

CREATE TABLE tasks (

    id                  SERIAL PRIMARY KEY,

    module\_id           INTEGER NOT NULL REFERENCES modules(id),

    title               VARCHAR(255) NOT NULL,

    description         TEXT NOT NULL,

    sandbox\_schema      VARCHAR(100) NOT NULL,  \-- npr. 'ecommerce\_v1'

    expected\_query      TEXT NOT NULL,

    expected\_result     JSONB NOT NULL,          \-- snapshot očekivanog rezultata

    difficulty          INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),

    estimated\_time\_sec  INTEGER,

    is\_active           BOOLEAN NOT NULL DEFAULT TRUE,

    created\_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE INDEX idx\_tasks\_module ON tasks(module\_id);

CREATE INDEX idx\_tasks\_difficulty ON tasks(difficulty);

CREATE INDEX idx\_tasks\_active ON tasks(is\_active) WHERE is\_active \= TRUE;

\-- \============================================================

\-- TASK\_CONCEPTS — M:N (task pokriva koncepte)

\-- Odgovara Prolog covers/2

\-- \============================================================

CREATE TABLE task\_concepts (

    task\_id     INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,

    concept\_id  INTEGER NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,

    is\_primary  BOOLEAN NOT NULL DEFAULT FALSE,  \-- glavni koncept za BKT update

    PRIMARY KEY (task\_id, concept\_id)

);

CREATE INDEX idx\_task\_concepts\_concept ON task\_concepts(concept\_id);

\-- \============================================================

\-- ATTEMPTS — pokušaji rješavanja zadataka

\-- \============================================================

CREATE TABLE attempts (

    id                  SERIAL PRIMARY KEY,

    user\_id             INTEGER NOT NULL REFERENCES users(id),

    task\_id             INTEGER NOT NULL REFERENCES tasks(id),

    submitted\_query     TEXT NOT NULL,

    is\_correct          BOOLEAN NOT NULL,

    error\_type          VARCHAR(100),            \-- 'wrong\_join\_type', 'missing\_where', ...

    execution\_time\_ms   INTEGER,

    rows\_returned       INTEGER,

    xp\_awarded          INTEGER NOT NULL DEFAULT 0,

    hint\_requested      BOOLEAN NOT NULL DEFAULT FALSE,

    attempt\_number      INTEGER NOT NULL CHECK (attempt\_number \>= 1),

    created\_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE INDEX idx\_attempts\_user\_task ON attempts(user\_id, task\_id);

CREATE INDEX idx\_attempts\_user\_created ON attempts(user\_id, created\_at DESC);

CREATE INDEX idx\_attempts\_error\_type ON attempts(error\_type) WHERE error\_type IS NOT NULL;

\-- \============================================================

\-- SKILL\_MASTERY — BKT stanje per user per concept

\-- \============================================================

CREATE TABLE skill\_mastery (

    user\_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    concept\_id      INTEGER NOT NULL REFERENCES concepts(id),

    p\_l             FLOAT NOT NULL DEFAULT 0.15 CHECK (p\_l BETWEEN 0 AND 1),

    p\_t             FLOAT NOT NULL DEFAULT 0.20 CHECK (p\_t BETWEEN 0 AND 1),

    p\_g             FLOAT NOT NULL DEFAULT 0.20 CHECK (p\_g BETWEEN 0 AND 1),

    p\_s             FLOAT NOT NULL DEFAULT 0.10 CHECK (p\_s BETWEEN 0 AND 1),

    attempts\_count  INTEGER NOT NULL DEFAULT 0,

    correct\_count   INTEGER NOT NULL DEFAULT 0,

    last\_updated    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user\_id, concept\_id)

);

\-- \============================================================

\-- MISCONCEPTIONS — detektirani pattern-i grešaka

\-- \============================================================

CREATE TABLE misconceptions (

    id              SERIAL PRIMARY KEY,

    user\_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    code            VARCHAR(100) NOT NULL,   \-- 'left\_join\_vs\_inner\_with\_null'

    description     TEXT,

    occurrences     INTEGER NOT NULL DEFAULT 1,

    first\_seen      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    last\_seen       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user\_id, code)

);

CREATE INDEX idx\_misconceptions\_user ON misconceptions(user\_id);

\-- \============================================================

\-- BADGES — definicije bedževa

\-- \============================================================

CREATE TABLE badges (

    id              SERIAL PRIMARY KEY,

    code            VARCHAR(50) UNIQUE NOT NULL,

    name            VARCHAR(100) NOT NULL,

    description     TEXT,

    icon            VARCHAR(50),

    rule            TEXT NOT NULL,  \-- Prolog pravilo kao string, evaluirano u Fazi 3

    xp\_reward       INTEGER NOT NULL DEFAULT 0

);

\-- \============================================================

\-- USER\_BADGES — koji je korisnik kada zaradio koji badge

\-- \============================================================

CREATE TABLE user\_badges (

    user\_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    badge\_id    INTEGER NOT NULL REFERENCES badges(id),

    earned\_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user\_id, badge\_id)

);

\-- \============================================================

\-- XP\_LOG — audit trail svih XP transakcija

\-- \============================================================

CREATE TABLE xp\_log (

    id          SERIAL PRIMARY KEY,

    user\_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    attempt\_id  INTEGER REFERENCES attempts(id),

    delta       INTEGER NOT NULL,

    reason      VARCHAR(100) NOT NULL,   \-- 'correct\_answer', 'badge\_earned', 'streak\_bonus'

    created\_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE INDEX idx\_xp\_log\_user\_created ON xp\_log(user\_id, created\_at DESC);

\-- \============================================================

\-- STREAKS — dnevni tracking aktivnosti

\-- \============================================================

CREATE TABLE streaks (

    user\_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    date            DATE NOT NULL,

    attempts\_count  INTEGER NOT NULL DEFAULT 0,

    PRIMARY KEY (user\_id, date)

);

\-- \============================================================

\-- HINTS — rule-based fallback hintovi (kada LLM nije dostupan)

\-- \============================================================

CREATE TABLE hints (

    id              SERIAL PRIMARY KEY,

    error\_type      VARCHAR(100) NOT NULL,

    concept\_id      INTEGER REFERENCES concepts(id),

    hint\_text       TEXT NOT NULL,

    difficulty\_min  INTEGER DEFAULT 1 CHECK (difficulty\_min BETWEEN 1 AND 5),

    difficulty\_max  INTEGER DEFAULT 5 CHECK (difficulty\_max BETWEEN 1 AND 5),

    language        VARCHAR(5) NOT NULL DEFAULT 'hr'

);

CREATE INDEX idx\_hints\_error\_concept ON hints(error\_type, concept\_id);

\-- \============================================================

\-- RECOMMENDATIONS\_LOG — log preporuka za evaluaciju RecommenderAgent-a

\-- \============================================================

CREATE TABLE recommendations\_log (

    id                  SERIAL PRIMARY KEY,

    user\_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    recommended\_task\_id INTEGER NOT NULL REFERENCES tasks(id),

    strategy            VARCHAR(50) NOT NULL,    \-- 'weak\_with\_prereqs\_met', 'partial\_continuation', ...

    reasoning           JSONB NOT NULL,          \-- {mastery\_snapshot, prereqs\_met\_list}

    accepted            BOOLEAN,                  \-- je li user kliknuo preporuku (NULL \= pending)

    accepted\_at         TIMESTAMPTZ,

    created\_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE INDEX idx\_recommendations\_user ON recommendations\_log(user\_id, created\_at DESC);

\-- \============================================================

\-- AGENT\_MESSAGES\_LOG — log FIPA-ACL poruka (za debug i evaluaciju MAS-a)

\-- \============================================================

CREATE TABLE agent\_messages\_log (

    id              BIGSERIAL PRIMARY KEY,

    sender          VARCHAR(50) NOT NULL,

    receiver        VARCHAR(50) NOT NULL,

    performative    VARCHAR(30) NOT NULL,    \-- 'request', 'inform', 'agree', ...

    content         JSONB,

    correlation\_id  UUID,

    created\_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE INDEX idx\_agent\_messages\_correlation ON agent\_messages\_log(correlation\_id);

CREATE INDEX idx\_agent\_messages\_created ON agent\_messages\_log(created\_at DESC);

### 6.3 Ključne odluke u dizajnu

- **JSONB za `expected_result` i `reasoning`**: fleksibilnost za različite oblike rezultata (single row, multi-column, aggregations). PostgreSQL JSONB omogućuje indeksiranje i upite preko polja (`->`, `->>`, `@>`).  
- **`concept_prerequisites` duplicira Prolog činjenice**: namjerno. Prolog je source of truth za reasoning, ali SQL tablica omogućuje brze UI query-je ("prikaži prereq graf za korisnika X") bez pyswip round-trip-a.  
- **Soft delete kroz `is_active` na tasks**: nikad ne brišemo zadatke jer attempts referiraju na njih. `ON DELETE` je `RESTRICT` (default).  
- **Cascade delete na korisničke podatke**: kad korisnik izbriše račun, brišu se sve njegove privatne tablice (attempts, skill\_mastery, streaks, xp\_log).  
- **`attempt_number` kolona**: redni broj pokušaja za isti task — omogućuje analitiku "koliko pokušaja prosječno treba za LEFT JOIN".  
- **BigSerial za `agent_messages_log`**: može generirati mnogo poruka tijekom intenzivnih sesija, INT bi se mogao prepuniti.

---

## 7\. Shema sandbox baze podataka

### 7.1 Pregled — e-commerce primjer

Sandbox baza sadrži **8 tablica** e-commerce domene na kojima korisnici izvršavaju SQL zadatke. Domena je odabrana jer:

- Svi studenti imaju intuitivno razumijevanje (kupci → narudžbe → proizvodi)  
- Pokriva sve SQL koncepte (JOIN-ovi kroz relacije, agregacije po kategorijama, subqueries za "kupci koji su kupili X")  
- `employees` tablica omogućuje self-join zadatke (zaposlenik ↔ manager)  
- `suppliers` tablica dodaje 4\. relacijsku razinu za multi-table JOIN-ove

### 7.2 ERD

erDiagram

    CATEGORIES ||--o{ PRODUCTS : classifies

    SUPPLIERS ||--o{ PRODUCTS : supplies

    CUSTOMERS ||--o{ ORDERS : places

    EMPLOYEES ||--o{ ORDERS : processes

    EMPLOYEES ||--o{ EMPLOYEES : manages

    ORDERS ||--o{ ORDER\_ITEMS : contains

    PRODUCTS ||--o{ ORDER\_ITEMS : appears\_in

    PRODUCTS ||--o{ REVIEWS : receives

    CUSTOMERS ||--o{ REVIEWS : writes

### 7.3 SQL DDL sandbox baze

\-- \============================================================

\-- docker/postgres-sandbox/init.sql

\-- \============================================================

CREATE SCHEMA IF NOT EXISTS ecommerce\_v1;

SET search\_path TO ecommerce\_v1;

\-- Read-only role za izvršavanje korisničkih upita

CREATE ROLE sandbox\_readonly NOINHERIT;

\-- \--------------------------------------------------

CREATE TABLE categories (

    id              SERIAL PRIMARY KEY,

    name            VARCHAR(100) NOT NULL UNIQUE,

    description     TEXT

);

CREATE TABLE suppliers (

    id              SERIAL PRIMARY KEY,

    name            VARCHAR(150) NOT NULL,

    country         VARCHAR(50) NOT NULL,

    contact\_email   VARCHAR(255),

    rating          NUMERIC(3,2) CHECK (rating BETWEEN 0 AND 5\)

);

CREATE TABLE products (

    id              SERIAL PRIMARY KEY,

    name            VARCHAR(200) NOT NULL,

    category\_id     INTEGER REFERENCES categories(id),

    supplier\_id     INTEGER REFERENCES suppliers(id),

    price           NUMERIC(10,2) NOT NULL CHECK (price \>= 0),

    stock           INTEGER NOT NULL DEFAULT 0 CHECK (stock \>= 0),

    is\_discontinued BOOLEAN NOT NULL DEFAULT FALSE,

    created\_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE TABLE customers (

    id              SERIAL PRIMARY KEY,

    first\_name      VARCHAR(100) NOT NULL,

    last\_name       VARCHAR(100) NOT NULL,

    email           VARCHAR(255) NOT NULL UNIQUE,

    country         VARCHAR(50),

    city            VARCHAR(100),

    registered\_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()

);

CREATE TABLE employees (

    id              SERIAL PRIMARY KEY,

    first\_name      VARCHAR(100) NOT NULL,

    last\_name       VARCHAR(100) NOT NULL,

    email           VARCHAR(255) NOT NULL UNIQUE,

    manager\_id      INTEGER REFERENCES employees(id),  \-- self-reference\!

    department      VARCHAR(50) NOT NULL,

    salary          NUMERIC(10,2) NOT NULL CHECK (salary \>= 0),

    hired\_at        DATE NOT NULL

);

CREATE TABLE orders (

    id              SERIAL PRIMARY KEY,

    customer\_id     INTEGER NOT NULL REFERENCES customers(id),

    employee\_id     INTEGER REFERENCES employees(id),   \-- nullable: self-service orders

    order\_date      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    status          VARCHAR(20) NOT NULL DEFAULT 'pending'

                    CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled')),

    total\_amount    NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (total\_amount \>= 0\)

);

CREATE TABLE order\_items (

    id              SERIAL PRIMARY KEY,

    order\_id        INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,

    product\_id      INTEGER NOT NULL REFERENCES products(id),

    quantity        INTEGER NOT NULL CHECK (quantity \> 0),

    unit\_price      NUMERIC(10,2) NOT NULL CHECK (unit\_price \>= 0),

    UNIQUE(order\_id, product\_id)

);

CREATE TABLE reviews (

    id              SERIAL PRIMARY KEY,

    product\_id      INTEGER NOT NULL REFERENCES products(id),

    customer\_id     INTEGER NOT NULL REFERENCES customers(id),

    rating          INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),

    comment         TEXT,

    created\_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(product\_id, customer\_id)  \-- jedna recenzija po paru

);

\-- \--------------------------------------------------

\-- Indeksi za realistične EXPLAIN zadatke (Modul 6\)

\-- \--------------------------------------------------

CREATE INDEX idx\_orders\_customer ON orders(customer\_id);

CREATE INDEX idx\_orders\_employee ON orders(employee\_id) WHERE employee\_id IS NOT NULL;

CREATE INDEX idx\_orders\_date ON orders(order\_date DESC);

CREATE INDEX idx\_order\_items\_order ON order\_items(order\_id);

CREATE INDEX idx\_order\_items\_product ON order\_items(product\_id);

CREATE INDEX idx\_products\_category ON products(category\_id);

CREATE INDEX idx\_products\_supplier ON products(supplier\_id);

CREATE INDEX idx\_reviews\_product ON reviews(product\_id);

\-- \--------------------------------------------------

\-- Dodijeli read-only role grantove

\-- \--------------------------------------------------

GRANT USAGE ON SCHEMA ecommerce\_v1 TO sandbox\_readonly;

GRANT SELECT ON ALL TABLES IN SCHEMA ecommerce\_v1 TO sandbox\_readonly;

### 7.4 Veličina seed podataka

| Tablica | Broj redova | Obrazloženje |
| :---- | :---- | :---- |
| `categories` | 15 | Dovoljno za raznoliko grupiranje (Electronics, Books, Sports, …) |
| `suppliers` | 30 | 4 zemlje × \~7 dobavljača po zemlji — omogućuje GROUP BY country |
| `products` | 100 | Raspoređeni po kategorijama i dobavljačima; \~7 po kategoriji |
| `customers` | 200 | Dovoljno za "top 10" zadatke, raspodjela po gradovima i zemljama |
| `employees` | 50 | S hijerarhijom 4 razine (CEO → VPs → Managers → Reps) za self-join |
| `orders` | 1000 | \~5 po kupcu u prosjeku, raspodjela po statusima |
| `order_items` | 3000 | \~3 stavke po narudžbi |
| `reviews` | 500 | \~5 po proizvodu |
| **UKUPNO** | **\~4895 redova** | Dovoljno za realne zadatke, ne ruši 5s timeout |

### 7.5 Sandbox security

Sandbox PostgreSQL instanca (port 5433\) konfigurirana je za sigurnost:

- **Izolirani kontejner** — zasebna Docker instanca, zasebna mreža  
- **Read-only role** za SELECT zadatke — `sandbox_readonly` nema INSERT/UPDATE/DELETE privilegije  
- **Read-write role** samo za DML zadatke (Modul 4\) — kreira se `sandbox_readwrite` privremeno, resetira schema prije svakog pokušaja  
- **Statement timeout** — `SET statement_timeout = 5000` (5s) — ubija dugo trajne upite  
- **Idle in transaction timeout** — `SET idle_in_transaction_session_timeout = 3000` — sprječava leak-ane transakcije  
- **Schema-per-task variant** — za DML zadatke (INSERT/UPDATE/DELETE), svaki pokušaj izvršava se u freshly cloned schemi, tako da jedan korisnikov DELETE ne utječe na drugog  
- **Query parsing prije izvršavanja** — `sqlparse` detektira zabranjene konstrukte (DROP, TRUNCATE, GRANT)

---

## 8\. Alembic setup

### 8.1 Inicijalizacija

Korak-po-korak za postavljanje Alembic migracija u `backend/`:

\# U WSL-u, u root-u repo-a

cd backend

\# 1\. Instaliraj alembic kroz uv (već imamo uv iz Faze 0\)

uv pip install alembic sqlalchemy\[asyncio\] psycopg\[binary\]

\# 2\. Inicijaliziraj Alembic

alembic init alembic

\# 3\. Editiraj alembic.ini — postavi sqlalchemy.url

\# (bolje: koristi env var umjesto hardcoded URL-a)

### 8.2 Konfiguracija `alembic/env.py`

\# backend/alembic/env.py

import os

from logging.config import fileConfig

from sqlalchemy import engine\_from\_config, pool

from alembic import context

\# Import svih SQLAlchemy modela — važno za autogenerate

from app.db.models import Base

config \= context.config

\# Override sqlalchemy.url iz env-a

config.set\_main\_option('sqlalchemy.url', os.getenv('DATABASE\_URL'))

if config.config\_file\_name is not None:

    fileConfig(config.config\_file\_name)

target\_metadata \= Base.metadata

def run\_migrations\_online():

    connectable \= engine\_from\_config(

        config.get\_section(config.config\_ini\_section),

        prefix='sqlalchemy.',

        poolclass=pool.NullPool,

    )

    with connectable.connect() as connection:

        context.configure(connection=connection, target\_metadata=target\_metadata)

        with context.begin\_transaction():

            context.run\_migrations()

run\_migrations\_online()

### 8.3 Prva migracija

\# Kreiraj migraciju iz SQLAlchemy modela

alembic revision \--autogenerate \-m "Initial schema: users, modules, concepts, tasks, attempts, skill\_mastery, misconceptions, badges, xp\_log, streaks, hints, recommendations\_log, agent\_messages\_log"

\# Pregledaj generirani fajl u alembic/versions/

\# Obavezno provjeri da ne briše/mijenja neželjene stvari

\# Primijeni migraciju

alembic upgrade head

\# Verificiraj

psql \-h localhost \-p 5432 \-U postgres \-d sql\_tutor \-c "\\dt"

### 8.4 Versioning strategija

- **Jedna migracija \= jedna logička promjena** — ne kombinirati dodavanje tablice s mijenjanjem druge  
- **Migracije su immutable** — nikad ne mijenjaj postojeću migraciju, uvijek dodaj novu  
- **Naming konvencija**: `{timestamp}_{verb}_{object}.py` (npr. `20260420_add_leaderboard_view.py`)  
- **Uvijek test downgrade** — svaka migracija mora imati funkcionalan `downgrade()` za rollback  
- **Seed podaci NE idu u migracije** — idu u zaseban `seed.py` skript

---

## 9\. Deliverables checklist (milestone Faze 1\)

- [ ] `docs/faza-1-domenski-model.md` finaliziran (ovaj dokument)  
- [ ] `backend/app/db/models.py` — svi SQLAlchemy modeli za 15 tablica  
- [ ] `backend/alembic/versions/001_initial_schema.py` — generirana migracija  
- [ ] `alembic upgrade head` prolazi na glavnoj PostgreSQL bazi  
- [ ] `backend/app/db/seed.py` — seed skripta za 30 koncepata, 6 modula, 5 placeholder bedževa, prerequisite veze  
- [ ] `backend/prolog/ontology.pl` — sve činjenice  
- [ ] `backend/prolog/rules.pl` — sva pravila preporuke  
- [ ] `backend/prolog/badges.pl` — placeholder (prazan, popunjava Faza 3\)  
- [ ] `backend/prolog/prolog_engine.py` — pyswip wrapper s metodama `inject_mastery`, `query_recommendation`, `cleanup`  
- [ ] `docker/postgres-sandbox/init.sql` — 8 tablica \+ indeksi \+ role-ovi  
- [ ] `backend/scripts/seed_sandbox.py` — generator seed podataka za sandbox (\~4900 redova)  
- [ ] `docker-compose up -d postgres-sandbox` pokreće i učitava schemu  
- [ ] `backend/tests/test_recommender_synthetic.py` — testovi 3 sintetička profila prolaze  
- [ ] `backend/bkt/model.py` — klasa `BKT` s metodama `update`, `predict`  
- [ ] `backend/bkt/parameters.py` — tier-based defaults dictionary  
- [ ] `backend/tests/test_bkt.py` — testovi BKT jednadžbi (primjer iz §5.5 prolazi)

---

## 10\. Reference

Nove reference iz literature (dodane uz popis iz plana Section 9):

- **Hawkins, W. J., Heffernan, N. T., & Baker, R. S. J. D. (2014).** Learning Bayesian Knowledge Tracing Parameters with a Knowledge Heuristic and Empirical Probabilities. *Intelligent Tutoring Systems*. Springer. — korišteno u §5.6 za diskusiju identifikabilnosti BKT parametara.  
    
- **Piech, C., et al. (2015).** Deep Knowledge Tracing. *NeurIPS 2015*. — korišteno u §5.1 i §2.1 za opravdanje izbora BKT-a umjesto DKT-a zbog low data requirement i interpretabilnosti.  
    
- **Beck, J. E., & Chang, K.-m. (2007).** Identifiability: A Fundamental Problem of Student Modeling. *User Modeling 2007*. — korišteno u §5.6 za mitigacije identifikabilnosti.  
    
- **Martin, B., Mitrovic, A., Mathan, S., & Koedinger, K. R. (2011).** Evaluating and improving adaptive educational systems with learning curves. *User Modeling and User-Adapted Interaction*. — korišteno u §2.1 za 530-node taksonomiju SQL-Tutora.  
    
- **Ohlsson, S. (1992).** Constraint-based student modeling. *Journal of Artificial Intelligence in Education*. — teorijski background za CBM, za diskusiju razlika BKT vs. CBM.

Postojeće reference iz plana koje su ključne u Fazi 1:

- Corbett & Anderson (1995) — §5.3 BKT jednadžbe  
- Pelánek (2017) — §2.1, §5.1 data requirement za BKT  
- Yudelson et al. (2013) — §5.4, §5.6 tier-based vs. individualized BKT  
- Mitrovic (1998, 2015\) — §2.1 SQL-Tutor granulacija  
- Wagsuriya & Mongkolnam (2017) — §4 ontology-based ITS  
- FIPA (2002), Palanca et al. (2020) — Faza 3 reference

---

*Dokument kraj. Sljedeći korak: implementacija u Claude Code prema akcijskom planu u Section 11 (dodaje se nakon odobrenja ovog dokumenta).*  
