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
| **#42** | **Indikator „riješeno" na pregledu Modula ODGOĐEN** | 🟡 **odgođen → Faza 6** | ModulesPage je **koncept-razina** (kartice modula + koncept-retci s mastery %), ne izlistava pojedinačne zadatke → nema klijentskog puta do „riješeno". Prava opcija traži proširenje `/modules` per-koncept `solved_task_count` (user-aware) — **još jedna izmjena ugovora na zamrznutom backendu**, a mastery % već komunicira napredak. Odluka korisnika (2026-07-25): odgoditi. Task screen (#41) i Dashboard CTA indikatori pokrivaju mjesta gdje student radi s konkretnim zadatkom |
| **#44** | **Preporučivač skače među temama (INSERT → INNER JOIN) — breadth-first ZPD, NIJE bug** | 📌 **svojstvo dizajna (za rad), ostavljeno kako je** | Uočeno uživo: student riješi `insert`, klikne „Sljedeći zadatak" i dobije `inner_join` — naizgled nepovezan skok. **Uzrok je ZPD prioritet** (`rules.pl` `recommend_next`, redom: weak → partial → unlock_new → fallback) nad GLOBALNIM skupom koncepata, NE lanac po temi. Konkretno: `insert` (tier easy, prior P(L)=0.30 → **partial**) rješavanjem poraste iznad 0.30 i ostaje partial; `inner_join` (tier medium, prior **0.15 → weak**) ima jedini preduvjet `join_condition` (transverzalni glue → maskiran kao savladan), pa je **weak-ready**. Klauzula 1 (weak) ide PRIJE klauzule 2 (partial) → `inner_join` preskoči „nastavak INSERT-a". Posljedica: nakon jednog točnog rješenja koncept ispadne iz *weak* u *partial* i biva deprioritiziran → sustav **breadth-first** obilazi slabe ready-koncepte umjesto da produbi jedan. **Obranjivo (ZPD je poanta rada); NE mijenja se pred evalom** (izmjena je u Prolog/recommenderu = zamrznuti backend + mijenja adaptivnost koju eval mjeri). Odluka korisnika (2026-07-26): ostaviti, opisati u radu. Srodno: #16 (saturacija P(L)), #35 (ZPD escape) — ista klasa emergentnih svojstava spoja BKT + Prolog |
| **#45** | 🔴 **Deklarirana odvojenost streaka od XP-a poništena je vlastitim mehanizmom — vremenski ovisan XP ulazi u level i global rang** | 📌 **prijetnja valjanosti (za rad), NE popravljati** | **Jezgra nije efekt na usporedivost nego PROTURJEČJE U DIZAJNU.** `gamification_logic.py:43-45` izrijekom tvrdi: *„streak NAMJERNO ne množi XP — XP ostaje čist proxy za učinak-u-učenju (streak se nagrađuje kroz `streak_7` badge). Badge XP (`seed_data.py` `xp_reward`) se u persistenceu STAKUJE u isti `xp_delta` kao attempt XP."* **Druga rečenica opovrgava prvu:** ograda („XP je čist proxy za učinak") i mehanizam kojim se opravdava („nagrađuje se kroz badge") **su isti put**. `streak_7` nosi **30 XP** (`seed_data.py` BADGES), a `gamification_persistence.py:283-294` ih upisuje u `xp_log` (uz `attempt_id=NULL`) **i u `user.xp`** (`:293` `user.xp += xp_reward`), nakon čega `:297` `user.level = level_for_xp(user.xp)` **recomputa level uključivo s njima** (redoslijed je izrijekom komentiran kao bitan). Global ljestvica sortira po `User.xp` (`routes.py:632`) → badge XP ulazi i u **rang**. Uz `level_for_xp = 1 + xp // 100` (`LEVEL_STEP=100`), tih 30 XP je **30 % jednog level koraka** — dovoljno da samo po sebi prebaci granicu levela. **Formula XP-a je čista:** `compute_xp` (`:96-122`) = `round_half_up(base[difficulty] × verdict_factor[verdict] × attempt_bonus[attempt_number])` — tri ulaza, nijedan vremenski; nema dnevnog bonusa ni streak multiplikatora, a Prolog nema **nijedno** XP pravilo (citat pretrage: `grep -rniE "\bxp\b" backend/prolog/` → **0 pogodaka**). Vremenska ovisnost ulazi **isključivo** kroz `streak_7`, i to je jedini takav bedž od pet (v. tablicu u bilješci #24). **POSLJEDICA:** dva sudionika s **identičnim skupom riješenih zadataka** mogu se razlikovati u **XP-u, levelu i global rangu** isključivo po tome je li rad raspoređen na 7 uzastopnih dana ili zbijen. 🔴 **Ovo NIJE posljedica promjene strategije evaluacije** — za razliku od #24, gdje je pala samo pretpostavka o dostižnosti. Tvrdnja iz docstringa je **netočna od trenutka kad je `streak_7` dobio `xp_reward > 0`**, dakle od seeda Faze 1; asinkrona evaluacija ju je samo učinila **vidljivom** (pod jednokratnom nadziranom sesijom bedž nitko nije mogao osvojiti, pa je efekt bio nula i proturječje je spavalo). **NE popravlja se** — gamifikacija je zamrznuta, a izmjena `xp_reward` ili level formule mijenja mjerenje koje eval provodi. U radu se prijavljuje uz #29 (rezultat-bazirana evaluacija), #31 i #35 kao **prijetnja konstruktnoj valjanosti**: XP je deklariran kao mjera učinka u učenju, a dijelom mjeri raspored rada. Pri interpretaciji ljestvice i usporedbi sudionika XP treba čitati **uz badge-strukturu**, ne kao čistu mjeru uspješnosti. **Ispravak samog docstringa ODGOĐEN (odluka 2026-08-10, kandidat za Fazu 6).** Diff je pripremljen (`docs/faza-4.7-errata-prijedlog.md`, PRIJEDLOG 5) i mijenja **isključivo komentar**, nula izvršnog koda — ali `gamification_logic.py` je backend, pa po 🔒 politici zamrznutog backenda i najmanja izmjena traži **pun `pytest` + `preflight`**, a `pytest` piše u živu `tutor_main` i ostavlja FIPA promet koji nijedan cleanup ne dohvaća (#40). **Cijena tog ciklusa nadmašuje korist**, jer ovaj redak errate već nosi istinu — netočna tvrdnja je zabilježena ondje gdje se nalazi traže. Docstring ostaje netočan do Faze 6, svjesno i zapisano. Srodno #24 (kriterij bedža), #47 (weekly prozor), #9 (kohortna izolacija) |
| **#47** | 🟡 **Weekly ljestvica mjeri SVJEŽINU, ne trud — klizni prozor + opis koji imenuje drugu vrstu prozora** | 📌 **nalaz o dizajnu (za rad)** | **Mehanizam:** `_read_leaderboard_weekly` (`routes.py:648-660`) računa score kao `SUM(xp_log.delta)` uz `cutoff = datetime.now(Europe/Zagreb) - timedelta(days=7)`, a docstring izrijekom navodi *„Useri bez ijednog `xp_log` reda u prozoru se NE prikazuju"*. Prozor je **klizan prema trenutku GLEDANJA**, ne prema početku sudionika. **Posljedica:** sudionik koji je odradio studiju i završio prije 10 dana **nestaje s weekly ljestvice bez ijedne promjene u vlastitim podacima** — njegov XP, level i global rang su netaknuti, ali ga weekly više ne broji ni u `total`. Pod jednokratnom nadziranom sesijom efekt nije postojao: svi su radili unutar istog prozora pa je **weekly ≡ global**. 🔴 **Uz to, opis u UI-ju imenuje DRUGU VRSTU PROZORA.** Sve tri korisniku vidljive niske govore o *tjednu*: `LeaderboardPage.tsx:53` label **„Ovaj tjedan"**, `:52` opis **„Osvojeni XP u tekućem tjednu (Europe/Zagreb)."**, `:133` prazno stanje **„Ovaj tjedan još nema osvojenog XP-a"**. „Tekući tjedan" se čita kao **kalendarski tjedan** (pon–ned), a implementacija je **klizni prozor zadnjih 7 dana** — to su različiti skupovi (u srijedu klizni prozor obuhvaća i prošli četvrtak, kalendarski ne). Jedino točno formuliran opis („zadnjih 7 dana") živi u **komentaru koda** (`LeaderboardPage.tsx:15`), dakle nevidljiv korisniku; citat pretrage: `grep -rniE "7 dana\|sedam dana"` u `frontend/src` daje samo taj komentar i nepovezane pogotke u `StatsSummary`/`attempt-stats`. **Odluka 4.5 da tekst bude generički bila je ISPRAVNA** i ostaje: envelope nema `window_start`, a klijentski izračunata granica mogla bi promašiti backend definiciju za sat ili dan (invarijanta „backend konstante se ne rekonstruiraju na klijentu"). **Problem nije genericnost nego imenovanje pogrešne vrste prozora** — „zadnjih 7 dana" je jednako generično, ne traži nijedan podatak iz odgovora, i točno je. **Nedosljednost unutar projekta:** `attempt-stats.ts:4-6` i `StatsSummary.tsx:2-5` uspostavljaju pravilo *„LABELIRANJE OBAVEZNO: 'zadnjih N pokušaja', nikad gol 'Accuracy'"* — dakle mjera nad prozorom MORA nositi svoj prozor u labeli. Weekly ljestvica je ista klasa mjere i to pravilo **ne slijedi**. **Popravak je copy-only i frontend-only** (tri niske u `LeaderboardPage.tsx`), ali dira eval-verificirani ekran → **nije izveden bez izričite odluke**. U radu: weekly ljestvica se pod asinkronom evaluacijom **ne smije čitati kao mjera ukupnog truda** — ona mjeri aktivnost u kliznom prozoru; za usporedbu sudionika koristiti global scope. Srodno #45 (vremenski ovisan XP), #15 (mjera nad prozorom bez server-side filtera) |
| **#48** | 🟡 **Stanje „odabrano" na `ConceptCurveCard` kršilo je 1.4.11 (AA) neovisno o fokusu** | ✅ **zatvoreno u 4.7-4c (posljedica korekcije `--ring`)** | `ConceptCurveCard.tsx:61` renderira odabranu karticu kao `selected ? "border-ring bg-muted/40" : "border-border"`. `border-ring` je time **indikator stanja**, ne fokusa: vidljiv je trajno, i kad fokus nije na kartici. SC 1.4.11 Non-text Contrast (AA, WCAG 2.1) pokriva „vizualne informacije potrebne za identifikaciju komponenata **i njihovih stanja**" → traži ≥3:1 prema susjednoj boji. **Izmjereno 2026-08-10:** `--ring` vs `bg-muted/40` nad `card` = **2,51:1 light** ❌ (dark 3,79 ✅). **Zatvoreno korekcijom `--ring` 0.708 → 0.556 u 4c → 4,57:1 ✅.** 🔴 **Zapisano SAMOSTALNO iako ga popravlja tuđa promjena:** bez vlastitog broja nalaz bi tiho nestao i vratio se neprimijećen ako se token ikad vrati na svjetliju vrijednost ili ako `ConceptCurveCard` dobije vlastitu boju. ⚠️ **Bilješka o hijerarhiji:** token **ne razdvaja** „odabrano" od „fokusirano" — oba vuku `--ring`, pa su nakon korekcije na 4,57 odnosno 4,73:1, praktički jednako teški (zatečeno je bilo 2,51 vs 2,59 — jednako blisko). Odnos se **ne mijenja**, oba se dižu. Hijerarhija „fokus > odabir" tražila bi **vlastiti token** za `ConceptCurveCard` — dizajnerska odluka za Fazu 6. Srodno: #50, #33 |
| ~~#49~~ | — | 🚫 **BROJ SE NE DODJELJUJE** | Broj `#49` pojavljivao se u tekstu #41 kao referenca na **politiku zamrznutog backenda**, koja **nema broj** (🔒 retci nisu numerirani). Referenca je ispravljena 2026-08-10, ali se broj **trajno umirovljuje** da se ne dogodi da netko kasnije naiđe na stari commit ili wrapup s „#49" i poveže ga s pogrešnim nalazom. Sljedeći slobodan broj je **#50**. V. konvenciju o prostoru imena u zaglavlju |
| **#50** | 🔴 **Kontrast se kroz cijeli projekt mjerio vs `card`, a dio elemenata renderira na `-soft` i drugim alpha-plohama — nenavedena ploha je bila kvar, ne brojke** | ✅ **zatvoreno u 4.7-4c (tokeni) + 🔒 politika** | **Uzorak, ne incident.** Otkriveno u tri kruga: (1) #13 — `text-partial` objavljen kao 5,50 vs `card`, a renderira se na `bg-partial-soft` gdje je 4,86; (2) revizija FeedbackPanela — `muted-foreground` **4,18–4,26** i `accent-warm-text` **4,22–4,30** na `-soft` plohama, oboje ispod AA, dok su vs `card` prolazili (4,73 / 4,78); (3) inventar `-soft` potrošača — 🔴 **ispravak razmjera:** raniji zapis „svih sedam pogođenih elemenata je u FeedbackPanelu" bio je **NETOČAN**. `bg-incorrect-soft` nosi i **`ErrorState.tsx:28`**, dijeljeni primitiv koji se renderira na **svakom ekranu** (20 upotreba u 12 datoteka: Task ×4, ErrorBoundary ×3, Profil ×2, Dashboard ×2, Admin ×2, TaskEntry, Moduli, Ljestvica, RunResultPanel, MasteryCurves, AttemptHistory, ContinueCard) — pa je pogođena **poruka svake greške u aplikaciji**, plus `RunResultPanel:130` i blokovi grešaka na `/login` i `/register`. **Uzrok nije token nego ploha:** `-soft` plohe su ~10 % tamnije od `card`, a oba tokena prolazila su na `card` s tankom rezervom. **Svaka pojedina ranija tvrdnja bila je TOČNA za plohu koju je mjerila** — kvar je bio u tome što ploha nije bila navedena, pa se tvrdnja čitala šire nego što vrijedi (npr. `MASTER.md:46` „amber tekst NA pozadini ≥4.5:1 ✓" bez imenovane pozadine). **Zatvoreno u 4c:** `--muted-foreground` 0.556 → **0.528**, `--accent-warm-text` 0.56 → **0.514** (light); puna matrica 23 plohe × 7 tekst tokena, obje teme, **0 padova** — `docs/faza-4.7-kontrast-matrica.md`. **Uz to dopunjena 🔒 DOC politika** (v. redak niže). Srodno #13, #33, #51 |
| **#51** | 📌 **Gamifikacijske površine su najslabiji a11y teren u aplikaciji — strukturno, ne slučajno** | 📌 **nalaz o dizajnu (za rad); tekst popravljen u 4c, plohe ostaju** | Sva tri pada izvan `-soft` bila su **gamifikacijski čipovi**: `BadgeGallery.tsx:73,97` (`muted-foreground` na `bg-muted` = 4,34), `:96` (`accent-warm-text` na `bg-accent-warm/20` = **3,89**, tekst od **10,4 px** — najmanji u aplikaciji) i `BadgeStrip.tsx:47` (4,32). Uz #48 (`ConceptCurveCard` „odabrano" 2,51) i #50 (XP čip, streak, level-up, badge čip u FeedbackPanelu) obrazac je **sustavan**. **Strukturni uzrok:** par `earned`/`unearned` traži **dvije plohe niskog kontrasta** da bi razlika djelovala suptilno → tekst pada na obje. Tokeni su AA-verificirani u 4.1b vs **pune** plohe; bedževi su **jedini potrošači alpha-kompozitiranih ploha** i nastali su u 4.4a, dvije faze kasnije, **bez ponovljenog mjerenja**. **Izmjereno 2026-08-10:** same plohe `accent-warm/5,10,20` vs `card` daju **1,05–1,52:1** u obje teme, dakle **daleko ispod 3:1** — ali **nisu nosilac informacije**: stanje nose **ikona + tekst** (`Check`/`Lock` + „Osvojeno"/„Zaključano", `BadgeGallery.tsx:100-110`; `CircleUserRound` + `font-semibold` + `aria-current` u `LeaderboardTable.tsx:57-79`), pa je tint **ukras**, isto rezoniranje kao #33. Razlučivost čipova nakon 4c: ΔE(Oklab) **0,121** (zatečeno 0,120) — nositelj je **chroma**, ne svjetlina, pa potamnjenje teksta razliku **ne dira**. **Formulacija za rad:** nagradne površine su **dizajnirane da budu suptilne**, a suptilnost je u izravnom sukobu s kontrastnim zahtjevom — to je **tenzija dizajna gamifikacije**, ne previd implementacije. Srodno #48, #50, #33 |
| **#46** | 🔴 **Brisanje POJEDINOG sudionika nije dokazano izvedivo, a obećanje o njemu trajno stoji na Profilu** | 🔴 **otvoren — BLOKATOR prije nego link ode sudionicima** | Informacija o sudjelovanju (4.7-1a) obećava „za zahtjev za brisanje podataka: <kontakt>" i „podaci se čuvaju do obrane rada, nakon čega se brišu". Od 4.7-1a-dopune taj tekst je i na **Profilu** (`ParticipationSection`), dakle stoji **trajno pred svakim prijavljenim korisnikom**, ne jednokratno prije registracije — zato je rok „prije slanja linka", a ne „prije deploya". **Mehanizam:** `agent_messages_log` **nema `user_id`** (`models.py:394-409` — 7 stupaca, nijedan ne referencira korisnika, nema FK na `users` pa ni CASCADE ne pomaže), a njegov `content` JSONB nosi `submitted_query` studenta (4.5b README to navodi kao osobni podatak). **Nijedan cleanup ga ne dohvaća po korisniku:** `purge_demo_users.py:61-75` pokriva 9 tablica (3 eksplicitno + 5 CASCADE + `users`) i te tablice **nema među njima jer nema po čemu filtrirati**; jedino mjesto koje je uopće briše je `TRUNCATE TABLE agent_messages_log RESTART IDENTITY` u `prepare_eval_baseline.py:435` — **sve ili ništa**, iza `--confirm`. **IZMJERENO 2026-07-26** (brojači prije i poslije, `seed_demo_user` → 27 attempta kroz pravi `POST /attempt` → `purge_demo_users`): `users` 1→1, `attempts` 12→12, `skill_mastery_history` 22→22 (sve točno na baseline ✅), a `agent_messages_log` **363→696 = +333 zapisa koje ništa ne može obrisati po korisniku**. To je **12,3 zapisa po attemptu**, što se poklapa s izmjerenih 12/attempt iz #34. **Ekstrapolacija na eval volumen:** 20 sudionika × 30 attempta = 600 attempta → **~7 400 zapisa** s upitima sudionika, bez ijednog puta do brisanja po osobi (isti red veličine kao procjena ~7 200 u #34). **Moguć put bez izmjene sheme:** prikupiti `correlation_id`-eve iz `attempts` tog korisnika PRIJE brisanja attempta, pa obrisati logove po tom skupu — ali to **ne pokriva poruke bez `correlation_id`** ni one koje prethode stvaranju attempta (#40: samo 5 od 12 poruka po attemptu nosi `attempt_id`), i mora biti **verificirano u OBA smjera** (poučak iz #39). **Odluka je korisnikova:** (a) izgraditi i verificirati proceduru prije slanja linka, ili (b) preformulirati odlomak da ne obećava više od dokazano izvedivog. Srodno: #37, #40, #34 |
| **#43** | **Koncept-retci u Module overviewu nisu bili klikabilni (nije bilo puta koncept→zadatak)** | ✅ **4.6-eval (backend escalation, bez migracije)** | UI je imao koncepte ali nijedan endpoint nije mapirao koncept → `task_id` (task se dohvaća samo po ID-u; `/modules` nije nosio ID-eve). **Popravak:** `/modules` ConceptNode dobio `entry_task_id` — reprezentativan AKTIVAN primary zadatak (najlakši prvi: `difficulty ↑, id ↑`), **statički** (bez user-konteksta → `/modules` ostaje čist katalog, cacheable). `entry_task_id != null` ⟺ `primary_task_count > 0` (ista maska). Frontend: ConceptRow je `<Link>` na `/task/<id>` kad je klikabilan = **`entryTaskId != null && state !== "locked"`** — zaključani (nezadovoljeni preduvjeti) i glue/izvan-opsega (0 zadataka) ostaju neklikabilni, savladani su klikabilni za vježbu (bez XP-a, #41). „Koji zadatak": najlakši primary; **NE** „sljedeći neriješen" (to bi tražilo user-aware `/modules`) — kandidat za dogradnju. 1 novi test (`entry_task_id` == DB ground truth + invarijanta). ⚠️ eskalacija zamrznutog backenda (kao #41) |

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

**Opseg motiona u 4.7 (da se ne pročita kao tiho oživljavanje 4.6):** 4.6 ostaje rezana.
Jedina animirana površina dodana u 4.7 je **mobilni navigacijski drawer**, i to kao
posljedica zahtjeva **pristupačnosti** (ispod 768px nije postojala nikakva navigacija), ne
kao motion polish. Gamifikacijski motion (XP count-up, level-up celebration, badge-unlock,
streak flame), page tranzicije, ⌘K paleta i WebSocket **ostaju neizvedeni**.
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
