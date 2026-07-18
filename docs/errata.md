# Errata / nalazi — KONSOLIDIRANI POPIS

**Ovo je JEDINI kanonski popis nalaza.** Wrapupi po fazama smiju referencirati brojeve
odavde, ali ih ne dupliciraju (do 4.4-0g popis je živio u `faza-4.3-wrapup.md`, što je
dovelo do visećih referenci: `#14`, `#15` i `#26` bili su citirani u kodu a nisu postojali
u tablici).

**Konvencija:** broj je trajan i **ne reciklira se**. `task_id` se u nalazima NE citira —
koristi se `source_id` (NALAZ #21).

**Legenda statusa:** ✅ zatvoren · 🟡 otvoren · 📌 prihvaćeno kao limitacija/dizajn ·
🔒 politika

| # | Tema | Status | Gdje je riješen / bilješka |
|---|---|---|---|
| ERRATA #8 | `attempts` nema `verdict` kolonu | ✅ **revidiran** | Partial je AKTIVAN, deriviran iz `error_type='row_mismatch'` (4.3c). Kolona i dalje ne postoji — nije ni potrebna |
| flag #3 | `new_badges` je best-effort | 📌 dizajn | Kozmetika u FeedbackPanelu; autoritativno stanje je `/profile`. Trajna karakteristika |
| #7 | `task.module_id` ≠ modul primarnog koncepta (3/83) | 🟡 **otvoren** | Mitigiran u UI (breadcrumb iz primarnog koncepta, 4.3a). Stabilni ključevi: `correlated_subquery_d3_d9c8f988`, `_d4_7101bea2`, `_d5_7948781f`. **Data cleanup = Faza 6** |
| #9 | Test/dev useri ruše leaderboard asserte | ✅ 4.4-0b | Testovi kohortno skopirani (relativni redoslijed + monotoni rankovi + `total >= len(kohorta)`), bez diranja `routes.py` |
| #10 | UI unlock ≠ Recommender unlock | ✅ 4.3 Stage 0 | `primary_task_count` dodan u `/modules` |
| #10b | `primary_task_count` izložen ali NIKAD konzumiran | ✅ 4.4-0e | Polje je od 4.3 stajalo mrtvo → M6 je izgledao otključivo. Uvedeno 5. stanje `unavailable` u `deriveProgress` |
| #11 | `NextTaskResponse` bez naslova zadatka | ✅ odbijen | Dvostruki hop prihvaćen (cachiran) |
| #12 | `/run` rows dict kolabira duplikate stupce s različitim vrijednostima | 🟡 otvoren | UI caveat ugrađen (preporuka `AS` aliasa); pravi fix = contract promjena (rows kao arrayevi) → **Faza 6** |
| #13 | Partial hue 55–60 preblizu accent-warm 70–85 | 📌 mitigiran | Ikona+tekst kanal OBAVEZAN (MASTER §2.2). Trajna korekcija hue→45 = kandidat 4.7 |
| #14 | `earned_at` bedža nije izložen kroz API | 📌 **limitacija** | `/profile.badges` je `list[str]`; datum postoji SAMO u `user_badges`. Galerija (4.4a) prikazuje bedževe **bez datuma** — datum se NE improvizira |
| #15 | `/attempts` nema server-side filtere | 📌 **limitacija** | Povijest (4.4a) namjerno NEMA filter kontrole: client-side filter nad jednom stranicom lagao bi da filtrira cijelu povijest |
| #16 | — | — | **Broj nije korišten** (rezerviran radi kontinuiteta numeracije) |
| #17 | Frontend nema committed e2e suite | 🟡 otvoren | Brojke „N/N" u 4.1–4.3 bile su RUČNE verifikacije (headless Chrome/CDP), ne runner. Formulacije ispravljene u 4.4-0b. **Smoke suite = ulazni gate za eval (4.7)** |
| #18 | BKT `skill_mastery_history` je REKURZIVAN LANAC | ✅ procedura | Brisanje iz SREDINE lanca invalidira sve kasnije točke. Legitimno: (i) brisanje repa ili (ii) potpuni re-run. Kodirano u `scripts/purge_polluted_attempts.py` (default ODBIJA sredinu lanca) |
| #19 | Modul 6 je IZVAN OPSEGA evaluacije | ✅ 4.4-0e/0f | M6 taskovi ulaze `is_active=False` (izvedeno iz `UNSUPPORTED_CONCEPTS` → preživljava re-import). **Opseg evaluacije = M1–M5 + transverzalni M0.** Dopuna 0f: `/task/{id}` vraća 404 za neaktivan task (zadnja zaobilaznica zatvorena) |
| #20 | Task bank nije bio pod verzijom (P0) | ✅ 4.4-0f | `final_dataset.json` (83 zadatka) je sada verzioniran; LLM međukoraci ostaju ignorirani. **Ne regenerirati kroz LLM bez izričite odluke** |
| #21 | `task_id` je nestabilan preko reseeda | ✅ invarijanta | `down -v` resetira SERIAL (npr. #7 taskovi 71–73 → 60–62). **`source_id` je kanonski ključ** — dokumentacija, testovi i sweep izvještaji koriste njega |
| #22 | Bedž `explorer` bio NEDOSTIŽAN | ✅ 4.4-0f | Kriterij je bio hardkodiran `{1..6}`, a M6 je izvan opsega. Sada DINAMIČKI: moduli koji stvarno imaju aktivne zadatke (`BadgeFacts.evaluable_modules`, trenutno {1..5}) |
| #23 | DML evaluacijska rupa (9/83), postojala od Faze 2 | ✅ 4.4-0d | `evaluation.py` hardkodirao `dml=False` → svaki INSERT/UPDATE/DELETE padao na „permission denied". Nikad nije bila pokrivena testom; sada 10 novih testova |
| #24 | `streak_7` traži 7 KALENDARSKIH dana | 📌 **dizajn** | Horizont bedža je dulji od trajanja evaluacijske sesije → **očekivana stopa osvajanja 0 %**. To je svjestan dugoročni retention element, **ne defekt**; tako se i izvještava u analizi gamifikacije. Bedž se NE mijenja |
| #25 | Bedž `join_master` je NEDOSTIŽAN normalnim putem | 🟡 **otvoren — čeka odluku** | `right_join` ima **1 primarni + 0 sekundarnih** aktivnih taskova → (a) `<2` ga čini **subfloor** pa ga Prolog maskira na 0.99 i recommender ga NIKAD ne nudi, (b) 0 sekundarnih pojavljivanja = nema uzgrednih BKT updatea. Simulacija (student točno riješi sve ponuđeno, 38 taskova): `right_join` ostaje na **prioru 0.0500**, `left_join` 0.854 ✓, `inner_join` 0.9999 ✓ → `join_master` = **NE**. `null_ninja` je dostižan (`null_handling` 1.0000 ✓). ⚠️ **ISPRAVAK:** izvještaj i commit poruka Faze 4.4-0f tvrdili su da je `join_master` dostižan („2 točna po konceptu") — taj je račun bio točan izolirano, ali je previdio da `right_join` NIKAD ne biva ponuđen (subfloor maska) niti dobiva uzgredne updateove. Vrijedi ovaj zapis. Opcije u §Odluke |
| #26 | `make dev` nije bio from-scratch sposoban | ✅ 4.4-0g | Nedostajali su import taskova, seed sandboxa i **registracija SPADE agenata** (Prosody volume se briše uz `down -v` → backend lifespan puca). Sve uvedeno u `dev` lanac |
| 🔒 | **Backend je nakon 4.4-0f TVRDO ZAMRZNUT** | 🔒 politika | Do kraja evaluacije svaka izmjena backenda (rute, sheme, agenti, evaluator, BKT, gamifikacija, Prolog) je **eskalacija, ne rutina** — traži izričitu odluku i ponovni `make preflight` + puni `pytest` |

---

## Odluke koje čekaju (NALAZ #25 — `join_master`)

Popravak **nije** napravljen (backend je zamrznut). Opcije s cijenom:

| opcija | zahvat | cijena / rizik |
|---|---|---|
| (i) dokumentirati kao limitaciju | samo tekst | 0 koda. Ali bedž ostaje u galeriji s kriterijem koji se ne može ispuniti — ista klasa problema kao #22 prije popravka. U analizi se izvještava 0 % |
| (ii) eval/demo seed koji ga čini dostižnim | `seed_demo_user` (dopušteno, nije backend) | Popravlja SAMO demo prikaz (dva puta riješi `right_join` task izravno). Stvarni student ga i dalje ne može osvojiti — **kozmetika, ne rješenje** |
| (iii) sniziti subfloor prag `<2` → `<1` | `recommender_logic` | **ESKALACIJA (zamrznuto).** Mijenja ponašanje preporuka globalno, ne samo za `right_join` |
| (iv) dodati 2. `right_join` task | dataset | **ESKALACIJA** — zabranjeno regenerirati/dodavati taskove; k tome mijenja verzionirani artefakt |
| (v) promijeniti pravilo bedža (npr. samo inner+left) | `gamification_logic` + Prolog | **ESKALACIJA (zamrznuto)** |

**Preporuka:** (i) za evaluaciju — dokumentirati kao poznatu limitaciju i izvijestiti 0 %,
identično kao #24. Strukturni uzrok (`right_join` ima jedan jedini zadatak) je stvar
task banka, a on je zamrznut i verzioniran.
