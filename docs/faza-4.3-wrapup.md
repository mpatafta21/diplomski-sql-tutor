# Faza 4.3 — Task screen (⭐ eval-kritični checkpoint) — WRAP-UP

**Status:** ✅ KOMPLETNA (Stage 0 + Stage 0b + 4.3a + 4.3b + 4.3c na grani `faza-4-3-task-screen`; PR "Faza 4.3" → `main` čeka push/potvrdu — sandbox ne može push). **Nakon ove faze sustav je EVAL-UPOTREBLJIV**: student odrađuje pun ciklus dohvati → piši SQL → Run → Submit → feedback → sljedeći zadatak, sve protiv živog agentskog backenda.
**Obuhvat:** **Stage 0** (aditivni contract dodatak `primary_task_count`), **Stage 0b** (migracija `attempts.detail` + `feedback.detail` — ZADNJA backend izmjena, ugovor zaključan do eval-a), **4.3a** (statika + Monaco), **4.3b** (Run petlja), **4.3c** (Submit petlja + feedback).
**Rezultat:** backend suite **471 passed / 1 skipped** (467 ulaz + 4 nova testa; 0 regresija); frontend **`tsc -b` + build + oxlint + prettier zeleni**; **ručna** e2e verifikacija kroz headless Chrome (CDP, živi backend): 4.3a **21 scenarij** · 4.3b **27 scenarija** · 4.3c pun ciklus **28 scenarija** — *nije* committed automatizirani suite (NALAZ #17); 3× `/code-review` (26 nalaza ukupno: 25 primijenjeno, 1 potvrđen kao ugovorni limit → NALAZ #12), `/review-animations` gate (2 Block nalaza, oba popravljena), `accessibility-review` (0 kritičnih; partial-vs-accent numerički dokaz).
**Grane/PR/tagovi:** `faza-4-3-task-screen` · tagovi `faza-4-3a-task-static` → `faza-4-3b-run` → `faza-4-3c-submit` · commitovi `1418a9f` (Stage 0) → `dcbef43` (Stage 0b) → `36a1a9d` (4.3a) → `43d3632` (4.3b) → `6d33946` (4.3c).

Cilj cijele 4.3: srce eval-a — kompletna petlja rješavanja zadatka nad zaključanim ugovorom, s feedbackom koji je **tutor, ne semafor** (pedagoški detail, tri stanja, hrvatske poruke po značenju greške).

---

## 1. Stage 0 + 0b — zadnje backend izmjene (ugovor ZAKLJUČAN)

### 1.1 `ConceptNode.primary_task_count` (Stage 0 — NALAZ #10 fix)
`/modules` sada po konceptu vraća **broj aktivnih PRIMARY taskova** (COUNT, ne boolean — Recommender razlikuje TRI kategorije: glue `0` / subfloor `<2` / normalni `≥2`). Ista semantika kao `recommender_logic._concept_task_stats` (zrcaljeni LEFT JOIN — privatni helper se ne importa preko granice modula). Živo: `join_condition=0`, `column_alias=0`, `null_handling=4` (modul 0 S taskovima!). UI unlock logika (`lib/progress.ts`) od sada može zrcaliti Recommenderove kategorije bez divergencije.

### 1.2 `attempts.detail` + `feedback.detail` (Stage 0b — Opcija A, pedagoško srce)
- **Problem:** `EvaluationOutcome.detail` ("Stupci se razlikuju — dobiveni: […], očekivani: […]") umirao je unutar EvaluatorAgenta — nije se persistirao, a Coordinator gradi feedback IZ DB reda. "Samo prosljeđivanje kroz routes.py" nije postojalo.
- **Odluka (Opcija A):** nullable kolona `attempts.detail` (migracija **`e7c41f0a2b91`**, up+down oba dokazana) — uklapa se u postojeći dizajn (Coordinator čita iz DB-a), nula FIPA promjena. Evaluator persistira postojeći detail (correct → NULL, placeholder "OK" se ne sprema); `FeedbackModel.detail` + `AttemptItem.detail` (povijest za 4.4 besplatno).
- **🔴 Sigurnosni guard (grana po grana, živo potvrđeno):** detail NIKAD ne sadrži `expected_query` ni sadržaj očekivanih redaka — `ComparisonResult.first_mismatch` (jedini nosilac očekivanog retka) ostaje izvan API-ja. Izloženo samo: imena očekivanih stupaca (ionako u opisu zadatka), brojevi redaka, PG poruka studentovog vlastitog upita.

---

## 2. Što je 4.3a donijela (statika + Monaco)

- **Split layout** (opis+shema / editor, xl 5fr/7fr), keyed struktura koja 4.3b/c nasljeđuju.
- **🔴 NALAZ #7 — breadcrumb IZ PRIMARNOG KONCEPTA**, nikad `task.module_id` (kriv za 3/83): `concepts[is_primary]` → `buildConceptIndex` → modul. **Dokazano na tasku `correlated_subquery_d3_d9c8f988`: "Podupiti", ne "DML operacije".** (Numerički id je tada bio 71, danas 60 — koristi `source_id`, NALAZ #21.)
- **Statička shema referenca** (`lib/sandbox-schema.ts`): 1:1 mirror `init.sql` (8 tablica, PK/FK uklj. self-FK, kompozitni UNIQUE) s **guard komentarom + SHA-256 manifesta** — ako se sandbox shema promijeni, datoteka se MORA ažurirati. Collapsible tablice, mono identifikatori, FK kao `→ tablica.stupac`.
- **Monaco self-hosted** (obrazac projekta — nula CDN-a, dokazano network captureom): `loader.config({ monaco })` + Vite `?worker` (SQL nema language worker — editorWorkerService dovoljan). Custom dark/light teme iz 4.1b tokena; theme toggle mijenja editor. **TaskPage je lazy ruta** — monaco chunk (3.6 MB) izvan glavnog bundlea.
- **Skale razdvojene:** `TaskDifficultyChip` (task difficulty 1–5 → magenta; 4 i 5 dijele `expert` jer `cross_module` nije rank) vs `ConceptChip` (tier violet).
- Ključni review ulovi: monaco akcije registrirane **samo uz postojeći handler** (bezuvjetna registracija guta Shift+Enter newline), kanonski task ID (`/^\d+$/` — `0x2A` bi aliasirao task), breadcrumb `<li>` separatori, mac-aware kbd (⌘/Ctrl), `useMemo` conceptIndex + `memo` SchemaReference (bez rebuilda po keystroku).

## 3. Što je 4.3b donijela (Run petlja)

- **`useRun` mutation:** `/run` UVIJEK vraća 200 — SQL greška je **podatak** (`error` polje), ne mrežna greška; **NULA invalidacija** (ništa se ne persistira — dokazano: 8 runova, 0 `/profile` poziva, `attempts` tablica prazna).
- **RunResultPanel:** `columns` array je **AUTORITET** (ćelija = `row[col]`, nikad `Object.keys`); sirovi PG error u mono bloku (`whitespace-pre` — LINE/caret se poklapa s Monaco linijama; "Upit nije prošao" ≠ ocjena); 0 redaka = legitiman ishod; NULL ćelije vidljive; **cap 200 renderanih redaka** (3000-row upit: 234 ms, bez smrzavanja); hrvatski plural (nominativ + genitiv iza "od").
- **Keyed `TaskView`** — promjena `:taskId` ne remounta route element; key resetira SQL/rezultat (kasnije i feedback) po tasku.
- **`/review-animations` gate:** flash-of-skeleton na re-Run (najfrekventnija akcija) → skeleton samo za PRVI Run, na re-run stari rezultat ostaje uz dim s tranzicijom (`lastResult` state — v5 `mutate()` briše `data` na pending, verificirano u query-core kodu).
- Ostali ulovi: stabilan `onRetry` (memo tablice stvarno radi), retry ponavlja zadnji POSLANI upit (ne obrisani editor), `border-separate` (sticky header uz `border-collapse` gubi rub), `Kbd` dedup u `ui/kbd.tsx`.

## 4. Što je 4.3c donijela (Submit petlja — feedback)

### 4.1 🔴 TRI feedback stanja — ERRATA #8 REVIDIRAN (partial AKTIVIRAN)
`verdict` kolona i dalje ne postoji, ali je partial **deterministički izvediv**: backend `row_mismatch` ⇔ interni verdict "partial" (evaluation.py:186 je jedini izvor). **Derivacija iz `error_type === "row_mismatch"`, NE iz `xp_delta>0`** — review dokazao da je xp_delta best-effort read (Gamification teče PARALELNO s Coordinatorovim RESPOND-om; degradirani put xp_delta=0 bi partial obojio crvenim "Netočno" uz poruku "Stupci su točni…"). Živo dokazano: ⚠️ "Djelomično" + "+8 XP" (`bg-partial-soft` u DOM-u), NE "Netočno". **MASTER.md §2.2 + §8 revidirani u istom diffu** (SSOT više ne brani partial; propisuje ikona+tekst kanal).

### 4.2 error_type mapa + detail (lib/feedback.ts)
Svih 7 vrijednosti + null, **fail-closed** (nepoznat → generička greška, nikad slavlje). Nazivi varaju — mapirano po ZNAČENJU: `syntax_error` = prazan/neprepoznatljiv upit ("Nisi poslao upit"), `execution_error` = prave SQL greške. **Detail prikaz:** hrvatski pedagoški (wrong_columns nabraja stupce, empty_result broj redova) = čitljivi tekst; sirove PG poruke i interni engleski ("Row 0 differs") = **diskretan mono blok** ISPOD hrvatske glavne poruke — tehnički detalj, ne izgleda kao kvar.

### 4.3 XP / level / badge (živi dokazi)
- **Apsolutni `xp`, nikad suma delti** — badge XP nije u delti (dokaz: ukupno 28 > suma delti 18; `first_correct` +10 ide kroz `xp_log` s `attempt_id=NULL`).
- **Level-up deriviran** (nema flaga): prethodni level iz `/profile` cachea koji `useSubmitAttempt.onSuccess` **patcha autoritativnim snapshotom iz odgovora** prije invalidacije (bez patcha: lažni "Novi level!" lanac na CTA navigaciji — cache bez observera se ne refetcha). Celebracija SAMO uz `xp_delta>0` (best-effort level ne smije sjesti na netočan pokušaj). Cache-miss → bez celebracije.
- **`new_badges` = kozmetika** (flag #3): unlock čip iz odgovora, autoritativno stanje iz `/profile`.
- **Invalidacije nakon Submita:** `["profile"]` `["next-task"]` `["attempts"]` (za razliku od Run-a!). Dokaz: povratak na dashboard refetcha oba unatoč staleTime.
- **Dva timeouta razdvojena:** HTTP 504 (agent pipeline; `submitSlot="gateway"` + retry zadnje predaje) ≠ `error_type:"timeout"` (200; studentov SQL predug).
- **CTA "Sljedeći zadatak"** reusa `recommendation.ts` mapper (fail-closed; `task_id=null` → done/error razlučeno); keyed remount čisti SQL+rezultat+feedback.

### 4.4 🔴 A11y — partial vs accent-warm (izmjereno, ne "približno")
4.1b upozorenje se materijaliziralo: ΔE(OKLab) partial↔accent-warm(-text) **0.044–0.056**, pod protan/deutan simulacijom RGB dist **31–61/441** — boja sama NIJE pouzdan kanal (skripta `a11y-partial.py`). Rješenje: verdict UVIJEK nosi **ikona + tekst** (⚠ TriangleAlert + "Djelomično"), XP chip razlučiv i formom (ispunjen + tamni tekst). Kontrast `text-partial` AA ✓ (8.68:1 dark / 5.50:1 light). **Kandidat trajne korekcije: pomak partial hue 60→45** (traži rekalibraciju 4.1b tokena — odluka za 4.7).

### 4.5 Motion (jedino nagradno mjesto u appu)
Pop-in panel (`zoom-in-95`, 240 ms, entrance ease), XP/badge čipovi `ease-reward` overshoot na 240 ms (review-animations Block: 700 ms `duration-reward` je za count-up envelope 4.6, ne za entrance frekventne akcije), badge stagger 60 ms, `motion-reduce` svugdje, **nula konfeta**.

---

## 5. Čemu ovo služi ostalim fazama

- **4.4 (Profil):** `/attempts` povijest sada nosi `detail` (Stage 0b besplatno); `BADGE_ICON` izvučen u `lib/badge-icons.ts` (treći potrošač = galerija); `["attempts"]` invalidacija već žicana — 4.4 samo doda query.
- **4.5 (Leaderboard/Admin):** nav stub obrazac se samo miče po ekranu (kao 4.2→4.3).
- **4.6 (Motion):** `--duration-reward` (700 ms) namjerno NEKORIŠTEN — rezerviran za count-up envelope; FeedbackPanel je referentno mjesto za reward motion.
- **4.7 (QA):** partial hue korekcija (60→45) čeka odluku; `a11y-partial.py` skripta je ponovljiva provjera.
- **Eval (Faza 6):** pun ciklus + `skill_mastery_history` + `feedback.detail` = svi podaci za analizu teku od sada.

---

## 6. Zaključane odluke / napomene za nasljednike

- **Backend ugovor ZAKLJUČAN** (Stage 0b je zadnja izmjena do eval-a). `NextTaskResponse.title` ODBIJEN (dvostruki hop radi i cachiran je); `GET /schema` ODBIJEN (ER statički iz init.sql).
- **`deriveVerdict` ide preko `error_type`** — ne mijenjati na xp_delta proxy (race s paralelnim Gamificationom). `lib/feedback.ts` je jedino mjesto verdict semantike.
- **`/profile` cache se patcha iz `/attempt` odgovora** (`useSubmitAttempt.onSuccess`) — nositelj level-up derivacije; ne razbiti pri 4.4+ refaktorima.
- **Run ≠ Submit invarijante:** Run NULA invalidacija / Submit tri; Run bez verdicta; oba hotkeya registrirana SAMO uz handler od prvog rendera (mount-time — dokumentirano u SqlEditoru).
- **Keyed `TaskView`** = jedini mehanizam per-task resetiranja (SQL/rezultat/feedback) — nova per-task stanja MORAJU živjeti u TaskViewu, ne iznad.
- **`lib/sandbox-schema.ts`** se ažurira uz SVAKU promjenu sandbox sheme (SHA guard u headeru).
- **Monaco:** self-hosted invarijanta (nula CDN-a); jsdelivr string u chunku je inertna loader konstanta.
- **E2e useri:** jedinstveni sufiks po runu + brisanje SVIH ovisnih tablica (Submit stvara attempts/xp_log/mastery/streaks!) — NALAZ #9 disciplina.

### Errata-trail (ažurirano stanje nakon 4.3)

> 📌 **Kanonski popis je od Faze 4.4-0g u [`docs/errata.md`](errata.md)** — ondje su svi
> nalazi sa statusom (uklj. #14, #15, #24, #25, #26 kojih ovdje nema). Tablica ispod je
> povijesni zapis stanja nakon 4.3 + zatvaranja iz 4.4-0b…0f.
| # | Stavka | Stanje |
|---|---|---|
| ERRATA #8 | `attempts` nema `verdict` | ✅ **REVIDIRAN** — partial AKTIVAN (deriviran iz `error_type=row_mismatch`); kolona i dalje ne postoji (nije ni potrebna) |
| flag #3 | `new_badges` best-effort | Riješeno po dizajnu — kozmetika u FeedbackPanelu, autoritativno `/profile`; ostaje trajna karakteristika |
| NALAZ #7 | `task.module_id` kriv (3/83) | **Mitigiran u UI** (breadcrumb iz primarnog koncepta). Stabilni ključevi: `correlated_subquery_d3_d9c8f988`, `correlated_subquery_d4_7101bea2`, `correlated_subquery_d5_7948781f` (numerički id-evi 71–73 → danas 60–62, NALAZ #21). Data cleanup i dalje Faza 6 |
| NALAZ #9 | test/dev useri ruše asserte | ✅ **ZATVOREN u 4.4-0b** — leaderboard testovi kohortno skopirani (tvrdnje na useru koje test sam kreira: relativni redoslijed + monotoni rankovi + `total >= len(kohorta)`), bez diranja `routes.py`. `pytest` 471/1 zelen DOK `demo44_student` postoji u bazi |
| NALAZ #10 | UI unlock ≠ Recommender | ✅ **ZATVOREN** — `primary_task_count` u `/modules`; `lib/progress.ts` može zrcaliti kategorije (dovršiti spajanje u 4.4+ ako zatreba) |
| **#10b** | `primary_task_count` bio izložen ali NIKAD konzumiran u UI-ju | **PONOVNO OTVOREN u 4.4-0c**, ✅ **ZATVOREN u 4.4-0e**. Polje je od 4.3 stajalo mrtvo (postojalo samo u `schema.d.ts`), pa je M6 renderiran kao običan modul: „0 / 2 koncepata savladano" + „Zaključano · 10 % · Traži: GROUP BY, JOIN 3+ tablica" — obećanje otključavanja za koncepte koji se NIKAD ne mogu dovršiti. Sada `deriveProgress` ima 5. stanje `unavailable` (`primary_task_count === 0`, izvan modula 0) → „Nema zadataka", bez bara/postotka/prereqa; `ModuleCard` prikazuje „Nema dostupnih zadataka". Komentar u kodu veže polje na #10/#10b da ga refaktor ne obriše kao mrtvo |
| NALAZ #11 | `NextTaskResponse` bez naslova | ✅ **ZATVOREN kao odbijen** — dvostruki hop prihvaćen (cachiran) |
| **NOVO #12** | `/run` rows dict kolabira duplikat stupce s RAZLIČITIM vrijednostima (`SELECT o.id, c.id`) | UI caveat ugrađen (upozorenje + preporuka AS aliasa); pravi fix = contract promjena (rows kao arrayevi) — kandidat Faza 6 |
| **NOVO #13** | partial hue 55–60 preblizu accent-warm 70–85 | Ikona+tekst kanal obavezan (ugrađeno, MASTER §2.2); trajna korekcija hue→45 = kandidat 4.7 |
| **NOVO #17** | frontend NEMA committed e2e suite | Brojke „N/N" u 4.1–4.3 wrapupima bile su **ručne** verifikacije kroz headless Chrome (CDP, živi backend), **ne** reproducibilan runner — `@playwright/test`/`vitest` nisu u `package.json` (samo `oxlint` + `prettier`). Formulacije ispravljene u 4.4-0b (ne izmišljamo suite da brojke postanu istinite). **Smoke suite = ulazni gate za eval (4.7)** |
| **NOVO #18** | BKT `skill_mastery_history` je **REKURZIVAN LANAC** | Svaka točka je posterior izračunat IZ PRETHODNE (`BKT(p_l0=row.p_l)`), nije nezavisan uzorak. **Brisanje točke iz SREDINE lanca invalidira sve kasnije točke tog koncepta** — one su računate iz zagađenog priora. Legitimno čišćenje je ILI (i) brisanje REPA od zagađene točke nadalje, ILI (ii) potpuni re-run BKT-a nad preostalim attemptima kronološki. „Vrati na zadnji snapshot" vrijedi **samo** ako je zagađena točka bila ZADNJA. Čišćenje u 4.4-0d **jest** bilo ispravno (provjereno: zagađeni attempt bio je 28/28, dakle zadnji u lancu za `where_filter`). Procedura kodirana u `scripts/purge_polluted_attempts.py` — po defaultu ODBIJA brisanje iz sredine lanca, `--allow-tail-truncate` je eksplicitan pristanak. **Obavezno pročitati prije čišćenja eval podataka (Faza 6)** |
| **NOVO #19** | Modul 6 je **IZVAN OPSEGA EVALUACIJE** | 2 koncepta (`explain_plan`, `index_usage`), 5 taskova — evaluacijska jezgra ih ne zna ocijeniti (plan-presence put nije implementiran). Od 4.4-0e ulaze **`is_active=False`** izvedeno iz `UNSUPPORTED_CONCEPTS` u `scripts/import_dataset.py`, pa to **preživljava re-import** (i automatski se vraća ako plan-presence evaluacija bude gotova). **Formulacija za rad: opseg evaluacije je 5 evaluabilnih modula (M1–M5) + transverzalni M0; M6 je deklariran kao bonus izvan opsega.** POSLJEDICA: bedž `explorer` (traži pokušaj u svih 6 modula) je **nedostižan** dok je M6 izvan opsega |
| **NOVO #23** | DML evaluacijska rupa (9/83 taskova) postojala od **Faze 2**, nikad pokrivena testom | `agents/evaluation.py` hardkodirao je `dml=False` pa je svaki INSERT/UPDATE/DELETE padao na „permission denied" (`execution_error`) — student bi na točan DELETE vidio „Greška u SQL-u". Writable put (`sandbox_readwrite` + transakcija + ROLLBACK) postojao je i bio testiran u `test_sandbox_runner.py`, ali ga studentski put nikad nije koristio; `test_evaluation.py` nije imao NIJEDAN DML test (nije regresija — nikad nije bilo pokriveno). Popravljeno u 4.4-0d (derivacija iz `DML_CONCEPTS`), sada pokriveno s **10 novih testova** (5 DML e2e + ROLLBACK invarijanta + readonly regresija + 5 recommender) |
| **NOVO #20** | **Task bank nije bio pod verzijom (P0)** | `data/generated_tasks/` bio je gitignoran u cijelosti → 83 zadatka postojala su SAMO lokalno i u DB-u: nereproducibilan artefakt rada u jednom primjerku. ✅ **ZATVOREN u 4.4-0f**: kanonski `final_dataset.json` (114 KB, version 2b-3) je pod verzijom; LLM međukoraci (pilot/failed/validated/raw, ~680 KB) ostaju ignorirani — to je i bio izvorni razlog ignorea. Provjereno: 0 tajni, nema prompt/model/cost polja. Ignore je morao biti popravljen na DVA mjesta (root + nested `.gitignore`, koji ima prednost). **Dataset se NE regenerira kroz LLM bez izričite odluke** |
| **NOVO #21** | **Task ID je nestabilan preko reseeda** | `docker compose down -v` resetira SERIAL → svi numerički id-evi se pomaknu. Dokaz: NALAZ #7 taskovi bili 71–73, nakon 0e su 60–62; M6 bio 90–94, sada 79–83. Sva dokumentacija koja citira brojeve od tada je netočna. **INVARIJANTA: `task_id` je runtime detalj, `source_id` je KANONSKI ključ — dokumentacija, testovi i izvještaji koriste `source_id`.** Sweep od 0f ispisuje `source_id` uz svaki task; testovi rade lookup po `source_id` |
| **NOVO #22** | `explorer` bio NEDOSTIŽAN | Kriterij je bio hardkodiran `EXPLORER_MODULES={1..6}`, a M6 je od 4.4-0e izvan opsega (NALAZ #19) → bedž nedostižan SVAKOM studentu, a galerija (4.4a) ga je i dalje prikazivala s kriterijem koji se ne može ispuniti. ✅ **ZATVOREN u 4.4-0f opcijom (i) — DINAMIČKI**: kriterij = moduli koji STVARNO imaju aktivne zadatke (`BadgeFacts.evaluable_modules`, trenutno {1..5}); automatski se proširi ako M6 ikad postane evaluabilan. `eval_badges` ostaje čist (fakti se injektiraju), fail-closed na prazan skup. Opis bedža i Prolog mirror usklađeni sa stvarnim kriterijem |
| **#19 dopuna** | `/task/{id}` bio zadnja zaobilaznica | Recommender neevaluabilne koncepte više nije nudio, ali je izravan URL i dalje otvarao M6 task (200) → student je mogao predati rješenje i dobiti `unsupported_eval` (0 XP + BKT kazna koja curi na evaluabilne sekundarne koncepte). ✅ **ZATVOREN u 4.4-0f**: `_read_task_detail` tretira neaktivan task kao nepostojeći (404). `schemas.py` nedirnut, `openapi.json`/`schema.d.ts` byte-identični; frontend to već pokriva postojećim `ErrorState` (provjereno živo — nema bijelog ekrana) |
| 🔒 **ZAMRZNUTO** | **Backend je nakon 4.4-0f TVRDO ZAMRZNUT** | Do kraja evaluacije svaka izmjena backenda (rute, sheme, agenti, evaluator, BKT, gamifikacija) je **eskalacija, ne rutina** — traži izričitu odluku i ponovni prolaz kroz `make sweep` + puni `pytest`. Frontend (4.4b+) i dalje smije raditi protiv zamrznutog ugovora |
| pre-existing lint | oxlint fast-refresh warninzi (4) | Ista tolerirana klasa kao na mainu; lint-hardening zaseban |

---

## 7. Sljedeće na redu

1. **Push + PR "Faza 4.3"** → `main` (ručno — sandbox ne može push); nakon mergea `alembic upgrade head` gdje god backend vrti (migracija `e7c41f0a2b91`).
2. **Faza 4.4 — Profile/Stats:** badge galerija (locked+unlocked: `/badges` × `/profile`; `BADGE_ICON` iz lib-a), povijest pokušaja (`/attempts` — sada s `detail`; `Page` envelope, paginirano), **BKT P(L) krivulje** (`/mastery-history`, Recharts — instalacija tek tada), stats sažetak. Skill-lanac isti.
3. Paralelno ništa ne blokira — jezgra 4.0–4.4 na putu da bude eval-spremna prije 4.5–4.7 polisha (4.3 je bio kritični prag ✓).
