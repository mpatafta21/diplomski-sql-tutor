# Faza 4.7 — nalazi nađeni usput, NEPOPRAVLJENI

Nalazi koji su izašli tijekom 4.7 polisha a **nisu 4.7 opseg**. Ovdje se bilježe, ne
popravljaju. Po 🔒 DOC politici svaka tvrdnja „X ne postoji" nosi citat pretrage.

---

## N-1 🔴 BLOKATOR PRIJE SLANJA LINKA — brisanje pojedinog sudionika nije dokazano izvedivo

**Status:** 🔴 blokator **prije nego link ode studentima** · **nije 4.7** · nađeno 2026-07-26
(stage 1A-dopuna)

> ⚠️ **PRIORITET PODIGNUT** (odluka korisnika, 2026-07-26, stage 1A-dopuna t.3): prvotno je
> ovo bilo zabilježeno kao „blokator deploymenta". Nakon što je informacija o sudjelovanju
> dodana i na **Profil**, obećanje o brisanju podataka prikazuje se **trajno svakom
> prijavljenom korisniku**, na ekranu koji posjećuje tijekom cijelog sudjelovanja — ne samo
> jednom prije registracije. Procedura brisanja pojedinog sudionika mora zato postojati
> **prije nego link ode studentima**, ne tek prije deploya. Obećanje koje stoji na ekranu
> mjesecima, a nije izvedivo, teže je opravdati od jednokratne rečenice.

### Tvrdnja

Informacija sudionika na `/register` (Faza 4.7-1a) obećava dvije stvari:

> „Za pitanja ili zahtjev za brisanje podataka: mpatafta21@student.foi.hr"
> „Podaci se čuvaju do obrane rada, nakon čega se brišu."

`agent_messages_log` **nema `user_id` kolonu** (#40), pa ga nijedan postojeći cleanup ne
dohvaća po korisniku, a `submitted_query` u njegovom `content`-u je vezan uz korisnika
(4.5b README, sekcija o osobnim podacima). **Brisanje jednog sudionika na zahtjev
trenutno NIJE dokazano izvedivo do kraja.**

### Dokaz 1 — tablica nema `user_id`

`backend/app/db/models.py:394-409`, cijeli popis stupaca:

```python
class AgentMessageLog(Base):
    __tablename__ = "agent_messages_log"
    __table_args__ = (
        Index("idx_agent_messages_correlation", "correlation_id"),
        Index("idx_agent_messages_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sender: Mapped[str] = mapped_column(String(50), nullable=False)
    receiver: Mapped[str] = mapped_column(String(50), nullable=False)
    performative: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[dict | None] = mapped_column(JSONB)
    correlation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
```

Sedam stupaca, **nijedan ne referencira korisnika**. Nema ni FK na `users`, pa ni CASCADE
ne pomaže. To potvrđuje i sam `prepare_eval_baseline.py:43`:

> `agent_messages_log` nema `user_id` (provjereno u shemi) → brisanje usera

### Dokaz 2 — po korisniku ga NE briše nijedno mjesto (citat pretrage)

```
$ grep -rn "agent_messages_log" --include=*.py --include=*.sh --include=*.sql \
    --include=Makefile . | grep -v "^./docs/"
scripts/backup_eval_data.sh:32:VERIFY_TABLES=(users attempts skill_mastery … agent_messages_log)
backend/app/db/models.py:395:    __tablename__ = "agent_messages_log"
backend/tests/test_agents_smoke.py:1,200,201,224   (testovi — čitaju/asertiraju)
backend/tests/test_db_schema.py:25,105,106         (testovi — shema)
backend/agents/recommender_agent.py:18             (komentar)
backend/agents/base.py:9,72                        (log_message — UPIS)
backend/alembic/versions/ac6a5eeac6e5_…:24,34,35,273,274,275  (migracija)
backend/scripts/prepare_eval_baseline.py:22,43,238,292,390,394,399,435,436
```

**Jedino mjesto koje ga uopće briše** je `prepare_eval_baseline.py:435`:

```python
session.execute(text("TRUNCATE TABLE agent_messages_log RESTART IDENTITY"))
```

To je **TRUNCATE cijele tablice** iza `--confirm` — sve ili ništa. Nema klauzule, nema
filtera, nema puta do „samo ovaj sudionik".

```
$ grep -rn "agent_messages_log" backend/scripts/
→ pogodci SAMO u prepare_eval_baseline.py (gore); nijedna druga skripta je ne dira
```

### Dokaz 3 — `purge_demo_users.py` je najbliža stvar per-user brisanju, i ne pokriva logove

`backend/scripts/purge_demo_users.py:61-75`:

```python
counts["skill_mastery_history"] = session.execute(
    delete(SkillMasteryHistory).where(SkillMasteryHistory.user_id.in_(ids))).rowcount
counts["xp_log"]   = session.execute(delete(XpLog).where(XpLog.user_id.in_(ids))).rowcount
counts["attempts"] = session.execute(delete(Attempt).where(Attempt.user_id.in_(ids))).rowcount
# users → CASCADE pokriva misconceptions, recommendations_log,
# skill_mastery, streaks, user_badges.
counts["users"]    = session.execute(delete(User).where(User.id.in_(ids))).rowcount
```

Pokriva 9 tablica (3 eksplicitno + 5 kroz CASCADE + `users`). **`agent_messages_log` nije
među njima** — i ne može biti, jer nema po čemu filtrirati. Uz to skripta hvata samo
`demo44_` prefiks, dakle nije ni namijenjena stvarnom sudioniku.

### Zašto to nije samo higijena

`content` je `JSONB` i nosi `submitted_query` studenta (4.5b README to izrijekom navodi kao
osobni podatak). Dakle nakon „brisanja" sudionika u bazi ostaje njegov SQL kod. Veza na
osobu nije u tablici, ali je **rekonstruktibilna** kroz `correlation_id` → `attempt_id`
u onim porukama koje ga nose (#40: 5 od 12 poruka po attemptu nosi `attempt_id`) — a i bez
toga sadržaj upita sam po sebi može biti prepoznatljiv.

### Što treba prije deploya (NIJE 4.7)

Procedura brisanja **pojedinog** sudionika, uključujući FIPA logove, **verificirana u oba
smjera** (dokazano da briše kad treba I da ne briše kad ne treba — poučak iz #39). Mogući
put bez izmjene sheme: prikupiti `correlation_id`-eve iz `attempts` tog korisnika PRIJE
brisanja attempta, pa obrisati logove po tom skupu — ali to je **backend/ops posao**,
mora se izmjeriti i testirati, i ne pokriva poruke bez `correlation_id`.

**Do tada je tvrdnja o brisanju na zahtjev djelomično nepokrivena.** Odluka je korisnikova:
(a) izgraditi proceduru prije deploya, ili (b) preformulirati odlomak u informaciji
sudionika da ne obećava više od onoga što je dokazano izvedivo.

**Srodno:** #37 (nenadoknadivi eval podaci), #40 (`pytest` ostavlja FIPA promet koji
nijedan cleanup ne dohvaća), 4.5b README (osobni podaci u logovima).

---

## N-2 🟡 `og:image` je RELATIVNA putanja — scraperi traže apsolutnu URL

**Status:** 🟡 deployment stavka · **nije 4.7** · 2026-07-26 (stage 1A-dopuna, točka 4)

`og:image` **je izrađen** (1200×630 PNG, `public/og-image.png`, izvor `public/og-image.svg`)
i uveden u `index.html` uz `og:image:width/height/alt` i
`twitter:card=summary_large_image`.

**Ali:** vrijednost je `/og-image.png`, dakle **relativna**. Open Graph scraperi (Slack,
Facebook, iMessage, WhatsApp) dohvaćaju sliku iz odvojenog zahtjeva i **zahtijevaju
apsolutnu URL** — relativnu većina ne razriješi. Domena je poznata tek pri deployu, pa se
ovdje ne može upisati.

**Prije objave linka sudionicima:** zamijeniti `/og-image.png` s
`https://<domena>/og-image.png`. Dokazati preview alatom platforme kojom se link šalje
(npr. Slack unfurl / Facebook Sharing Debugger), ne pretpostavkom.

Do tada preview i dalje nosi `og:title` + `og:description` (dokazano u buildu), što je
bitno bolje od gole domene — samo bez slike.

**Napomena o formatu:** slika je PNG namjerno. Slack/Facebook/iMessage **ne** renderiraju
SVG kao `og:image`, pa bi SVG bio isto što i nemati sliku. SVG je zadržan u `public/` kao
izvor za ponovnu rasterizaciju.

---

## N-3 🟡 Snimanje ekrana za dokumentaciju zaprlja `agent_messages_log` — ista klasa kao #40

**Status:** 🟡 proceduralno · zabilježeno · 2026-07-26 (stage 1A-dopuna, točka 6)

Za snimke prijavljenog stanja u stage 1A-dopuni registriran je privremeni korisnik
`demo44_shot` i otvoren Dashboard. **Dashboard poziva `/next-task`, a to prolazi kroz pun
agentski lanac** (XMPP → Prolog → Recommender) → svaki poziv **upisuje FIPA poruke u
`agent_messages_log`**.

Korisnik je uredno obrisan (`purge_demo_users` → `users_matched: 1`, `users: 1`; provjereno
`SELECT`-om, ostao je samo `admin`), **ali logovi nisu** — po N-1 se i ne mogu obrisati po
korisniku.

Izmjereno nakon čišćenja: `attempts` = 12, `agent_messages_log` = **351**.
⚠️ **Ne mogu tvrditi koliki je moj doprinos** — nisam zabilježio baseline PRIJE snimanja.
`attempts` = 12 nisu moji (nijedan Submit nije izvršen), a dio od 351 zapisa je.

**Praktična posljedica: nikakva za eval**, jer pred-eval slijed iz `docs/eval-runbook.md`
(`pytest → baseline --confirm → preflight → backup`) radi `TRUNCATE agent_messages_log`
(`prepare_eval_baseline.py:435`) pa ovo nestaje prije prve stvarne sesije.

**Poučak za dalje:** svaka radnja koja dira živi backend radi dokumentacije (snimke,
demonstracije, ručne provjere) treba **zabilježiti brojače prije i poslije**, isto kao što
runbook to traži za `make smoke`. Bez baseline brojke tvrdnja „ništa nisam zaprljao" nije
provjerljiva — a ovaj nalaz je dokaz koliko je lako.

### Dopuna — poučak PRIMIJENJEN, i sad ima brojku (2026-07-26, stage 1A-dopuna t.3)

Za snimke Profila s punom stranicom pokušaja trebao je račun s poviješću →
`seed_demo_user` (27 attempta kroz **pravi** `POST /attempt`, dakle pun agentski lanac).
Ovaj put su brojači zabilježeni PRIJE:

| tablica                 | prije | poslije (nakon `purge_demo_users`) | Δ           |
| ----------------------- | ----- | ---------------------------------- | ----------- |
| `users`                 | 1     | 1                                  | **0** ✅    |
| `attempts`              | 12    | 12                                 | **0** ✅    |
| `skill_mastery_history` | 22    | 22                                 | **0** ✅    |
| `agent_messages_log`    | 363   | **696**                            | **+333** ❌ |

`purge_demo_users` je uredno vratio sve što može (`skill_mastery_history: 77`, `xp_log: 9`,
`attempts: 27`, `users: 1`) i sve tri tablice su **točno** na baselineu. `agent_messages_log`
je narastao za **333 zapisa** i nema ga čime obrisati po korisniku — to je **N-1 izmjeren,
ne pretpostavljen** (27 attempta × ~12 poruka ≈ 324, plus `/next-task` i `/profile` pozivi).

**Preporuka za `docs/eval-runbook.md` (NE mijenjati sad):** prije snimanja artefakata za rad
(uklj. `docs/figures/`, #38) i prije svake demonstracije nad živim sustavom zabilježiti
`COUNT(*)` iz `agent_messages_log`, i tretirati snimanje kao **zahvat nad bazom**, ne kao
čitanje. Dashboard sam po sebi povlači `/next-task` → pun agentski lanac → upis.

**Srodno:** #40 (`pytest` ostavlja 87 redaka), N-1 (nema per-user brisanja logova), #38.

---

## N-4 🟡 Prsten fokusa je 2,59:1 u light temi — ispod 3:1 (WCAG 2.2 SC 2.4.11), token, cijela app

**Status:** 🟡 token-level a11y · **nije 4.7** (tokeni zamrznuti) · izmjereno 2026-07-26

Pri mjerenju nove sekcije na Profilu izmjeren je i `--ring`, koji nosi **svaki**
`focus-visible:outline-*` u aplikaciji:

|                                   | vs `card`     |
| --------------------------------- | ------------- |
| `--ring` light `oklch(0.708 0 0)` | **2,59:1** ❌ |
| `--ring` dark `oklch(0.556 0 0)`  | **3,79:1** ✅ |

WCAG 2.2 SC 2.4.11 (Focus Appearance) traži **≥ 3:1** za indikator fokusa prema susjednoj
pozadini. Light tema ne prolazi.

🔴 **Nije uvedeno u 4.7** — `--ring` je shadcn-seedani token iz 4.1b i koristi ga svaka
fokusabilna površina (nav, gumbi, poveznice, inputi, paginacija). Popravak je **izmjena
tokena**, što je globalnim pravilima 4.7 izričito zabranjeno, i tražio bi remjeru cijele
palete kao u #33.

**Ublažavajuće, ali NE opravdanje:** inputi uz prsten dobivaju i `focus-visible:border-ring`

- `ring-3`, a poveznice u sekciji sudjelovanja su **trajno podcrtane** pa fokus nije jedini
  signal njihove interaktivnosti. To ne mijenja činjenicu da je sam indikator ispod praga.

**Ne tvrdim da je fokus u novoj sekciji WCAG-usklađen** — tvrdim izmjerenu brojku i
navodim da je ograničenje naslijeđeno, app-wide.

Kandidat za Fazu 6 uz punu remjeru palete. Prijavljuje se u radu kao poznato ograničenje,
kao #33.

---

## N-5 🔴 Stage 1C dobiva izlazni kriterij: mobilni drawer MORA imati stavku Profil

**Status:** 🔴 ulazni uvjet za stage 1C · 2026-07-26

Informacija o sudjelovanju je od stage 1A-dopune **na Profilu** (`/profile#sudjelovanje`).
Ispod 768px sidebar je `hidden … md:flex` (`AppShell.tsx:88`) i **nema zamjenske
navigacije** — dakle prijavljen korisnik na telefonu **nema puta** do te informacije:
`/register` mu je zatvoren (`PublicOnlyRoute` → `Navigate to="/"`), a Profil nedosežan.

**Izlazni kriterij za 1C:** mobilni drawer mora sadržavati stavku **Profil**. Bez nje je
tekst o sudjelovanju, kontaktu i brisanju podataka nedostupan cijeloj klasi korisnika.

⚠️ **ISPRAVAK vlastite tvrdnje:** u izvještaju report gatea 1b napisao sam da „stage 1C ne
mora ništa replicirati (nije nav stavka)". To je bilo **netočno** — vrijedilo bi samo da
sekcija nije vezana na ekran koji se dosiže navigacijom. Vezana je.

---

## N-6 🟡 `CORS_ORIGINS` default pokriva samo `:5173` — kriv origin izgleda kao pad aplikacije

**Status:** 🟡 deployment stavka · **nije 4.7** · empirijski potvrđeno 2026-07-26

`backend/app/core/config.py:77-79`:

```python
CORS_ORIGINS: list[str] = _list(
    "CORS_ORIGINS",
    ["http://localhost:5173", "http://127.0.0.1:5173"],
)
```

**Kako se manifestira:** pri snimanju u stage 1A-dopuni dev server je bio dignut na `:5199`.
Token je bio valjan — `curl -H "Authorization: Bearer …" /me` vraća **200** s ispravnim
korisnikom — ali je preglednik odbio odgovor zbog CORS-a, `AuthProvider` je pao u
`status='anon'` i `ProtectedRoute` je preusmjerio na `/login`. **Simptom je izgledao kao
neispravna prijava**, a bio je konfiguracija origina. Nijedna poruka u UI-ju to ne razlučuje.

**Zašto je to deployment rizik, ne kurioznost:** na javnom VPS-u frontend ide s domene, ne s
`localhost:5173`. Ako `CORS_ORIGINS` nije postavljen kroz env, **svi** studenti dobiju
uspješnu prijavu koja se odmah vrati na `/login` — dakle sustav izgleda potpuno slomljen,
a backend je zdrav.

**Prije deploya:** `CORS_ORIGINS` postaviti na stvarnu domenu i dokazati **prijavom kroz
preglednik**, ne `curl`-om (curl ne provodi CORS pa uspijeva i kad preglednik ne bi).

---

## Metodološka bilješka za wrapup i rad — izračun mjeri element, snimka mjeri hijerarhiju

**Zabilježeno 2026-07-26 (stage 1A + 1A-dopuna).**

Pomoć uz polje `username` na `/register` prošla je kontrastni izračun: `text-muted-foreground`
na `card` = **4,73:1 light / 6,91:1 dark** (izmjereno 2026-07-26, alpha-kompozitirano),
dakle **iznad** WCAG AA praga 4,5:1. U izolaciji je izgledala uredno.

Na **snimci** je bila najslabiji tekst na ekranu — i to je postala **tek nakon** što je
susjedni blok (informacija sudionika) podignut s `text-xs`/`muted-foreground` na
`text-sm`/`foreground` (19,13:1 / 15,97:1). Nijedan element nije pao ispod praga; pala je
**relativna hijerarhija**, a to nijedan per-element izračun ne mjeri.

**Poučak:** kontrastni izračun i vizualna provjera nisu redundantni, nego mjere različite
stvari — izračun **usklađenost pojedinog elementa**, snimka **relativnu težinu u
kompoziciji**. Uz to: promjena jednog elementa može pogoršati čitljivost **drugog,
nedirnutog** elementa, pa provjera nakon izmjene ne smije biti ograničena na izmijenjeni
element.

Isti poučak vrijedi i u drugom smjeru: prsten fokusa (N-4) izgleda uredno na snimci, a
izmjeren je na **2,59:1** u light temi — snimka to ne otkriva. Zato oboje.

Vezano uz 🔒 DOC politiku (#33): brojka i datum su nužni, ali nisu dovoljni — treba i
naznaka **u kojem kontekstu** je mjereno.
