# Faza 4.5 — KORAK 0: READ-ONLY inventar (Leaderboard + Admin)

**Nula izmjena koda.** Sve tvrdnje su iz `schema.d.ts` (citat) ili živog probea (sirovi JSON).
Snimljeno: 2026-07-19, backend 🔒 ZAMRZNUT.

---

## 2a. `/leaderboard`

### Oblik (doslovno iz `schema.d.ts`)
```ts
LeaderboardItem: { rank: number; username: string; xp: number; level: number }
Page_LeaderboardItem_: { items: LeaderboardItem[]; total: number; limit: number; offset: number }
```
> `@description`: „`xp` je score za dani scope (global = User.xp, weekly = SUM(delta) u prozoru). `level` je uvijek trenutni User.level."

**Nullability:** nijedno polje nije nullable. **Query:** `scope?: "global" | "weekly"` (default `global`), `limit?`, `offset?` — paginacija je offset-based, isti `Page` envelope kao `/attempts`.

### Živi probe (demo user)
```json
// GET /leaderboard?scope=global&limit=3
{"items":[{"rank":1,"username":"demo44_student","xp":700,"level":8}],"total":1,"limit":3,"offset":0}
// GET /leaderboard?scope=weekly&limit=3
{"items":[{"rank":1,"username":"demo44_student","xp":700,"level":8}],"total":1,"limit":3,"offset":0}
```

### ✅ `display_name` — NEMA GA, i to je DOBRA vijest
Polje se zove **`username`**, ne `display_name`, i **NIJE email**. Živo potvrđeno: `"demo44_student"` (email tog usera je `demo44_student@mailinator.com` i **ne pojavljuje se u odgovoru**). Skeniranje cijelog odgovora na `@` i `email` → 0 pogodaka.
**Verdikt: nema izlaganja osobnog podatka.** Ostaje odluka za 4.5: username je pri registraciji slobodan unos, pa se studente na evalu treba uputiti da ne upisuju puno ime ako to nije željeno — to je *organizacijska*, ne tehnička mjera.

### Trenutni user NIJE označen u odgovoru
Nema `is_current_user` ni `me` polja → **isticanje se mora poklopiti klijentski** preko `/me.username`. Napomena za 4.5: ako user nije u dohvaćenoj stranici, njegov rank se **ne može** izvesti iz `Page` envelope (nema „my rank" polja) — ili se lista prelistava, ili se prihvaća da isticanje radi samo na vidljivoj stranici.

### Weekly prozor
`routes.py:614` — `_read_leaderboard_weekly`: „Score = SUM(xp_log.delta) u zadnjih 7 dana; cutoff TZ-aware (Europe/Zagreb)" (`_ZAGREB = ZoneInfo("Europe/Zagreb")`, `routes.py:82`).
🔴 **Granica prozora se NE vidi u odgovoru** — nema `window_start`/`window_end`. UI ne može prikazati „od kada" bez hardkodiranja pravila (što bi prekršilo invarijantu #6). Za 4.5: ili se piše generički tekst („zadnjih 7 dana"), ili je to jedini kandidat za contract dodatak — a backend je zamrznut, pa **preporuka: generički tekst**.

---

## 2b. `/admin/agent-logs`

### Oblik (doslovno)
```ts
AgentLogItem: {
  id: number; sender: string; receiver: string; performative: string;
  content: { [key: string]: unknown } | null;
  correlation_id: string | null; created_at: string /* date-time */;
}
Page_AgentLogItem_: { items: AgentLogItem[]; total: number; limit: number; offset: number }
```
**Query parametri:** `correlation_id?`, `sender?`, `limit?`, `offset?`.
🔴 **NEMA filtera po vremenu ni po receiveru ni po performativu** — plan 4.5 spominje „filter po cid/agentu/vremenu"; **vremenski filter ne postoji** i backend je zamrznut → 4.5 radi s onim što ima.
⚠️ **`limit` je server-side capiran na 200** (zatraženo `limit=1000` → vraćeno 200 uz `total=552`). Paginacija je obavezna.

### Živi probe — ADMIN (2 zapisa doslovno)
```json
{"id":576,"sender":"recommender@localhost","receiver":"gateway@localhost","performative":"inform",
 "content":{"reason":"partial_continuation","concept":"select_basic","task_id":15,"user_id":1},
 "correlation_id":"7cc3d18c-383b-4a95-be92-7fbde0b9b127","created_at":"2026-07-19T15:17:15.753032Z"}
{"id":575,"sender":"gateway@localhost","receiver":"recommender@localhost","performative":"request",
 "content":{"user_id":1},
 "correlation_id":"7cc3d18c-383b-4a95-be92-7fbde0b9b127","created_at":"2026-07-19T15:17:15.725637Z"}
```
**Živi probe — STUDENT:** `HTTP 403` ✅ (guard radi na backendu, ne samo u UI-ju).

**Sadržaj:** `performative` ∈ {`inform` (305), `request` (247)} — FIPA performativ **jest** prisutan. `correlation_id`, `sender`, `receiver`, `created_at` svi prisutni. `content` je **pravi JSON objekt** (dict), ne string → UI ga može formatirati bez parsiranja.
**Senderi:** `coordinator@`, `evaluator@`, `gateway@`, `gwprobe@`, `knowledge@`, `recommender@`.

### 🔴 SIGURNOSNI VERDIKT — ČISTO
Sken nad **svih 552 živih zapisa** (ne iz koda):

| obrazac | pogodaka |
|---|---|
| `expected_query`, `expected_result`, `expected_output`, `expected_rows`, `first_mismatch` | **0** ✅ |
| `password`, `hashed_password`, `$2b$` | **0** ✅ |
| `access_token`, `secret` | **0** ✅ |
| `email` | **0** ✅ |

Puni popis ključeva ikad viđenih u `content`: `attempt_id, code, concept, concepts, correlation_id, current_streak, detail, error, error_type, execution_time_ms, feedback, gamification, is_correct, is_primary, level, new_badges, primary_concept, query, reason, recommendation, submitted_query, task_id, updated_concepts, user_id, verdict, xp, xp_delta`.

Jedini osjetljiviji sadržaj je **`submitted_query` — studentov VLASTITI upit** (55 zapisa), što je za admin/mentora legitimno i nužno za debugging. **Rješenja zadataka NISU izložena** — `expected_query` nikad ne ulazi u FIPA poruke (poklapa se s guardom iz 4.3 Stage 0b).

### Pun `correlation_id` tok — rekonstruktibilan ✅
Filter `?correlation_id=…` radi (`total=12`). Jedan attempt = **12 zapisa**:
```
gateway     → coordinator  [request] {submitted_query, task_id, user_id}
gateway     → coordinator  [request] {submitted_query, task_id, user_id}      🔁 identičan duplikat
coordinator → evaluator    [request] {task_id, user_id}
coordinator → evaluator    [request] {submitted_query, task_id, user_id}
evaluator   → knowledge    [inform]  {verdict, concepts[], primary_concept, is_correct, …}
evaluator   → gamification [inform]  {verdict, concepts[], primary_concept, is_correct, …}
evaluator   → knowledge    [inform]  {…}                                       🔁 identičan duplikat
evaluator   → gamification [inform]  {…}                                       🔁 identičan duplikat
knowledge   → coordinator  [inform]  {attempt_id, updated_concepts[]}
coordinator → recommender  [request] {user_id}
recommender → coordinator  [inform]  {reason, concept, task_id, user_id}
coordinator → gateway      [inform]  {feedback, gamification, recommendation, correlation_id}
```
Tok RECEIVE→EVALUATE→UPDATE→RECOMMEND→RESPOND je **potpuno vidljiv** — to je ona vrijednost za tezu.

🔴 **NALAZ #34 — 3 od 12 zapisa su BYTE-IDENTIČNI DUPLIKATI** (ids 560, 565, 566 u snimljenom toku): isti sender/receiver/performative/content. Uz to su `coordinator→evaluator` dva zapisa s RAZLIČITIM payloadom (jedan bez `submitted_query`). **Za 4.5:** log viewer koji ih prikaže sirovo izgledat će kao da sustav šalje duplo. Preporuka: viewer grupira po `correlation_id` i **vizualno označi duplikate**, ne da ih tiho briše (skrivanje bi lagalo o tome što se stvarno dogodilo). Uzrok je u zamrznutom backendu → ne dira se.

**Volumen za eval:** 12 zapisa/attempt (od toga 9 jedinstvenih). 30 studenata × 20 attempta ≈ **7 200 zapisa** — trivijalno za paginirani viewer.

---

## 2c. 🔴 ANALIZA ZA RAD — koliko KC-ova mjerimo SEKUNDARNO (NALAZ #31 × #29)

### A) Strukturno (task bank, svih 30 koncepata)
Ako student jednom riješi svaki aktivni zadatak, svaki koncept dobije `prim + sec` BKT updatea:

| koncept | modul | primarnih | sekundarnih | ukupno | **% sekundarnih** |
|---|---|---|---|---|---|
| `column_alias` | 0 | 0 | 4 | 4 | **100.0 %** |
| `select_basic` | 1 | 2 | 18 | 20 | **90.0 %** |
| `order_by` | 1 | 2 | 16 | 18 | **88.9 %** |
| `where_filter` | 1 | 3 | 19 | 22 | **86.4 %** |
| `group_by` | 2 | 5 | 16 | 21 | **76.2 %** |
| `limit_offset` | 1 | 3 | 7 | 10 | 70.0 % |
| `null_handling` | 0 | 4 | 8 | 12 | 66.7 % |
| `agg_count` | 2 | 4 | 7 | 11 | 63.6 % |
| `agg_sum_avg` | 2 | 3 | 5 | 8 | 62.5 % |
| `inner_join` | 3 | 4 | 6 | 10 | 60.0 % |
| `from_clause` | 1 | 3 | 4 | 7 | 57.1 % |
| `correlated_subquery` | 5 | 3 | 2 | 5 | 40.0 % |
| `left_join` | 3 | 3 | 2 | 5 | 40.0 % |
| `distinct` | 1 | 2 | 1 | 3 | 33.3 % |
| `scalar_subquery` | 5 | 2 | 1 | 3 | 33.3 % |
| `multi_table_join` | 3 | 5 | 2 | 7 | 28.6 % |
| `agg_min_max`, `cross_join`, `delete`, `exists_subquery`, `full_outer_join`, `having_filter`, `insert`, `in_subquery`, `right_join`, `self_join`, `update` | 2–5 | 2–4 | 0 | 2–4 | 0.0 % |
| `explain_plan`, `index_usage`, `join_condition` | 6/0 | 0 | 0 | 0 | — (nema procjene) |

### B) Empirijski (demo user, 28 attempta — 15 koncepata s poviješću)
| koncept | kao primarni | kao sekundarni | % sekundarnih |
|---|---|---|---|
| `order_by` | **0** | **21** | **100 %** |
| `select_basic` | **0** | 12 | **100 %** |
| `group_by` | **0** | 9 | **100 %** |
| `where_filter` | **0** | 3 | **100 %** |
| `limit_offset` | **0** | 3 | **100 %** |
| `column_alias` | **0** | 1 | **100 %** |
| `correlated_subquery` | 1 | 2 | 66.7 % |
| ostalih 8 (`distinct`, `full_outer_join`, `agg_min_max`, `cross_join`, `agg_count`, `scalar_subquery`, `exists_subquery`, `inner_join`) | 1–10 | 0 | 0 % |

### PRESUDA
- **Strukturno: 5 od 27 procjenjivih KC-ova (18,5 %) dobiva PRETEŽNO (>70 %) sekundarnu procjenu** — poimence: **`column_alias` (100 %), `select_basic` (90 %), `order_by` (88,9 %), `where_filter` (86,4 %), `group_by` (76,2 %)**. `limit_offset` je granični slučaj (točno 70,0 %).
- **ISKLJUČIVO sekundarno (100 %): `column_alias`** — jedini KC koji strukturno nikad ne može biti mjeren kao primarni.
- **Empirijski je gore: 6 KC-ova ima 100 % sekundarnu procjenu**, uključujući `order_by` s **21 updateom i nijednim kao primarni**. Taj student na Profilu vidi `order_by` P(L) = 1.000 („savladano") — procjenu izvedenu isključivo iz zadataka kojima ORDER BY **nije bio ciljna vještina**.

**Zašto je to prijetnja valjanosti (za poglavlje o mjerenju):** spoj s **NALAZ #29** (evaluator uspoređuje SKUP REDAKA, ne strukturu upita) znači da student može dobiti pun BKT kredit za KC koji (a) nije bio cilj zadatka i (b) nije nužno ni upotrijebljen u rješenju. Za KC-ove iz gornje liste tvrdnja „model je izmjerio savladanost X" oslanja se na pretpostavku da je student, rješavajući nešto drugo, doista koristio X — a rezultat-bazirana evaluacija tu pretpostavku ne provjerava.

**Preporuka za rad (ne za kod):** u analizi razdvojiti KC-ove po izvoru procjene (primarno vs pretežno sekundarno) i tvrdnje o savladanosti za drugu skupinu iznositi uz ogradu. **Ništa se ne popravlja** — zadaci i backend su zamrznuti; ovo je mjerenje, ne defekt.

---

## 2d. Frontend nasljeđe za 4.5

### Nav stubovi — POSTOJE
`components/layout/AppShell.tsx`:
```ts
// (Zadatak/Ljestvica) vode na "/" dok 4.5 ne donese ekrane — `stub: true` im
// GASI active stanje (inače bi na "/" bile istovremeno "aktivne").
const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, to: "/",        stub: false },
  { label: "Moduli",    icon: BookOpen,        to: "/modules", stub: false },
  { label: "Zadatak",   icon: Terminal,        to: "/",        stub: true  },
  { label: "Profil",    icon: User,            to: "/profile", stub: false },
  { label: "Ljestvica", icon: Trophy,          to: "/",        stub: true  },
] as const
```
→ **„Ljestvica" stub već postoji** (samo se prebaci `to: "/leaderboard"`, `stub: false`). Invarijanta #3: `h-11` = 44px touch target po stavci.

> ⚠️ **ISPRAVAK (4.5a):** ranija verzija ovog dokumenta tvrdila je „Admin stavke NEMA".
> **Netočno** — `SidebarNav` već ima role-gated Admin stavku:
> ```tsx
> {user?.role === "admin" && (
>   <NavLink to="/" end …><ShieldCheck …/>Admin</NavLink>
> )}
> ```
> Stavka je **stub** (`to="/"`), ali uvjetovanje po roli **postoji i radi**. Za 4.5b
> preostaje samo prebaciti `to` na `/admin` — ne graditi role-gating ispočetka.
> (Poučak iz #33: tvrdnja u dokumentaciji nosi citat ili se ne piše.)

### Role-guard — 🔴 **NE POSTOJI**
`routes/guards.tsx` ima **samo** `ProtectedRoute` (auth status) i `PublicOnlyRoute`. Nema `AdminRoute`, nema provjere role nigdje u routeru. `MeResponse` **ima** `role: string` (`schema.d.ts:463`) i `useAuth().user` ga nosi → materijal postoji, guard treba **napisati** u 4.5.
Backend guard je potvrđen živo (403 studentu), pa je UI guard stvar UX-a, ne sigurnosti.

### Reusabilne 4.4 komponente
- **Paginacija:** `AttemptHistory` ima gotov obrazac — `PAGE_SIZE = 20`, `offset` state, `hasPrev/hasNext` iz `total`, „Prethodna/Sljedeća" gumbi, „Prikaz X–Y od N". Isti `Page{items,total,limit,offset}` envelope vraćaju **i `/leaderboard` i `/admin/agent-logs`** → obrazac se prenosi 1:1. **Kandidat za ekstrakciju u `components/ui/Pagination.tsx`** (tada tri potrošača).
- **Stanja:** `components/state/{Loading,Empty,Error}State` — već univerzalni.
- **`useAttempts`** je predložak za `useLeaderboard`/`useAgentLogs` (isti `unwrap` + `Page` oblik).
- **`verdict-ui.ts` / `badge-icons.ts`** — nisu relevantni za 4.5.
- **⚠️ NE reusati `AttemptRow`** — vezan je na `AttemptItem` i verdict semantiku.

---

## PRIJEDLOG STAGINGA 4.5

**4.5a — Leaderboard (student-facing, nizak rizik)**
Ekstrakcija `Pagination` iz `AttemptHistory` → `useLeaderboard` → `/leaderboard` ruta + odstubanje nav stavke → global/weekly prebacivač → isticanje trenutnog usera preko `/me.username` (uz svjesno ograničenje: samo na vidljivoj stranici). Weekly prozor opisati generički („zadnjih 7 dana") jer granica nije u odgovoru.

**4.5b — Admin (role-guarded, veći rizik)**
Prvo `AdminRoute` guard + uvjetna nav stavka (role iz `/me`), pa `useAgentLogs` s filterima koji **stvarno postoje** (`correlation_id`, `sender`) — bez vremenskog filtera. Viewer grupira po `correlation_id` i prikazuje tok kao vremensku liniju s FIPA performativima; **duplikati se označavaju, ne skrivaju** (NALAZ #34). Paginacija obavezna (cap 200).

**Redoslijed je namjeran:** 4.5a ekstrahira `Pagination` koji 4.5b odmah koristi, a 4.5b nosi jedini novi sigurnosni element (role guard).
