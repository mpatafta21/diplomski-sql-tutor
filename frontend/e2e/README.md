# e2e smoke — student happy path (NALAZ #17)

Jedan Playwright scenarij koji dokazuje da student **uopće prođe** kroz sustav:

```
register → login → /task → Run → Submit → feedback → „Sljedeći zadatak"
```

## Pokretanje

```bash
cd frontend
npm run e2e            # headless, jedan worker
npm run e2e:ui         # interaktivno, za debug
```

Traži: **docker compose gore** (`postgres-main`), **backend na :8000**
(`make backend`), i dev server — njega Playwright digne sam ili ponovno iskoristi
postojeći na :5173. Protiv druge adrese: `E2E_BASE_URL=https://… npm run e2e`.

## 🔴 KADA SE NE POKREĆE

**NIKAD tijekom evaluacijske sesije** — isto pravilo kao za `pytest` (#40). Suite piše u
**živu `tutor_main`**: stvara pravog korisnika, pravi attempt i pravi promet kroz agentski
lanac. Teardown vraća sve osim jedne tablice (v. niže).

**Predviđena mjesta pokretanja:**

1. **prije** pred-eval slijeda (`pytest → baseline --confirm → preflight → backup`);
2. **nakon deploya**, protiv žive domene, kao provjera da je put prohodan prije nego link
   ode sudionicima — tada `E2E_BASE_URL` pokazuje na javni URL, a teardown se **ne
   izvodi** protiv produkcijske baze bez odluke (docker-compose pristup ondje ionako ne
   postoji).

## Higijena podataka

**Prefiks `e2e_`** + jedinstveni sufiks po runu. Prefiks je odabran jer ga
`prepare_eval_baseline.py` već poznaje kao sentinel testnog računa — nepoznati korisnici
se po 🔒 politici **nikad ne brišu nagađanjem**.

**Redoslijed brisanja je određen FK grafom**, provjereno upitom nad `information_schema`
(2026-08-10), ne intuicijom:

```
xp_log                → attempts (attempt_id), users
skill_mastery_history → attempts (attempt_id), users
attempts              → users
skill_mastery · streaks · user_badges · misconceptions · recommendations_log → users
```

Zato `attempts` **ne ide prvi** — dvije tablice vise o njemu. Isti redoslijed koristi i
`backend/scripts/purge_demo_users.py:61-75`.

**Dokaz umjesto tvrdnje.** `global-setup` snimi `COUNT(*)` po tablici, `global-teardown`
ga ponovi i **ispiše razliku**. Ako ijedna tablica osim `agent_messages_log` ne padne
natrag na polaznu brojku, **teardown baca grešku** — suite koji zagađuje bazu gori je od
suitea koji ne postoji.

Izmjereno na runu 2026-08-10:

```
✅ users 1→1 · attempts 13→13 · xp_log 7→7 · skill_mastery 3→3
✅ skill_mastery_history 24→24 · streaks 3→3 · user_badges 1→1
✅ misconceptions 2→2 · recommendations_log 75→75
⚠️  agent_messages_log 816→837 (+21)
```

### 🔴 `agent_messages_log` se NE MOŽE očistiti

Tablica **nema `user_id`** (ERRATA #40, #46), pa je nijedan cleanup po korisniku ne
dohvaća — ni ovaj teardown, ni `purge_demo_users`, ni CASCADE (nema FK na `users`). Jedino
mjesto koje je briše je `TRUNCATE` u `prepare_eval_baseline.py:435`, iza `--confirm`.

**Jedan run ostavlja ~21 zapis.** Broj je namjerno **vidljiv** u ispisu, ne prešućen: ono
što se ne može očistiti mora se barem znati. Pred-eval slijed te zapise ionako briše.

## Opseg — što suite NE radi

- **Ne provjerava točnost odgovora.** Rješenje zadatka nije u API-ju (i ne smije biti),
  pa smoke ne zna što je točno. Tvrdi da lanac radi: editor prima unos, Run vraća panel,
  Submit vraća feedback s **nekim** verdiktom, CTA vodi na zadatak.
- **Nema coveragea, unit testova ni snapshotova.** Ovo je ulazni gate, ne test suite.
- **Nema izmjena ponašanja produkcijskog koda.** `data-testid` bi bio dopušten; nije
  trebao — sve se dohvaća preko role/label, kako korisnik i vidi ekran.

## Dvije zamke naučene pri pisanju (ne ponavljati)

**1. Monaco i `keyboard.type()`.** SQL autocomplete hvata pojedinačne pritiske i sam
dopunjava, pa unos stigne izobličen — `SELECT id, name FROM categories ORDER BY id;`
završilo je kao `1ST id, ROM cateri Od;`. Koristi se **`keyboard.insertText()`**, koji ne
generira key eventove.

**2. `.local` e-adrese backend odbija s 422.** `email-validator` ih tretira kao
special-use/reserved. To je **ispravno ponašanje**, ne bug — testni podaci idu na
`@example.com` (IANA-rezerviran za dokumentaciju).
