# Faza 5.2 — UI za hint (wrapup)

**Datum:** 2026-08-13 · **Grana:** `faza-5-hintagent` · **Tagovi:** `faza-5-2-ui`,
`faza-5-complete` · **Commitovi:** B (backend) i C (frontend) odvojeni, kako je plan tražio.

---

# 0. Isporučeno

| # | promjena | gdje |
|---|---|---|
| 1 | `ProfileResponse` + `remaining` / `next_refill_at` | `backend/app/api/schemas.py`, `routes.py` |
| 2 | `schema.d.ts` + `openapi.json` regenerirani | `npm run gen:api`, `make openapi-snapshot` |
| 3 | `useHint` mutacija, mapiranje po `detail` | `frontend/src/hooks/useHint.ts` |
| 4 | mapiranje ishoda → poruka, fail-closed | `frontend/src/lib/hint.ts` |
| 5 | slot za savjet iznad `FeedbackPanel`a | `frontend/src/components/task/HintPanel.tsx` |
| 6 | gumb, meta redak, `aria-live`, dva `data-testid` | `frontend/src/pages/TaskPage.tsx` |
| 7 | N-20 regresijski gate | `frontend/e2e/hint-row.spec.ts` |
| 8 | dokazne snimke svih stanja | `docs/figures/hint-stanja-5.2/` |

---

# A — Baseline, snimljen PRIJE gumba

Ista lekcija kao p95 u 5.1: referentna vrijednost se ne snima retroaktivno. Mjereno na
živom Task ekranu (`/task/15`, pravi podaci), **prije ijedne izmjene `frontend/src/`**.

| širina | kartica editora | `editor-box` | akcijski red | djece u redu | prelama se |
|---|---|---|---|---|---|
| 768 px | 605,2 | 420 | **44** | 1 (`div` s Run+Submit) | ne |
| 1280 px | 705,2 | 520 | **44** | 1 | ne |
| 1920 px | 705,2 | 520 | **44** | 1 | ne |

Uz to izmjereno i ono što baseline tablica ne pokazuje, a odlučilo je dizajn:
**stvarna širina akcijskog reda na 768 px je 432 px** (sidebar + grid uzimaju ostatak
od 768), a Run + Submit ondje troše **298,5 px**. Gumbu je preostalo ~121 px — i to je
cijeli manevarski prostor koji je 5.2 imala.

---

# B — Backend: `ProfileResponse` +2 polja

## B.1 Jedan izvor, i to dokazan mjerenjem

Ruta zove `hint_logic.hint_credit` — **istu funkciju** koju zove `POST /hint`. Nije
izdvajanje bilo potrebno; funkcija je već postojala kao zajednička.

Test `test_profile_remaining_matches_hint_response` uspoređuje brojku iz `/profile` s
brojkom iz `HintResponse` **nakon istog niza**: pun bucket → hint → idempotentno
ponavljanje. Ne provjerava da kod izgleda dijeljeno, nego da brojke ne odlutaju.

## B.2 `next_refill_at` je `null` kad je bucket pun

Nasljeđeno iz `hint_credit`, ne dodano ovdje.

## B.3 🔴 STANI I JAVI — brojač pod isključenim flagom

**Odluka: oba polja su `null`.**

Brojač bez značajke je besmislen, a svaka konkretna brojka laže na svoj način:

- `5` **reklamira** hintove kojih na ovom poslužitelju nema;
- `0` se čita kao „potrošeno" — a to je stanje iz kojeg se izlazi čekanjem, dok se ovdje
  nema što čekati. To je i jedina razlika koju UI mora vidjeti, pa je čuva zaseban test
  (`test_exhausted_bucket_is_zero_not_null`).

**Izostavljanje polja odbačeno**, iako ga je plan naveo kao kandidata: `openapi-typescript`
ionako generira `remaining?: number | null` (polje nije `required`), pa bi frontend morao
pokrivati *dva* oblika odsutnosti (`undefined` i `null`) umjesto jednog. Jedan oblik je
manje grana na fail-closed putu.

Napomena o dvoznačnosti koju odluka **ne** uklanja: `next_refill_at === null` znači i
„bucket pun" i „značajka isključena". Razliku nosi `remaining` (`5` vs `null`), a UI je
ionako ne treba — gumb se sakriva prije nego brojač postane vidljiv.

## B.4 🔴 STANI I JAVI — `schema.d.ts` diff

**Diff je točno §C.1.3 + dva polja. Ništa više.** Ugovor 5.1 je bio potpun.

```
/hint → post                                   ← C.1.3 #1
HintRequestBody                                ← C.1.3 #1
HintResponse                                   ← C.1.3 #1
MeResponse.hints_enabled                       ← C.1.3 #1
TaskDetailResponse.last_attempt_error_type     ← C.1.3 #1
ProfileResponse.remaining                      ← 5.2
ProfileResponse.next_refill_at                 ← 5.2
```

**Usput popravljeno:** `make openapi-snapshot` pisao je JSON u **jedan red**, iako je
komentar targeta tvrdio da je snapshot „diff-vidljiv u PR-u". Svaka regeneracija davala
je diff od 1696 obrisanih redaka, u kojem se stvarna promjena ne vidi. Dodan `indent=2`
— format je sada isti kao commitani artefakt, a diff gore je čitljiv upravo zbog toga.

---

# C — Frontend

## C.1 Mapiranje po `detail`, ne po statusu

`lib/hint.ts` zna pet ishoda i šesti — `unknown`. `ApiError` iz `lib/api/query` nosi samo
`status`, pa ga `useHint` **ne koristi**: tijelo greške se čita u `mutationFn` i pretvara
u `HintError.reason`. Bez toga bi `503 hints_disabled` (sakrij gumb zauvijek) i
`503 hint_unavailable` (pokušaj opet) bili isto stanje.

Fail-closed po obrascu `lib/feedback.ts`: nepoznat `detail` → generička poruka s retryjem,
nikad prazan slot.

`onSuccess` invalidira **samo** `["profile"]` (C.3.3). Hint ne mijenja BKT, XP ni
preporuku, pa se ne invalidira ništa drugo — isti obrazac kao `useRun`.

## C.2 🔴 STANI I JAVI — pomicanje fokusa na klik: **NE**

Plan (§C.5.2 t.2) je tražio ocjenu prijedloga da klik na zaključan gumb pomakne fokus na
vidljivi razlog. **Presuda: ne pomiče se. Dovoljan je `aria-live="polite"`.** Četiri
razloga, po težini:

1. **Razlog se čuje i bez klika.** `aria-describedby` je na gumbu, pa ga čitač ekrana
   pročita čim gumb dobije fokus — dakle **prije** klika. Objava na klik je pojačanje,
   ne jedini kanal.
2. **Fokus bi otišao s kontrole koju korisnik upravo koristi.** Tipkovnički korisnik
   pritisne Enter i izgubi mjesto; za povratak treba Shift+Tab. To je kazna za onoga koga
   mjera treba zaštititi.
3. **Traži `tabindex="-1"` na statičnom `<p>`** — dodatna zaustavna točka i dokumentirani
   a11y miris.
4. **WCAG 3.2.1/3.2.2** upozoravaju na nenajavljenu promjenu konteksta na fokus/unos;
   nezatražen skok fokusa je upravo to.

Implementacijska napomena koja nije bila u planu: `aria-live` objavljuje **promjenu**
sadržaja, pa bi drugi klik s istim tekstom prošao nečujno. Regija se zato prvo prazni pa
puni (`setHintObjava("")` → 80 ms → tekst). Bez toga bi „objava na klik" radila točno
jednom po ekranu.

**Izmjereno:** klik na zaključan gumb → **0 zahtjeva prema `/hint`** (brojač mrežnog
prometa u Playwrightu), a `[aria-live]` sadrži
`"Savjet se otključava nakon netočne predaje."`.

## C.3 🔴 STANI I JAVI — zastarjeli savjet: **ostaje, uz oznaku**

Tri kandidata iz plana i razlog izbora:

| opcija | zašto ne / da |
|---|---|
| briše se na novoj predaji | 🔴 **tiho uništava plaćeni sadržaj.** Idempotencija veže hint uz `after_attempt_id`; nakon nove predaje isti klik traži **novi** hint i troši **novi** kredit. Student ne može besplatno vratiti ono što je obrisano |
| **ostaje uz oznaku (odabrano)** | savjet koji je student primjenjivao ostaje čitljiv, a jedna rečenica („Savjet je zatražen uz prethodnu predaju.") uklanja laž da opisuje sadašnju grešku |
| ostaje nepromijenjen | savjet bi šutke opisivao grešku koje više nema — najgore od tri |

Cijena odabranog je jedan redak teksta. Cijena brisanja je kredit.

**Reset po zadatku (C3.2) — potvrđeno.** Sve hint stanje (`hintText`, `hintStale`,
`hintsHidden`, `hintObjava`) živi u `TaskView`, koji je `key={task.id}` još od 4.3b. Hint
iz zadatka 15 **ne može** preživjeti prelazak na 16, iz istog mehanizma koji već resetira
SQL i Run rezultat. Provjereno u živom prolasku kroz dva zadatka.

## C.4 Brojač

Iz `/profile`, u meta retku, **nikad u natpisu**. Izmjereno da se ne dekrementira lokalno:

```
prije hinta        Preostalo savjeta: 4
nakon hinta        Preostalo savjeta: 3     ← invalidacija ["profile"] iz useHint
nakon ponavljanja  Preostalo savjeta: 3     ← idempotentno, kredit se NE troši
```

Da je brojač dekrementiran lokalno, treći redak bi pisao `2` i lagao.

## C.5 `data-testid`

`editor-box` i `action-row` — prva dva u projektu, oba potrošena u `e2e/hint-row.spec.ts`.

---

# D — Exit: izmjereno

## D.1 🔴 Matrica §C.4.1 — **jedna ćelija se pomaknula, i to predvidivo**

| širina | | bez gumba | `disabled` | `enabled` |
|---|---|---|---|---|
| **768** | kartica | 605,2 | **636,4** | **636,4** |
| | `editor-box` | 420 | 420 | 420 |
| | `action-row` | 44 | 44 | 44 |
| | prelama se | ne | **ne** | **ne** |
| **1280** | kartica | 705,2 | **736,4** | **736,4** |
| | `editor-box` | 520 | 520 | 520 |
| | `action-row` | 44 | 44 | 44 |
| | prelama se | ne | **ne** | **ne** |
| **1920** | kartica | 705,2 | **736,4** | **736,4** |
| | `editor-box` | 520 | 520 | 520 |
| | `action-row` | 44 | 44 | 44 |
| | prelama se | ne | **ne** | **ne** |

**Ono što je N-20 tražio — drži.** Akcijski red je 44 px u svih devet ćelija, editor se
nije pomaknuo ni za piksel, red se ne prelama ni na 768 px. Gumb stane u onih ~121 px koji
su mu preostali.

**🔴 Ono što se pomaknulo: kartica, +31,2 px u svih šest ćelija s gumbom.** To NIJE
gumb — to je **vidljivi meta redak** ispod akcijskog reda (razlog kad je zaključano,
brojač kad je otključano): 19,2 px teksta + 12 px iz postojećeg `space-y-3`.

Zašto nije riješeno da kartica ostane nepromijenjena:

- Redak bi morao stati **unutar** onih 44 px, dakle u akcijski red. Na 768 px ondje ima
  432 px ukupno, a Run + Submit + gumb za savjet troše ~432. **Za tekst nema mjesta —
  ni jedan piksel.**
- Alternative bi tražile žrtvovanje nečega što nije bilo na stolu: skraćivanje
  zamrznutog natpisa, `size="sm"` gumb (28 px < 44 px, ruši WCAG 2.5.5 invarijantu iz
  `button.tsx`), ili skrivanje `Kbd` čipova s Run/Submit — a to je izmjena
  eval-verificiranog UI-ja radi kozmetike.
- Sakriti razlog nije opcija: `aria-describedby` mora pokazivati na **vidljiv** tekst
  (§C.5.1, presedan `RegisterPage.tsx:152`).

**Zaključak:** §C.4.1 je htio dokazati da gumb ne gura editor. Ne gura. Kartica je niže
od editora i raste prema dolje, pa +31,2 px ne pomiče ništa iznad sebe. Ako se svejedno
želi nula pomaka, jedini put je odluka o `Kbd` čipovima — i to je odluka za tebe, ne za
ovu fazu.

## D.2 N-20 test — i dokaz da pada

`e2e/hint-row.spec.ts` na 768 px tvrdi `action-row === 44` i `editor-box === 420`.

**Dokazano namjernom promjenom natpisa** („Zatraži hint" → „Zatraži hint za ovaj zadatak"):

```
Expected: 44
Received: 100      ← red se prelomio, kao što N-20 predviđa
1 failed
```

Natpis vraćen; test zelen. Test se **glasno preskače** kad je `USE_LLM_HINTS=false` —
tada gumba nema i tvrdnja ne bi mjerila ništa.

## D.3 Svih sedam stanja — na živom lancu

Snimke i provenijencija: `docs/figures/hint-stanja-5.2/`.

| stanje | ishod na ekranu | dokaz |
|---|---|---|
| `hints_disabled` | gumb **nije u DOM-u** (`count() === 0`), nema ni meta retka | `1-hints-disabled.png` |
| `hint_not_unlocked` | poruka **bez** retryja | `6a-…png` |
| `hint_rate_limited` | razlog + „Sljedeći savjet za 3 h 57 min" | `6b-…png` |
| `hint_unavailable` | gumb **ostaje**, `ErrorState` s retryjem | `5-…png` |
| 200 `fallback` | tekst savjeta u slotu | `4-…png` |
| idempotentno ponavljanje | **identičan tekst**, brojač se ne mijenja | isti prikaz (C.2.2) |
| `hint_timeout` | vlastita poruka + retry | `7-…png` |

`hints_disabled` i `hint_unavailable` daju **različit** ishod, iako oba nose 503 — što je
i bila poanta mapiranja po `detail`.

🔴 **Odstupanje:** `source: "llm"` nije izazvan uživo u 5.2. Poslužitelj je namjerno vožen
bez `ANTHROPIC_API_KEY`, pa su svi uspješni hintovi iz kataloga. Razlog je izbjegavanje
potrošnje bez tvoje odluke; gubitka dokaza nema jer se `source` **nigdje ne renderira** —
`llm` odgovor je pikselski identičan `fallback` odgovoru, a LLM put je dokazan uživo u
5.1 §E. `hint_timeout`, koji korak 0 nije uspio izazvati, **jest** izazvan ovdje
(`HINT_TIMEOUT=0.001`).

## D.4 Koegzistencija i re-verifikacija

**Hint + feedback istovremeno:** oba vidljiva, `hint.top < feedback.top`, oznaka
zastarjelosti prisutna (`8-koegzistencija-stale.png`).

**🔴 `FeedbackPanel`, sva 4 stanja** — `TaskPage.tsx` je eval-verificiran put, pa je
ponovno provjeren na živom lancu: Netočno (0 XP) · Djelomično (+8 XP) · Točno (+10 XP,
bedž) · Već riješeno (bez XP). **Bez regresije.**

## D.5 🔴 Kontrast (N-4, `getComputedStyle` nad živim elementom)

Metoda: boje se **ne parsiraju regexom** — tokeni su `oklch()`, pa bi regex nad
`oklch(0.7 0.02 260)` vratio besmislen broj i tiho dao krivi omjer. Boje se rasteriziraju
kroz `<canvas>` i čitaju kao pikseli; podloga se kompozitira uz stablo dok alfa ne
dosegne 1. Tema je jedna (light je ukinut u 4.7).

| par | tekst | podloga | omjer | AA |
|---|---|---|---|---|
| natpis gumba, **zaključan** | `#9c9fb7` | `#13142c` | **6,92:1** | ✅ |
| natpis gumba, **otključan** (`hint`) | `#36dede` | `#012525` | **9,79:1** | ✅ |
| razlog (`muted-foreground`) | `#9c9fb7` | `#13142c` | **6,92:1** | ✅ |
| brojač `remaining` | `#9c9fb7` | `#13142c` | **6,92:1** | ✅ |
| tekst savjeta u slotu | `#f3f4fe` | `#012525` | **14,84:1** | ✅ |
| `<code>` čip u savjetu | `#f3f4fe` | `#05141d` | **17,11:1** | ✅ |
| `rate-limited` tekst | `#9c9fb7` | `#091e28` | **6,55:1** | ✅ |

Brojke za plohe savjeta su iz **druge iteracije** (v. §E3) — prva verzija stajala je na
`bg-muted/40` i mjerila 15,48:1. Ponovno je izmjereno jer se ploha promijenila, a ne
prepisano: to je točno greška koju opisuje ERRATA #50 (pet mjerenja, svako točno za svoju
plohu, defekt preživio).

🔴 **Odstupanje od §C.5.3:** plan je za natpis gumba naveo podlogu `card`. Stvarna podloga
je `bg-muted` **samog gumba** (`#212243`), ne kartica — plan je pisan prije nego je gumb
dobio plohu. Izmjeren je stvarni par; da je izmjeren propisani, brojka bi bila neistinita.

## D.6 Gateovi

| gate | ishod |
|---|---|
| `tsc -b` | ✅ |
| `vite build` | ✅ |
| `oxlint` | ✅ (samo zatečeni `only-export-components` warninzi) |
| `prettier --check .` | ✅ |
| `npm run e2e` | ✅ **2 passed**, teardown čist (sve tablice `+0`, `agent_messages_log` +27 kao i uvijek) |
| `pytest` | ✅ **755 passed, 1 skipped** |
| `make preflight` | ✅ zelen |

---

# E — Odstupanja od plana, na jednom mjestu

| # | plan | izvedeno | zašto |
|---|---|---|---|
| 1 | „visina kartice nepromijenjena u svih 9 ćelija" | kartica **+31,2 px** u 6 ćelija s gumbom | vidljiv razlog (§C.5.1) ne stane u 44 px reda na 768 px; red i editor **jesu** nepromijenjeni |
| 2 | kontrastni par „natpis gumba vs `card`" | izmjeren „natpis gumba vs `bg-muted` gumba" | gumb ima vlastitu plohu; propisani par ne postoji na ekranu |
| 3 | „svih 7 stanja na živom lancu" | 7/7, ali `source:"llm"` kroz katalog | bez `ANTHROPIC_API_KEY` — nema potrošnje bez odluke; `source` se ne renderira, prikaz identičan |
| 4 | — | `make openapi-snapshot` dobio `indent=2` | target je tvrdio „diff-vidljiv u PR-u", a pisao jedan red |

---

# E2 — Prvi prolaz s UKLJUČENIM LLM-om (2026-08-13, nakon taga)

Flag je nakon zatvaranja faze prebačen na `USE_LLM_HINTS=true` u `backend/.env` (i cijeli
blok hint varijabli dodan u `.env.example`, gdje ga dotad **uopće nije bilo**). Prvi
prolaz kroz UI sa živim modelom, 5 stvarnih poziva.

**Mehanika drži bez iznimke:**

| provjera | rezultat |
|---|---|
| brojač kroz niz | 5 → 4 (savjet) → **4** (ponavljanje) → 3 → 2 |
| ponovljeni klik na isti pokušaj | **bajt-identičan tekst**, kredit netaknut |
| različiti pokušaji → različiti savjeti | ✅ tri različita teksta |
| točna predaja | gumb se **ponovo zaključava**, savjet ostaje uz oznaku |
| klik na zaključan gumb | **0 zahtjeva** |
| prelazak na drugi zadatak | savjet nestaje (keyed `TaskView`) |
| latencija | 3,6–4,2 s (LLM) · 1,8 s (ponavljanje iz pohrane) |

**Dva nalaza koje je otkrio tek živi model** — mock u `test_hint_route.py` provjerava
mehaniku, a sadržaj savjeta ne gleda nitko:

- **ERRATA #64 🔴** — savjet za `row_mismatch` je nagađanje i jednom je dao **netočan
  SQL** („prvo `LIMIT`, pa `ORDER BY`"). Uzrok: payload za taj tip nosi interni string
  `Row 0 differs`, dok `wrong_columns` nosi `expected_columns` i ondje je savjet točan.
  Popravak je izmjena payloada → zaseban zadatak, izvan opsega 5.2.
- **ERRATA #65 🟡 → popravljeno isti dan** — model vraća Markdown, slot ga je prikazivao
  doslovno. `hintSegments`/`hintParagraphs` prevode **samo** `**bold**` i `` `kod` ``,
  fail-safe na nesparene znakove, bez `dangerouslySetInnerHTML` i bez nove ovisnosti.
  Usput uhvaćen `<code>` čip na 10,24 px → podignut na `text-sm` (12,8 px), kontrast
  **17,23:1**.

🔴 **Tagovi `faza-5-2-ui` i `faza-5-complete` premješteni** na commit s popravkom #65.
Bili su lokalni i nepushani, a „complete" koji isključuje kvar nađen isti dan bio bi
netočna oznaka.

---

# E3 — Boja savjeta (2026-08-13, odluka korisnika nakon taga)

Zahtjev: gumb neka bude „funky", neka se **naglasi kad se otključa**, a kutija savjeta
neka nosi istu boju.

## Izbor huea je bio OSTATAK, ne ukus

Paleta je gusto alocirana, pa je slobodan pojas nađen odbijanjem, ne biranjem:

| pojas | zauzeto |
|---|---|
| 25 / 60 / 150 | verdikti — netočno / djelomično / točno |
| 80 | `accent-warm` — XP, level, streak (MASTER §2.1) |
| 190–260 | mastery gradijent, `tier-easy`, `chart-1/2` |
| 205–355 | `difficulty-*`, `tier-medium/hard`, bazne plohe (280) |

Ostaje **~160–200**. Uzet je **195**: 45° od `correct`, 135° od `partial`, 170° od
`incorrect` — ne može se pročitati kao ocjena.

🔴 **Amber je odbijen unatoč idiomu žarulje.** `accent-warm` (80) već je uz `partial` (60)
predmet ERRATE #13, a savjet stoji **iznad** panela s ocjenom — dvije amber plohe jedna
nad drugom su točno ta zabuna.

🔴 **Adjacencija koja postoji i zašto ne smeta:** `mastery-100` je na 190. Mastery
gradijent se **ne renderira na Task ekranu** — sidebar ondje koristi isključivo
`accent-warm` (provjereno `SidebarCards.tsx`). Zapisano jer je to jedini par koji bi
mogao zasmetati ako se sidebar ikad proširi.

## Naglasak nosi GUMB, ne ploha

| stanje | izgled |
|---|---|
| zaključan | **bez plohe i bez obruba** — samo `muted-foreground` tekst i ikona |
| otključan | `border-hint/45` / `bg-hint-soft` / `text-hint`, žarulja u istoj boji |
| prijelaz | jednokratni **poskok žarulje** + halo oko gumba, 400 ms |

Razlika sada **nosi promjenu dostupnosti**, koju je dotad nosio samo `aria-disabled`. Boja
je pritom **pojačanje, ne jedini kanal** (MASTER §2.2): natpis je nepromijenjen,
`aria-disabled` i vidljivi razlog rade kao prije, a kontrast zaključanog natpisa je
**porastao** (6,92:1 na `card`, prije 5,86:1 na `bg-muted`) — tiši ne znači slabiji.

## Animacija otključavanja

🔴 **Ovo NIJE ono što C.2.2 zabranjuje.** Ondje je zabranjeno animirati **dolazak
savjeta**, jer je idempotentno ponavljanje bajt-identično novom odgovoru pa bi animacija
novosti lagala na svakom ponovljenom kliku. Ovdje se animira **prijelaz nedostupno →
dostupno**, a to je stvarna jednokratna promjena stanja.

🔴 **Okidač je PRIJELAZ, ne vrijednost.** `hintUnlockedRef` se inicijalizira *početnim*
stanjem, pa dolazak na već otključan zadatak ne animira ništa — animira se samo
`false → true` koji se dogodi dok je ekran otvoren. Bez toga bi svaka navigacija ponovila
slavlje za nešto što nije novo, dakle ista laž koju C.2.2 sprječava. **Izmjereno:** reload
već otključanog zadatka → animacija se **ne pojavljuje** (25 uzoraka kroz 1,25 s).

Jednokratno (WCAG 2.2.2), `--duration-slow` (400 ms), **ne** `--duration-reward` — tih
700 ms je rezervirano za `level-pulse`, a savjet nije nagrada. Halo je `box-shadow`, koji
ne ulazi u tok, pa se ništa ne pomiče. Reduced motion: globalni guard.

🔴 Klasa se **skida** nakon animacije (600 ms timeout). Da ostane, `animation` bi se
ponovno pokrenuo na svaki idući re-render koji dira taj čvor.

Ploha savjeta ostaje na disciplini `-soft` obitelji (L 0.24, C 0.04) — savjet je **peer**
panelu s ocjenom i ne smije ga nadglasati. `ErrorState` u grani neuspjeha ostaje
**neutralan**: kvar dohvata nije savjet i ne nosi njegovu boju.

## Izmjereno

- **Geometrija netaknuta** — mijenjaju se boje i `box-shadow`/`transform`, od kojih
  nijedno ne ulazi u tok, pa N-20 gate i dalje prolazi: `action-row` 44 px, `editor-box`
  420 px, red se ne prelama na 768 px.
- **Ikona i dalje 16 px.** Klasa animacije ne smije sadržavati `size-`: base gumb
  stilizira ikonu kroz `[&_svg:not([class*='size-'])]:size-4`, pa bi takvo ime tiho
  ubilo veličinu. Provjereno `getComputedStyle` → `16px×16px` u sva tri stanja.
- **Animacija se ne ponavlja na mount** — v. gore, 25 uzoraka nakon reloada.
- **Kontrast** — sedam parova, sve brojke u §D.5. Najniži je 5,86:1 (zaključan natpis,
  nepromijenjen); otključani natpis je 9,79:1.
- `npm run e2e` 2/2, teardown čist.

## Odstupanje koje ovime nastaje

Plan §C2.1 tražio je neutralni `border-border`/`bg-muted` u **oba** stanja. To više ne
vrijedi za otključano stanje. Odluka je tvoja i zapisana ovdje; zamrznuto je i dalje sve
ostalo — natpis, `aria-disabled`, geometrija, mjesto gumba u redu.

---

# E4 — Admin reset kredita (2026-08-13, odluka korisnika)

`POST /admin/hint-credit/reset` + admin-only gumb uz brojač.

## Zašto reset, a ne „admin bez ograničenja"

Neograničen admin nikad ne može vidjeti `hint_rate_limited`, a to je jedno od sedam
stanja koja rad dokumentira i **demonstrira se upravo na adminu**. Brojač bi mu uz to
uvijek pisao 5, dakle bio bi dekorativan. S resetom limit ostaje stvaran: može se
iscrpiti, pokazati, pa vratiti.

## Zašto smije brisati retke

🔴 **Adminovi `hint_requests` redci nisu telemetrija.** Admin je po dizajnu izvan analize
— `/leaderboard` ga izrijekom isključuje („admin nije natjecatelj"). Studentovi redci
jesu: oni su jedini izvor o potrošnji savjeta i rupama u katalogu.

Zato ruta:

1. **ne prima `user_id`** i briše isključivo retke pozivatelja. Parametar za ciljanog
   korisnika nije propust nego **izostavljen namjerno** — s njim bi jedna kriva vrijednost
   obrisala evaluacijske podatke sudionika. Čuva ga test
   `test_reset_touches_only_the_caller`.
2. briše **samo ono što troši kredit** (`CONSUMING_SOURCES`). `source='unavailable'`
   ostaje — ne troši ništa, a mjeri rupu u katalogu.
3. vraća `remaining`/`next_refill_at` iz `hint_credit`, **iste funkcije** koju zovu
   `/hint` i `/profile` — ne iz pretpostavke „nakon brisanja je puno". Treća
   implementacija istog pravila bila bi mehanizam N-8; čuva ga
   `test_reset_agrees_with_profile`.

Time je izbjegnuta i **migracija**: pravi „reset bez brisanja" tražio bi novu kolonu
(npr. `users.hint_credit_reset_at`), a shema se po CLAUDE.md ne mijenja bez zasebne
odluke. Ako reset ikad zatreba **za studenta**, brisanje više neće biti prihvatljivo i
ta migracija postaje nužna — zapisano ovdje da se ne otkriva ispočetka.

## Izmjereno na živom sustavu

| provjera | rezultat |
|---|---|
| student — gumb u DOM-u | **0** (ne renderira se) |
| student — izravan poziv rute | **403** `admin_required`, nula obrisanih redaka |
| admin — reset | toast „obrisano 5 zapisa", `/profile.remaining` 0 → **5**, `next_refill_at` → `null` |
| N-20 @768 s admin gumbom | red **44 px**, editor **420 px**, bez prelamanja |
| `pytest` | **760 passed, 1 skipped** |
| `make preflight` | zelen |
| `npm run e2e` | 2/2, teardown čist |

🔴 **Skrivanje gumba nije kontrola pristupa.** Gumb se sakriva radi urednosti; kontrola je
`require_admin` na ruti, i to je izmjereno pozivom iz studentove sesije, ne pretpostavljeno.

🔴 **Odstupanje:** gumb je `size="xs"` (24 px), ispod WCAG 2.5.5 praga od 44 px. Svjesno —
`button.tsx` xs/sm izrijekom drži kao escape-hatch za gusti sekundarni UI, a ovo je admin
alat koji student nikad ne renderira, dakle nije dio studentskog puta za koji se AA tvrdi.
Veći gumb narastao bi meta redak. Kartica je na adminovu ekranu viša **+4,8 px** (24 px
gumb umjesto 19,2 px retka teksta); studentov ekran je nepromijenjen, pa matrica iz §D.1
i dalje vrijedi.

🔴 Ovo je bila **eskalacija zamrznutog backenda** (🔒 politika od 4.4-0f) uz izričitu
odluku korisnika, pa su pun `pytest` i `make preflight` odvrćeni kako politika traži.

---

# F — Otvoreno

- **N-21** (`submitted_query` u FIPA logu) — i dalje otvoren, izvan opsega 5.2.
- **`hint_requests` nije u `COUNTED_TABLES`** (`frontend/e2e/db.ts`). Čisti se kaskadno
  (FK `ON DELETE CASCADE` prema `users` i `attempts`) i provjereno je da ne ostaju siročad
  (`0` redaka bez korisnika nakon purgea), ali **nije pokriven before/after dokazom** kao
  ostale tablice. Sitno; jedan redak u `COUNTED_TABLES` ako se želi zatvoriti.
- **Odluka o `Kbd` čipovima** na 768 px — jedini put do nulte promjene visine kartice
  (v. D.1). Nije donesena ovdje jer dira eval-verificirani Run/Submit.
- **ERRATA #64** — kvaliteta savjeta za `row_mismatch`. Traži izmjenu
  `build_hint_payload` (strukturni opis očekivanog rezultata umjesto internog
  `Row 0 differs`), dakle backend i vlastita grana. 🔴 Vrijedi riješiti **prije** nego
  savjeti odu sudionicima: `row_mismatch` je najčešći „skoro točan" ishod i jedini s
  djelomičnim XP-om, pa je to trenutak u kojem savjet najviše znači — a sada ondje
  najmanje vrijedi.
- **Curenje glasa modela** u tekst savjeta („to znači da trebam reći da…") — prompt-level,
  ista grana kao #64.
