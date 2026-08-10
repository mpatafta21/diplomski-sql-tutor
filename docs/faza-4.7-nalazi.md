# Faza 4.7 — nalazi nađeni usput, NEPOPRAVLJENI

Nalazi koji su izašli tijekom 4.7 polisha a **nisu 4.7 opseg**. Ovdje se bilježe, ne
popravljaju. Po 🔒 DOC politici svaka tvrdnja „X ne postoji" nosi citat pretrage.

---

## N-1 🔴 BLOKATOR PRIJE SLANJA LINKA — brisanje pojedinog sudionika nije dokazano izvedivo

**Status:** 🔴 blokator **prije nego link ode studentima** · **nije 4.7** · nađeno 2026-07-26
(stage 1A-dopuna) · ⟳ **PROMOVIRAN U ERRATU KAO #46** (2026-08-09)

> 📌 **Kanonski zapis je od 2026-08-09 `docs/errata.md` #46.** Ovaj odjeljak ostaje kao
> radni trag s punim dokazima; errata nosi status, izmjerenu brojku i ekstrapolaciju na
> eval volumen. Razlog promocije: ovo nije radna bilješka nego **obveza prema sudioniku**
> koja trajno stoji na Profilu. Ako se tekst obećanja ikad mijenja, mijenja se **#46**.

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

## N-4 🟡 Prsten fokusa — ISPRAVLJEN KRITERIJ i PREMJEREN prema OBJE susjedne boje

**Status:** 🟡 token-level a11y · **nije 4.7** (tokeni zamrznuti) · prvo mjerenje
2026-07-26, **ispravak kriterija i puno premjeravanje 2026-08-09**

### ⟳ ISPRAVAK VLASTITE TVRDNJE — krivi kriterij i premala mjerna baza

Izvorni zapis glasio je „2,59:1 u light temi — ispod 3:1 (**WCAG 2.2 SC 2.4.11**)".
**Oboje je trebalo popraviti:**

1. 🔴 **Krivi kriterij.** SC **2.4.11 u WCAG 2.2 je „Focus Not Obscured (Minimum)"** — o
   tome da fokusirani element nije **prekriven** autorskim sadržajem; s kontrastom nema
   veze. U **WCAG 2.1, koji je baseline projekta** (plan §3.5), SC 2.4.11 **uopće ne
   postoji**. Zahtjev **≥ 3:1 za vidljivost indikatora** dolazi iz **SC 1.4.11 Non-text
   Contrast (AA, WCAG 2.1)**, koji pokriva „vizualne informacije potrebne za identifikaciju
   komponenata sučelja **i njihovih stanja**" — fokus je stanje. Kontrast **i veličina
   zajedno** su SC **2.4.13 Focus Appearance (WCAG 2.2)**, a to je **AAA** — izvan
   baselinea, navodi se samo informativno.
2. 🔴 **Premala mjerna baza.** Prsten graniči s **dvije** boje: plohom oko sebe i
   komponentom koju okružuje. Brojka 2,59:1 mjerila je **samo jedan par** (`ring` vs
   `card`) i prikazana je kao cijela slika. Premjeravanje pokazuje da to **podcjenjuje**
   jedan slučaj (ispunjeni gumb, 6,91:1) i **precjenjuje ujednačenost** ostalih.

### Kako je mjereno

Konvertor oklch → sRGB → relativna luminancija, alpha **kompozitirana** nad navedenom
plohom. Prije upotrebe **validiran na šest već objavljenih brojki** projekta (`ring` vs
`card` 2,59 / 3,79; `muted-foreground` vs `card` 4,73 / 6,91; `foreground` vs `card`
19,79 / 17,16) — sve reproducirane na dvije decimale, pa su nove brojke usporedive sa
starima. Vrijednosti tokena: `--ring` light `oklch(0.708 0 0)` = `#a1a1a1`, dark
`oklch(0.556 0 0)` = `#737373`.

Geometrija je pročitana **iz živog DOM-a** (CDP, dev server, `/register`), ne iz koda:
`outline-style: solid`, `outline-width: 2px`, `outline-offset: 2px`,
`outline-color: oklch(0.708 0 0)` light / `oklch(0.556 0 0)` dark, uz
`matches(":focus-visible") === true`.

### Mehanizam A — `outline-2 outline-offset-2 outline-ring`

Poveznice, nav stavke, `ConceptRow`, `MasteryRow`, mailto u sekciji sudjelovanja.

🔴 **Ključna posljedica `outline-offset: 2px`:** razmak od 2px pokazuje **plohu ispod**, pa
su **obje** susjedne boje prstena ista ploha. Ovdje **nema druge boje koja bi indikator
spasila** — za razliku od mehanizma B.

| Ploha ispod                                    |     light     |    dark     |
| ---------------------------------------------- | :-----------: | :---------: |
| `card` (kartice, Profil)                       | **2,59:1** ❌ | 3,79:1 ✅   |
| `background` (ploha stranice)                  | **2,59:1** ❌ | 4,18:1 ✅   |
| `sidebar` (nav — glavna tipkovnička površina)  | **2,48:1** ❌ | 3,79:1 ✅   |
| `bg-muted/40` nad `card` (info blok /register) | **2,51:1** ❌ | 3,56:1 ✅   |

### Mehanizam B — `focus-visible:border-ring` + `ring-3 ring-ring/50`

Shadcn baza za `Input` i `Button`. Tri granice: prsten-rub prema **ispuni komponente**,
prsten-rub prema **halou** (`ring/50` kompozitiran nad plohom), halo prema **plohi**.

| Komponenta                | granica                                  |     light     |    dark     |
| ------------------------- | ---------------------------------------- | :-----------: | :---------: |
| **Input**                 | rub(ring) vs ispuna (light `bg-transparent`→`card`; dark `bg-input/30`) | **2,59:1** ❌ | 3,38:1 ✅ |
|                           | rub(ring) vs halo                        |    1,68:1     |   2,02:1    |
|                           | halo vs ploha                            |    1,54:1     |   1,87:1    |
| **Button default**        | rub(ring) vs `primary` (ispuna gumba)    |  **6,91:1** ✅ | 3,76:1 ✅  |
|                           | rub(ring) vs halo                        |    1,68:1     |   2,02:1    |
| **Button outline** (paginacija) | rub(ring) vs ispuna                |  **2,59:1** ❌ | 3,38:1 ✅  |

Uz to, kontrast **promjene stanja** (rub u mirovanju `--input` → rub u fokusu `--ring`):
**2,06:1** light / **2,41:1** dark — relevantno samo za AAA čitanje (2.4.13), navodi se
radi potpunosti.

### PRIJEDLOG PRESUDE — 🔴 ČEKA OK (t.3c)

Pod **SC 1.4.11 (AA, WCAG 2.1)**, prag ≥ 3:1 prema susjednoj boji:

- **DARK tema PROLAZI** na svakoj izmjerenoj granici komponente (3,38–4,18:1).
- **LIGHT tema PADA** za mehanizam A (2,48–2,59:1 prema **jedinoj** susjednoj boji) te za
  `Input` i `Button outline` (2,59:1). To pogađa nav, poveznice, koncept-retke, inpute i
  paginaciju — dakle **većinu tipkovničkog puta**.
- **LIGHT tema PROLAZI** samo za ispunjeni `Button default` — 6,91:1 prema vlastitoj
  tamnoj ispuni. Ta je granica ono što gumb čini razlučivim; vanjska granica ga ne nosi.
- **Halo (`ring/50`) nikad ne dosegne 3:1** prema plohi (1,54 light / 1,87 dark) → on je
  **ukras, ne indikator**; nositelj je 1px/2px rub.

Prethodna formulacija „prsten je 2,59:1" time nije bila netočna za par koji je izmjerila,
ali **jest bila nepotpuna kao presuda o aplikaciji**.

### Što se NE radi sada

🔴 **Nijedan token nije mijenjan** (`--ring` ni bilo koji drugi) — potvrđeno u diffu.
Popravak je token-level i dira svaku fokusabilnu površinu, što je globalnim pravilima 4.7
zabranjeno.

**Prijedlog za Fazu 6 — kao ZASEBAN nalaz, odvojeno od #13 i #33.** Spajanje nalaza u
`c12ec31` je i dovelo do toga da #13 ostane bez vlastite presude; ovaj se ne smješta u isti
paket. Smjerovi (ni jedan nije odabran, svi traže remjeru):
podignuti tamnoću `--ring` u light temi; ili dodati drugi, kontrastni sloj prstena
(vanjski svijetli + unutarnji tamni) čime prestaje ovisiti o jednoj plohi; ili ukinuti
`outline-offset` ondje gdje prsten leži na ispuni komponente.

**Ublažavajuće, ali NE opravdanje:** poveznice u sekciji sudjelovanja su **trajno
podcrtane** (v. N-7), pa fokus nije jedini signal njihove interaktivnosti. To ne mijenja
izmjerenu brojku indikatora.

---

## N-7 ✅ Poveznica u `ParticipationSection` — 1.4.1 PROVJEREN IZ DOM-a, prolazi

**Status:** ✅ provjereno, **bez izmjene koda** · 2026-08-09

Prethodni zapis naveo je **jednu** brojku (19,79:1) za „tekst sekcije **i** poveznicu".
Ista brojka za dva elementa znači **istu boju** — a ako je boja jedini razlikovni kanal,
to je prekršaj **SC 1.4.1 Use of Color**. Provjereno je **iz računatog stila živog DOM-a**
(CDP, `/register`, gdje je niz klasa **byte-identičan** onome u
`ParticipationSection.tsx:68`), obje teme:

| svojstvo                 | poveznica                  | okolni `<p>`               |
| ------------------------ | -------------------------- | -------------------------- |
| `color` (light)          | `oklch(0.145 0 0)`         | `oklch(0.145 0 0)` — ISTA  |
| `color` (dark)           | `oklch(0.985 0 0)`         | `oklch(0.985 0 0)` — ISTA  |
| `text-decoration-line`   | **`underline`**            | `none`                     |
| `text-underline-offset`  | `4px`                      | `auto`                     |
| `font-weight`            | **500**                    | 400                        |

**Presuda: 1.4.1 nije prekršen — i to ne granično.** Boja **uopće nije kanal** (identična
je), pa se razlikovanje u cijelosti oslanja na **podcrtavanje + težinu fonta**, dva
ne-bojna kanala. Jedna brojka za oba elementa bila je **posljedica** te odluke, ne simptom
propusta. **Nikakav popravak nije potreban** — `underline underline-offset-4 font-medium`
već stoji u komponenti.

**Fokus-vidljivost te poveznice, mjerena zasebno** (traženo uz ovu provjeru): outline
2px, offset 2px, boja `--ring` → **2,59:1 light / 3,79:1 dark** na `card` (Profil) i
**2,51:1 / 3,56:1** na `bg-muted/40` (/register). Light pada pod 1.4.11 — to je N-4,
naslijeđeno i app-wide, ne svojstvo ove komponente.

**Usput uočeno, NE dirano (nije 4.7 opseg, nije prekršaj):** poveznica „Prijavi se"
(`RegisterPage.tsx:220-227`) razlikuje se od okolnog teksta bojom (`text-foreground` vs
`text-muted-foreground`) i težinom (500 vs 400), a podcrtava se **tek na hover**
(`hover:underline`). Težina fonta jest ne-bojni kanal pa 1.4.1 formalno drži, ali je
kanal slabiji nego kod mailto poveznice. Kandidat za dosljednost, ne za popravak.

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

## N-8 🔴 Prostor imena „invarijanta" je NEKOHERENTAN — isti broj nosi dva različita pravila

**Status:** 🔴 otvoren · **konsolidacija čeka odluku korisnika** · pun search 2026-08-10

Hipoteza je bila da su invarijante **raspršene** po wrapupima (nije rupa, samo nije na
jednom mjestu). **Pun search je pokazao nešto drugo — i gore.**

### Citat pretrage — jedino mjesto koje ih NUMERIRA

```
$ grep -rniE "invarijant[a-zšćžđč]* #[0-9]+ *[—–-]" docs/
docs/faza-4.1-wrapup.md:85: - **Invarijanta #1 — 401 runtime:** …
docs/faza-4.1-wrapup.md:86: - **Invarijanta #2 — TS6 `erasableSyntaxOnly`:** …
docs/faza-4.1-wrapup.md:87: - **Invarijanta #3 — 44px touch-targeti (WCAG 2.5.5):** …

$ grep -rniE "invarijant" docs/faza-4-plan.md CLAUDE.md .claude/ design-system/
(nula pogodaka)
```

Kasniji wrapupi (4.2 §5, 4.3 §5, 4.4b) **imaju isti odjeljak** „Zaključane odluke /
napomene za nasljednike" i u njemu **nabrajaju invarijante — ali BEZ brojeva**, kao obične
natuknice. **Numerirana su samo tri, i to sva tri u 4.1.**

### 🔴 Zato ovo nije „rupa na #5" nego KOLIZIJA

Kod referencira **#1, #2, #3, #4, #6**. Usporedba s jedinim definicijama:

| broj | definicija (`faza-4.1-wrapup.md`) | kod koji se SLAŽE | kod koji PROTURJEČI |
| :---: | --- | --- | --- |
| **#1** | 401 runtime (tipizirana `error` grana je `never`) | `guards.tsx:4` ✅ | 🔴 `MasteryBar.tsx:5,51,58` i `ConceptRow.tsx:4` — koriste #1 za **„border-ani track / progres isključivo kroz MasteryBar"** |
| **#2** | TS6 `erasableSyntaxOnly`, bez parameter-properties | `ErrorBoundary.tsx:5` ✅ | 🔴 `progress.ts:5` i `ModulesPage.tsx:4` — koriste #2 za **„prag iz `/profile.mastery_threshold`"** |
| **#3** | 44px touch-targeti (WCAG 2.5.5) | `pagination.tsx:46` ✅ | — |
| **#4** | **nema definicije** | — | `LoginPage.tsx:2`, `RegisterPage.tsx:2` — „prijava po USERNAME, NE email" |
| **#6** | **nema definicije** | — | `useProfile.ts:4`, `mastery.ts:6`, `MasteryHighlights.tsx:4`, `MasteryCurves.tsx:12`, `ProgressHero.tsx:5`, `LeaderboardPage.tsx:18` — „prag iz `/profile.mastery_threshold`" |

**Dva su broja dvoznačna u samom kodu** (#1 i #2), a **isto pravilo** („prag dolazi iz
`/profile`") nosi **dva različita broja** — #2 na dva mjesta i #6 na šest.

**„#5 je nedodijeljen" je time kriv okvir.** Numeracija nije niz s rupom nego **tri
definirana broja plus četiri naknadno izmišljena**, od kojih dva gaze postojeće. `#5`
doista nigdje ne postoji (ni definicija ni referenca), ali to je posljedica, ne uzrok.

### 🔴 Zašto NISAM konsolidirao

Uputa je predviđala raspršenost → „konsolidiraj, nula izmjena komentara u kodu". Pri
koliziji to **nije izvedivo bez diranja komentara**: konsolidirani popis mora odlučiti
**kome pripada #1 i #2**, a koji god izbor padne, **8 datoteka** nosi suprotno značenje.
Tri puta:

1. **Definicije 4.1 su autoritativne** → prenumerirati kolidirajuće komentare
   (`MasteryBar`, `ConceptRow`, `progress.ts`, `ModulesPage`) i dodijeliti #4/#6 brojeve.
   Dira 8 datoteka, ali samo komentare.
2. **Ukinuti brojeve** → komentari referenciraju pravilo opisno („invarijanta: prag iz
   `/profile`"), popis ostaje neimenovan. Najotpornije na ponavljanje, dira istih 8.
3. **Konsolidirati popis, komentare ostaviti** → popis bi tada **dokumentirao koliziju**
   umjesto da je riješi. Najjeftinije, ali ostavlja dvoznačnost u kodu.

**Preporuka: (2).** Prostor imena je već jednom pukao (errata → #49, v. konvencija u
`errata.md`); brojevi bez jednog vlasnika pucaju opet. Opisna referenca nema što slomiti.
**Odluka je korisnikova** — svaka od tri opcija mijenja frontend komentare, što je izvan
onoga što je uputa dopuštala.

---

## N-9 📌 Zaključak za Fazu 6 — higijena komentara u gamifikaciji je SUSTAVNA, ne slučajna

**Status:** 📌 preporuka za Fazu 6 · 2026-08-10

Dva nalaza iz ovog prolaza **nisu dva nepovezana pogotka** — oba su ista klasa defekta, u
istim datotekama:

1. **Netočan docstring** (`gamification_logic.py:43-45`) tvrdi da je streak odvojen od
   XP-a, dok mehanizam kojim se to opravdava (`streak_7` bedž) upravo tu odvojenost
   poništava — **ERRATA #45**. Ispravak je pripremljen i **odgođen** (pun `pytest` +
   `preflight` po politici zamrznutog backenda, a `pytest` zaprlja živu bazu — #40).
2. **Dvije reference na nepostojeći dokument** — „3D nalaz #6" u
   `gamification_logic.py:88` i `gamification_persistence.py:138`. Citat pretrage:
   `grep -rn "3D nalaz" docs/` → **0 pogodaka**; popis nalaza Faze 3D u repou ne postoji
   (`docs/` ima samo `faza-3-plan.md`, bez wrapupa). Backend zamrznut → **nije dirano**.

### Obrazac je poznat — #23 ga je već pokazao

`#23` (DML rupa, `evaluation.py` hardkodirao `dml=False`) preživio je **tri faze** jer
**nikad nije bio pokriven testom**. Ista dinamika vrijedi za dokumentaciju: moduli nastali
**prije Faze 4** imali su **slabiji nadzor komentara i dokumentacije** od frontenda —
frontend je od 4.1 nadalje prolazio kroz inventare (KORAK 0), `/code-review` i 🔒 DOC
politiku, a `backend/agents/` nije prošao nijedan takav prolaz otkad je napisan u Fazi 3.
Otud i to da su **obje** ove netočnosti nađene **uzgred**, dok se tražilo nešto treće — a
ne kroz namjenski prolaz.

### Preporuka

Faza 6 radi **ciljani prolaz nad komentarima i docstringovima**, ne nasumce, nad:

- **`backend/agents/`** — `gamification_logic.py`, `gamification_persistence.py`,
  `evaluation.py`, `persistence.py`, `recommender_agent.py`, `base.py`
- **`backend/bkt/`** — isti period nastanka, ista izloženost
- **`backend/prolog/`** — `badges.pl` je deklarativni mirror koji se **ne konzultira**
  (izrijekom navedeno u zaglavlju); mirror koji nitko ne izvršava tiho zastarijeva

⚠️ **Ispravak putanje iz naloga:** traženo je `backend/app/agents/` i `backend/app/logic/`
— **ni jedna ne postoji**. Stvarne su `backend/agents/` i `backend/bkt/`
(`ls backend/` → `agents alembic app bkt config prolog scripts tests`; `backend/app/`
sadrži `api bridge core db prolog schemas`, bez `logic`). Prolaz bi promašio cilj.

**Kriterij prolaza:** svaka tvrdnja u komentaru koja se može provjeriti — provjeri se; ono
što ne stoji ili se ispravlja ili se označi kao zastarjelo. Isti postupak kao stage 0 ovog
polisha nad `index.css`, samo nad backendom.

---

## N-10 🔴 `ErrorState` posuđuje VERDICT semantiku za sistemsku grešku — stavka za STAGE 2

**Status:** 🔴 otvoren · **nije 4c** (dira komponentu, ne token) · nađeno 2026-08-10

[ErrorState.tsx:28](frontend/src/components/state/ErrorState.tsx#L28) renderira se na
**`bg-incorrect-soft`** uz `border-incorrect/30` i `text-incorrect` ikonu — dakle na plohi
koja u ovom dizajn-sustavu znači **„tvoj odgovor je netočan"** (MASTER §2.2, semantika
verdicta). Ali `ErrorState` ne govori o odgovoru nego o **sustavu**: „Dashboard nije
dostupan", „Ljestvica nije dostupna", „Preporuka nije dostupna".

### Zašto to nije kozmetika pod nenadziranim evalom

Student koji vidi **istu crvenu plohu** za „tvoj SQL je pogrešan" i za „backend je pao"
nema kanal kojim bi razlikovao **vlastiti neuspjeh** od **kvara aplikacije**. Pod
nadzorom bi pitao; asinkrono zaključi da griješi, pa odustane. To ne kvari samo doživljaj
— kvari **podatke**: odustajanje uzrokovano kvarom ulazi u analizu kao slab učinak.

### Doseg — svaki ekran, ne jedan

```
$ grep -rn "<ErrorState" frontend/src --include=*.tsx | cut -d: -f1 | sort | uniq -c
   4 pages/TaskPage.tsx          2 pages/AdminPage.tsx        1 components/task/RunResultPanel.tsx
   3 components/ErrorBoundary.tsx 1 pages/TaskEntryPage.tsx    1 components/profile/MasteryCurves.tsx
   2 pages/ProfilePage.tsx        1 pages/ModulesPage.tsx      1 components/profile/AttemptHistory.tsx
   2 pages/DashboardPage.tsx      1 pages/LeaderboardPage.tsx  1 components/dashboard/ContinueCard.tsx
```

**20 upotreba u 12 datoteka** — Dashboard, Moduli, Profil, Ljestvica, Admin, Task,
TaskEntry, plus `ErrorBoundary` (render crash, bilo gdje). Nema ekrana koji ga ne koristi.

### Popravak postoji i nema potrošača

`--neutral` i **`--neutral-soft`**… ⚠️ **provjereno:** `--neutral` postoji
(`index.css:195` light / `:268` dark), ali **`--neutral-soft` NE postoji** — citat
pretrage: `grep -n "neutral-soft" frontend/src/index.css` → **0 pogodaka**. Postoji samo
`--neutral`. Dakle popravak nije „prebaci na postojeći token" nego **ili** uvesti
`--neutral-soft` (nova vrijednost + mjerenje), **ili** koristiti `bg-muted` +
`border-border` (postojeći neutralni par, `VERDICT_UI.unknown` već tako izgleda:
`FeedbackPanel.tsx:69-71`).

🔴 **Ispravljam vlastitu pretpostavku iz naloga** („`--neutral-soft` postoji i nema
potrošača") — polovica je točna: potrošača nema jer **ni token ne postoji**.

**Zašto ne u 4c:** dira `ErrorState.tsx` (komponentu), a 4c je token-only. Ide u
**STAGE 2 (oporavak od greške)**, gdje se ionako dira `ErrorState` zbog kontakta i
poruke za trajni pad. Tamo se rješava jednim potezom.

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
