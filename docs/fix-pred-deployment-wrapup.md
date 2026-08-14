# Fix pred deployment — wrapup

**Datum:** 2026-08-14 · **Grana:** `fix-pred-deployment` (s `main`a)

Četiri zatečene stavke koje su preostale nakon mergea `fix-koncept-do-zadatka`, plus
preformulacija teksta o sudjelovanju. Nijedna nije uvedena ovom granom.

| commit | sadržaj |
|---|---|
| `0999883` | kredit za hint više ne može u minus — gornja granica prozora |
| `738ea72` | payload za `row_mismatch` nosi očekivani poredak (ERRATA #64) |
| `3528092` | predaja razlikuje tri ishoda + `hint_requests` pod dokazom + tekst #46 |

**Nula promjena sheme. Nula novih ovisnosti.** 11 datoteka, +526 / −39.

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

# B — ERRATA #64: savjet za `row_mismatch`

## B.1 Što je popravljeno

Payload je za taj tip nosio samo `detail`, a taj string zna biti `Row 0 differs` — interna
dijagnostika bez ijedne činjenice o očekivanom rezultatu. Sada uz njega ide
**`expected_order`** (stupac + smjer), izveden iz `expected_result` **strogom**
monotonošću.

🔴 Stroga monotonost namjerno: kod ponovljenih vrijednosti poredak nije određen tim
stupcem, pa bi tvrdnja „sortirano po X" bila **nagađanje** — a nagađanje je upravo ono što
#64 popravlja.

Privatnosna odluka 5.0 (selektivni B+) ostaje netaknuta: sve se izvodi iz
`expected_result`, bez ijednog znaka studentovog upita.

## B.2 🔴 Dvije stavke uvedene pa ODBAČENE nakon živog mjerenja

Obje su na papiru izgledale korisno. Mock ih ne bi razotkrio — **sadržaj savjeta ne gleda
nijedan test**, i to je i dalje istina.

| stavka | zašto je odbačena |
|---|---|
| `expected_columns` | model **sortiranu** listu čita kao PROPISANI REDOSLIJED stupaca i savjetuje preslagivanje SELECT-a. Izmjereno: „stupci su (country, id, name)" — to je abecedni poredak, ne poredak rezultata. **Ista klasa kvara koju #64 popravlja, samo pomaknuta.** Uz to suvišan: `row_mismatch` po definiciji znači da su stupci točni |
| `expected_row_count` | kad se brojevi razlikuju, `detail` ih **već** nosi („actual=30 vs expected=3"); kad se poklapaju (oblik „Row 0 differs"), broj navodi model da govori o broju redaka — dakle o nečemu što nije problem |

Ostaje jedina činjenica koju `detail` **nikad** ne nosi: očekivani poredak.

## B.3 Što se NE može tvrditi

🔴 **Izvorni kvar se nije reproducirao.** Netočan SQL iz #64 („prvo `LIMIT`, pa
`ORDER BY`") nije se pojavio ni u jednom od **18 živih poziva**, ni prije ni poslije
izmjene. Bio je to jedan opažen slučaj, pa se ne smije tvrditi da ga je popravak
eliminirao — samo da model sada ima činjenicu koja mu je nedostajala, i da je **koristi**
(imenuje točan stupac i smjer: „`category_id` uzlazno", „silazno jer tražite najveće").

Usput opaženo, bez popravka: jedan odgovor sadržavao je zalutali ćirilički token
(„первих"). To je model, ne payload.

**Potrošnja: 18 živih poziva, ~$0,02.**

## B.4 Pravilo o payloadu PREOZNAČENO, ne ublaženo

Modul je propisivao „najviše JEDNO od `error_detail` / `expected_columns` / `sqlstate`".
Sada se razlikuju dvije vrste polja:

- **nosači signala O STUDENTU** (`error_detail`, `sqlstate`) — i dalje **najviše jedan**;
  to je granica iz privatnosne odluke 5.0 i ne pomiče se;
- **strukturni opis OČEKIVANOG rezultata** — izvodi se iz `expected_result`, ne nosi
  nijedan znak studentovog rada, pa ograničenje iz prve skupine na njega ne odgovara.

Zatvoreni skup polja i guard §G2.3 prošireni su novim poljem — **inače bi ga tiho
preskočili**, a polje koje guard ne zna provjeriti jednako je polju bez guarda.

Prompt je dobio pravilo 7 (ne komentiraj vlastiti postupak — curenje glasa iz #64) i
pravilo 8 (osloni se na dane podatke umjesto pogađanja).

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
| `pytest` | ✅ **786 passed, 1 skipped, 0 failed** |
| `make preflight` | ✅ zelen |
| `npm run e2e` | ✅ **4 passed** (3 zatečena + novi gate), teardown čist |
| `tsc -b` · `build` · `prettier` · `oxlint` | ✅ |

---

# G — Otvoreno

- **Kvaliteta savjeta i dalje nema automatsku provjeru.** `test_hint_route.py` mocka LLM i
  provjerava mehaniku; sadržaj ne gleda nitko. Zato su dvije stavke iz §B.2 uhvaćene tek
  čitanjem stvarnih odgovora. Ako se to želi zatvoriti, treba zaseban, ručno pokretan
  provjeravač nad živim modelom — ne u `pytest` suiti (potrošnja).
- Dugovi iz prethodne grane: `(is_primary AND is_active)` maska na 5 mjesta;
  `resolve_task_for_concept` ponavlja dva upita.
- Nedirnuto i nepromijenjeno: N-21/#61, #40, #7, #47, #12, #45, zadaci za M6 i
  transverzalne, odluka o `Kbd` čipovima.
