# M6 plan-presence + `column_alias` — zatvaranje grane

**Grana:** `m6-plan-presence` → `main` · **15 commita** (`1e48bbb` … `970abf6`)
**ERRATA:** #66–#79 · **Datum:** 2026-08-18

---

## Što grana rješava

Modul 6 (Optimizacija) bio je **neevaluabilan**: jezgra ocjenjuje po rezultatu, a
anti-pattern u M6 vraća **bajt-identične retke**. Grana uvodi **plan-presence evaluaciju** —
usporedbu izvedbenih planova umjesto pohranjene tvrdnje o planu.

🔴 Usput je mjerenje pokazalo da je pretpostavka TODO-a bila nepotpuna: **od 5 zatečenih M6
zadataka samo je 1 bio zdrav**. Tri su tražila Index Scan a njihov referentni upit daje Seq
Scan (planer je u pravu, zadatak nije), a jedan je imao praznu tvrdnju jer `ORDER BY id
LIMIT 1` uvuče `orders_pkey`. Da je TODO izveden doslovno, isporučio bi tri zadatka koja
padaju na vlastitom rješenju.

## Glavne izmjene

**Evaluacija.** Tvrdnja o planu se **ne pohranjuje** — zadatak je već nosi kroz
`expected_query`. Oba upita se EXPLAIN-aju istovremeno i uspoređuju potpisi
`PlanSignature(uses_index, index_names, join_methods)`. Nula promjena sheme, ne može
zastarjeti, preživljava reseed.

**Tri gatea.** `plan_is_stable` (potpis nepromijenjen pod `enable_seqscan=off` /
`enable_hashjoin=off`), gate diskriminacije pri autorstvu, i novi gate u `sweep` —
*svojstvo imenovano u `description` mora stajati u potpisu referentnog plana*, s pravilom
**po konceptu** i tvrdim pravilom protiv tihog preskakanja.

**`plan_unavailable` više nije ishod pokušaja.** Kad `EXPLAIN` ne uspije, student s
ispravnim upitom dobivao je `is_correct=false`, BKT ažuriranje netočnim ishodom i potrošen
hint kredit. Šteta je egzaktna i najveća usred učenja: **p_l 0.80 → 0.46** umjesto → 0.97.
Sada **503**, bez pokušaja; prijenos ide **performativom** `refuse`, router se ne dira.

**Izvor hinta se bira po određenosti dijagnoze.** LLM se poziva samo kad klasifikacija i
payload **zajedno** određuju dijagnozu; inače deterministički fallback. Izmjereno nad 12
stvarnih hintova: `execution_error` i `timeout` model popunjava iz opisa zadatka i izgovara
kao činjenicu o studentovom upitu (2/2 prolaza svaki), a `explain_submitted` je siguran jer
**ime klase jest dijagnoza**. Katalog dopunjen s 8 tekstova (32 → 40).

**Katalog zadataka.** `index_usage` 3 aktivna, `explain_plan` 2, `column_alias` 3;
`join_condition` ostaje bez zadataka (odluka). Četiri pokvarena M6 zadatka **deaktivirana,
ne obrisana**, uz `deactivation_reason`.

## Gateovi — sva četiri u istom prolazu

| gate | ishod |
|---|---|
| `pytest` | **930 passed, 1 skipped, 0 failed** |
| `make preflight` | ✅ zelen — 88 aktivnih zadataka, 0 nestabilnih planova |
| `npm run e2e` | ✅ **4 passed** |
| `npm run build` | ✅ `built in 3.36s` |

`make backup` valjan; **restore dokazan neovisno** — md5 svih tekstova hintova identičan
izvoru.

## ERRATA unosi nastali u grani

| # | tema | status |
|---|---|---|
| **#66** | zadatak je tvrdio o bazi nešto što baza ne radi; preživjelo tri faze | ✅ zatvoren |
| **#67** | `make backup` nikad nije radio iz čistog klona (nedostajao `+x`) | ✅ popravljen |
| **#68** | `column_alias` ima zadatke koje preporučivač nikad ne nudi (ZPD escape) | 🟡 otvoren |
| **#69** | smetnja sustava zapisivana kao studentova greška (`plan_unavailable`) | ✅ zatvoren |
| **#70** | `task_not_found` istekne umjesto da odgovori; pouka o dokazivanju | 🟡 otvoren |
| **#71** | sustav se ponašao ispravno iz razloga koji nitko nije odlučio | 📌 poučak, zatvoren ugovornim testom |
| **#72** | model halucinira kad klasifikacija ne određuje dijagnozu | ✅ **zatvoren** |
| **#73** | `OrchestrationFSM` se uklanja dvaput; progutan `ValueError` | 🟡 otvoren, dokazano da ne curi |
| **#74** | kvalifikacija tvrdnje o XMPP-u (poruke ne prelaze mrežu) | 📌 nalaz za rad |
| **#75** | nijedan knjižnični zapis ne dolazi u log | 🟡 stavka deploymenta |
| **#76** | tvrdnja o „dva sjemena" nije bila reproducibilna | 🟡 otvoren |
| **#77** | kurikularni redoslijed nije pravilo nego poredak injekcije | 🟡 otvoren |
| **#78** | gate diskriminacije pokriva samo skriptom autorirane zadatke | 🟡 zamijenjen gateom O |
| **#79** | interni engleski niz procurio u tekst savjeta | 🟡 kozmetika |

🔴 **#79 — provjerena Odluka 6 (selektivni B+).** Sumnja da sirova PG poruka nosi studentov
upit modelu **nije se potvrdila**: grana je nedosežna (`evaluate()` izlazi prije
`compare()`; 0/12 namjerno pokvarenih upita ju je pogodilo), a izmjereni payload nosi samo
`sqlstate`. **Odluka 6 nije prekršena.**

## Metodološki rezultati (za rad)

- **Dosežnost se MJERI, u oba smjera** — nova invarijanta iz dva vlastita povučena nalaza
  (#70, #79): kod koji podnosi stanje nije dokaz da stanje nastaje, a kod koji bi procurio
  nije dokaz da curi.
- **Taksonomija greške je ugovor s pet potrošača** — tri od devet nalaza code reviewa bila
  su ista greška: novo ponašanje ugurano u zatečenu kategoriju umjesto novog imena.
- **Gate stabilnosti nastao je iz flaky testa**, ne iz teorije.
- **Dosežnost koncepta se mjeri simulacijom kroz stvarni preporučivač**, ne računa iz brojki.

## Napomene za mergera

- `--no-ff` (squash bi osirotio tagove).
- Nakon mergea slijedi tag `pred-deployment-zeleno`; provjereno da to ime **ne koristi**
  nijedna grana ni postojeći tag.
- Baza nije na kanonskom baselineu jer je aplikacija stvarno korištena 18.8. u 14:27–14:28
  (račun `admin`). Kanonski baseline uspostavlja `prepare_eval_baseline --confirm` prije
  evaluacijske sesije.
