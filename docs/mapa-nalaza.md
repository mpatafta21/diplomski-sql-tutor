# Mapa nalaza → poglavlja rada

Svrha: za svaki nalaz iz [`errata.md`](errata.md) odrediti **gdje u radu pripada**, **je li
zatvoren**, i **nosi li brojku koja se može citirati**. Errata ostaje kanonski izvor — ovo
je samo pogled na nju iz perspektive strukture rada.

## 🔴 Dvije stvari koje treba znati prije čitanja

**1. Nalazi #1–#6 NE POSTOJE.** Konsolidirani popis počinje na **#7**. Provjereno pretragom
(`ERRATA #1`…`#6` → 0 pogodaka u svim oblicima). Brojevi nikad nisu bili dodijeljeni; rane
faze nalaze nisu numerirale. Tablica ih zato **nema** — izmišljanje redaka za njih bilo bi
gore od praznine. Uz to je **#49 trajno umirovljen** (nikad dodijeljen, v. konvenciju u
zaglavlju errate).

**Ukupno klasificirano: 79 unosa** (#7–#84 + `#10b` + umirovljeni #49).

**2. Tri politike (🔒 DOC) nisu ovdje** jer po konvenciji **nemaju broj**: mjerenje uz brojku
i datum (iz #33), ploha i filtar lažnih pozitiva (iz #50), te tri pravila o instrumentu (iz
#84). Sve tri pripadaju **poglavlju 5.6** i u radu se citiraju opisno, nikad brojem.

## Kako čitati stupac „poglavlje"

Prvo navedeno poglavlje je **težište** (podebljano); ostala su mjesta gdje se nalaz
legitimno spominje kao sporedan. Nalaz koji ide u više poglavlja u radu se **piše jednom**,
a drugdje referencira.

## Kako čitati stupac „brojka"

Brojka je **doslovno prepisana iz errate**, ne parafrazirana — da se u tekst rada može
prenijeti bez ponovnog otvaranja izvora. **🔴 bez brojke** znači da nalaz tvrdi nešto što
nije izmjereno.

🔴 Izostanak brojke **nije svugdje jednako težak**, pa je popis na dnu razdvojen: u
poglavljima 5.x tvrdnja bez brojke nema pokrića i traži mjerenje, dok je kod nalaza o
implementaciji ili operativi izostanak očekivan i nije signal.

---

| broj | sažetak | poglavlje | status | brojka za citiranje |
|---|---|---|---|---|
| #7 | `task.module_id` ne odgovara modulu primarnog koncepta zadatka. | **3** · 4 | 🟡 otvoren | 3/83 zadatka |
| #8 | `attempts` nema `verdict` kolonu; „djelomično" se derivira iz `error_type`. | **4** | 📌 prihvaćena limitacija | 🔴 **bez brojke** |
| #9 | Test/dev korisnici rušili su asertacije ljestvice jer dijele bazu. | **nijedno** | ✅ popravljen | 🔴 **bez brojke** |
| #10 | UI je otključavao koncepte drukčije nego preporučivač. | **4** | ✅ popravljen | 🔴 **bez brojke** |
| #10b | `primary_task_count` bio je izložen a nikad konzumiran — mrtvo polje sugerira mogućnost koje nema. | **4** · 5.6 | ✅ popravljen | grep `.soft` → **0 pogodaka** (druga pojava iste klase) |
| #11 | `NextTaskResponse` ne nosi naslov zadatka — dvostruki hop prihvaćen. | **4** | 📌 prihvaćena limitacija | 🔴 **bez brojke** |
| #12 | `/run` vraća retke kao dict, pa kolabira istoimene stupce s različitim vrijednostima. | **4** | 🟡 otvoren | 🔴 **bez brojke** |
| #13 | Hue „djelomično" (55–60) preblizu je gamifikacijskom amberu (70–85). | **4** · 6 | 📌 prihvaćena limitacija | hue 55–60 vs 70–85; `text-partial` 5,50 vs `card` a 4,86 na `-soft` |
| #14 | `earned_at` bedža ne postoji u API-ju, pa se datum osvajanja ne prikazuje. | **4** | 📌 prihvaćena limitacija | 🔴 **bez brojke** |
| #15 | `/attempts` nema server-side filtere, pa povijest namjerno nema filter kontrole. | **4** | 📌 prihvaćena limitacija | 🔴 **bez brojke** |
| #16 | P(L) saturira i plato je istina o modelu, ne greška implementacije. | **5.5** · 3 | 📌 prihvaćena limitacija | od 12. prilike serija u **0,99978–1,00000**; 4 uzastopne greške 1,000 → **0,993** (21 prilika) |
| #17 | Frontend nije imao committed e2e suite — brojke „N/N" bile su ručne verifikacije. | **5.6** · 4 | 🟡 otvoren | **5 → 1** tvrdnji „N/N" (git povijest: 4.1→2, 4.2→0, 4.3→3; danas 1); pokriva ih **5 e2e scenarija**, ne 1:1 |
| #18 | BKT povijest je rekurzivan lanac: brisanje iz sredine invalidira sve kasnije točke. | **5.5** · 4 | ✅ popravljen | lanac **min 2 · medijan 6 · max 43**; brisanje iz sredine najdubljeg (`where_filter`) invalidira **22** kasnije točke |
| #19 | Modul 6 je bio izvan opsega evaluacije (`is_active=False`). | **3** · 4 | ✅ popravljen | 🔴 **bez brojke** |
| #20 | Task bank nije bio pod verzijom. | **4** | ✅ popravljen | **85 zadataka** (83 LLM + 2 ručna; 80 aktivnih, 5 M6 neaktivnih) |
| #21 | `task_id` je nestabilan preko reseeda; kanonski ključ je `source_id`. | **nijedno** · 5.6 | ✅ popravljen | 🔴 **bez brojke** |
| #22 | Bedž `explorer` bio je nedostižan jer je kriterij hardkodirao module 1–6. | **6** · 4 | ✅ popravljen | 🔴 **bez brojke** |
| #23 | Evaluator je hardkodirao `dml=False`, pa je svaki INSERT/UPDATE/DELETE padao na „permission denied". | **4** · 5.6 | ✅ popravljen | **9/83** zadataka neocjenjivo, **tri faze**, 0 testova |
| #24 | Bedž `streak_7` traži 7 kalendarskih dana — dostižnost je pala s prelaskom na asinkroni eval. | **6** | 📌 prihvaćena limitacija | **7 uzastopnih dana** |
| #25 | Bedž `join_master` bio je nedostižan jer `right_join` nikad nije bio ponuđen. | **6** · 5.5 | ✅ popravljen | `right_join` prior **0,0500 → 0,8541** nakon 2. zadatka |
| #26 | `make dev` nije bio from-scratch sposoban (nedostajala registracija agenata). | **nijedno** | ✅ popravljen | 🔴 **bez brojke** |
| #27 | Subfloor pravilo tiho ubija koncepte s točno jednim zadatkom. | **5.5** · 3 | ✅ popravljen | `right_join` (1 primarni, 0 sekundarnih) i `insert` (1, 0) → **0 BKT updatea** nakon savršenog prolaza |
| #28 | DB `concepts.tier` divergira od Prolog tiera, a Prolog je autoritativan za BKT. | **3** · 4 | 📌 prihvaćena limitacija | **6/30** koncepata |
| #29 | Rezultatska evaluacija ne razlikuje ekvivalentne formulacije — BKT kredit bez upotrebe koncepta. | **5.5** | 📌 prihvaćena limitacija | **20 od 30** koncepata dopušta zaobilazak → **61 od 88** zadataka (**69,3 %**); provjereno 20, prošlo **20/20** uz strojni AST dokaz |
| #30 | `RETURNING` u multi-row `INSERT`-u nema zajamčen redoslijed. | **5.5** · 4 | 📌 prihvaćena limitacija | 1 zadatak, 2 retka |
| #31 | Koncept bez primarnih zadataka svejedno skuplja BKT povijest kroz sekundarna pojavljivanja. | **5.5** · 3 | ✅ popravljen | `column_alias` 0 primarnih / 4 sekundarna → `p_l=0,7284`; `order_by` 2 zadatka, **21 točka, 19 sekundarnih** |
| #32 | Recharts stavlja `tabindex=0` + `role="application"` na svaki graf → crna rupa fokusa. | **4** · 6 | ✅ popravljen | **15 tab-stopova** (78 → 63) |
| #33 | Donji stopovi mastery gradijenta su ispod 3:1, a dokumentirana mitigacija nikad nije vrijedila. | **4** · 5.6 | 📌 prihvaćena limitacija | `mastery-0` **2,13:1** dark / **1,58:1** light; obrub **1,32:1** umjesto tvrđenih ≥3:1 |
| #34 | `agent_messages_log` sadrži byte-identične duplikate. | **4** · 5.6 | 📌 prihvaćena limitacija | **3 od 12** zapisa po pokušaju; ~**7 200** za 600 pokušaja |
| #35 | ZPD escape — koncepti se „savladaju" prije nego ih sustav ikad počne poučavati. | **5.5** | 📌 prihvaćena limitacija | sekundarnih updatea: `order_by` **88,9 %**, `select_basic` **90 %**, `where_filter` **86,4 %**; `order_by` 21 update / 0 primarnih → P(L)=1,000 |
| #36 | `/admin/agent-logs` tiho capira `limit` na 200, pa „pregled svega" nije moguć. | **4** · 5.6 | ✅ popravljen | cap **200**; ~**7 200** zapisa pri eval volumenu |
| #37 | Evaluacijski podaci su nenadoknadivi, a živjeli su samo u docker volumenu. | **nijedno** · 5.6 | ✅ popravljen | negativni test verifikacije: **35 vs 0** redaka |
| #38 | Snimke za rad nastajale su u scratchpadu, izvan repozitorija. | **nijedno** | ✅ popravljen | **9 snimki** stavljeno pod verziju |
| #39 | `make dev-reset` guard odbijao je i ispravnu potvrdu jer `docker compose exec` jede stdin. | **5.6** · nijedno | ✅ popravljen | **3 od 16** `except` blokova u `agents/` nose `# pragma: no cover`; **0 od 3** ima test koji ih vidi aktivirane |
| #40 | `pytest` piše u živu bazu i ostavlja FIPA zapise koje nijedan cleanup ne dohvaća. | **5.6** | 📌 prihvaćena limitacija | 485 testova → **87 redaka**; nakon baselinea **12 redaka / 1 tok**; samo **5 od 12** poruka nosi `attempt_id` |
| #41 | Ponovno rješavanje već riješenog zadatka farmalo je XP. | **6** · 4 | ✅ popravljen | 🔴 **bez brojke** |
| #42 | Mastery postotak ne komunicira napredak — razilazi se s prijeđenim sadržajem u oba smjera. | **6** · 5.5 | ✅ popravljen | `select_basic` **99 % uz 1/2**, `from_clause` **99 % uz 1/3**, `where_filter` **77 % uz 3/3** |
| #43 | Nije postojao put koncept → zadatak; retci koncepata nisu bili klikabilni. | **4** · 6 | ✅ popravljen | 🔴 **bez brojke** |
| #44 | Preporučivač skače među temama (INSERT → INNER JOIN) — breadth-first ZPD, nije bug. | **5.5** · 6 | 📌 prihvaćena limitacija | `insert` prior 0,30 → *partial*; `inner_join` prior **0,15 → weak**, pa pretječe |
| #45 | Deklarirana odvojenost streaka od XP-a poništena je vlastitim mehanizmom — vremenski ovisan XP ulazi u level i rang. | **5.5** · 6 | 📌 prihvaćena limitacija | `streak_7` = **30 XP** = **30 %** jednog level koraka (`LEVEL_STEP=100`) |
| #46 | Brisanje podataka pojedinog sudionika nije dokazano izvedivo, a obećanje je stajalo na Profilu. | **6** · 4 | 📌 prihvaćena limitacija | `agent_messages_log` **363 → 696 = +333** zapisa nakon 27 pokušaja (**12,3/pokušaj**); ~**7 400** za eval volumen |
| #47 | Weekly ljestvica mjeri svježinu, ne trud — klizni prozor uz opis koji imenuje kalendarski tjedan. | **6** · 5.5 | 📌 prihvaćena limitacija | klizni prozor **7 dana**; tri niske u UI-ju govorile o „tjednu" |
| #48 | Stanje „odabrano" na kartici krivulje kršilo je SC 1.4.11 neovisno o fokusu. | **4** | ✅ popravljen | **2,51:1** light → **4,57:1** nakon korekcije `--ring` |
| #49 | Broj se trajno ne dodjeljuje (bio je viseća referenca na politiku bez broja). | **nijedno** | 🚫 umirovljen | 🔴 **bez brojke** |
| #50 | Kontrast se mjerio prema `card`, a elementi renderiraju na `-soft` plohama — nenavedena ploha je bila kvar. | **4** · 5.6 | ✅ popravljen | `muted-foreground` **4,18–4,26** i `accent-warm-text` **4,22–4,30** na `-soft`; `ErrorState` u **20 upotreba / 12 datoteka**; matrica **23×7, 0 padova** |
| #51 | Gamifikacijske površine su strukturno najslabiji a11y teren jer suptilnost i kontrast su u sukobu. | **4** · 6 | 📌 prihvaćena limitacija | **3,89:1** na tekstu od **10,4 px**; plohe `accent-warm/5–20` **1,05–1,52:1**; ΔE **0,121** |
| #52 | `--destructive` nikad nije bio mjeren; mjeren pada, ali nije regresija nove palete. | **4** · 5.6 | 🟡 otvoren | obrub **2,34** / **2,43**, halo **1,98** (prag **3,00**); od **18 mjesta samo 1 dosežno** |
| #53 | Sustav nema WARNING semantiku, pa se rezervacija amber boje predvidljivo probija. | **4** | 🟡 otvoren | **4 jasna prekršaja** od 19 potrošača (2 popravljena), 1 granično, 14 ispravnih |
| #54 | `recommendations_log` broji i preporuke koje nitko nije vidio (refetch na fokus taba). | **5.6** · 5.5 | 🟡 otvoren | **75 → 89 redaka** kroz nekoliko sati, svi `user_id=1`, `attempts` nepromijenjen na **13**; `staleTime` **60 s** |
| #55 | Projekt ima mjerni instrument za vrijednosti (boje), a nijedan za učinak (vrijeme, dosežnost, izvršenje). | **5.6** | 🟡 otvoren | **tri kvara × tri faze**; sve tranzicije radile na **150 ms** umjesto 160/240/400/700 |
| #56 | Prag ΔE 0,10 bio je ad hoc; projektni prag je 0,05. | **4** · 5.6 | 📌 prihvaćena limitacija | prag **0,05** (projektni) vs **0,10** (ad hoc); **6 parova** ispod 0,10 |
| #57 | Test pisan prema promatranom ponašanju zaključava kvar kao specifikaciju. | **5.6** | ✅ popravljen | **četvrti primjerak** istog obrasca (uz #39, N-18, `--font-heading`) |
| #58 | Uklanjanje trenja iz ponovnog pokušaja može promijeniti raspodjelu uzastopnih predaja. | **5.6** · 6 | 🟡 otvoren | 🔴 **0/129 — ali mjerenje NE ODLUČUJE**: prolaz konstrukcijom nikad ne ponavlja upit; ostaje nemjeren |
| #59 | Informacija sudionika nije pokrivala slanje podataka vanjskoj usluzi; bilježena privola se ne uvodi. | **6** | 📌 prihvaćena limitacija | 🔴 **bez brojke** |
| #60 | Preporuka koncepta ovisila je o fizičkom poretku redaka u heapu. | **5.5** · 4 · 5.6 | ✅ popravljen | **3 fizička poretka, 3/3 predviđena ishoda**; `run_seed` piše novu verziju svih **30** koncepata pri svakom bootu |
| #61 | `submitted_query` se trajno pohranjuje u `agent_messages_log`, šire nego što je sudioniku rečeno. | **6** · 4 | 🟡 otvoren | **1568 od 7480** redaka nosi `submitted_query`; najstariji **2026-07-20**; iz hint puta **0 od 68** |
| #62 | Druga istovremena predaja se trajno odbacuje, ne odgađa. | **5.4** | ✅ popravljen | **1,0 uspjeha po rafalu** za K=2,3,4,8 (12 rafala); uspjeli ~**120 ms**, neuspjeli **15 012–15 070 ms**; **99 odbačenih** u 874 toka |
| #63 | Odgovor se izgubi (504), a pokušaj ostane zabilježen i BKT ažuriran. | **5.4** · 5.5 | ✅ popravljen | **3/3** reprodukcije: 504 uz **1 redak** u `attempts` i **2 BKT snapshota**; inform stiže **36 ms** nakon timeouta |
| #64 | Savjet za `row_mismatch` je nagađanje i u jednom slučaju dao netočnu tvrdnju o SQL sintaksi. | **5.5** · 5.6 | 🟡 otvoren | poredak detektiran u **40 od 80** zadataka, **proturječi u 10**, 2 bez poretka; **18 živih poziva**, izvorni slučaj **0 reprodukcija** |
| #65 | Model vraća Markdown, a slot ga je prikazivao doslovno. | **4** · 6 | ✅ popravljen | **2 od 4** živa savjeta nose `**` ili `` ` ``; `text-xs` = **10,24 px**; kontrast **17,23:1** |
| #66 | Tri M6 zadatka tvrdila su o bazi neistinu, a četvrti nije razlikovao ništa. | **3** · 5.5 | ✅ popravljen | od **5 zatečenih M6 zadataka zdrav samo 1** (81); Seq Scan **5,50** vs Index Scan **8,16** |
| #67 | `make backup` nikad nije radio iz čistog klona — skripta bez izvršnog bita. | **nijedno** · 5.6 | ✅ popravljen | mode **100644** umjesto 100755 |
| #68 | `column_alias` je dobio zadatke koje preporučivač nikad ne nudi (ZPD escape, druga potvrda). | **5.5** | 📌 prihvaćena limitacija | `p_l` **0,9356 > prag 0,85**, ponuđen **0 puta**; 4 sekundarna pojavljivanja |
| #69 | `plan_unavailable` je smetnju sustava zapisivao kao studentovu grešku. | **5.5** · 5.4 | ✅ popravljen | BKT šteta egzaktna: **0,80 → 0,4600** umjesto 0,9743; **0,50 → 0,2286** umjesto 0,9053; **92** `refuse` zapisa |
| #70 | `task_not_found` istekne umjesto da odgovori — jedina iznimka od pravila iz #69. | **5.4** · 5.6 | 🟡 otvoren | **504 nakon 9,09 s** (7 s + 2 s); 3 zahtjeva, `flow_count` **0 → 0** |
| #71 | Sustav se ponašao ispravno iz razloga koji nitko nije odlučio — nijedan test nije mogao pasti. | **5.6** | ✅ popravljen | ugovorni test s **48 tvrdnji**; skup tipova se čita iz izvora |
| #72 | Kad klasifikacija ne određuje dijagnozu, model rupu popuni iz opisa zadatka i izgovori je kao činjenicu o upitu. | **5.5** | ✅ popravljen | **12 stvarnih hintova**, pogođeni `execution_error` i `timeout` **2/2 prolaza**; katalog **32 → 40** redaka; kredit **5 → 5** |
| #73 | `OrchestrationFSM` se uklanja dvaput; `ValueError` se guta na svaku predaju. | **4** · 5.4 | 🟡 otvoren | **20 predaja → 20 iznimaka, 20/20** iste klase; `behaviours` **1 prije i 1 poslije** (nije curenje) |
| #74 | U jednoprocesnoj izvedbi agentske poruke ne prelaze mrežu — XMPP služi za autentikaciju. | **4** · 5.4 | 📌 prihvaćena limitacija | uz Prosody `exited`: **200 u 0,12–0,13 s**, pun lanac od **12 poruka**, burst **10/10** |
| #75 | Pod uvicornom iz Makefilea nijedan knjižnični zapis ne dolazi u log. | **4** · 5.6 | 🟡 otvoren | **0 redaka** sa `slixmpp`/`spade`; uz `basicConfig` isti prekid daje **7×** `connection_lost` |
| #76 | Tvrdnja o „dva sjemena" u falsifikaciji nije bila reproducibilna — drugo sjeme nigdje zapisano. | **5.6** | 🟡 otvoren | sjemena **20260814** i **20260818**, **3000 stanja, 0 povreda** |
| #77 | Kurikularni redoslijed nije izražen kao pravilo nego samo kao poredak injekcije. | **5.5** · 3 | 🟡 otvoren | savršen student: **prvi spoj korak 3**, `where_filter` **korak 7**; realističan **10/10 prolaza** pri stopama 0,7 i 0,5; tier prior **0,30 = `weak_threshold` 0,30** |
| #78 | Gate diskriminacije pokriva samo zadatke koje je autorska skripta napisala. | **5.6** · 3 | 🟡 otvoren | **1 od 5** aktivnih PLAN_CHECKED zadataka (**20 %**) izvan autorskog gatea — 81 je jedini, potvrđeno |
| #79 | Interni dijagnostički niz procurio je doslovno u tekst savjeta. | **5.5** · 5.6 | 🟡 otvoren | **0/12** namjerno pokvarenih upita pogodilo je granu koja bi nosila upit |
| #80 | Savjet za `row_mismatch` promašuje jer mu `detail` ne imenuje razliku — „siguran" tip s praznim sadržajem. | **5.5** · 5.3 | 🟡 otvoren | **0/2 pogotka**; kontrola: `wrong_columns`+`plan_mismatch` **2/2**, katalog **1/1** |
| #81 | `syntax_error` je kroz sučelje nedostižan — klijentski gard zatvara jedini ulaz. | **5.3** · 5.6 | 🟡 otvoren | **7 od 8** tipova nastalo kroz sučelje, `syntax_error` **0** |
| #82 | Stanje „Svi koncepti savladani" ne nastaje ni sa svim riješenim zadacima. | **5.3** · 6 | 🟡 otvoren | **88/88 riješeno, 0 pojavljivanja**; nakon **57.** zadatka CTA vrti isti zadatak uz **31 neriješen** |
| #83 | Zalutali ćirilični znak u tekstu savjeta (`vidišь`). | **nijedno** · 5.5 | 🟡 otvoren | **1 znak** (U+044C) u korpusu od 5 savjeta |
| #84 | Ispuštanje `ORDER BY` ocjenjuje se točnim jer se poredak izvodi iz teksta upita umjesto iz zadatka. | **5.5** · 5.3 · 5.6 | 📌 prihvaćena limitacija | **najmanje 44/88** (gornja granica 56); bez `LIMIT`-a **19/19** prolazi; popravak zatvara **12 od 44**, čini **22** zadatka plan-ovisnima |

---

## Koliko ih je po poglavlju

**Po težištu** (svaki nalaz broji se jednom — ovo je raspodjela posla po poglavljima):

| poglavlje | težište | spominje se ukupno |
|---|---:|---:|
| 3 — domenski model, koncepti, granularnost | **4** | 9 |
| 4 — implementacija, arhitektonske odluke | **25** | 36 |
| 5.3 — kompletan prolaz kroz sučelje | **2** | 4 |
| 5.4 — istovremenost | **3** | 6 |
| 5.5 — granice pristupa | **18** | 25 |
| 5.6 — valjanost instrumenta | **10** | 28 |
| 6 — rasprava, korisničko iskustvo | **9** | 18 |
| nijedno — operativno, bez vrijednosti za rad | **8** | 9 |
| **ukupno** | **79** | 135 |

**Po statusu:**

| status | broj |
|---|---:|
| ✅ popravljen | 33 |
| 📌 prihvaćena limitacija | 24 |
| 🟡 otvoren | 21 |
| 🚫 umirovljen | 1 |

## Nalazi bez brojke — 15 od 79 (bilo 21)

Izostanak brojke nije svugdje jednako težak. Nalaz o **implementaciji** („polje ne postoji
u API-ju") je činjenica koja se ne mjeri; nalaz o **granicama pristupa ili valjanosti**
bez brojke je **tvrdnja bez pokrića**. Zato su razdvojeni — popis koji sve trpa u isti koš
proizvodi lažne pozitive i postaje neupotrebljiv, isti razred kao 🔒 politika iz #50.

**Stanje nakon zadnjeg mjernog kruga (2026-08-18):** svih **6** nalaza iz skupine A je
izmjereno; **5 ih je dobilo brojku, 1 (#58) je zapisan kao nemjeren**. Preostalih **15**
su činjenice o implementaciji i operativi, gdje se brojka ne očekuje.

### A. ~~Traže mjerenje prije nego uđu u tekst~~ → **SVIH 6 IZMJERENO 2026-08-18**

Popis je zatvoren u posljednjem mjernom krugu. Ishod nije jednoličan i to je bitno:

| broj | ishod mjerenja |
|---|---|
| **#29** | 🔴 **Najveći nalaz kruga.** Nije anegdota nego obitelj: **20 od 30** koncepata dopušta formulaciju koja daje iste retke bez upotrebe koncepta, a oni su primarni koncept **61 od 88** zadataka. Provjereno po jedan zadatak za svaki, **20/20** prošlo sve tri provjere (retci · `evaluate()` · AST uz kontrolu nad referencom). |
| #18 | Lanac **min 2 · medijan 6 · max 43**; brisanje iz sredine najdubljeg invalidira **22** kasnije točke — polovicu povijesti koncepta. |
| #17 | **5 → 1** tvrdnji „N/N" (mjereno nad git poviješću, jer je tekst ispravljen u 4.4-0b); danas **5 e2e scenarija**, ali pokrivenost **nije 1:1**. |
| #39 | **3 od 16** `except` blokova u `agents/` nosi `# pragma: no cover`; **0 od 3** ima test koji ih vidi aktivirane — što pragma i deklarira. |
| #78 | Potvrđeno: **1 od 5** aktivnih PLAN_CHECKED zadataka izvan gatea; **81 je jedini**. |
| **#58** | 🔴 **MJERENJE NE ODLUČUJE.** 0/129 identičnih uzastopnih upita — ali prolaz konstrukcijom nikad ne ponavlja upit, pa nula opisuje **instrument**, ne sustav. #58 ostaje **nemjeren**; brojka se navodi samo uz ogradu ili se izostavlja. |

🔴 **#58 je jedini koji nije uspio, i to je zapisano kao neuspjeh.** Alternativa bi bila
navesti 0/129 kao rezultat — brojka bi bila točna, a zaključak lažan.

### B. Brojka se ne očekuje — 15 nalaza

Činjenice o implementaciji, operativi i odlukama. Idu u tekst kao tvrdnje, ne kao mjerenja;
gdje su sporedne, spuštaju se u fusnotu.

`#8` (4), `#9` (nijedno), `#10` (4), `#11` (4), `#12` (4), `#14` (4), `#15` (4), `#19` (3), `#21` (nijedno), `#22` (6), `#26` (nijedno), `#41` (6), `#43` (4), `#59` (6), `#49` (nijedno)

---

## Što mapa pokazuje kao cjelinu

- **Težište je u poglavlju 4** (25 nalaza) i **5.5** (18). Poglavlje 4 je time najveće po
  broju, ali 5.5 nosi najveće tvrdnje — ondje su sve prijetnje valjanosti.
- **Poglavlje 5.6 ima 10 nalaza o vlastitim mjernim sredstvima.** To je neuobičajeno mnogo
  i samo po sebi je rezultat: projekt je sustavno bilježio kad ga je vlastiti instrument
  iznevjerio (#55, #57, #71, #76, tri pravila iz #84).
- **5.3 i 5.4 su tanki po broju** (2 odnosno 3), ali oba su **potpuno pokrivena brojkama** —
  nastali su iz namjenskih mjerenja, ne iz usputnih opažanja.
- **21 nalaz je otvoren**, i to je stanje s kojim se ide u pisanje: većina ih je svjesno
  ostavljena uz zapisanu odluku (#29, #35, #44, #45, #59, #84), a ne previdom.
