# Runbook za evaluacijski dan

**Namjena:** slijediti korak po korak, pod stresom, bez razmišljanja o implementaciji.
Sve brojke u ovom dokumentu su **izmjerene 2026-07-20**, ne procijenjene.

> 🔴 **JEDNO PRAVILO IZNAD SVIH:** evaluacijski podaci nastaju jednom i
> **nenadoknadivi su** (NALAZ #37). Ako nešto pođe po zlu — **prvo backup, pa
> onda razmišljanje**. Nijedan kvar nije toliko hitan da opravda brisanje.

---

## 0. Zabranjeno tijekom evala

| ❌ NE POKREĆI | zašto |
|---|---|
| `docker compose down -v` | briše volumene = SVE attempte, BKT povijest, XP. Nepovratno |
| `make dev-reset` | isto (to je jedini target koji poziva `down -v`) |
| `uv run python -m scripts.prepare_eval_baseline --confirm` | briše usere i njihove podatke |
| `uv run python -m scripts.purge_demo_users` | briše sve `demo44_` usere |
| `uv run python -m scripts.seed_demo_user` | interno zove purge `demo44_` usera |
| `make db-seed` / `make db-tasks` tijekom sesije | sigurni su za podatke (vidi §7), ali nemaju svrhu usred sesije |
| 🔴 `pytest` (bilo koji test) | **testovi pišu u ŽIVU `tutor_main`** — nemaju zasebnu bazu (NALAZ #40). Ubacili bi lažni FIPA promet među podatke sudionika |

✅ **Sigurno tijekom evala:** `make backup`, `make preflight`, `make sweep`,
`make smoke`, čitanje admin sučelja, restart backenda.

---

## 1. PRIJE sesije (T-30 min)

```bash
cd ~/projects/diplomski-sql-tutor

# 1. Podigni sve (ako još ne vrti)
make infra-up && make wait-db
make db-migrate && make db-seed && make db-tasks
make sandbox-seed-if-empty && make register-agents

# 2. Backend + frontend (u dva odvojena terminala, da ih vidiš odvojeno)
make backend      # terminal A
make frontend     # terminal B

# 3. 🔴 GATE — mora biti ZELEN
make preflight

# 4. Provjeri baseline (dry-run, ništa ne briše)
cd backend && uv run python -m scripts.prepare_eval_baseline
```

**Očekivano baseline stanje:**

```
useri: 1 (admina: 1) · attempti: 0 · BKT: 0 · XP: 0 · zadataka: 85 (aktivnih: 80) · koncepata: 30
```

Ako baseline **nije** čist, očisti ga (ovo je jedini trenutak kad je brisanje dopušteno):

```bash
uv run python -m scripts.prepare_eval_baseline            # pogledaj plan
uv run python -m scripts.prepare_eval_baseline --confirm  # pa izvrši
make preflight                                            # i opet gate
```

### Izmjereno vrijeme podizanja od nule

Puni `down -v` → spreman sustav, **2026-07-20, topli docker imageovi**:

| korak | vrijeme |
|---|---|
| `infra-up` | 1 s |
| `wait-db` | 3 s |
| `db-migrate` | 1 s |
| `db-seed` | 1 s |
| `db-tasks` (85 zadataka) | 1 s |
| `sandbox-seed-if-empty` (Faker, 4 898 redaka) | 1 s |
| `register-agents` (5 SPADE agenata) | 1 s |
| `sweep` (80/80) | < 1 s |
| **infra ukupno** | **9 s** |
| backend startup (SPADE agenti se spajaju na Prosody) | ~18 s |
| `preflight` | 4 s |
| **UKUPNO do spremnog sustava** | **≈ 31 s** |

⚠️ Vrijedi uz **već povučene docker imageove**. Prvo povlačenje `postgres:16` i
`prosody/prosody` na sporoj mreži traje višestruko dulje — ne oslanjaj se na
ovu brojku ako je stroj svjež.

### 🔴 Očekivano stanje `agent_messages_log` na početku sesije

Baseline isprazni tablicu (`TRUNCATE`), ali `make preflight` **poslije njega** napravi
jedan pravi attempt kroz živi lanac i ostavi njegov trag. **Izmjereno 2026-07-21**, nakon
punog slijeda `pytest` → `baseline --confirm` → `preflight`:

```
redaka: 12 · korelacijskih tokova: 1 · bez correlation_id: 0 · attempts: 0
```

**`agent_messages_log` sadrži ~12 redaka iz preflight smoke testa; u analizi se
filtriraju kao orphan `correlation_id` (nema pripadajući attempt).**

Provjereno da je taj tok stvarno orphan — smoke obriše svog usera i attempt, a log ostaje:

| correlation_id | redaka | s `attempt_id` | attempt_id | postoji u `attempts` | status |
|---|---|---|---|---|---|
| `de134da2-…` | 12 | 5 | 111 | **ne** | **ORPHAN** |

⚠️ **Orphan se mora računati po TOKU, ne po retku.** Samo **5 od 12** poruka uopće nosi
`attempt_id` (`evaluator→knowledge` i `evaluator→gamification`); `gateway→coordinator` i
`coordinator→evaluator` prethode stvaranju attempta pa ga nemaju. Filtriranje redak-po-redak
ostavilo bi 7 poruka neklasificiranih.

```sql
-- Orphan tokovi: nijedna poruka toka ne pokazuje na postojeći attempt
WITH tok AS (
  SELECT correlation_id, count(*) AS redaka,
         min((content->>'attempt_id')::int) AS attempt_id
  FROM agent_messages_log GROUP BY correlation_id
)
SELECT t.*, (a.id IS NOT NULL) AS vezan
FROM tok t LEFT JOIN attempts a ON a.id = t.attempt_id;
```

### 🔴 Zamka: recikliranje `attempts.id` nakon `dev-reset`

Orphan test se oslanja na `attempt_id`, a smoke ostavlja trag koji pokazuje na **obrisani**
attempt. Unutar iste instalacije to je sigurno: baseline briše attempte s `DELETE` (ne
`TRUNCATE`), pa se `attempts_id_seq` **nikad ne resetira** — provjereno, stoji na 111 uz 0
redaka. Jedina tablica koja se resetira je `agent_messages_log` (`RESTART IDENTITY`).

**Ali nakon `make dev-reset` baza nastaje iznova i sekvenca kreće od 1.** Tada smoke dobije
`attempt_id = 1`, obriše ga, a **prvi stvarni studentski attempt također dobije `id = 1`** →
orphan smoke tok bi se lažno prikazao kao „vezan" uz podatke stvarnog sudionika.

**Zato: odmah nakon `preflight`, a PRIJE dolaska sudionika, zabilježi smoke `correlation_id`:**

```bash
docker compose exec -T postgres-main psql -U tutor -d tutor_main -tAc \
  "SELECT DISTINCT correlation_id FROM agent_messages_log;" | tee docs/eval-smoke-cid.txt
```

U analizi taj `correlation_id` isključi **imenom**, ne heuristikom:

```sql
SELECT * FROM agent_messages_log WHERE correlation_id <> '<zabilježeni-cid>';
```

Provjereno: isključenje po zabilježenom cid-u daje **0 preostalih redaka** na čistom
baselineu. Ovaj je postupak imun na recikliranje ID-a; `attempt_id` heuristika nije.

### Zadnja provjera prije dolaska sudionika

- [ ] `make preflight` **ZELEN** (80/80 sweep + živi smoke)
- [ ] baseline čist (attempti = 0)
- [ ] smoke `correlation_id` zabilježen u `docs/eval-smoke-cid.txt` (vidi gore)
- [ ] `make backup` napravljen i **kopiran na drugi medij**
- [ ] frontend dostupan na `http://localhost:5173`, prijava admina radi
- [ ] admin sučelje `/admin` se otvara i prikazuje promet

---

## 2. Registracija sudionika

**Način:** sudionici se registriraju sami kroz `/register` u aplikaciji
(alternativa je unaprijed pripremiti račune istim putem — endpoint je isti).

### 🔴 Konvencija koja NE otkriva identitet

| polje | format | primjer |
|---|---|---|
| username | `S` + dvoznamenkasti broj | `S01`, `S02`, … `S20` |
| email | `<username u malim slovima>@example.com` | `s01@example.com` |
| lozinka | zajednička, zapisana offline | npr. `Eval2026!sql` |

**Zašto baš tako — oboje je testirano uživo (2026-07-20):**

1. 🔴 **`@eval.local` NE RADI.** Vraća `422 value is not a valid email address`
   — `EmailStr` (pydantic + `email-validator`) odbija `.local` kao special-use
   domenu. `@example.com` je testiran i vraća **200**. Ne improviziraj domenu na
   licu mjesta.
2. 🔴 **Prefiks `S` je siguran od skripti za čišćenje.** Sentinel prefiksi koje
   `prepare_eval_baseline` briše su `demo44_`, `rival_`, `test_`, `e2e_`,
   `smoke_`. Račun `S99` je u testu ispravno prijavljen kao **NEPOZNAT i NIJE
   obrisan** — za brisanje ga je trebalo imenovati (`--also-user S99`).
   **NIKAD ne dodjeljuj sudioniku username koji počinje sentinel prefiksom.**

Mapu `S01 → stvarno ime` drži **na papiru ili u datoteci izvan repozitorija**.
Ona nije potrebna za analizu — export je pseudonimizira u `P01`, `P02`, …

---

## 3. TIJEKOM sesije

### Što nadzirati

- **`/admin`** (admin račun) — FIPA promet po `correlation_id`.
  Zdrav attempt = **12 poruka, svih 6 agenata**, tok
  RECEIVE → EVALUATE → UPDATE → RECOMMEND → RESPOND.
- 3 od 12 poruka nose čip **„duplikat zabilježenog prometa"** — to je **očekivano**
  (NALAZ #34), nije kvar.
- **Cap od 200 zapisa** (NALAZ #36): viewer uvijek piše „Prikazano N od M".
  Kad `M > 200`, **filtar po `correlation_id` je jedini upotrebljiv ulaz** — ne
  pokušavaj prelistati sve.
- Terminal backenda — traži `ERROR` / `504`.

### Ako student prijavi da „ne radi"

| simptom | značenje | postupak |
|---|---|---|
| vrti se, pa greška nakon ~15 s | `GATEWAY_TIMEOUT = 15 s` → HTTP 504 `orchestration_timeout` | neka **osvježi stranicu** i pogleda povijest prije ponovnog slanja — vidi upozorenje ispod |
| „odjavljen sam" | JWT traje **1440 min (24 h)** — ne bi se smjelo dogoditi unutar sesije | neka se ponovno prijavi; podaci su u bazi |
| 403 na `/admin` | student, ne admin | očekivano |

> ⚠️ **504 NE znači da pokušaj nije zabilježen.** `/attempt` je sinkron, ali
> evaluator perzistira pokušaj *prije* nego coordinator odgovori — ako istekne
> prozor od 15 s, redak u `attempts` može već postojati. Zato: **osvježi i
> provjeri povijest, pa tek onda šalji ponovno**, inače nastaje dvostruki
> pokušaj koji kvari brojke.

---

## 4. POSLIJE svake sesije

```bash
# 1. 🔴 BACKUP — prvo ovo, prije bilo čega drugog
make backup
```

Skripta sama provjeri da je dump **restore-abilan** (restore u privremenu bazu →
usporedba broja redaka i agregata → drop). Ako padne, **NE nastavljaj** — javi.

```bash
# 2. Kopiraj na DRUGI medij (obavezno!)
cp backups/tutor_main_*.sql.gz /mnt/c/Users/<ti>/OneDrive/diplomski-backups/

# 3. Provjeri da je kopija stvarno tamo i da nije 0 bajta
ls -la /mnt/c/Users/<ti>/OneDrive/diplomski-backups/
```

🔴 **Laptop je jedna točka kvara.** Backup koji leži samo na istom disku ne štiti
od kvara diska. `backups/` je u `.gitignore` — git ga **ne** čuva.

```bash
# 4. Export za analizu (pseudonimizirano)
cd backend && uv run python -m scripts.export_eval_data
```

Izlaz ide u `exports/eval_<timestamp>/`. Skripta sama provjeri da nijedan CSV ne
sadrži username ni email i **odbije export** ako sadrži.

🔴 `_pseudonym_map.csv` je jedina datoteka s identitetom — **ne commitati, ne
prilagati radu**, čuvati odvojeno od ostalih CSV-ova.

---

## 5. Oporavak — što ako backend padne usred sesije

**Podaci su sigurni.** Razlog, konkretno:

- `/attempt` je **sinkron** — student čeka odgovor, a pokušaj se perzistira u
  PostgreSQL unutar tog zahtjeva.
- Podaci žive u **docker volumenu** `pg_main_data`, ne u procesu backenda.
  Pad uvicorna, zatvaranje terminala i restart stroja **ne diraju bazu**.

**Postupak:**

```bash
# 1. Digni backend ponovno
make backend

# 2. Provjeri da je živi put zdrav
make smoke

# 3. Provjeri da su podaci tu
docker compose exec -T postgres-main psql -U tutor -d tutor_main \
  -c "SELECT count(*) FROM attempts;"
```

Studenti se **ponovno prijave i nastavljaju** — token traje 24 h, pa ga većina
neće ni morati obnavljati. Izgubljen je najviše **jedan pokušaj u letu**
(onaj koji je bio usred obrade u trenutku pada).

**Ako ne pomogne — redoslijed eskalacije:**

1. `docker compose ps` — vrte li sve tri usluge?
2. `docker compose restart prosody` pa restart backenda (SPADE agenti se spajaju
   na Prosody **na startupu**; ako je Prosody pao, agenti se ne mogu spojiti).
3. `make register-agents` — ako je Prosody volume izgubljen, računi agenata
   moraju se ponovno registrirati (NALAZ #26).
4. `make preflight` — potvrda da je sve opet zdravo.
5. **NIKAD `down -v`.**

---

## 6. Poznata ponašanja koja NISU kvarovi

| pojava | objašnjenje |
|---|---|
| Nakon `make preflight` u logovima ostane **12 FIPA zapisa** | smoke test radi jedan pravi attempt; briše svog usera i njegove attempte, ali `agent_messages_log` **nema `user_id`** pa ostaje. Bezopasno i očekivano |
| Nakon `pytest` u logovima ostane **~87 FIPA zapisa** | NALAZ #40 — testovi dijele bazu s dev/eval podacima i dižu pravi probe-agent (`gwprobe@localhost`). Čiste svoje usere i attempte, ali ne i logove. **Zato: baseline se pokreće POSLIJE testova, nikad prije** |
| 3 od 12 poruka označene kao „duplikat" | NALAZ #34 — zabilježeni promet stvarno sadrži duplikate; viewer ih označava umjesto da ih sakrije |
| Viewer prikazuje najviše 200 zapisa | NALAZ #36 — backend tiho capira `limit`; UI to ispisuje |
| Bedž `streak_7` nitko ne osvoji | NALAZ #24 — traži 7 kalendarskih dana, dulje od sesije. Očekivana stopa **0 %** |
| Modul 6 zaključan / nedostupan | NALAZ #19 — M6 je izvan opsega evaluacije, zadaci su `is_active=False` |
| P(L) krivulja „stoji" blizu 1.0 | NALAZ #16 — svojstvo BKT parametara, ne greška |

---

## 7. Zašto seed skripte NE MOGU obrisati podatke studenata

Provjereno u kodu (2026-07-20) — vidi i `docs/faza-4.6-eval-wrapup.md`:

- **`make db-seed`** (`app/db/seed.py`) — nema nijedne `DELETE`/`TRUNCATE`
  naredbe. Dira 5 tablica, sve UPSERT: `modules`, `concepts`,
  `concept_prerequisites`, `badges`, `users`. Jedini dodir `users` je
  `seed_admin` s `ON CONFLICT DO NOTHING`. **Ne dira** `attempts`,
  `skill_mastery`, `skill_mastery_history`, `xp_log`, `user_badges`, `streaks`.
- **`make sandbox-seed-if-empty`** — spaja se na `SANDBOX_DATABASE_URL`
  (port 5433, kontejner `postgres-sandbox`). `tutor_main` je **druga instanca
  Postgresa** na 5432. TRUNCATE pogađa isključivo 8 tablica sheme `ecommerce_v1`
  (`orders`, `products`, …). Kredencijali `sandbox_admin` nemaju pristup
  `tutor_main`.
- **`make db-tasks`** — importira samo `Task`/`TaskConcept`; taskovi se
  UPSERT-aju, nikad ne brišu. K tome je `attempts.task_id` FK s pravilom
  **NO ACTION**, pa bi brisanje taska s pokušajima baza **odbila**.

---

## 8. Kontakt / eskalacija

| situacija | postupak |
|---|---|
| `make backup` javi da restore nije prošao | **Zaustavi sesiju.** Podaci su u bazi, ali ih ne možeš sigurno iznijeti. Ne diraj volumene dok se ne razriješi |
| Sustav ne radi > 10 min | Prekini sesiju, ispričaj se sudionicima, zapiši točno vrijeme i simptom (za odjeljak o ograničenjima u radu) |
| Sumnja da su podaci izgubljeni | **Ne pokreći ništa što piše u bazu.** Prvo `ls -la backups/`, pa procjena |
| Pitanje o opsegu/metodologiji | mentor (voditelj AI Laba) |

**Zabilježi tijekom sesije** (ide u rad): broj sudionika, trajanje, sve prekide i
njihovo trajanje, sva pitanja sudionika koja otkrivaju nejasnoće u sučelju.
