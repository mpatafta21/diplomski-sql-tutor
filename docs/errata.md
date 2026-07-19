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
| #20 | Task bank nije bio pod verzijom (P0) | ✅ 4.4-0f | `final_dataset.json` je sada verzioniran (**85 zadataka**: 83 iz LLM batcha + 2 ručno autorska iz 0h; 80 aktivnih, 5 M6 neaktivnih); LLM međukoraci ostaju ignorirani. **Ne regenerirati kroz LLM bez izričite odluke** |
| #21 | `task_id` je nestabilan preko reseeda | ✅ invarijanta | `down -v` resetira SERIAL (npr. #7 taskovi 71–73 → 60–62). **`source_id` je kanonski ključ** — dokumentacija, testovi i sweep izvještaji koriste njega |
| #22 | Bedž `explorer` bio NEDOSTIŽAN | ✅ 4.4-0f | Kriterij je bio hardkodiran `{1..6}`, a M6 je izvan opsega. Sada DINAMIČKI: moduli koji stvarno imaju aktivne zadatke (`BadgeFacts.evaluable_modules`, trenutno {1..5}) |
| #23 | DML evaluacijska rupa (9/83), postojala od Faze 2 | ✅ 4.4-0d | `evaluation.py` hardkodirao `dml=False` → svaki INSERT/UPDATE/DELETE padao na „permission denied". Nikad nije bila pokrivena testom; sada 10 novih testova. ⚠️ **POPRAVAK JE BIO DJELOMIČAN:** vratio je `update` i `delete` (4 taska svaki), ali je `insert` imao samo 1 primarni task pa ga je subfloor maska i dalje činila NEDOSTUPNIM — student INSERT nije mogao vježbati sve do 4.4-0h (vidi #27) |
| #24 | `streak_7` traži 7 KALENDARSKIH dana | 📌 **dizajn** | Horizont bedža je dulji od trajanja evaluacijske sesije → **očekivana stopa osvajanja 0 %**. To je svjestan dugoročni retention element, **ne defekt**; tako se i izvještava u analizi gamifikacije. Bedž se NE mijenja |
| #25 | Bedž `join_master` je NEDOSTIŽAN normalnim putem | ✅ **ZATVOREN u 4.4-0h — PODACIMA, bez izmjene pravila** | `right_join` ima **1 primarni + 0 sekundarnih** aktivnih taskova → (a) `<2` ga čini **subfloor** pa ga Prolog maskira na 0.99 i recommender ga NIKAD ne nudi, (b) 0 sekundarnih pojavljivanja = nema uzgrednih BKT updatea. Simulacija (student točno riješi sve ponuđeno, 38 taskova): `right_join` ostaje na **prioru 0.0500**, `left_join` 0.854 ✓, `inner_join` 0.9999 ✓ → `join_master` = **NE**. `null_ninja` je dostižan (`null_handling` 1.0000 ✓). ⚠️ **ISPRAVAK:** izvještaj i commit poruka Faze 4.4-0f tvrdili su da je `join_master` dostižan („2 točna po konceptu") — taj je račun bio točan izolirano, ali je previdio da `right_join` NIKAD ne biva ponuđen (subfloor maska) niti dobiva uzgredne updateove. **RJEŠENJE (0h):** `right_join` je dobio 2. primarni zadatak → izlazi iz subfloora → recommender ga sada NUDI → simulacija: 0.0500 → **0.8541 ✓**. `join_master` = **DA**, uz NULA promjena Prolog/gamification pravila. Opcije (iii)–(v) iz §Odluke NISU trebale |
| #26 | `make dev` nije bio from-scratch sposoban | ✅ 4.4-0g | Nedostajali su import taskova, seed sandboxa i **registracija SPADE agenata** (Prosody volume se briše uz `down -v` → backend lifespan puca). Sve uvedeno u `dev` lanac |
| **#27** | **Subfloor pravilo tiho ubija koncepte s TOČNO 1 zadatkom** | ✅ **4.4-0h (podacima)** | `subfloor_concepts` maskira svaki koncept (modul ≠ 0) s `<2` aktivna primarna zadatka kao „savladan" (0.99) da ga Prolog ne preporuči. Posljedica: koncept s **točno 1** zadatkom nikad ne biva ponuđen, njegov jedini zadatak se nikad ne servira, i ako nema sekundarnih pojavljivanja BKT mu ostaje na tier prioru — **tiho, bez ijedne greške u logovima**. Zatečeno stanje: `right_join` (1 primarni, 0 sekundarnih) i `insert` (1, 0) — empirijski potvrđeno simulacijom (0 updatea nakon savršenog rješavanja svih ponuđenih zadataka). **Riješeno dodavanjem po jednog ručno autorskog zadatka** (2 primarna → izlaze iz subfloora), bez ijedne izmjene pravila. **OSTAJU kao namjerna limitacija:** `explain_plan`/`index_usage` (M6, #19) i `join_condition`/`column_alias` (modul-0 glue, dizajn) |
| **#28** | DB `concepts.tier` ≠ Prolog tier za 6/30 koncepata | 📌 **PRIHVAĆENO KAO LIMITACIJA** | BKT parametre određuje **Prolog** (`create_bkt_for_concept` → `engine.get_tier`) — on je autoritativan (CLAUDE.md). DB stupac `concepts.tier` divergira za: `insert` (DB medium / Prolog easy), `null_handling` (hard/medium), `cross_join` (medium/hard), `exists_subquery` (hard/medium), `in_subquery` (hard/medium), `scalar_subquery` (hard/medium). Praktična posljedica: **UI tier-chipovi** (iz `/modules`, dakle DB) mogu pokazivati drugu težinu nego što BKT stvarno koristi. **Prolog tier je AUTORITATIVAN za BKT**; `concepts.tier` u DB-u je PRIKAZNI metapodatak. **NE popravljati** — promjena bi mogla imati ripple učinak na unlock logiku (tier ulazi u prior, a prior u prag otključavanja). Kandidat za Fazu 6, uz punu re-verifikaciju. U radu se prijavljuje kao poznata divergencija prikaza i modela |
| **#29** | **Rezultat-bazirana evaluacija ne razlikuje ekvivalentne formulacije** | 📌 **metodološko ograničenje** | Evaluator uspoređuje SKUP REDAKA, ne strukturu upita. Posljedica: zadatak namijenjen jednom KC-u rješiv je drugom tehnikom — npr. `right_join_d2_manual_b87adfc6` daje identičan rezultat s `LEFT JOIN`-om (zamjenom strana), `EXISTS`/`NOT IN` podupitom ili `EXCEPT`-om. Student tada dobiva **BKT kredit za `right_join` bez da ga je upotrijebio** → mjerena „savladanost" koncepta može biti **spuriozna**. Vrijedi SUSTAVNO (svaki KC čiji je rezultat dostižan alternativnom formulacijom), ne samo za ovaj zadatak. Strukturna provjera (parsiranje upita, npr. sqlglot AST) bila bi rješenje, ali je izvan opsega i mijenja evaluator (zamrznut). **Prijavljuje se u radu kao prijetnja valjanosti mjerenja** (konstruktna valjanost BKT procjene po KC-u) |
| **#30** | `RETURNING` u multi-row `INSERT`-u nema zajamčen redoslijed | 📌 **rizik nizak, zabilježen** | SQL standard ne jamči redoslijed redaka koje `RETURNING` vraća; PostgreSQL ih de facto vraća redoslijedom umetanja. Pogađa `insert_d3_manual_d034def1` (2 retka). Rizik je dodatno ublažen time što `runner.compare` bez `ORDER BY` u upitu koristi **set-usporedbu** (redoslijed nebitan). Ako se ikad pojavi flaky ishod na tom zadatku, uzrok je ovdje |
| 🔒 | **Backend je nakon 4.4-0f TVRDO ZAMRZNUT** | 🔒 politika | Do kraja evaluacije svaka izmjena backenda (rute, sheme, agenti, evaluator, BKT, gamifikacija, Prolog) je **eskalacija, ne rutina** — traži izričitu odluku i ponovni `make preflight` + puni `pytest` |

---

## ~~Odluke koje čekaju~~ → RIJEŠENO u 4.4-0h (NALAZ #25 — `join_master`)

**Odabrana je opcija izvan ove liste:** dodan je 2. `right_join` zadatak (ručno autorski, ne LLM),
čime koncept izlazi iz subfloora i postaje dostupan — **bez ijedne izmjene koda ili pravila**.
Opcije ispod ostaju zapisane radi traga odlučivanja:

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
