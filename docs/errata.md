# Errata / nalazi — KONSOLIDIRANI POPIS

**Ovo je JEDINI kanonski popis nalaza.** Wrapupi po fazama smiju referencirati brojeve
odavde, ali ih ne dupliciraju (do 4.4-0g popis je živio u `faza-4.3-wrapup.md`, što je
dovelo do visećih referenci: `#14`, `#15` i `#26` bili su citirani u kodu a nisu postojali
u tablici).

**Konvencija:** broj je trajan i **ne reciklira se**. `task_id` se u nalazima NE citira —
koristi se `source_id` (NALAZ #21).

🔴 **Konvencija o PROSTORU IMENA (uvedena 2026-08-10 nakon sweepa visećih referenci).**
Projekt ima **više neovisnih numeracija** i one se u tekstu razlikuju **samo po riječi
ispred broja**: errata (`#N` / `NALAZ #N`), **invarijante** (`invarijanta #N`, definirane u
`faza-4.1-wrapup.md`), **Fix/Issue** iz Faze 2B (LLM prompt iteracije), **flagovi**
(`flag #N`), **code review runde**, **3D nalazi** i **PR brojevi**. Gol `#N` bez riječi
ispred je zato **dvoznačan** i ne smije se pisati. Uz to: **politike (🔒 retci) NEMAJU
broj** — referencira ih se opisno, nikad izmišljenim brojem. Zatečeni primjer, ispravljen
2026-08-10: redak #41 referencirao je politiku zamrznutog backenda nepostojećim brojem
`#49`, koji nikad nije bio dodijeljen nijednom nalazu.

**Legenda statusa:** ✅ zatvoren · 🟡 otvoren · 📌 prihvaćeno kao limitacija/dizajn ·
🔒 politika

| # | Tema | Status | Gdje je riješen / bilješka |
|---|---|---|---|
| ERRATA #8 | `attempts` nema `verdict` kolonu | ✅ **revidiran** | Partial je AKTIVAN, deriviran iz `error_type='row_mismatch'` (4.3c). Kolona i dalje ne postoji — nije ni potrebna |
| flag #3 | `new_badges` je best-effort | 📌 dizajn | Kozmetika u FeedbackPanelu; autoritativno stanje je `/profile`. Trajna karakteristika |
| #7 | `task.module_id` ≠ modul primarnog koncepta (3/83) | 🟡 **otvoren** | Mitigiran u UI (breadcrumb iz primarnog koncepta, 4.3a). Stabilni ključevi: `correlated_subquery_d3_d9c8f988`, `_d4_7101bea2`, `_d5_7948781f`. **Data cleanup = Faza 6** |
| #9 | Test/dev useri ruše leaderboard asserte | ✅ 4.4-0b | Testovi kohortno skopirani (relativni redoslijed + monotoni rankovi + `total >= len(kohorta)`), bez diranja `routes.py` |
| #10 | UI unlock ≠ Recommender unlock | ✅ 4.3 Stage 0 | `primary_task_count` dodan u `/modules` |
| #10b | `primary_task_count` izložen ali NIKAD konzumiran | ✅ 4.4-0e | Polje je od 4.3 stajalo mrtvo → M6 je izgledao otključivo. Uvedeno 5. stanje `unavailable` u `deriveProgress`. **DOPUNA (2026-08-10, bez novog broja):** ista klasa nađena je u frontendu — `lib/verdict-ui.ts:36,43,50` izvozi polje `soft` (`bg-correct-soft` / `bg-partial-soft` / `bg-incorrect-soft`) koje **nema nijednog potrošača** (citat pretrage: `grep -rn "\.soft\b" frontend/src` isključivši samu definiciju → 0 pogodaka; `AttemptRow.tsx:40` koristi samo `meta.border` i stoji na `card`). Zbog #10b se zna kako to završi: mrtvo polje sugerira mogućnost koja nije izvedena. **Polje se NE briše i NE žica bez odluke** — brisanje dira eval-verificirani mirror, a žičenje bi stavilo verdict-plohe u povijest pokušaja, što je dizajnerska promjena. Kandidat za Fazu 6 |
| #11 | `NextTaskResponse` bez naslova zadatka | ✅ odbijen | Dvostruki hop prihvaćen (cachiran) |
| #12 | `/run` rows dict kolabira duplikate stupce s različitim vrijednostima | 🟡 otvoren | UI caveat ugrađen (preporuka `AS` aliasa); pravi fix = contract promjena (rows kao arrayevi) → **Faza 6** |
| #13 | Partial hue 55–60 preblizu accent-warm 70–85 | 📌 **prihvaćeno kao limitacija (4.7)** | **Zatvoreno VLASTITIM obrazloženjem, neovisno o #33.** Ikona+tekst kanal OBAVEZAN (MASTER §2.2) → boja je pojačanje, ne nosilac informacije. Korekcija hue→45 je izvediva ali se NE izvodi — v. bilješku „#13" u §Bilješke uz nalaze |
| #14 | `earned_at` bedža nije izložen kroz API | 📌 **limitacija** | `/profile.badges` je `list[str]`; datum postoji SAMO u `user_badges`. Galerija (4.4a) prikazuje bedževe **bez datuma** — datum se NE improvizira |
| #15 | `/attempts` nema server-side filtere | 📌 **limitacija** | Povijest (4.4a) namjerno NEMA filter kontrole: client-side filter nad jednom stranicom lagao bi da filtrira cijelu povijest |
| #16 | **P(L) saturira i plato je istina, ne greška** | 📌 **svojstvo modela** | Uz easy parametre (`l0=.30 t=.30 g=.25 s=.08`) P(L) brzo saturira blizu 1.0 i nakon greške se jedva vraća — izmjereno živo na `order_by` (21 prilika): od 12. prilike nadalje serija stoji u rasponu 0.99978–1.00000, a 4 uzastopne greške spuste 1.000 → 0.993. Regresija je time praktički nedetektabilna okom. To je POSLJEDICA IZBORA PARAMETARA, ne greška implementacije (kanonska BKT formula, Corbett & Anderson 1994, ručno verificirana na živim podacima — poklapanje na 3 decimale). **UI to NE SKRIVA:** Y-os krivulja je fiksna `[0,1]` (`Y_DOMAIN`, lib/mastery-history.ts) pa se plato vidi kao plato; auto-scale bi raspon 0.9998–1.0000 razvukao preko cijele visine grafa i lagao o dramatičnom usponu. Broj je do 4.4b stajao neiskorišten (rezerviran); sada je dodijeljen jer ga kod referencira |
| #17 | Frontend nema committed e2e suite | 🟡 otvoren | Brojke „N/N" u 4.1–4.3 bile su RUČNE verifikacije (headless Chrome/CDP), ne runner. Formulacije ispravljene u 4.4-0b. **Smoke suite = ulazni gate za eval (4.7)** |
| #18 | BKT `skill_mastery_history` je REKURZIVAN LANAC | ✅ procedura | Brisanje iz SREDINE lanca invalidira sve kasnije točke. Legitimno: (i) brisanje repa ili (ii) potpuni re-run. Kodirano u `scripts/purge_polluted_attempts.py` (default ODBIJA sredinu lanca) |
| #19 | Modul 6 je IZVAN OPSEGA evaluacije | ✅ 4.4-0e/0f | M6 taskovi ulaze `is_active=False` (izvedeno iz `UNSUPPORTED_CONCEPTS` → preživljava re-import). **Opseg evaluacije = M1–M5 + transverzalni M0.** Dopuna 0f: `/task/{id}` vraća 404 za neaktivan task (zadnja zaobilaznica zatvorena) |
| #20 | Task bank nije bio pod verzijom (P0) | ✅ 4.4-0f | `final_dataset.json` je sada verzioniran (**85 zadataka**: 83 iz LLM batcha + 2 ručno autorska iz 0h; 80 aktivnih, 5 M6 neaktivnih); LLM međukoraci ostaju ignorirani. **Ne regenerirati kroz LLM bez izričite odluke** |
| #21 | `task_id` je nestabilan preko reseeda | ✅ invarijanta | `down -v` resetira SERIAL (npr. #7 taskovi 71–73 → 60–62). **`source_id` je kanonski ključ** — dokumentacija, testovi i sweep izvještaji koriste njega |
| #22 | Bedž `explorer` bio NEDOSTIŽAN | ✅ 4.4-0f | Kriterij je bio hardkodiran `{1..6}`, a M6 je izvan opsega. Sada DINAMIČKI: moduli koji stvarno imaju aktivne zadatke (`BadgeFacts.evaluable_modules`, trenutno {1..5}) |
| #23 | DML evaluacijska rupa (9/83), postojala od Faze 2 | ✅ 4.4-0d | `evaluation.py` hardkodirao `dml=False` → svaki INSERT/UPDATE/DELETE padao na „permission denied". Nikad nije bila pokrivena testom; sada 10 novih testova. ⚠️ **POPRAVAK JE BIO DJELOMIČAN:** vratio je `update` i `delete` (4 taska svaki), ali je `insert` imao samo 1 primarni task pa ga je subfloor maska i dalje činila NEDOSTUPNIM — student INSERT nije mogao vježbati sve do 4.4-0h (vidi #27) |
| #24 | `streak_7` traži 7 KALENDARSKIH dana | 📌 **dizajn — REVIDIRAN 2026-08-09** | Kriterij je nepromijenjen i **opis u izvornom zapisu je bio točan** (`gamification_logic.py:241` + `streak_from_active_dates:186-191`); revidirana je **pretpostavka o dostižnosti**, koja je pala s prelaskom na asinkronu javnu evaluaciju. Izvorna tvrdnja „očekivana stopa osvajanja 0 %" vrijedila je pod modelom nadzirane jednokratne sesije. Bedž se i dalje NE mijenja — v. bilješku „#24" u §Bilješke uz nalaze |
| #25 | Bedž `join_master` je NEDOSTIŽAN normalnim putem | ✅ **ZATVOREN u 4.4-0h — PODACIMA, bez izmjene pravila** | `right_join` ima **1 primarni + 0 sekundarnih** aktivnih taskova → (a) `<2` ga čini **subfloor** pa ga Prolog maskira na 0.99 i recommender ga NIKAD ne nudi, (b) 0 sekundarnih pojavljivanja = nema uzgrednih BKT updatea. Simulacija (student točno riješi sve ponuđeno, 38 taskova): `right_join` ostaje na **prioru 0.0500**, `left_join` 0.854 ✓, `inner_join` 0.9999 ✓ → `join_master` = **NE**. `null_ninja` je dostižan (`null_handling` 1.0000 ✓). ⚠️ **ISPRAVAK:** izvještaj i commit poruka Faze 4.4-0f tvrdili su da je `join_master` dostižan („2 točna po konceptu") — taj je račun bio točan izolirano, ali je previdio da `right_join` NIKAD ne biva ponuđen (subfloor maska) niti dobiva uzgredne updateove. **RJEŠENJE (0h):** `right_join` je dobio 2. primarni zadatak → izlazi iz subfloora → recommender ga sada NUDI → simulacija: 0.0500 → **0.8541 ✓**. `join_master` = **DA**, uz NULA promjena Prolog/gamification pravila. Opcije (iii)–(v) iz §Odluke NISU trebale |
| #26 | `make dev` nije bio from-scratch sposoban | ✅ 4.4-0g | Nedostajali su import taskova, seed sandboxa i **registracija SPADE agenata** (Prosody volume se briše uz `down -v` → backend lifespan puca). Sve uvedeno u `dev` lanac |
| **#27** | **Subfloor pravilo tiho ubija koncepte s TOČNO 1 zadatkom** | ✅ **4.4-0h (podacima)** | `subfloor_concepts` maskira svaki koncept (modul ≠ 0) s `<2` aktivna primarna zadatka kao „savladan" (0.99) da ga Prolog ne preporuči. Posljedica: koncept s **točno 1** zadatkom nikad ne biva ponuđen, njegov jedini zadatak se nikad ne servira, i ako nema sekundarnih pojavljivanja BKT mu ostaje na tier prioru — **tiho, bez ijedne greške u logovima**. Zatečeno stanje: `right_join` (1 primarni, 0 sekundarnih) i `insert` (1, 0) — empirijski potvrđeno simulacijom (0 updatea nakon savršenog rješavanja svih ponuđenih zadataka). **Riješeno dodavanjem po jednog ručno autorskog zadatka** (2 primarna → izlaze iz subfloora), bez ijedne izmjene pravila. **OSTAJU kao namjerna limitacija:** `explain_plan`/`index_usage` (M6, #19) i `join_condition`/`column_alias` (modul-0 glue, dizajn) |
| **#28** | DB `concepts.tier` ≠ Prolog tier za 6/30 koncepata | 📌 **PRIHVAĆENO KAO LIMITACIJA** | BKT parametre određuje **Prolog** (`create_bkt_for_concept` → `engine.get_tier`) — on je autoritativan (CLAUDE.md). DB stupac `concepts.tier` divergira za: `insert` (DB medium / Prolog easy), `null_handling` (hard/medium), `cross_join` (medium/hard), `exists_subquery` (hard/medium), `in_subquery` (hard/medium), `scalar_subquery` (hard/medium). Praktična posljedica: **UI tier-chipovi** (iz `/modules`, dakle DB) mogu pokazivati drugu težinu nego što BKT stvarno koristi. **Prolog tier je AUTORITATIVAN za BKT**; `concepts.tier` u DB-u je PRIKAZNI metapodatak. **NE popravljati** — promjena bi mogla imati ripple učinak na unlock logiku (tier ulazi u prior, a prior u prag otključavanja). Kandidat za Fazu 6, uz punu re-verifikaciju. U radu se prijavljuje kao poznata divergencija prikaza i modela |
| **#29** | **Rezultat-bazirana evaluacija ne razlikuje ekvivalentne formulacije** | 📌 **metodološko ograničenje** | Evaluator uspoređuje SKUP REDAKA, ne strukturu upita. Posljedica: zadatak namijenjen jednom KC-u rješiv je drugom tehnikom — npr. `right_join_d2_manual_b87adfc6` daje identičan rezultat s `LEFT JOIN`-om (zamjenom strana), `EXISTS`/`NOT IN` podupitom ili `EXCEPT`-om. Student tada dobiva **BKT kredit za `right_join` bez da ga je upotrijebio** → mjerena „savladanost" koncepta može biti **spuriozna**. Vrijedi SUSTAVNO (svaki KC čiji je rezultat dostižan alternativnom formulacijom), ne samo za ovaj zadatak. Strukturna provjera (parsiranje upita, npr. sqlglot AST) bila bi rješenje, ali je izvan opsega i mijenja evaluator (zamrznut). **Prijavljuje se u radu kao prijetnja valjanosti mjerenja** (konstruktna valjanost BKT procjene po KC-u) |
| **#30** | `RETURNING` u multi-row `INSERT`-u nema zajamčen redoslijed | 📌 **rizik nizak, zabilježen** | SQL standard ne jamči redoslijed redaka koje `RETURNING` vraća; PostgreSQL ih de facto vraća redoslijedom umetanja. Pogađa `insert_d3_manual_d034def1` (2 retka). Rizik je dodatno ublažen time što `runner.compare` bez `ORDER BY` u upitu koristi **set-usporedbu** (redoslijed nebitan). Ako se ikad pojavi flaky ishod na tom zadatku, uzrok je ovdje |
| **#31** | **Koncept bez PRIMARNIH zadataka svejedno skuplja BKT povijest (sekundarna pojavljivanja)** | ✅ **4.4b** | `primary_task_count === 0` znači „nema vlastitih zadataka", NE „nema podataka". `column_alias` ima 0 primarnih ali **4 aktivna sekundarna** zadatka, a KM radi BKT update i za sekundarne koncepte → student rješavanjem `inner_join_d2_b39dec5d` dobije stvarnu točku (živo potvrđeno: `p_l=0.7284`). Prva verzija 4.4b klasificirala je koncept PRIJE nego je pogledala točke, pa je tu točku tiho odbacila i uz koncept ispisala „nema zasebnu krivulju" — neistina o vlastitim izmjerenim podacima. **Pravilo: IZMJERENI PODATAK NADJAČAVA KATEGORIJU** — ima točaka → ima krivulju, bez obzira na skupinu. Isto vrijedi za interpretaciju u radu: „koncept bez primarnih zadataka" ≠ „koncept bez BKT procjene". Ilustracija razmjera: `order_by` ima 2 primarna zadatka, a 21 točku — 19 ih dolazi iz sekundarnih pojavljivanja |
| **#32** | **Recharts v3 stavlja `tabindex=0` + `role="application"` na svaki graf** | ✅ **4.4b** | Default `accessibilityLayer` je uključen. Uz `aria-hidden` wrapper (mini-grafovi su dekoracija uz tekstualni ekvivalent) to stvara **„crnu rupu fokusa"**: tipkovnica stane na element o kojem čitač ekrana ne kaže ništa. Izmjereno na Profilu: **15 takvih tab-stopova** (78 → 63 nakon popravka). Rješenje: `accessibilityLayer={false}` + `tabIndex={-1}` na mini-grafovima; detaljni graf (nije `aria-hidden`, ima stvarnu vrijednost od keyboard navigacije) sloj ZADRŽAVA. **Provjeriti pri svakom novom Recharts grafu** (4.5 leaderboard/admin) |
| **#33** | **Mastery gradijent: donji stopovi su ispod 3:1, rekalibracija ODBAČENA + mitigacija je bila krivo dokumentirana** | 📌 **limitacija (mjereno)** | **Zatečeno** (vs `card`, ispravno alpha-kompozitirano): `mastery-0` **2.13:1** dark / **1.58:1** light ❌, `mastery-25` **3.41:1** dark ✅ / **2.28:1** light ❌; `mastery-50/75/100` prolaze u obje teme (5.50/8.41/12.26 dark, 3.41/5.07/7.49 light). **Rekalibracija odbačena — matematički nemoguća bez lomljenja skale:** u light temi `mastery-0` i `mastery-25` trebaju L ≤ 0.665, a `mastery-50` je već na L = 0.63 → tri donja stopa morala bi stati u raspon L 0.63–0.665, čime prestaju biti međusobno razlučiva (uvjet „percepcijski kontinuiran gradijent" iz MASTER §2.3 pada). I u dark temi bi `mastery-0` skočio 0.42 → 0.505, na 0.025 od `mastery-25` (0.53) — isti kolaps. **Zaključak: gradijent je skala SALIJENTNOSTI, ne nosilac informacije.** ⚠️ **Uz to ispravljena NETOČNA dokumentacija:** docstring `MasteryBar` tvrdio je da je mitigacija „border-border ≥3:1 u obje teme" — izmjereno je **1.32:1 dark / 1.26:1 light**, dakle ta tvrdnja nikad nije vrijedila. Stvarna (i postojeća) mitigacija je `role="progressbar"` + `aria-valuenow` + **tekstualni postotak uz svaki bar**, odnosno tekstualni P(L) + tablica točaka uz krivulje (4.4b). Nijedna vrijednost tokena nije mijenjana |
| **#34** | **`agent_messages_log` sadrži byte-identične duplikate (3 od 12 po attemptu)** | 📌 **zatečeno, backend zamrznut** | Živo izmjereno nad jednim `correlation_id` tokom: 12 zapisa, od kojih su 3 (`gateway→coordinator request`, `evaluator→knowledge inform`, `evaluator→gamification inform`) **byte-identični** ranijima; uz to `coordinator→evaluator` postoji dvaput s RAZLIČITIM payloadom (jedan bez `submitted_query`). Tok RECEIVE→EVALUATE→UPDATE→RECOMMEND→RESPOND je i dalje potpuno rekonstruktibilan. **Posljedica za 4.5b:** log viewer koji ih prikaže sirovo izgledat će kao da sustav šalje duplo → viewer ih mora **označiti, ne sakriti** (skrivanje bi lagalo o zabilježenom prometu). Volumen: 12 zapisa/attempt → ~7 200 za eval od 600 attempta. Uzrok nije istražen jer je backend zamrznut — kandidat za Fazu 6 |
| **#35** | **ZPD escape — koncepti se „savladaju" prije nego ih sustav ikad počne poučavati** | 📌 **nalaz o dizajnu (za rad)** | Koncepti s visokim udjelom sekundarnih updatea (`order_by` 88,9 %, `select_basic` 90 %, `where_filter` 86,4 % — vidi #31) prijeđu prag ovladanosti **PRIJE nego im Prolog ikad ponudi primarni zadatak**. Emergentno svojstvo spoja dvaju pravila koja su svako za sebe ispravna: (a) BKT ažurira **sve** koncepte zadatka, i (b) Prolog bira koncepte **ispod praga**. Posljedica: KC koji uzgredno raste nikad ne padne u izbor preporučivača → **sistematski nikad izravno poučen, a model ga proglasi savladanim**. Mjereno na demo useru: `order_by` **21 update, 0 primarnih**, završni P(L) = 1.000. **Popravak nije moguć bez izmjene ugovora** — `/mastery-history` ne razlikuje primarno od sekundarnog, pa ni UI ni analiza ne mogu odvojiti „naučeno" od „uzgredno kreditirano" bez novog polja. Prijavljuje se u radu zajedno s #29 (rezultat-bazirana evaluacija) i #31 kao **prijetnja konstruktnoj valjanosti**: mjerimo korelat izloženosti, ne nužno usvojenost |
| **#36** | **`/admin/agent-logs` tiho capira `limit` na 200** | ✅ **prikazano u UI-ju (4.5b)** | Zatraženo `limit=1000` vraća **200** uz `total` koji je veći — bez ijedne poruke o skraćivanju. Pri eval volumenu (12 zapisa/attempt → ~7 200 za 20 studenata × 30 attempta) to znači da „pregled svega" **nije moguć**, pa je filter po `correlation_id` JEDINI upotrebljiv ulaz, a ne pomoćna opcija. Backend je zamrznut → cap se ne mijenja, nego se **izlaže**: viewer uvijek ispisuje „Prikazano N od M zapisa", a kad `total > 200` dodaje „Poslužitelj vraća najviše 200 zapisa po zahtjevu — suzi filtrom ili prelistaj". Prešutjeti cap značilo bi tvrditi da se vidi sve. Vrijedi i za 4.5b i za svaku buduću analizu logova |
| 🔒 **DOC** | **Svaka a11y/kontrast tvrdnja nosi izmjerenu brojku i datum** | 🔒 politika (poučak iz #33) | Docstring `MasteryBar` godinu je dana tvrdio „border ≥3:1" bez ijednog mjerenja — bilo je 1.32:1. Od 4.5a: tvrdnja o kontrastu, touch targetu ili SR ponašanju ide u kod/dokumentaciju **samo uz brojku i datum mjerenja**, ili se ne piše. Isti poučak vrijedi za inventare: tvrdnja „X ne postoji" traži citat pretrage — u 4.5 KORAK 0 tvrdnja „Admin nav stavke NEMA" bila je netočna (postoji, role-gated, `AppShell.tsx:65`) i ispravljena je u 4.5a |
| 🔒 **DOC** | **Tvrdnja o kontrastu bez navedene PLOHE je nepotpuna tvrdnja; iscrpna provjera bez filtra lažnih pozitiva je neupotrebljiva** | 🔒 politika (dopuna, iz #50) | **(a) Ploha.** Uz brojku i datum (politika iz #33) ide i **ploha prema kojoj je mjereno**, i to ona na kojoj element **stvarno stoji** — alpha-kompoziti se kompozitiraju (`bg-muted/40` nad `card`, ne `muted`). Bez toga tvrdnja vrijedi za jedan par, a čita se kao da vrijedi za sve (#50: pet mjerenja u tri faze, svako točno za svoju plohu, a defekt je preživio). **(b) Filtar lažnih pozitiva.** Prvi pokušaj iscrpne matrice išao je **kartezijevim produktom** i dao **40+ lažnih padova** (npr. `text-foreground` na `bg-primary` = 1,21:1 — par koji **ne postoji**, jer za tu plohu služi `primary-foreground`). Provjera koja proizvodi previše lažnih pozitiva praktički je **jednako neupotrebljiva kao ona koje nema** — pravi padovi utope se u šumu. Zato se mjeri **samo stvarno postojeći par**, s oznakom dokaza: **●** ploha i tekst u istom `className`, **○** tekst u podstablu elementa koji nosi plohu. Ista klasa kao #39 (guard netestiran u oba smjera): alat koji nije kalibriran ne štiti, samo umiruje. **Zašto je greška preživjela pet mjerenja:** ranija su išla **po elementu** (točna, ali uska), a iscrpna bi **bez filtra** utopila prave padove u lažnima — trebalo je oboje |
| 🔒 | **Backend je nakon 4.4-0f TVRDO ZAMRZNUT** | 🔒 politika | Do kraja evaluacije svaka izmjena backenda (rute, sheme, agenti, evaluator, BKT, gamifikacija, Prolog) je **eskalacija, ne rutina** — traži izričitu odluku i ponovni `make preflight` + puni `pytest` |
| **#37** | **Evaluacijski podaci su nenadoknadivi, a živjeli su samo u docker volumenu** | ✅ **4.6-eval (procedura)** | Attempti, BKT povijest i XP nastaju **jednom**, tijekom sesije sa stvarnim sudionicima, i ne mogu se rekonstruirati. Do 4.6-eval postojali su isključivo u volumenu `pg_main_data` — jedan `docker compose down -v`, kvar diska ili greška u komandi obrisali bi **cijelu evaluaciju diplomskog rada**, a repo o tome nije imao ni riječi. **Riješeno:** (a) `scripts/backup_eval_data.sh` + `make backup` rade `pg_dump` izvan volumena i **verificiraju restore** (restore u privremenu bazu → usporedba broja redaka po tablici I agregata `Σxp/Σtočnih` → drop); verifikacija je testirana i u negativnom smjeru (dump s uklonjenim `COPY attempts` retcima daje 35 vs 0 → skripta pada). (b) `backups/` u `.gitignore` (dumpovi nose e-mailove i bcrypt hasheve) uz izričitu obvezu kopiranja na **drugi medij** — laptop je jedna točka kvara. (c) `down -v` je **zabranjen tijekom evala**; audit Makefilea potvrđuje da ga nijedan target ne poziva implicitno (`infra-down` je bez `-v`), a jedini koji ga poziva je novi `make dev-reset` uz obveznu upisanu potvrdu `OBRISI SVE`. Puna procedura: `docs/eval-runbook.md` |
| **#38** | **Artefakti rada (slike) bili su izvan verzije** | ✅ **4.6-eval** | Snimke zaslona za rad (FIPA tok, BKT krivulje, profil, moduli, feedback) nastajale su u scratchpadu, koji **nije repozitorij** — ista klasa problema kao #17 (e2e verifikacije), #20 (task bank) i #26 (`make dev`). Nereproducibilno i gubi se. **Riješeno:** `docs/figures/` s 9 snimki (1440×900 @2× ) + `README.md` s provenijencijom, namjenom svake slike u radu i **izmjerenom** provjerom privatnosti (grep 2026-07-20: `email` se renderira samo u `RegisterPage` i kao naziv stupca sintetičke sandbox sheme; `ProfilePage`/`AppShell` ga ne prikazuju) |
| **#39** | **`make dev-reset` guard je odbijao i ISPRAVNU potvrdu (`docker compose exec` jede stdin)** | ✅ **4.6-eval** | Prva verzija targeta ispisivala je stanje baze kroz `docker compose exec -T` **prije** `read -r ans`. `exec -T` i dalje pripaja stdin i **proždere ga**, pa je `read` dobivao prazan string i guard je odbijao brisanje čak i kad je korisnik upisao točno `OBRISI SVE`. Kvar je bio **zatvoren** (odbijao je brisati — sigurna strana), ali je target time bio neupotrebljiv. Popravak: `</dev/null` na svim naredbama koje prethode `read`-u. **Poučak:** guard koji nije testiran u OBA smjera nije guard — testirano je i da kriva potvrda prekida (exit ≠ 0, volumeni netaknuti) i da ispravna prolazi |
| **#40** | **`pytest` piše u ŽIVU `tutor_main` bazu i ostavlja FIPA zapise iza sebe** | 📌 **zatečeno, dokumentirano** | Test suite ne koristi zasebnu bazu — `tests/conftest.py` čita isti `DATABASE_URL`, a `test_coordinator.py` diže **pravi probe-agent** (`gwprobe@localhost`) na živi Prosody. Izmjereno 2026-07-20: puni `pytest` (485) na čistom baselineu ostavio je **87 redaka u `agent_messages_log`** (`gwprobe→coordinator` 8, `coordinator→evaluator` 18, …). Testovi **čiste** svoje usere i attempte (`users`=1, `attempts`=0 poslije), ali `agent_messages_log` **nema `user_id`** pa ga cleanup ne dohvaća — ista slijepa točka kao kod `make smoke` (12 zapisa). **Posljedica za eval:** pokretanje testova tijekom sesije ubacuje lažni promet među stvarni. **Ne popravlja se** (backend/test infra zamrznuti, a rizik je proceduralan): runbook zabranjuje `pytest` tijekom sesije, a baseline se pokreće **poslije** testova, ne prije. **DOPUNA (2026-07-21):** uzrok je strukturan — `agent_messages_log` **nema `user_id`**, pa ga **nijedan automatski cleanup ne pokriva**: ni `smoke_live_attempt.cleanup()` (briše po `user_id`), ni `purge_demo_users` (isto), ni CASCADE s `users` (nema FK). Jedino mjesto koje ga uopće čisti je **eksplicitni `TRUNCATE` u `prepare_eval_baseline.py:435`** (iza `--confirm`, isključiv s `--keep-agent-logs`). Izmjereno nakon punog slijeda `pytest` → `baseline --confirm` → `preflight`: **12 redaka, 1 korelacijski tok, 0 bez `correlation_id`**, uz `attempts`=0 → tok je **ORPHAN**. 🔴 Orphan se računa **po TOKU, ne po retku**: samo **5 od 12** poruka nosi `attempt_id` (`evaluator→knowledge`, `evaluator→gamification`); `gateway→coordinator` i `coordinator→evaluator` prethode stvaranju attempta. 🔴 Uz to, `attempt_id` heuristika **nije pouzdana nakon `dev-reset`** — sekvenca `attempts_id_seq` tada kreće od 1 pa smoke i prvi stvarni attempt dobiju **isti id**, i orphan tok se lažno prikaže kao vezan. (Unutar iste instalacije rizika nema: baseline briše attempte s `DELETE`, ne `TRUNCATE`, pa se sekvenca ne resetira — provjereno, 111 uz 0 redaka.) Postupak: zabilježiti smoke `correlation_id` odmah nakon preflighta i isključiti ga **imenom** — `docs/eval-runbook.md` |
| 🔒 **DOC** | **Destruktivna skripta ima `--dry-run` kao DEFAULT i izlistava plan prije izvršenja** | 🔒 politika (iz #37) | `prepare_eval_baseline.py` briše podatke → default je dry-run, stvarno brisanje traži `--confirm`. Uz to: **nepoznati useri se NIKAD ne brišu nagađanjem.** Student bez sentinel prefiksa (`demo44_`, `rival_`, `test_`, `e2e_`, `smoke_`) mogao bi biti stvarni sudionik prethodne sesije, pa se **prijavljuje i preskače**; za brisanje ga treba imenovati (`--also-user`). Dokazano uživo: račun `S99` (konvencija sudionika) prijavljen je kao nepoznat i **nije obrisan**. Isti princip vrijedi za svaku buduću skriptu koja piše u `tutor_main` |
| **#41** | **Ponovno rješavanje već riješenog zadatka farmalo je XP** | ✅ **4.6-eval (backend escalation, bez migracije)** | Svaki `Submit` stvara novi `Attempt` (novi `attempt_id`, `attempt_number`+1) → `persist_gamification` je dodjeljivao XP po svakom točnom pokušaju; idempotencija je štitila samo od dvostruke obrade **istog** `attempt_id`, ne od re-farmanja. Bonus opada na bazu (attempt 3+ ×1.0) ali baza uvijek teče → beskonačan XP na jednom zadatku. **Popravak: „prvo-rješavanje-nosi-XP" gate** — `prior_correct_solve_exists(user, task, <attempt_number)` (izvedeno iz `attempts`, **bez nove kolone**); ako task ima raniji točan pokušaj → `delta=0`. Streak (aktivni dan), badge idempotencija i level-recompute netaknuti. Izloženo UI-ju: `AttemptResponse.already_solved` + `TaskDetailResponse.solved` (indikator „Riješeno" na Task screenu, Dashboard CTA; FeedbackPanel „Već riješeno · bez XP"). 3 nova TDD gate-testa + 1 `/task.solved` test; ciljani suite-ovi (gamification/coordinator/api/api_read/api_user) zeleni. ⚠️ Ovo je bila **eskalacija zamrznutog backenda** (v. 🔒 redak „Backend je nakon 4.4-0f TVRDO ZAMRZNUT" — politika **nema broj**) uz izričitu odluku korisnika (2026-07-25); po #40 i toj 🔒 politici puni `pytest` + `preflight` ionako idu kroz pred-eval slijed `pytest → baseline --confirm → preflight → backup` |
| **#42** | **Indikator „riješeno" na pregledu Modula** | ✅ **zatvoren 2026-08-14** (`fix-koncept-do-zadatka`) | **Odgoda (2026-07-25) je pala jer se pokazalo da mastery % NE komunicira napredak — to je bila pogrešna pretpostavka ovog retka.** Izmjereno na `admin`u: `select_basic` 99 % uz **1/2** riješena, `from_clause` 99 % uz **1/3**, `where_filter` 77 % uz **3/3**. Postotak je BKT procjena ZNANJA i razilazi se s prijeđenim sadržajem u OBA smjera, pa je koncept s visokim postotkom izgledao gotov, a klik na onaj sa svim riješenim vraćao je već riješen zadatak i djelovao kao kvar. 🔴 **Izvedeno DRUKČIJE nego što ovaj redak predlaže:** `solved_task_count` je dodan u **`/profile.mastery`**, ne u `/modules`. Razlog koji redak nije imao — `["modules"]` se na klijentu **ne invalidira ni na jednu predaju** (`staleTime` 5 min), pa bi ondje brojač pokazivao neriješenim ono što je student upravo riješio; `["profile"]` se invalidira u `useSubmitAttempt`. Ukupan broj i dalje nosi `primary_task_count` iz `/modules` (katalog). Uz brojač: ikona retka prebačena s mastery na **„ima li još novog zadatka"**, a postotak je dobio tooltip s objašnjenjem (raste i od zadataka u kojima je koncept SPOREDAN — BKT ažurira sve koncepte zadatka). Srodno #41, #10b |
| **#44** | **Preporučivač skače među temama (INSERT → INNER JOIN) — breadth-first ZPD, NIJE bug** | 📌 **svojstvo dizajna (za rad), ostavljeno kako je** | Uočeno uživo: student riješi `insert`, klikne „Sljedeći zadatak" i dobije `inner_join` — naizgled nepovezan skok. **Uzrok je ZPD prioritet** (`rules.pl` `recommend_next`, redom: weak → partial → unlock_new → fallback) nad GLOBALNIM skupom koncepata, NE lanac po temi. Konkretno: `insert` (tier easy, prior P(L)=0.30 → **partial**) rješavanjem poraste iznad 0.30 i ostaje partial; `inner_join` (tier medium, prior **0.15 → weak**) ima jedini preduvjet `join_condition` (transverzalni glue → maskiran kao savladan), pa je **weak-ready**. Klauzula 1 (weak) ide PRIJE klauzule 2 (partial) → `inner_join` preskoči „nastavak INSERT-a". Posljedica: nakon jednog točnog rješenja koncept ispadne iz *weak* u *partial* i biva deprioritiziran → sustav **breadth-first** obilazi slabe ready-koncepte umjesto da produbi jedan. **Obranjivo (ZPD je poanta rada); NE mijenja se pred evalom** (izmjena je u Prolog/recommenderu = zamrznuti backend + mijenja adaptivnost koju eval mjeri). Odluka korisnika (2026-07-26): ostaviti, opisati u radu. Srodno: #16 (saturacija P(L)), #35 (ZPD escape) — ista klasa emergentnih svojstava spoja BKT + Prolog |
| **#45** | 🔴 **Deklarirana odvojenost streaka od XP-a poništena je vlastitim mehanizmom — vremenski ovisan XP ulazi u level i global rang** | 📌 **prijetnja valjanosti (za rad), NE popravljati** | **Jezgra nije efekt na usporedivost nego PROTURJEČJE U DIZAJNU.** `gamification_logic.py:43-45` izrijekom tvrdi: *„streak NAMJERNO ne množi XP — XP ostaje čist proxy za učinak-u-učenju (streak se nagrađuje kroz `streak_7` badge). Badge XP (`seed_data.py` `xp_reward`) se u persistenceu STAKUJE u isti `xp_delta` kao attempt XP."* **Druga rečenica opovrgava prvu:** ograda („XP je čist proxy za učinak") i mehanizam kojim se opravdava („nagrađuje se kroz badge") **su isti put**. `streak_7` nosi **30 XP** (`seed_data.py` BADGES), a `gamification_persistence.py:283-294` ih upisuje u `xp_log` (uz `attempt_id=NULL`) **i u `user.xp`** (`:293` `user.xp += xp_reward`), nakon čega `:297` `user.level = level_for_xp(user.xp)` **recomputa level uključivo s njima** (redoslijed je izrijekom komentiran kao bitan). Global ljestvica sortira po `User.xp` (`routes.py:632`) → badge XP ulazi i u **rang**. Uz `level_for_xp = 1 + xp // 100` (`LEVEL_STEP=100`), tih 30 XP je **30 % jednog level koraka** — dovoljno da samo po sebi prebaci granicu levela. **Formula XP-a je čista:** `compute_xp` (`:96-122`) = `round_half_up(base[difficulty] × verdict_factor[verdict] × attempt_bonus[attempt_number])` — tri ulaza, nijedan vremenski; nema dnevnog bonusa ni streak multiplikatora, a Prolog nema **nijedno** XP pravilo (citat pretrage: `grep -rniE "\bxp\b" backend/prolog/` → **0 pogodaka**). Vremenska ovisnost ulazi **isključivo** kroz `streak_7`, i to je jedini takav bedž od pet (v. tablicu u bilješci #24). **POSLJEDICA:** dva sudionika s **identičnim skupom riješenih zadataka** mogu se razlikovati u **XP-u, levelu i global rangu** isključivo po tome je li rad raspoređen na 7 uzastopnih dana ili zbijen. 🔴 **Ovo NIJE posljedica promjene strategije evaluacije** — za razliku od #24, gdje je pala samo pretpostavka o dostižnosti. Tvrdnja iz docstringa je **netočna od trenutka kad je `streak_7` dobio `xp_reward > 0`**, dakle od seeda Faze 1; asinkrona evaluacija ju je samo učinila **vidljivom** (pod jednokratnom nadziranom sesijom bedž nitko nije mogao osvojiti, pa je efekt bio nula i proturječje je spavalo). **NE popravlja se** — gamifikacija je zamrznuta, a izmjena `xp_reward` ili level formule mijenja mjerenje koje eval provodi. U radu se prijavljuje uz #29 (rezultat-bazirana evaluacija), #31 i #35 kao **prijetnja konstruktnoj valjanosti**: XP je deklariran kao mjera učinka u učenju, a dijelom mjeri raspored rada. Pri interpretaciji ljestvice i usporedbi sudionika XP treba čitati **uz badge-strukturu**, ne kao čistu mjeru uspješnosti. **Ispravak samog docstringa ODGOĐEN (odluka 2026-08-10, kandidat za Fazu 6).** Diff je pripremljen (`docs/faza-4.7-errata-prijedlog.md`, PRIJEDLOG 5) i mijenja **isključivo komentar**, nula izvršnog koda — ali `gamification_logic.py` je backend, pa po 🔒 politici zamrznutog backenda i najmanja izmjena traži **pun `pytest` + `preflight`**, a `pytest` piše u živu `tutor_main` i ostavlja FIPA promet koji nijedan cleanup ne dohvaća (#40). **Cijena tog ciklusa nadmašuje korist**, jer ovaj redak errate već nosi istinu — netočna tvrdnja je zabilježena ondje gdje se nalazi traže. Docstring ostaje netočan do Faze 6, svjesno i zapisano. Srodno #24 (kriterij bedža), #47 (weekly prozor), #9 (kohortna izolacija) |
| **#47** | **Weekly ljestvica mjeri SVJEŽINU, ne trud — klizni prozor + opis koji imenuje drugu vrstu prozora** | ✅ **opis popravljen 2026-08-14** (`fix-pred-deployment`): „Ovaj tjedan" → **„Zadnjih 7 dana"** na sva tri mjesta (label, opis, prazno stanje). 📌 **Sam nalaz o dizajnu OSTAJE** — mjera je i dalje klizni prozor i ne smije se čitati kao ukupan trud; za usporedbu sudionika koristiti global scope | **Mehanizam:** `_read_leaderboard_weekly` (`routes.py:648-660`) računa score kao `SUM(xp_log.delta)` uz `cutoff = datetime.now(Europe/Zagreb) - timedelta(days=7)`, a docstring izrijekom navodi *„Useri bez ijednog `xp_log` reda u prozoru se NE prikazuju"*. Prozor je **klizan prema trenutku GLEDANJA**, ne prema početku sudionika. **Posljedica:** sudionik koji je odradio studiju i završio prije 10 dana **nestaje s weekly ljestvice bez ijedne promjene u vlastitim podacima** — njegov XP, level i global rang su netaknuti, ali ga weekly više ne broji ni u `total`. Pod jednokratnom nadziranom sesijom efekt nije postojao: svi su radili unutar istog prozora pa je **weekly ≡ global**. 🔴 **Uz to, opis u UI-ju imenuje DRUGU VRSTU PROZORA.** Sve tri korisniku vidljive niske govore o *tjednu*: `LeaderboardPage.tsx:53` label **„Ovaj tjedan"**, `:52` opis **„Osvojeni XP u tekućem tjednu (Europe/Zagreb)."**, `:133` prazno stanje **„Ovaj tjedan još nema osvojenog XP-a"**. „Tekući tjedan" se čita kao **kalendarski tjedan** (pon–ned), a implementacija je **klizni prozor zadnjih 7 dana** — to su različiti skupovi (u srijedu klizni prozor obuhvaća i prošli četvrtak, kalendarski ne). Jedino točno formuliran opis („zadnjih 7 dana") živi u **komentaru koda** (`LeaderboardPage.tsx:15`), dakle nevidljiv korisniku; citat pretrage: `grep -rniE "7 dana\|sedam dana"` u `frontend/src` daje samo taj komentar i nepovezane pogotke u `StatsSummary`/`attempt-stats`. **Odluka 4.5 da tekst bude generički bila je ISPRAVNA** i ostaje: envelope nema `window_start`, a klijentski izračunata granica mogla bi promašiti backend definiciju za sat ili dan (invarijanta „backend konstante se ne rekonstruiraju na klijentu"). **Problem nije genericnost nego imenovanje pogrešne vrste prozora** — „zadnjih 7 dana" je jednako generično, ne traži nijedan podatak iz odgovora, i točno je. **Nedosljednost unutar projekta:** `attempt-stats.ts:4-6` i `StatsSummary.tsx:2-5` uspostavljaju pravilo *„LABELIRANJE OBAVEZNO: 'zadnjih N pokušaja', nikad gol 'Accuracy'"* — dakle mjera nad prozorom MORA nositi svoj prozor u labeli. Weekly ljestvica je ista klasa mjere i to pravilo **ne slijedi**. **Popravak je copy-only i frontend-only** (tri niske u `LeaderboardPage.tsx`), ali dira eval-verificirani ekran → **nije izveden bez izričite odluke**. U radu: weekly ljestvica se pod asinkronom evaluacijom **ne smije čitati kao mjera ukupnog truda** — ona mjeri aktivnost u kliznom prozoru; za usporedbu sudionika koristiti global scope. Srodno #45 (vremenski ovisan XP), #15 (mjera nad prozorom bez server-side filtera) |
| **#48** | 🟡 **Stanje „odabrano" na `ConceptCurveCard` kršilo je 1.4.11 (AA) neovisno o fokusu** | ✅ **zatvoreno u 4.7-4c (posljedica korekcije `--ring`)** | `ConceptCurveCard.tsx:61` renderira odabranu karticu kao `selected ? "border-ring bg-muted/40" : "border-border"`. `border-ring` je time **indikator stanja**, ne fokusa: vidljiv je trajno, i kad fokus nije na kartici. SC 1.4.11 Non-text Contrast (AA, WCAG 2.1) pokriva „vizualne informacije potrebne za identifikaciju komponenata **i njihovih stanja**" → traži ≥3:1 prema susjednoj boji. **Izmjereno 2026-08-10:** `--ring` vs `bg-muted/40` nad `card` = **2,51:1 light** ❌ (dark 3,79 ✅). **Zatvoreno korekcijom `--ring` 0.708 → 0.556 u 4c → 4,57:1 ✅.** 🔴 **Zapisano SAMOSTALNO iako ga popravlja tuđa promjena:** bez vlastitog broja nalaz bi tiho nestao i vratio se neprimijećen ako se token ikad vrati na svjetliju vrijednost ili ako `ConceptCurveCard` dobije vlastitu boju. ⚠️ **Bilješka o hijerarhiji:** token **ne razdvaja** „odabrano" od „fokusirano" — oba vuku `--ring`, pa su nakon korekcije na 4,57 odnosno 4,73:1, praktički jednako teški (zatečeno je bilo 2,51 vs 2,59 — jednako blisko). Odnos se **ne mijenja**, oba se dižu. Hijerarhija „fokus > odabir" tražila bi **vlastiti token** za `ConceptCurveCard` — dizajnerska odluka za Fazu 6. Srodno: #50, #33 |
| ~~#49~~ | — | 🚫 **BROJ SE NE DODJELJUJE** | Broj `#49` pojavljivao se u tekstu #41 kao referenca na **politiku zamrznutog backenda**, koja **nema broj** (🔒 retci nisu numerirani). Referenca je ispravljena 2026-08-10, ali se broj **trajno umirovljuje** da se ne dogodi da netko kasnije naiđe na stari commit ili wrapup s „#49" i poveže ga s pogrešnim nalazom. Sljedeći slobodan broj je **#50**. V. konvenciju o prostoru imena u zaglavlju |
| **#50** | 🔴 **Kontrast se kroz cijeli projekt mjerio vs `card`, a dio elemenata renderira na `-soft` i drugim alpha-plohama — nenavedena ploha je bila kvar, ne brojke** | ✅ **zatvoreno u 4.7-4c (tokeni) + 🔒 politika** | **Uzorak, ne incident.** Otkriveno u tri kruga: (1) #13 — `text-partial` objavljen kao 5,50 vs `card`, a renderira se na `bg-partial-soft` gdje je 4,86; (2) revizija FeedbackPanela — `muted-foreground` **4,18–4,26** i `accent-warm-text` **4,22–4,30** na `-soft` plohama, oboje ispod AA, dok su vs `card` prolazili (4,73 / 4,78); (3) inventar `-soft` potrošača — 🔴 **ispravak razmjera:** raniji zapis „svih sedam pogođenih elemenata je u FeedbackPanelu" bio je **NETOČAN**. `bg-incorrect-soft` nosi i **`ErrorState.tsx:28`**, dijeljeni primitiv koji se renderira na **svakom ekranu** (20 upotreba u 12 datoteka: Task ×4, ErrorBoundary ×3, Profil ×2, Dashboard ×2, Admin ×2, TaskEntry, Moduli, Ljestvica, RunResultPanel, MasteryCurves, AttemptHistory, ContinueCard) — pa je pogođena **poruka svake greške u aplikaciji**, plus `RunResultPanel:130` i blokovi grešaka na `/login` i `/register`. **Uzrok nije token nego ploha:** `-soft` plohe su ~10 % tamnije od `card`, a oba tokena prolazila su na `card` s tankom rezervom. **Svaka pojedina ranija tvrdnja bila je TOČNA za plohu koju je mjerila** — kvar je bio u tome što ploha nije bila navedena, pa se tvrdnja čitala šire nego što vrijedi (npr. `MASTER.md:46` „amber tekst NA pozadini ≥4.5:1 ✓" bez imenovane pozadine). **Zatvoreno u 4c:** `--muted-foreground` 0.556 → **0.528**, `--accent-warm-text` 0.56 → **0.514** (light); puna matrica 23 plohe × 7 tekst tokena, obje teme, **0 padova** — `docs/faza-4.7-kontrast-matrica.md`. **Uz to dopunjena 🔒 DOC politika** (v. redak niže). Srodno #13, #33, #51 |
| **#51** | 📌 **Gamifikacijske površine su najslabiji a11y teren u aplikaciji — strukturno, ne slučajno** | 📌 **nalaz o dizajnu (za rad); tekst popravljen u 4c, plohe ostaju** | Sva tri pada izvan `-soft` bila su **gamifikacijski čipovi**: `BadgeGallery.tsx:73,97` (`muted-foreground` na `bg-muted` = 4,34), `:96` (`accent-warm-text` na `bg-accent-warm/20` = **3,89**, tekst od **10,4 px** — najmanji u aplikaciji) i `BadgeStrip.tsx:47` (4,32). Uz #48 (`ConceptCurveCard` „odabrano" 2,51) i #50 (XP čip, streak, level-up, badge čip u FeedbackPanelu) obrazac je **sustavan**. **Strukturni uzrok:** par `earned`/`unearned` traži **dvije plohe niskog kontrasta** da bi razlika djelovala suptilno → tekst pada na obje. Tokeni su AA-verificirani u 4.1b vs **pune** plohe; bedževi su **jedini potrošači alpha-kompozitiranih ploha** i nastali su u 4.4a, dvije faze kasnije, **bez ponovljenog mjerenja**. **Izmjereno 2026-08-10:** same plohe `accent-warm/5,10,20` vs `card` daju **1,05–1,52:1** u obje teme, dakle **daleko ispod 3:1** — ali **nisu nosilac informacije**: stanje nose **ikona + tekst** (`Check`/`Lock` + „Osvojeno"/„Zaključano", `BadgeGallery.tsx:100-110`; `CircleUserRound` + `font-semibold` + `aria-current` u `LeaderboardTable.tsx:57-79`), pa je tint **ukras**, isto rezoniranje kao #33. Razlučivost čipova nakon 4c: ΔE(Oklab) **0,121** (zatečeno 0,120) — nositelj je **chroma**, ne svjetlina, pa potamnjenje teksta razliku **ne dira**. **Formulacija za rad:** nagradne površine su **dizajnirane da budu suptilne**, a suptilnost je u izravnom sukobu s kontrastnim zahtjevom — to je **tenzija dizajna gamifikacije**, ne previd implementacije. Srodno #48, #50, #33 |
| **#46** | 🔴 **Brisanje POJEDINOG sudionika nije dokazano izvedivo, a obećanje o njemu trajno stoji na Profilu** | 📌 **ODLUKA 2026-08-14: procedura se NEĆE graditi** (v. „Odluke o nerješavanju" na dnu) | Informacija o sudjelovanju (4.7-1a) obećava „za zahtjev za brisanje podataka: <kontakt>" i „podaci se čuvaju do obrane rada, nakon čega se brišu". Od 4.7-1a-dopune taj tekst je i na **Profilu** (`ParticipationSection`), dakle stoji **trajno pred svakim prijavljenim korisnikom**, ne jednokratno prije registracije — zato je rok „prije slanja linka", a ne „prije deploya". **Mehanizam:** `agent_messages_log` **nema `user_id`** (`models.py:394-409` — 7 stupaca, nijedan ne referencira korisnika, nema FK na `users` pa ni CASCADE ne pomaže), a njegov `content` JSONB nosi `submitted_query` studenta (4.5b README to navodi kao osobni podatak). **Nijedan cleanup ga ne dohvaća po korisniku:** `purge_demo_users.py:61-75` pokriva 9 tablica (3 eksplicitno + 5 CASCADE + `users`) i te tablice **nema među njima jer nema po čemu filtrirati**; jedino mjesto koje je uopće briše je `TRUNCATE TABLE agent_messages_log RESTART IDENTITY` u `prepare_eval_baseline.py:435` — **sve ili ništa**, iza `--confirm`. **IZMJERENO 2026-07-26** (brojači prije i poslije, `seed_demo_user` → 27 attempta kroz pravi `POST /attempt` → `purge_demo_users`): `users` 1→1, `attempts` 12→12, `skill_mastery_history` 22→22 (sve točno na baseline ✅), a `agent_messages_log` **363→696 = +333 zapisa koje ništa ne može obrisati po korisniku**. To je **12,3 zapisa po attemptu**, što se poklapa s izmjerenih 12/attempt iz #34. **Ekstrapolacija na eval volumen:** 20 sudionika × 30 attempta = 600 attempta → **~7 400 zapisa** s upitima sudionika, bez ijednog puta do brisanja po osobi (isti red veličine kao procjena ~7 200 u #34). **Moguć put bez izmjene sheme:** prikupiti `correlation_id`-eve iz `attempts` tog korisnika PRIJE brisanja attempta, pa obrisati logove po tom skupu — ali to **ne pokriva poruke bez `correlation_id`** ni one koje prethode stvaranju attempta (#40: samo 5 od 12 poruka po attemptu nosi `attempt_id`), i mora biti **verificirano u OBA smjera** (poučak iz #39). **Odluka je korisnikova:** (a) izgraditi i verificirati proceduru prije slanja linka, ili (b) preformulirati odlomak da ne obećava više od dokazano izvedivog. 🔴 **ODLUKA 2026-08-14: (a) se NE radi, (b) JE IZVEDEN** (grana `fix-pred-deployment`). Tekst više ne poziva na zahtjev za brisanje, a odlomak o čuvanju sada IMENUJE ograničenje umjesto da obećanje tiho nestane: podaci se brišu u cijelosti nakon obrane, a pojedinačno brisanje tijekom istraživanja nije moguće jer dio tehničkih zapisa nije vezan uz korisnički račun. Jedna izmjena pokriva `/register` i Profil. Srodno: #37, #40, #34 |
| **#43** | **Koncept-retci u Module overviewu nisu bili klikabilni (nije bilo puta koncept→zadatak)** | ✅ **4.6-eval (backend escalation, bez migracije)** | UI je imao koncepte ali nijedan endpoint nije mapirao koncept → `task_id` (task se dohvaća samo po ID-u; `/modules` nije nosio ID-eve). **Popravak:** `/modules` ConceptNode dobio `entry_task_id` — reprezentativan AKTIVAN primary zadatak (najlakši prvi: `difficulty ↑, id ↑`), **statički** (bez user-konteksta → `/modules` ostaje čist katalog, cacheable). `entry_task_id != null` ⟺ `primary_task_count > 0` (ista maska). Frontend: ConceptRow je `<Link>` na `/task/<id>` kad je klikabilan = **`entryTaskId != null && state !== "locked"`** — zaključani (nezadovoljeni preduvjeti) i glue/izvan-opsega (0 zadataka) ostaju neklikabilni, savladani su klikabilni za vježbu (bez XP-a, #41). „Koji zadatak": najlakši primary; **NE** „sljedeći neriješen" (to bi tražilo user-aware `/modules`) — kandidat za dogradnju. 1 novi test (`entry_task_id` == DB ground truth + invarijanta). ⚠️ eskalacija zamrznutog backenda (kao #41) |
| **#66** | 🔴 **Tri M6 zadatka tvrdila su o bazi neistinu, a četvrti nije razlikovao ništa — preživjelo jer se mjerila samo usporedba redaka** | ✅ **zatvoren 2026-08-14** (`m6-plan-presence`) | Grana je otvorena da M6 dobije zadatke, a mjerenje je srušilo pretpostavku na kojoj je stajala. **(a)** Rezultatska evaluacija M6 ne može ocijeniti: anti-pattern (`LOWER(email) = …`, `customer_id::text = …`) vraća **bajt-identične retke**. **(b)** 🔴 Gore: referentni upiti zadataka **79, 80, 82** daju **Seq Scan** iako im opis tvrdi Index Scan — sva tri gađaju `customers` (200 redaka), gdje je Seq Scan (5.50) stvarno jeftiniji od Index Scana (8.16). Planer je u pravu, zadatak nije. **(c)** Zadatak **83** ima stabilan plan ali **praznu tvrdnju**: `ORDER BY id LIMIT 1` uvuče `orders_pkey` u plan, pa i referentni i CAST anti-pattern daju `Index Scan / orders_pkey` — identičan potpis, dakle prolazi ono što zadatak zabranjuje. Od 5 zatečenih M6 zadataka **zdrav je bio samo 81**. **Popravak:** plan-presence evaluacija koja EXPLAIN-a **oba** upita u istom trenutku i uspoređuje `PlanSignature(uses_index, index_names, join_methods)`; tvrdnja o planu nigdje se ne pohranjuje jer je zadatak već nosi — to je njegov `expected_query` (nema migracije, ne može zastarjeti, preživljava reseed). Uz to **dva gatea**: `plan_is_stable` (potpis nepromijenjen pod `enable_seqscan=off` i `enable_hashjoin=off`) i gate diskriminacije pri autorstvu (anti-pattern mora dati iste retke a drugi potpis). 🔴 **Gate stabilnosti nije izveden iz teorije nego iz FLAKY TESTA:** tvrdnja o zadatku 79 prošla je izolirano a pala u punoj datoteci, jer mrtvi redci iz rollbackanog DML-a drugog testa podignu `relpages` i prevrnu izbor plana. Posljedice: Kat. C maska u recommenderu **uklonjena** (bila obrana, postala bi blokada), subfloor je time **prazan**, `is_active` je sada **eksplicitan po zadatku** (ne izveden iz koncepta) uz `deactivation_reason`. Katalog: `index_usage` 3 aktivna, `explain_plan` 2, oba +2 trajno deaktivirana (ne brišu se — dokaz nalaza i negativan primjer gatea). Srodno #29 (rezultatska evaluacija), #19, #27, #57 |
| **#68** | 🟡 **`column_alias` je dobio zadatke koje preporučivač nikad ne nudi** | 📌 **nalaz o dizajnu (za rad); ne popravlja se** | Odlukom korisnika (2026-08-14) dobio je 3 ručno autorska zadatka i time ispao iz Kat. A. Simulacija savršenog studenta: p_l dosegne **0.9356 — iznad praga 0.85 — a koncept nije ponuđen NIJEDNOM**. Uzrok: 4 sekundarna pojavljivanja saturiraju BKT prije nego koncept dođe na red, a Prolog bira samo koncepte **ispod** praga. **ERRATA #35 (ZPD escape) po drugi put**, sada potvrđena prospektivno. Strah iz plana (da će zapeti ISPOD praga i zaključati `group_by`) **nije se ostvario** — `group_by` je uredno otključan (0.99999). Zadaci nisu mrtvi: dosežni su klikom na koncept (`resolve_task_for_concept`, put iz #42/#43), ali ne kroz „Sljedeći zadatak"; razlika je zaključana testom. Popravak bi tražio da BKT razlikuje primarna od sekundarnih ažuriranja = izmjena ugovora `/mastery-history`, isto što #35 navodi kao nemoguće bez novog polja. **Za rad:** dodavanje zadataka konceptu s puno sekundarnih pojavljivanja NE čini ga podučavanim. Srodno #35, #31, #66 |
| **#69** | 🔴 **`plan_unavailable` je smetnju sustava zapisivao kao studentovu grešku — naslijeđeno od `unsupported_eval`, vidljivo tek premještanjem pod novo ime** | ✅ **zatvoren 2026-08-14** (`m6-plan-presence`) | Kad `EXPLAIN` ne uspije, student koji je predao **objektivno ispravan** upit dobivao je `is_correct=false`. Izmjereno kroz pun agentski lanac uz **stvarni** pad EXPLAIN-a (referentni upit gađa nepostojeću tablicu, bez ijednog mocka): nastao je `attempts` redak, BKT je ažuriran **netočnim** ishodom, i **potrošen je hint kredit** (`hint_requests.source='llm'`). Šteta po BKT-u je egzaktna, ne procjena — zabilježeni `p_l` do zadnje znamenke odgovara `update(is_correct=False)`: **0.05→0.1078** (točan bi bio 0.3782), **0.50→0.2286** (0.9053), 🔴 **0.80→0.4600** (0.9743), 0.95→0.7840 (0.9945). Najgore je pogođen student **usred učenja** (−0.68 kod p_l 0.50), ne novak. Ovo je razred **#63**: ishod sustava i ishod zapisan u bazi se razilaze, a `attempts` je istraživački podatak i `skill_mastery_history` rekurzivan lanac (#18) pa se redak ne može obrisati iz sredine. **Naslijeđeno, ne uvedeno:** isti je slučaj prije išao kao `unsupported_eval`; premještanjem pod vlastito ime postao je vidljiv. **Popravak (odluka korisnika):** `plan_unavailable` **NE stvara pokušaj** — Evaluator izlazi PRIJE `persist_attempt` i odbija tok (`refuse(model-updated)`), Coordinator to mapira u `flow["error"]`, ruta u **503**, frontend u poruku koja izrijekom kaže da nije riječ o grešci u upitu. Smetnja se broji u `agent_messages_log` uz `correlation_id`, ne u `attempts` (izmjereno: 92 zapisa `refuse` evaluator→coordinator). 🔴 **Odbijena je opcija „perzistiraj ali preskoči BKT"**: tražila bi da `attempts` nosi dvije uloge — zapis o radu i zapis o kvaru — a taj je obrazac na ovoj grani već bio uzrok kvara (`_BLOCK_VALUE`) i razlog uklanjanja `entry_task_id`. Kategorija je **jednočlana**: `plan_unavailable` je jedini `error_type` gdje nije zakazao student. Srodno #63, #18, #66 |
| **#70** | 🟡 **`task_not_found` istekne umjesto da odgovori — jedini preostali put koji ne poštuje pravilo uspostavljeno u #69** | 🟡 **otvoren, NE popravlja se u ovoj grani** | `_send_task_not_found` ([`evaluator_agent.py:165-193`](../backend/agents/evaluator_agent.py)) šalje INFORM ontologije **`attempt-result`**, a `_flow_template` ([`coordinator.py:551-558`](../backend/agents/coordinator.py)) matcha **samo** `model-updated` i `recommend-next` za dani `cid` — poruka do toka **nikad ne stigne**. **IZMJERENO 2026-08-14** (nepostojeći `task_id` kroz pun lanac): klijent dobije **HTTP 504 `evaluation_timeout` nakon 9.09 s** (= `update_timeout` 7 s + `settle` 2 s); utori se **uredno oslobađaju** (3 uzastopna zahtjeva, `flow_count` 0 → 0). Dakle: točan status za krivi razlog, i to nakon punog prozora čekanja. 🔴 **Ostaje JEDINA iznimka** od pravila koje #69 uspostavlja (smetnja → brz, imenovan odgovor), pa se **ne smije citirati kao presedan**. 🔴 **POUKA IZ ISPRAVKA:** prva verzija ovog nalaza tvrdila je da put daje *degradiran 200 s `verdict="unknown"`* — izvedeno iz `build_response_payload`, koji podnosi `attempt_id=None` ([`coordinator.py:230`](../backend/agents/coordinator.py)), **bez provjere da poruka dotle uopće dolazi**. **KOD KOJI PODNOSI STANJE NIJE DOKAZ DA TO STANJE NASTAJE.** Ista klasa kao povučeni dio #60 („trag u produkcijskim podacima"). Mehanizam je usput potvrđen namjernim kvarom: ograniči li se `_flow_template` performativom, i novi `refuse` put daje isti 504 |
| **#71** | 🟡 **Sustav se ponašao ispravno iz razloga koji nitko nije odlučio — pa nijedan test nije mogao pasti** | 📌 **poučak; zatvoren uvođenjem ugovornog testa** | Pri reviziji taksonomije uočeno da `plan_unavailable` nije bio ni u `ERROR_TEXT` ni u `TEXT_DETAIL_TYPES` (`feedback.ts`), pa je padao na `FALLBACK_ERROR_TEXT` — *„Ocjenjivanje nije uspjelo — pokušaj ponovno predati rješenje."* 🔴 **Ta je poruka bila TOČNA**: smetnja jest prolazna i ponovni pokušaj jest ispravan savjet. Ali točnost je bila **posljedica fallbacka, ne odluke** — nitko taj tekst nije napisao za taj tip, i prekine li se veza (promjena fallbacka, novi tip s drukčijim značenjem), ponašanje tiho postaje netočno **a da nijedan test ne padne**, jer nijedan ne tvrdi vezu koja nije uspostavljena. Drugi primjerak istog obrasca u istom krugu: `unsupported_eval` attempti su bili **0** ne zato što je put bio siguran, nego zato što je **maska Kat. C slučajno štitila i od toga** — svi M6 zadaci bili su `is_active=False`, pa do predaje nikad nije došlo. **Zatvoreno** parametriziranim ugovornim testom (`test_error_taxonomy_contract.py`, 48 tvrdnji): svaki tip koji `evaluate()` emitira mora imati poruku, točno jednu politiku prikaza detalja, svjesnu misconception-odluku, točno jednu politiku hint payloada i opis za LLM — a skup tipova se **čita iz izvora**, ne prepisuje. **Za rad:** „radi ispravno" i „ispravnost je zajamčena" nisu ista tvrdnja; razlika se vidi tek kad se pita KOJI test pada ako se ponašanje pokvari |
| **#72** | 🔴 **Model je halucinirao dijagnozu iz SAME KLASIFIKACIJE, bez ijednog detalja — i ta je dijagnoza proturječila ispravnom radu studenta** | 📌 **prijetnja valjanosti savjeta (za rad); stroža tvrdnja od #64** | Izmjereno 2026-08-14 uz stvarni pad EXPLAIN-a. Student je predao **ispravan** upit; sustav nije uspio dohvatiti plan. `plan_unavailable` **nije** bio u `DETAIL_SAFE_TYPES`, pa je modelu otišla **samo klasifikacija** — bez `detail`a, bez plana, bez referentnog upita. Doslovni odgovor: *„Čini se da referentni upit u zadatku ima problem s izvedbom — moguće je da koristi operacije koje baza ne može optimizirati indeksima (npr. funkcije nad stupcima, ili operatore koji sprječavaju korištenje indeksa). Provjeri jesu li u WHERE ili JOIN uvjetima stupci direktno uspoređeni, bez transformacija…"* — student je napisao **točno takav** upit. 🔴 **Ovo je stroža tvrdnja od #64** („model izmišlja kad su podaci tanki"): ovdje podataka o grešci **nije bilo uopće**, a model je svejedno proizveo konkretnu, provjerivu i **netočnu** dijagnozu. **Minimalan payload NE ograničava halucinaciju.** Posljedica za odluku o selektivnom B+ (5.0): manje podataka znači manje utemeljenja, pa se rizik po studenta **seli iz privatnosti u točnost** — dvije mjere koje su se dosad čitale kao ista os. Nakon #69 ovaj put više ne postoji (`plan_unavailable` nije ishod pokušaja, pa hint sloj do njega ne dolazi), ali nalaz vrijedi **za svaki tip koji šalje samo klasifikaciju** (`CLASSIFICATION_ONLY_TYPES`: `execution_error`, `timeout`, `explain_submitted`). Srodno #64, #59 🔴 **DOPUNA 2026-08-18 — nalaz je SVOJSTVO SLOJA, ne jedan slučaj; tvrdnja preformulirana.** Izvorni primjerak (`plan_unavailable`) nestao je s ERRATOM #69, pa je nalaz premjeren nad **12 stvarnih hintova kroz pun lanac** (`USE_LLM_HINTS=true`, `claude-haiku-4-5`, svježi račun po tipu, po dva neovisna prolaza za pet tipova). **Preformulirana tvrdnja:** nije „model halucinira iz gole klasifikacije" nego — **kad klasifikacija NE određuje dijagnozu jednoznačno, a `detail` se ne šalje, model rupu popuni iz `task_description` i to izgovori kao činjenicu o studentovom upitu.** `task_description` se naime šalje UVIJEK (`build_hint_payload`), pa „bez ijednog detalja" nikad nije značilo „bez ikakvog konteksta" — samo bez konteksta o **studentu**. **Primjerci, doslovno:** `execution_error` (student napisao `SELECT nepostojeca_kolona FROM orders`, u payloadu samo `sqlstate=42703`) → *„Greška 42703 … provjeri naziv stupca `status`: je li točno napisan, postoji li zaista u tablici `orders`"*, i u drugom prolazu *„provjeri postoji li razmak ili tipfeler u nazivu stupca `status`"* — **stupac `status` student nije ni spomenuo**, model ga je uzeo iz opisa zadatka. `timeout` (student napisao `SELECT count(*) FROM orders a, orders b, orders c, orders d`) → *„Upit je vjerojatno trajao dugo jer je `DISTINCT` primijenjen na previše stupaca ili na cijele redove. Provjeri — trebao bi ti `DISTINCT` primjenjiti samo na stupac `status`"* — **u upitu nema `DISTINCT`a**, savjet vodi u krivo. 🔴 **Protuprimjer koji tvrdnju izoštrava:** `explain_submitted` je također `CLASSIFICATION_ONLY`, ali je **siguran** — *„Vidiš da si dao `EXPLAIN` plan umjesto samog upita"* je točno, jer **ime klase JEST dijagnoza**. Dakle opasnost ne nosi izostanak detalja sam po sebi, nego **nedoodređenost klasifikacije**. **Kontrolna skupina** (`DETAIL_SAFE` / rekonstrukcija stupaca): `row_mismatch` i `wrong_columns` u oba prolaza pogađaju stvarnu grešku i imenuju točan cilj (`ORDER BY` smjer; `id, first_name, last_name, department`) — **s detaljem model ne izmišlja**. Usput: jedan `row_mismatch` hint doslovno je citirao interni engleski `„Row 0 differs"` studentu. **Pogođeni tipovi: `execution_error` i `timeout`** (2/2 prolaza svaki). **Čeka odluku korisnika** — kandidati: hint se ne nudi za tipove čija klasifikacija ne određuje dijagnozu, ili prompt izrijekom zabranjuje tvrdnje o sadržaju upita. |
| **#67** | 🔴 **`make backup` nikad nije radio iz čistog klona** | ✅ **popravljen 2026-08-14** (`1e48bbb`) | `scripts/backup_eval_data.sh` stajao je u gitu kao **`100644`** — bez izvršnog bita. `make backup` je padao na „Permission denied", pa je target bio neupotrebljiv bez ručnog `bash scripts/…`. Pogađa **jedini mehanizam koji štiti nenadoknadive evaluacijske podatke** (#37); verifikacija u 4.6-eval očito je išla kroz `bash`, pa izvršni bit nikad nije ušao u indeks. Ista klasa kao **#26** (`make dev` nije bio from-scratch sposoban) i **#39** (`dev-reset` guard neupotrebljiv): **target koji nije pokrenut onako kako ga dokumentacija propisuje nije provjeren target.** Audit: `backup_eval_data.sh` je JEDINA `.sh` datoteka u repou i jedina koju Makefile poziva izravno, pa druge rupe ovog oblika nema |
| **#73** | 🟡 **`OrchestrationFSM` se uklanja dvaput — jednom naš kod, jednom SPADE lifecycle; `ValueError` se guta na SVAKU predaju** | 🟡 **otvoren, ne popravlja se u ovoj grani** | Na svaku predaju uvicorn ispiše `Task exception was never retrieved` + `ValueError('This behaviour is not registered')` iz `remove_behaviour` (`spade/agent.py:286`). **IZMJERENO 2026-08-18** instrumentiranjem `Agent.remove_behaviour` u zasebnom procesu (repo nedirnut), 20 predaja kroz pun lanac: **20 iznimaka, 20/20 klasa `OrchestrationFSM`, sve na `coordinator@localhost`**. Pozivatelji, prebrojani nad 5 predaja: `coordinator.py:710 in _release_flow → OrchestrationFSM = OK` (5×), pa `behaviour.py:305 in _step → OrchestrationFSM = ValueError` (5×); usporedbe radi `behaviour.py:305 in _step → _Send = OK` (5×). Dakle **naš eksplicitni `remove_behaviour` pobjeđuje utrku i skine FSM**, a SPADE-ov *implicitni* epilog `CyclicBehaviour._step` (`self.agent.remove_behaviour(self)`) zatekne prazno i baci. Naš `_release_flow` ([`coordinator.py:705-712`](../backend/agents/coordinator.py)) **već ima** gard `has_behaviour` + `except ValueError`, ali gard štiti **naš** poziv — SPADE-ov epilog teče u vlastitom `_start()` tasku, izvan njega. `_release_flow` zove sam FSM ([`coordinator.py:567`](../backend/agents/coordinator.py)); `kill()` u našem kodu **ne postoji nigdje**. 🔴 **NIJE curenje:** `len(agent.behaviours)` je **1 prije prve predaje i 1 nakon 20** za svih 7 agenata (`coordinator` = `_Intake`, `gateway` = `_Resolve`), krivulja ravna, bez rasta. **Ne skriva ništa drugo:** 20/20 progutanih iznimaka je **isti** `ValueError` — grana ne može sakriti stvarnu grešku u toku jer se izvršava tek nakon `is_running = False`, kad je tok već završen. Zatečeno, **nije uvedeno ovom granom**, ali je u putu koji su #62/#63 dirali pa ne prolazi kao kozmetika. Srodno #62, #63 |
| **#74** | 🟢 **Kvalifikacija tvrdnje o XMPP-u: u jednoprocesnoj izvedbi agentske poruke ne prelaze mrežu** | 📌 **nalaz za poglavlje rada, NIJE kvar** | Agenti razmjenjuju FIPA-ACL poruke kroz SPADE; u jednoprocesnoj izvedbi SPADE ih isporučuje **unutar procesa**, a XMPP služi za **autentikaciju i registraciju**. Izvor je `spade/container.py:121-133`: `to = str(msg.to)`, pa `if to in self.__agents: self.__agents[to].dispatch(msg)`, inače `await behaviour._xmpp_send(msg=msg)`. Svih 7 (6 domenskih + gateway) startaju u istom uvicorn procesu ⟹ isti `Container` ⟹ uvijek prva grana. **IZMJERENO 2026-08-18:** uz Prosody u stanju `exited` predaje i dalje daju **200 u 0,12–0,13 s s punim lancem od 12 poruka** (3 mjerenja + burst 10/10). 🔴 **Ovo bolje objašnjava `--workers 1`** nego dosadašnja formulacija: ograničenje ne dolazi samo od in-process `AgentBridge` dicta nego od toga da **agenti postoje jednom po procesu** — drugi worker značio bi drugi skup agenata s istim JID-ovima. Distribuirana izvedba usmjerila bi **iste** poruke preko XMPP-a **bez izmjene agentskog koda** (druga grana istog `if`-a), pa arhitektura nije poništena — ali tvrdnja da agenti komuniciraju preko XMPP-a u tekstu rada traži ovu kvalifikaciju. Srodno #62 |
| **#75** | 🟡 **Pod uvicornom iz Makefilea nijedan knjižnični zapis ne dolazi u log — incident ne ostavlja trag** | 🟡 **stavka deploymenta, ne ove grane** | Uvicorn konfigurira samo vlastite loggere (`uvicorn`, `uvicorn.error`, `uvicorn.access`) i **ne postavlja root handler**, pa sve ispod `WARNING` iz knjižnica propada. **IZMJERENO 2026-08-18:** log procesa pokrenutog **točno naredbom iz Makefilea** ([`Makefile:167-168`](../Makefile)) sadrži **0 redaka** sa `slixmpp`/`spade` — nema ni `Agent … connected and authenticated` pri startupu. Za usporedbu, isti kod uz `logging.basicConfig(level=INFO)` u prekidu XMPP veze ispisuje `slixmpp.xmlstream.xmlstream: connection_lost: (None,)` **7×** (po agentu). 🔴 Za **nenadziranu evaluacijsku sesiju** to znači da prekid, reconnect i svaka knjižnična greška prolaze **bez ijednog traga**; jedino što se probije je `asyncio` na razini `ERROR` (v. #73), i to bez timestampa i bez imena loggera. Srodno #57 |
| **#76** | 🟡 **Tvrdnja o „dva sjemena" u falsifikaciji nije bila reproducibilna — drugo sjeme nigdje nije zapisano** | 🟡 **otvoren, popravak bez koda odgođen** | `fix-koncept-zadatak-wrapup.md` §D.4a tvrdi da je dubinski prolaz `FALSIFY_TRIALS=1500` bio čist **„uz dva različita sjemena"**, a u `test_recommender_no_dead_end.py` postoji **samo** `SEED = 20260814` (hardkodiran, bez env override-a). Drugi prolaz **nigdje nije zabilježen** — ni broj, ni ishod — pa se tvrdnja nije mogla ponoviti niti opovrgnuti. Ista klasa kao #71 („ispravno slučajno"): rezultat je vjerojatno bio točan, ali **nijedan artefakt ga ne čuva**, a upravo je taj test pisan pod devizom „sjeme je fiksno da pad bude reproducibilan". **Zatvoreno djelomično 2026-08-18:** drugi prolaz je ponovljen s izrijekom zapisanim sjemenom **20260818** (3000 stanja ukupno, 0 povreda, v. `m6-plan-presence-wrapup.md` §H). 🔴 **Preporuka koja NIJE izvedena:** `SEED` i `TRIALS` trebaju dolaziti iz env varijable (`FALSIFY_SEED`, `FALSIFY_TRIALS`) s dokumentiranim defaultima, da se prolaz s drugim sjemenom ne mora izvoditi izvan repoa — kako je i ovaj put morao (driver u scratchpadu koji postavlja `SEED` na modulu). Dok toga nema, svaka tvrdnja o „više sjemena" ostaje neprovjeriva iz samog repoa. Srodno #71, #60 |
| **#77** | 🔴 **Kurikularni redoslijed nije izražen kao pravilo nego samo kao poredak injekcije — a poredak nikad ne arbitrira; tier prior oblikovan kao PROCJENA ZNANJA troši se kao PRIORITET** | 🟡 **otvoren, odluka o poluzi predstoji; NIJE uzrokovano granom `m6-plan-presence`** | Ontologija kodira **logičke** preduvjete (`prerequisite/2`), moduli kodiraju **kurikularni** redoslijed (`modules.order_index`), a `recommend_next/2` konzultira **samo prvo**. `module.order_index` ulazi jedino kroz `_KANONSKI_POREDAK` ([`db_helpers.py:27`](../backend/agents/db_helpers.py)) kao **poredak injekcije**, dakle kao razrješavač izjednačenja — a izjednačenja nema, jer klauzula za `weak` strogo pretječe klauzulu za `partial` (`rules.pl:91-98`). Posljedica: **svaki otključan `weak` koncept pretječe nedovršeni modul 1**, jer tier prior `easy` = **0.30** ([`bkt/parameters.py:15`](../backend/bkt/parameters.py)) pada točno na `weak_threshold(0.30)` (`rules.pl:36`), a `weak` je **strogi `<`** — pa su M1 koncepti `partial`, a sve ostalo (`medium` 0.15, `hard` 0.05) `weak`. 🔴 **Dvije konstante jednake vrijednosti u dvije datoteke, i strogost jednog `<` odlučuje cijeli kurikularni redoslijed.** **IZMJERENO 2026-08-18** (SAVEPOINT/rollback, kroz stvarni Prolog motor): **savršen student** → `select_basic, from_clause, inner_join, right_join, cross_join, self_join, where_filter, …` — **prvi spoj korak 3, `where_filter` (modul 1) tek korak 7**; put nije ćorsokak (svih 29 koncepata u 29 koraka). **Realističan student** (BKT update kao u živom lancu, netočan pokušaj = `update(False)`): pri stopi točnosti **0.7** inverzija u **5/5** prolaza (prvi spoj korak 3–9, `where_filter` 5–13), pri **0.5** u **5/5** (spoj 3–9, `where_filter` 5–14) — dakle **10/10, ne vrijedi samo za jake studente**. `from_clause` pritom ispada iz prvih deset jer ga sekundarni updateovi zasite prije nego dođe na red. 🔴 **Nije nov nalaz nego treći susret s istim razredom:** #44 je isto ponašanje (INSERT → INNER JOIN) zabilježio 2026-07-26 uz odluku *„obranjivo, ZPD je poanta rada, ne mijenja se pred evalom"*; ovdje je novo (a) da pogađa **prvih deset koraka**, ne tek sredinu sesije, (b) da preživljava realističnu stopu točnosti, (c) izmjerena cijena tri poluge. **Poluge, sve tri uklanjaju inverziju i sve tri prolaze falsifikaciju** (2 × 1500 stanja, sjemena 20260814/20260818, `exhausted` 0): **(1)** `weak_threshold` inkluzivan → **2 pada** u zatečenoj suiti, oba samo o **nazivu reasona** (`weak_with_prereqs_met` umjesto `partial_continuation`), preporuka ostaje `select_basic`; drugo mjesto praga je `_WEAK_THRESHOLD = 0.30` u [`hint_payload.py:65`](../backend/agents/hint_payload.py). **(2)** `partial` klauzula prije `weak` → **4 pada**, među njima `test_subfloor_never_recommended` (subfloor koncept `insert` **preporučen kao meta**) — semantička regresija, ne kozmetika. **(3)** `prerequisite(join_condition, where_filter)` → **0 padova, 91/91 zeleno**, ali mijenja **ontologiju**, koju CLAUDE.md proglašava autoritativnim izvorom i koja je opisana u `faza-1-domenski-model.md` i `superpowers/plans/…faza-1b-prolog-ontologija.md`. Srodno #44, #35, #16, #60 |
| **#78** | 🟡 **Gate diskriminacije pokriva samo zadatke koje je autorska skripta napisala — zadatak 81 je izvan njega, a `anti is None` bi ga klasificirao kao „nije M6"** | 🟡 **otvoren; gate se NE seli u sweep (odluka 2026-08-18)** | Gate 2 (*isti redci, drugi potpis*) živi u [`manual_tasks_m6.py:287-315`](../backend/scripts/manual_tasks_m6.py) i grana se na `anti = task.get("anti_pattern"); if anti is None: … return` — dakle **zadatak bez deklariranog anti-patterna prolazi bez ijedne provjere plana, i to bez poruke**. **IZMJERENO 2026-08-18:** od **5 aktivnih `PLAN_CHECKED` zadataka** anti-pattern imaju samo **4** (3782, 3783, 3784, 3785); **81 (`index_usage_d3_41c8280e`) došao je kroz `import_dataset` i nema ga nigdje** — ni u skripti, ni u bazi (`tasks` nema kolonu za to), ni u `config/concepts/*.yaml` (ondje su `anti_patterns` **prozni opisi za LLM prompt**, ne izvediv SQL). 🔴 **Rupa je u POKRIVENOSTI, ne u sadržaju:** zadatak 81 je zdrav, ali ga nijedan gate ne bi provjerio, a jedini znak bila bi šutnja. **Zato gate diskriminacije NIJE prenesen u `sweep_task_integrity`:** uvoz `TASKS` vezao bi sweep (dio `preflighta`) uz **7 hardkodiranih SQL stringova**, dok `is_active`, `expected_query` i sam popis zadataka žive u bazi — to je konstanta koju je `m6-transverzalni-korak-0.md` §C.1 odbio (*„sadržaj kataloga u evaluacijskoj jezgri; može zastarjeti tiho"*), samo **uvezena umjesto prepisana**; a 81 bi uz to i dalje tiho ispao. Cijena nije bila razlog: izmjereno **0,18 s** za 2 × `EXPLAIN` + 1 × `execute` nad svih 5 (pojedinačni `EXPLAIN` 10–20 ms), daleko ispod praga. **Umjesto toga izabrana je varijanta O** — *svojstvo imenovano u `description` mora se pojaviti u potpisu referentnog plana* — jer primjenjuje isto načelo koje §C.2 već koristi za `expected_query`: **zadatak sam nosi svoju tvrdnju**, pa nema kataloga u kodu, imena indeksa se provjeravaju prema `pg_indexes`, i pokriva **i zadatak 81**. Nad imenima indeksa izmjereno ispravno: 81/3782/3783/3785 prolaze, a **83 pada s pravim razlogom** (opis obećava `idx_orders_customer`, plan daje `orders_pkey`) — trošak **0,06 s**. 🔴 **Generalizacija na metode spoja je ZAUSTAVLJENA** — v. §I wrapupa. Srodno #66, #45 |
| **#79** | 🟡 **Interni dijagnostički niz procurio je DOSLOVNO u tekst namijenjen studentu — kroz `error_detail` prema modelu** | 🟡 **otvoren, popravak nije jednoredan** | Izmjereno 2026-08-18 kroz pun lanac: hint za `row_mismatch` studentu je odgovorio *„Ako se pojavljuje **"Row 0 differs"**, to znači da redoslijed rezultata nije onaj koji se očekuje…"*. **Nije halucinacija** (za razliku od #72) — dijagnoza je bila **točna**; problem je što je model **prepisao interni engleski ispis** u hrvatsku pedagošku prozu. Zaseban razred: **propuštanje internog ispisa**, ne izmišljanje. **Put:** `ComparisonResult.diff_summary` → `attempts.detail` ([`evaluation.py:467`](../backend/agents/evaluation.py)) → `error_detail` u payloadu, jer je `row_mismatch` u `DETAIL_SAFE_TYPES`. 🔴 **Nabrojani su SVI interni nizovi koji tim putem mogu doći do modela** — sva četiri su `diff_summary` varijante iz [`sandbox_runner.py:295-368`](../backend/scripts/lib/sandbox_runner.py): **(1)** `"Row {i} differs"` (izmjeren primjerak), **(2)** `"Row count mismatch: actual={n} vs expected={m}"`, **(3)** `"Set diff: {n} expected rows missing from actual"`, **(4)** 🔴 `"Actual execution failed: {actual.error}"` — ovaj uz engleski **ugrađuje i sirovu PG poruku**, koja po vlastitoj bilješci u `ExecutionResult.sqlstate` *„nosi doslovni redak upita i NE smije van"*. Ostali `detail`i koji idu modelu su hrvatski i pedagoški (`plan_mismatch`, `empty_result`, `syntax_error`), pa su izvan ovog nalaza. **Zašto to nije isto što i prikaz u sučelju:** `feedback.ts` te nizove svjesno stavlja u `MONO_DETAIL_TYPES` — diskretan mono blok **označen kao tehnički detalj**, upravo zato što su interni. Kad ih model prepiše u savjet, gube tu oznaku i čitaju se kao poruka sustava studentu. **Popravak nije jednoredan** (kandidati: izbaciti `row_mismatch` iz `DETAIL_SAFE_TYPES` — gubi se točnost savjeta; prevesti `diff_summary` — dira ugovor usporedbe i `MONO_DETAIL_TYPES`; zabraniti citiranje u promptu — mijenja prompt), pa **ostaje otvoren**. Srodno #72, #59 🔴 **DOPUNA 2026-08-18 — ODLUKA 6 NIJE PREKRŠENA; moja izvorna formulacija bila je preširoka.** Izmjereno, ne izvedeno. **(1) Grana je NEDOSEŽNA iz studentovog puta:** `compare()` gradi `"Actual execution failed: …"` samo `if not actual.success`, a `evaluate()` na `if not result.success:` ([`evaluation.py:362`](../backend/agents/evaluation.py)) **vraća prije** poziva `compare()` ([`evaluation.py:410`](../backend/agents/evaluation.py)) — pa jedini ulaz u `compare()` nosi `success=True`. Empirijska potvrda: **0/12** namjerno pokvarenih upita kroz `evaluate()` (nepostojeći stupac, nepostojeća tablica, `SELEKT`, dijeljenje nulom, tip-neslaganje, cross join s timeoutom, prazan upit, sami `SELECT`, DML, `GROUP BY` greška, `EXPLAIN`) proizveo je `detail` koji počinje tim nizom. Ostali pozivatelji `compare()` su offline alati (`smoke_test_dataset.py`, `task_validator.py`) i testovi — ne pišu `attempts` ni ne dosežu hint sloj. **(2) Sirova PG poruka JEST pohranjena, ali NE odlazi modelu.** Za `execution_error` `detail` doista nosi doslovni redak upita — izmjereno: `'column "nepostojeca_kolona" does not exist\nLINE 1: SELECT nepostojeca_kolona FROM orders WHERE customer_id = 10...\n ^'`. Ali `execution_error` je u `CLASSIFICATION_ONLY_TYPES`, pa `build_hint_payload` **nikad ne dodaje `error_detail`**. Payload koji je stvarno otišao, doslovno: `{"task_description": "…", "concept": "select_basic", "mastery": "nisko", "error_type": "execution_error", "sqlstate": "42703"}` — provjereno na četiri fragmenta (`nepostojeca_kolona`, `SELECT nepostojeca`, `customer_id = 108`, cijeli upit): **nijedan nije u payloadu**. To je selektivni B+ koji radi točno kako je 5.0 §2 odlučila. **(3) Ispravak moje tvrdnje:** `"Actual execution failed: {actual.error}"` **jest** u kodu i **jest** bi ugradio PG poruku, ali do modela ne dolazi — ni preko te grane (nedosežna), ni preko `execution_error` (klasifikacija bez detalja). **#79 time ostaje kozmetika** i izvan opsega: preostala tri niza (`"Row {i} differs"`, `"Row count mismatch: …"`, `"Set diff: …"`) su engleska ali **ne nose ni znak studentovog upita**. Nije blokator za slanje linka. |

---

## Bilješke uz nalaze — dugi oblik

Nalazi čije obrazloženje ne stane u ćeliju tablice. Redak u tablici nosi status i
presudu, ovdje stoji dokaz.

### #13 — zašto se korekcija hue→45 NE izvodi (odluka 4.7, 2026-08-09)

🔴 **Za trag odlučivanja:** #13 se **NE** zatvara nasljeđivanjem dokaza iz #33. Commit
`c12ec31` (4.4b) ih je bio spojio jednom rečenicom — „Token-level, ide uz rekalibraciju
palete zajedno s partial hue 60→45" — iako s #33 nema veze: **#33 je o kontrastu mastery
gradijenta, #13 o hue blizini partiala i accenta.** Kad je #33 odbačen matematičkim
dokazom, #13 je otišao s njim **bez vlastite presude**. Ovo je ispravlja.

1. **Mitigacija je izmjerena i drži — ali tek nakon što je izmjerena u PRAVOM kontekstu.**
   Ikona + tekstualna oznaka su OBAVEZAN kanal (MASTER §2.2), pa boja **nije nosilac
   informacije** nego pojačanje: verdict „Djelomično" nosi `TriangleAlert` + tekstualnu
   oznaku u svakoj grani (`FeedbackPanel.tsx:55-59`, `verdict-ui.ts:39-45`).
   Izmjereno 2026-08-09 (alpha-kompozitirano, konvertor validiran na prethodno
   objavljenim brojkama):

   | `text-partial` prema | light | dark |
   |---|---|---|
   | `bg-partial-soft` — **stvarni kontekst renderiranja** | **4,86:1** ✅ | **8,03:1** ✅ |
   | `card` — ploha na kojoj komponenta NE stoji | 5,48:1 ✅ | 8,68:1 ✅ |

   🔒 **DOC — poučak, ne fusnota:** wrapup 4.3 (`docs/faza-4.3-wrapup.md:58`) objavio je
   „Kontrast `text-partial` AA ✓ (8.68:1 dark / 5.50:1 light)". Te su brojke mjerene
   **vs `card`**, a komponenta se renderira unutar omotača `border-partial/40
   bg-partial-soft` — dakle na `partial-soft`. Mjerenje je bilo **izvan konteksta
   renderiranja**. Ovdje ishod ne mijenja presudu (oba para prolaze AA), ali je to
   **ista klasa greške** kao netočni docstring `MasteryBar` iz #33: broj je bio točan za
   par koji je izmjeren i neprimjenjiv na par koji se stvarno vidi. Otud dopuna politike:
   uz brojku i datum ide i **ploha prema kojoj je mjereno**.
   (Napomena o preciznosti: ponovno mjerenje `partial` vs `card` u light temi daje
   **5,48:1** naspram objavljenih 5,50:1 — isti par, razlika je zaokruživanje konvertora,
   ne promjena tokena.)

2. **Korekcija je izvediva, ali ne besplatna.** Pomak na hue 45 dira **4 datoteke i
   0 komponenata** (`index.css` ×4 vrijednosti, `MASTER.md` §2.2 + §2.7, errata) —
   komponente vuku `text-partial`/`bg-partial-soft`/`border-partial` pa promjena tokena
   propagira sama. Hue udaljenosti bi se popravile prema accentu i **pogoršale** prema
   `incorrect`: light 55→45 znači Δ do accenta 15→**25**, a Δ do `incorrect` 30→**20**;
   dark 60→45 znači Δ do accenta 20→**35**, Δ do `incorrect` 35→**20**.

3. **Cijena je ponovno otvaranje SSOT-a neposredno pred deploy.** MASTER §2.7 t. 4
   propisuje hue mapu sustava (**25 incorrect · 55 partial · 70–85 accent · 150 correct ·
   190–260 mastery · 300 tier · 345 difficulty**). Pomak partiala prepisuje tu mapu, a po
   🔒 DOC politici traži **novo mjerenje cijele skale** u obje teme, ne samo partiala.

4. **Korist je neprimjetna.** Boja ionako nije jedini kanal (t. 1), pa se korisniku ništa
   ne mijenja. Uz to se partial prikazuje na **eval-verificiranom** FeedbackPanelu (4.3c,
   živo verificiran) — dodir bez funkcionalne koristi je čisti regresijski rizik.

**Status: 📌 prihvaćeno kao limitacija.** Nijedna vrijednost tokena nije mijenjana.
Kandidat za Fazu 6 uz punu remjeru palete, zajedno s #33 i s nalazom o prstenu fokusa —
ali kao **odvojeni nalazi s odvojenim obrazloženjima**, ne kao jedan paket. Spajanje je i
dovelo do ovog propusta.

### #24 — revizija pretpostavke o dostižnosti (2026-08-09)

**Kriterij, pročitan iz koda (ne iz errate):** `gamification_logic.py:240-241`
`if facts.current_streak >= 7: earned.add("streak_7")`, gdje `current_streak` dolazi iz
`streak_from_active_dates:186-191` — broj **uzastopnih kalendarskih dana** s barem jednim
pokušajem, koji **završava danas**, u zoni Europe/Zagreb. Deklarativni mirror
`badges.pl:22-23` govori isto. ✅ **Opis kriterija u izvornom zapisu je bio TOČAN.**

**Ono što pada je zaključak.** Izvorni zapis tvrdio je: „horizont bedža je dulji od
trajanja evaluacijske sesije → **očekivana stopa osvajanja 0 %**". Ta je tvrdnja bila
točna **pod modelom nadzirane jednokratne laboratorijske sesije**, u kojoj sudionik sustav
vidi jedan dan. **Taj model više ne vrijedi:** evaluacija se izvodi asinkrono preko javnog
linka, sudionici rade u vlastitom ritmu kroz dane ili tjedne. `streak_7` time prestaje
biti nedostižan **po konstrukciji**.

**Kriterij se NE mijenja** (gamifikacija je zamrznuta; i nema potrebe). Mijenja se
**status u analizi gamifikacije**:

- prije: 0 % je bila **predvidljiva posljedica dizajna eksperimenta** — izvještavala se
  kao takva, bez informacijske vrijednosti;
- sada: stopa osvajanja je **mjerena varijabla** — pokazatelj *održanog* angažmana kroz
  dane, a ne trenutne aktivnosti.

**Pun katalog provjeren na vremenske komponente** (`seed_data.py` BADGES × `eval_badges`,
`gamification_logic.py:226-247`):

| Bedž | Kriterij (iz koda) | Vremenska komponenta |
|---|---|---|
| `first_correct` | `facts.has_correct` | nema |
| `join_master` | `{inner,left,right}_join ⊆ mastered` | nema (problem je bio podatkovni — #25/#27) |
| **`streak_7`** | `current_streak >= 7` | **DA — kalendarski dani; JEDINI** |
| `null_ninja` | `"null_handling" in mastered` | nema |
| `explorer` | `evaluable_modules ⊆ attempted_modules` | nema (broj modula, ne vrijeme) |

Ostala četiri mjere **ishode** (točnost, ovladanost, pokrivenost modula) koji ne poznaju
pojam dana. Po tragu #22 provjereno i da `explorer` nema fiksne brojke koja bi ostarila —
kriterij je od 4.4-0f dinamičan uz fail-closed guard (`gamification_logic.py:244-246`).

**Empirijski (2026-07-26):** `seed_demo_user` odradio je **27 attempta u JEDNOM danu**
(streak 1/1) → osvojeno `['first_correct', 'explorer']`. `explorer` je dakle osvojen
unutar jednog dana — potvrđeno **mjerenjem**, ne izvodom; `streak_7` nije, kako i mora
biti pri streaku 1.

⚠️ **Dostižan ≠ vjerojatan.** Kriterij je strog: 7 **uzastopnih** dana, **bez ijednog
propuštenog**, svaki s barem jednim pokušajem. Sudionik koji odradi studiju kroz dva
tjedna s prekidima ne osvaja bedž. Očekivana stopa ostaje **niska**, ali je sada
**empirijsko pitanje**, ne unaprijed poznata nula. U radu se izvještava izmjerena stopa uz
ovu napomenu o strogosti.

**Ostaje netaknuto:** `streak_7` je i dalje svjestan dugoročni retention element, ne
defekt. Bedž se ne mijenja.

---

## Opseg implementacije — REZANE faze (odluka korisnika, 2026-07-20)

**Faza 4.6 (motion/WebSocket) i Faza 4.7 (visual QA polish) su REZANE.**

**Obrazloženje:** preostali runway do rujanskog roka troši se na **evaluaciju sa
sudionicima i pisanje rada**, a ne na uglađivanje sučelja. Obje rezane faze su
poboljšanja postojećeg, nijedna ne otključava novu funkcionalnost niti utječe na
mjerenje: motion/WS je vizualna dorada i realtime dostava koju sinkroni `/attempt`
ne treba, a visual QA je polishing iznad razine koja je već izmjerena kao
prolazna (a11y i kontrast provjereni u 4.4b/4.5a/4.5b).

**Ovo ide i u rad**, u odjeljak o opsegu implementacije: sustav je za evaluaciju
funkcionalno potpun (M1–M5 + transverzalni M0), a rezano je svjesno i
obrazloženo, ne izostavljeno previdom.

Umjesto njih izvedena je **Faza 4.6-eval** — sigurnost podataka, export,
čist baseline i operativne procedure (#37, #38, #39).

### ⟳ REVIZIJA (2026-08-09) — Faza 4.7 je OŽIVLJENA, 4.6 ostaje rezana

**Što se mijenja:** odjeljak iznad točno opisuje odluku od 2026-07-20, ali je u dijelu
koji se tiče **4.7** nadglasan. Faza 4.7 (visual QA / a11y / responsive / hardening)
**više nije rezana**. Faza 4.6 (motion + WebSocket) **ostaje rezana** i neizmijenjena;
umjesto nje je izvedena 4.6-eval (#37, #38, #39). Postojeći tekst se **ne prepisuje** —
trag odlučivanja ostaje, isti obrazac kao §„~~Odluke koje čekaju~~".

**Razlog — promjena strategije evaluacije s NADZIRANE LABORATORIJSKE na ASINKRONU
JAVNU.** Odluka od 2026-07-20 pretpostavljala je nadziranu sesiju: pripremljeni računi,
usmene upute i prisutan autor koji pomaže kad nešto pukne. Evaluacija se sada izvodi na
**javnom URL-u**, sa **samostalnom registracijom** i **bez nadzora**. Nenadzirano sučelje
na javnom URL-u nosi drukčiji rizik nego sučelje kojim se rukuje uz prisutnog autora, pa
se mijenja i *što je* polish:

- Put `/register → prvi login → prazna stanja → prvi zadatak` prestaje biti kozmetika i
  postaje **jedini kanal uputa** — nema usmenog objašnjenja koje bi ga nadomjestilo.
- Oporavak od greške prestaje biti ugodnost i postaje **uvjet da sudionik završi** — nema
  nikoga da ga izvuče.
- Obrazloženje preporuke (#44) više se ne može dati uživo; ako ga UI ne nosi, sudionik ga
  ne dobiva.
- Nepoznat preglednik i nepoznata širina zaslona postaju stvaran rizik (u labosu su bili
  poznati).
- Informiranje sudionika i kontakt postaju obveza sučelja, a ne razgovora (v. #46).

**Opseg motiona u 4.7 (da se ne pročita kao tiho oživljavanje 4.6):** ~~4.6 ostaje rezana.~~
Jedina animirana površina dodana u 4.7 je **mobilni navigacijski drawer**, i to kao
posljedica zahtjeva **pristupačnosti** (ispod 768px nije postojala nikakva navigacija), ne
kao motion polish. ~~Gamifikacijski motion (XP count-up, level-up celebration, badge-unlock,
streak flame), page tranzicije, ⌘K paleta i WebSocket **ostaju neizvedeni**.~~
*(⟳ 2026-08-10: dvije precrtane tvrdnje nadglasane su završnom revizijom niže.)*
`framer-motion`/`motion` nisu u `package.json`; sav motion u aplikaciji je CSS
(`tw-animate-css` + motion tokeni iz 4.1b).

**Što ostaje istinito iz odluke 2026-07-20:** obrazloženje da polish ne otključava novu
funkcionalnost i ne utječe na mjerenje vrijedi za **estetski** dio 4.7 (razmaci,
poravnanja, motion). Taj dio je i dalje najniži prioritet i reže se prvi ako rok pritisne.
Ono što je 4.7 dobila natrag je **operativna upotrebljivost bez nadzora**, ne uglađivanje.

**Kako se prijavljuje u radu:** u odjeljku o opsegu implementacije navodi se da je 4.6
(motion/WS) rezana svjesno i obrazloženo, a da je 4.7 izvedena u **suženom,
prioritiziranom** obliku vođenom zahtjevima asinkrone javne evaluacije — ne kao puni
vizualni QA prolaz iz plana §4.7. Popis stvarno izvedenog vodi
`docs/faza-4.7-korak-0.md` §9 i wrapup 4.7; nepopravljeni nalazi su u
`docs/faza-4.7-nalazi.md`.

### ⟳ ZAVRŠNA REVIZIJA (2026-08-10) — 4.6 se IZVODI unutar 4.7; granica se više ne pomiče

**Što se mijenja, zadnji put:** Faza 4.6 **više nije rezana** — izvedena je u cijelosti
unutar 4.7 (stage 3, DIO B), **osim**: WebSocketa (backend + infra, deployment nepoznanica
— ostaje rezan), ⌘K palete (Monaco hvata tipke, najmanja vrijednost — ostaje rezana) i
page tranzicija (B.6 — rezane UNUTAR DIJELA B: entrance stagger već animira ulaz svake
ne-Task stranice pa bi fade dupli-animirao isti mount, a Task mora ostati bez entrance
animacije; jedina čista dekoracija na popisu, rezana prva, kako je i predviđeno).

**Stvarno izvedeno (2026-08-10):** hover/press mikrointerakcije (B.1) · entrance stagger
(B.2) · klizni aktivni nav indikator (B.3) · animirani progres + streak flame ≤ 1,8 s
(B.4) · FeedbackPanel: XP count-up, level-up puls + konfeti, badge unlock (B.5, uz ručnu
re-verifikaciju sva 4 stanja na živom agentskom lancu). Usput otkriven i popravljen
**N-18**: `duration-*` klase bile su bez učinka od 4.1b (sve tranzicije na defaultu
150 ms). 🔴 `framer-motion` NIJE uveden — sve je CSS + minimalni JS kroz postojeće motion
tokene; jedina nova ovisnost je `canvas-confetti` (4,2 kB gzip, lijeni chunk).

**Poučak:** tri uzastopne revizije istog opsega (2026-07-20 rez → 2026-08-09 oživljena
4.7 uz „4.6 ostaje rezana" → 2026-08-10 izvedba 4.6) bile su signal da granica **nije
bila stvarna, nego odgađanje odluke**. Granica koja se mora ponovno crtati svakih
tjedan-dva nije granica opsega nego simptom da kriterij reza („polish ne utječe na
mjerenje") nije bio točan za gamifikacijski dio — v. sljedeći odlomak.

**Za rad (odjeljak o gamifikaciji):** gamifikacijska povratna sprega bila je dosad
implementirana kao **TIHE BROJKE** — XP se promijeni, level se promijeni, bedž se pojavi,
sve bez ikakve istaknutosti. Rad opisuje gamifikaciju kao jedan od tri stupa sustava, a
literatura mehanizam gamifikacije opisuje kao **istaknutost povratne sprege** (salience),
ne kao puko postojanje nagrade u bazi. 4.6 time **dovršava stup koji rad tvrdi da
postoji**, ne ukrašava ga — zato njezino izvođenje prije evaluacije nije polish nego
usklađivanje implementacije s opisom sustava u radu.

**Napomena o valjanosti (bilježi se, nije prijetnja):** istaknutija nagrada može pojačati
privlačnost svakodnevnog povratka, što je u interakciji s **#45** (vremenski ovisan XP —
streak mehanika). Nije prijetnja valjanosti jer **svi sudionici dobivaju istu verziju
prije početka evaluacije** (nema between-subjects razlike u istaknutosti), ali se
interakcija bilježi za interpretaciju rezultata: mjereni angažman uključuje i doprinos
istaknutosti povratne sprege, ne samo mehanike nagrađivanja.

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

---

## #52 🟡 `--destructive` je bio nemjeren — sad je mjeren, i pada (3:1), ali NIJE regresija

**Status:** 🟡 zapisan, **ne popravlja se u redizajn-stageu 1** · izmjereno 2026-08-10 (dark)

Do danas `--destructive` nije imao **nijedan redak** u matrici (`scripts/a11y/pairs.py`),
premda ga `grep` nalazi na **18 mjesta**. Klasa problema #33: nitko o njemu ništa nije
tvrdio jer ga nitko nije mjerio.

### Što je od tih 18 zapravo dosežno — **samo jedan render**

| mjesto | dosežno? | dokaz |
|---|---|---|
| `ui/button.tsx:19-20` — `variant="destructive"` | **NE** | `grep -rn 'variant="destructive"' frontend/src` → **0 pogodaka**. Mrtav kod |
| `ui/field.tsx:53,217` — `data-invalid`, `FieldError` | **NE** | `grep -rn 'from "@/components/ui/field"'` → **0 importa**. Cijela datoteka je neupotrijebljena |
| `ui/button.tsx:8` — `aria-invalid:*` na gumbu | **NE** | nijedan `<Button>` u aplikaciji ne dobiva `aria-invalid` |
| **`ui/input.tsx:12` — `aria-invalid:*`** | **DA** | 5 upotreba: `LoginPage.tsx:77,93` · `RegisterPage.tsx:148,177,193` |

U dark temi na to polje padaju `dark:aria-invalid:border-destructive/50` (obrub) i
`dark:aria-invalid:ring-destructive/40` (3px halo). Oboje je **ne-tekst**, prag **3,00:1**
(SC 1.4.11 — indikator stanja „polje nije valjano").

### Mjerenje

| par | zatečeno | predloženo (ink-indigo) | prag |
|---|:---:|:---:|:---:|
| obrub `destructive/50` vs vlastita ploha (`input/30`) | **2,34** ❌ | 2,35 ❌ | 3,00 |
| obrub `destructive/50` vs okolina (`card`) | **2,43** ❌ | 2,42 ❌ | 3,00 |
| halo `destructive/40` vs `card` | **1,98** ❌ | 1,97 ❌ | 3,00 |

🔴 **Pada danas, jednako pada i nakon redizajna** (razlika ≤ 0,01). **Nije regresija** —
nova paleta ovo stanje ne uzrokuje niti ga mjerljivo mijenja.

**Zašto se ne popravlja ovdje:** boja nije jedini kanal. Nevaljano polje uz obrub nosi i
tekst greške s `role="alert"` (`LoginPage.tsx:80-84`), a taj je `text-incorrect` na `card`
= **6,18:1 ✅**. Isto rezoniranje kao #51 i #33: tint je pojačanje, ne nosilac. Popravak
(pojačati alfu obruba na ~48 %) mijenja vizualni jezik svih polja i **jest dizajnerska
odluka**, ne korekcija palete.

**Izvedeno:** sva tri para dodana u `pairs.py` (`SURFACE_VS_SURROUND`) da tvrdnja više ne
može živjeti nemjerena. Uz njih dodano i **7 parova obruba** (`border`/`input`/
`sidebar-border` nad `background`/`card`/`muted`, 1,25–1,62 — v. #33: docstring je tvrdio
„≥3:1", stvarnost je bila upola manja).

### Usputno: `--destructive` je izvan sRGB gamuta

`oklch(0.704 0.191 22.216)` → linearni R = **1,0127**. `palette.py` ga **tiho klampa**.
Izmjereno: maksimalna chroma u gamutu na toj svjetlini i hueu je **0,1877**, dakle višak je
**0,0033**. Renderirano `#ff6467`; ispravljena vrijednost `oklch(0.704 0.188 22.216)` daje
`#ff6568` — razlika **1/255 na dva kanala**.

**Presuda: vrijednost se NE mijenja** — mjerenje pokazuje da vizualne potrebe nema, a
uputa je bila „minimalno i samo ako mjerenje pokaže da treba". 🔴 **Ali klampanje ne smije
ostati tiho:** `palette.py` treba upozoriti kad ulazna vrijednost izađe iz gamuta, umjesto
da vrati brojku za boju koja nije deklarirana. To je popravak **harnessa**, ne palete, i
zapisuje se kao stavka za stage u kojem se harness ionako dira.

---

## #53 🔴 STRUKTURNI: sustav nema WARNING semantiku, pa se §2.1 predvidljivo probija

**Status:** 🔴 zatečeno · **STRUKTURNI**, ne higijenski · brand mark popravljen u 4.7-r2,
ostatak čeka novi token (Faza 6) · revidirano i preuokvireno 2026-08-10 (1C t.0c)

> ⟳ **PREUOKVIREN.** Prva verzija ovog nalaza brojala je prekršaje i tražila da se
> „poprave". To je bio krivi okvir — isti kao kod #51, gdje je ispalo da problem nije u
> pojedinim pozivima nego u tome što skup tokena **nema mjesta** za ono što se pokušava
> izraziti.
>
> ### Skup semantika koje sustav ima
>
> | semantika | tokeni |
> |---|---|
> | verdict | `correct` · `incorrect` · `partial` (+ `-soft`) |
> | tier | `tier-easy/medium/hard` |
> | difficulty | `difficulty-*` ×5 |
> | mastery | `mastery-0…100` |
> | gamifikacija | `accent-warm` trio |
> | danger | `destructive` |
> | data-viz | `chart-1…5` |
> | **warning** | 🔴 **NE POSTOJI** |
>
> **Amber je univerzalno warning boja.** Sustav ima amber, ali ga je §2.1 rezervirao za
> gamifikaciju. Kad developer treba označiti *upozorenje* — „poslužitelj vraća najviše
> 200 zapisa", „ovaj zapis je duplikat" — ne postoji token koji to znači, a postoji token
> koji tako **izgleda**. Rezervacija se zato ne probija iz nemara nego **predvidljivo**,
> i probijat će se opet pri svakoj sljedećoj poruci te vrste.
>
> **Popravak nije prebojati tri mjesta, nego uvesti token** (`--warning` + `-soft`, ili
> proširiti `--neutral` obitelj). To je promjena skupa semantika → **Faza 6**, uz odluku
> o hue-u koja mora proći isti cross-scale guard kao sve ostalo (§2.7): amber pojas
> 70–85 je zauzet, pa warning ili dijeli pojas s gamifikacijom (i tada ih razlikuje
> nešto drugo), ili ide izvan njega.
>
> **Srodno:** #51 (gamifikacijske površine kao strukturno najslabiji a11y teren),
> N-10 (`ErrorState` posuđuje verdict plohu za sistemsku grešku — **isti korijen**:
> nedostaje ne-verdict, ne-gamifikacijska semantika).

MASTER §2.1 kaže za topli amber: *„Rezerviran ISKLJUČIVO za: XP, level, streak, badge,
progres, CTA 'sljedeći zadatak'. **Ne koristi se za dekoraciju, navigaciju ni neutralne
akcije.**"*

🔴 **Zapisuje se SAMOSTALNO iako ga na brandu popravlja tuđa promjena** (gradijent iz
4.7-r2 t.4). Obrazac #48: nalaz koji rješava tuđa izmjena mora imati vlastiti broj, inače
tiho nestane i vrati se neprimijećen kad se ta izmjena ikad povuče.

### Puna revizija svih 19 potrošača

```
$ grep -rn "accent-warm-text" frontend/src --include=*.tsx --include=*.ts
```

| # | mjesto | što nosi | §2.1 |
|---|---|---|:---:|
| 1 | `AppShell.tsx:87` | **brand ikona, sidebar** | 🔴 dekoracija |
| 2 | `AppShell.tsx:102` | **brand ikona, mobilni header** | 🔴 dekoracija |
| 3 | `AdminPage.tsx:172` | „Poslužitelj vraća najviše 200 zapisa — suzi filtrom" | 🔴 **sistemska poruka o limitu** |
| 4 | `AgentFlowCard.tsx:79` | čip „duplikat zabilježenog prometa" | 🔴 **oznaka anomalije podataka** |
| 5 | `AgentFlowCard.tsx:149` | „N duplikata" | 🔴 isto |
| 6 | `LeaderboardTable.tsx:79,86` | ikona + „(ti)" na vlastitom retku | 🟡 **granično** — ljestvica jest gamifikacija, ali „(ti)" je oznaka identiteta, ne napredak |
| 7 | `ProgressHero.tsx:26,59` | level, streak | ✅ |
| 8 | `FeedbackPanel.tsx:147,169` | XP čip, level-up | ✅ |
| 9 | `AttemptRow.tsx:67` | „+N XP" | ✅ |
| 10 | `BadgeGallery.tsx:72,96` · `BadgeStrip.tsx:51` | bedževi | ✅ |
| 11 | `ContinueCard.tsx:93` · `TaskEntryPage.tsx:76` | `PartyPopper` kad je sve savladano | ✅ progres |
| 12 | `ContinueCard.tsx:118` | eyebrow „POČNI OVDJE" / „NASTAVI OVDJE" nad CTA-om | ✅ CTA kontekst |
| 13 | `ConceptCurveDetail.tsx:153` | label „prag ovladanosti" na grafu | ✅ progres |

**Ukupno: 4 jasna prekršaja (2 popravljena), 1 granično, 14 ispravnih.**

### Što je popravljeno, a što nije

**Popravljeno (#1, #2):** brand mark sada nosi `--grad-brand` (h280), ne amber. Time
prestaje tvrditi „ovo je napredak" na mjestu koje je čista brand identifikacija.

**NIJE popravljeno (#3, #4, #5), i NEĆE biti dok ne postoji token:** sva tri označavaju
**upozorenje**, a upozorenje u ovom sustavu nema boju. Prebojati ih u `--partial` ili
`--incorrect` značilo bi reći „student je pogriješio" ondje gdje je poslužitelj nešto
ograničio — zamjena jedne netočnosti drugom, glasnijom. Ostaju amber dok ne stigne
`--warning`, i ovdje je zapisano da to **nije previd nego posljedica praznine u skupu**.
(Sva tri su usto na admin ekranu, koji student nikad ne vidi — što snižava hitnost, ali
ne mijenja dijagnozu.)

**#6 ostaje granično i NE dira se.** Boja ondje nije jedini kanal — uz nju stoje ikona i
tekst „(ti)" (`LeaderboardTable.tsx:84-88`, s vlastitim komentarom „Tekstualni kanal —
oznaka ne smije biti samo boja/ikona"). Ako se §2.1 ikad proširi, ovo je prvi kandidat za
eksplicitno dopuštenje, ne za promjenu koda.

---

## #54 🔴 VALJANOST: `recommendations_log` broji i preporuke koje nitko nije vidio

**Status:** 🔴 otvoren · **nalaz o valjanosti mjerenja**, ne o kodu · utvrđeno 2026-08-10
(4.7-1C t.6) · klasa: #29 / #31 / #35 / #45 / #47

### Mehanizam, s citatom

TanStack Query **po defaultu refetcha na fokus prozora** (`refetchOnWindowFocus: true`).
`main.tsx:17-27` postavlja samo `retry` u `defaultOptions.queries` — **`refetchOnWindowFocus`
se NE gasi nigdje**, ni globalno ni po upitu:

```
$ grep -rn "refetchOnWindowFocus" frontend/src   → 0 pogodaka
```

Jedina obrana je `staleTime` na `useNextTask` (`useNextTask.ts:18`, **60 s**), i njezin
komentar točno opisuje mehanizam:

> „bez staleTime svaki tab-focus okida cijeli agentski pipeline i može zamijeniti CTA
> pod rukom"

`staleTime` **odgađa**, ne ukida: nakon 60 s neaktivnosti sljedeći povratak fokusa okida
`/next-task` → `RecommenderAgent` upiše redak (`recommender_agent.py:76-88`) → i to bez
ijednog studentovog klika.

### Zašto je to nalaz o VALJANOSTI, a ne o kodu

Ponašanje je **ispravno** za UI (svjež CTA po povratku na tab). Problem je što isti poziv
ostavlja **trag u tablici koja se čita kao mjera**.

🔴 **Evaluacija je asinkrona i nenadzirana** — studenti rade danima, iz vlastitih
preglednika, i **ostavljaju tabove otvorene**. Svaki povratak na takav tab (nakon 60 s)
generira redak. Zato:

- **broj redaka u `recommendations_log` NIJE broj preporuka koje je student vidio**, a
  pogotovo nije broj onih na koje je reagirao;
- svaka metrika oblika „izdane preporuke", „stopa prihvaćanja preporuke",
  „preporuka → attempt konverzija" ima **napuhan nazivnik/brojnik za nepoznat faktor**,
  koji ovisi o navici korisnika (koliko tabova drži otvoreno), ne o sustavu.

**Empirijski trag iz ove sesije:** tablica je narasla 75 → 89 redaka kroz nekoliko sati,
**svi pod `user_id = 1` (admin), bez ijednog attempta** (`attempts` za tog korisnika
nepromijenjen na 13). Sonda je isključila krivu atribuciju kao uzrok: registracija →
`/next-task` → novi redak nosi **ispravan** `user_id` novog korisnika. Dakle rast dolazi
iz refetcha otvorenog taba, ne iz buga.

### Što se NE radi

Ne gasi se `refetchOnWindowFocus` — to bi pogoršalo UI radi čistoće mjerenja, a mjerenje
nije razlog zbog kojeg aplikacija postoji. Ne dira se `staleTime`.

### Što treba u analizu rada

1. **Ne izvještavati sirovi `COUNT(*)`** iz `recommendations_log` kao „broj preporuka".
2. Ako metrika treba: brojati **distinct `(user_id, recommended_task_id)` parove**, ili
   vezati preporuku uz **attempt koji je unutar razumnog prozora slijedi** — oboje je
   analitička odluka, ne izmjena koda.
3. U ograničenjima rada navesti ovaj efekt uz ostale nalaze o valjanosti (#29/#31/#35/#45/#47).

⚠️ Isto vrijedi, u manjoj mjeri, za `agent_messages_log` (N-3): i on raste bez studentove
akcije, samo mu je uzrok drugi (nema `user_id`, pa ga nijedan cleanup ne dohvaća).

---

## 🔒 DOC — dopuna politike (2026-08-10, 1C-zatvaranje)

### Tvrdnja „X nema potrošača" mora biti dokaz o UČINKU, ne o imenu

**Grep po imenu tokena je nepotpun dokaz** kad token može biti posredovan:

| posredovanje | primjer |
|---|---|
| **alias** | `--font-heading: var(--font-sans)` — potrošač piše `font-heading`, a token koji stvarno djeluje je `--font-sans` |
| `@theme` / `@theme inline` mapiranje | `--color-neutral: var(--neutral)` → utility se zove `text-neutral`, deklaracija `--neutral` |
| shadcn registry setup | komponenta iz paketa nosi klasu koju projekt nikad nije napisao |
| dinamičan pristup | `VERDICT_META[verdict].soft`, `buttonVariants({ variant })` s varijablom |

**Povod.** U 4.7 je zapisano da `--font-heading` ima **nula potrošača**. Netočno — imao ih
je **dva** (`ProgressHero.tsx:26`, `ui/card.tsx:41`). Nisu se vidjeli jer je token bio
**alias** za `--font-sans`, pa nije imao **učinak**; grep po imenu ih je promašio. Čim je
alias dobio vlastitu vrijednost, display font se automatski proširio na sve naslove
kartica — širi doseg nego što je commit tvrdio.

🔴 **Ista klasa kao #39** (guard netestiran u oba smjera): alat kalibriran za jedan smjer
ne štiti. Grep po imenu nalazi ono što se **zove** kao token, a ne ono što ga **doseže**.

### Što se traži kao dokaz

1. **Za živ token:** izgrađeni CSS (`frontend/dist/assets/index-*.css`) — postoji li
   `var(--token)` uporaba i je li generirana ijedna utility klasa. Tailwind emitira
   utility samo ako je niska u izvoru, pa odsutnost klase **jest** dokaz.
2. **Za obrisanu stavku:** `git show <commit>^:<put>` → izvuci **svaki** identifikator koji
   je nosila (izvozi, `data-slot`, `group/`, `peer/`), pa `git log -S` po svakom kroz
   **cijelu** povijest.
3. **Za dinamičan pristup:** pročitati sva mjesta koja objekt konzumiraju i provjeriti
   ima li spreada, destrukturiranja ili računatog ključa.

⚠️ **Prisutnost klase u `dist` NIJE dokaz dosežnosti koda.** Tailwind emitira klasu čim je
niska u izvoru — i iz mrtvog koda. `.bg-correct-soft` je u `dist`, ali dolazi iz
`FeedbackPanel`/`TaskPage`, ne iz `verdict-ui.ts` `soft` polja, koje i dalje nitko ne čita.

### Re-verifikacija cijele 4.7 ovom metodom (2026-08-10)

| stavka | metoda | ishod |
|---|---|---|
| `--sidebar-primary` (+`-foreground`), **obrisan** | `git log -S` kroz cijelu povijest | niska `sidebar-primary` **nikad** nije postojala izvan `index.css` (3 commita, svi samo `index.css`) → brisanje ispravno ✅ |
| `ui/field.tsx`, **obrisan** | `git show` + 15 identifikatora (10 izvoza, `data-slot`, `group/`, `peer/`) | svi postoje **samo** u toj datoteci, od `eae9967` do brisanja; 0 `data-slot="field*"` i 0 `group/field` izvan nje → brisanje ispravno ✅ |
| `--neutral`, `--neutral-soft` | `dist` CSS | 1 deklaracija, **0** `var()`, **0** utility ✅ |
| `--duration-reward` | `dist` CSS | 1 deklaracija, **0** utility ✅ |
| `verdict-ui.ts` `soft` | čitanje jedinog konzumenta | `AttemptRow.tsx:35-52` čita `icon`, `border`, `chip`, `label` — **nikad `soft`**; nema spreada ni računatog ključa ✅ |
| `variant="destructive"` | `buttonVariants` indirekcija | izvezen, ali **nigdje importan** izvan `button.tsx`; `variant` je tipiziran `VariantProps`, pa bi potrošač morao napisati literal — 0 pogodaka ✅ |
| `--accent`, `--accent-foreground`, `--sidebar-foreground`, `--chart-3/4/5` | `dist` CSS | svi: 1 deklaracija, **0** `var()`, **0** utility ✅ |

**Nijedna obrisana stavka nije imala stvarnog potrošača.** Revert nije potreban.

---

## #55 🔴 STRUKTURNI: projekt ima instrument za VRIJEDNOSTI, ne za UČINAK

**Status:** 🔴 zatečeno, strukturno · zapisano 2026-08-11 (zatvaranje 4.7) ·
klasa: 🔒 DOC + **nalaz za rad**

### Tvrdnja

`scripts/a11y/` mjeri **boje i kontraste** — i to dobro, do razine ΔE i alpha-kompozita.
**Ništa u projektu nikad nije mjerilo vrijeme, dosežnost ni izvršenje.** Zato su tri
kvara iste klase preživjela po nekoliko faza: svaki je bio *deklariran ispravno* i
*neprovjeren u učinku*.

| # | što je deklarirano | što se stvarno događalo | koliko dugo |
|---|---|---|---|
| `--font-heading` (4.7-r2) | „token ima 0 potrošača" | imao ih je **dva**; alias `var(--font-sans)` nije imao **učinak**, pa ga grep po imenu nije vidio | od uvođenja do 1C t.0a |
| `--duration-*` (**N-18**, 4.1b → 4.7) | tokeni 160 / 240 / 400 / 700 ms + klase `duration-*` na ~10 mjesta | klase se **nisu generirale** (imenovana trajanja nisu TW v4 namespace), varijable su tree-shakeane → **svaka tranzicija je radila na TW defaultu 150 ms** | **tri faze** |
| **#23** `dml=False` (Faza 2 → 4.4-0d) | evaluator podržava DML | hardkodirana zastavica → svaki INSERT/UPDATE/DELETE „permission denied"; **nikad pokriveno testom** | tri faze |

### Zajednički obrazac

U sva tri slučaja **izvor je bio točan, a izlaz nije postojao**. Alat koji čita `index.css`
i računa kontrast po definiciji ne može uhvatiti nijedan od njih: on gleda *što piše*, ne
*što se izvrši*. Grep po imenu identifikatora nasljeđuje istu slabost — nalazi deklaraciju,
ne učinak.

**Dokaz učinka ima tri oblika, i nijedan nije grep:**
`getComputedStyle` nad živim elementom (vrijeme, primijenjena svojstva) · pikselno mjerenje
snimke (vidljivost) · test koji izvrši put (dosežnost, #23).

### 🔴 Posljedica za sve dosadašnje motion gateove

`/review-animations` je do 2026-08-10 pokretan nad sustavom u kojem su **sva trajanja bila
150 ms**. Svaki raniji prolaz (4.3, Task screen) odobrio je dakle *drugi* sustav od onoga
koji je bio dokumentiran. Ponovljena provjera nakon N-18 popravka (2026-08-11) mjeri
stvarne vrijednosti: nav 0,16 s · kartica 0,24 s · ulazna animacija 0,40 s · panel ocjene
0,24 s · XP zraka 2 s.

### Za rad

Ovo je nalaz o **metodologiji verifikacije**, ne o CSS-u. U raspravi o ograničenjima
implementacije navodi se da je projekt imao mjerni instrument za jednu dimenziju (boja) i
nijedan za ostale (vrijeme, dosežnost, izvršenje), te da su upravo u tim dimenzijama
kvarovi preživjeli najdulje — po tri faze. To je provjerljiva, samokritična tvrdnja s tri
primjerka, a ne opće mjesto o „važnosti testiranja".

---

## #56 🟡 ΔE prag za skale razina: 0,05 je projektni, 0,10 je bio ad hoc

**Status:** 🟡 odlučeno 2026-08-11 (zatvaranje 4.7) · **odluka: zadržavaju se sadašnje
hue rampe uz dokumentirani prag 0,05** · klasa: 🔒 DOC

### Što je bilo sporno

U recenzijskom prolazu postavljen je kriterij **ΔE ≥ 0,10** za svaku točku tier i
difficulty rampe prema svim ostalim skalama. Pri mjerenju je šest parova palo ispod njega.
🔴 **Taj prag NIJE projektni.** Dokumentirani prag kolizije u ovom sustavu je **0,05**
(MASTER §2.7, `pairs.py`, sve dosadašnje odluke o paletama). Prag 0,10 pojavio se prvi put
u toj recenziji, kao ad hoc kriterij, i primijenjen je retroaktivno na skalu koju nijedna
ranija faza nije po njemu mjerila.

### Zamrznuta skala nije prolazila ni taj prag

Izmjereno nad skalom **prije** rampi (jednohuena, 4.1b → 4.7-r2):

| | zamrznuta skala | sadašnje rampe |
|---|:---:|:---:|
| min ΔE prema skalama | 0,1101 (`tier-easy × mastery-25`) | **0,0643** (`difficulty-beginner × mastery-0`) |
| min ΔE susjednih razina | **0,0583** | 0,0588 |
| parova ispod 0,10 | **3** | 6 |

Dakle prag 0,10 nikad nije bio svojstvo ovog sustava; zamrznuta skala je i sama imala tri
para ispod njega i susjede na 0,0583.

### 🔴 Regresija se ne prešućuje

Rampe **jesu lošije na osi „prema skalama"**: `difficulty-beginner × mastery-0` pao je s
**0,1101 na 0,0643**. Zauzvrat su bolje na osi „susjedne razine" (razina se sada čita iz
tona, ne iz svjetline) i unakrsno tier×difficulty (**0,3754** zbog razdvajanja registrom).
Sve je iznad projektnog praga 0,05.

### Kolizija je uz to teško dosežna na zaslonu (mjereno)

`mastery-0` je pojas p(L) < 0,125. Iz BKT parametara po tieru (`bkt/parameters.py`) donja
granica p(L) uz uzastopne netočne odgovore je:

| tier | P(L₀) | donja granica | `mastery-0` dosežan? |
|---|:---:|:---:|:---:|
| easy | 0,30 | **0,3358** | ne |
| medium | 0,15 | **0,2286** | ne |
| hard | 0,05 | **0,1200** | da (usko) |

A `difficulty-beginner` badge nosi **isključivo modul „Osnove SELECT-a"**, koji ima **samo
easy koncepte** (upit nad `modules × concepts`). Agregatna traka kartice je pri 0/N
nevidljiva (fill je izvan trake), a već pri 1/7 = 0,143 prelazi u `mastery-25`.
**Zaključak: taj par se ne može pojaviti unutar iste kartice.** Na istom zaslonu je moguć
samo kao tanka traka u drugoj, proširenoj kartici — v. presudu t.1 u wrapupu.

### PRIJEDLOG F — izračunat kandidat za Fazu 6 (da se ne izvodi ponovno)

Pretragom prostora (uz uvjete: monotone rampe, očuvan registar, hue izvan chrome pojasa
272–288, `hard` ostaje magenta a ne crvena, sve u sRGB gamutu, tekst na fillu ≥ 4,5) nađen
je skup u kojem **svi parovi prolaze ΔE ≥ 0,10**, minimum **0,1023**:

```css
--tier-easy:                oklch(0.80 0.100 255);  /* tamni tekst 10,62 */
--tier-medium:              oklch(0.70 0.160 300);  /* tamni tekst  6,99 */
--tier-hard:                oklch(0.74 0.190 335);  /* tamni tekst  7,85 */
--difficulty-beginner:      oklch(0.25 0.040 205);  /* svijetli tekst 13,60 */
--difficulty-intermediate:  oklch(0.32 0.100 285);  /* svijetli tekst 11,26 */
--difficulty-advanced:      oklch(0.41 0.130 320);  /* svijetli tekst  8,13 */
--difficulty-expert:        oklch(0.50 0.155 355);  /* svijetli tekst  5,63 */
--difficulty-cross-module:  oklch(0.22 0.020 300);  /* svijetli tekst 14,95 */
```

Susjedne razine: tier 0,1516 / 0,1162 · difficulty 0,1229 / 0,1171 / 0,1265.
Najbliža skala: `tier-easy × mastery-75` 0,1023 · `difficulty-beginner × mastery-0` 0,1656.
**Ne primjenjuje se u 4.7** (pred deploymentom se paleta ne dira), nego stoji kao gotov
kandidat za Fazu 6.

---

## #57 🔴 STRUKTURNI: test pisan prema PROMATRANOM ponašanju zaključava kvar kao specifikaciju

**Status:** 🔴 zatečeno · otkriveno 2026-08-11 pri popravku N-11 · klasa: 🔒 DOC +
**nalaz za rad**

### Što se dogodilo

Smoke suite (1B) tvrdio je da CTA nakon predaje **mora biti `link` „Sljedeći zadatak"**.
Ta je tvrdnja bila točan opis onoga što je aplikacija radila — i **istovremeno opis kvara**:
kad preporučivač vrati isti zadatak, `Link` na istu rutu ne remounta keyed `TaskView`, pa
klik ne radi ništa (**N-11**). Isti prolaz (1B) koji je N-11 **otkrio** i zapisao kao nalaz,
**zaključao ga je kao očekivano ponašanje** u asertaciji. Popravak N-11 zato je oborio
vlastiti smoke test — i to je bio jedini razlog zbog kojeg se kvar više nije mogao tiho
vratiti.

### Uzrok

Suite je pisan **promatranjem** onoga što aplikacija radi, a ne izvođenjem iz onoga što bi
trebala raditi. Za smoke test to je djelomično legitiman postupak (cilj mu je „lanac je
prošao", ne „ponašanje je ispravno") — ali granica je prijeđena kad je promatrana
implementacijska činjenica (*„CTA je element `a` s atributom `href`"*) postala asertacija.

### Ista klasa, četvrti primjerak

Uz #55 (`--font-heading`, `--duration-*`, #23) ovo je četvrti primjerak istog obrasca:

> 🔴 **Instrument kalibriran prema zatečenom stanju potvrđuje zatečeno stanje.**

- **#39** — guard testiran samo u jednom smjeru: test je potvrđivao da radi ono što radi.
- **N-18** — `/review-animations` proveden nad sustavom na 150 ms: gate je odobrio ono što
  je zatekao, a ne ono što je dokument propisivao.
- **`--font-heading`** — grep po imenu potvrdio je ime, ne učinak.
- **ovaj nalaz** — asertacija je snimila zatečeni DOM kao ugovor.

### Za rad

U raspravi o metodologiji: automatizirana provjera **nije neovisan svjedok** ako je njezino
očekivanje izvedeno iz promatranja sustava koji ispituje. Razlika je operativna, ne
filozofska — provjerljiva je pitanjem *„je li ovo očekivanje izvedeno iz zahtjeva ili
prepisano s ekrana?"*. Test sada provjerava **obje grane ishoda** (drugi zadatak → link i
navigacija; isti zadatak → gumb i vidljivo čišćenje panela), dakle ugovor, ne zatečeni DOM.

---

## #58 🟡 VALJANOST: retry bez trenja može promijeniti raspodjelu uzastopnih predaja

**Status:** 🟡 zabilježeno 2026-08-11 · **ponašanje se NE mijenja** · stavka za analizu evala

Popravak N-11 uklonio je trenje iz ponovnog pokušaja na istom zadatku: umjesto navigacije
koja ne radi ništa, korisnik dobiva gumb koji čisti panel, a **SQL ostaje u editoru**
(svjesna odluka — v. N-11). Posljedica koju treba očekivati u podacima:

- više **uzastopnih predaja istog zadatka** po korisniku,
- više BKT ažuriranja iz **istog dokaza** (ista pogreška predana više puta),
- veći `attempt_number` → **manji XP bonus** (`FIRST_ATTEMPT_BONUS` pada na bazu),
- interakcija s **#29** (evaluacija je rezultat-bazirana i ne razlikuje ekvivalentne
  formulacije) i **#16** (saturacija P(L)).

**Za analizu:** izračunati udio identičnih uzastopnih `submitted_query` po korisniku i
usporediti ga s brojem različitih pokušaja; ako je udio visok, interpretacija „broj
pokušaja do rješenja" mora to uzeti u obzir. **Ponašanje se ne mijenja** — trenje u
sučelju nije prihvatljiv način prikupljanja čišćih podataka.

---

## #59 🔴 VALJANOST: informacija sudionika ne pokriva slanje podataka vanjskoj usluzi

**Status:** 📌 **ODLUKA 2026-08-14: zabilježena privola se NEĆE uvoditi** — informacija
ostaje kakva jest, `USE_LLM_HINTS` ostaje uključen. Zabilježen 2026-08-11.
V. „Odluke o nerješavanju" na dnu dokumenta.

Tekst koji sudionik vidi prije registracije (`participation.ts`) opisivao je što se
**bilježi** — SQL upiti, ishodi pokušaja, procjena znanja — ali ni jednom riječju nije
spominjao da bi išta od toga moglo **napustiti sustav**. Do Faze 5 to je bilo točno:
jedini LLM poziv bio je offline generiranje zadataka, bez ijednog studentovog podatka.

HintAgent to mijenja. Zahtjev za savjetom šalje podatke o studentovom pokušaju vanjskoj
usluzi (Anthropic, Claude API). Sudionik koji je pristao na tekst bez te tvrdnje **nije
pristao na to**.

### Što je učinjeno

Umetnut odlomak (indeks 2, odmah iza bilježenja) koji granicu izriče u **oba** smjera:

- **ne izlazi:** tekst upita,
- **izlazi:** opis zadatka, koncept, vrsta greške i njezini **brojčani pokazatelji**
  (npr. broj vraćenih redaka), procjena znanja koncepta,
- **ne izlazi ništa** bez izričitog zahtjeva za savjetom.

Granica nije nagađana — izmjerena je nad živom bazom (§A1 plana 5.0). Mjerenje je i
suzilo prvotnu namjeru: `execution_error` `detail` nosi **doslovni redak upita** (jedan
uzorak sadrži i zaostali komentar iz editora), a `wrong_columns` nabraja **studentove
aliase**. Oba su izbačena iz onoga što se šalje.

### Zašto ostaje otvoren

Odlomak informira, ali **ne bilježi suglasnost**. Nosilac pristanka je i dalje čin
registracije, kao i dosad. Prije nego hint proradi u evalu treba odluka: je li informacija
dovoljna ili traži zaseban, bilježen pristanak (nova kolona → migracija).

### Srodno

- **#46** — brisanje pojedinog sudionika nije dokazano izvedivo; sada mu se pridružuje
  pitanje što je s podacima koji su već otišli vanjskoj usluzi.
- **#37**, **#40** — ista obitelj: obećanje prema sudioniku šire je od dokazanog
  ponašanja sustava.

### Za rad

Nalaz je primjer općenitijeg obrasca: **tekst suglasnosti stari zajedno s arhitekturom.**
Tvrdnja „sustav bilježi X" bila je potpuna dok je sustav bio zatvoren; dodavanje jednog
vanjskog poziva učinilo ju je nepotpunom a da nijedan njezin znak nije promijenjen.
Provjera „je li informacija sudionika još istinita?" mora biti stavka pri svakoj izmjeni
koja otvara novi izlazni kanal, ne pri ponovnom čitanju teksta.

---

## #60 🔴 STRUKTURNI: preporuka koncepta ovisila je o fizičkom poretku redaka u heapu

**Status:** 🔴 popravljeno · grana `fix-recommender-determinizam` · blokator za **deployment**

> **Numeracija:** #59 je zauzet na grani `faza-5-hintagent` (informacija sudionika). Ovaj
> nalaz uzima #60 da se dvije grane ne sudare pri spajanju.

### Lanac, svaki korak izmjeren

1. `load_concept_code_map` ([db_helpers.py](../backend/agents/db_helpers.py)) čitao je
   `select(Concept.code, Concept.id)` **bez `ORDER BY`** → redoslijed = fizički poredak
   redaka u heapu.
2. `build_mastery_snapshot` gradi dict **tim** redoslijedom.
3. `PrologEngine.inject_mastery` asertira `mastery/3` činjenice redoslijedom dicta
   (`assertz` dodaje na kraj).
4. `recommend_next/2` ([rules.pl:57-59](../backend/prolog/rules.pl)) zove
   `weak(User, Concept)` s **nevezanim** `Concept`, pa Prolog backtracka po činjenicama
   redom asercije — i **reže prvim rješenjem** (`!`).

⇒ **Prvi weak koncept s ispunjenim prereq-ima u fizičkom poretku pobjeđuje.**

Lanac je potvrđen u tri različita fizička poretka; svaki je unaprijed predvidio ishod:

| fizički poredak | prvi kandidat | `recommend()` vratio |
|---|---|---|
| seed poredak | `scalar_subquery` | `scalar_subquery` |
| abecedno (`code ASC`) | `cross_join` | `cross_join` |
| obrnuto po `id` | `scalar_subquery` | `scalar_subquery` |

### Što mijenja fizički poredak

- 🔴 **`run_seed()` pri SVAKOM bootu** — `make db-seed` → `on_conflict_do_update` nad svih
  30 koncepata ([seed.py:60-71](../backend/app/db/seed.py)). Svaki `UPDATE` piše novu
  verziju tuplea. **Zato je ovo blokator deploymenta, ne test-only smetnja.**
- `test_seed.py::test_seed_is_idempotent` — isto, dvaput po pokretanju suitea.
- `VACUUM FULL`, `CLUSTER`, restore iz dumpa, autovacuum.

### 🔴 POVUČENO: „trag u produkcijskim podacima" (ispravak 2026-08-12)

**Prvotna verzija ovog odjeljka tvrdila je da `recommendations_log` pokazuje kad je drift
počeo. Ta tvrdnja je provjerena i NE STOJI. Povlači se u cijelosti.**

Tvrdilo se: tri tjedna samo `inner_join` (176×) i `select_basic` (20×), a pet novih
koncepata (`group_by`, `cross_join`, `update`, `where_filter`, `null_handling`) pojavljuje
se prvi put 2026-08-11 — „istog dana kad je heap opetovano prepisivan".

**Što provjera pokazuje.** Svih 17 redaka s tim konceptima pripada **jednom stvarnom
korisniku** (`user_id 565`), u neprekinutoj sesiji 11:52–12:01, i svaka preporuka slijedi
**neposredno iza pokušaja koji je promijenio znanje**:

| vrijeme | pokušaj | preporuka odmah nakon |
|---|---|---|
| 11:56:39 | riješen `inner_join` (task 44) | `cross_join` |
| 11:57:16 | riješen `cross_join` (task 39) | `where_filter` |
| 11:59:04 | riješen `order_by` (task 13) | `group_by` |
| 12:01:10 | riješen `group_by` (task 30, 7. pokušaj) | `null_handling` |
| 12:01:30 | riješen `null_handling` (task 1) | `update` |

`skill_mastery_history` to potvrđuje: u istom prozoru `inner_join` 0,217 → 0,644,
`group_by` 0,217 → 0,657, `where_filter` 0,728 → 0,987. **Znanje se stvarno mijenjalo, pa
je preporuka legitimno pratila** — to je sustav koji radi, ne kvar.

Vremenski se ni ne poklapa: redci su 11:56–12:01, a opetovano prepisivanje heapa (pokretanja
suitea) dogodilo se ~5 sati kasnije.

**Ispravna tvrdnja:** `recommendations_log` **niti potvrđuje niti opovrgava** utjecaj kvara
na stvarne korisnike. Nedostatak raznolikosti kroz tri tjedna govori o slabom korištenju, ne
o stabilnosti preporuke.

🔴 **Kvar i popravak time NISU dovedeni u pitanje** — dokazani su izravnim pokusom (tri
fizička poretka, svaki unaprijed predvidio ishod; test pada 5/5 na starom kodu, prolazi 5/5
na novom). To mjerenje ne ovisi ni o jednom retku iz `recommendations_log`.

**Pouka, ista obitelj kao #55 i #57:** podudarnost datuma je uzeta kao uzročnost jer je
*potvrđivala* zaključak do kojeg je pokus već došao. Pokus je bio valjan i bez nje; „trag"
je dodan kao ukras, a ukras je bio netočan. Dokaz koji ništa ne nosi svejedno može biti
kriv, i onda kvari nalaz koji je inače dobar.

### Popravak

Kanonski `ORDER BY modules.order_index, concepts.order_index, concepts.id` — pedagoški
slijed koji rad ionako tvrdi. Par `(modules.order_index, concepts.order_index)` je
**izmjereno jedinstven** nad svih 30 koncepata (0 sudara), pa `id` nikad ne odlučuje;
stoji da poredak ostane totalan ako se doda koncept koji sudari.

### 🔴 Dva testa koja su padala bila su POŠTENA

`test_advanced_recommends_inner_join` i `test_concurrent_recommends_serialized_and_correct`
tvrdili su `inner_join` — što je i **kanonski** ishod (modul 3, prije `cross_join` u istom
modulu, prije `update`/`delete` u modulu 4 i `scalar_subquery` u modulu 5) i ono što je
produkcija radila 176 puta kroz tri tjedna. Nisu bili prestrogi ni „zaključali zatečeno
stanje" — mjerili su ispravnu stvar, samo su padali tek kad bi se poredak slučajno
pomaknuo. **Nijedan nije prilagođen.**

To je razlika prema **#57**: ondje je test kodirao promatrano ponašanje kao ugovor; ovdje
je test kodirao ispravan ugovor, a sustav ga je povremeno kršio.

### Novi test tvrdi DETERMINIZAM, ne konkretan koncept

`test_recommender_determinizam.py` forsira dva suprotna fizička poretka (`code ASC` i
`code DESC`) i traži isti ishod. Pada 5/5 na starom kodu (`cross_join` vs `update`),
prolazi 5/5 na novom.

Dva pokušaja prije njega su odbačena i vrijedi ih zabilježiti:

1. **Prepisivanje po fiksnom ključu** (`ORDER BY id DESC`) je **idempotentno** nad heapom
   koji je već u tom poretku → drugi poziv ne mijenja ništa, test postaje prazan hod.
2. **`UPDATE ... SET name = name` uopće ne jamči poredak.** Uz 30 redaka u dvije stranice
   PostgreSQL nove verzije smjesti u slobodan prostor **iste** stranice (HOT), pa se
   poredak jedva pomakne. `CLUSTER` prepisuje heap u poretku indeksa, bez iznimke.

Oba su otkrivena jer test nosi **guard koji tvrdi da je perturbacija stvarno djelovala**.
Bez njega bi test „prolazio" ne ispitavši ništa — isti obrazac kao #55.

### Za rad

Nedeterminizam nije bio u algoritmu nego u **pretpostavci o redoslijedu koju SQL ne daje**.
`SELECT` bez `ORDER BY` ne jamči ništa, ali ga vrati u poretku koji izgleda stabilno dok se
tablica ne prepiše — pa se pretpostavka nikad ne opovrgne u razvoju. Simbolička jezgra
(Prolog) je pritom radila točno ono što je specificirana raditi; kvar je nastao na
**granici** simboličkog i relacijskog sloja, gdje se uređeni ulaz tiho pretvorio u
neuređeni. To je nalaz o hibridnoj arhitekturi, ne o Prologu.

### Odluka o promjeni ponašanja (2026-08-12)

Popravak **mijenja preporuku** za profil `partial (M1 mastered)`. Odluka korisnika:
**prihvaćeno.**

| profil | prije (ovisilo o heapu) | poslije (determinističko) |
|---|---|---|
| `weak` (bez mastery retka) | `select_basic` | `select_basic` |
| `partial` (M1 mastered) | `cross_join` ili `update` | **`group_by`** |
| `unlock` (M1+M2+null_handling) | `cross_join` ili `update` | **`inner_join`** |

Za `weak` i `unlock` popravak reproducira ono što je produkcija radila tri tjedna
(`select_basic` 20×, `inner_join` 176×). Za `partial` **nije postojala stabilna polazna
vrijednost** — pokvareni kod je davao `cross_join` ili `update` ovisno o stanju heapa, pa
se nije imalo što sačuvati. `group_by` je modul 2, odmah iza M1, dakle traženi pedagoški
slijed.

**Za analizu evala.** ~~Preporuke od 2026-08-11 izuzeti jer nisu signal o studentima nego o
poretku redaka.~~ **Povučeno istog dana kad i „trag u produkcijskim podacima" (v. gore) —
uputa je bila pogrešna i bacila bi ispravne podatke.** Sesija 2026-08-11 11:52–12:01 je
uredna: svaka preporuka slijedi pokušaj koji je promijenio `p_l`.

Ono što **ostaje** istinito i mora se navesti: sve preporuke zabilježene **prije** merge-a
ovog popravka nastale su dok je kvar bio aktivan, pa se **za nijednu pojedinačnu ne može
tvrditi** da je bila kanonska. Kvar se očituje samo kad više kandidata dijeli status
`weak` + `prereqs_met`; kad je kandidat jedan, poredak ne mijenja ništa. Zato: ne izuzimati
podatke, nego uz svaku tvrdnju o preporukama iz tog razdoblja navesti da determinizam nije
bio zajamčen.

---

## #61 🔴 VALJANOST: `submitted_query` se trajno pohranjuje u `agent_messages_log`

**Kad:** otkriveno 2026-08-12, pri exit mjerenju Faze 5.1 (kriterij: „log ne sadrži
`hint_text` ni `submitted_query`").

**Što je izmjereno** (živi `tutor_main`, ne čitanje koda):

| mjera | vrijednost |
|---|---|
| redaka u `agent_messages_log` | 7480 |
| redaka koji sadrže `submitted_query` | **1568** |
| najstariji takav redak | **2026-07-20** |
| redaka od `hint@localhost` | 68 |
| od toga sa `submitted_query` | **0** |

**Što to znači.** FIPA lanac `POST /attempt` prosljeđuje payload sa studentovim upitom, a
`TutorAgent.log_message` upisuje `content` doslovno. Doslovni SQL koji je student napisao
time završava u trajnoj tablici koja se **ne briše** i **ulazi u izvoz**.

🔴 **Ovo NIJE uveo HintAgent.** Hint put je izmjeren i čist: van ide `{user_id, task_id}`,
natrag `{task_id, source, hint_len}`. Nalaz je zatečen i star tri tjedna; Faza 5.1 ga je
samo **otkrila**, jer je prvi put netko pretražio sadržaj tog loga umjesto da čita kôd.

**Zašto je relevantno za rad:**
- `export_eval_data.py` pseudonimizira `user_id`, ali sadržaj `content` ne dira — pseudonim
  ne pomaže ako je uz njega doslovni rad koji je osoba napisala,
- privola iz 5.0 §D govori o obradi podataka o učenju; trajna pohrana doslovnog uratka je
  jača tvrdnja od one koju je sudionik pročitao,
- ista je logika po kojoj je `hint_text` u 5.1 redigiran — kriterij je već postojao, samo
  se primjenjivao na jedan put a ne na oba.

**Nije popravljeno u 5.1** jer bi tražilo izmjenu `base.py` i `coordinator.py`, koji su
odlukom 8 plana 5.1 zamrznuti. **Status: OTVORENO** — Faza 6.

**Što se NE tvrdi:** da su podaci ikamo procurili. Log je lokalna baza u Dockeru. Tvrdi se
samo da pohrana postoji, da je trajna, i da je šira od onoga što je sudioniku rečeno.

---

## #62 🔴 STRUKTURNI: druga istovremena predaja se ODBACUJE, ne odgađa

**Kad:** izmjereno 2026-08-12, kontrolnim mjerenjem koje je N-22 tražio.

**Nalaz.** `POST /attempt` podnosi **točno jednu istovremenu predaju**. Svaka koja stigne dok
je Coordinator FSM u toku biva **trajno odbačena**: student čeka 15 s, dobije 504
`orchestration_timeout`, i **redak u `attempts` nikad ne nastane**.

**Izmjereno** (bez hintova; `coordinator.py` byte-identičan `origin/main`-u):

| K istovremenih | uspjeha po rafalu |
|---|---|
| 2 | **1,0** |
| 3 | **1,0** |
| 4 | **1,0** |
| 8 | **1,0** |

Dvanaest rafala, dvanaest uspjeha — nikad dva. Rafal od 4 dao je **1 redak** u `attempts`.
Raspodjela je bimodalna: uspjeli ~120 ms **na svakoj razini** (125 ms pri n=1, 123 ms pri
n=8), neuspjeli 15 012–15 070 ms. Latencija uspjelih **ne raste** → nije zasićenje nego
gubitak.

**Uzrok** ([coordinator.py:178-209](../backend/agents/coordinator.py#L178-L209)): drain-loop
`_recv_matching` odbacuje poruke s tuđim `correlation_id`-em. Invarijant
([coordinator.py:29-31](../backend/agents/coordinator.py#L29-L31)) tvrdi da je takva poruka
„nužno MRTVA … nikad buduća, pa je drop siguran". 🔴 Tvrdnja pada čim dva HTTP klijenta
predaju istovremeno. Komentar predviđa pad „ako se uvede dispatcher"; zapravo pada od Faze
3E.3.

**Dopune iz istrage (2026-08-12), grana `fix-coordinator-concurrency`:**

1. 🔴 **Kvar je lokaliziran u Coordinatoru.** `/next-task` (izravno gateway → Recommender)
   pod istim harnessom daje **K uspjeha za K = 2, 4, 8** — nula gubitaka. Latencije rastu
   stepenasto (87 → 291 ms pri K=8): red se formira i **prazni**. Razlika je strukturna:
   gateway je **dispatcher** (`dict[cid → Future]`, ne čeka određeni cid), Coordinator je
   **stroj stanja s jednim utorom** (`self.agent._flow`, čeka točno jednu poruku).
2. **Gubitak nije potpuno tih** — ispravak ranije formulacije. Svaku poruku bilježe **oba**
   agenta (pošiljatelj nakon slanja, primatelj pri primitku), pa odbačena poruka ima **samo
   pošiljateljev redak**. Forenzika nad 874 tokova: **99** odbačenih u RECEIVE (svi
   2026-08-12, iz ovih mjerenja), **0** redaka u `attempts` za njih. Postoji izvediv upit
   koji izgubljene predaje broji **retroaktivno**.
3. **Izloženo je točno jedno korisničko djelovanje.** Samo `submit-attempt` pokreće tok;
   `model-updated` i `recommend-next` su odgovori unutar toka. `/next-task`, `/run` i
   `/profile` Coordinator ne dodiruju. To jedno djelovanje nosi ocjenu, XP i BKT.
4. **Horizontalno skaliranje ne pomaže.** Više uvicorn radnika prijavilo bi se na Prosody
   **istim JID-om**, a `AgentBridge` je in-process dict — odgovor bi mogao stići radniku koji
   ne drži Future i ondje se tiho izgubiti. Ista klasa gubitka, teža za dijagnozu.
5. **Nijedan test ovo ne hvata, i to nije slučajno.** `test_cid_correlation_two_sequential_flows`
   u docstringu piše „Sekvencijalno jer FSMBehaviour serijalizira" — **ugrađuje ograničenje
   u dizajn testa**. `test_stale_message_guard_drops_foreign_cid` šalje stranu
   `model-updated` (mrtvu poruku — slučaj u kojem je invarijant ispravan), nikad strani
   `submit-attempt` (budući zahtjev — slučaj u kojem pada). Peti primjerak obrasca iz **#57**.

**Preporučen smjer:** korelacijski dispatcher po uzoru na `AgentBridge`
(`docs/fix-62-korak-0.md` §C.5). Zaobilaženje Coordinatora odbijeno — FSM orkestracija je
dio doprinosa rada, ne implementacijski detalj.

**Status: ✅ ZATVOREN** (2026-08-13, grana `fix-coordinator-concurrency`, commit `846f241`).

Popravak: FSM **po razgovoru**, s predloškom vezanim uz vlastiti `correlation_id`. SPADE
`dispatch()` isporučuje poruku svakom behaviouru čiji predložak matcha, pa je predložak
sam po sebi korelacijski router — ručni registry Future-a nije ni pisan. Prijem je izdvojen
iz FSM-a u `_Intake`: dok je bio stanje, jedan razgovor u tijeku značio je da se sljedeći
ne može ni primiti.

Uz to `MAX_CONCURRENT_FLOWS = 64` s **eksplicitnim** odbijanjem na granici (`refuse` +
`coordinator_busy` → HTTP 503, ne 504) — tiho odbijanje ondje bilo bi ovaj isti nalaz
reproduciran na drugom mjestu.

| mjerenje | prije | poslije |
|---|---|---|
| K=2,4,8 istovremenih predaja | **1** redak, bez obzira na K | **K** redaka i **K** odgovora |
| 20 studenata, tempo evala (~19 s) | ~13 % gubitka (procjena) | **60/60**, p95 197 ms |
| p95 pri K=1 (kontrola, ista sesija) | 123,6 ms | 124,2 ms — unutar devijacije |

Invarijanta iz `coordinator.py:29-31` **prepisana** i po prvi put vezana uz test koji ju
izvršava (`tests/test_coordinator_concurrency.py`). GATE 2 pao kao opis sustava.
Detalji: `docs/fix-62-63-wrapup.md`.

---

## #63 🔴 VALJANOST: odgovor se izgubi, a pokušaj OSTANE zabilježen

**Kad:** reproducirano 2026-08-12 (3/3), tijekom istrage #62.

🔴 **Zaseban kvar od #62** — isti simptom (504), druga uzročna veza, drugi popravak.
I **ne treba nikakav pad procesa.**

**Nalaz.** Kad evaluacija traje dulje od `DEFAULT_UPDATE_TIMEOUT = 5.0`
([coordinator.py:77](../backend/agents/coordinator.py#L77)), Coordinator odustaje i vraća
504 `evaluation_timeout`. Ali Evaluator je **već commitao** pokušaj (D6 garancija: commit
**prije** informa), a KnowledgeModel i Gamification rade dalje — pokreće ih Evaluatorov
inform, **neovisno o Coordinatoru**.

**Izmjereno** — `POST /attempt` sa `SELECT pg_sleep(6);`, sandbox `statement_timeout = 5 s`:

| pokušaj | HTTP | trajanje | redaka u `attempts` | BKT snapshotova |
|---|---|---|---|---|
| 1 | 504 `evaluation_timeout` | 5076 ms | **1** | **2** |
| 2 | 504 `evaluation_timeout` | 6620 ms | **1** | **2** |
| 3 | 504 `evaluation_timeout` | 5115 ms | **1** | **2** |

FIPA trag (isti `cid`): `knowledge → coordinator inform` stiže **36 ms nakon** što je
Coordinator već poslao `evaluation_timeout` gatewayu.

**Zašto nije rubni slučaj.** Sandbox `statement_timeout` je 5 s, a `DEFAULT_UPDATE_TIMEOUT`
5,0 s — svaki upit koji potroši statement timeout **nužno** prekorači i UPDATE prozor, jer
režija uvijek doda nekoliko ms. Nedostajući uvjet spajanja → kartezijev produkt → timeout je
**uobičajena greška u učenju SQL-a**. Takav student dobiva „sustav ne odgovara" dok mu se
pokušaj bilježi i BKT kažnjava; preda ponovno i bude kažnjen **dvaput za isti upit**.

**Što je izmjereno, a što izvedeno:** izmjereno je `xp_awarded = 0` (pokušaj je bio netočan).
Da isti prozor zadesi **točan** upit, XP bi bio dodijeljen dok student vidi grešku — to
slijedi iz koda (Gamification visi o Evaluatorovom informu), ali **nije izmjereno**, jer bi
tražilo točan upit sporiji od 5 s.

**Posljedica za UI:** 504 danas pokriva dva ishoda koje sučelje ne razlikuje —
`orchestration_timeout` (ništa nije zabilježeno) i `evaluation_timeout` (zabilježeno je).
Tekst „Evaluacija je predugo trajala" netočan je za prvi slučaj. Prijedlozi u
`docs/fix-62-korak-0.md` §E.2.

**Status: ✅ ZATVOREN** (2026-08-13, commit `23e2046`).

Popravak ima dva dijela i nijedan sam ne bi bio dovoljan:

1. UPDATE prozor se **izvodi** iz sandbox granice
   (`DEFAULT_STATEMENT_TIMEOUT_S + 2`), ne postavlja kao vlastita konstanta — granica je
   zato dobila ime u `sandbox_runner.py`, da se veza vidi umjesto da se duplicira.
   🔴 Produljenje je postalo sigurno **tek nakon #62**.
2. Kad prozor ipak istekne, Coordinator **provjeri je li upisano** umjesto da pretpostavi
   da nije. Redak postoji → odgovara stvarnim ishodom (200); ne postoji → greška je
   istinita. Polazna crta je `max(attempts.id)` s prijema, ne vrijeme — usporedba po
   `created_at` mjerila bi aplikacijski sat protiv sata baze.

Podizanje same konstante bilo bi pomicanje praga, ne popravak; zato provjera.

**Izmjereno s produkcijskim konstantama:**

| upit | prije | poslije |
|---|---|---|
| `pg_sleep(4.9)`, **točan** | 504 + pokušaj + 2 BKT + **30 XP** | **200**, `is_correct=true` |
| `pg_sleep(5.2)`, prespor | 504 + pokušaj + 2 BKT | **200**, `error_type=timeout` |

Ne dira `persistence.py`, `evaluate-query` payload ni migracije; D6 netaknut.
Detalji: `docs/fix-62-63-wrapup.md`.

---

## #64 🔴 KVALITETA SAVJETA: hint za `row_mismatch` je nagađanje, i zna dati NETOČAN SQL

**Status:** 🟡 **OTVOREN.** Popravak payloada pokušan 2026-08-14 na grani
`fix-pred-deployment` pa **POVUČEN prije mergea** — v. niže.

**Isporučena je samo prompt-razina** (odluka korisnika 2026-08-14: pravi popravak čeka
Fazu 6): pravilo protiv curenja glasa modela, pravilo da se kod nedostatka podataka pita
umjesto da se pretpostavi, i 🔴 **pravilo 9 — NIKAD ne iznositi pravila o redoslijedu SQL
klauzula.** Zadnje gađa točno opaženu štetu: kvar nije bio neodređenost nego **netočna
tvrdnja o sintaksi** („prvo `LIMIT`, pa `ORDER BY`").

🔴 **Prompt-pravilo je SLABA mjera** i tako je i odabrano — ne jamči ništa, a mock ne vidi
kvalitetu savjeta. Odabrano je jer je jedino koje ne košta migraciju na zamrznutom backendu
tjedan prije evala, a šteta koju pokriva je jedini dokumentirani konkretan slučaj.

🔴 **Zašto NE „neka payload čita `ORDER BY` referentnog upita" (odbačeno 2026-08-14):** za
velik dio zadataka poredak **JEST rješenje** („prikaži 3 najskuplja proizvoda"). Reći
modelu „očekuje se silazno po cijeni" znači dati mu odgovor — što krši prompt pravilo 2
(nikad dio upita koji rješava zadatak), ne samo guard `test_expected_query_is_never_read`.
Prava informacija nije KOJI je poredak točan nego KOJE je VRSTE razlika (broj redaka /
poredak / skup); `sandbox_runner` to već razlikuje, ali dovođenje do hint puta traži novu
kolonu i migraciju.

🔴 **Zašto je povučen — izmjereno nad svih 80 aktivnih zadataka.** Ideja je bila izvesti
očekivani poredak iz `expected_result` (strogo monoton stupac). Poredak je detektiran u
**40** zadataka, a u **10** je PROTURJEČIO `ORDER BY`-u referentnog upita; još 2 zadatka
poredak uopće nemaju. Najgori oblik su višestruki ključevi (`ORDER BY prosjecna_ocjena
DESC, product_id ASC`): primarni ključ ima izjednačenja pa nije monoton, sekundarni jest —
pa bi se **tiebreaker proglasio poretkom**. Sužavanje na „točno jedan monoton stupac" ne
spašava: 4 od 24 i dalje proturječe. Uz to Python uspoređuje stringove po codepointu, a
`expected_result` je poredao PostgreSQL pod svojom kolacijom.

🔴 **Zašto je to gore od zatečenog stanja:** tvrdnja bi išla uz prompt-pravilo „osloni se
na dane podatke", pa bi model netočan poredak iznosio **sigurnije** nego kad nagađa —
sustavno umjesto povremeno.

🔴 **Odbačene i dvije uže varijante**, obje nakon čitanja stvarnih odgovora:
`expected_columns` (model sortiranu listu čita kao propisani REDOSLIJED stupaca; uz to
suvišan jer `row_mismatch` znači da su stupci točni) i `expected_row_count` (kad se brojevi
razlikuju `detail` ih već nosi; kad se poklapaju, navodi model na temu koja nije problem).

**Što treba za pravi popravak:** jedini pouzdan izvor poretka je `ORDER BY` referentnog
upita, a `hint_payload` ga po dizajnu ne smije ni spomenuti
(`test_expected_query_is_never_read`). Proširenje tog opsega je **odluka korisnika** —
klauzula je dio rješenja. Alternativa: evaluacijska jezgra emitira strukturiran podatak o
poretku umjesto stringa `Row 0 differs`.

🔴 **Što se NE tvrdi:** izvorni netočan SQL („prvo `LIMIT`, pa `ORDER BY`") **nije se
reproducirao** ni u jednom od 18 živih poziva. Bio je jedan opažen slučaj. Puna analiza:
[`docs/fix-pred-deployment-wrapup.md`](fix-pred-deployment-wrapup.md) §B.

🔴 **Ostaje otvoreno:** kvaliteta savjeta nema automatsku provjeru — `test_hint_route.py`
mocka LLM i gleda mehaniku, sadržaj ne gleda nitko. Zato su gornje dvije stavke uhvaćene
tek ručnim čitanjem odgovora.

**Kad:** izmjereno 2026-08-13, prvi prolaz kroz UI s uključenim `USE_LLM_HINTS` i živim
`ANTHROPIC_API_KEY` (5 stvarnih poziva, `claude-haiku-4-5`, `source='llm'`).

**Nalaz.** Predano `... ORDER BY id DESC LIMIT 3` umjesto `ASC` (dakle: točni stupci,
krivi poredak → `row_mismatch`). Model je vratio:

> „Tvoji stupci su ispravni, ali vrati se na redoslijed upita: prvo trebaš **WHERE ili
> LIMIT**, a zatim **ORDER BY**? Ponovi redoslijed klauzula u SELECT iskazu."

To **nije samo promašena dijagnoza** (problem je bio smjer sortiranja, ne poredak
klauzula) nego i **netočna uputa o SQL sintaksi**: `ORDER BY` ide **prije** `LIMIT`.
Student koji posluša savjet napiše upit koji ne parsira.

**Uzrok je strukturan, ne slučajan — i vidi se iz usporedbe s drugim tipom greške.**
`build_hint_payload` ([hint_payload.py:66](../backend/agents/hint_payload.py#L66)) šalje
najviše jedno od `error_detail` / `expected_columns` / `sqlstate`, po bijeloj listi:

| `error_type` | što payload nosi | kakav je savjet ispao |
|---|---|---|
| `wrong_columns` | **`expected_columns`** — rekonstruirani ključevi iz `expected_result` | **točan i konkretan**: „zadatak traži točno `id`, `name` i `country`" |
| `row_mismatch` | `error_detail`, a to je interni string tipa `Row 0 differs` | **spekulativan**; u jednom od dva mjerenja i netočan |

Studentov upit **namjerno** ne napušta sustav (selektivni B+, odluka 5.0), pa model nema
iz čega vidjeti da je razlika bila `DESC` vs `ASC`. Kad payload nosi tvrdu činjenicu,
savjet je dobar; kad nosi interni dijagnostički string, model **popuni prazninu
izmišljanjem**.

🔴 **Privatnosna odluka NIJE uzrok i ne treba je mijenjati.** Uzrok je što za
`row_mismatch` u payload ne ide ništa **strukturno o očekivanom rezultatu** — a to se dade
izvesti iz `expected_result`, koji sustav ionako ima, **bez ijednog znaka studentovog
upita**: npr. „očekuje se 3 retka, sortirano uzlazno po `id`" umjesto `Row 0 differs`.

**Zašto 5.1 ovo nije uhvatila.** `test_hint_route.py` mocka LLM u svakom testu (nula
potrošnje, ispravna odluka) i provjerava **mehaniku** — status, idempotenciju, kredit,
redigiranost loga. Ništa ondje ne gleda **sadržaj** savjeta, pa ni ne može. Kvar je
vidljiv tek na živom modelu, i to samo ako se pročita što je napisao.

**Opseg.** Pogađa `row_mismatch`, koji je najčešći „skoro točan" ishod i **jedini koji
nosi djelomičan XP** — dakle točno onaj trenutak u kojem je savjet najvredniji.

**NE popravlja se u 5.2.** Plan 5.2 izrijekom zabranjuje diranje `hint_agent.py` i
`/hint` rute, a ovo je izmjena payloada, dakle backend i vlastita grana. Zabilježeno
ovdje da ne ovisi o sjećanju.

**Usput uočeno, isti prolaz:** u jednom savjetu procurio je glas modela — „to znači da
**trebam reći** da `FROM` klauzula…". Prompt-level, ista grana kad se otvori.

## #65 🟡 Model vraća Markdown, a slot ga je prikazivao doslovno

**Kad:** izmjereno 2026-08-13, isti prolaz kao #64. ✅ **POPRAVLJENO isti dan.**

`hint_text` je išao u `<p>` neobrađen, pa je student čitao `**ograničiti broj redaka**`
i `` `FROM` `` sa zvjezdicama i backtickovima. Izmjereno: **2 od 4** živa savjeta nose
`**` ili `` ` `` (potvrđeno i upitom nad `hint_requests`).

Prompt Markdown **ne traži** — model ga dodaje sam. Popravak je zato na strani prikaza, ne
prompta (koji je u zamrznutom opsegu, v. #64): `hintSegments` / `hintParagraphs` u
`lib/hint.ts` prevode **samo** `**podebljano**` i `` `kod` `` u React čvorove.

🔴 **Nije Markdown parser i ne smije to postati.** Nesparen `*` ili `` ` `` ostaje
**doslovan znak** — provjereno na sedam ulaza, uključujući „3 * 4 = 12"; invarijanta je da
vraćanje graničnika u segmente reproducira normalizirani ulaz, dakle **nijedan znak se ne
gubi**. Renderira se kroz React čvorove, **nikad** `dangerouslySetInnerHTML`: tekst dolazi
od modela i ne smije moći unijeti oznake u DOM.

**Usput uhvaćeno mjerenjem, ne okom:** prva verzija `<code>` čipa imala je `text-xs`, što
uz root skalu od ~14 px daje **10,24 px** — najsitniji tekst na ekranu, i to na imenima
stupaca koja student mora **pročitati i utipkati**. Ista greška koju je već platio
`RegisterPage` (v. 🔒 politika iz #33). `text-xs` maknut → čip nasljeđuje `text-sm`
odlomka (12,8 px). Kontrast izmjeren nakon promjene: **17,23:1** (`#f3f4fe` na `#0e0f23`,
kompozitirano `bg-background/60` nad `bg-muted/40` nad `card`).

---

## 🔒 Odluke o NERJEŠAVANJU (2026-08-14)

Dva nalaza se **svjesno ne rješavaju**. Zapisano ovdje jer odluka da se nešto ne popravi
mora biti vidljiva jednako kao popravak — inače se za godinu dana čita kao previd.

### #46 — procedura brisanja pojedinog sudionika se NE gradi

**Odluka korisnika.** Ostaje kako jest: `agent_messages_log` nema `user_id`, pa se podaci
pojedinog sudionika (uključujući `submitted_query`) ne mogu obrisati po osobi; jedini put
je `TRUNCATE` cijele tablice u `prepare_eval_baseline.py`.

🔴 **Što ostaje OTVORENO unatoč ovoj odluci:** opcija (b) iz retka #46 — **preformulirati
tekst** na Profilu i u informaciji o sudjelovanju da ne obećava brisanje na zahtjev.
Odluka pokriva **mehanizam**, ne tekst. Dok tekst stoji nepromijenjen, sustav svakom
prijavljenom korisniku obećava nešto što ne može isporučiti, a to je copy-only izmjena,
ne inženjerski zadatak. **Za rad:** ovo se prijavljuje kao ograničenje obrade podataka,
uz #37 i #40.

### #59 — zabilježena privola za vanjsku uslugu se NE uvodi

**Odluka korisnika.** Nosilac pristanka ostaje **čin registracije**, uz tekst koji
sudionika **informira** da se podaci o pokušaju šalju vanjskoj usluzi (Anthropic). Zaseban,
bilježen pristanak tražio bi novu kolonu i migraciju; ne radi se.

Što je time prihvaćeno kao ograničenje: ne postoji zapis **tko je i kada** pristao, pa se
pristanak ne može ni dokazati ni povući po osobi. `USE_LLM_HINTS` ostaje uključen.

🔴 Ovo NE poništava mjeru koja već stoji: studentov **upit** ne napušta sustav (selektivni
B+, odluka 5.0) — šalje se opis greške, ne tekst rješenja.

**Za rad:** oboje se prijavljuje u poglavlju o ograničenjima, ne prešućuje. Odluka je
donesena svjesno i uz poznat mehanizam, što je razlika u odnosu na previd.

---

## #66 🔴 STRUKTURNI: zadatak je tvrdio o bazi nešto što baza ne radi, i to je preživjelo tri faze

**Kad:** 2026-08-14, grana `m6-plan-presence`. Otvorena da M6 dobije zadatke; mjerenje je
srušilo pretpostavku na kojoj je grana stajala.

### Što je zatečeno

TODO je tri dana stajao na tvrdnji „M6 je neevaluabilan jer jezgra ocjenjuje po rezultatu".
Tvrdnja je **točna, ali nije bila cijeli problem**.

| task | koncept | plan REFERENTNOG upita | opis zadatka tvrdi | ishod |
|---|---|---|---|---|
| 79 | `explain_plan` | 🔴 Seq Scan | „izvesti Index Scan" | deaktiviran |
| 80 | `explain_plan` | 🔴 Seq Scan | Index Scan | deaktiviran |
| 81 | `index_usage` | Bitmap Index Scan / `idx_orders_customer` | slaže se | **zadržan** |
| 82 | `index_usage` | 🔴 Seq Scan | Index Scan | deaktiviran |
| 83 | `index_usage` | Index Scan / `orders_pkey` | „koristi `idx_orders_customer`" | deaktiviran |

**Od pet zadataka zdrav je bio jedan.**

### Dva različita kvara, ne jedan

**(a) Tri zadatka gađaju premalu tablicu.** `customers` ima 200 redaka i 3 stranice.
Izmjereno: **Seq Scan 5.50 vs Index Scan 8.16** — planer indeks odbija jer je sekvencijalni
prolaz stvarno jeftiniji. `customers_email_key` postoji i upotrebljiv je (uz
`enable_seqscan=off` plan prelazi na Index Scan). 🔴 **Planer je u pravu, zadatak nije.**

**(b) Zadatak 83 ima prazan potpis.** Njegov `ORDER BY id LIMIT 1` dopušta planeru da
prošeta `orders_pkey` indeksom i stane. Posljedica:

```
REF  83 (customer_id = 5)     Limit, Index Scan, orders_pkey
ANTI 83 (CAST na TEXT)        Limit, Index Scan, orders_pkey    ← IDENTIČNO
```

Oba plana „koriste indeks", pa bi svaka provjera oblika „koristi li indeks" propustila
anti-pattern koji zadatak izrijekom zabranjuje. Ciljani `idx_orders_customer` referentni
upit **uopće ne dira**.

### Zašto je preživjelo tri faze

`sweep_task_integrity` provjerava da referentni upit reproducira `expected_result`. Za sva
tri pokvarena zadatka **redci se poklapaju savršeno** — kvar je isključivo u načinu
izvođenja, a njega nijedan gate nije gledao. Isti obrazac kao metodološki zaključak 4.7:
**instrument je mjerio vrijednosti, ne učinak.**

### Popravak — tvrdnja o planu se NE pohranjuje

Odbačeni su i nova kolona (`tasks.plan_assertion`) i konstanta s popisom po `source_id`:
prva je migracija sheme tjedan prije evala, druga stavlja sadržaj kataloga u evaluacijsku
jezgru gdje tiho zastari (klasa #45).

**Zadatak već nosi tvrdnju o planu — to je njegov `expected_query`.** Evaluacija zato
EXPLAIN-a **oba** upita u istom trenutku i uspoređuje potpise:

```
PlanSignature(uses_index: bool, index_names: frozenset, join_methods: frozenset)
```

Nema migracije; tvrdnja ne može zastarjeti (referentni upit i tvrdnja su isti objekt);
preživljava reseed sandboxa jer se obje strane mjere nad istim podacima.

🔴 **`index_names` nije kozmetika** — bez njega `uses_index` laže, i točno zbog toga
zadatak 83 nije bio uhvaćen prvom verzijom potpisa.

### Gate stabilnosti — izveden iz FLAKY TESTA, ne iz teorije

Prva verzija testa tvrdila je konkretan ishod za zadatak 79. **Prošla je izolirano a pala u
punoj datoteci.** Uzrok: rollbackani DML iz drugog testa ostavlja mrtve retke, `relpages`
naraste, cijena Seq Scana poraste i planer se prebaci na Index Scan. Ocjena bi ovisila o
tome je li autovacuum upravo prošao.

Izmjerena margina izbora plana (cijena alternative / cijena odabranog):

| upit | margina | stabilan |
|---|---|---|
| `customers WHERE email = …` (79/80/82) | **1.48x** | 🔴 NE |
| `orders WHERE customer_id = 42` | 1.00x | ✅ |
| `order_items WHERE order_id = 500` | 1.00x | ✅ |
| `orders ORDER BY order_date DESC LIMIT 10` | 1.00x | ✅ |
| spoj `orders × order_items` **bez** filtra | — | 🔴 NE |
| spoj `orders × order_items` **s** filtrom | — | ✅ |

Margina 1.00x znači da gašenje seq scana **ne mijenja cijenu** — indeks je izabran
bezuvjetno, nema ruba s kojeg bi se prebacio. `plan_is_stable` zato traži da potpis ostane
nepromijenjen pod `enable_seqscan=off` i `enable_hashjoin=off`. `enable_nestloop` NIJE u
gateu: on zabranjuje strategiju koju `explain_plan` uči, pa bi odbio upravo ono što treba
propustiti — zastavica koja zabranjuje cilj nije test stabilnosti nego test postojanja.

### Nizvodne posljedice

- **Kat. C maska uklonjena** iz `recommender_logic`. Dok M6 nije bio evaluabilan, maska
  0.99 bila je obrana od ćorsokaka; sada bi bila blokada (Prolog preskače koncepte iznad
  praga → zadaci nikad ponuđeni). **Subfloor je time prazan.**
- **`is_active` je eksplicitan po zadatku**, ne izveden iz koncepta (#19 kriterij je pao):
  neispravni su POJEDINI zadaci, a to koncept ne može izraziti. Razlog stoji uz zadatak
  (`deactivation_reason`) pa preživljava re-import.
- **Bedž `explorer` sada traži i M6** (kriterij je dinamičan). Provjereno **simulacijom**,
  ne rezoniranjem (poučak #25): savršen student posjeti module **0–6**, dakle bedž ostaje
  dostižan.
- Zadaci 79/80/82/83 se **ne brišu** — dokaz su nalaza i negativan primjer na kojem se gate
  provjerava (poučak #39).

### Za rad

Ovo je najčišći primjer granice rezultatske evaluacije u projektu: postoji cijela klasa
koncepata (izvedbeni plan, upotreba indeksa) gdje je **točan rezultat nužan ali ne i
dovoljan uvjet točnog rješenja**. Uz #29 (ekvivalentne formulacije) i #35 (ZPD escape) ide
u raspravu o konstruktnoj valjanosti. Dodatno: sandbox je namjerno malen zbog brzine, a ta
odluka **isključuje** dio gradiva — planer na 200 redaka ne bira indeks ni kad postoji.

---

## #68 🟡 `column_alias` je dobio zadatke koje preporučivač nikad ne nudi (ZPD escape, druga potvrda)

**Kad:** 2026-08-14, ista grana. Odluka korisnika bila je da `column_alias` dobije zadatke,
a `join_condition` ne.

**Izvedeno:** 3 ručno autorska zadatka. Koncept time ispada iz Kat. A
(`transversal_concepts` traži count == 0). Kako je modul 0, **ne hvata ga ni subfloor**
(traži modul ≠ 0) — ostaje bez ikakve mreže.

**Strah iz plana bio je pogrešan, a stvarni ishod drukčiji.** Plan je strahovao da će
koncept zapeti **ispod** praga i zaključati nizvodni `group_by`. Simulacija savršenog
studenta (46 zadataka):

| mjera | vrijednost |
|---|---|
| `column_alias` p_l | **0.9356** |
| `group_by` p_l | 0.99999 |
| je li `group_by` otključan | ✅ DA |
| koliko je puta `column_alias` **ponuđen** | 🔴 **0** |

🔴 **Koncept saturira IZNAD praga prije nego dođe na red.** Ima 4 sekundarna pojavljivanja,
BKT ažurira sve koncepte zadatka, a Prolog bira samo koncepte **ispod** praga. To je
**ERRATA #35 (ZPD escape) po drugi put**, sada na konceptu koji je zadatke dobio namjerno i
mjereno.

**Što to znači za isporuku:** tri nova zadatka **nisu mrtva** — `resolve_task_for_concept`
ih vraća, pa su dosežni klikom na redak koncepta u pregledu Modula (put iz #42/#43). Ali
kroz „Sljedeći zadatak" se ne nude. Razlika „dosežno navigacijom" vs „nuđeno preporukom"
zaključana je testom, da se stanje ne čita kao potpuna pokrivenost.

**Ne popravlja se.** Popravak bi tražio da BKT razlikuje primarna od sekundarnih
ažuriranja, što je izmjena ugovora `/mastery-history` i jezgre modela — isto što #35 već
navodi kao nemoguće bez novog polja.

**Za rad:** dodavanje zadataka konceptu s puno sekundarnih pojavljivanja **ne čini ga
podučavanim**. Nalaz je koristan jer je nastao iz namjernog pokušaja da se koncept pokrije,
pa je mehanizam potvrđen prospektivno, a ne samo retrospektivno kao u #35.

---

## #69 🔴 STRUKTURNI: smetnja sustava zapisana kao studentova greška

**Kad:** 2026-08-14, grana `m6-plan-presence`, pri reviziji nove `plan_unavailable` grane.

### Kako je izmjereno

Bez ijednog mocka. Umetnut je privremeni M6 zadatak čiji **referentni** upit gađa
nepostojeću tablicu, pa `EXPLAIN` nad njim pada stvarno. Student je predao upit koji točno
reproducira `expected_result` — dakle **objektivno ispravno rješenje**. Lanac je pravi
(`POST /attempt` → evaluator → knowledge → gamification → hint).

| pitanje | zatečeno |
|---|---|
| `attempts` redak s `is_correct=false` | 🔴 **DA** (`error_type=plan_unavailable`) |
| BKT ažuriran netočnim ishodom | 🔴 **DA** (`skill_mastery_history` vezan uz taj attempt) |
| potrošen hint kredit | 🔴 **DA** (`hint_requests.source='llm'` ∈ `CONSUMING_SOURCES`) |
| XP | 0 |
| streak | nije izgubljen — pokušaj se broji kao aktivan dan |
| misconception | ✅ nije zabilježen (`plan_unavailable` je u `_MECHANICAL_ERRORS`) |

### 🔴 Šteta po BKT-u je EGZAKTNA, ne procjena

Zabilježeni `p_l = 0.10782608695652175` do zadnje znamenke odgovara
`update(is_correct=False)` iz priora 0.05. Točan ishod dao bi 0.3782.

| polazni p_l | netočan | točan | šteta |
|---|---|---|---|
| 0.05 (novak) | 0.1078 | 0.3782 | −0.27 |
| 0.50 | 0.2286 | 0.9053 | **−0.68** |
| 0.80 | 0.4600 | 0.9743 | −0.51 |
| 0.95 | 0.7840 | 0.9945 | −0.21 |

**Najgore je pogođen student usred učenja, ne novak** — i kod prethodnog znanja `p_l`
stvarno **pada** (0.80 → 0.46), ne samo raste sporije.

### Zašto je to razred #63, a ne kozmetika

Ishod sustava („nisam uspio dohvatiti plan") i ishod zapisan u bazi („student je
pogriješio") se **razilaze**, i to trajno: `attempts` je istraživački podatak,
`skill_mastery_history` je **rekurzivan lanac** (#18) pa se takav redak ne može obrisati iz
sredine bez invalidacije svega kasnijeg. Eval traje danima, a `plan_unavailable` je po
konstrukciji **prolazan** — nastaje iz timeouta, dakle nasumično i nereproducibilno.

🔴 **Nalaz je NASLIJEĐEN, ne uveden ovom granom.** Isti je slučaj prije išao pod
`unsupported_eval` i imao istu manu; premještanjem pod vlastito ime postao je **vidljiv**.

### Popravak i odbijena alternativa

**Izvedeno:** `plan_unavailable` **ne stvara pokušaj**. Evaluator izlazi PRIJE
`persist_attempt` i odbija tok — `refuse(model-updated)`; Coordinator to prevodi u
`flow["error"]`, RESPOND vraća error-dict, ruta mapira u **503**, frontend u poruku koja
izrijekom kaže *„Ovo nije greška u tvom upitu"*. Smetnja se broji u `agent_messages_log` uz
`correlation_id` (izmjereno: 92 zapisa `refuse` evaluator→coordinator, payload
`{"error": "plan_unavailable", …}`), **ne** u `attempts`.

🔴 **Odbijena opcija „perzistiraj attempt, preskoči BKT i kredit".** Tražila bi da
`attempts` nosi **dvije uloge** — zapis o studentovom radu i zapis o smetnji sustava. Isti
je obrazac na ovoj grani već bio uzrok kvara (`_BLOCK_VALUE`: jedna maska za dva različita
razloga) i razlog uklanjanja `entry_task_id`. **Podatak o smetnji ide u log, ne u
instrument.**

### Zašto `refuse`, a ne novo polje u payloadu

Prijenos ide **performativom**, ne sadržajem. `if payload.get("error")` bilo bi „novo
ponašanje bez novog imena" — obrazac koji je u ovoj grani već proizveo tri nalaza (wrapup
§G2) — i sutrašnji legitiman `inform(model-updated)` s poljem `error` tiho bi prekidao tok.
Ontologija je **tema** razgovora, performativ je **govorni čin**: `refuse(model-updated)` =
„odbijam isporučiti model-updated za ovaj tok". Presedan: `_refuse_busy` (#62).

🔴 **Router NIJE diran.** Izmjereno da `_flow_template` ne ograničava performativ, pa
`refuse` ulazi u svoj tok, a tuđi `cid` i dalje ne ulazi. Proširenje predloška na
`attempt-result` je **odbijeno** jer ne bi bilo aditivno u učinku: usput bi promijenilo i
`task_not_found`, čije zatečeno ponašanje tada još nije bilo izmjereno (v. #70).

### Kako je granica zaključana

`tests/test_plan_unavailable_flow.py` (5 tvrdnji) — sve dokazane namjernim kvarom:

| tvrdnja | namjerni kvar | ishod kvara |
|---|---|---|
| 503 i nula redaka | (zatečeno stanje prije popravka) | `[200 ×10]` |
| utor se oslobađa na svakoj smetnji | preskoči `_release_flow` na novom putu | **10 utora procurilo od 10 smetnji** |
| K=8 istovremeno, mješavina, bez unakrsnih odgovora | — | — |
| `inform` s poljem `error` NE prekida tok | granaj na sadržaj payloada | 503 na uredno perzistiranu predaju |
| tuđi `cid` ne ulazi u tok | ograniči predložak performativom | `refuse` ne ulazi ni u svoj tok |

🔴 Curenje utora se **ne vidi u jednokratnom testu**: `MAX_CONCURRENT_FLOWS` je 64, pa bi se
procurjeli utor očitovao tek nakon 64 smetnje — usred otvorenog evala, kao „sve predaje
odjednom vraćaju 503".

**Zatečeni `test_coordinator_concurrency.py` ostao je zelen bez ijedne izmjene** (6 passed)
— to je bio uvjet da se tvrdnja „mehanika tokova nije dirana" uopće smije izgovoriti.

---

## #70 🟡 `task_not_found` istekne umjesto da odgovori — i pouka o dokazivanju

**Status:** 🟡 otvoren, **ne popravlja se u ovoj grani.**

### Izmjereno (2026-08-14, nepostojeći `task_id` kroz pun lanac)

| mjera | vrijednost |
|---|---|
| HTTP status | **504** |
| `detail` | `evaluation_timeout` |
| trajanje | **9.09 s** (= `update_timeout` 7 s + `SETTLE_WINDOW_S` 2 s) |
| oslobađanje utora | ✅ uredno (3 uzastopna zahtjeva, `flow_count` 0 → 0) |

### Mehanizam

`_send_task_not_found` šalje INFORM ontologije **`attempt-result`** na pošiljatelja
(Coordinator), ali `_flow_template` matcha **samo** `model-updated` i `recommend-next` za
dani `cid`. Poruka do toka **nikad ne stigne**; UPDATE istekne, `_settle` ne nađe redak, i
put završi kao `evaluation_timeout`. Student dobije **točan status iz krivog razloga**, i to
nakon punog prozora čekanja.

🔴 Nakon #69 ovo je **JEDINI preostali put** koji ne poštuje pravilo „smetnja → brz,
imenovan odgovor". Zapisan je zato da se **ne citira kao presedan**.

### 🔴 POUKA — kod koji podnosi stanje nije dokaz da to stanje nastaje

Prva verzija ovog nalaza tvrdila je da put daje **degradiran 200 s `verdict="unknown"`**.
Tvrdnja je izvedena iz `build_response_payload`, koji uredno podnosi `attempt_id=None` — ali
**bez provjere da poruka dotle uopće dolazi**. Ne dolazi.

**KOD KOJI PODNOSI STANJE NIJE DOKAZ DA TO STANJE NASTAJE.** Ista klasa kao povučeni dio
#60 („trag u produkcijskim podacima"), i isti obrazac koji je u ovom projektu već tri puta
proizveo netočan nalaz: čitanje jedne funkcije umjesto izvršavanja puta.

Mehanizam je usput potvrđen **namjernim kvarom** na drugom mjestu: ograniči li se
`_flow_template` performativom, i novi `refuse` put daje isti 504 nakon istog prozora —
dakle „poruka koja ne matcha predložak" doista završava kao `evaluation_timeout`.

---

## #73 🟡 Isti objekt uklonjen dvaput: naš gard i SPADE-ov epilog ne znaju jedan za drugoga

**Simptom.** Na svaku predaju, u terminalu:

```
Task exception was never retrieved
future: <Task finished name='Task-96' coro=<CyclicBehaviour._start() done,
         defined at .../spade/behaviour.py:126>
         exception=ValueError('This behaviour is not registered')>
Traceback (most recent call last):
  File ".../spade/behaviour.py", line 140, in _start
    await self._step()
  File ".../spade/behaviour.py", line 305, in _step
    self.agent.remove_behaviour(self)
  File ".../spade/agent.py", line 286, in remove_behaviour
    raise ValueError("This behaviour is not registered")
ValueError: This behaviour is not registered
```

**Mehanizam.** `CyclicBehaviour._step` završava bezuvjetnim `self.agent.remove_behaviour(self)`
(`behaviour.py:305`), a `Agent.remove_behaviour` diže `ValueError` ako `has_behaviour()`
vrati `False` (`agent.py:286`). Kad je isto ponašanje već skinuto, epilog zatekne prazno.

Kod nas ga skida `OrchestrationFSM` sam nad sobom: `_release_flow(self._flow["cid"], self)`
([`coordinator.py:567`](../backend/agents/coordinator.py)) → `remove_behaviour(fsm)`
([`coordinator.py:710`](../backend/agents/coordinator.py)). Taj poziv **ima** gard:

```python
try:
    if self.has_behaviour(fsm):
        self.remove_behaviour(fsm)
except ValueError:  # pragma: no cover — utrka s vlastitim kill()om
    pass
```

🔴 Gard je ispravan, ali štiti **pogrešnu stranu**. On hvata iznimku iz *našeg* poziva.
Iznimka koja se stvarno događa dolazi iz SPADE-ovog epiloga, koji teče u **vlastitom
`_start()` tasku** — izvan našeg `try`. Komentar `# pragma: no cover — utrka s vlastitim
kill()om` opisuje utrku koja se nikad ne dogodi; prava utrka je s epilogom, i nju gard ne
vidi.

**Mjerenje (2026-08-18).** `Agent.remove_behaviour` omotan u zasebnom procesu, repo
nedirnut. 20 predaja kroz pun lanac:

| | vrijednost |
|---|---|
| iznimaka ukupno | **20** (1 po predaji) |
| klasa | **`OrchestrationFSM` 20/20** |
| agent | `coordinator@localhost` 20/20 |
| progutano nešto drugo? | **ne** — 20/20 isti `ValueError` |

Pozivatelji, prebrojani nad 5 predaja:

| pozivatelj | ponašanje | ishod |
|---|---|---|
| `coordinator.py:710 in _release_flow` | `OrchestrationFSM` | **OK** (5×) |
| `behaviour.py:305 in _step` | `OrchestrationFSM` | 🔴 **ValueError** (5×) |
| `behaviour.py:305 in _step` | `_Send` | OK (5×) |

Redoslijed je time izmjeren, ne pretpostavljen: **naš eksplicitni poziv pobjeđuje** i skine
FSM, pa SPADE-ov epilog padne. `_Send` (OneShotBehaviour gatewaya) nitko ne skida
eksplicitno, pa njegov epilog uredno prolazi — kontrolna skupina u istom mjerenju.

**Nije curenje.** `len(agent.behaviours)` po agentu, prije prve predaje i nakon 20:

| agent | prije | nakon 20 | klase |
|---|---|---|---|
| gateway | 1 | **1** | `_Resolve` |
| coordinator | 1 | **1** | `_Intake` |
| evaluator / knowledge / recommender / gamification / hint | 1 | **1** | po jedno vlastito |

Krivulja je ravna kroz svih 20 mjerenja. Razlog je što `remove_behaviour` **prvo** provjeri
`has_behaviour` i tek onda `pop` — neuspješan poziv ne ostavlja ništa za sobom.

**Zašto ipak nije kozmetika.** Grana je u putu koji su #62/#63 popravili
(`_start → _step → remove_behaviour`), a `_release_flow` je funkcija koja oslobađa **utor**.
Dok stoji ovakva, svaki budući kvar u epilogu FSM-a izgleda **identično** ovom benignom
ispisu, pa se neće razlikovati od šuma. Ne skriva grešku *danas* — epilog se izvršava tek
nakon `is_running = False`, kad je tok već završio i odgovor otišao — ali uklanja razliku
između „sve u redu" i „nešto je puklo na kraju toka".

**Ne popravlja se u ovoj grani** (odluka korisnika). Kad se bude popravljalo, popravak nije
u našem gardu nego u tome da se FSM **ne skida eksplicitno** i prepusti epilogu, ili da se
epilog neutralizira prije skidanja.

---

## #74 🟢 Što točno znači „agenti komuniciraju preko XMPP-a"

**Za poglavlje o arhitekturi. Nije kvar i ne traži izmjenu koda.**

Agenti razmjenjuju FIPA-ACL poruke kroz SPADE. Kako ih SPADE **isporuči** ovisi o tome jesu
li pošiljatelj i primatelj u istom procesu — `spade/container.py:121-133`:

```python
async def send(self, msg: Message, behaviour: BehaviourType) -> None:
    to = str(msg.to)
    if to in self.__agents:
        self.__agents[to].dispatch(msg)
    else:
        await behaviour._xmpp_send(msg=msg)
```

U ovoj izvedbi svih 7 (6 domenskih + gateway) startaju u **istom uvicorn procesu**
([`main.py:64-65`](../backend/app/main.py)), dakle u istom `Container`u, pa se uvijek uzima
**prva** grana: `dispatch()`, in-process. XMPP ostaje na putu **autentikacije i
registracije** pri startupu, ne na putu poruka.

**Izmjereno 2026-08-18.** Prosody u stanju `exited`, tri predaje i burst:

| | status | vrijeme | lanac |
|---|---|---|---|
| ugašen t=0 | 200 | 0,13 s | 12 poruka |
| ugašen +30 s | 200 | 0,13 s | 12 poruka |
| ugašen +60 s | 200 | 0,12 s | 12 poruka |
| burst 10 predaja | **10/10 = 200** | — | — |

Ranije, uz `docker restart` (nedostupnost 0,52 s): slixmpp je prekid vidio
(`<stream:error><system-shutdown/>Received SIGTERM`, 7× `disconnected`) i vratio vezu tek
nakon **74,8 s**, a predaje na +0/+10/+30/+60 s su svejedno sve dale 200 s punim lancem.

🔴 **Posljedica za `--workers 1`.** Dosadašnje obrazloženje bilo je in-process
`AgentBridge` dict. Točnije je: **agenti postoje jednom po procesu**. Drugi uvicorn worker
značio bi drugi cijeli skup agenata s **istim JID-ovima** — ne dijeljenje posla, nego
dvostruki sustav. To je jači razlog od korelacijskog registryja i trebao bi zamijeniti
dosadašnju formulaciju.

**Što ovo NE znači.** Arhitektura nije poništena i FIPA sloj nije dekorativan: performativi,
ontologije i `Template.match()` stvarno upravljaju usmjeravanjem, samo unutar procesa.
Distribuirana izvedba (agenti u zasebnim procesima ili kontejnerima) usmjerila bi **iste**
poruke kroz **drugu granu istog `if`-a**, bez ijedne izmjene agentskog koda. Ono što traži
ispravak je samo **tvrdnja** u tekstu: reći da agenti komuniciraju FIPA-ACL porukama kroz
SPADE, uz napomenu o načinu isporuke, umjesto da se XMPP prikazuje kao message bus kroz
koji poruke stvarno putuju.
