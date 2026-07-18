# Faza 4.2 — Dashboard + Module overview — WRAP-UP

**Status:** ✅ KOMPLETNA (Stage 0 + 4.2a + 4.2b na grani `faza-4-2-dashboard`; PR "Faza 4.2" → `main` čeka push/potvrdu). Student vidi svoj napredak (XP/level/streak, mastery, bedževi), ima jasan CTA na sljedeći zadatak i pregled svih modula s locked/unlocked stanjima — sve s pravih endpointa, nula mocka.
**Obuhvat:** **Stage 0** (aditivni backend contract dodatak `/profile`), **4.2a** (Dashboard ekran + data sloj), **4.2b** (Module overview).
**Rezultat:** backend suite **467 passed / 1 skipped** (Stage 0 dodao 1 test; 0 regresija); frontend **`tsc -b` + build + oxlint + prettier zeleni**; **ručni** e2e dokazi kroz headless Chrome (CDP; svjež + populated user, obje teme) za oba ekrana — *nije* committed automatizirani suite (NALAZ #17); 2× `/code-review` (19 nalaza ukupno: 18 popravljeno, po 1 preskočen s razlogom po ekranu).
**Grane/PR/tagovi:** `faza-4-2-dashboard` · tagovi `faza-4-2a-dashboard` → `faza-4-2b-modules` · commitovi `73223b8` (Stage 0) → `89b974f` (4.2a) → `528e482` (4.2b).

Cilj cijele 4.2: prva dva **data ekrana** nad zaključanim ugovorom — uz podatkovni sloj (TanStack Query hookovi + domenske lib-ove) koji 4.3–4.5 nasljeđuju bez retrofita.

---

## 1. Stage 0 — `/profile` izlaže level-progres + mastery prag (jedina backend izmjena)

**Problem:** XP bar treba `xp % 100`, a locked/unlocked treba prag `0.85` — obje su backend konstante koje NISU bile u API-ju → frontend bi ih duplicirao preko mrežne granice.
**Rješenje (aditivno, TDD):** `ProfileResponse` + 4 non-null polja iz POSTOJEĆIH funkcija (`gamification_logic.progress_to_next_level`, `LEVEL_STEP`, `MASTERY_THRESHOLD` = mirror `rules.pl:11`):

```json
{ "xp_in_level": 90, "xp_to_next": 10, "level_step": 100, "mastery_threshold": 0.85 }
```

OpenAPI snapshot + `schema.d.ts` regenerirani u istom commitu (contract-change vidljiv u diffu). **Grep-invarijanta od sada: `0.85` i `LEVEL_STEP` ne postoje u frontend kodu** — sve dolazi iz `/profile`.

---

## 2. Što je 4.2a donijela (Dashboard)

### 2.1 Podatkovni sloj (nasljeđuju ga svi budući ekrani)
- **Hookovi** (`src/hooks/`): `useProfile` / `useModules` / `useNextTask` / `useTask(id)` / `useBadges` — svi kroz typed klijent + `unwrap` most (`src/lib/api/query.ts`: openapi-fetch ne baca → runtime `response.ok` check, **ne** tipizirana error grana). `useTask` koristi `skipToken` (gating + tipizacija na jednom mjestu, bez casta). Katalozi (`modules`/`badges`) `staleTime` 5 min; **`next-task` `staleTime` 60 s** (najskuplji read u sustavu — XMPP→Recommender→Prolog+BKT; bez toga svaki tab-focus okida cijeli agentski pipeline).
- **`lib/recommendation.ts`** — strojni `reason` → hrvatski tekst + semantička kategorija. Pokriva svih 8 vrijednosti iz koda (rules.pl: `weak_with_prereqs_met`/`partial_continuation`/`unlock_new`/`fallback`; recommender_logic: `exhausted`/`no_recommendation`; rubni `error`/`recommend_timeout`). **Fail-closed:** nepoznat reason uz `task_id=null` → "error" (retry), nikad slavljenička kartica. `exhausted` ≠ "sve savladano" (ponestalo taskova za JEDAN koncept) → neutralna kartica; samo `no_recommendation` slavi.
- **`lib/mastery.ts`** — `buildConceptIndex` (jedini izvor taksonomije: code→ime/tier/modul), `enrichMastery`, `masteryFillClass` (P(L)→token bucket).

### 2.2 Ekran
- **Hero:** level + XP bar (`xp_in_level/level_step` IZ API-ja) + streak (current/longest). Amber accent isključivo ovdje (gamifikacija).
- **CTA "Nastavi ovdje":** `/next-task` → naslov iz `/task/{id}` (preporuka nosi samo ID!) + tier chip + ljudski reason. `task_id=null` → done/error razlučeno. Onboarding varijanta za svježeg usera koristi generički tekst ("Odabrano prema tvojoj trenutnoj razini") jer reason `partial_continuation` na prioru laže ("nastavi gdje si stao" — nigdje nije stao).
- **Mastery highlights:** join mastery×modules; split po `mastery_threshold` ("Za ojačati" samo NESAVLADANI — ne po poziciji). Samo dirani koncepti (netaknuti = 4.2b teren).
- **Bedževi:** earned (`/profile.badges`) × katalog (`/badges`); `icon` je lucide ime (compass/star/link/ghost/fire) → statična mapa + `Award` fallback.
- **Empty state:** dizajniran onboarding (CTA + "kako sustav radi" trio), ne prazni grafovi.
- **`MasteryBar`** — JEDINI renderer progresa u appu: border-ani track (mastery-0/25 fillovi su <3:1 → track nosi granicu), fill transform-only (GPU), `motion-reduce` gate.
- `/task/:taskId` **stub ruta** (drži CTA navigaciju; ekran gradi 4.3).

### 2.3 Ključni code-review ulov 4.2a
**Query cache se nije čistio pri logout/login** → idući user u istom tabu na tren vidi podatke prethodnog. Fix: `queryClient.clear()` u `logout`/`login`/`register` (AuthProvider). Uz to: status-aware retry na QueryClientu (4xx se NE retrya — deterministički), paralelni warm `/next-task` fetch (ne čeka profile/modules gate).

---

## 3. Što je 4.2b donijela (Module overview)

### 3.1 🔴 Glavni nalaz faze: UI locked ≠ Recommender locked (i kako je razriješeno)
Recommender (`recommender_logic.build_mastery_snapshot`) NE koristi sirovi mastery za prereq provjeru:
- **Transverzalni glue** (modul 0, 0 primary taskova: `column_alias`, `join_condition`) → "prozirni": 0.99 čim je njihov `all_prereqs` (tranzitivni!) zatvarač savladan. `join_condition` k tome nema NI sekundarnih updateova → sirovi p_l mu nikad ne raste.
- **Subfloor** (modul ≠ 0, <2 taska: `right_join`, `insert`) → trajno maskirani kao savladani (nikad se ne preporučuju).

Naivno "svi direktni prereq-i sirovo ≥ prag" dalo bi **kontradikciju na ekranu**: Recommender preporuči `inner_join` (dokazano vlastitim e2e podacima), a Moduli bi ga pokazali zaključanim.

**Odluka (dokumentirana u `lib/progress.ts` headeru):** prereq zadovoljen = sirovo savladan ILI modul-0 čvor čiji su **svi tranzitivni ne-modul-0 preci** sirovo savladani (jedino zrcaljenje izvedivo iz `/modules`; modul 0 JE u API-ju, broj taskova NIJE).
**Poznati reziduali** (fix = budući contract dodatak, npr. `ConceptNode.has_tasks` — kandidat za 4.3 KORAK 0 ili Fazu 6):
1. `null_handling` (modul 0 S taskovima) — UI prozirno, Recommender normalno → UI može prerano otključati `agg_count`/`left_join`/`in_subquery` (samo informativni smjer; CTA slijedi Recommendera).
2. `right_join → full_outer_join` — UI konzervativniji od Recommenderove maske.

### 3.2 Ekran
- **6 modul-kartica** (order_index) + **odvojena transverzalna sekcija** (modul 0 nije ravnopravna kartica — dashed, s objašnjenjem "vježbaju se kroz zadatke ostalih modula"). Kartica: ime, description (nullable hendlan), **difficulty chip (magenta ×5)**, "X/Y koncepata savladano" + agregatni MasteryBar. Bez task-counta (nije u API-ju — odluka D).
- **Detalj = in-place Collapsible** (ne ruta): svi podaci stižu jednim `/modules` fetchom, ruta bi dodala loading stanja bez dobiti.
- **4 stanja koncepta** (ikona+tekst+boja, ne samo boja): ◌ nije-započeto · 🔒 zaključano ("Traži: <imena>" — mapirano code→ime) · ● u-tijeku (bar + %) · ✓ savladano. **Nije-započeto ≠ zaključan** (koncept može biti otključan a netaknut). Netaknuti NEMAJU p_l (tier prior se NE prikazuje — bila bi laž studentu). **Tier chip (violet ×3)** — skale razdvojene od difficulty.
- **E2E dokazi** (populated user sa savladanim select_basic+from_clause): otključali se `where_filter`, `distinct`, **`inner_join`** (poklapanje s Recommenderom ✓); `group_by → Traži: WHERE filtriranje` (cross-modul `column_alias` prozirno razriješen ✓); `COUNT → Traži: GROUP BY, NULL handling` (cross-modul hint po imenu ✓).

### 3.3 Ključni code-review ulovi 4.2b
- **Tranzitivnost prozirnosti** (direktni prereq nije dovoljan — `all_prereqs` semantika) — popravljeno closure-walkom.
- **`cursor-pointer` globalno nedostajao** na buttonima (Tailwind v4 preflight daje `cursor:default`; MASTER §7) — global base-layer fix, vrijedi za cijelu app od 4.1c.
- Multi-active nav na "/" (4 stavke istovremeno "aktivne" — stub flag gasi active na stubovima).
- Zaključan-a-diran koncept gubio vidljivi bar (regresija preduvjeta ne smije sakriti napredak).
- `Math.floor` za % (0.849 se ne smije prikazati kao prag-postotak uz "U tijeku").

---

## 4. Čemu ovo služi ostalim fazama

- **4.3 (Task screen):** nasljeđuje `useTask`, `recommendation.ts` mapper (isti za `/attempt.recommendation`), tier chipove, state-primitive obrasce; invalidacija `["next-task"]`/`["profile"]` nakon submita je NJEGOV posao (staleTime je postavljen s tim planom).
- **4.4 (Profil):** `BadgeStrip` join obrazac (katalog × earned) proširuje se u locked+unlocked galeriju; `masteryFillClass` ista skala za BKT krivulje.
- **4.5 (Leaderboard/Admin):** nav stub flag se samo miče po ekranu.
- **4.6 (Motion):** MasteryBar/chevron već poštuju motion tokene + reduced-motion.

---

## 5. Zaključane odluke / napomene za nasljednike

- **Nula backend konstanti u frontendu:** `level_step`/`mastery_threshold` dolaze iz `/profile` — grep na `0.85`/`100` (kao prag/step) mora ostati čist.
- **`MasteryBar` je jedini progres-renderer** (border-ani track invarijanta) — ne praviti druge.
- **Dvije skale, nikad miješati:** modul→difficulty (magenta ×5), koncept→tier (violet ×3). `TIER_LABEL` centralno u `ConceptChip.tsx`.
- **`recommendationKind` je fail-closed** — nova backend failure vrijednost padne u "error" (retry), ne u slavlje. Novi done-reason mora se eksplicitno dodati u `DONE_REASONS`.
- **Query cache je user-scoped** → `queryClient.clear()` na logout/login je nosiva invarijanta (ne razbiti u 4.3+).
- **`lib/progress.ts` je jedino mjesto unlock semantike** — 4.3+ ne smije replicirati vlastitu; ako treba drugdje, izvući, ne kopirati. Reziduali dokumentirani u headeru.
- **`/next-task` je skup** — ne dirati mu `staleTime` bez razloga; nakon attempta invalidirati, ne pollati.

### Errata-trail (ažurirano stanje nakon 4.2)
| # | Stavka | Stanje |
|---|---|---|
| ERRATA #8 | `attempts` nema `verdict` | Otvoreno — `partial` token i dalje neaktivan (4.3 prikazuje correct/incorrect) |
| flag #3 | `new_badges` best-effort | Otvoreno — Dashboard bedževe čita iz `/profile` (autoritativno), `new_badges` ostaje kozmetika za 4.3 |
| NALAZ #7 | `task.module_id ≠ primary_concept.module` (3/83: taskovi 71–73, correlated_subquery u "DML operacije") | **Ne materijalizira se u 4.2** — Module overview računa iz koncepata, ne iz task.module_id. Rizik ostaje za 4.3 ako Task screen prikaže modul iz `task.module_id`. Cleanup Faza 6 |
| NALAZ #9 | Leaderboard testovi nisu izolirani od dev usera | **Ponovljeno u 4.2a** (inventar-user srušio 2 testa) — sanirano brisanjem; svi e2e useri se od sada brišu prije pytest-a. Trajni fix = 4.5/6 |
| **NOVO #10** | UI unlock ≠ Recommender unlock za `null_handling` + subfloor | Djelomično zrcaljeno (modul-0 prozirnost); reziduali dokumentirani u `progress.ts`. Pravi fix: contract dodatak `has_tasks` (kandidat 4.3 KORAK 0 / Faza 6) |
| **NOVO #11** | `NextTaskResponse` bez naslova | Dashboard CTA plaća drugi hop (`/task/{id}`) za jedan string; 4.3 solve-petlja isto. Kandidat: aditivno `title` polje (uz #10 u istom contract dodatku) |

---

## 6. Sljedeće na redu

**Faza 4.3 — Task screen (⭐ eval-kritični checkpoint):**
1. **KORAK 0 prijedlog:** mini contract dodatak (aditivno): `ConceptNode.has_tasks` (#10) + `NextTaskResponse.title` (#11) — oba su read-only polja, TDD kao Stage 0.
2. Ekran: opis + ER dijagram (statički `ecommerce_v1`) + sample preview kroz `/run` · Monaco (custom tema iz 4.1b čeka) · Run (`/run`) vs Submit (`/attempt`) · feedback (`error_type` → ljudski tekst; SAMO correct/incorrect — ERRATA #8) · `new_badges` kozmetika · invalidacija `["next-task"]`/`["profile"]` nakon submita.
3. Skill-lanac isti; `/review-animations` gate za editor-feedback prijelaze.

> Nakon 4.3 sustav je eval-upotrebljiv (jezgra 4.0–4.4 prije 4.6/4.7 polisha). PR "Faza 4.2" → main čeka push + potvrdu mergea.
