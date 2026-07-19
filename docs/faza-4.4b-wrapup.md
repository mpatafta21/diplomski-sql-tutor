# Faza 4.4b — BKT P(L) krivulje (istraživački doprinos) — WRAP-UP

**Status:** ✅ KOMPLETNA na grani `faza-4-4-profile`, tag `faza-4-4b-bkt-curves`. Bez push-a.
**Obuhvat:** mreža malih krivulja (small multiples) po modulu + uvećani detalj s tooltipom, tri skupine koncepata, fiksna Y-os, referentna linija praga, a11y tekstualni kanal.
**Gates:** `tsc -b` ✓ · `vite build` ✓ · `oxlint` exit 0 (4 pre-existing fast-refresh warninga) · `prettier --check` ✓ · `pytest` **485 passed / 1 skipped** · `make preflight` **ZELEN** · `schema.d.ts` **byte-identičan** · `/code-review` (6 nalaza, svi popravljeni) · `accessibility-review` (1 kritičan popravljen, 1 limitacija).
**Backend:** NULA izmjena. Nijedan backend fajl nije dirnut (`git status` potvrđuje).

---

## 1. Što je isporučeno

| Datoteka | Uloga |
|---|---|
| `hooks/useMasteryHistory.ts` | jedan fetch cijele nepaginirane serije (`queryKey: ["mastery-history"]`) |
| `lib/mastery-history.ts` | čisti izvod: grupiranje, kategorizacija, `Y_DOMAIN`, formatiranje |
| `components/profile/MasteryCurves.tsx` | orkestracija sekcije, stanja, odabir koncepta |
| `components/profile/ConceptCurveCard.tsx` | mini-krivulja + **tekstualni** P(L) i status |
| `components/profile/ConceptCurveDetail.tsx` | uvećani graf, tooltip, a11y tablica točaka |
| `components/profile/UntrackedConcepts.tsx` | skupine (B)/(C) — bez obećanja dostupnosti |

Dirnuto postojeće: `ProfilePage` (kompozicija + `id="povijest"` anchor), `useSubmitAttempt` (+1 invalidacija), `lib/mastery.ts` (izvučen `masteryStep`/`hasOwnTasks`), `lib/progress.ts` (koristi `hasOwnTasks`), `lib/api/types.ts` (+1 alias).

## 2. Zaključane odluke (i zašto)

- **🔴 Os X = REDNI BROJ PRILIKE, ne vrijeme.** Standard u BKT literaturi (Pelánek 2017; Yudelson 2013), a naši su timestampovi zgusnuti (27 attempta unutar jedne minute) pa bi vremenska os dala nakupinu. Timestamp je u tooltipu. Dokaz iz DOM-a: X tickovi `["1","6","11","16","21"]`.
- **🔴 Os Y = FIKSNO [0,1], nikad auto-scale.** Dokaz iz DOM-a: Y tickovi `["0.00","0.25","0.50","0.75","1.00"]` na `order_by` seriji koja od 12. prilike stoji u 0.99978–1.00000. Auto-scale bi taj plato razvukao preko cijele visine → vizualna laž. Vidi **NALAZ #16**.
- **Referentna linija iz `/profile.mastery_threshold`**, nikad hardkodirano — živo renderira „prag ovladanosti (0.850)".
- **Boja mini-krivulje = magnituda** (mastery gradijent prema trenutnom `p_l`, MASTER §2.3/§2.6); **detalj = `--chart-1`** (identitet serije, magnituda je već na osi).
- **Redoslijed točaka se NE re-sortira** — točke istog attempta dijele identičan timestamp (živo: 3 koncepta na istu mikrosekundu), pa se oslanjamo na dolazni `ORDER BY created_at, id`.
- **Jedan fetch, klijentsko grupiranje** — `?concept=` po konceptu bio bi N+1.

## 3. 🔴 Tri skupine koncepata — i ispravak koji je review iznudio

Derivacija je iz podataka (`hasOwnTasks` + broj modula), nikad iz popisa kodova. Živo (30 koncepata): `primary_task_count === 0` daje TOČNO 4 — `column_alias`, `join_condition` (M0) i `explain_plan`, `index_usage` (M6).

> ⚠️ **Ispravak spec-a:** skupina (A) ima **26** koncepata, ne 22 (30 ukupno − 4). Bitno je i da `null_handling` (modul 0, ali **4 primarna zadatka**) ide u (A), ne u glue skupinu — modul 0 nije sinonim za „bez zadataka".

**NALAZ #31 (uhvaćen u `/code-review`, popravljen):** prva verzija je klasificirala koncept PRIJE nego je pogledala točke. `column_alias` ima 0 primarnih ali **4 aktivna sekundarna** zadatka, a BKT ažurira i sekundarne koncepte → student dobije stvarnu točku (`p_l=0.7284`, živo dokazano rješavanjem `inner_join_d2_b39dec5d`), koju je kod tiho odbacio uz tekst „nema zasebnu krivulju". **Pravilo je sada: izmjereni podatak nadjačava kategoriju.** Za rad je važna i općenitija posljedica: *„koncept bez primarnih zadataka" ≠ „koncept bez BKT procjene"* — `order_by` ima 2 primarna zadatka, a 21 točku.

## 4. Recharts — uvjeti iz spikea

1. `recharts@3.9.2`, `--legacy-peer-deps` (poznat openapi-typescript ⟂ typescript@6 konflikt; **bez** `.npmrc`, bez bumpa). `react-is@19` već postojao — nije dupliciran.
2. **🔴 Chunk dokaz (before → after):** glavni bundle `index` **533.67 kB → 533.86 kB** (+0.19 kB, i to iz MOG koda — invalidacija i tipovi, ne iz rechartsa), lazy `ProfilePage` **11.70 kB → 373.66 kB** (+362 kB). `grep recharts|react-smooth` u glavnom bundleu = **0 pogodaka**, u ProfilePage chunku = 15. *Napomena: „nedirnut" je +0.19 kB, ne 0 — ne tvrdim bit-identičnost.*
3. **Theme-reaktivnost bez remounta (izmjereno):** `stroke` atribut ostaje `var(--mastery-100)` prije i poslije togglea, computed boja se mijenja `oklch(0.86 0.12 190)` → `oklch(0.44 0.072 190)`, a `data-probe` postavljen na SVG čvor **preživi** toggle → isti DOM čvor, nema remounta.
4. `isAnimationActive={false}` na svakoj seriji i na tooltipu (react-smooth ne poštuje `prefers-reduced-motion`).

## 5. Stanja

- **Novi user** (`[]`, HTTP 200): `EmptyState` + CTA. Lista „još nema podataka" se tada **preskače** (inače dvije poruke o istoj činjenici + zid od 26 čipova).
- **1 točka:** crta se TOČKA, ne linija — verificirano na admin useru (1 kružić, `path d = null`, bez `NaN` u geometriji, X-os pokazuje samo „1"). Uz to hrvatski plural „1 prilika".
- Loading/Error: postojeći primitivi iz `components/state/`.

## 6. A11y — što je izmjereno

**🔴 Kritično, popravljeno (NALAZ #32):** Recharts v3 default `accessibilityLayer` stavlja `tabindex="0"` + `role="application"` na svaki graf. Uz `aria-hidden` mini-grafove to je dalo **15 „crnih rupa fokusa"** (tab stane na element o kojem AT ne kaže ništa). Popravak `accessibilityLayer={false}` + `tabIndex={-1}` na mini-grafovima → **15 → 0**, ukupno tab-stopova 78 → 63. Detaljni graf sloj zadržava (nije `aria-hidden`, keyboard navigacija ondje ima vrijednost).

**Ostalo (izmjereno canvas-sRGB konverzijom, obje teme):**
- Sav tekst prolazi AA: 18.97:1 / 19.8:1 (naslov, P(L)), 7.66:1 / 4.74:1 (muted, 10.24 px).
- Osi i tickovi 7.66:1 / 4.74:1 ✓, `--chart-1` 7.44:1 / 4.86:1 ✓, prag (`accent-warm`) 10.41:1 / 3.19:1 ✓.
- Touch targeti: najmanja kartica **141 px** visine (≫ 44 px) ✓. Reflow na 720 px bez horizontalnog scrolla ✓.
- Disclosure semantika: `aria-expanded` + `aria-controls` → `role="region"` s labelom „Detalj krivulje — ORDER BY" (bilo `aria-pressed`, što je za panel netočno).
- Krivulja NIJE jedini kanal: svaka kartica nosi tekstualni `P(L)` + status, detalj ima punu `<table>` s `<caption>` i `scope="col"`.

**📌 Prihvaćena limitacija:** `--mastery-0` (2.35:1 dark / 1.58:1 light) i `--mastery-25` (2.28:1 light) su **ispod 3:1** za grafičke objekte (1.4.11). Pogađa krivulje koncepata s niskim P(L) — dakle baš one koje student koji muku muči najviše gleda. Ublaženo time što je graf `aria-hidden` uz potpuni tekstualni ekvivalent (informacija se ne gubi), pa 1.4.11 formalno ne grize. **Ovo je token-level stvar (MASTER §2.3), ne 4.4b:** ide uz rekalibraciju palete u **4.7**, zajedno s već zakazanom korekcijom partial hue 60→45 (#13).

## 7. Za nasljednike

- **`Y_DOMAIN` je invarijanta** — svaki novi graf P(L) koristi fiksnu skalu. Auto-scale na saturiranoj seriji je vizualna laž (NALAZ #16).
- **`hasOwnTasks` (lib/mastery.ts) je JEDINI izvor** predikata „koncept ima vlastite zadatke" — konzumiraju ga `deriveProgress` i `categorizeConcept`. Prag mijenjati SAMO ondje (prije 4.4b bio je prepisan na dva mjesta).
- **Svaki novi Recharts graf** mora proći provjeru iz #32 (`accessibilityLayer` vs `aria-hidden`) — relevantno za 4.5.
- **Datum/vrijeme:** krivulje koriste iste `Intl` opcije kao `AttemptRow` (`dateStyle:"medium"`, `timeStyle:"short"`); objedinjavanje u `lib/datetime.ts` je kandidat za 4.7 (AttemptRow je 4.4a, izvan opsega ove pod-faze).
- **Deep-link na konkretan pokušaj ne postoji** — `/attempts` nema server-side filtere (#15) i filter se NIJE dodavao zbog ovoga; link vodi na povijest kao cjelinu (`#povijest` anchor).

## 8. Otvoreno / sljedeće

1. **NALAZ #17 i dalje otvoren** — verifikacija je i ovdje bila **ručna** (headless Chrome/CDP iz scratchpada, `playwright-core` NIJE u `package.json`). Nema committed e2e suitea; ostaje ulazni gate za eval (4.7).
2. **Faza 4.5** — Leaderboard + Admin (nav stub obrazac).
3. Kandidati za 4.7: kontrast mastery-0/25 za stroke, `lib/datetime.ts`, smoke suite.
