# Faza 4.0 — Backend contract completion — WRAP-UP

**Status:** ✅ KOMPLETNA (4.0a + 4.0b mergeani/spremni). Backend HTTP ugovor je sada finalan i frontend (4.1+) gradi protiv njega bez retrofita.
**Obuhvat:** pod-faze **4.0a** (read endpointi + `/run` + history) i **4.0b** (JWT auth + gate migracija).
**Rezultat suite:** **466 passed / 1 skipped**, 0 regresija (ulaz faze bio 402/1 → 4.0a 436/1 → 4.0b.1 451/1 → 4.0b.2 466/1).
**Grane/PR:** `faza-4a-read-endpoints` (PR #16, mergean) · `faza-4b-auth` (4.0b.1 auth core + 4.0b.2 gate migracija).

Cilj cijele 4.0: dovesti API do ciljne površine iz `faza-4-plan.md` §2 **prije** frontenda, da svaka React komponenta gleda točno ono što ruta vraća (polja/tipovi/null) i da auth bude enforcean od prvog dana.

---

## 1. Što je 4.0a donijela (read endpointi + `/run` + history)

### 1.1 Novi read endpointi (čisti DB read, bez agenata)
| Ruta | Vraća | Namjena za frontend |
|---|---|---|
| `GET /task/{id}` | `{id, title, description, difficulty, estimated_time_sec, module_id, concepts[]}` | Task screen (4.3) — opis zadatka. **NAMJERNO bez `expected_query`/`expected_result`/`sandbox_schema`** (rješenje se ne curi kroz API) |
| `GET /modules` | moduli + koncepti + prereq graf `{code, name, tier, order_index, prerequisites[]}` | Module overview (4.2) + izvor taksonomije za mastery join |
| `GET /badges` | katalog bedževa `{code, name, description, icon, xp_reward}` (**bez `rule`** — Prolog kriterij se ne izlaže) | Badge galerija (4.4) — locked/unlocked |
| `GET /attempts` | povijest pokušaja usera, **paginirano** (`Page[AttemptItem]`) | Profile/povijest (4.4) |
| `GET /mastery-history` | `[{concept, p_l, attempt_id, created_at}]` kronološki | BKT krivulje kroz vrijeme (4.4) |
| `GET /leaderboard` | global + weekly `Page[LeaderboardItem]` | Leaderboard (4.5) |
| `GET /admin/agent-logs` | FIPA-ACL log, paginirano, filter po cid/senderu | Admin panel / eval debugging (4.5) |
| `POST /run` | `{columns, rows, exec_ms, error}` — sandbox exec **bez bodovanja** | Task screen "Run" + sample-data preview (4.3) |

### 1.2 Nova perzistencija — `skill_mastery_history` (D-HIST)
- Nova tablica `skill_mastery_history` (migracija) — snapshot `p_l` po svakom BKT updateu.
- **KM hook:** `agents/knowledge_logic.update_mastery_for_attempt` piše snapshot **atomarno** s mastery upsertom (isti commit). N attempta → N history redova.
- Zašto: `skill_mastery` je current-only upsert → nije imao izvor za "P(L) kroz vrijeme". Snapshot počinje puniti od sada → BKT krivulje imaju podatke za eval.

### 1.3 Ključne garancije uhvaćene u 4.0a
- `/run` ide **čistim exec putom** (reuse `SandboxRunner`, `dml=False` hardkodiran, readonly rola) — NE persistira attempt, NE dira XP/BKT.
- `/task/{id}` **ne izlaže rješenje** (test to eksplicitno asertira nad tijelom odgovora).
- Paginacija (`Page[T]` generički envelope) s clamp-om (limit → [1,100/200], ne 422).
- Leaderboard weekly prozor TZ-aware (Europe/Zagreb, isto kao streak logika).

---

## 2. Što je 4.0b donijela (JWT auth + gate migracija)

### 2.1 Auth infrastruktura (4.0b.1 — aditivno)
- **`app/core/security.py`**: bcrypt hash/verify, JWT mint/decode (python-jose HS256), `get_current_user` / `require_admin` FastAPI dependencyji, `oauth2_scheme`.
- **Rute:** `POST /register` (role **uvijek** forsiran `student`, 409 na duplikat), `POST /login` (OAuth2 form, 401 `invalid_credentials`), `GET /me`.
- **Config:** `JWT_SECRET` (obavezan), `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` (24h za eval sesije) + `ADMIN_*`.
- **`seed_admin`** idempotentan (ON CONFLICT DO NOTHING) — 1 admin za tebe/mentora, kredencijali iz env-a.
- **Test helper:** `conftest.auth_header(user_id, role)` — mint tokena direktno (radi s dummy-hash test userima).

### 2.2 Gate migracija (4.0b.2 — lomni komad)
- **9 ruta auth-gated** (`Depends(get_current_user)`) + **`/admin/agent-logs` admin-guarded** (`require_admin`).
- **5 ruta derivira `user_id` iz tokena** (ne više iz body/query): `/attempt`, `/next-task`, `/profile`, `/attempts`, `/mastery-history`.
- **`AttemptRequest` izgubio `user_id`** — klijent ga više ne bira; `/attempt` ga ubrizgava iz tokena u Coordinator payload.
- **Leaderboard filtriran na `role='student'`** (admin nije natjecatelj; count i rows broje isti skup).
- **Semantička promjena:** "unknown user" je sada **401** (auth greška), ne 404 — jer user dolazi iz tokena.

### 2.3 Enforcement (dokazano testovima)
- Bez tokena → **401** na svih 12 zaštićenih ruta.
- Student na `/admin/agent-logs` → **403**; admin → **200**.
- **Spoof-proof invariant:** token usera A + body koji podvaljuje `user_id: B` → attempt ide za **A** (B ostaje bez ijednog attempta). Klijent ne može lažirati identitet.

---

## 3. Finalna API površina (ugovor za frontend)

Legenda: 🔓 javno · 🔒 traži JWT · 🛡️ admin-only.

| Metoda | Ruta | Auth |
|---|---|---|
| POST | `/register` · `/login` | 🔓 |
| GET | `/me` | 🔒 |
| POST | `/attempt` (token-user) · `/run` | 🔒 |
| GET | `/next-task` · `/profile` · `/attempts` · `/mastery-history` (token-user) | 🔒 |
| GET | `/task/{id}` · `/modules` · `/badges` · `/leaderboard` | 🔒 |
| GET | `/admin/agent-logs` | 🔒🛡️ |

Svih 12 zaštićenih ruta izlaže `security` u OpenAPI shemi → `openapi-typescript` (4.1c) generira contract-safe tipove uključujući auth.

---

## 4. Čemu ovo služi ostalim fazama

- **4.1c (App shell):** typed API klijent iz `/openapi.json` — auth flow (`/register`→`/login`→token→protected) je gotov backend ugovor; `/me` zamjenjuje goli `user_id`.
- **4.2 (Dashboard/Modules):** `/profile` (mastery `concept→p_l`) joina se s `/modules` (taksonomija) klijentski; locked/unlocked iz `prerequisites`.
- **4.3 (Task screen — jezgra):** `/task/{id}` (opis, bez rješenja) + `/run` (Run bez bodovanja) + `/attempt` (Submit, token-user, pun feedback). Sve što petlja "dohvati→piši→Run/Submit→feedback→next" treba.
- **4.4 (Profile/Stats):** `/badges`×`/profile` (galerija), `/attempts` (povijest), `/mastery-history` (BKT krivulje — izvor puni se od 4.0a nadalje, ključno za eval).
- **4.5 (Leaderboard/Admin):** `/leaderboard` (student-filtriran), `/admin/agent-logs` (correlation_id flow za eval debugging teze).
- **Eval (Faza 6):** auth razlučuje studente; `skill_mastery_history` daje podatke za BKT analizu; admin panel za nadzor agent-komunikacije.

---

## 5. Zaključane odluke / napomene za nasljednike

- **Hashing kroz `bcrypt` izravno, NE passlib** — `spade→pyjabber` tvrdi `bcrypt>=4.3`, a passlib 1.7.4 je nekompatibilan (napušten 2020.). Isti API (`hash_password`/`verify_password`), 72-bajtni truncate.
- **`EmailStr`** (`pydantic[email]`) na `/register` — contract-correct format u OpenAPI-ju.
- **404→401 semantika** namjerna za token-derived rute (unknown user = auth greška).
- **Leaderboard = samo studenti** — dizajn odluka (admin nije natjecatelj), ujedno rješava fragilnost total-count testa bez patcha.
- **`.env`** sadrži `JWT_SECRET` + `ADMIN_*` (gitignored); `.env.example` ima `change-me-in-prod` placeholdere.

### Otvoreni dug koji i dalje dira frontend (errata-trail, nepromijenjen)
| # | Stavka | Utjecaj |
|---|---|---|
| ERRATA #8 | `attempts` nema `verdict` kolonu | Partial se NE razlučuje u UI (4.3) — samo correct/incorrect |
| flag #3 | `new_badges` best-effort | Badge-unlock je kozmetika; autoritativno iz `/profile` (4.3/4.4) |
| flag #5 | F2 mentor-pending XP konstante | Ne blokira frontend; **pingaj mentora paralelno** |
| NALAZ #7 | `task.module_id ≠ primary_concept.module` (3/83) | Module overview mapiranje (4.2) — data cleanup Faza 6 |
| pre-existing lint | `test_api.py` 7 ruff grešaka (postoje na `main`) | Nije regres; čeka zaseban lint-hardening |

---

## 6. Sljedeće na redu

**Faza 4.1 — Frontend foundation:**
1. **4.1a — Tooling & scaffold:** `frontend/` (Vite+React+TS), Tailwind, shadcn init, ESLint+Prettier, Makefile/README run-targeti (backend+frontend jednom komandom).
2. **4.1b — Design system & tokeni:** `ui-ux-pro-max --design-system` → `design-system/MASTER.md` (SSOT za tokene), CSS varijable + Tailwind theme, custom Monaco tema, motion tokeni, token-preview stranica.
3. **4.1c — App shell & infra:** routing + layout, **typed API klijent iz `/openapi.json`**, TanStack Query, auth context (token storage), protected routes, login/register stranice, state-primitivi.

**Paralelno (ne blokira):** ping mentoru za F2 XP konstante (flag #5).

> Redoslijed drži funkcionalnu jezgru (4.0–4.4) eval-upotrebljivom prije 4.5–4.7 polisha. Backend ugovor je zaključan — frontend od sada ne mijenja rute, samo ih konzumira.
