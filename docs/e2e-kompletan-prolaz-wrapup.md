# Kompletan prolaz kroz sučelje — wrapup

**Grana:** `e2e-kompletan-prolaz` · **Datum:** 2026-08-18 · **Trajanje:** 15:58–18:22 UTC
**Račun:** `Maks` / `maks@example.com` (student, `users.id` — v. §A) · **Nalazi:** ERRATA #80–#84

Prvi put je itko prošao **cijelu aplikaciju kroz sučelje**, od registracije do
zadnjeg od 88 aktivnih zadataka. Ovo nije test nego proizvodnja materijala za rad:
galerija od 26 snimki, sekvenca preporuka, BKT krivulje, XP progresija i korpus od
pet savjeta. Sve je išlo kroz Monaco, gumbe i „Sljedeći zadatak" — **nijedan
zahtjev nije poslan mimo sučelja**; mrežni se promet samo promatrao, jer je to
jedini način da se zabilježi točan `error_type`, `xp_delta` i `reason`.

🔴 **Podaci OSTAJU u `tutor_main`.** Prolaz se ne vraća na baseline. Jedini put
natrag je backup snimljen prije početka (§A).

---

## A — Prije početka

| stavka | stanje |
|---|---|
| **Backup** | `backups/tutor_main_20260818_171316.sql.gz` (708 kB) |
| **Restore provjeren** | ✅ **ne samo `rc=0`**: dump je vraćen u privremenu bazu, brojke redaka po 9 tablica identične, i agregat `Σxp/Σtočnih = 706/34` identičan |
| **Backend** | uvicorn `--reload` → jedan radni proces (provjereno: PID 31434 ima točno jedno dijete). `--workers` se ne prosljeđuje jer ga `--reload` isključuje |
| **Kontejneri** | `postgres-main`, `postgres-sandbox`, `prosody` — sva tri gore |
| **`USE_LLM_HINTS`** | `true`, model `claude-haiku-4-5`, `HINT_MAX=5`, dopuna +1 / 4 h |

### Račun — zašto baš `Maks`, bez prefiksa

Prije nego je nastala ijedna snimka provjereno je **što sučelje uopće prikazuje**:

| ekran | prikazuje |
|---|---|
| Dashboard | `Dobrodošao, {username}` / `Bok, {username}` ([`DashboardPage.tsx:113`](../frontend/src/pages/DashboardPage.tsx)) |
| Profil | `Napredak, bedževi i povijest — {username}` |
| Topbar / drawer | `{username}` + rola |
| Ljestvica | `{username}`; **`/leaderboard` e-adresu uopće ne vraća** |

**Zasebnog polja za ime NEMA** — `users` ima samo `username` i `email`, a `email`
se ne renderira nigdje u studentskom putu. Zato je `username` doslovno **`Maks`**:
nijedna snimka ne može pokazati ni prefiks ni e-adresu. Nije bilo potrebe za
odlukom korisnika jer nijedan ekran nije prisiljen prikazati nešto drugo.

🔴 **Posljedica za sljedivost:** račun **nema sentinel prefiks** (`e2e_`, `demo44_`,
`test_`…), pa ga `prepare_eval_baseline.py` neće prepoznati kao testni i **neće ga
obrisati**. To je za ovaj prolaz namjera, ali je i zamka za sljedeću evaluacijsku
pripremu — tko bude čistio bazu prije sudionika mora znati da `Maks` nije sudionik
nego materijal za rad.

### COUNTED_TABLES

| tablica | prije | poslije | Δ |
|---|---:|---:|---:|
| users | 2 | 3 | +1 |
| attempts | 69 | 199 | **+130** |
| xp_log | 36 | 137 | +101 |
| skill_mastery | 22 | 51 | +29 |
| skill_mastery_history | 149 | 488 | **+339** |
| streaks | 11 | 12 | +1 |
| user_badges | 2 | 6 | +4 |
| misconceptions | 14 | 35 | +21 |
| recommendations_log | 292 | 431 | +139 |
| hint_requests | 3 | 8 | +5 |
| agent_messages_log | 32 284 | 34 294 | +2 010 |

🔴 **Baseline više nije onaj od prije.** Brojke „prije" su iz 17:13, prije prolaza;
snimljene su u `docs/prolaz-podaci/counted-tables-{prije,poslije}.txt`. Razlika u
`attempts` je **točno 130** — koliko je i predaja u dnevniku, dakle **nijedna
predaja nije udvostručena** unatoč pet ponovnih pokretanja skripte (§F).

U `agent_messages_log` je uz prolaz upalo i **408 zapisa iz probnih pokretanja**
skripte (tri kratka prolaza na računu `e2e_proba`, koji je poslije uredno obrisan;
sve ostale tablice vraćene su na baseline i provjerene brojkom). Ta tablica nema
`user_id` pa je nijedan cleanup po korisniku ne dohvaća — ERRATA #40/#46.

---

## B — Tijek

### Brojke

| | |
|---|---|
| **Zadataka riješeno** | **88 / 88** (svi aktivni) |
| **Predaja** | **130** |
| Točno iz prve | **54 zadatka (61,4 %)** |
| Jedna netočna pa točna | **26 zadataka (29,5 %)** |
| Dvije netočne pa točna | **8 zadataka (9,1 %)** |
| Verdikti | 88 Točno · 9 Djelomično · 33 Netočno |
| **Završni XP / level** | **4 653 XP · level 47** |
| Level-upova | **46** |
| Bedževa | **4 / 5** |
| Savjeta | **5 potrošenih** + 1 ispravno odbijen |
| BKT točaka | **339** |

Tražena raspodjela bila je ~60/30/10; ostvarena je 61,4/29,5/9,1 — odstupanje
dolazi iz toga što se 88 ne dijeli s 10.

### Redoslijed: preporučivač do 57. zadatka, pa Moduli

Prvih **57** zadataka odredio je **preporučivač** (gumb „Sljedeći zadatak", 87
predaja). U **18:03:30** je tri puta zaredom vratio **već riješen zadatak 39** uz
`reason: repeat_practice` — dakle unutar dosega više nije bilo neriješenog
zadatka, iako ih je **31 ostao neriješen**. Od te točke prolaz je nastavljen
**klikom po konceptu u Modulima** (43 predaje), ovim redom:

```
from_clause → order_by → having_filter → agg_count → agg_min_max → inner_join
→ left_join → full_outer_join → multi_table_join → update → delete
→ correlated_subquery → null_handling → column_alias
```

Raspodjela `reason` vrijednosti kroz cijeli prolaz:
`partial_continuation` 59 · `repeat_practice` 43 · `weak_with_prereqs_met` 28.

---

## C — Savjeti: pet, doslovno, s ocjenom

Limit je 5 i nije se čekala dopuna. Zadaci su birani ondje gdje bi stvaran student
zapeo: teži tier, tek otključan koncept, ili nakon netočne predaje na zadatku
težine 5. Uhvaćena su **oba puta** — katalog (`fallback`) i model (`llm`).

Kriterij ocjene je jedan i doslovan: **opisuje li savjet grešku koju je student
stvarno napravio.** Cijeli korpus s upitima i točnim rješenjima je u
[`docs/prolaz-podaci/d-hintovi.csv`](prolaz-podaci/d-hintovi.csv).

---

### Savjet 1 — zadatak 30 `group_by` (medium, težina 1) · `execution_error` · **izvor `fallback`**

**Student napisao** (zaboravljen `GROUP BY`):
```sql
SELECT category_id, COUNT(*) AS broj_proizvoda FROM products ORDER BY category_id ASC
```
**`detail` koji je sustav imao:** `column "products.category_id" must appear in the GROUP BY clause…`

> **„PostgreSQL traži da svaki stupac iz ispisa koji nije agregat bude naveden i u
> GROUP BY. Poruka koja spominje tu klauzulu znači da jedan stupac ondje
> nedostaje."**

**Ocjena: TOČAN I KORISTAN.** Imenuje točno klauzulu koja nedostaje. Zanimljivo je
*zašto* je siguran: po pravilu iz ERRATE #72 `execution_error` uopće ne ide modelu,
nego katalogu — pa savjet **ne tvrdi ništa o sadržaju studentova upita** i nema
što promašiti. Cijena je generičnost; korist je da ne može lagati.

---

### Savjet 2 — zadatak 35 `having_filter` (medium, težina 2) · `row_mismatch` · **izvor `llm`**

**Student napisao** (jedina razlika: `ASC` umjesto `DESC`):
```sql
… GROUP BY category_id HAVING COUNT(*) > 6 ORDER BY broj_proizvoda ASC, category_id ASC
```
**`detail` koji je otišao modelu:** `Row 0 differs`

> **„Provjeri jesi li koristio HAVING klauzulu da filtriraš samo grupe gdje je
> brojač proizvoda veći od 6 — taj uvjet ne ide u WHERE, već nakon GROUP BY.
> Također provjeri koristi li tvoj upit GROUP BY category_id kako bi SQL znao kako
> grupiraj podatke prije brojanja."**

🔴 **Ocjena: NETOČAN.** Student je **već** napisao i `HAVING COUNT(*) > 6` i
`GROUP BY category_id`. Savjet objašnjava grešku koje nema, a **ne spominje
sortiranje**, koje je jedina razlika. Student koji ga posluša mijenja ispravan dio
upita.

---

### Savjet 3 — zadatak 3784 `explain_plan` (hard, težina 3) · `plan_mismatch` · **izvor `llm`**

**Student napisao** (`CAST` poništava indeks):
```sql
… WHERE CAST(o.customer_id AS TEXT) = '42' ORDER BY o.id, oi.product_id
```
**`detail`:** `Rezultat je točan, ali upit ne koristi indeks, a rješenje ga koristi; strategija spoja je Hash Join, a traži se Nested Loop.`

> **„Provjeri EXPLAIN plan za svoj upit: vidišь li Hash Join ili Nested Loop? Ako
> vidiš Hash Join, to znači da baza ne koristi indeks na customer_id — provjeri
> piše li se customer_id direktno kao broj ili ga negdje pretvaraš (npr. CAST,
> operacija). Indeks se aktivira samo ako ga filtar koristi u originalnom obliku."**

**Ocjena: TOČAN I KORISTAN.** Imenuje točan anti-obrazac (`CAST` nad stupcem) i
točnu posljedicu u planu. Usput: u tekstu stoji **`vidišь`** — zalutali ćirilični
znak iz modela (ERRATA #83).

---

### Savjet 4 — zadatak 55 `multi_table_join` (hard, težina 5) · `wrong_columns` · **izvor `llm`**

**Student napisao** (zaboravljen alias na `COUNT(DISTINCT p.id)`):
```sql
SELECT s.name AS supplier_name,
       COUNT(DISTINCT p.id),          -- ← bez AS distinct_products_sold
       SUM(oi.quantity) AS total_quantity, …
```
**`detail`:** `Stupci se razlikuju — dobiveni: ['avg_review_rating', 'count', 'supplier_name', 'total_quantity'], očekivani: [… 'distinct_products_sold' …]`

> **„Provjeri redoslijed stupaca u SELECT klauzuli — trebali bi biti
> supplier_name, distinct_products_sold, total_quantity i avg_review_rating, ali
> čini se da su drugačiji u tvojoj listi. Provjeri i redoslijed kako su navedeni u
> upitu i imena koja si dao aliasima za agregacijske funkcije."**

**Ocjena: TOČAN I KORISTAN.** Imenuje stupac koji nedostaje i upućuje na aliase
agregata — točno na grešku. Uzrok djelomično pripisuje „redoslijedu", što nije
točno, ali cilj je pogođen.

---

### Savjet 5 — zadatak 62 `correlated_subquery` (hard, težina 5) · `row_mismatch` · **izvor `llm`**

**Student napisao** (jedina razlika: `LIMIT 7` umjesto `LIMIT 5`).
**`detail`:** `Row count mismatch: actual=7 vs expected=5`

> **„Tvoj upit vraća više redaka nego što bi trebalo — provjeri je li u
> koreliranome podupitu ispravno filtriran skup narudžbi protiv kojega se računa
> prosjek. […] Provjeri WHERE klauzulu u podupitu — je li referencirano
> customer_id iz vanjske tablice?"**

**Ocjena: DJELOMIČNO TOČAN.** Prva rečenica je **točna i utemeljena u `detail`u**.
Ostatak nagađa kvar u koreliranome podupitu — koji je student napisao **ispravno**
— i šalje ga da prepravlja dio koji radi.

---

### Šesti klik: kredit potrošen

Na zadatku 4 (`null_handling`, nakon dvije netočne predaje) kliknut je savjet sa
**0 preostalih**. Sustav je odgovorio *„Potrošio si sve savjete za sada. Sljedeći
savjet za 1 h 49 min."* i **nije potrošio ništa** — izmjereno `0 → 0`, bez retka u
`hint_requests`. Ponašanje je ispravno i poruka nosi konkretno vrijeme dopune.

### Što korpus pokazuje kao cjelinu

| `error_type` | izvor | savjeta | pogodili grešku |
|---|---|---:|---|
| `execution_error` | fallback | 1 | **1/1** |
| `plan_mismatch` | llm | 1 | **1/1** |
| `wrong_columns` | llm | 1 | **1/1** |
| `row_mismatch` | llm | 2 | **0/2** (jedan djelomično) |

Podjela nije slučajna i objašnjava se **sadržajem `detail`a**, ne tipom:

- `wrong_columns` i `plan_mismatch` šalju **imenovani** detalj (koji stupac, koji
  čvor plana) → model imenuje pravu grešku;
- `row_mismatch` šalje **`Row 0 differs`** — interni engleski niz koji ne kaže
  *što* se razlikuje → model rupu popuni iz opisa zadatka i izgovori je kao
  činjenicu o studentovu upitu.

To je **isti mehanizam koji ERRATA #72 opisuje za `UNDERDETERMINED_TYPES`**, samo
na tipu koji je razvrstan kao „siguran". Nalaz je zaveden kao **ERRATA #80**.

---

## D — Podaci za rad

Sve u [`docs/prolaz-podaci/`](prolaz-podaci/), izvezeno skriptom
[`scripts/prolaz/3_izvoz.py`](../scripts/prolaz/3_izvoz.py):

| datoteka | redaka | sadržaj |
|---|---:|---|
| `a-sekvenca.csv` | 130 | redni broj · zadatak · koncept · modul · `reason` preporuke · pokušaj · greška studenta · `error_type` · `detail` · XP · level · streak |
| `b-bkt-krivulje.csv` | 339 | `p_l` po konceptu nakon svakog pokušaja + redni broj točke u krivulji |
| `c-xp-level.csv` | 101 | kumulativni XP kroz vrijeme, oznaka level-upa |
| `c-bedzevi.csv` | 4 | bedževi s vremenom osvajanja |
| `d-hintovi.csv` | 6 | svih 5 savjeta doslovno + odbijeni šesti, s upitom, točnim rješenjem i ocjenom |
| `e-vremena.csv` | 130 | trajanje svake predaje |
| `sazetak.json` | — | agregati |

### Vremena odgovora `/attempt` (N = 1 student)

Mjereno **u pregledniku**, od klika na Submit do odgovora — dakle cijeli lanac
gateway → Coordinator → Evaluator → KM → Gamification → Recommender.

| | ms |
|---|---:|
| N | 129 valjanih |
| min | 184 |
| **p50** | **227** |
| **p95** | **283,5** |
| max | 5 331 |

`max` je zadatak 52 — namjerni kartezijev produkt koji sandbox prekida nakon 5 s;
to je granica sustava, ne njegova latencija.

🔴 **Jedno mjerenje (od 130) je odbačeno** jer je ispalo negativno (−1 628 ms):
sistemski sat je pod WSL2 skočio unatrag između početka mjerenja i odgovora.
Odbačeno je **prebrojano i prikazano**, ne prešućeno.

🔴 **Ovo NIJE mjerenje opterećenja.** Jedan student, sekvencijalno, bez ijedne
istovremene predaje. Brojka govori koliko lanac traje kad je slobodan, i ništa o
tome kako se ponaša pod paralelnim opterećenjem.

---

## E — Što bi student osjetio

**Prvih pet minuta su dobre.** Registracija je jednostavna, Dashboard novaka ne
laže praznim grafovima nego kaže „prvi zadatak te već čeka", a Moduli pošteno
pokazuju da je gotovo sve zaključano. Prvi zadatak je lagan, prvi „Točno" stigne
za dvjestotinjak milisekundi i odmah donese bedž. Brzina je ovdje stvarna prednost
— ništa se ne čeka.

**Onda se izgubi osjećaj mjesta.** Treći zadatak je `INNER JOIN`, četvrti
`CROSS JOIN` — a student još nije vidio `WHERE`. Do desetog koraka bio je u
modulima 1, 3, 4 i 5, i ni jedan nije dovršio. Sustav to objašnjava rečenicom
„Sustav vodi prema konceptima s najnižom procjenom znanja, pa se teme mogu
izmjenjivati", što je istinito, ali **student koji je otvorio Module vidi
uredno numerirano gradivo i ne razumije zašto ga sustav vodi drukčije**. To je
mjesto na kojem bi stvaran student prvi put zastao.

**Level prestane nešto značiti.** Do kraja prolaza student je prošao **46
level-upa** — u prosjeku jedan na svaka dva zadatka. Konfeti koji su na prvom
level-upu bili nagrada do trideset i petog su smetnja koja prekriva ekran.
Bedževi se pak potroše rano: zadnji (`join_master`) stigao je oko 2/3 prolaza, pa
**posljednjih tridesetak zadataka ne donosi nijedno priznanje**. Peti bedž
(`streak_7`) traži sedam uzastopnih dana i u jednoj sesiji je nedostižan po
dizajnu.

**Povratna sprega je najbolji dio sustava.** Tri stanja se jasno razlikuju,
„Djelomično" uz +20 XP je pošteno prema studentu koji je skoro pogodio, a M6
poruka *„Rezultat je točan, ali upit se ne izvodi kako zadatak traži"* točno
pogađa ton — ne kaže studentu da je pogriješio SQL, nego da nije pogodio pouku.

**Savjet je kocka.** Kad sustav zna što je krivo (koji stupac, koji čvor plana),
savjet je izvrstan. Kad zna samo da se nešto razlikuje, izmisli uvjerljivu i
netočnu dijagnozu — a student nema način razlikovati ta dva slučaja. Uz limit od
pet savjeta na 88 zadataka, dva promašaja su 40 % potrošenog kredita.

**Kraj nema kraj.** Nakon 57 zadataka „Sljedeći zadatak" počne vrtjeti isti već
riješen zadatak uz „Ovaj si zadatak već riješio — ponovi ga za vježbu". Student
koji se oslanja na taj gumb u tom trenutku **misli da je gotov**, a 31 zadatak ga
još čeka u Modulima. Ni sa svih 88 riješenih ne pojavi se ekran „Svi koncepti
savladani" — put se jednostavno zavrti u mjestu.

**Zadnji dojam je proturječan:** Profil kaže „Osvojeno 4 od 5", Dashboard nudi
ponavljanje već riješenog zadatka, a kartica „Za ojačati" pokazuje `CROSS JOIN` na
**77 %** iako su oba njegova zadatka riješena.

---

## F — Nalazi

Puni tekst je u [`docs/errata.md`](errata.md). Ovdje sažetak.

| broj | nalaz | težina |
|---|---|---|
| **#80** | 🔴 Savjet za `row_mismatch` promašuje jer mu `detail` (`Row 0 differs`) ne imenuje razliku — 0/2 pogotka na stvarnom prolazu | prijetnja valjanosti savjeta |
| **#81** | 🔴 `syntax_error` je kroz sučelje NEDOSTIŽAN — klijentski gard blokira predaju praznog upita, a to je jedini ulaz u tu granu | rupa u taksonomiji |
| **#82** | 🟡 Stanje „Svi koncepti savladani" ne nastaje ni sa 88/88 — `repeat_practice` uvijek vrati `task_id` | mrtav ekran |
| **#83** | 🟢 Zalutali ćirilični znak u tekstu savjeta (`vidišь`) | kozmetika |
| **#84** | 🟡 Ispuštanje `ORDER BY` iz upita ocjenjuje se TOČNIM jer se `order_matters` izvodi iz **predanog** upita | pedagoška rupa |

### Potvrde i opovrgnuća zatečenih nalaza

**ERRATA #77 — POTVRĐENA na stvarnom prolazu.** Simulacija je predviđala prvi spoj
oko 3. koraka i `where_filter` oko 5.–13.; izmjereno kroz sučelje: **prvi spoj
(`inner_join`) je 3. korak, `where_filter` 5.** Do 10. koraka student je bio u
M1, M3, M4, M5 i M0. Ovo više nije predviđanje modela nego zabilježeno ponašanje.

**ERRATA #68 — POTVRĐENA.** `column_alias` **nijednom** nije ponuđen preporukom
kroz 57 preporuka. Njegova tri zadatka riješena su tek klikom po konceptu, i to
kao **posljednja tri u cijelom prolazu**.

**ERRATA #35/#31 (ZPD escape) — vidljiva u brojkama.** `where_filter` ima **43**
BKT točke na 3 vlastita zadatka, `order_by` **40** na 2, `select_basic` **32** na
2 — dakle 90 % ažuriranja dolazi iz zadataka u kojima je koncept sporedan. Sva
četiri koncepta završavaju na `p_l = 1.0000`.

**Preporučivač NIJE ponudio ništa besmisleno.** Kroz 57 preporuka nije bilo
zadatka izvan dosega ni koncepta bez ispunjenih preduvjeta; `reason` je uvijek bio
jedan od tri legitimna. Prigovor iz #77 je **kurikularni**, ne logički.

**M6 je dosegnut i radi.** `explain_plan` i `index_usage` ocijenjeni su
plan-usporedbom; `plan_mismatch` (2×) i `explain_submitted` (2×) uredno su nastali
i prikazani. Poruka i `detail` su pedagoški, ne tehnički.

**Gamifikacija na 88 zadataka:** v. §E — 46 level-upa i 4/5 bedževa, pri čemu
posljednja trećina prolaza ne donosi nijedno novo priznanje.

### Pokrivenost taksonomije grešaka

| `error_type` | pojava | kroz sučelje |
|---|---:|---|
| `wrong_columns` | 14 | ✅ |
| `execution_error` | 9 | ✅ |
| `row_mismatch` | 9 | ✅ |
| `empty_result` | 5 | ✅ |
| `plan_mismatch` | 2 | ✅ |
| `explain_submitted` | 2 | ✅ |
| `timeout` | 1 | ✅ |
| **`syntax_error`** | **0** | 🔴 **nedostižan — ERRATA #81** |

🔴 **Svih 42 netočnih predaja dalo je TOČNO onaj `error_type` koji je offline
verifikacija predvidjela — nula odstupanja.** Netočni upiti izvedeni su iz
`expected_query` imenovanim studentskim greškama i svaki je prije prolaza pušten
kroz `agents.evaluation.evaluate`, pa se u prolaz nije ušlo s pretpostavkom.

---

## G — Kako se prolaz ponavlja

```bash
cd backend && uv run python ../scripts/prolaz/1_kandidati.py   # mutacije + verifikacija
python3 scripts/prolaz/2_plan.py                                # plan (60/30/10)
cd frontend && npx playwright test --config=playwright.prolaz.config.ts
python3 scripts/prolaz/3_izvoz.py                               # CSV-ovi
```

Stanje je u `frontend/e2e-prolaz/.stanje/stanje.json` (gitignorirano). Ponovno
pokretanje se **prijavi na postojeći račun i nastavi** — preskače riješene zadatke
i, unutar zadatka, predaje koje su već u bazi. To nije udobnost nego nužnost:
prolaz se ne vraća na baseline, pa bi ponavljanje iz nule udvostručilo podatke.

### Tri kvara vlastite skripte (ne aplikacije), da se ne ponove

1. **Playwright učita spec dvaput** (jednom da prebroji testove, jednom u
   workeru). Zapis stanja u konstruktoru uvjerio je drugo učitavanje da je riječ o
   nastavku. Datoteka sada nastaje tek pri prvom stvarnom događaju.
2. **`.view-lines` se čita prije nego Monaco iscrta sve retke** → jedno očitanje
   vratilo je „delete from orders" umjesto tri retka i prolaz je stao. Provjera
   sada anketira do 6 s.
3. **Klik na `.view-lines` presreće `<p>` s opisom zadatka** (45 s čekanja, pa
   pad). Unos sada ide **fokusom na Monacov `textarea`**, koji ne radi hit-test.
   Uz to je `actionTimeout` postavljen na 45 s — Playwrightov default je *bez
   granice*, pa je jedan neizvediv klik prije toga visio 16 minuta bez ijedne
   poruke.

Nijedan od ta tri nije kvar aplikacije; svi su zabilježeni ovdje jer bi se inače
ponovili pri sljedećem prolazu. **Sve što je nađeno u aplikaciji ostavljeno je
nepopravljeno i zavedeno u erratu**, kako je i traženo.
