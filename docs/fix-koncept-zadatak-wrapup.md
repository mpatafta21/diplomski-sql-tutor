# Fix „koncept → zadatak" — wrapup

**Datum:** 2026-08-14 · **Grana:** `fix-koncept-do-zadatka` (s `main`a) ·
**Plan:** [`fix-koncept-zadatak-korak-0.md`](fix-koncept-zadatak-korak-0.md)

Dva zatečena nalaza sa zajedničkim korijenom, oba zatvorena. Nijedan nije uveo Faza 5.

---

# 0. Isporučeno

| commit | sadržaj |
|---|---|
| `0fafd30` | reprodukcijski testovi (2 padaju namjerno) + korak-0 |
| `cf97b20` | `recommendable/1` u `rules.pl` + injekcija |
| `9f5ea65` | `GET /task-for-concept/{code}` + `resolve_task_for_concept` |
| `2fb0035` | frontend linkovi kroz `/koncept/:code` + e2e gate |
| `c82d1a1` | jedan upit za sve kategorije umjesto tri |
| `ae39cb6` | drugi oblik ćorsokaka — koncept kojemu je sve riješeno (v. A.6) |
| `d0f4904` | `/modules` više ne nosi `entry_task_id` (v. B.5) |
| `c138e00` | „Sve savladano" više ne zvuči kao kraj puta (v. B.6) |
| `b9d4091` | ispravak zastarjelih brojki u opisu Kat. C |
| `a3366f9` | brojač riješeno/ukupno uz postotak — ERRATA #42 (v. C.2) |
| `97cdfb8` | kvačica znači „nema novog zadatka", ne „savladano" (v. C.3) |
| `ef479b6` | tooltip: postotak je procjena znanja (v. C.4) |
| `28daf4b` | podcrtana samo brojka, ne separator ispred nje |
| `89851dd` | falsifikacijski gate (200 stanja) + zaostala papirologija |
| `bda5e36` | nalazi iz `code-review` prije mergea (v. §G) |

**Novih testova:** 20 (recommender 11, ruta 8, `/profile` 1) + 1 e2e.
**Nula promjena sheme.** **Nula novih ovisnosti** (`radix-ui` je bio u `package.json`).

🔴 **Opseg je narastao nakon prvog zatvaranja** — kvarove 2 i 3 (§A.6, §C) korisnik je
našao testiranjem popravljenog sučelja, ne plan. Oba su zatečena; drugi je popravak prvog
učinio vidljivim.

---

# A — Kvar 1: ćorsokak na transverzalnom konceptu

## A.1 Uzrok nije bio ondje gdje ga je nalaz smjestio

Zapis u memoriji opisuje kao mehanizam neslaganje tranzitivnih i izravnih prereqs
(`build_mastery_snapshot` korak 4 gleda `all_prereqs`, `rules.pl prereqs_met` samo
izravne). To **jest okidač, ali nije uzrok.**

Uzrok: `_BLOCK_VALUE = 0.0` nosi **dvije uloge**. Postoji da blokira nizvodne koncepte
(`inner_join` se ne smije otključati dok `join_condition` nema svoje prereqs), ali 0,0 je
ujedno `weak` (< 0,30), pa isti broj koncept čini i **kandidatom za preporuku**.

🔴 **Poravnanje prereqs računice — naizgled očit popravak — bilo bi gore od kvara.**
`join_condition` bi postao 0,99 čim `from_clause` sazrije i **lažno otključao**
`inner_join`. To je točno kvar zbog kojeg Kat. A uopće postoji (v. docstring
`recommender_logic.py:15-20` i zatečeni test T4). Taj put je odbačen u planu i ovdje se
bilježi da ga netko kasnije ne otkrije kao „propuštenu jednostavnu opciju".

## A.2 Mehanizam je PRIORITET, ne prazan skup kandidata

Izmjereno na stvarnom motoru, profil iz nalaza (`from_clause` 0,99998 · `select_basic`
0,8412):

```
actionable skup ima TRI člana: join_condition, select_basic, where_filter
join_condition = 0.0 → weak → klauzula 1 + cut → pobijedi
select_basic (0,8412) i where_filter → partial → klauzula 2, nikad se ne stigne
→ select_task_for_concept(join_condition) → None → reason="exhausted"
```

Dakle nije bilo „nema kandidata sa zadacima" — bila su dva, ali ih je transverzalni
preskočio prioritetom.

**Zašto ga suite nije uhvatio:** zatečeni T4 testira novaka, a novaku `from_clause` nije
mastered pa `prereqs_met(join_condition)` padne i klauzula 1 se ne upali. Uvjet ulaska je
**`from_clause` savladan + `select_basic` < 0,85**, a `from_clause` saturira brzo
(sekundarni koncept gotovo svakog zadatka) — stanje kroz koje realno prolazi svaki
sudionik.

## A.3 Popravak provodi pravilo koje je kod već propisivao

`recommendable/1` — koncepti s ≥ 1 aktivnim primary zadatkom. Kat. B i C to pravilo već
poštuju kroz masku 0,99 (`recommender_logic.py:240-243`: *„maskiranje je na razini
KONCEPTA, ne taska"*); Kat. A ga je zaobilazila kroz 0,0.

**Nedirnuto:** `_BLOCK_VALUE`, korak 4 snapshota, `all_prereqs`, maske 0,99, pragovi,
`transversal_concepts`, `subfloor_concepts`. Blokada nizvodnog teče kroz `mastered/2`,
koji ne zna za `recommendable`.

## A.4 🔴 Greška u prvoj izvedbi, i zašto je vrijedi zapisati

Guard je prvo stavljen kao **PRVI** cilj u klauzuli. S nevezanim `Concept` on time postaje
**generator**: poredak rješenja prestaje ovisiti o `mastery/3` (kanonski pedagoški slijed)
i počinje ovisiti o poretku `recommendable/1` fakata — koji su se tada injektirali iz
Python **seta**, dakle poretkom ovisnim o hashu i promjenjivim između procesa.

**To je mehanizam ERRATE #60** — preporuka koja se mijenja bez ijedne izmjene koda.
Simptom je bio pad zatečenog testa: M1+M2 mastered dalo je `update` umjesto `inner_join`.

Obrazloženje u prvoj verziji komentara bilo je i netočno („guard mora biti prvi da ne
potroši cut") — cut je na **kraju** tijela, pa pozicija guarda na njega ne utječe; utječe
samo na to tko nabraja.

**Popravljeno dvostruko:** guard je zadnji cilj prije cuta (čisti filtar nad već vezanim
konceptom), a injekcija ide kanonskim poretkom umjesto iz seta.

## A.5 C.4 iz plana — lažno slavlje se ne može dogoditi

Pitanje: može li guard ostaviti sustav bez kandidata, pa `recommend_next` padne →
`no_recommendation` → `TaskEntryPage` prikaže „Sve savladano" iako student ima što raditi?

Izmjereno na 4000 nasumičnih stanja kroz stvarni Prolog motor (`findall` nad postojećim
predikatima, bez reimplementacije pravila u Pythonu): **0 povreda**.

Strukturni razlog: graf ima **točno jedan korijen** — `select_basic`, koji je
recommendable i nemaskiran. Transverzalni je 0,0 samo ako mu je neki uzvodni koncept
nesavladan; penjanjem uz lanac uvijek se stigne do nesavladanog **recommendable** koncepta
s ispunjenim prereqs.

🔴 **Ovaj dokaz vrijedi SAMO za tadašnju, slabiju definiciju kandidata** („koncept ima
zadatke"). Per-user invarijanta iz A.6 ga poništava — ondje korijen može ispasti iz
kandidata a ostati nesavladan. Zato A.7 uvodi rezervu. Zapisano ovdje da se dokaz ne
citira izvan uvjeta pod kojima je izveden.

## A.6 🔴 DRUGI OBLIK ISTOG ĆORSOKAKA — nađen nakon prvog zatvaranja

Nakon prvih pet commitova korisnik je javio da na računu `admin` i dalje piše „Nema novih
zadataka". Izmjereno:

```
admin: riješeno 9 / 80 → 71 NERIJEŠEN zadatak
preporuka: where_filter — 3 zadatka, SVA TRI riješena, p_l = 0,7728
→ select_task_for_concept → None → "exhausted"
```

Isti simptom, drugi uzrok: kvar iz nalaza bio je koncept **bez ijednog zadatka**
(transverzalni); ovaj je koncept **sa zadacima kojih je student sve riješio**, a mastery mu
je ispod praga — pa ostaje kandidat zauvijek. `insert` (2/2, p_l 0,7702) bio je drugi takav.

🔴 **Ovo je bila pogrešna procjena, ne propust u analizi.** U `concepts_with_tasks` je
izrijekom pisalo da definicija namjerno glasi „IMA zadatke", a ne „ima NERIJEŠENE zadatke",
da bi se sačuvalo stanje `exhausted` koje zatečeni test očekuje. Sačuvano je očekivanje
testa, a posljedica je trajna slijepa ulica. **Ispravna invarijanta je „koncept može dati
zadatak OVOM korisniku"**, a prva izvedba je provela njezinu slabiju verziju.

Zatečeni `test_exhausted_concept_returns_exhausted` tvrdio je upravo to ponašanje i time
zaključao ćorsokak kao specifikaciju — klasa NALAZA #57 (test pisan prema promatranom
ponašanju).

**Odluka korisnika 2026-08-14:** preporuka prelazi na drugi koncept.

## A.7 Rezerva, jer nova invarijanta otvara stanje koje stara nije imala

Per-user invarijanta poništava dokaz iz A.5. Ako **korijenski** koncept (`select_basic`,
jedini korijen) ispadne iz kandidata a nije savladan, `prereqs_met` blokira sve nizvodno →
`recommend_next` padne → `no_recommendation` → sučelje javi **„Sve savladano"**. To je laž,
i gore od početnog kvara.

Zato ljestvica, ne prekidač:

1. koncept s **neriješenim** zadatkom unutar ZPD-a;
2. ako takvog nema → drugi Prolog krug sa širim skupom (koncepti koji imaju zadatke) →
   `reason="repeat_practice"` + riješen zadatak za ponavljanje. Ponavljanje diže mastery
   kroz BKT i time otključava ostatak grafa;
3. tek ako ni to → `no_recommendation` (istinito).

Drugi krug se plaća samo u tom rijetkom stanju. Obje grane imaju vlastiti test.

---

# B — Kvar 2: klik na koncept vodio na riješen zadatak

`entry_task_id` u `/modules` je statičan (`ORDER BY difficulty, id`, bez usera). Kako
student napreduje, promašaj postaje **vjerojatniji** — najlakše rješava prvo, a link uvijek
nudi najlakše.

## B.1 🔴 Obrazloženje „cacheable katalog" nije stajalo kako je zapisano

| tvrdnja iz komentara | izmjereno |
|---|---|
| „bez user-konteksta" | ruta traži `Depends(get_current_user)`; `_user` je namjerno neiskorišten |
| „cacheable" | nula `Cache-Control` headera u `backend/app/`; jedini keš je React Query `staleTime: 5 min` |

**Odlučujuće:** `["modules"]` se **ne invalidira ni na jednu predaju**. User-aware polje u
`/modules` zato bi do 5 minuta nakon rješavanja i dalje nudilo riješen zadatak — isti kvar,
samo rjeđi i teže uočljiv. To je jači razlog protiv te opcije od „gubi se cacheability".

## B.2 Dva različita `None` koja se nisu dala razlikovati

`select_task_for_concept` vraćao je `None` i za „koncept nema zadataka" i za „svi
riješeni". `resolve_task_for_concept` ih razdvaja u `(id, False)` / `(id, True)` /
`(None, False)`, a stari potpis **delegira** na nju i zadržava svoj ugovor — „sve riješeno"
i dalje daje `None`, pa `recommend()` i dalje vraća `exhausted`.

Zadatak za ponavljanje nudi se **samo** na izravan klik, gdje ga je korisnik zatražio.

## B.3 Rubni slučaj ispao jeftiniji od procjene

Odabrano je „vodi na riješen uz oznaku". Procjena u planu bila je da to traži novo stanje
na eval-verificiranom Task ekranu. **Ne traži** — bedž „Riješeno" postoji od ranije
(`TaskPage.tsx:449-457`), a komentar uz njega već propisuje baš to ponašanje; poslije
predaje `FeedbackPanel` pokaže „Već riješeno · bez XP".

## B.4 `entry_task_id` ostaje _(nadiđeno u B.5)_

Prva odluka: ne uklanjati. Polje je i dalje bilo točan signal „koncept ima aktivnih
zadataka" i time uvjet klikabilnosti u oba potrošača, pa `/modules` nije trebao izmjenu
ugovora. Zapisano kao „kandidat za čišćenje, ne obveza".

## B.5 …pa je ipak uklonjen

**Ispravak tvrdnje iz B.4 i iz ranije verzije §E:** ondje je pisalo da je polje ostalo
„bez potrošača". To **nije bilo točno** — točna tvrdnja je „bez potrošača **za
navigaciju**". Klikabilnost je i dalje visjela o njemu
(`ConceptRow.tsx:68`, `MasteryHighlights.tsx:40`).

Taj posao je preuzeo `primary_task_count > 0`. Ekvivalencija nije pretpostavljena — ruta ju
je gradila po konstrukciji (ista `is_primary + is_active` maska), a **zatečena suita ju je
već tvrdila**:

```python
assert (c["entry_task_id"] is not None) == (c["primary_task_count"] > 0)
```

🔴 **Zašto uklanjanje, a ne ostavljanje mrtvog polja.** Kao polje s konkretnim `task_id`-em
pozivalo je da se na njega opet linka — dakle da se vrati kvar koji je ova grana upravo
zatvorila. Brojač nema odredište u sebi i ne može se tako zloupotrijebiti.

Zamjenski test je namjerno **širi od imena polja**: nijedan ključ u čvoru koncepta ne smije
sadržavati `task_id`, jer bi isti kvar pod drugim imenom prošao. Klijent koristi postojeći
`hasOwnTasks()` (`lib/mastery.ts`), jedini izvor tog pravila za cijeli frontend od 4.4b.

Ugovor: `openapi.json` −11 redaka, `schema.d.ts` −2. Nula promjena sheme baze.

## B.6 „Sve savladano" više ne zvuči kao kraj puta

Uočeno pri falsifikaciji (`no_recommendation` u 397 od 1500 stanja): taj reason znači da su
svi koncepti **iznad praga**, ne da su svi zadaci riješeni. To dvoje se razilazi — koncepti
imaju 2–5 zadataka, a BKT saturira brže nego što se svi riješe.

Zatečeni tekst („Trenutno nema koncepta za preporuku — sve je savladano.") čitao se kao
„nema više što raditi" i studentu s desetcima neriješenih zadataka bio je terminalan. Sada
govori o savladanosti i upućuje na Module, uz gumb na `/modules` kao primarnu akciju u tom
stanju.

🔴 **Zatečeno ponašanje ZPD dizajna, ne kvar koji je uvela ova grana.** Zabilježeno jer ga
je tek falsifikacija učinila vidljivim.

---

# C — Kvar 3: ekran je miješao ZNANJE i NAPREDAK

Nađen tek kad je korisnik prošao kroz popravljeno sučelje. Nije regresija ove grane —
zatečeno stanje koje je popravak kvara 2 učinio vidljivim: kad klik konačno vodi na
neriješen zadatak, postaje očito da redak ne govori koliko ih je ostalo.

## C.1 Jedan korijen, tri pritužbe

Postotak na Modulima je **BKT procjena znanja**, ne napredak kroz zadatke. Razilaze se u
**oba** smjera, izmjereno na `admin`u:

| koncept | prikazano | riješeno (primarni) |
|---|---|---|
| `select_basic` | Savladano · 99 % | **1/2** |
| `from_clause` | Savladano · 99 % | **1/3** |
| `where_filter` | 77 % | **3/3** |
| `insert` | 77 % | **2/2** |

Posljedice koje je korisnik prijavio, sve tri iz istog korijena: (a) koncept na 99 % ima
neriješenih zadataka; (b) klik na koncept sa 77 % vraća **već riješen** zadatak — jer ondje
doista nema neriješenog; (c) `limit_offset` je na 75 % uz **0/3** riješena.

Treći slučaj ima vlastiti mehanizam: **BKT ažurira SVE koncepte zadatka, ne samo primarni.**
Potvrđeno u kodu — `evaluator_agent.py:200-204` šalje sve koncepte, `knowledge_agent.py:49`
ih uzima **bez filtriranja po `is_primary`**. Dakle `order_by` je na 77 % jer su riješena
tri zadatka u kojima je **sporedan**, a nijedan kojemu je glavna tema.

🔴 Preporučivač se sve vrijeme ponašao ispravno. Ekran je odgovarao na „koliko znam", a
čitao se kao „koliko mi je ostalo".

## C.2 Brojač — i zašto u `/profile`, a ne u `/modules`

`solved_task_count` je dodan u **`/profile.mastery`**; ukupan broj i dalje nosi
`primary_task_count` iz `/modules`.

🔴 ERRATA #42 je predlagala proširenje **`/modules`**. Odbijeno iz razloga koji taj redak
nije imao: `["modules"]` se na klijentu **ne invalidira ni na jednu predaju**
(`staleTime` 5 min), pa bi brojač ondje pokazivao neriješenim ono što je student upravo
riješio. `["profile"]` se invalidira u `useSubmitAttempt`, dakle osvježi se točno kad se
promijeni. Time je i odgoda iz 2026-07-25 pala — obrazloženje odgode („mastery % već
komunicira napredak") pokazalo se netočnim, v. tablicu u C.1.

Brojač namjerno broji **samo primarne** zadatke, jer klik ide kroz
`select_task_for_concept`, koji također bira samo primarne. Da uključi sporedne, `order_by`
bi pisao „3/18" a klik bi dao prvi od 2 — vratili bismo „brojač kaže jedno, klik da drugo",
dakle kvar koji je ova grana upravo zatvorila.

## C.3 Ikona više ne znači „savladano" nego „nema novog zadatka"

Odluka korisnika. Ikona odgovara na pitanje koje student postavlja **prije** klika.

🔴 **Stanje `mastered` NIJE dirano, i to je bilo nužno.** Isti predikat (`isMastered`)
određuje i `satisfied` u prereq walku i zrcali `rules.pl mastery_threshold`; da mu se
promijeni značenje, klijent bi zaključavao koncepte drukčije nego Prolog, koji je
autoritativan. Zato je izmjena isključivo u prikazu — natpis, postotak, bar, zaključavanje
i „X/Y savladano" po modulu ostaju na znanju.

Posljedica koja je uz odluku izrijekom navedena i prihvaćena: kvačica se sada pojavljuje i
uz „U tijeku · 77 %", dakle uz koncept koji **nije** savladan. Prebacivanje ide samo za
`in_progress` i `mastered`; `not_started` zadržava isprekidani krug (takav koncept ne može
imati riješenih — prvi točan pokušaj stvorio bi mu BKT redak), `locked` i `unavailable`
zadržavaju svoje. Isto pravilo primijenjeno i na Dashboard, inače bi isti simbol u istoj
aplikaciji značio dvije stvari.

## C.4 Tooltip — i a11y ograničenje koje ga je oblikovalo

Postotak je dobio tooltip s objašnjenjem (`radix-ui`, **već u ovisnostima** — nova nije
dodana).

🔴 **Trigger NIJE fokusabilan, i to je ograničen izbor, ne previd.** Postotak je unutar
`<Link>`a koji pokriva cijeli redak; fokusabilan element ondje je ugniježđena interaktivna
kontrola (WCAG 4.1.2) i razbija tab redoslijed. Provjereno u pregledniku da Radix ne
ubacuje `tabindex` (`asChild` nad spanom → `tabindex=null`). Posljedica je da tipkovnica i
čitači ekrana ne dohvaćaju tooltip, pa uz njega ide **`sr-only` inačica istog teksta** —
tooltip nikad nije jedini nositelj informacije.

Podcrtan je **samo** broj: separator „·" i razmaci izvučeni su iz triggera u vanjski span,
koji ostaje jedan flex item da se `gap-1` ne udvostruči. Izmjereno: podcrtani element
sadrži točno `"33 %"`, `textDecorationLine` je `underline` na brojci i `none` na roditelju.

---

# D — Izmjereno

## D.1 Oba kvara, na živom sustavu kroz HTTP

```
1) /next-task na profilu iz nalaza
   prije:  {task_id: null, concept: "join_condition", reason: "exhausted"}
   poslije:{task_id: 15,   concept: "select_basic",   reason: "partial_continuation"}

2) /task-for-concept/inner_join → 44 → (riješi 44) → 45
   nalaz je javljao: „inner_join vodi na 44, riješen, još 3 neriješena"

3) /task-for-concept/join_condition → 404 concept_has_no_tasks
```

Preporuka pada na `select_basic`, što je i pedagoški točno — to je stvarna slaba točka
profila.

## D.2 🔴 p95 `/next-task` — porast pa neto pad

| mjerenje | p95 | p50 | stdev | n |
|---|---|---|---|---|
| **baseline** (prije ijedne izmjene) | 43,8 ms | 40,0 | 2,5 | 40 |
| nakon `recommendable/1`, naivno | **47,2 ms** | 44,0 | 2,5 | 40 |
| nakon uklanjanja ponovljenog upita | **39,2 ms** | 34,6 | 3,1 | 40 |
| nakon per-user invarijante (A.6) | 45,6 ms | 38,8 | 4,4 | 40 |
| ista, **ponovljeno** | **43,5 ms** | 40,2 | 2,5 | 40 |

🔴 Redak 45,6 napuhao je **jedan outlier od 61,3 ms** (max u ponovljenom mjerenju je 44,0,
stdev 2,5 umjesto 4,4). Mjerodavan je ponovljeni: **43,5 ms, jednako baselineu**. Per-user
upit košta 1,43 ms i ne može se poslužiti iz keširanog kataloga (0,00 ms) — to je cijena
ispravne invarijante, plaćena iz dobitka na ponovljenim upitima.

🔴 **Porast od 3,4 ms nije bio šum** — stdev je 2,5 u oba mjerenja. Razlaganje po
koracima pokazalo je da uzrok **nije** injekcija u Prolog (0,39 ms) nego ponovljeni upit:
`_concept_task_stats` vrtio se **tri** puta po pozivu (zatečeno dvaput, guard je bio treći),
a `load_concept_code_map` dvaput.

Kategorizatori sada primaju već izračunat `stats`, `build_mastery_snapshot` prima
`code_map`; oba opcionalna, pa zatečeni pozivi i testovi rade nepromijenjeno. Ishod je
**4,6 ms ispod baselinea**, jer je uz novi upit uklonjen i zatečeni dvostruki.

**Ograda (ista kao 5.1 §B.1):** jedan stroj (WSL2), jedan proces, `n=40`. Svojstvo lokalnog
mjerenja, ne svojstvo sustava.

## D.3 Gateovi

| gate | ishod |
|---|---|
| `pytest` | **781 passed, 1 skipped, 1 failed** — pad je ZATEČEN, v. F |
| `make preflight` | ✅ zelen (80/80 zadataka, smoke kroz pun lanac) |
| `npm run e2e` | ✅ **3 passed** (2 zatečena + novi gate), teardown čist |
| `tsc -b` · `prettier` · `oxlint` | ✅ (oxlint samo zatečeni `only-export-components`) |
| ugovor | `gen:api` + `openapi-snapshot`: `/task-for-concept` dodan, `entry_task_id` uklonjen, `solved_task_count` dodan |

## D.4a Falsifikacija: 200 nasumičnih stanja, i dokaz da hvata

`tests/test_recommender_no_dead_end.py` zove **stvarni** `recommend()` nad stvarnim
Prolog motorom (ne repliku pravila) i tvrdi četiri stvari nad nasumičnim stanjima:
nikad `exhausted` (P1), `no_recommendation` samo kad su svi koncepti sa zadacima
savladani (P2), `repeat_practice` nudi doista riješen zadatak (P3), vraćeni zadatak je
aktivan i primaran za vraćeni koncept (P4). Svako stanje ide u `SAVEPOINT` i rollbacka,
pa u živu `tutor_main` ne ostaje ništa (ERRATA #40).

Default je 200 stanja (**4,2 s**); dubinski prolaz `FALSIFY_TRIALS=1500` — oba čista,
uz dva različita sjemena. Sjeme je fiksno da pad bude reproducibilan.

🔴 **Dokazano namjernim kvarom, i prvi pokušaj je PROMAŠIO** — vrijedi zapisati.
Vraćanje samo slabije definicije kandidata (`concepts_with_tasks`) test **nije** srušilo:
`resolve_task_for_concept` vraća zadatak za ponavljanje umjesto `None`, pa sam maskira
ćorsokak. Dakle protiv drugog oblika postoje **dvije neovisne brane**, a ne jedna.
Vjerna sabotaža tražila je sva tri mjesta (slab skup kandidata + uklonjena rezerva +
`select_task_for_concept` umjesto `resolve_`), i tek tada: **20 povreda u 200 stanja**,
među njima `where_filter` — točno koncept na kojem je korisnik zapeo.

🔴 Test uz to tvrdi da je grana `repeat_practice` **pogođena barem jednom**. Bez toga bi
P3 mogao prolaziti zato što se taj put nikad ne izvrši.

## D.4 Testovi dokazani namjernim kvarom

Po disciplini iz 5.2 §D.2 — test koji nije viđen kako pada ne čuva ništa:

| brana | kako je dokazana |
|---|---|
| poredak `recommendable` ne mijenja preporuku | guard vraćen na prvi cilj → **pada**; vraćeno → prolazi |
| e2e link ide na `/koncept/` | link vraćen na `/task/${entryTaskId}` → **pada** na `href "/task/15"` |

🔴 **Prva verzija obiju brana bila je bezvrijedna i to je uhvaćeno mjerenjem, ne okom:**

- Test prioriteta prolazio je i prije popravka — `self_join` (ALL_30 idx 16) dolazi prije
  `join_condition` (idx 27), pa ga je klauzula 1 zatekla prvog. Prepravljen tako da je
  transverzalni jedini `weak`, a konkurent `partial`.
- Test poretka prolazio je s namjerno vraćenom regresijom — sa svima na 0,10 `prereqs_met`
  vrijedi samo za `select_basic` (jedini korijen), pa je odgovor jedinstven bez obzira na
  poredak. Prepravljen na profil s više kandidata.

---

# E — Odstupanja od plana

| # | plan | izvedeno | zašto |
|---|---|---|---|
| 1 | rubni slučaj traži novo stanje na Task ekranu | nula izmjena ondje | bedž „Riješeno" i `already_solved` put već postoje (B.3) |
| 2 | „p95 nepromijenjen" | p95 **pao** 43,8 → 39,2 | mjerenje je otkrilo zatečeni dvostruki upit; popravljen usput (D.2) |
| 3 | — | dodan `perf` commit | nije bio u planu; izmjereni porast tražio je uzrok, ne objašnjenje |

---

# G — Code review prije mergea

14 nalaza; 12 popravljeno u istom krugu (v. commit poruku). Tri koja vrijedi
izdvojiti jer nisu bila vidljiva iz testova:

**1. Prolog atomi bez navodnika — fail-closed je bio fail-OPEN.**
`assertz(f"recommendable({code})")` s kodom koji nije `snake_case` (npr. `CTE`)
asertira klauzulu s **varijablom** — `recommendable(_)`, činjenicu koja se poklapa sa
svime. Guard bi prestao filtrirati i ćorsokak bi se tiho vratio. Katalog danas nema takav
kod, pa je kvar latentan; dodan je `_atom()` koji navodi i **odbija** sve izvan
`^[a-z][a-zA-Z0-9_]*$`. Isto je vrijedilo za `mastery/3` — zatečeno od Faze 1.

**2. `aria-label` je potiskivao `sr-only` objašnjenje.** Uz tooltip je stavljena `sr-only`
inačica, uz tvrdnju „tooltip nije jedini nositelj". Ta tvrdnja **nije stajala**:
`aria-label` na `<Link>`u zamjenjuje sadržaj potomaka pri računanju pristupačnog imena, pa
čitač ekrana nije dobivao ni `sr-only` tekst ni brojač — i to baš na **klikabilnim**
retcima, gdje informacija najviše treba. Brojač i postotak sada su u samom `aria-label`u, a
objašnjenje stoji **jednom** u zaglavlju stranice umjesto ~30 puta.

**3. Popravak jednog nalaza uveo je regresiju, i ništa je nije uhvatilo.**
Pri ispravljanju netočnog docstringa `select_task_for_concept`a ispala je provjera
`None if repeat else task_id`, čime bi funkcija tiho vraćala **riješen** zadatak onome tko
je zove kao „daj neriješen". Suita je ostala zelena. Dodan je test koji tu semantiku pribija
— pouka je da je funkcija bez produkcijskih pozivatelja bila i bez pokrića.

## Svjesno NIJE popravljeno

- **`(is_primary AND is_active)` maska živi na pet mjesta** (`_concept_task_stats`,
  `_read_modules`, `resolve_task_for_concept`, `concepts_with_available_tasks`,
  `_read_profile`), a brojnik i nazivnik prikazanog omjera dolaze iz dvije **različite**
  kopije. To je N-8 klasa i realan rizik: promjena predikata na jednom mjestu daje
  „3/2 zadataka". Objedinjavanje dira preporučivač i dvije rute, pa je zaseban zadatak.
- **`resolve_task_for_concept` ponavlja `load_concept_code_map` i upit riješenih** koje je
  `concepts_with_available_tasks` upravo izvršio. p95 je izmjeren i **unutar baselinea**
  (43,5 vs 43,8 ms), pa dobitak ne opravdava izmjenu prije mergea.

---

# F — Otvoreno

- 🔴 **ZATEČEN pad: `test_hint_logic.py::test_credit_is_per_user`** (`assert -8 == 5`).
  🔴 **Brojka RASTE sa svakim danom** — kroz rad na ovoj grani išla je −6 → −7 → −8, što
  samo po sebi potvrđuje dijagnozu (v. niže: `_NOW` je fiksiran u prošlosti, pa razmak
  raste s protokom stvarnog vremena).
  **Nije iz ove grane** — provjereno pokretanjem istog testa na `main`u u zasebnom
  worktreeju, gdje pada identično. Dva uzroka zajedno:
  1. `_NOW` je tvrdo kodiran na **2026-08-12**, a `admin` ima stvarne `hint_requests` iz
     13./14. 8. (živi LLM prolaz iz 5.2 §E2). `hint_credit` filtrira samo **donju** granicu
     prozora (`created_at > window_start`), pa retci noviji od `now` ulaze u računicu i
     bucket ode u minus.
  2. test bira „nekog drugog korisnika" s `select(User.id).where(User.id != uid).limit(1)`
     — **bez `ORDER BY`**, dakle proizvoljan redak (mehanizam ERRATE #60).

  Klasa ERRATE #40 (suite čita živu `tutor_main`). Popravak je izvan opsega ove grane;
  kandidat za zasebnu granu s ostalim fixevima prije deploya.

- ~~Docstring `recommender_logic.py:32`~~ → ✅ ispravljeno (`b9d4091`). Zatečeni tekst: Tvrdi da `explain_plan` ima 2 a
  `index_usage` 3 aktivna primary zadatka, i da ih zato subfloor ne hvata. **Izmjereno:
  oba imaju 0 aktivnih** (M6 deaktiviran, nalaz 4.4-0c B4), pa ih subfloor **hvata**.
  Popis `UNSUPPORTED_CONCEPTS` i dalje treba stajati (ako se M6 ikad vrati, count raste
  iznad praga i subfloor ih ispušta), ali navedeni razlog više ne vrijedi.
- ~~`entry_task_id` bez potrošača za navigaciju~~ → ✅ **uklonjen iz ugovora** (`d0f4904`).
  🔴 Ispravak ranije tvrdnje iz ovog dokumenta: polje **nije** bilo bez potrošača — još je
  određivalo **klikabilnost** (`ConceptRow.tsx`, `MasteryHighlights.tsx`). Točna tvrdnja je
  bila „bez potrošača **za navigaciju**". Taj posao je preuzeo `primary_task_count > 0`,
  ekvivalencija koju je zatečena suita već tvrdila.
- Nalazi iz Faze 5 na svojim granama: ERRATA #64 (kvaliteta hinta), #46, #59, N-21,
  zadaci za M6.

🔴 **Za rad:** `rules.pl` je ono što eval mjeri, pa ova grana **mora leći prije snimanja
baselinea**, ne poslije.
