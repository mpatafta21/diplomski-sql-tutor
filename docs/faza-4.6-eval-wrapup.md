# Faza 4.6-eval — Sigurnost podataka, export, čisti baseline — WRAP-UP

**Status:** ✅ KOMPLETNA na grani `faza-4-6-eval-prep`, tag `faza-4-6-eval-prep`. Bez push-a.
**Obuhvat:** backup s verificiranim restoreom, guard protiv `down -v`, pseudonimizirani export,
čisti eval baseline, runbook za dan evaluacije, slike za rad.
**Gates:** `pytest` **485 passed / 1 skipped** · `make preflight` **ZELEN** · `ruff` čist ·
`black` primijenjen na nove skripte.
**Backend:** **NULA izmjena postojećeg koda.** `git diff main..HEAD -- backend/` je **PRAZAN**;
dodane su samo dvije NOVE skripte pod `backend/scripts/` (konvencija repoa — ondje živi svih
20 postojećih skripti). `schema.d.ts` i `openapi.json` netaknuti.

---

## 1. Što je isporučeno

| Datoteka | Uloga |
|---|---|
| `scripts/backup_eval_data.sh` | `pg_dump` izvan volumena + **verifikacija restore-a** |
| `Makefile` → `backup` | poziva gornju skriptu |
| `Makefile` → `dev-reset` | jedini target s `down -v`, uz obveznu upisanu potvrdu |
| `backend/scripts/export_eval_data.py` | 9 CSV-ova za analizu, pseudonimizirano + samoprovjera |
| `backend/scripts/prepare_eval_baseline.py` | čišćenje dev tragova, `--dry-run` kao DEFAULT |
| `docs/eval-runbook.md` | procedura za dan evaluacije, sve brojke izmjerene |
| `docs/figures/` (9 PNG + README) | slike za rad + provenijencija |
| `.gitignore` | `backups/`, `exports/` |
| `README.md` | sekcije `make backup` i zabrana `down -v` |

---

## 2. 🔴 IZLAZ 1 — Dokaz da je backup RESTORE-ABILAN

Ne „datoteka postoji", nego **vraćena i uspoređena**:

```
▸ pg_dump u tijeku...        ✓ 52K · gzip integritet OK
▸ Verifikacija restore-a (privremena baza 'tutor_main_restore_check')
  ┌────────────────────────┬──────────┬──────────┬────────┐
  │ tablica                │   izvor  │  restore │ status │
  │ agent_messages_log     │      978 │      978 │  ✓     │
  │ attempts               │       35 │       35 │  ✓     │
  │ skill_mastery_history  │       93 │       93 │  ✓     │
  │ users / tasks / xp_log │  2/85/33 │  2/85/33 │  ✓     │
  └────────────────────────┴──────────┴──────────┴────────┘
  ✓ agregat attempta (Σxp/Σtočnih) identičan: 840/23
```

Brojke redaka **nisu dovoljne** (dump s pokvarenim vrijednostima imao bi iste), pa se
uspoređuje i agregat `Σxp_awarded / Σis_correct`.

**🔴 Negativni test — provjera stvarno hvata pokvaren dump:** iz valjanog dumpa uklonjeni
su svi `COPY public.attempts` retci i takav je vraćen → **izvor 35 vs restore 0** →
skripta bi pala. Provjera koja uvijek kaže ✓ ne dokazuje ništa.

---

## 3. 🔴 IZLAZ 2 — Makefile targeti koji diraju volumene

Audit svih targeta (`grep` za `down`/`-v`/volume):

| target | dira volumene? |
|---|---|
| `infra-down` | **NE** — `docker compose down` bez `-v` |
| `dev`, `infra-up`, `db-*`, `sandbox-seed*`, `sweep`, `smoke`, `preflight`, `backup` | NE |
| **`dev-reset`** | **DA — jedini.** Ispiše stanje baze i zadnji backup, pa traži doslovno `OBRISI SVE` |

**Guard testiran u OBA smjera:** kriva potvrda → `✅ PREKINUTO — ništa nije obrisano`
(exit ≠ 0, volumeni netaknuti); ispravna → volumeni obrisani.

### Potvrda 1e — seed skripte NE MOGU dirati podatke studenata

| skripta | dokaz |
|---|---|
| `make db-seed` (`app/db/seed.py`) | **0 pogodaka** na `DELETE`/`TRUNCATE`/`DROP` u cijelom `app/db/`. Dira 5 tablica, sve UPSERT (`seed.py:30,60,87,95,114`): `modules`, `concepts`, `concept_prerequisites`, `badges`, `users`. Jedini dodir `users` je `seed_admin` s `ON CONFLICT DO NOTHING` po username (`seed.py:120`) → ne mijenja postojeće retke, ne rehashira lozinku. **Ne dira** `attempts`, `skill_mastery`, `skill_mastery_history`, `xp_log`, `user_badges`, `streaks` |
| `make sandbox-seed-if-empty` | Spaja se na `SANDBOX_DATABASE_URL` (`seed_sandbox.py:29,85-92`) = port **5433**, kontejner `postgres-sandbox`. `tutor_main` je **druga instanca** na 5432. TRUNCATE pogađa 8 tablica sheme `ecommerce_v1` (`seed_sandbox.py:78-81`, `search_path` na `:91`): `reviews`, `order_items`, `orders`, `products`, `employees`, `customers`, `suppliers`, `categories`. Kredencijali `sandbox_admin` nemaju pristup `tutor_main` |
| `make db-tasks` | Importira samo `Concept`/`Module`/`Task`/`TaskConcept` (`import_dataset.py:24`). Taskovi se UPSERT-aju (`:103`), nikad ne brišu; jedini `DELETE` je `task_concepts` po `task_id` (`:121`) |

**Dodatna strukturna brana (izmjerena iz `information_schema`):** `attempts.user_id` i
`attempts.task_id` su FK s pravilom **NO ACTION** → brisanje usera ili taska s pokušajima
baza **odbija**. Studentovi podaci ne mogu tiho nestati kao posljedica brisanja negdje drugdje.

**Odgovor na „STANI I JAVI ODMAH": ništa od navedenog nije aktiviralo alarm.**

---

## 4. IZLAZ 3 — Export: sanity brojke i potvrda privatnosti

Na demo podacima (prije čišćenja):

```
sudionika ukupno: 2 (studenata: 1) · s barem jednim attemptom: 2
attempta: 35 · BKT točaka: 93 · XP zapisa: 33 · bedževa: 3 · zadataka: 85
raspon datuma: 2026-07-19 … 2026-07-20
```

**Provjera privatnosti je UGRAĐENA u skriptu, ne obećanje u dokumentaciji.** Nakon pisanja
CSV-ova skripta pročita svaki i usporedi **ćeliju po ćeliju** sa svim živim usernameovima
i e-mailovima; nađe li pogodak, **odbija export** (`SystemExit`).

Usporedba je po ćeliji, ne po sirovom tekstu, iz konkretnog razloga: admin se zove `admin`,
a `participants.csv` ima stupac `role` s vrijednošću `admin` — sirovi `substring` to je
prijavljivao kao curenje. `role` je **zatvoren šifrarnik** koji generira sama skripta pa se
izuzima imenom; svaki drugi stupac se provjerava. Neovisno o tome, ćelija koja sadrži `@`
je curenje **uvijek** — taj oblik ne može doći ni iz jednog legitimnog stupca.

**🔴 Testirano u oba smjera** (podmetnuti redci):

| scenarij | ishod |
|---|---|
| username u stupcu `user_pseudonym` | **ODBIJENO** ✓ |
| e-mail u proizvoljnom stupcu | **ODBIJENO** ✓ |
| čist redak (kontrola) | prošlo ✓ |

Živi izlaz: `✓ 9 CSV datoteka provjereno ćeliju-po-ćeliju protiv 4 živih identiteta — 0 pogodaka`.

`_pseudonym_map.csv` je jedina datoteka s identitetom; `exports/` je u `.gitignore`.
`submitted_query` je **namjerno izostavljen** (osobni podatak, nepotreban za kvantitativnu analizu).

---

## 5. IZLAZ 4 — Baseline: dry-run i zeleni preflight

**Dry-run je otkrio rupu koju plan nije predvidio:** od 35 attempta samo je 28 pripadalo
`demo44_student`; **7 je bilo adminovih** (dev testiranje). Admin se zadržava → baseline
ne bi bio nula. Zato skripta briše **aktivnost** admin računa (attempts, BKT, XP, bedževi,
streakovi, misconceptions, recommendations_log), a **račun, rolu i lozinku ostavlja** — bez
računa nema pristupa admin sučelju tijekom evala. Brojke se poklapaju: 28 + 7 = 35,
79 + 14 = 93, 25 + 8 = 33.

**🔴 Nepoznati useri se NE BRIŠU.** Student bez sentinel prefiksa mogao bi biti stvarni
sudionik prethodne sesije (#37), pa se prijavljuje i preskače; za brisanje ga treba imenovati
(`--also-user`). **Dokazano uživo:** račun `S99` (konvencija sudionika) prijavljen je kao
nepoznat i **nije obrisan**.

**Završno stanje:**

```
useri: 1 (admina: 1) · attempti: 0 ✓ · BKT: 0 ✓ · XP: 0 ✓ · FIPA logova: 0 ✓
zadataka: 85 (aktivnih: 80) · koncepata: 30
✅ BASELINE ČIST
```

`make preflight` nakon toga: **ZELEN** (sweep 80/80 + živi smoke `is_correct=True`).

---

## 6. Puni from-scratch prolaz (izmjereno 2026-07-20)

Uz `make dev-reset` obrisane su **sve tri** volumena i sustav podignut od nule — ujedno
ponovna potvrda NALAZA #26:

| korak | vrijeme | | korak | vrijeme |
|---|---|---|---|---|
| `infra-up` | 1 s | | `sandbox-seed-if-empty` (4 898 redaka) | 1 s |
| `wait-db` | 3 s | | `register-agents` (5/5) | 1 s |
| `db-migrate` | 1 s | | `sweep` (80/80) | < 1 s |
| `db-seed` | 1 s | | **infra ukupno** | **9 s** |
| `db-tasks` (85) | 1 s | | backend startup + `preflight` | ~18 s + 4 s |
| | | | **UKUPNO do spremnog sustava** | **≈ 31 s** |

⚠️ Vrijedi uz **već povučene docker imageove**.

---

## 7. Errata (dodano u ovoj fazi)

- **#37** — eval podaci nenadoknadivi, živjeli samo u volumenu → backup s verificiranim
  restoreom, `backups/` gitignoriran uz obvezu kopije na drugi medij, `down -v` zabranjen.
- **#38** — artefakti rada (slike) bili izvan verzije → `docs/figures/` + provenijencija.
- **#39** — `make dev-reset` guard je odbijao i **ispravnu** potvrdu: `docker compose exec -T`
  prije `read` **proždire stdin**. Kvar je bio zatvoren (odbijao brisati — sigurna strana),
  ali je target bio neupotrebljiv. Popravak `</dev/null`. **Poučak: guard koji nije testiran
  u oba smjera nije guard.**
- **#40** — **`pytest` piše u živu `tutor_main`**: nema zasebnu testnu bazu, a
  `test_coordinator.py` diže pravi probe-agent (`gwprobe@localhost`). Puni suite ostavio je
  **87 redaka** u `agent_messages_log`. Testovi čiste svoje usere i attempte, ali ne logove
  (tablica nema `user_id` — ista slijepa točka kao `make smoke`, 12 zapisa).
  → runbook zabranjuje `pytest` tijekom sesije; **baseline se pokreće POSLIJE testova**.
- **🔒 DOC** — destruktivna skripta ima `--dry-run` kao default i nikad ne briše nepoznato
  nagađanjem.

**Rezani opseg:** Faze **4.6 (motion/WS)** i **4.7 (visual QA)** rezane su odlukom korisnika
(runway za eval + pisanje). Obrazloženje zapisano u erratu i ide u rad, u odjeljak o opsegu
implementacije — rezano svjesno, ne izostavljeno previdom.

---

## 8. Za nasljednike / otvoreno

- **Redoslijed prije evala je bitan:** `pytest` → `prepare_eval_baseline --confirm` →
  `make preflight` → `make backup`. Obrnuto (baseline pa testovi) ostavlja 87 lažnih zapisa.
- **KORAK 5 je morao ići PRIJE KORAKA 3** — čišćenje baselinea briše `demo44_student`, jedini
  račun s BKT poviješću, pa se snimke krivulja poslije toga više ne mogu napraviti. Plan je
  imao obrnut redoslijed; izvedeno je zamijenjeno.
- **NALAZ #17 i dalje otvoren** — snimke su rađene golim `chrome-headless-shell` + CDP iz
  scratchpada; `playwright-core` i dalje NIJE u `package.json`, committed e2e suite ne postoji.
- **Zamke pri ponovnom snimanju** (obje su jednom dale lažnu figuru): Monaco ignorira
  `textarea.value` → tipkati kroz `Input.insertText`; upit mora ići u **novi redak** jer ga
  inače placeholder-komentar guta. Skripta sad prekida ako upit nije na vlastitom retku.
- **Backup nije automatiziran** — `make backup` se pokreće ručno. Kopiranje na drugi medij je
  ljudski korak i najslabija karika u lancu; runbook ga stavlja odmah iza svake sesije.
