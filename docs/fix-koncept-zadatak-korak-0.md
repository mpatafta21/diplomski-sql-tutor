# Korak 0 — put „koncept → zadatak" (istraga + plan)

**Datum:** 2026-08-14 · **Grana (predložena):** `fix-koncept-do-zadatka`, s `main`a
**Povod:** dva nalaza sa zajedničkim korijenom, oba zatečena (nije ih uveo Faza 5):

1. preporučivač zapne na transverzalnom konceptu → „Nema novih zadataka" uz 74 neriješena;
2. klik na koncept vodi na već riješen zadatak.

🔴 **Zajednički korijen:** put „koncept → zadatak" postoji na **tri mjesta**, a samo jedno
zna što je student riješio. Popravljati ih odvojeno znači triput riješiti isto.

| mjesto | zna riješeno? | tko troši |
|---|---|---|
| `select_task_for_concept` ([recommender_logic.py:193](../backend/agents/recommender_logic.py#L193)) | **da** (`solved_task_ids`) | `recommend()` |
| `entry_task_id` u `/modules` ([routes.py:645](../backend/app/api/routes.py#L645)) | ne — statičan, bez usera | `/modules` |
| klijentski linkovi | ne — troše `entry_task_id` | `MasteryHighlights.tsx:78`, `ConceptRow.tsx:114` |

---

# A — Zatečeno stanje, izmjereno

## A.1 Kvar 1: jedna vrijednost nosi dvije uloge

`_BLOCK_VALUE = 0.0` ([recommender_logic.py:65](../backend/agents/recommender_logic.py#L65))
postoji da **blokira nizvodne** koncepte: `inner_join` se ne smije otključati dok
`join_condition` nema svoje prereqs. Ali 0,0 je ujedno `weak` (< 0,30) u
[rules.pl:20](../backend/prolog/rules.pl#L20), pa isti broj koncept čini i **kandidatom za
preporuku**. Od jedne vrijednosti traže se dva suprotna ponašanja.

Lanac do ćorsokaka:

```
select_basic 0,8412 (< 0,85)
  → build_mastery_snapshot kor. 4 gleda TRANZITIVNE prereqs → join_condition = 0.0
  → rules.pl prereqs_met gleda samo IZRAVNE (from_clause ✓) → prolazi
  → klauzula 1 (weak + prereqs_met) → pobijedi join_condition
  → transverzalni koncept po dizajnu ima 0 zadataka
  → select_task_for_concept → None → reason="exhausted" → „Nema novih zadataka"
```

🔴 **Tranzitivno-vs-izravno neslaganje je OKIDAČ, ne uzrok.** Poravnanje snapshota na
izravne prereqs učinilo bi `join_condition` 0,99 čim `from_clause` sazrije, pa bi
`inner_join` bio **lažno otključan** — točno ono protiv čega postoji Kat. A
([docstring, l. 15-20](../backend/agents/recommender_logic.py#L15)). Taj put je slijepa
ulica i **ne ide u plan**.

Uvjet ulaska: `from_clause` savladan, `select_basic` < 0,85. `from_clause` saturira brzo
(sekundarni koncept gotovo svakog zadatka) → kroz to stanje realno prolazi svaki sudionik.
**Prijetnja valjanosti evala, ne samo UX.**

## A.2 Popravak provodi pravilo koje kod već propisuje

[recommender_logic.py:240-243](../backend/agents/recommender_logic.py#L240) doslovno kaže:

> „Maskiranje je na razini KONCEPTA, ne taska: filtriranje tek u
> `select_task_for_concept` dalo bi `reason='exhausted'` (task_id=None) = tiši ćorsokak
> umjesto rješenja (4.4-0d KORAK 4)."

Kat. B (subfloor) i Kat. C (neevaluabilni) to poštuju kroz masku 0,99. **Kat. A ga krši**
putem s 0,0 i završi u točno tom `exhausted`-u. Dakle ne izmišljamo pravilo — provodimo
postojeće na kategoriju koja ga je izbjegla.

## A.3 Obrazloženje „`/modules` je cacheable katalog" ne stoji kako je zapisano

| tvrdnja iz komentara | izmjereno |
|---|---|
| „bez user-konteksta" | ruta traži `Depends(get_current_user)` ([routes.py:259](../backend/app/api/routes.py#L259)); `_user` je namjerno neiskorišten |
| „cacheable" | nema nijednog `Cache-Control` headera u `backend/app/`; jedini keš je React Query `staleTime: 5 min` ([useModules.ts:14](../frontend/src/hooks/useModules.ts#L14)) |

🔴 **Odlučujuće:** `["modules"]` se **ne invalidira ni na jednu predaju** —
[useSubmitAttempt.ts:49-56](../frontend/src/hooks/useSubmitAttempt.ts#L49) invalidira
`profile`, `next-task`, `attempts`, `mastery-history`, `task`. User-aware polje u
`/modules` zato bi do 5 minuta nakon rješavanja i dalje nudilo riješen zadatak — **isti
kvar, samo rjeđi i teže uočljiv**. To je razlog zašto opcija „user-aware polje" nije
odabrana, jači od „gubi se cacheability".

## A.4 Presedan za resolver već postoji

`TaskEntryPage` (`/task`) razriješi `/next-task` pa `<Navigate replace>` na `/task/:id`.
Nosi i zamku koju bismo inače otkrili tek u testu:

> „`replace`: entry ruta NE smije ostati u historyju — inače bi Back s task screena opet
> pao ovamo, ponovno razriješio preporuku i vratio na isti zadatak."

Resolver za koncept je **isti obrazac s drugim izvorom**, ne novi mehanizam.

## A.5 Rubni slučaj je gotovo besplatan

Odabrano je „vodi na riješen zadatak uz oznaku". Bedž **već postoji** —
[TaskPage.tsx:449-457](../frontend/src/pages/TaskPage.tsx#L449) renderira „Riješeno" kad
`task.solved`, a komentar uz njega već propisuje odabrano ponašanje: *„Ponovni Submit se i
dalje smije predati (vježba), ali NE nosi XP."* `FeedbackPanel` nakon predaje pokaže „Već
riješeno · bez XP" (`attempt.already_solved`).

⇒ **Nema novog stanja na eval-verificiranom ekranu.** Najviše dopuna natpisa, i to je
zaseban, odvojiv commit.

---

# B — Odluke (korisnik, 2026-08-14)

| # | odluka | posljedica |
|---|---|---|
| 1 | ćorsokak se popravlja **u Prologu**, novim predikatom | `rules.pl` se mijenja — autoritativan izvor ostaje autoritativan; 0,0 zadržava **samo** ulogu blokade |
| 2 | navigacija ide kroz **novu resolver rutu** | `/modules` i `entry_task_id` ostaju netaknuti |
| 3 | svi zadaci riješeni → **vodi na riješen uz oznaku „za ponavljanje, bez XP-a"** | v. A.5 — bedž postoji |

---

# C — Popravak 1: `recommendable/1`

## C.1 Definicija skupa

`recommendable(C)` ⟺ **C ima ≥ 1 aktivan primary zadatak**. Izvor je već postojeći
`_concept_task_stats` (count > 0) — bez novog upita i bez hardkodiranih imena.

🔴 **Ne zamjenjuje maske.** Kat. B (0,99) i Kat. C (0,99) **ostaju kakve jesu**.
`recommendable` je obrana u dubinu za Kat. A, ne nova jedina obrana. Napomena: docstring na
[l. 32](../backend/agents/recommender_logic.py#L32) tvrdi da `explain_plan` ima 2 a
`index_usage` 3 aktivna zadatka, dok mjerenje 2026-08-13 kaže da M6 ima **0 aktivnih**
(5 deaktiviranih). Docstring je vjerojatno zastario — **provjeriti upitom pri
implementaciji**, ne prepisivati brojku.

## C.2 Izmjena `rules.pl`

Uvjet ulazi u **sve četiri** klauzule `recommend_next/2`:

```prolog
recommend_next(User, Concept) :-
    recommendable(Concept),
    weak(User, Concept),
    prereqs_met(User, Concept), !.
```

`explain_recommendation/3` **se ne dira** — poziva se s već vezanim konceptom, pa guard
ondje ne bi ništa filtrirao, a dodao bi drugu definiciju istog pravila (mehanizam N-8).

`prereqs_met`, `mastered`, `all_prereqs` i pragovi ostaju **bajt-identični**. Blokada
nizvodnog teče kroz `mastered/2`, koji ne zna za `recommendable`.

## C.3 Injekcija i čišćenje — predikat NIJE user-scoped

`mastery/3` je po korisniku; `recommendable/1` je **globalan** (izveden iz kataloga,
jednak za sve). Zato:

- `retractall(recommendable(_))` je globalna operacija i **mora biti unutar iste kritične
  sekcije** kao `inject_mastery → recommend_next → clear_mastery`.
- 🔴 **Provjeriti da `prolog_lock` doista omata sav taj slijed** ([3C.2 omotač,
  komentar l. 236](../backend/agents/recommender_logic.py#L236)). Ako ne omata, globalni
  `retractall` bi drugom korisniku maknuo činjenice usred njegova upita — **gori kvar od
  onoga koji popravljamo**. Ovo je prvi implementacijski korak, prije ijedne izmjene.
- Alternativa (injekcija jednom pri bootu) odbačena: katalog se mijenja
  deaktivacijom zadatka, pa bi fakti ostali zastarjeli do restarta.

## C.4 🔴 STANI I JAVI — što kad nijedan koncept ne prođe

Ako nijedan `recommendable` koncept nije preporučiv, `recommend_next/2` **padne** →
`rec is None` → `reason="no_recommendation"`. `TaskEntryPage` to mapira u **slavlje**
(`PartyPopper`, „sve savladano"). To bi bila laž ako transverzalni koncepti ostanu
nesavladani a nevidljivi.

Prije popravka izmjeriti može li se to stanje uopće dogoditi i s kojim profilom. Ako može
— javljam prije nego biram između (a) zadržati `no_recommendation` (tvrdnja „sve što se
može vježbati je savladano" je onda istinita) i (b) uvesti zaseban `reason`.

## C.5 Što se izrijekom NE mijenja

`_BLOCK_VALUE = 0.0`, korak 4 `build_mastery_snapshot`a, `all_prereqs` (tranzitivno),
`_MASK_VALUE`, pragovi u `rules.pl`, `transversal_concepts`, `subfloor_concepts`.

---

# D — Popravak 2: resolver ruta

## D.1 Ugovor

```
GET /task-for-concept/{code}   (auth, kao /modules)
→ 200 { task_id: int, concept: str, repeat: bool }
→ 404 concept_not_found      — nepoznat code
→ 404 concept_has_no_tasks   — koncept nema nijedan aktivan primary zadatak
```

**Bez FIPA lanca, izravan DB read.** Nema Prologa u ovom putu (`select_task_for_concept` je
čist SQL), pa bi bridge dodao round-trip bez ijedne koristi. Presedan: `/modules` je
također izravan `to_thread` read.

## D.2 🔴 Dva različita `None` koja se sada ne razlikuju

`select_task_for_concept` vraća `None` u **dva različita slučaja**, a pozivatelj ih ne može
razlučiti:

| slučaj | što treba | sada |
|---|---|---|
| koncept nema aktivnih primary zadataka | 404, link ionako ne postoji (`primary_task_count === 0` → `clickable === false`) | `None` |
| svi zadaci riješeni | najlakši zadatak + `repeat: true` (odluka 3) | `None` |

Rješenje: nova funkcija `resolve_task_for_concept(session, user_id, code) -> (int|None, bool)`
u `recommender_logic`, a `select_task_for_concept` **delegira na nju** i zadržava svoje
`None`-ponašanje za `recommend()`.

🔴 **Kandidatski upit se NE duplicira.** Dvije implementacije istog pravila su točno
mehanizam N-8; guard za Kat. C (`UNSUPPORTED_CONCEPTS`, l. 203) mora vrijediti na oba puta.

## D.3 Klijent

- nova ruta `/koncept/:code` → komponenta po uzoru na `TaskEntryPage`
  (`LoadingState` → `<Navigate replace>` → `ErrorState` s retryjem);
  🔴 `replace` je obavezan, iz istog razloga koji `TaskEntryPage` dokumentira;
- `MasteryHighlights.tsx:78` i `ConceptRow.tsx:114`: `to={`/task/${entryTaskId}`}` →
  `to={`/koncept/${code}`}`; `aria-label` ostaje nepromijenjen;
- `entry_task_id` u `/modules` **ostaje u ugovoru** — uklanjanje polja je promjena ugovora
  koju ovaj popravak ne treba; nakon prebacivanja linkova ostaje bez potrošača, što se
  bilježi u wrapup kao kandidat za čišćenje.

---

# E — Testovi (TDD, prije koda)

**Prolog / preporučivač**
1. transverzalni koncept s 0,0 **nije** preporučen ni kroz jednu klauzulu;
2. blokada nizvodnog i dalje radi: `join_condition` 0,0 ⇒ `inner_join` nije `prereqs_met`;
3. 🔴 **reprodukcija zatečenog kvara**: `select_basic` 0,8412 + `from_clause` 0,99998 ⇒
   rezultat **nije** `{task_id: None, reason: "exhausted"}`;
4. falsifiabilna kontrola iz nalaza ostaje: `select_basic` 0,90 ⇒ `where_filter`, task 19;
5. Kat. B i Kat. C se i dalje ne preporučuju (maska 0,99 nedirnuta).

**Resolver**
6. koncept s neriješenima → vraća **neriješen**, ne najlakši;
7. svi riješeni → najlakši + `repeat: true`;
8. koncept bez aktivnih zadataka → 404 `concept_has_no_tasks`;
9. nepoznat code → 404 `concept_not_found`;
10. bez sesije → 401 (isti guard kao `/modules`);
11. `UNSUPPORTED_CONCEPTS` → nikad zadatak, ni izravnim pozivom.

**e2e**
12. klik na koncept u Modulima → dolazak na **neriješen** zadatak (regresijski gate za oba
    nalaza odjednom).

---

# F — Exit kriteriji, mjereni

| # | kriterij | kako se mjeri |
|---|---|---|
| 1 | ćorsokak nestao na zatečenom profilu | `/next-task` na računu koji je 2026-08-13 davao `exhausted` → `task_id != null` |
| 2 | blokada nizvodnog netaknuta | test 2 + ručna provjera da `inner_join` ne iskoči novaku |
| 3 | klik na koncept daje neriješen zadatak | e2e 12, na 3 koncepta iz nalaza (`inner_join`, `cross_join`, `insert`) |
| 4 | 🔴 p95 `/next-task` nepromijenjen | **baseline se snima PRIJE izmjene** — retroaktivno se ne može (poučak 5.1 §B.1) |
| 5 | `pytest` zelen, bez regresija | pun `pytest` (zamrznuti backend) |
| 6 | `make preflight` zelen | — |
| 7 | `npm run e2e` + čist teardown | — |
| 8 | ugovor regeneriran | `npm run gen:api` + `make openapi-snapshot` (`indent=2` od 5.2) |

---

# G — Redoslijed commitova

1. `test(fix): reprodukcija ćorsokaka i klika na riješen zadatak` — **pada**
2. `fix(recommender): recommendable/1 — transverzalni koncept nije kandidat`
3. `feat(api): GET /task-for-concept — resolver koji zna što je riješeno`
4. `feat(frontend): linkovi na koncept idu kroz resolver`
5. `docs: wrapup — izmjereno, odstupanja, otvoreno`

Koraci 2 i 3 su neovisni i mogu se recenzirati odvojeno; 4 ovisi o 3.

---

# H — Rizici i ograničenja

- 🔴 **`rules.pl` je ono što rad mjeri.** Izmjena mijenja ponašanje koje eval ocjenjuje →
  **mora leći prije baselinea**, ne poslije. Ovo je razlog zašto je grana prva na redu.
- 🔒 **Backend je zamrznut od 4.4-0f** → svaka izmjena traži pun `pytest` + `preflight`.
- ⚠️ `pytest` piše u živu `tutor_main` (#40) → **ne pokretati tijekom evaluacijske sesije**.
- ✅ **Nema promjene sheme** — nijedna migracija, pa ne traži zasebnu odluku po CLAUDE.md.
- ⚠️ **Novi endpoint je promjena API ugovora** → `schema.d.ts` + `openapi.json` u istom
  commitu kao ruta.
- ⚠️ Dashboard i Moduli su eval-verificirani ekrani — mijenja se **samo `to=`** u dva
  linka, ništa u izgledu; matrice iz 4.7 ostaju važeće.

---

# I — Izvan opsega

`entry_task_id` se **ne uklanja** iz `/modules`; ERRATA #64 (kvaliteta hinta), #46, #59,
N-21, M6 zadaci — sve ostaje na svojim granama.
