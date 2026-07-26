# Faza 4.7 — nalazi nađeni usput, NEPOPRAVLJENI

Nalazi koji su izašli tijekom 4.7 polisha a **nisu 4.7 opseg**. Ovdje se bilježe, ne
popravljaju. Po 🔒 DOC politici svaka tvrdnja „X ne postoji" nosi citat pretrage.

---

## N-1 🔴 BLOKATOR DEPLOYMENTA — brisanje pojedinog sudionika nije dokazano izvedivo do kraja

**Status:** 🔴 blokator deploymenta · **nije 4.7** · nađeno 2026-07-26 (stage 1A-dopuna)

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

**Srodno:** #40 (`pytest` ostavlja 87 redaka), N-1 (nema per-user brisanja logova).
