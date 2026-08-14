# Fix pred deployment — wrapup

**Datum:** 2026-08-14 · **Grana:** `fix-pred-deployment` (s `main`a)

Četiri zatečene stavke koje su preostale nakon mergea `fix-koncept-do-zadatka`, plus
preformulacija teksta o sudjelovanju. Nijedna nije uvedena ovom granom.

| commit | sadržaj |
|---|---|
| `0999883` | kredit za hint više ne može u minus — gornja granica prozora |
| `738ea72` | prompt-pravila protiv curenja glasa; payload POVUČEN (v. §B) |
| `3528092` | predaja razlikuje tri ishoda + `hint_requests` pod dokazom + tekst #46 |

**Nula promjena sheme. Nula novih ovisnosti.**

🔴 Grana sadrži i **jedan povučen popravak** (§B). Zapisan je jednako podrobno kao
isporučeni — odluka da se nešto NE isporuči nosi jednako informacije kao isporuka, a ovdje
i više: mjerenje koje ju je izazvalo vrijedi i za svaki idući pokušaj.

---

# A — `hint_credit` je mogao u minus

`test_hint_logic.py::test_credit_is_per_user` bio je **jedini crveni test** u suiti, i
zatečen — potvrđen na `main`u u zasebnom worktreeju tijekom prethodne grane. Dva neovisna
uzroka koja su se poklopila:

**A.1 Nedostajala je gornja granica prozora.** Upit je filtrirao samo
`created_at > window_start`, pa je redak noviji od `now` ulazio u petlju, a
`level += (now - prev) / refill` s **negativnim** razmakom obarao bucket ispod nule.

🔴 **Nije samo test-artefakt.** `now` se uzima **prije** upita, pa istovremeni upis hinta
može leći s `created_at > now` i u produkciji. Parametar `now` znači „stanje u tom
trenutku", a to traži obje granice — popravak je zato ispravak funkcije, ne prilagodba
testu.

**A.2 Test je birao „bilo kojeg drugog korisnika".** `select(User.id).where(User.id != uid).limit(1)`
— **bez `ORDER BY`**, dakle proizvoljan redak (mehanizam ERRATE #60), koji je u živoj
`tutor_main` (ERRATA #40) znao biti `admin` sa stvarnim zapisima. Dobio je vlastitu
fixture.

🔴 **Brojka je rasla s vremenom: −6 → −7 → −8** kroz nekoliko dana rada, jer je `_NOW`
tvrdo kodiran na 2026-08-12 a `admin` ima stvarne zapise iz 13./14. 8. To je usput bio i
najjači dokaz dijagnoze — kvar koji se sam pogoršava ne može biti slučajan poredak redaka.

⇒ **Suita je nakon ovoga prvi put potpuno zelena: 783 passed, 0 failed.**

---

# B — ERRATA #64: pokušaj POVUČEN prije mergea

## B.1 Što je isporučeno

Samo **prompt-pravila**: 7 (ne komentiraj vlastiti postupak — curenje glasa modela, drugi
nalaz iz #64) i 8 (kad nemaš dovoljno podataka, reci što provjeriti umjesto da
pretpostaviš u čemu je greška).

**Payload je nedirnut.** #64 ostaje OTVORENA.

## B.2 🔴 Zašto je popravak payloada povučen

Ideja: za `row_mismatch` slati `expected_order` (stupac + smjer), izveden iz
`expected_result` strogom monotonošću, da model ne mora nagađati. Prošao je sve testove i
na tri živa primjera davao bolje savjete od zatečenog stanja.

**Code review je posumnjao, a mjerenje nad svih 80 aktivnih zadataka potvrdilo:**

| ishod | zadataka |
|---|---|
| poredak detektiran | 40 |
| — slaže se s `ORDER BY` referentnog upita | 28 |
| — 🔴 **PROTURJEČI mu** | **10** |
| — zadatak uopće nema `ORDER BY` | 2 |

Najgori oblik su višestruki ključevi: `ORDER BY prosjecna_ocjena DESC, product_id ASC` —
primarni ključ ima izjednačenja pa nije monoton, sekundarni jest, pa bi se **tiebreaker
proglasio poretkom**. Sužavanje na „točno jedan monoton stupac" ne spašava: **4 od 24** i
dalje proturječe.

Uz to: Python uspoređuje stringove po codepointu, a `expected_result` je poredao PostgreSQL
pod svojom kolacijom — za `['apple', 'Banana']` Python zaključi `desc`, dakle obrnuto.

🔴 **Zašto je to gore od zatečenog stanja, a ne samo „nepotpuno":** netočna tvrdnja išla bi
uz prompt-pravilo „osloni se na dane podatke", pa bi model krivi poredak iznosio
**sigurnije** nego kad nagađa. Ista klasa kvara koju #64 opisuje — samo **sustavna umjesto
povremene**, u ~30 % slučajeva s detektiranim poretkom.

## B.3 Dvije uže varijante, također odbačene nakon živog mjerenja

| stavka | zašto |
|---|---|
| `expected_columns` | model **sortiranu** listu čita kao PROPISANI redoslijed stupaca i savjetuje preslagivanje SELECT-a („stupci su (country, id, name)" — abecedni poredak). Uz to suvišan: `row_mismatch` znači da su stupci točni |
| `expected_row_count` | kad se brojevi razlikuju, `detail` ih **već** nosi; kad se poklapaju („Row 0 differs"), navodi model na temu koja nije problem |

## B.4 Što bi trebalo za pravi popravak

Jedini pouzdan izvor poretka je `ORDER BY` **referentnog upita**, a `hint_payload` ga po
dizajnu ne smije ni spomenuti — čuva to `test_expected_query_is_never_read`. Proširenje tog
opsega je **odluka korisnika**, jer je klauzula dio rješenja. Alternativa bez diranja
guarda: evaluacijska jezgra emitira strukturiran podatak o poretku umjesto stringa
`Row 0 differs`.

## B.4a Što je umjesto toga isporučeno — i zašto svjesno slabo

Odluka korisnika 2026-08-14: pravi popravak čeka Fazu 6, sada ide samo prompt-razina.

Dodano **pravilo 9: nikad ne iznositi pravila o redoslijedu SQL klauzula.** Gađa točno
opaženu štetu — kvar iz #64 nije bio neodređen savjet nego **netočna tvrdnja o sintaksi**
(„prvo `LIMIT`, pa `ORDER BY`"), koju bi student prepisao u upit koji ne parsira.

🔴 **Bez zavaravanja: prompt-pravilo ne jamči ništa**, a upravo je ova grana pokazala da
mock ne vidi kvalitetu savjeta. Odabrano je jer je jedina mjera koja ne košta migraciju na
zamrznutom backendu tjedan prije evala, a pokriva jedini dokumentirani konkretan slučaj.

## B.5 Što je ovaj pokušaj ipak dao

- **18 živih poziva (~$0,02)** i mjerenje nad 80 zadataka koje je pretvorilo #64 iz
  „model ponekad izmišlja" u „znamo točno koji izvor podataka je pouzdan, a koji nije".
- Potvrda da je izvorni netočan SQL bio **jedan opažen slučaj** — nije se reproducirao ni
  u jednom od 18 poziva, ni prije ni poslije.
- 🔴 Potvrda da **kvalitetu savjeta ne čuva nijedan test**: sve tri odbačene varijante
  prošle su punu suitu. Uhvatilo ih je tek čitanje odgovora i mjerenje nad katalogom.

---

# C — Predaja razlikuje TRI ishoda

`fix-62-63-wrapup.md` §F.1 propisao je podjelu i ostavio je Fazi 5.2, koja ju **nije
izvela**. `TaskPage` je granao samo na `status === 504`, pa je `503 coordinator_busy`
padao u poruku *„Veza prema poslužitelju nije uspjela"*.

🔴 Ta poruka je bila **netočna**: veza JE uspjela, poslužitelj je odgovorio, sustav je bio
zauzet — i ponovni pokušaj **odmah** ima smisla, za razliku od isteka gdje čekanje ne
pomaže.

Mapira se po `detail`, ne po statusu (obrazac `lib/hint.ts` iz 5.2): **tri ishoda dijele
dva statusa**. `ApiError` nosi samo `status`, pa se tijelo greške čita u `mutationFn`.

Novi gate `e2e/submit-ishodi.spec.ts` **podmeće** odgovore umjesto da izaziva stvarnu
konkurentnost — tvrdnja je o mapiranju na klijentu, a backend ima vlastite testove
(`test_coordinator_concurrency.py`); nuspojava koja je ovdje korist: nijedan podmetnuti
zahtjev ne dođe do baze, pa teardown ostaje čist.

🔴 **Dokazano namjernim kvarom:** sa `submitFailure` koji uvijek vraća `unknown` test pada
s **točno starom porukom** „Predaja nije uspjela".

---

# C2 — ERRATA #47: weekly ljestvica govorila je neistinu

Sva tri korisniku vidljiva teksta govorila su o **tjednu** („Ovaj tjedan", „u tekućem
tjednu", „Ovaj tjedan još nema osvojenog XP-a"), a backend računa **klizni prozor zadnjih
7 dana**. To su različiti skupovi — u srijedu klizni prozor obuhvaća i prošli četvrtak,
kalendarski ne.

Popravak je copy-only: **„Zadnjih 7 dana"** na sva tri mjesta. Odluka 4.5 da tekst bude
generički **ostaje na snazi** — „zadnjih 7 dana" ne traži nijedan podatak iz odgovora, pa
se granica prozora i dalje ne rekonstruira na klijentu. Slijedi se i pravilo iz
`attempt-stats.ts`: mjera nad prozorom mora nositi svoj prozor u labeli.

🔴 **Sam nalaz #47 ostaje otvoren kao nalaz o dizajnu:** weekly i dalje mjeri svježinu, ne
trud, i ne smije se čitati kao ukupan doprinos. Popravljen je opis, ne mjera.

---

# D — `hint_requests` pod before/after dokazom

Otvoreno iz 5.2 §F. Tablica se čisti kaskadno, ali to je bila **tvrdnja o shemi, ne
mjerenje**. Sada je u `COUNTED_TABLES`: `5 → 5 (+0)`.

---

# E — Tekst o sudjelovanju (ERRATA #46)

Odluka korisnika: procedura brisanja se **ne gradi**. Tekst je dotad obećavao brisanje
podataka na zahtjev, a sustav to ne može isporučiti — `agent_messages_log` nema `user_id`
ni FK na `users`.

🔴 **Ograničenje se IMENUJE, umjesto da se obećanje tiho ukloni.** Sudionik ima pravo znati
zašto. Novi tekst: podaci se brišu **u cijelosti** nakon obrane, a pojedinačno brisanje
tijekom istraživanja **nije moguće jer dio tehničkih zapisa o radu sustava nije vezan uz
korisnički račun**. Kontakt ostaje, bez poziva na zahtjev za brisanje.

Jedna izmjena pokriva **oba** mjesta prikaza (`/register` i Profil). Uz to je u istoj
datoteci zabilježena odluka o #59 — nosilac pristanka trajno ostaje čin registracije.

---

# F — Gateovi

| gate | ishod |
|---|---|
| `pytest` | ✅ **783 passed, 1 skipped, 0 failed** |
| `make preflight` | ✅ zelen |
| `npm run e2e` | ✅ **4 passed** (3 zatečena + novi gate), teardown čist |
| `tsc -b` · `build` · `prettier` · `oxlint` | ✅ |

---

# G — Otvoreno

- 🔴 **ERRATA #64 ostaje OTVORENA** — v. §B.4 za ono što joj treba i zašto je jeftini put
  odbačen.
- **Kvaliteta savjeta i dalje nema automatsku provjeru.** `test_hint_route.py` mocka LLM i
  provjerava mehaniku; sadržaj ne gleda nitko. Zato su dvije stavke iz §B.2 uhvaćene tek
  čitanjem stvarnih odgovora. Ako se to želi zatvoriti, treba zaseban, ručno pokretan
  provjeravač nad živim modelom — ne u `pytest` suiti (potrošnja).
- Dugovi iz prethodne grane: `(is_primary AND is_active)` maska na 5 mjesta;
  `resolve_task_for_concept` ponavlja dva upita.
- Nedirnuto i nepromijenjeno: N-21/#61, #40, #7, #47, #12, #45, zadaci za M6 i
  transverzalne, odluka o `Kbd` čipovima.
