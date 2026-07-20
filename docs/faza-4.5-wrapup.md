# Faza 4.5 — Leaderboard + Admin (FIPA agent-log viewer) — WRAP-UP

**Status:** ✅ KOMPLETNA na grani `faza-4-5-leaderboard-admin`, tagovi `faza-4-5a-leaderboard`, `faza-4-5b-admin-guard`, `faza-4-5b-agent-logs`. Bez push-a.
**Obuhvat:** reusabilni `Pagination`, ljestvica (global/weekly), `AdminRoute` role-guard, FIPA agent-log viewer s grupiranjem po `correlation_id`.
**Gates:** `tsc -b` ✓ · `vite build` ✓ · `oxlint` exit 0 (pre-existing fast-refresh warninzi) · `prettier --check` ✓ · `pytest` **485 passed / 1 skipped** · `make preflight` **ZELEN** · `/code-review` (1 nalaz popravljen inline) · `accessibility-review` (izmjereno, prolazi).
**Backend:** NULA izmjena. `git diff main..HEAD` za `backend/`, `schema.d.ts`, `openapi.json` je **PRAZAN** — cijela faza građena protiv zamrznutog ugovora.

---

## 1. Što je isporučeno

| Datoteka | Uloga |
|---|---|
| `components/ui/pagination.tsx` | reusabilna offset paginacija nad `Page<T>` (`{items,total,limit,offset}`) |
| `hooks/useLeaderboard.ts` | ljestvica global/weekly; scope-svjestan `placeholderData` |
| `components/leaderboard/LeaderboardTable.tsx` | tablica ljestvice, isticanje trenutnog usera |
| `pages/LeaderboardPage.tsx` | orkestracija: scope prebacivač, stanja, paginacija |
| `routes/guards.tsx` | **+`AdminRoute`** + `ForbiddenScreen` (403) |
| `hooks/useAgentLogs.ts` | FIPA promet; `MAX_LIMIT` cap; filtri `correlation_id`/`sender` |
| `lib/agent-logs.ts` | grupiranje u tokove, detekcija duplikata, formatiranje |
| `components/admin/AgentFlowCard.tsx` | jedan `correlation_id` tok kao vremenska linija |
| `pages/AdminPage.tsx` | viewer: filtri, cap-disclosure, 4 stanja + 403 |

Dirnuto postojeće: `AttemptHistory` (koristi `Pagination` umjesto inline gumba), `AppShell` (nav „Ljestvica" i „Admin" odstubani), `router.tsx` (+2 lazy rute + `AdminRoute` wrapper), `lib/api/types.ts` (+2 aliasa).

## 2. Zaključane odluke (i zašto)

- **`Pagination` prvi, viewer drugi** — ista komponenta ima tri potrošača (povijest 4.4a, ljestvica, agent-logovi), svi na istom `Page<T>` envelopeu. Regresija povijesti dokazana živo: prije/poslije **identično** (isti tekst „Prikaz X–Y od N", isti disabled stanja, 44px targeti, 63 → 63 fokusabilnih).
- **🔴 `username`, NIKAD email na ljestvici** — email uopće nije u odgovoru (sken KORAK 0: 0 pogodaka).
- **Isticanje usera je KLIJENTSKO preko `username`** — `/leaderboard` ne označava trenutnog usera; `username` je jedino zajedničko polje `/me` × `LeaderboardItem` i ima UNIQUE constraint (`users_username_key`) pa poklapanje ne može pogoditi krivog. Po `id` nije moguće (ljestvica ga ne vraća). **Rang se NE izmišlja** — ako user nije na stranici, diskretna napomena.
- **Weekly prozor: generički tekst** („tekući tjedan, Europe/Zagreb") — granica nije u odgovoru, a klijentski izračunat datum mogao bi promašiti backend definiciju za sat/dan (ista logika kao invarijanta #6).
- **🔴 Guard PRVI, viewer drugi** — jedini ekran sa sigurnosnim elementom u cijelom frontendu.
- **403 ekran, ne tihi redirect** — redirect na `/` skriva da ruta postoji i da korisniku fali ovlast (mentor prijavljen krivim računom vidio bi samo „bačen sam na dashboard"). 403 je iskren, oporavljiv (vodi natrag), razlikuje „nemaš pravo" od „ruta ne postoji". Guard je UNUTAR `AppShell` → nav i odjava ostaju dostupni.
- **Tok, ne JSON dump** — zapisi grupirani po `correlation_id`, sortirani po `id` (NE po `created_at`; timestampi se unutar commita poklapaju).
- **🔴 Duplikati OZNAČENI, ne skriveni** (NALAZ #34) — deduplikacija bi UI učinila urednijim ali bi lagala o zabilježenom prometu, a promet je predmet rada.

## 3. 🔴 Race na hard refreshu — zašto ne postoji

`AdminRoute` čeka `status === "loading"` pa tek onda sudi o roli. To je sigurno **jer je svojstvo `AuthProvider`a**: `setUser(me)` se izvršava **prije** `setStatus("authed")`, pa je `user.role` zajamčeno poznat u trenutku kad status prestane biti `loading`. Admin se ne odbija zbog neučitanog `/me`, student se ne propušta dok se rola ne zna. U kodu stoji upozorenje: promijeni li se taj redoslijed, guard postaje propustan.

Dokazano živo (hard refresh, `waitUntil:networkidle`):

| | rezultat |
|---|---|
| admin → `/admin` | h1 „Administratorski pregled" · bez bijelog ekrana · bez spinnera · 0 pageerrora |
| student → `/admin` | h1 „Nemaš pristup ovom dijelu" · isto |

## 4. 🔴 UI guard NIJE sigurnosna granica

Dokazano oboje (scenarij koji se stvarno dogodi ako guard zakaže):

- **(i)** UI blokira studenta (403 ekran gore).
- **(ii)** guard zaobiđen — token zamijenjen studentskim dok je React state još „admin" → `/admin/agent-logs` vraća **HTTP 403** `{"detail":"admin_required"}`, a ekran to prikazuje kao `role="alert"` poruku, **bez crasha, bez spinnera** (0 pageerrora). Admin token na istoj ruti → 200.

**1d — curenje između sesija:** pravi UI login/logout (ne token injection): admin → `/admin` OK → odjava → student login → nav bez Admin stavke, badge „student", `/admin` → 403 ekran. `queryClient.clear()` na logoutu (4.1c) drži cache čistim.

## 5. FIPA agent-log viewer — artefakt za obranu

Pun ciklus jednog attempta = **12 poruka, svih 6 agenata**, čitljivo u jednom ekranu:

```
request  gateway     → coordinator
request  gateway     → coordinator   [duplikat]
request  coordinator → evaluator
request  coordinator → evaluator
inform   evaluator   → knowledge
inform   evaluator   → gamification
inform   evaluator   → knowledge     [duplikat]
inform   evaluator   → gamification  [duplikat]
inform   knowledge   → coordinator
request  coordinator → recommender
inform   recommender → coordinator
inform   coordinator → gateway
```
= RECEIVE → EVALUATE → UPDATE → RECOMMEND → RESPOND.

- **Duplikati:** 3/12 nose čip „duplikat zabilježenog prometa", **0 sakriveno**. Usporedba po stabilnom potpisu (sortirani ključevi `content`a), pa redoslijed ključeva ne odlučuje što je duplikat.
- **🔴 Cap vidljiv** (NALAZ #36) — backend tiho capira `limit` na 200; UI uvijek ispisuje „Prikazano N od M zapisa", a kad `total > 200` dodaje „Poslužitelj vraća najviše 200 zapisa po zahtjevu — suzi filtrom ili prelistaj". Živo: „Prikazano 50 od 792 zapisa · 8 tokova".
- **Filtri:** samo `correlation_id` + `sender` (ugovor druge nema; **vremenskog filtra nema**, suprotno planu §4.5 — nije izmišljen klijentski). Draft/applied odvojeni (tipkanje ne okida zahtjev po znaku). Filtar cid → „Prikazano 12 od 12 (uz filtar) · 1 tok".
- **Sadržaj:** mono blok `whitespace-pre` + vlastiti `overflow-x` (obrazac 4.3b) → dugačak JSON scrolla u sebi, ne razvlači stranicu.

## 6. Stanja

- **Ljestvica:** loading skeleton · error s retryem · prazna („Ljestvica je još prazna" / „Ovaj tjedan još nema osvojenog XP-a") · „nisi na ovoj stranici" (obje grane dokazane privremenim `PAGE_SIZE=2`).
- **Viewer:** loading skeleton · error s retryem · **dva RAZLIČITA prazna** („Još nema zabilježenog prometa" vs „Nema zapisa za zadani filtar" + Poništi) · **403** (vidi §4).

## 7. A11y — što je izmjereno (2026-07-19, obje teme)

- **Ljestvica:** `<table>` s `<caption>` i `scope="col"`; rang je stupac „Mjesto", ne vizualni redoslijed; trenutni user nosi `aria-current="true"` + ikonu + tekst „(ti)" (ne samo boju). Kontrast vs card: ime 17.18/19.8:1, „(ti)" 9.43/4.78:1, `th` 6.94/4.74:1 — sve ✅.
- **Viewer:** `<ol>` vremenska linija, collapsible sadržaj s `aria-expanded`, labeli filtara vezani `for`→`id` (provjereno). Kontrast vs card — dark: chart-1 6.73, chart-2 8.47, accent-warm-text 9.43, muted-fg 6.94; light: 4.86 / 4.62 / 4.78 / 4.74 — sve ✅. Performativi su KATEGORIJE → chart paleta, nikad correct/incorrect semantika.
- **Fokus-stopova unutar `aria-hidden`: 0** na obje rute (NALAZ #32 čist — tablice ne uvode Recharts-stil rupe). `/leaderboard` 9 fokusabilnih, `/admin` 16.
- Touch targeti ≥ 44px, reflow @720px bez horizontalnog scrolla.

## 8. Bundle

| chunk | veličina | napomena |
|---|---|---|
| `pagination` | 0.99 kB | dijeljen (tri potrošača) |
| `LeaderboardPage` | 4.64 kB | lazy |
| `AdminPage` | 9.05 kB | lazy — nije u studentskom putu |

Glavni bundle je pao (533.86 → ~455 kB) jer je `Card` izdvojen u dijeljeni `card-*.js` (76.47 kB) — **nije ušteda**, zbroj je ~neutralan.

## 9. 🔴 Sigurnost / privatnost

- Sken **svih 552 živih zapisa** `agent_messages_log`: rješenja zadataka (`expected_query`), lozinke, hashevi (`$2b$`), tokeni i e-mailovi **NISU izloženi** — 0 pogodaka. Jedini osjetljiv sadržaj je studentov vlastiti `submitted_query`.
- README dobio 🔴 sekciju: logovi vežu `submitted_query` uz `user_id`/`username` → **obrada osobnih podataka**, traži suglasnost sudionika evala i anonimizaciju u radu. Nije sigurnosni propust, ali jest obveza.

## 10. Ispravci koje je faza iznudila

- **`useLeaderboard` scope-svjestan `placeholderData` (inline review):** goli `keepPreviousData` je pri prebacivanju global↔weekly na trenutak prikazivao brojke jednog razdoblja **ispod naslova drugog** (tiha neistina, ne samo flash). Popravljeno: prethodni podaci se zadrže samo unutar istog scopea. Dokazano: +0ms nakon prebacivanja tablica je prazna (loading), ne stara.
- **KORAK 0 inventar ispravljen:** ranije je tvrdio „Admin nav stavke NEMA" — netočno, postoji role-gated (`AppShell.tsx:65`). Poučak formaliziran kao 🔒 DOC politika u errati (tvrdnja „X ne postoji" traži citat pretrage).

## 11. Errata (dodano u ovoj fazi)

- **#34** — duplikati zabilježenog prometa (3/12 po attemptu) → viewer ih **označava**.
- **#35** — ZPD escape: koncepti s visokim udjelom sekundarnih updatea (`order_by` 88,9%, `select_basic` 90%) „savladaju" se **prije nego ih Prolog ikad ponudi kao primarne** (`order_by`: 21 update, 0 primarnih, P(L)=1.000). Emergentno svojstvo spoja „BKT ažurira sve koncepte" + „Prolog bira ispod praga". Popravak nemoguć bez izmjene ugovora → prijetnja valjanosti mjerenja, prijavljuje se u radu uz #29/#31.
- **#36** — `/admin/agent-logs` tiho capira `limit` na 200; UI to prikazuje.
- **🔒 DOC** — a11y/kontrast tvrdnja nosi izmjerenu brojku i datum; tvrdnja „X ne postoji" nosi citat.

## 12. Za nasljednike / otvoreno

- **`Pagination` je sada dijeljeni primitiv** — svaki novi paginirani prikaz koristi njega, ne inline gumbe. Envelope je uvijek `Page<T>` (`{items,total,limit,offset}`, NEMA page/size).
- **`AdminRoute` ovisi o redoslijedu u `AuthProvider`u** (`setUser` prije `setStatus`) — ne mijenjati taj redoslijed bez re-provjere guarda.
- **Weekly „moj rank" i eval-statistike ne postoje** — envelope nema „my rank" polje, a statistike su izvan opsega (plan §4.5 ih spominje; odbačeno svjesno).
- **NALAZ #17 i dalje otvoren** — verifikacija je i ovdje bila ručna (headless Chrome/CDP iz scratchpada, `playwright-core` NIJE u `package.json`). Nema committed e2e suitea.
- **Sljedeće:** Faza 4.6-eval (backup, export, čisti baseline, runbook) — operativna priprema za evaluaciju. Fazu 4.6 (motion/WS) i 4.7 (visual QA polish) korisnik je **rezao** (runway za eval + pisanje).
