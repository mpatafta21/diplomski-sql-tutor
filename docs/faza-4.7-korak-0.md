# Faza 4.7 — KORAK 0: inventar polisha (READ-ONLY)

**Datum:** 2026-07-26 · **Grana:** `faza-4-7-polish` (otvorena iz čistog `main`)
**Opseg:** nula izmjena koda. Nula backend izmjena. Ovo je istraga.
**Kontekst koji mijenja prioritete:** evaluacija se **NE** radi u labosu. Aplikacija ide na javni
URL, studenti se sami registriraju i rade asinkrono bez nadzora. Nema usmenih uputa, nema
pripremljenih računa, nema nikoga tko pomaže kad nešto pukne.

---

## KORAK -1 — GIT GATE ✅ PROŠAO

```
$ git log --oneline -8 main
a08b7c0 Merge pull request #25 from mpatafta21/faza-4-6-eval-fixes
046ffa0 feat(4.6-eval): klik na koncept → zadatak (Moduli + Dashboard) + recommender doc
b46e11e feat(4.6-eval): eval self-test fixevi — nav Zadatak, first-solve XP, breadcrumb deep-link
c2c9ed6 Merge pull request #24 from mpatafta21/faza-4-6-eval-prep
a8904f1 docs(4.6-eval): mikro-provjera — orphan FIPA tokovi i zamka recikliranja attempt_id
49cb0a8 feat(ops): faza-4.6-eval — backup s verificiranim restoreom, export, čist baseline, runbook
a7df7c1 feat(docs): add wrap-up for Faza 4.5 — Leaderboard and Admin features
8e09fde Merge pull request #23 from mpatafta21/faza-4-5-leaderboard-admin

$ git branch --contains faza-4-5-leaderboard-admin
  faza-4-5-leaderboard-admin
  faza-4-6-eval-fixes
  faza-4-6-eval-prep
  fix/turn1
* main                     ← ✅ 4.5 JE u main

$ git branch --contains faza-4-6-eval-prep
warning: refname 'faza-4-6-eval-prep' is ambiguous.
  faza-4-6-eval-fixes
  faza-4-6-eval-prep
  fix/turn1
* main                     ← ✅ 4.6-eval JE u main

$ git status
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

Oboje u `main`, tree čist → otvorena grana `faza-4-7-polish`.

---

## A — ŠTO JE ERRATA OSTAVILA OTVORENO (vizualno / a11y / UX)

Filtrirano iz `docs/errata.md` na 🟡/📌 nalaze koji diraju vizualni/a11y/UX sloj.

| # | Tema | Status | Rješiv u frontendu? | Opseg |
|---|---|---|---|---|
| **#13** | partial hue 55–60 preblizu accent-warm 70–85 | 📌 mitigiran | **DJELOMIČNO** (vidi §A.1) | tokeni + 2 mjesta dokumentacije, **0 komponenti** |
| **#33** | mastery gradijent, donji stopovi < 3:1 | 📌 limitacija (mjereno) | **NE — ZABRANJENO DIRATI** (vidi §A.2) | — |
| **#17** | frontend nema committed e2e suite | 🟡 otvoren | **DA** | veće (nova dev-dep + suite) |
| #12 | `/run` rows dict kolabira duplikate stupce | 🟡 otvoren | NE (contract) | — (Faza 6) |
| #7 | `task.module_id` ≠ modul primarnog koncepta (3/83) | 🟡 otvoren | već mitigiran u UI-ju | 0 (ne dirati) |
| #14 | `earned_at` bedža nije u API-ju | 📌 limitacija | NE | 0 |
| #15 | `/attempts` bez server-side filtera | 📌 limitacija | NE | 0 |
| #16 | P(L) saturira, plato je istina | 📌 svojstvo modela | NE (UI to svjesno ne skriva) | 0 |
| #32 | Recharts v3 `tabindex=0` na svaki graf | ✅ 4.4b | — | **regresijski rizik pri svakom novom grafu** |
| #34 | duplikati u `agent_messages_log` | 📌 zatečeno | označeni, ne skriveni (4.5b) | 0 |
| #36 | `/admin/agent-logs` tiho capira limit na 200 | ✅ izložen u UI-ju | — | 0 |
| #42 | indikator „riješeno" na Modulima | 🟡 odgođen → Faza 6 | **NE** (traži user-aware `/modules`) | — |
| #44 | preporučivač skače među temama | 📌 dizajn | **DA — samo objašnjenje** (vidi §F.6) | jedna rečenica |
| 🔒 DOC | a11y tvrdnja nosi izmjerenu brojku + datum | 🔒 politika | vrijedi za sve što 4.7 napiše | — |

### A.1 — #13 razlučen: što bi „trajna korekcija hue→45" stvarno tražila

**Zatečene vrijednosti** (`frontend/src/index.css`):

| Token | Light | Dark |
|---|---|---|
| `--incorrect` | `oklch(0.53 0.19 25)` | `oklch(0.70 0.19 25)` |
| `--partial` | `oklch(0.53 0.11 55)` (:177) | `oklch(0.78 0.13 60)` (:250) |
| `--partial-soft` | `oklch(0.96 0.02 60)` (:178) | `oklch(0.24 0.04 60)` (:251) |
| `--accent-warm` | `oklch(0.66 0.13 72)` (:181) | `oklch(0.80 0.15 80)` (:254) |
| `--accent-warm-text` | `oklch(0.56 0.12 70)` (:183) | `oklch(0.80 0.15 80)` (:256) |

**Hue udaljenosti — zatečeno vs hue→45:**

| | do `incorrect` (25) | do `accent-warm` |
|---|---|---|
| light, sad (55) | Δ30 | Δ15 (vs `accent-warm-text` 70) |
| light, →45 | Δ20 | **Δ25** ✅ poboljšanje |
| dark, sad (60) | Δ35 | Δ20 (vs 80) |
| dark, →45 | Δ20 | **Δ35** ✅ poboljšanje |

**Presuda: korekcija je izvediva i NE ruši cross-scale guard, ali guard mora biti prepisan.**
MASTER §2.7 točka 4 propisuje hue mapu **„25 incorrect · 55 partial(rezerv.) · 70–85 accent ·
150 correct · 190–260 mastery · 300 tier · 345 difficulty"**. Pomak na 45 rješava koliziju s
accentom (koja je stvarni problem — oba su „topla" i partial nosi XP čipove u istom panelu)
ali steže odmak od `incorrect` s Δ30 na Δ20. To je i dalje razlučivo, ali tvrdnja se ne smije
napisati bez mjerenja (🔒 DOC).

**Točan opseg dodira — 4 datoteke, NULA komponenti:**
1. `frontend/src/index.css:177,178` (light `--partial`, `--partial-soft`)
2. `frontend/src/index.css:250,251` (dark)
3. `design-system/sql-tutor/MASTER.md:57` (tablica §2.2) + `:150` (hue mapa §2.7) + `:66–69`
   (obrazloženje mitigacije)
4. `docs/errata.md:24` (#13 status)

Komponente **ne diraju** vrijednosti — `FeedbackPanel.tsx:58-59` i `lib/verdict-ui.ts:42-44`
vuku `text-partial` / `bg-partial-soft` / `border-partial/40`, a `StatsSummary.tsx:69`
`text-partial`. Promjena tokena propagira sama.

**Rizik:** partial se prikazuje na eval-verificiranom FeedbackPanelu. Promjena je CSS-only i ne
dira ni jednu granu logike, ali mijenja piksel koji je 4.3c živo verificirao („⚠️ Djelomično" +
`bg-partial-soft` u DOM-u). **Cijena:** oba `--partial` i oba `--partial-soft` moraju biti
ponovno izmjerena vs `card` u obje teme (≥4.5:1 za tekst, ≥3:1 za granicu) i brojka + datum
upisani po 🔒 DOC politici. Bez tog mjerenja **ne dirati**.

**Zašto je #13 uopće ostao siroče:** commit `c12ec31` (4.4b) ih je bio *spojio* —
„Token-level, ide uz rekalibraciju palete zajedno s partial hue 60→45". #33 je potom odbačen
matematičkim dokazom, a #13 je otišao s njim iako s njim nema veze.

### A.2 — #33: NE DIRATI

Errata `#33` nosi mjerenja i dokaz nemogućnosti: u light temi bi `mastery-0` i `mastery-25`
trebali L ≤ 0.665 dok je `mastery-50` već na L = 0.63 → tri donja stopa u rasponu 0.035 L
prestaju biti razlučiva, čime pada uvjet „percepcijski kontinuiran gradijent" (MASTER §2.3).
Zaključak errate: **gradijent je skala salijentnosti, ne nosilac informacije**; stvarna
mitigacija je `role="progressbar"` + `aria-valuenow` + tekstualni postotak uz svaki bar.
4.7 ovdje **ne radi ništa**.

### A.3 🔒 DOC — neistina u kodu, otkrivena u ovom inventaru

`frontend/src/index.css` na tri mjesta tvrdi da je partial neaktivan:

```
14:  /* ── Semantika verdicta (MASTER.md §2.2) — partial REZERVIRAN, ne koristiti u UI (ERRATA #8) ── */
172:  /* Semantika verdicta — partial REZERVIRAN (ERRATA #8) */
245:  /* Semantika verdicta — partial REZERVIRAN (ERRATA #8) */
```

ERRATA #8 je **revidiran** u 4.3c (errata.md:16 — „Partial je AKTIVAN, deriviran iz
`error_type='row_mismatch'`"), a partial se koristi u `FeedbackPanel.tsx:58-59`,
`verdict-ui.ts:42-44` i `StatsSummary.tsx:69`. MASTER.md je ažuriran u istom diffu
(`:63-69`, `:223`), `index.css` **nije**. Ista klasa problema kao netočni `MasteryBar`
docstring iz #33. Komentar-only popravak, nula rizika.

---

## B — POKRIVENOST POLISH LANCA PO EKRANU

Lanac iz plana §4: `ui-ux-pro-max` → `ui-styling` → `emil-design-eng` → `/review-animations`
+ `/code-review`.

Izvor: commit bodies (`36a1a9d`, `43d3632`, `6d33946`, `6992c2a`, `c12ec31`, `f4c42bb`,
`7a00708`, `eae9967`, `aed995c`, `89b974f`, `528e482`) + `docs/faza-4.3-wrapup.md`.

| Ekran | ui-styling | emil polish | `/review-animations` | a11y izmjeren |
|---|---|---|---|---|
| Login (4.1c) | ✓ | ✗ | ✗ | ✗ |
| Register (4.1c) | ✓ | ✗ | ✗ | ✗ |
| Dashboard (4.2a) | ✓ | ✗ | ✗ | ✗ |
| Moduli (4.2b) | ✓ | ✗ | ✗ | ✗ |
| **Task screen (4.3a–c)** | ✓ | ✓ | **✓ (2 Block nalaza, oba popravljena)** | ✓ (4.3c, `a11y-partial.py`) |
| Profil (4.4a) | ✓ | ✗ | ✗ | ✓ (63 tab-stopa izmjereno) |
| BKT krivulje (4.4b) | ✓ | ✗ | ✗ | ✓ (#32: 15 → 0 fokus-rupa) |
| Leaderboard (4.5a) | ✓ | ✗ | ✗ | ✓ (2026-07-19, obje teme) |
| Admin (4.5b) | ✓ | ✗ | ✗ | ✓ (2026-07-19, obje teme) |

**Presuda:** `emil-design-eng` i `/review-animations` prošao je **SAMO Task screen**. To nije
propust — 4.6 (motion polish) je bio rezan, pa motion nikad nije globalno prošao. Potvrda:
`framer-motion` / `motion` **nije u `package.json`** (grep dependencies — nema ga). Sav
postojeći motion je Tailwind `animate-in` / `transition-*` iz `tw-animate-css`.

Login/Register/Dashboard/Moduli **nikad nisu izmjereni na a11y** — a Login/Register su od sada
najvidljivija površina (vidi §F).

### B.1 🔴 NEPOLIRANE ZADNJE IZMJENE (#41, #43 — izvan svih lanaca)

Sve tri su iz 2026-07-25/26, nakon što je 4.6/4.7 bio rezan → **nula polish lanaca**.

| Izmjena | Datoteka | Vizualno usklađen? | A11y provjeren? |
|---|---|---|---|
| Indikator „Riješeno" (#41) | [TaskPage.tsx:287-292](frontend/src/pages/TaskPage.tsx#L287-L292) | **DA** | **DA, implicitno** |
| Dashboard CTA „Riješeno" (#41) | [ContinueCard.tsx:128-133](frontend/src/components/dashboard/ContinueCard.tsx#L128-L133) | **DA** | **DA** |
| FeedbackPanel „Već riješeno · bez XP" (#41) | [FeedbackPanel.tsx:137-142](frontend/src/components/task/FeedbackPanel.tsx#L137-L142) | **DA** | **DA** |
| Klikabilni `ConceptRow` (#43) | [ConceptRow.tsx:112-120](frontend/src/components/modules/ConceptRow.tsx#L112-L120) | **DA** | **DA** |
| Klikabilni `MasteryRow` (#43) | [MasteryHighlights.tsx:76-84](frontend/src/components/dashboard/MasteryHighlights.tsx#L76-L84) | **DA, uz jednu iznimku** | **DA** |

**Zašto „DA" — citati, ne pretpostavke.**

TaskPage indikator i ContinueCard indikator su **byte-identični** stringovi klasa:
```tsx
// TaskPage.tsx:288 i ContinueCard.tsx:129 — isti string
"inline-flex items-center gap-1 rounded-md border border-correct/40 bg-correct-soft px-2 py-0.5 text-xs font-medium text-correct"
```
Oba nose `<CheckCircle2 aria-hidden="true" className="size-3.5" />` + tekst „Riješeno" → boja
**nije** jedini kanal (WCAG 1.4.1 ✓), a `correct`/`correct-soft` su tokeni čiji je kontrast
izmjeren još u 4.1b.

FeedbackPanel čip koristi neutralni `border-border` + `text-muted-foreground` — svjesno
**ne** zeleno, jer nije nagrada, nego objašnjenje odsutnosti XP-a. Ikona + tekst ✓.

`ConceptRow` link nosi eksplicitan SR tekst i fokus prsten:
```tsx
// ConceptRow.tsx:114-117
to={`/task/${concept.entryTaskId}`}
aria-label={`Otvori zadatak za koncept ${concept.name}`}
className="-mx-2 block space-y-1.5 rounded-md px-2 py-3 transition-colors duration-fast
  ease-standard hover:bg-sidebar-accent/40 focus-visible:outline-2
  focus-visible:outline-offset-2 focus-visible:outline-ring motion-reduce:transition-none"
```
Plus vizualna afordancija klika (`ChevronRight`, `:82-86`) i `motion-reduce` guard.
`MasteryHighlights.tsx:79-81` je **isti obrazac** s istim `aria-label`.

**JEDINA NEKONZISTENTNOST (kozmetika):** `ConceptRow` link ima `py-3`, `MasteryRow`
`py-1.5` ([MasteryHighlights.tsx:81](frontend/src/components/dashboard/MasteryHighlights.tsx#L81)).
Dva ista-namjenska „klikni koncept → zadatak" retka s različitim vertikalnim ritmom. Ukupna
visina `MasteryRow`-a (ime + bar + modul) je i dalje >44px pa touch target **nije** prekršen —
ali ne mogu to tvrditi brojkom bez mjerenja u pregledniku (🔒 DOC). Za 4.7: izmjeriti, pa
poravnati.

**Nije provjereno u ovom inventaru:** nijedna od pet izmjena nije prošla `/review-animations`
niti izmjereni kontrast u pregledniku. Tvrdnje gore su **strukturne** (postoji li ikona,
postoji li SR tekst, postoji li fokus prsten), ne fotometrijske.

---

## C — 🔴 EVAL-VERIFICIRANI PUT: ŠTO SE SMIJE DIRATI

Put koji je 4.3 živo verificirao (28 scenarija punog ciklusa, `docs/faza-4.3-wrapup.md`):
dohvati → piši SQL → Run → Submit → feedback → sljedeći.

| Datoteka | Uloga | Smije li polish dirati | Rizik regresije |
|---|---|---|---|
| `pages/TaskPage.tsx` | orkestracija, submitSlot, keyed TaskView | **SAMO layout/spacing** | 🔴 **VISOK** |
| `components/task/FeedbackPanel.tsx` | ocjena, XP, CTA | **SAMO tokeni/spacing** | 🔴 **VISOK** |
| `components/task/SqlEditor.tsx` | Monaco + hotkeys | **NE** | 🔴 **VISOK** |
| `components/task/RunResultPanel.tsx` | rezultat tablica | tokeni + tablični stil | 🟡 SREDNJI |
| `lib/feedback.ts` | `deriveVerdict`, `feedbackText` | **NE** | 🔴 **VISOK** |
| `lib/recommendation.ts` | `recommendationKind`, `reasonText` | **samo tekst** (§F.6) | 🟡 SREDNJI |
| `lib/verdict-ui.ts` | mirror VERDICT_UI za povijest | tokeni | 🟢 NIZAK |
| `hooks/useRun.ts` | 0 invalidacija | **NE** | 🔴 **VISOK** |
| `hooks/useSubmitAttempt.ts` | 5 invalidacija + profile patch | **NE** | 🔴 **VISOK** |
| `hooks/useTask.ts` | `/task/{id}` | **NE** | 🟡 SREDNJI |
| `components/task/SchemaReference.tsx` | statička shema (SHA-256 guard) | tokeni | 🟢 NIZAK |
| `lib/monaco-theme.ts` | editor tema | boje smiju | 🟢 NIZAK |

### C.1 Invarijante koje polish NE SMIJE prekršiti

1. **Keyed `TaskView`** — [TaskPage.tsx:106-112](frontend/src/pages/TaskPage.tsx#L106-L112).
   `key={taskQ.data.id}` resetira per-task stanje (SQL, `lastResult`, `lastAttempt`) jer
   promjena `:taskId` **ne** remounta route element. Ako polish refaktorira ovo u wrapper ili
   ukine key → SQL i feedback prethodnog zadatka procure u sljedeći. To bi zatrovalo eval
   podatke, ne samo izgled.

2. **`deriveVerdict` iz `error_type`, NIKAD iz `xp_delta`** — `lib/feedback.ts`. Wrapup 4.3:
   `xp_delta` je best-effort read (Gamification teče paralelno s RESPOND-om) → degradirani
   put `xp_delta=0` obojio bi partial crvenim „Netočno" uz poruku „Stupci su točni…".

3. **Run ≠ Submit invalidacije** — `useRun` **nula** (ništa se ne persistira, dokazano: 8
   runova → 0 `/profile` poziva), `useSubmitAttempt` **pet** (`profile`, `next-task`,
   `attempts`, `mastery-history`, `task/{id}`) + `setQueryData` patch profila **prije**
   invalidacije. Bez tog patcha level-up derivacija čita zastarjeli level i slavi isti
   level-up na svakom sljedećem tasku.

4. **Mount-time registracija hotkeya** —
   [SqlEditor.tsx:54-76](frontend/src/components/task/SqlEditor.tsx#L54-L76). Monaco akcije se
   registriraju **samo ako handler postoji pri mountu**; bezuvjetna registracija s praznim
   handlerom tiho pojede Shift+Enter (newline) i Ctrl+Enter. Posljedica: `onRun`/`onSubmit`
   moraju stići od **prvog** rendera — komentar na `TaskPage.tsx:328` to izrijekom čuva.
   Polish koji uvede uvjetni render editora (npr. „prikaži editor nakon animacije") **razbija
   hotkeye**.

5. **`columns` array je autoritet** — `RunResultPanel`, ćelija = `row[col]`, nikad
   `Object.keys` (NALAZ #12: dict kolabira duplikate).

6. **Kanonski task ID** — `/^\d+$/` ([TaskPage.tsx:56](frontend/src/pages/TaskPage.tsx#L56));
   `0x2A` / `1e2` / `" 5"` bi kroz `Number()` aliasirali drugi task pod istim query keyem.

7. **`mastery_threshold` iz `/profile`**, nikad hardkodiran 0.85.

8. **NALAZ #7** — breadcrumb modul iz **primarnog koncepta**, nikad `task.module_id`
   ([TaskPage.tsx:209-211](frontend/src/pages/TaskPage.tsx#L209-L211)).

### C.2 🔴 STANI-I-JAVI: eval-verificirani ekran ima nedovršen polish?

**Odgovor: NE, i to je dobra vijest.** Task screen je **jedini** ekran koji je prošao pun
lanac (§B). Ništa na njemu ne *traži* dodir. Jedini kandidat za dodir je hint-rezervacija
(§D) — i ona je čisto layoutna.

---

## D — HINT UI: GDJE ĆE SJESTI (priprema, ne gradnja)

### D.1 Traga NEMA — citat pretrage (🔒 DOC)

```
$ cd frontend/src && grep -rniE "hint" .
components/task/RunResultPanel.tsx:66:  /** Vizualni hint prečaca (platform-aware, iz TaskPage-a). */
components/ui/kbd.tsx:4: * Kbd (Faza 4.3b) — JEDAN chip za prečace (gumbi + hint u rezultat panelu).
lib/api/schema.d.ts:293:            /** Hint Requested */
lib/api/schema.d.ts:294:            hint_requested: boolean;
```

**Četiri pogotka, nula UI-ja.** Prva dva su hrvatska riječ „hint" u smislu *vizualne naznake
prečaca* — nemaju veze s HintAgentom. Druga dva su generirani tip. **Nema** gumba, **nema**
rute, **nema** komponente, **nema** hooka, **nema** tipa u `lib/api/types.ts`.

### D.2 `hint_requested` — postoji u ugovoru, mrtav u praksi

```
$ grep -rn "hint_requested" backend/ --include=*.py --include=*.sql | grep -v test
backend/app/db/models.py:196:    hint_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
backend/app/api/schemas.py:214:    hint_requested: bool
backend/app/api/routes.py:567:                Attempt.hint_requested,
backend/app/api/routes.py:590:                "hint_requested": r.hint_requested,
backend/agents/persistence.py:78:            hint_requested=False,
backend/alembic/versions/ac6a5eeac6e5_initial_schema_16_tables.py:152:    sa.Column('hint_requested', sa.Boolean(), server_default='false', nullable=False),
backend/scripts/export_eval_data.py:87:               a.execution_time_ms, a.rows_returned, a.hint_requested,
```

**Kako se postavlja:** `persistence.py:78` upisuje **hardkodirani `False`** pri svakom
attemptu. Nema puta kojim bi ikad postao `True` — ni ruta, ni FIPA poruka, ni request polje.
Kolona postoji od inicijalne migracije (Faza 1), predviđena za HintAgenta koji još ne
postoji.

**Kako se koristi:** `/attempts` ga vraća u `AttemptItem` (`schema.d.ts:293-294`), a
`export_eval_data.py:87` ga izvozi. Frontend ga **nikad ne čita** — `AttemptItem` se
konzumira u `AttemptRow.tsx` i `attempt-stats.ts`, ni jedan ne referencira `hint_requested`
(grep u §B potvrdio).

🔴 **STANI-I-JAVI:** postavljanje `hint_requested=True` je **backend izmjena** (`persistence.py`
+ vjerojatno novo polje u `AttemptRequest`). To je **Faza 5**, ne 4.7. 4.7 samo rezervira
prostor.

### D.3 Gdje hint gumb logično sjeda

Postojeći split (4.3a): lijevo opis + shema, desno Monaco + akcije.

**Preporuka: u desni akcijski red, lijevo od Run/Submit para** —
[TaskPage.tsx:337-359](frontend/src/pages/TaskPage.tsx#L337-L359):

```tsx
<div className="flex flex-wrap items-center justify-end gap-3">   // ← :337
  <div className="flex items-center gap-2">                        // ← :338 Run+Submit
```

Vanjski `justify-end` s `gap-3` **već je pripremljen** za drugi child lijevo od Run/Submit
grupe (zato je grupa u vlastitom `div`, a ne direktna djeca). Hint gumb ide kao prvi child
vanjskog flexa → sjeda uz lijevi rub akcijskog reda, vizualno odvojen od primarnih akcija.

**Zašto ne lijevi panel:** hint je odgovor na *ono što si napisao*, ne dio zadatka. Uz opis bi
čitao kao dio teksta zadatka.
**Zašto ne novi red:** dodatni red mijenja visinu kartice → editor bi se pomaknuo, a
`h-[420px]/xl:h-[520px]` je fiksan i eval-verificiran.

**Varijanta gumba:** `variant="ghost"` ili `"outline"` — **nikad `default`**. Primarna akcija
ekrana je Submit; hint je izlaz u nuždi. Tekstualno „Zatraži hint" + `Lightbulb` ikona
(`lucide-react`, već dependency).

**Gdje sadržaj hinta ide:** u `submitSlot` lanac
([TaskPage.tsx:361-389](frontend/src/pages/TaskPage.tsx#L361-L389)), **iznad** `FeedbackPanel`,
ali kao **zaseban slot** — hint i feedback moraju moći koegzistirati (zatražiš hint, pa
predaš). Postojeći `submitSlot` je ekskluzivan enum (točno jedan render); hint traži vlastiti
state, ne granu tog enuma.

**Boja:** ni `correct`/`incorrect`/`partial` (nije verdikt) ni `accent-warm` (rezerviran za
gamifikaciju, MASTER §2.1). → neutralni `border-border` + `bg-muted`, kao „unknown" verdikt
u `VERDICT_UI`.

### D.4 Stanja koja hint treba

| Stanje | Zašto | Obrazac koji već postoji |
|---|---|---|
| `idle` | gumb dostupan | — |
| `loading` | LLM misli (sekunde, ne ms) | `LoadingState lines={2}` — kao `submitSlot === "pending"` |
| `success` | prikaz hinta | novi slot, neutralni tokeni |
| `error` | LLM/mreža pao | `ErrorState` s `onRetry` |
| `unavailable` | HintAgent isključen / nema ključa | ⚠️ **nema obrasca** — treba tiho sakriti gumb, ne prikazati slomljeni |
| `rate-limited` / iskorišten | ako Faza 5 uvede limit | ⚠️ **nema obrasca** — disabled + razlog |

Zadnja dva su odluka Faze 5. 4.7 ne treba znati odgovor, ali **layout mora izdržati** i
prisutnost i odsutnost gumba bez pomicanja editora — `flex-wrap` na `:337` to već daje.

**4.7 zadaća: rezervirati red, ne graditi gumb.** Konkretno: potvrditi da akcijski red diše i
s trećim elementom, i da to ne mijenja visinu kartice.

---

## E — GLOBALNI POLISH DUG (cross-screen)

### E.1 Motion

**`framer-motion` / `motion` NIJE instaliran** — provjereno u `frontend/package.json`
(dependencies ne sadrže ni jedan). Sav motion je Tailwind (`tw-animate-css` v1.4.0):
`animate-in`, `fade-in`, `zoom-in-*`, `slide-in-from-*`, `transition-*` + motion tokeni iz
4.1b (`--ease-standard/entrance/exit/reward`, `--duration-*`).

Raspodjela (broj `animate-`/`transition-`/`motion-reduce` pojava po datoteci):

| Ekran / komponenta | Motion | Ocjena |
|---|---|---|
| FeedbackPanel | 5 | bogato (pop-in, XP/badge reward, level-up) |
| AttemptRow | 3 | ok |
| BadgeGallery, ModuleCard, ConceptRow, AppShell | 2 | ok |
| TaskPage, RunResultPanel, SchemaReference, MasteryHighlights, MasteryBar, ConceptCurveCard, AgentFlowCard, AttemptHistory, LeaderboardPage | 1 | minimalno |
| **Login / Register** | 1 (samo `animate-spin` na Loader2) | **gol** |
| **Dashboard** (page) | 0 | **gol** |
| **Moduli** (page) | 0 (djeca imaju) | **gol na razini stranice** |
| **Profil** (page) | 0 (djeca imaju) | **gol na razini stranice** |
| **Admin** (page) | 0 | **gol** |
| **TaskEntryPage** | 0 | **gol** |

**`motion-reduce` dosljednost: DA — globalno je pokriveno.**
[index.css:303-312](frontend/src/index.css#L303-L312):

```css
@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Univerzalni guard hvata **sve**, uključujući komponente bez per-element `motion-reduce:`
klase. Per-komponentni guardovi (11 datoteka) su dodatni sloj, ne nužnost. Uz to
`ModulesPage.tsx:79` čita `matchMedia("(prefers-reduced-motion: reduce)")` u JS-u za
`scrollIntoView` behavior — ispravno, jer CSS guard ne mijenja JS argument.

**Presuda: reduced-motion nije dug.** Dug je *odsutnost* motiona na 6 ekrana, a to je
najmanje važna stavka u cijelom inventaru (vidi staging §9, stavka 6).

### E.2 Loading — skeleton, ne spinner ✅

Svih 9 ekrana koristi `LoadingState`/`Skeleton`. Jedine `animate-spin` pojave:

```
components/ui/sonner.tsx:28   → Loader2Icon (toast loading — legitimno, toast ne nosi skeleton)
pages/RegisterPage.tsx:140    → in-button spinner na submitu
pages/LoginPage.tsx:114       → in-button spinner na submitu
```

Sve tri su **ispravne iznimke**: skeleton u gumbu ili toastu nema smisla. `RegisterPage`/
`LoginPage` uz to mijenjaju labelu („Registracija…" / „Prijava…") pa spinner nije jedini
signal. **Nema duga.**

### E.3 Empty — dizajnirani `EmptyState` ✅ (uz jednu svjesnu iznimku)

`EmptyState` (`components/state/EmptyState.tsx`) je primitiv s ikonom, naslovom, opisom i
opcionalnim CTA. Potrošači:

| Mjesto | Prazno stanje | CTA |
|---|---|---|
| `ModulesPage:134` | „Nema modula" (baza neseedana) | ✗ (upućuje adminu) |
| `LeaderboardPage:129` | dva teksta (weekly vs global) | ✗ (ispravno — nema što kliknuti) |
| `AttemptHistory:67` | „Još nema pokušaja" | ✓ „Riješi prvi zadatak" |
| `MasteryCurves:98` | „Krivulje se pojavljuju nakon…" | ✓ „Riješi zadatak" |
| `AdminPage:182,193` | dva različita (nema prometa vs filtar bez pogodaka) | ✓ „Poništi" |

**Svjesna iznimka:** `StatsSummary.tsx:38` vraća `null` na `total === 0` — komentar: „Greška
ili prazan skup → ništa (povijest ispod nosi error/CTA, bez duplog šuma)". To je namjera, ne
propust. **Nema goljih praznih prikaza.**

### E.4 Konzistentnost

| Element | Stanje |
|---|---|
| Paginacija | ✅ **jedan** `components/ui/pagination.tsx`, tri potrošača (`AttemptHistory:101`, `LeaderboardPage:165`, `AdminPage:207`) |
| Tablice | 🟡 dvije izvedbe: `LeaderboardTable` (`<table>`+`<caption>`+`scope="col"`) vs `RunResultPanel` (`<table>` s `border-separate` za sticky header). **Različite namjene → obranjivo** |
| Kartice | ✅ jedan `ui/card.tsx` |
| Prazna/error stanja | ✅ tri primitiva (`EmptyState`/`ErrorState`/`LoadingState`) |
| **Formatiranje datuma** | 🔴 **DUG — tri neovisna formattera** |
| Verdict vizual | 🟡 svjesni mirror + jedna divergencija |

**🔴 `lib/datetime.ts` NE POSTOJI.** Tri `Intl.DateTimeFormat("hr-HR")` instance:

```
components/admin/AgentFlowCard.tsx:26   const TIME_FMT = new Intl.DateTimeFormat("hr-HR", {…})
components/profile/AttemptRow.tsx:20    const DT_FMT   = new Intl.DateTimeFormat("hr-HR", {…})
lib/mastery-history.ts:227              const POINT_DT_FMT = new Intl.DateTimeFormat("hr-HR", {…})
```

Sve tri su ispravno na razini modula (konstrukcija je skupa) i sve tri su `hr-HR`, ali su tri
neovisne definicije opcija. Isti timestamp može biti drukčije formatiran u povijesti pokušaja
i u tooltipu krivulje. **Konsolidacija u `lib/datetime.ts` je zabilježeni kandidat 4.7** —
opseg: 1 nova datoteka + 3 poziva, nula vizualne promjene ako se opcije zadrže.

**Verdict divergencija:** `lib/verdict-ui.ts:54` label za `unknown` je **„Bez ocjene"**, a
`FeedbackPanel.tsx:68` **„Ocjenjivanje nije uspjelo"**. Isto stanje, dva teksta na dva ekrana.
Mirror je svjestan i dokumentiran (`verdict-ui.ts:4-9`: „DEKLARATIVNI MIRROR … Task screen se
u 4.4a NE dira"), ali ovaj tekst je slučajno razišao. Copy-only popravak.

### E.5 🔴 RESPONSIVE — presuda po ekranu

Breakpoint prefiksi po datoteci (`grep -o` count):

```
pages/AdminPage.tsx        sm=0 md=0 lg=0 xl=0
pages/DashboardPage.tsx    sm=1 md=0 lg=0 xl=0
pages/LeaderboardPage.tsx  sm=0 md=0 lg=0 xl=0
pages/LoginPage.tsx        sm=0 md=0 lg=0 xl=0
pages/ModulesPage.tsx      sm=0 md=0 lg=1 xl=0
pages/ProfilePage.tsx      sm=0 md=0 lg=0 xl=0
pages/RegisterPage.tsx     sm=0 md=0 lg=0 xl=0
pages/TaskEntryPage.tsx    sm=0 md=0 lg=0 xl=0
pages/TaskPage.tsx         sm=0 md=0 lg=0 xl=4
components/layout/AppShell.tsx  sm=0 md=5 lg=0 xl=0
```

#### 🔴 NALAZ 4.7-A: ISPOD 768px NEMA NAVIGACIJE

[AppShell.tsx:88](frontend/src/components/layout/AppShell.tsx#L88):
```tsx
<aside className="hidden w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
```

Sidebar je `hidden` do `md` (768px). Header (`:105-149`) sadrži **samo**: mobilni brand,
theme toggle, user chip, „Odjava". **Nema zamjene za nav.** Potvrda pretragom:

```
$ grep -rniE "hamburger|sheet|drawer|mobile.?nav|Menu[^s]" --include=*.tsx --include=*.ts .
pages/AdminPage.tsx:10: * traži i filter po vremenu; on NE POSTOJI …
pages/TaskPage.tsx:130: … editora, koji je u međuvremenu mogao biti obrisan …
pages/TaskPage.tsx:184: // Retry ponavlja zadnju POSLANU predaju (editor mogao biti obrisan …
hooks/useAgentLogs.ts:9: … spominje i filter po vremenu; on NE POSTOJI …
```

Sva četiri pogotka su hrvatska riječ „međuvremenu" i komentari o filterima. **Nula** mobilne
navigacije.

**Posljedica na javnom linku:** student koji otvori app na telefonu vidi Dashboard i **ne
može doći** do Modula, Profila ni Ljestvice osim kroz in-page linkove (ContinueCard →
`/task/:id`, MasteryHighlights → `/task/:id`). Iz `/task/:id` **nema puta natrag** osim
browser Back — breadcrumb vodi na `/modules`, što je jedini izlaz, i to slučajan.

Komentar na `:87` kaže „desktop primaran (plan §4.7); na užem ekranu skrivena, header ostaje" —
dakle **znalo se** i odgođeno je za 4.7. 4.7 sada ide.

#### Presuda po ekranu

| Ekran | < 768px | < 420px | Presuda |
|---|---|---|---|
| Login | ✅ `max-w-sm` centriran, `p-4` | ✅ | dobro |
| Register | ✅ isto | ✅ | dobro |
| Dashboard | 🟡 sadržaj ok (`max-w-5xl` + `sm:grid-cols-3` onboarding kolabira), **ali nema nav** | 🟡 isto | **treba nav** |
| Moduli | 🟡 `lg:grid-cols-2` → 1 kolona ✅, **nema nav** | 🟡 dugi „Traži: …" nizovi | **treba nav** |
| **Task** | 🔴 `xl:` (1280px!) → **sve ispod 1280 je jedna kolona**; Monaco `h-[420px]` | 🔴 Monaco na 390px | **odluka, vidi niže** |
| Profil | 🟡 mreža krivulja `sm:grid-cols-2 lg:grid-cols-3` → 1 ✅, **nema nav** | 🟡 `text-3xl` brojke u `sm:grid-cols-3` statistici | **treba nav** |
| BKT detalj | 🟡 graf ima `accessibilityLayer` — nije mjeren pod 420px | ❓ nije provjereno | izmjeriti |
| Leaderboard | ✅ `LeaderboardTable.tsx:34` ima `overflow-x-auto` (4.5a: „Reflow @720px bez horizontalnog scrolla") | 🟡 nije mjereno pod 420 | dobro-ish |
| Admin | 🟡 0 breakpointa, ali `AgentFlowCard:107` mono blok ima vlastiti `overflow-x` | 🟡 filtri u `flex-wrap` | **admin ≠ student — niski prioritet** |

#### 🔴 Odluka koju tražim: Task screen na mobitelu

**Predlažem: „desktop/tablet-preferirano + iskrena poruka pod 768px", NE puni mobilni Monaco.**

Obrazloženje:
1. **Monaco na dodir je stvarno loš** — nema mobilnu virtualnu tipkovnicu za SQL, `Ctrl+Enter`
   i `Shift+Enter` na telefonu **ne postoje**, a to su jedina dva prečaca ekrana
   (`TaskPage.tsx:344,353` `aria-keyshortcuts`). Student bi imao Run/Submit gumbe, ali bez
   ikakve prednosti editora.
2. **Rizik je jednosmjeran.** Pretvaranje Task screena u pravi mobilni ekran znači dirati
   `xl:` grid, visinu editora i akcijski red — dakle **eval-verificirani layout**, i to
   najviše-rizičnu datoteku u projektu (§C). Poruka „otvori na računalu" ne dira ništa.
3. **Studenti pišu SQL, ne skrolaju feed.** Realno će sjesti za računalo. Rizik nije da će
   pokušati na telefonu, nego da će vidjeti **slomljen** ekran i pomisliti da app ne radi.

Konkretno: pod `md` prikazati dizajniranu poruku („SQL editor traži širi ekran — otvori na
računalu ili tabletu") **umjesto** editora, uz zadržan opis zadatka, koncepte i shemu (to je
čitljivo na mobitelu i korisno). Opis + shema ostaju, editor se zamijeni. Tako mobitel nije
mrtav — služi za *čitanje* zadatka.

**Ne implementiram — tražim odluku.** Alternativa (puni mobilni editor) je legitimna ako
smatraš da eval mora podnijeti mobilne sudionike, ali tada Task screen **mora** natrag kroz
`/review-animations` + živu verifikaciju punog ciklusa, jer diramo jezgru.

---

## F — 🔴 PUT PRVOG DOLASKA BEZ NADZORA

Napravljen u 4.1c (`eae9967`), od tada **nije diran**. Od sada je najvidljivija površina.

### F.1 `/register` i `/login` — komponente, shema, poruke

**Komponente:** `pages/RegisterPage.tsx` (159 linija), `pages/LoginPage.tsx` (133), guard
`routes/guards.tsx:87-97` (`PublicOnlyRoute`), rute `routes/router.tsx:41-47`. Oba su
**eager** importa (nisu lazy) — ispravno, to je prvi ekran.

**Zod shema — register** ([RegisterPage.tsx:26-33](frontend/src/pages/RegisterPage.tsx#L26-L33)):
```tsx
const registerSchema = z.object({
  username: z
    .string()
    .min(3, "Korisničko ime mora imati bar 3 znaka")
    .max(50, "Korisničko ime može imati najviše 50 znakova"),
  email: z.email("Unesi ispravnu email adresu"),
  password: z.string().min(8, "Lozinka mora imati bar 8 znakova"),
})
```

**Zod shema — login** ([LoginPage.tsx:24-27](frontend/src/pages/LoginPage.tsx#L24-L27)):
```tsx
const loginSchema = z.object({
  username: z.string().min(1, "Unesi korisničko ime"),
  password: z.string().min(1, "Unesi lozinku"),
})
```

**Poruke grešaka — register** (`:53-64`): 409 → „Korisničko ime ili email već postoji.";
422 → „Neispravni podaci — provjeri unesena polja."; ostalo → „Registracija nije uspjela —
pokušaj ponovno." Prikaz dvostruk: `setError("root")` u `role="alert"` bloku (`:129-136`) +
`toast.error`.

**Poruke grešaka — login** (`:47-54`): 401 → „Neispravno korisničko ime ili lozinka."; ostalo
→ „Prijava nije uspjela — pokušaj ponovno."

**Helper tekst uz `username`: NE POSTOJI.** Citat — `RegisterPage.tsx:82-95` je cijeli blok
polja:
```tsx
<div className="space-y-2">
  <Label htmlFor="username">Korisničko ime</Label>
  <Input id="username" autoComplete="username" aria-invalid={!!errors.username}
    {...register("username")} />
  {errors.username && (
    <p className="text-sm text-incorrect" role="alert">{errors.username.message}</p>
  )}
</div>
```
Label, input, uslovna greška. **Nema** `<p>` s uputom, nema `aria-describedby`, nema
placeholdera. Student ne zna smije li dijakritiku, razmak, hoće li ime biti javno.

🔴 **To zadnje je stvarni problem, ne kozmetika:** `username` se **prikazuje na javnoj
Ljestvici** (`f4c42bb`: „username, NIKAD email"; isticanje trenutnog usera ide preko
usernamea). Student koji upiše svoje pravo ime i prezime izlaže ga svim ostalim sudionicima, a
nigdje mu to nije rečeno. To je frontend-rješivo jednom rečenicom uz polje.

### F.2 Koja polja traži `/register` — `email` JE obavezan

`frontend/src/lib/api/schema.d.ts` (generirano iz `openapi.json`, provjereno u sinkronu —
vidi §F.7):

```
RegisterRequest: {
    /** Username */
    username: string;
    /** Email */
    email: string;      ← BEZ `?` → OBAVEZAN
    /** Password */
    password: string;
};
```

Tri obavezna polja. `email` **nije** nullable ni optional. Zod shema ga ispravno zrcali
(`z.email(…)`, bez `.optional()`).

Napomena uz #38: `email` se renderira **samo** u `RegisterPage` — potvrđeno i u ovom
inventaru (`grep -rn "email"` u `src` daje pogotke samo u `RegisterPage.tsx:98-111` i
`lib/sandbox-schema.ts` kao naziv stupca sintetičke sheme). `ProfilePage`, `AppShell`,
`LeaderboardTable` ga ne prikazuju.

🔴 **Ali je i dalje prikupljen podatak.** Student na javnom URL-u daje email bez ijedne
rečenice o tome zašto, koliko dugo se čuva ni tko ga vidi. `docs/errata.md:50` (#37) već
bilježi da dumpovi „nose e-mailove i bcrypt hasheve". To je 🔴 stvar §F.4, ne kozmetika.

### F.3 Prvi dolazak: stanja s NULA attempta, ekran po ekran

| Ekran | Stanje | Ocjena |
|---|---|---|
| **Dashboard** | Dizajniran onboarding. `isFresh = xp===0 && mastery.length===0 && badges.length===0` ([DashboardPage.tsx:101-104](frontend/src/pages/DashboardPage.tsx#L101-L104)). Naslov „Dobrodošao, {username}", podnaslov „Tvoj put kroz SQL kreće ovdje", `ContinueCard onboarding` → „Počni ovdje" / „Riješi prvi zadatak", `OnboardingIntro` trio (Riješi / Prati napredak / Skupljaj nagrade). `ProgressHero`, `MasteryHighlights`, `BadgeStrip` **sakriveni** (`!isFresh`) | ✅ **dizajniran** |
| **ContinueCard** | Uz `onboarding` mijenja tekst razloga: „Odabrano prema tvojoj trenutnoj razini znanja." **umjesto** `reasonText(rec.reason)` — jer bi „nastavi gdje si stao" (`partial_continuation` iz tier priora) lagalo ([:135-140](frontend/src/components/dashboard/ContinueCard.tsx#L135-L140)) | ✅ **promišljeno** |
| **Moduli** | `isFresh = profile.data.mastery.length === 0` → kartica „Sve je pred tobom — kreni od koncepta {rootConcept.name}, jedinog bez preduvjeta" + CTA. Root iz **podataka** (`prerequisites.length === 0`), ne hardkodiran ([ModulesPage.tsx:124-170](frontend/src/pages/ModulesPage.tsx#L124-L170)) | ✅ **dizajniran** |
| **Profil → StatsSummary** | `total === 0` → `return null` (`:38`) | ✅ svjesno (povijest ispod nosi CTA) |
| **Profil → BadgeGallery** | katalog × earned=[] → svi zatamnjeni s kriterijem | ✅ |
| **Profil → AttemptHistory** | `total === 0` → `EmptyState` „Još nema pokušaja" + CTA „Riješi prvi zadatak" (`:60-79`) | ✅ **dizajniran** |
| **Profil → MasteryCurves** | `totalPoints === 0` → `EmptyState` „Krivulje se pojavljuju nakon prvih riješenih zadataka" + CTA. Uz to **svjesno preskače** listu „Još nema podataka" jer bi 26 čipova pretvorilo dizajnirano prazno u zid (`:133-137`) | ✅ **promišljeno** |
| **Leaderboard** | `total === 0` → `EmptyState`. Ako user nije na stranici → diskretna napomena, rang se ne izmišlja | ✅ |
| **Task screen** | prvi zadatak stiže preko `/next-task`; sve statično iz `/task/{id}` | ✅ |

**Nijedan crash, nijedan gol prazan prikaz.** Put prvog dolaska je funkcionalno **najbolje
pokriveni** dio inventara. Dug nije u praznim stanjima — dug je u **uputi i oporavku**.

### F.4 Mjesto za uputu ili suglasnost: NE POSTOJI

```
$ cd frontend/src && grep -rniE "suglasnost|pristanak|sudionik|istraživanj|privatnost|GDPR|diplomsk|upute|uvjeti|consent" .
components/modules/ConceptRow.tsx:66:  // (entryTaskId) I nije zaključan — zaključani (nezadovoljeni preduvjeti) i oni
lib/recommendation.ts:25:  unlock_new: "Preduvjeti su ispunjeni — vrijeme je za novi koncept.",
lib/mastery-history.ts:33: * bila vizualna laž u diplomskom radu.
```

**Tri pogotka, nula suglasnosti.** Prva dva su riječ „**preduvjeti**" (podniz „uvjeti"), treći
je komentar u kodu o diplomskom radu. **Nema** teksta prije registracije, **nema** checkboxa,
**nema** info bloka, **nema** rute `/o-istrazivanju` ili sličnog.

Uz to `index.html` ne pomaže:
```html
<html lang="en">          ← app je 100 % hrvatski
<title>frontend</title>   ← naslov tab-a na javnom URL-u
```

🔴 **Dva nalaza iz jedne datoteke:**
- **NALAZ 4.7-B:** `lang="en"` uz hrvatski sadržaj = **WCAG 2.1 AA 3.1.1 (Language of Page)
  prekršaj**. Čitač ekrana izgovara hrvatski tekst engleskom fonetikom. Jednoznakovni
  popravak (`lang="hr"`), nula rizika.
- **NALAZ 4.7-C:** `<title>frontend</title>` — tab, bookmark i shareani link zovu se
  „frontend". Uz WCAG 2.4.2 (Page Titled) je formalno zadovoljen (naslov postoji), ali je
  neinformativan. Copy-only.

**NALAZ 4.7-D:** [AppShell.tsx:100](frontend/src/components/layout/AppShell.tsx#L100) u
sidebar footeru prikazuje **„Faza 4.1c — app shell"** — interna razvojna oznaka, vidljiva
svakom studentu na svakom ekranu. Copy-only, nula rizika.

**Gdje bi uputa/suglasnost sjela.** Preporuka: **iznad forme na `/register`**, unutar
postojeće `Card` (`RegisterPage.tsx:69-75` `CardHeader`), kao proširen `CardDescription` ili
zaseban blok između headera i forme. Razlog: to je jedina točka kroz koju svaki sudionik
mora proći, prije ijednog prikupljenog podatka. `CardDescription` trenutno kaže samo „Novi
račun — uloga je uvijek student."

Što tekst mora pokriti (**odluka je tvoja/mentorova, ne moja** — ja utvrđujem mjesto):
čemu služi sustav, da je dio diplomskog rada, što se bilježi (upiti, ishodi, XP, procjena
znanja), da je `username` **javan na Ljestvici**, i kome se javiti kad pukne. Zadnje je
trenutno nemoguće — `ErrorState` default kaže „javi se administratoru" bez ijednog kontakta.

🔴 **STANI-I-JAVI (formalno):** je li za asinkronu javnu evaluaciju sa stvarnim sudionicima
potrebna **etička/GDPR suglasnost po pravilima FOI-ja**, i u kojem obliku (info blok vs
obavezan checkbox)? Ako je potreban **checkbox koji se bilježi**, to je backend izmjena (novo
polje) → **Faza 5/deployment, ne 4.7**. Ako je dovoljan **info tekst bez zapisa**, 4.7 to
rješava u cijelosti, frontend-only.

### F.5 Oporavak bez pomoći: ima li svaki error state akciju?

| Mjesto | Poruka | Akcija |
|---|---|---|
| `ErrorState` (primitiv) | default „Nešto je pošlo po zlu" | ✅ „Pokušaj ponovno" **ako je `onRetry` predan** (`:39-44`) |
| `ErrorBoundary` (render crash) | „Greška u prikazu" | ✅ reset (`handleReset`) |
| Dashboard | „Dashboard nije dostupan" | ✅ refetch profile+modules |
| Moduli | „Moduli nisu dostupni" | ✅ refetch |
| Profil | „Profil nije dostupan" | ✅ refetch |
| MasteryCurves | „Krivulje napretka nisu dostupne" | ✅ refetch |
| ContinueCard | „Preporuka nije dostupna" | ✅ refetch |
| TaskEntryPage | „Preporuka nije dostupna" | ✅ refetch |
| Task — nevalidan ID | „Zadatak ne postoji" | ❌ **NEMA AKCIJE** |
| Task — fetch fail | „Zadatak nije učitan" | ✅ refetch |
| Task — **504 gateway** | „Sustav ne odgovara / Evaluacija je predugo trajala" | ✅ `retrySubmit` |
| Task — infra fail | „Predaja nije uspjela" | ✅ `retrySubmit` |
| Run — infra | (RunResultPanel) | ✅ `retryRun`, čuva stari rezultat |
| Leaderboard | „Ljestvica nije dostupna" | ✅ refetch |
| Admin — **403** | „Nemaš ovlasti…" | ❌ **NEMA AKCIJE** (`AdminPage.tsx:141-146`) |
| `AdminRoute` 403 ekran | „Nemaš pristup ovom dijelu" | ✅ „Natrag na dashboard" |
| 401 (bilo gdje) | — | ✅ auto → `/login` (`guards.tsx:21-23`) |
| Login/Register fail | mapirano po statusu | ✅ forma ostaje ispunjena, može ponovno |

**Presuda: oporavak je gotovo posvuda pokriven.** Dva `ErrorState`-a bez akcije:

1. **`TaskPage.tsx:70-75`** — „Zadatak ne postoji" (`{taskId}` nije valjan ID). Slijepa ulica.
   Student koji je pokvario URL ili došao s mrtvog linka ostaje bez izlaza osim Backa.
   **Popravak: `onRetry` nema smisla, treba link na `/` ili `/modules`.** Frontend-only.
2. **`AdminPage.tsx:141-146`** — 403 bez akcije. **Admin ekran, nije studentski put** →
   niski prioritet.

**Ali:** ovo je otpornost na *pojedinačni* pad. Ono što **NE** postoji je poruka za slučaj da
agentski lanac padne **trajno**. Sve poruke kažu varijantu „pokušaj ponovno" — nijedna ne
kaže što ako i drugi pokušaj padne, i nijedna ne nosi kontakt. Pod nadzorom si to rješavao
uživo; asinkrono, student odustane. `ErrorState` default (`:20`) kaže „javi se
administratoru" — **bez ijednog načina da to učini**. To je copy + jedan kontakt, nula
backenda.

### F.6 🔴 NALAZ #44 — postoji li obrazloženje ZAŠTO taj zadatak?

**Postoji, i bolje je nego što je handover sugerirao — ali ne odgovara na pitanje koje #44
otvara.**

`lib/recommendation.ts:20-30` mapira strojni `reason` u hrvatski tekst:
```tsx
const REASON_TEXT: Record<string, string> = {
  weak_with_prereqs_met:
    "Ovaj koncept ti je trenutno najslabiji, a preduvjete već imaš — vrijeme je da ga ojačaš.",
  partial_continuation:
    "Nastavi gdje si stao — ovaj koncept je djelomično savladan.",
  unlock_new: "Preduvjeti su ispunjeni — vrijeme je za novi koncept.",
  fallback: "Sljedeći logičan korak na tvom putu učenja.",
  exhausted: "Riješio si sve dostupne zadatke za preporučeni koncept — …",
  no_recommendation: "Trenutno nema koncepta za preporuku — sve je savladano.",
}
```

Prikazuje se na **tri** mjesta:
- `FeedbackPanel.tsx:198-200` — ispod feedbacka, uz „Sljedeći zadatak" CTA
- `ContinueCard.tsx:139` — Dashboard „Nastavi ovdje" (uz onboarding iznimku, §F.3)
- `TaskEntryPage.tsx:87` — done-stanje

**Zašto to ipak ne rješava #44.** Scenarij iz errate: student riješi `insert`, klikne
„Sljedeći zadatak", dobije `inner_join`. Vidi:

> „Ovaj koncept ti je trenutno najslabiji, a preduvjete već imaš — vrijeme je da ga ojačaš."

Tekst je **istinit** (`inner_join` prior 0.15 = weak) i objašnjava **odabir koncepta**. Ali
student ne pita „zašto ovaj koncept", nego **„zašto sam prestao raditi INSERT"**. Nijedna od
šest poruka ne priznaje **prijelaz** — ni jedna ne kaže da je normalno skakati među temama,
niti da se na `insert` vraća kasnije. Bez toga skok čita kao bug, a app kao nepovezana.

Uz to: `reasonText` je vezan uz **jedan** reason po pozivu. „Zašto ne prethodni koncept" je
informacija o **odnosu** dvaju koncepata, a `/next-task` je ne nosi → jedina iskrena
formulacija je **generalna rečenica o strategiji**, ne per-zadatak izračun.

**Gdje bi ta jedna rečenica sjela — dva mjesta, oba postoje:**

1. **`FeedbackPanel.tsx:197-200`** (primarno — ovdje se skok *doživljava*):
   ```tsx
   <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-border/60 pt-3">
     <p className="text-xs text-muted-foreground">
       {reasonText(rec.reason)}
     </p>
   ```
   `<p>` je već tu, već `text-xs text-muted-foreground`, već u vlastitom flex childu.
   Rečenica ide **kao drugi `<p>`** ispod, ili kao proširenje istog. Nula strukturne promjene.

2. **`ContinueCard.tsx:134-141`** (sekundarno — isti `<p>` obrazac).

**Najmanje rizičan oblik:** statična rečenica u `lib/recommendation.ts` kao konstanta
(npr. `STRATEGY_NOTE`), renderirana **uz** `reasonText`. Mora reći da sustav ide za najslabijim
konceptom u tom trenutku, pa se teme smjenjuju, i da se nedovršeno vraća. **Ne piše se ovdje**
— tekst je copy odluka; utvrđeno je mjesto i oblik.

🟢 **Nula backenda.** `reason` već putuje kroz `/next-task` i `AttemptResponse.recommendation`.

### F.7 Divergencija `schema.d.ts` — NE POSTOJI ✅

Jedan od STANI-uvjeta. Provjereno regeneracijom, ne pretpostavkom:

```
$ npx openapi-typescript ./openapi.json -o <scratchpad>/schema-regen.d.ts
✨ openapi-typescript 7.13.0
🚀 ./openapi.json → …/schema-regen.d.ts [182.6ms]
$ diff <scratchpad>/schema-regen.d.ts src/lib/api/schema.d.ts
$ echo $?
0        ← prazan diff
```

Sva tri polja koja su #41/#43 dodali su prisutna i **konzumirana**:

| Polje | `schema.d.ts` | Frontend potrošač |
|---|---|---|
| `AttemptResponse.already_solved` | `:328` | `FeedbackPanel.tsx:137` |
| `ConceptNode.entry_task_id` | `:392` (`?: number \| null`) | `progress.ts:154,170,189`, `mastery.ts:55` → `ConceptRow.tsx:68,114`, `MasteryHighlights.tsx:40,78` |
| `TaskDetailResponse.solved` | `:625` | `TaskPage.tsx:287`, `ContinueCard.tsx:128` |

Nema mrtvih polja iz #41/#43, nema polja koje frontend čita a ugovor ne daje.
(Caveat: ovo dokazuje sinkron `schema.d.ts` ↔ `openapi.json`. Da je `openapi.json` sinkron s
**živim** backendom dokazuju commit bodies 4.5a/4.5b („schema.d.ts byte-identičan", „diff
prema main za backend/ + schema.d.ts + openapi.json je PRAZAN"), ne ovaj inventar.)

---

## G — TESTNI I PERFORMANCE DUG

### G.1 🔴 NALAZ #17 — nula testova, nula test dependencyja

```
$ find . -path ./node_modules -prune -o -type f \( -name "*.test.*" -o -name "*.spec.*" \
    -o -name "playwright.config.*" -o -name "vitest.config.*" \) -print
→ (prazno)

$ grep -c "vitest\|playwright\|@testing-library" package.json
0
```

`frontend/package.json` `scripts`: `dev`, `build`, `gen:api`, `lint` (oxlint), `format`,
`format:check`, `preview`. **Nema `test`.** `devDependencies`: `@types/node`, `@types/react`,
`@types/react-dom`, `@vitejs/plugin-react`, `openapi-typescript`, `oxlint`, `prettier`,
`typescript`, `vite`. **Ni jedan test runner.**

Errata #17 to zove „**ulazni gate za eval (4.7)**". Brojke „21/27/28 scenarija" iz 4.3 su
**ručne** CDP verifikacije, ne runner.

**Opseg minimalnog student-flow smokea.** Predlažem **Playwright, ne vitest** — traženi flow
je e2e nad živim backendom, ne unit. Vitest bi tražio mockanje cijelog agentskog lanca, što
testira mock, ne sustav.

- **Dependencies:** `@playwright/test` + `npx playwright install chromium` (~1 dev-dep,
  browser binarni download izvan gita). 🔴 **Po CLAUDE.md tražim odobrenje prije dodavanja u
  `package.json`.**
- **Suite:** 1 spec, ~7 koraka: register (uniqueni `smoke_` username) → login → `/task`
  entry redirect → Run (nešto što prolazi) → Submit (točno) → feedback vidljiv → „Sljedeći
  zadatak" navigira.
- **Ključni problem koji suite mora riješiti — čišćenje.** Smoke stvara **stvarnog usera i
  stvarne attempte u `tutor_main`**. Errata #40 već bilježi da `pytest` ostavlja 87 redaka u
  `agent_messages_log` koje **nijedan cleanup ne pokriva** (tablica nema `user_id`), a #37/
  runbook zabranjuju `pytest` tijekom sesije. Playwright smoke je **ista klasa problema**.
  Zato: sentinel prefiks `smoke_` (već priznat u `prepare_eval_baseline.py`), zabilježen
  `correlation_id`, i **zabrana pokretanja tijekom eval sesije** u runbooku.
- **Procjena:** mala po kodu, **srednja po proceduri** — vrijednost je u tome da bude
  pokretljiv *prije* evala, ne *tijekom*.

### G.2 Route-level lazy loading

`routes/router.tsx` — **eager:** `AppShell`, `DashboardPage`, `LoginPage`, `ModulesPage`,
`RegisterPage`, `TaskEntryPage`. **Lazy** (`React.lazy` + `Suspense` s `LoadingState`):

| Ruta | Komentar u kodu |
|---|---|
| `TaskPage` (`:18-20`) | „vuče monaco-editor (velik chunk) — code-split po ruti" |
| `ProfilePage` (`:24-26`) | „priprema za 4.4b chunk (BKT krivulje / chart lib)" |
| `LeaderboardPage` (`:29-33`) | „sekundarni ekran" |
| `AdminPage` (`:36-38`) | „vidi SAMO admin — nema ga u bundleu studentskog puta" |

**Presuda: lazy loading je dobro riješen, nema duga.** Eager set je točno ono što treba pri
prvom dolasku (login/register/dashboard/moduli). `TaskEntryPage` je svjesno eager —
`:56-58`: „lagana komponenta (bez monaca), ne treba vlastiti chunk/Suspense".

### G.3 Monaco: code-splitan ✅ ali ogroman 🔴 — brojke iz `vite build`

```
$ npm run build     (exit 0, ✓ built in 4.57s)

dist/assets/index-D_qiHCBA.js            459.31 kB │ gzip: 141.64 kB   ← GLAVNI bundle
dist/assets/card-CrZ3H5Lw.js              76.54 kB │ gzip:  25.41 kB   ← dijeljeni (Card)
dist/assets/TaskPage-8jM67E0X.js         136.42 kB │ gzip:  35.28 kB
dist/assets/ProfilePage-la9q2hwh.js      373.10 kB │ gzip: 108.10 kB   ← recharts
dist/assets/AdminPage-3-W-JeLD.js          9.06 kB │ gzip:   3.61 kB
dist/assets/editor.api2-Cq5M29hm.js    3,627.16 kB │ gzip: 926.88 kB   ← 🔴 MONACO
dist/assets/pgsql-DTj74zXo.js             11.91 kB │ gzip:   4.42 kB
dist/assets/sql-NEE52Syq.js                8.84 kB │ gzip:   3.73 kB
dist/assets/mysql-SOo6toE5.js              9.65 kB │ gzip:   3.98 kB
… + ~90 chunkova jezika koje nikad ne koristimo (twig, scss, handlebars, julia,
  systemverilog, scala, wgsl, perl, php, razor, clojure, ruby, protobuf, elixir,
  redshift, abap, powerquery, freemarker2, solidity, …)

dist/assets/editor-Br_kD0ds.css          145.99 kB
dist/assets/index-B6ujgZXg.css            64.57 kB

Ukupno dist/assets: 15 MB · 105 JS chunkova · 14 512 028 B JS
```

**Monaco JE code-splitan** — nije u glavnom bundleu (459 kB), potvrđeno i komentarom
`monaco-setup.ts:11-12` i wrapupom 4.3.

🔴 **Ali uzrok naduvavanja je jedna linija** —
[monaco-setup.ts:15](frontend/src/lib/monaco-setup.ts#L15):
```ts
import * as monaco from "monaco-editor"
```
Barrel import cijelog paketa → svi jezici, svi doprinosi. Otud `editor.api2` 3.63 MB i ~90
mrtvih jezičnih chunkova. Nam trebaju **`sql` / `pgsql`** (30.4 kB zajedno s `mysql`).

Vite warning to i kaže: „Some chunks are larger than 500 kB after minification."

**Popravak** je `monaco-editor/esm/vs/editor/editor.api` + eksplicitna registracija samo
SQL-a. **Rizik: 🔴 VISOK** — `monaco-setup.ts` i `SqlEditor.tsx` su eval-verificirani (§C),
tema (`monaco-theme.ts`) i hotkey registracija vise o istom `monaco` objektu. Bez pune žive
reverifikacije punog ciklusa **ne dirati**. Vidi presudu u §G.4.

### G.4 Prvo učitavanje preko sporije veze — što je stvarni rizik

Procjena je **aritmetička iz gzip brojki**, ne mjerena (na VPS nije deployano):

| Put | Gzip | 4G ~4 Mbps | 3G ~1 Mbps |
|---|---|---|---|
| Login/Register (glavni + CSS) | ~142 + ~20 kB ≈ 162 kB | ~0,3 s | ~1,3 s |
| Dashboard (isti bundle, već cachiran) | 0 | ~0 | ~0 |
| **Prvi ulaz na `/task/:id`** | **927 + 35 + 25 ≈ 987 kB** | **~2,0 s** | **~7,9 s** |
| Profil (prvi ulaz) | ~108 kB | ~0,2 s | ~0,9 s |

**Stvarni rizik (ne kozmetika):**
1. 🔴 **~1 MB gzip prije prvog zadatka.** Na sporoj vezi ~8 s praznog čekanja. `Suspense`
   fallback (`router.tsx:65`) prikazuje „Učitavanje zadatka" pa **nije bijeli ekran** — to je
   ono što spašava. Ali student koji čeka 8 s bez konteksta zaključi da je puklo.
2. 🔴 **Nema `Cache-Control`/gzip garancije.** Sve gornje brojke pretpostavljaju da VPS
   **servira gzip/brotli**. Ako serve nije konfiguriran, `/task` je **3,6 MB nekompresirano**
   → ~29 s na 1 Mbps. **To je deployment stavka, ne 4.7** — ali je najveći perf rizik u
   cijelom inventaru i mora biti na deploy checklisti.
3. 🟡 15 MB `dist/` ⇒ deploy artefakt + disk. Ne pogađa studenta (chunkovi jezika se nikad
   ne fetchaju), ali je smeće.

**Kozmetika (ne dirati u 4.7):** `ProfilePage` 373 kB (recharts) — sekundaran ekran, lazy,
učitava se nakon što je student već u sustavu. `card` 76 kB dijeljeni chunk — 4.5a je
zabilježio da je zbroj neutralan.

**Presuda za 4.7:** Monaco tree-shaking je **najveći perf dobitak i najveći regresijski
rizik**, i tiče se **jedine eval-verificirane datoteke** koju bi 4.7 inače ostavio na miru.
Preporučam **NE dirati u 4.7**, a umjesto toga:
(a) potvrditi gzip/brotli na VPS-u (deployment, ne kod), i
(b) provjeriti da `Suspense` fallback na `/task` izgleda kao *namjerno čekanje*, ne kao
zamrznuto — to je layout/copy, nula rizika.
Ako se ipak radi tree-shaking, ide **zadnji**, sam, s punom živom reverifikacijom ciklusa.

---

## H — PRIJEDLOG REVIZIJSKE BILJEŠKE ZA `errata.md` (🔒 DOC — čeka odobrenje)

`docs/errata.md:62-79` („Opseg implementacije — REZANE faze") tvrdi da su 4.6 **i** 4.7
rezane i da to ide u rad. Ako 4.7 sada ide, tvrdnja postaje neistinita.

**NE mijenjam sam.** Predloženi tekst — ide **ispod** postojećeg odjeljka, koji ostaje
nepromijenjen (trag odlučivanja se ne prepisuje, isto kao §„Odluke koje čekaju"):

```markdown
### ⟳ REVIZIJA (2026-07-26) — Faza 4.7 je OŽIVLJENA, 4.6 ostaje rezana

**Što se mijenja:** odjeljak iznad i dalje točno opisuje odluku od 2026-07-20, ali je od
tada nadglasan u dijelu koji se tiče **4.7**. Faza 4.7 (visual QA / a11y / responsive /
hardening) **više nije rezana**. Faza 4.6 (motion + WebSocket) **ostaje rezana** i
neizmijenjena; umjesto nje je izvedena 4.6-eval (#37, #38, #39).

**Razlog — promjena strategije evaluacije s NADZIRANE na ASINKRONU JAVNU.** Odluka od
2026-07-20 pretpostavljala je nadziranu sesiju u labosu: pripremljeni računi, usmene
upute i osoba koja pomaže kad nešto pukne. Evaluacija se sada izvodi na **javnom URL-u**,
sa **samostalnom registracijom** sudionika i **bez nadzora**. Time se mijenja *što je*
polish:

- Put `/register → prvi login → prazna stanja → prvi zadatak` prestaje biti kozmetika i
  postaje **jedini kanal uputa** — nema usmenog objašnjenja koje bi ga nadomjestilo.
- Oporavak od greške prestaje biti ugodnost i postaje **uvjet da sudionik uopće završi** —
  nema nikoga da ga izvuče.
- Obrazloženje preporuke (#44) više se ne može dati uživo; ako ga UI ne nosi, sudionik ga
  ne dobiva.
- Nepoznat preglednik i nepoznata širina ekrana postaju stvarni rizik (u labosu su bili
  poznati).

**Što ostaje istinito iz odluke 2026-07-20:** obrazloženje da polish ne otključava novu
funkcionalnost i ne utječe na mjerenje vrijedi za **estetski** dio 4.7 (razmaci,
poravnanja, motion). Taj dio je i dalje najniži prioritet i reže se prvi ako rok pritisne.
Ono što je 4.7 dobila natrag je **operativna upotrebljivost bez nadzora**, ne uglađivanje.

**Kako se prijavljuje u radu:** u odjeljku o opsegu implementacije navodi se da je 4.6
(motion/WS) rezana svjesno i obrazloženo, a da je 4.7 izvedena u **suženom, prioritiziranom
obliku** vođenom zahtjevima asinkrone javne evaluacije — ne kao puni vizualni QA prolaz iz
plana §4.7. Popis stvarno izvedenog vodi `docs/faza-4.7-korak-0.md` §9 i wrapup 4.7.
```

**Dodatno traži ispravak (isti diff, uz odobrenje):**
- `docs/faza-4-plan.md:18` — „**prva se reže 4.6/4.7 polish**" → treba bilješku da 4.7 nije
  rezana.
- `docs/errata.md:24` (#13) — status nakon odluke iz §A.1.
- `docs/errata.md:28` (#17) — status nakon odluke iz §G.1.

---

## 9. 🔴 PRIJEDLOG STAGINGA 4.7 (iz nalaza, ne iz plana)

Redoslijed je **vidljivost × nemogućnost oporavka bez nadzora**, ne ljepota.
Rizik je ocijenjen **nad eval-verificiranim putem** (§C).

### 4.7-1 — Put prvog dolaska bez nadzora 🔴 NAJVIŠI

| Stavka | Datoteka | Opseg | Rizik nad eval putem |
|---|---|---|---|
| `lang="en"` → `"hr"` (NALAZ 4.7-B, WCAG 3.1.1) | `index.html:2` | 1 znak | 🟢 **NULA** |
| `<title>frontend</title>` → pravi naslov (4.7-C) | `index.html:6` | copy | 🟢 **NULA** |
| „Faza 4.1c — app shell" iz sidebara (4.7-D) | `AppShell.tsx:100` | copy | 🟢 **NULA** |
| Helper tekst uz `username` + **da je javan na Ljestvici** | `RegisterPage.tsx:82-95` | +1 `<p>` + `aria-describedby` | 🟢 **NULA** |
| Info blok o istraživanju iznad forme (§F.4) | `RegisterPage.tsx:69-75` | copy + blok | 🟢 **NULA** (⚠️ čeka odluku o GDPR obliku) |
| Stale komentari „partial REZERVIRAN" (§A.3, 🔒 DOC) | `index.css:14,172,245` | komentar | 🟢 **NULA** |

**Prazna stanja se NE diraju** — §F.3 pokazuje da su dizajnirana i promišljena. Ovo je
gotovo isključivo **copy i jedan atribut**. Najveći dobitak po najmanjoj cijeni u cijelom
inventaru.

### 4.7-2 — Oporavak bez pomoći + obrazloženje preporuke 🔴

| Stavka | Datoteka | Opseg | Rizik |
|---|---|---|---|
| „Zadatak ne postoji" dobiva izlaz (§F.5) | `TaskPage.tsx:70-75` | +1 link | 🟡 **NIZAK** — dira eval datoteku, ali **granu koja se u evalu ne pogađa** (nevalidan ID) |
| Kontakt u `ErrorState` defaultu (§F.5) | `state/ErrorState.tsx:20` | copy | 🟢 NULA |
| Rečenica o strategiji preporuke (#44, §F.6) | `FeedbackPanel.tsx:197-200` + `lib/recommendation.ts` | +1 konstanta, +1 `<p>` | 🟡 **NIZAK-SREDNJI** — 🔴 dira **FeedbackPanel**, eval-kritičan. Samo dodatak u postojeći `<p>` blok; **`deriveVerdict` i CTA grane se NE diraju** |
| Ista rečenica na Dashboardu | `ContinueCard.tsx:134-141` | copy | 🟢 NULA |
| `unknown` label divergencija (§E.4) | `verdict-ui.ts:54` | copy | 🟢 NULA |

⚠️ **Jedina stavka koja traži živu reverifikaciju:** `FeedbackPanel` dodatak. Nakon nje
ponoviti verifikaciju sva tri verdikta (correct/partial/incorrect) + `already_solved` čip.

### 4.7-3 — Responsive / browser rizik na javnom linku 🔴

| Stavka | Datoteka | Opseg | Rizik |
|---|---|---|---|
| **Mobilna navigacija ispod 768px (NALAZ 4.7-A)** | `AppShell.tsx:88-113` | **komponenta** (Radix `Dialog`/`Popover` — `radix-ui` je već dep, `sheet` **nije** dodan) | 🟡 **SREDNJI** — nova komponenta u ljusci koja **omotava** Task screen. Ne dira `TaskPage`, ali mijenja kontekst u kojem se renderira |
| **Odluka o Task screenu na mobitelu (§E.5)** | `TaskPage.tsx` | ovisi o odluci | 🔴 **VISOK ako se radi puni mobilni editor** / 🟡 **SREDNJI za „širi ekran" poruku** |
| Cross-browser smoke (Firefox/Safari) | — | ručno | 🟢 NULA (samo mjerenje) |
| Mjerenje pod 420px na ekranima iz §E.5 | — | ručno | 🟢 NULA |

🔴 **Ovdje mi treba tvoja odluka prije implementacije** (§E.5): „desktop/tablet-preferirano +
iskrena poruka" vs „puni mobilni Monaco". Preporuka: prvo.

### 4.7-4 — Nepolirane izmjene #41/#43 + cross-screen nekonzistentnost 🟡

| Stavka | Datoteka | Opseg | Rizik |
|---|---|---|---|
| `py-1.5` → `py-3` poravnanje klik-retka (§B.1) | `MasteryHighlights.tsx:81` | 1 klasa | 🟢 NULA |
| `lib/datetime.ts` konsolidacija (§E.4) | nova + 3 poziva | mala | 🟢 NULA ako se opcije zadrže |
| Izmjeriti kontrast/touch #41/#43 čipova (🔒 DOC) | — | mjerenje | 🟢 NULA |
| `/review-animations` nad #41/#43 dodacima | — | gate | 🟢 NULA |

Sve je kozmetika **osim** mjerenja — a mjerenja moraju biti jer po 🔒 DOC politici bez brojke
i datuma ne smijem tvrditi da su ti čipovi a11y-čisti (§B.1 to izrijekom ne tvrdi).

### 4.7-5 — Smoke suite (#17) — gate za eval 🟡

| Stavka | Opseg | Rizik |
|---|---|---|
| `@playwright/test` u `devDependencies` | 🔴 **traži tvoje odobrenje** (CLAUDE.md) | 🟢 NULA (dev-dep) |
| 1 spec, 7 koraka (§G.1) | mala | 🟢 NULA nad kodom |
| **Sentinel `smoke_` + zabrana tijekom sesije u runbooku** | **procedura** | 🔴 **VISOK ako se preskoči** — po #40 smoke zaprlja `agent_messages_log`, koji nijedan cleanup ne pokriva |

Rizik ovdje **nije u kodu, nego u podacima.** Suite mora biti pokretljiv *prije* baselinea, ne
tijekom evala.

### 4.7-6 — Estetika koju nitko neće primijetiti — ZADNJE 🟢

| Stavka | Rizik |
|---|---|
| #13 partial hue → 45 (§A.1) — tokeni + MASTER + mjerenje kontrasta | 🟡 dira FeedbackPanel piksele → traži reverifikaciju |
| `emil-design-eng` polish 6 golih ekrana (§E.1) | 🟡 širok dodir, nula funkcionalne koristi |
| Razmaci/poravnanja/token dosljednost | 🟢 |
| **Monaco tree-shaking (§G.4)** | 🔴 **VISOK — preporučam NE u 4.7** |

**#33: ne dira se ni na kraju** (§A.2, matematički odbačeno).

---

## 10. 🔴 STANI-I-JAVI — sažetak

**Traži tvoju odluku prije nastavka:**

1. **Task screen na mobitelu** (§E.5) — „desktop/tablet-preferirano + poruka" (preporuka) vs
   „puni mobilni Monaco"? Druga opcija dira eval-verificiranu jezgru.
2. **Oblik suglasnosti sudionika** (§F.4) — info tekst (frontend-only, 4.7 ✅) vs **bilježen
   checkbox** (novo polje → **backend → Faza 5/deployment, NE 4.7**)? Ako FOI traži zapis
   suglasnosti, ovo ispada iz 4.7.
3. **`@playwright/test` u `package.json`** (§G.1) — nova dependency, po CLAUDE.md tražim
   odobrenje.
4. **Revizijska bilješka za erratu** (§H) — odobravaš predloženi tekst?
5. **#13 partial hue → 45** (§A.1) — ide u 4.7-6 ili se zatvara kao trajna limitacija kao
   #33? Izvedivo je, ali dira eval-verificirane piksele za dobitak koji nitko neće primijetiti.

**Zatečeno kao backend, dakle IZVAN 4.7 (samo prijavljujem, ne diram):**
- `hint_requested` se nikad ne postavlja na `True` (`persistence.py:78` hardkodira `False`)
  → HintAgent put je **Faza 5** (§D.2).
- #42 indikator „riješeno" na Modulima traži user-aware `/modules` → **Faza 6**.
- Sanitizacija/rezervacija `username`a kod-side → **Faza 5/deployment**. 4.7 rješava samo
  helper tekst.
- gzip/brotli i `Cache-Control` na VPS-u (§G.4) → **deployment checklista**, ne kod. Najveći
  perf rizik u inventaru.

**Čisto (STANI-uvjeti koji se NISU aktivirali):**
- ✅ `schema.d.ts` **nije** divergirao (§F.7, prazan `diff` nakon regeneracije).
- ✅ Ni jedan eval-verificirani ekran **ne traži** nedovršen polish (§C.2) — Task screen je
  jedini koji je prošao pun lanac.

---

## 11. Što ovaj inventar NIJE provjerio (iskren opseg)

Po 🔒 DOC politici, da se ne zamijeni sa provjerenim:

- **Nula mjerenja u pregledniku.** Sve a11y/responsive tvrdnje su **strukturne** (postoji li
  ikona, `aria-label`, `overflow-x`, breakpoint), ne fotometrijske. Kontrasti, touch targeti i
  reflow pod 420px **nisu mjereni** u ovoj sesiji.
- **App nije pokrenut.** Nema žive verifikacije nijednog ekrana; brojke iz §G su iz
  `vite build`, brojke iz §G.4 su **aritmetika iz gzip veličina**, ne mjerena mreža.
- **Cross-browser nije taknut.** Samo Chromium-bazirani pretpostavke iz prijašnjih faza.
- **Backend nije čitan osim ciljanih grepova** (`hint_requested`, `partial`).
- Tvrdnje o polish lancu (§B) izvedene su iz **commit bodyja i wrapupa**, ne iz zapisa
  pokretanja skillova (takvi zapisi ne postoje u repou).
