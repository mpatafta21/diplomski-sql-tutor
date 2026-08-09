# Faza 4.7 — PRIJEDLOZI TEKSTA ZA `errata.md` (čekaju odobrenje)

**`docs/errata.md` NIJE MIJENJAN.** Ovaj dokument sadrži samo predložene tekstove.
Datum pripreme: 2026-07-26 · grana `faza-4-7-polish`

Tri prijedloga:

1. **§„Opseg implementacije — REZANE faze"** — revizijska bilješka (uklj. opseg motiona, 4d)
2. **#13** — zatvaranje kao limitacija, VLASTITIM obrazloženjem (neovisno o #33)
3. **#24** — revizija: pretpostavka „0 %" pala je s prelaskom na asinkronu evaluaciju (4e)

---

## PRIJEDLOG 1 — revizija §„Opseg implementacije — REZANE faze"

**Gdje:** `docs/errata.md`, **ISPOD** postojećeg odjeljka (linije 62–79). Postojeći tekst
**ostaje nepromijenjen** — trag odlučivanja se ne prepisuje, isti obrazac kao
§„~~Odluke koje čekaju~~".

```markdown
### ⟳ REVIZIJA (2026-07-26) — Faza 4.7 je OŽIVLJENA, 4.6 ostaje rezana

**Što se mijenja:** odjeljak iznad točno opisuje odluku od 2026-07-20, ali je u dijelu koji
se tiče **4.7** nadglasan. Faza 4.7 (visual QA / a11y / responsive / hardening) **više nije
rezana**. Faza 4.6 (motion + WebSocket) **ostaje rezana** i neizmijenjena; umjesto nje je
izvedena 4.6-eval (#37, #38, #39).

**Razlog — promjena strategije evaluacije s NADZIRANE LABORATORIJSKE na ASINKRONU JAVNU.**
Odluka od 2026-07-20 pretpostavljala je nadziranu sesiju: pripremljeni računi, usmene upute
i prisutan autor koji pomaže kad nešto pukne. Evaluacija se sada izvodi na **javnom URL-u**,
sa **samostalnom registracijom** i **bez nadzora**. Nenadzirano sučelje na javnom URL-u nosi
drukčiji rizik nego sučelje kojim se rukuje uz prisutnog autora, pa se mijenja i _što je_
polish:

- Put `/register → prvi login → prazna stanja → prvi zadatak` prestaje biti kozmetika i
  postaje **jedini kanal uputa** — nema usmenog objašnjenja koje bi ga nadomjestilo.
- Oporavak od greške prestaje biti ugodnost i postaje **uvjet da sudionik završi** — nema
  nikoga da ga izvuče.
- Obrazloženje preporuke (#44) više se ne može dati uživo; ako ga UI ne nosi, sudionik ga
  ne dobiva.
- Nepoznat preglednik i nepoznata širina zaslona postaju stvaran rizik (u labosu su bili
  poznati).
- Informiranje sudionika i kontakt postaju obveza sučelja, a ne razgovora.

**Opseg motiona u 4.7 (da se ne pročita kao tiho oživljavanje 4.6):**
4.6 ostaje rezana. Jedina animirana površina dodana u 4.7 je **mobilni navigacijski
drawer**, i to kao posljedica zahtjeva **pristupačnosti** (ispod 768px nije postojala
nikakva navigacija), ne kao motion polish. Gamifikacijski motion (XP count-up, level-up
celebration, badge-unlock, streak flame), page tranzicije, ⌘K paleta i WebSocket **ostaju
neizvedeni**. `framer-motion`/`motion` nisu u `package.json`; sav motion u aplikaciji je
CSS (`tw-animate-css` + motion tokeni iz 4.1b).

**Što ostaje istinito iz odluke 2026-07-20:** obrazloženje da polish ne otključava novu
funkcionalnost i ne utječe na mjerenje vrijedi za **estetski** dio 4.7 (razmaci, poravnanja,
motion). Taj dio je i dalje najniži prioritet i reže se prvi ako rok pritisne. Ono što je
4.7 dobila natrag je **operativna upotrebljivost bez nadzora**, ne uglađivanje.

**Kako se prijavljuje u radu:** u odjeljku o opsegu implementacije navodi se da je 4.6
(motion/WS) rezana svjesno i obrazloženo, a da je 4.7 izvedena u **suženom,
prioritiziranom** obliku vođenom zahtjevima asinkrone javne evaluacije — ne kao puni
vizualni QA prolaz iz plana §4.7. Popis stvarno izvedenog vodi `docs/faza-4.7-korak-0.md` §9
i wrapup 4.7; nepopravljeni nalazi su u `docs/faza-4.7-nalazi.md`.
```

**Uz to traži ispravak (isti diff, uz odobrenje):**
`docs/faza-4-plan.md:18` — „prva se reže 4.6/4.7 polish" → bilješka da 4.7 nije rezana.

---

## PRIJEDLOG 2 — #13 se zatvara kao limitacija, VLASTITIM obrazloženjem

**Gdje:** `docs/errata.md`, red #13 (linija 24). Zamjena statusa i bilješke.

> 🔴 **Kritično za trag odlučivanja:** #13 se **NE** zatvara nasljeđivanjem dokaza iz #33.
> Commit `c12ec31` (4.4b) ih je bio spojio jednom rečenicom — „Token-level, ide uz
> rekalibraciju palete zajedno s partial hue 60→45" — iako s #33 nema veze: #33 je o
> **mastery gradijentu** (kontrast donjih stopova), #13 je o **hue blizini partiala i
> accenta**. Kad je #33 odbačen matematičkim dokazom, #13 je otišao s njim bez vlastite
> presude. Ovo je ispravlja.

```markdown
| #13 | Partial hue 55–60 preblizu accent-warm 70–85 | 📌 **prihvaćeno kao limitacija (4.7)** | **Zatvoreno VLASTITIM obrazloženjem, neovisno o #33** — v. bilješku niže |
```

Bilješka (ide u tijelo errate, ispod tablice ili kao podnožje reda):

```markdown
**#13 — zašto se korekcija hue→45 NE izvodi (odluka 4.7, 2026-07-26)**

1. **Mitigacija je izmjerena i drži.** Ikona + tekstualna oznaka su OBAVEZAN kanal
   (MASTER §2.2), pa boja **nije nosilac informacije** nego pojačanje. Izmjereno
   2026-07-26 (alpha-kompozitirano): `text-partial` u svom STVARNOM kontekstu
   (`bg-partial-soft` u FeedbackPanelu) daje **4,86:1 light / 8,03:1 dark**; vs `card`
   **5,48:1 / 8,68:1**. Oboje prolazi WCAG AA. Verdict „Djelomično" nosi `TriangleAlert`
   ikonu i tekstualnu oznaku u svakoj grani (`FeedbackPanel.tsx`, `verdict-ui.ts`).

2. **Korekcija je izvediva, ali ne besplatna.** Pomak na hue 45 dira **4 datoteke i
   0 komponenata** (`index.css` ×4 vrijednosti, `MASTER.md` §2.2 + §2.7, errata) —
   komponente vuku `text-partial`/`bg-partial-soft`/`border-partial` pa promjena tokena
   propagira sama. Hue udaljenosti bi se popravile prema accentu i pogoršale prema
   `incorrect`: light 55→45 znači Δ do accenta 15→**25**, a Δ do `incorrect` 30→**20**;
   dark 60→45 znači Δ do accenta 20→**35**, Δ do `incorrect` 35→**20**.

3. **Cijena je ponovno otvaranje SSOT-a neposredno pred deploy.** MASTER §2.7 točka 4
   propisuje hue mapu sustava (**25 incorrect · 55 partial · 70–85 accent · 150 correct ·
   190–260 mastery · 300 tier · 345 difficulty**). Pomak partiala prepisuje tu mapu, a
   po 🔒 DOC politici traži **novo mjerenje cijele skale** u obje teme, ne samo partiala.

4. **Korist je neprimjetna.** Boja ionako nije jedini kanal (t. 1), pa se korisniku ništa
   ne mijenja. Uz to se partial prikazuje na **eval-verificiranom** FeedbackPanelu (4.3c,
   živo verificiran) — dodir bez funkcionalne koristi je čisti regresijski rizik.

**Status: 📌 prihvaćeno kao limitacija.** Nijedna vrijednost tokena nije mijenjana.
Kandidat za Fazu 6 uz punu remjeru palete, zajedno s #33 i N-4 (prsten fokusa 2,59:1 light) —
ali kao **tri odvojena nalaza s odvojenim obrazloženjima**, ne kao jedan paket. Spajanje je i
dovelo do ovog propusta.
```

---

## PRIJEDLOG 3 — #24 TRAŽI REVIZIJU (asinkrona evaluacija mijenja pretpostavku)

### 3.1 Stvarni kriterij — pročitan iz koda, ne iz errate

**`streak_7` traži `current_streak >= 7`**, gdje je `current_streak` **broj uzastopnih
KALENDARSKIH dana s barem jednim pokušajem, koji završava danas**.

`backend/agents/gamification_logic.py:241`:

```python
if facts.current_streak >= 7:
    earned.add("streak_7")
```

`backend/agents/gamification_logic.py:186-191` (`streak_from_active_dates`):

```python
# current: brojimo unatrag od danas dok su dani uzastopni.
current = 0
cursor = today
while cursor in active_dates:
    current += 1
    cursor -= timedelta(days=1)
```

`active_dates` = skup datuma s barem jednim pokušajem, u zoni **Europe/Zagreb**
(docstring: „Datumi su VEĆ u ciljnoj zoni (Europe/Zagreb)"). Deklarativni mirror u
`backend/prolog/badges.pl:22-23` govori isto:

```prolog
user_badge(UserID, streak_7) :-
    current_streak(UserID, N), N >= 7.
```

Seed tekst (`app/db/seed_data.py`): „7 uzastopnih dana aktivnosti.", `xp_reward: 30`.

✅ **Opis kriterija u #24 je TOČAN.** Ono što pada je **zaključak** o dostižnosti.

### 3.2 Svi bedževi s vremenskom komponentom

Pun katalog je **5 bedževa** (`seed_data.py:177-240`, `eval_badges()` u
`gamification_logic.py:226-247`):

| Bedž            | Kriterij (iz koda)                                             | Vremenska komponenta               | Bila vezana na model „jedna sesija"?                                                  |
| --------------- | -------------------------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------- |
| `first_correct` | `facts.has_correct` — bilo koji točan pokušaj                  | **nema**                           | ne                                                                                    |
| `join_master`   | `{inner_join, left_join, right_join} ⊆ mastered` (P(L) ≥ 0.85) | **nema**                           | ne — problem je bio **podatkovni** (#25/#27, `right_join` subfloor), riješen u 4.4-0h |
| **`streak_7`**  | `current_streak >= 7` — **7 uzastopnih kalendarskih dana**     | **DA, kalendarski dani**           | 🔴 **DA — jedini**                                                                    |
| `null_ninja`    | `"null_handling" in mastered`                                  | **nema**                           | ne                                                                                    |
| `explorer`      | `evaluable_modules ⊆ attempted_modules`                        | **nema** (broj modula, ne vrijeme) | ne — ali v. 3.3                                                                       |

**Nijedan drugi kriterij nije implicitno vezan na trajanje sesije.** `streak_7` je jedini
koji mjeri **kalendarsko vrijeme**; ostala četiri mjere **ishode** (točnost, ovladanost,
pokrivenost modula) koji ne poznaju pojam dana.

Provjera po tragu #22 (`explorer` je već jednom bio nedostižan zbog hardkodirane
pretpostavke `{1..6}`): kriterij je od 4.4-0f **dinamičan** — `evaluable_modules` su moduli
(≠0) koji stvarno imaju aktivne zadatke, uz fail-closed guard na prazan skup
(`gamification_logic.py:244-246`). Nema fiksne brojke koja bi mogla ostariti.

### 3.3 Empirijski podatak (mjereno 2026-07-26)

`seed_demo_user` odradio je **27 attempta u JEDNOM danu** (streak 1/1) → osvojeno
**`['first_correct', 'explorer']`**, dakle 2 od 5.

- `explorer` je osvojen **unutar jednog dana** → potvrđeno da NIJE vezan na trajanje.
- `streak_7` nije osvojen, kako i mora biti pri streaku 1.
- `join_master` i `null_ninja` nisu osvojeni — ovladanost, ne vrijeme.

Zanimljiva veza: `explorer` traži pokušaj u **svakom** evaluabilnom modulu, a preporučivač
je **breadth-first** (#44 — skače među temama). Ta dva se poklapaju: ponašanje koje
studentu izgleda kao nepovezan skok upravo je ono što `explorer` čini lako dostižnim.

### 3.4 Predložena revizija #24

```markdown
| #24 | `streak_7` traži 7 KALENDARSKIH dana | 📌 **dizajn — REVIDIRAN 2026-07-26** | Kriterij nepromijenjen; **pretpostavka o dostižnosti je revidirana** uz prelazak na asinkronu evaluaciju. V. bilješku |
```

Bilješka:

```markdown
**#24 — revizija pretpostavke (2026-07-26)**

Izvorni zapis tvrdio je „horizont bedža je dulji od trajanja evaluacijske sesije →
**očekivana stopa osvajanja 0 %**". Ta je tvrdnja bila točna **pod modelom nadzirane
jednokratne laboratorijske sesije**, gdje sudionik sustav vidi jedan dan. **Taj model više
ne vrijedi:** evaluacija se izvodi asinkrono preko javnog linka, sudionici rade u vlastitom
ritmu kroz dane ili tjedne. Time `streak_7` prestaje biti nedostižan **po konstrukciji**.

**Kriterij se NE mijenja** (backend zamrznut, #49; i nema potrebe). Mijenja se **status u
analizi gamifikacije**:

- prije: 0 % je bila **predvidljiva posljedica dizajna eksperimenta**, izvještavala se kao
  takva, bez informacijske vrijednosti;
- sada: stopa osvajanja je **mjerena varijabla** — pokazatelj _održanog_ angažmana kroz
  dane, a ne trenutne aktivnosti. To je jedini bedž u katalogu koji to mjeri (v. tablicu
  vremenskih komponenti — ostala četiri mjere ishode, ne vrijeme).

⚠️ **Dostižan ≠ vjerojatan.** Kriterij je strog: 7 **uzastopnih** dana, **bez ijednog
propuštenog**, svaki s barem jednim pokušajem. Sudionik koji odradi studiju kroz dva tjedna
s prekidima ne osvaja bedž. Očekivana stopa ostaje **niska**, ali je sada **empirijsko
pitanje**, ne unaprijed poznat nula. U radu se izvještava izmjerena stopa uz ovu napomenu o
strogosti kriterija.

⚠️ **Prijetnja usporedivosti (novo, posljedica revizije):** `streak_7` nosi 30 XP
(`seed_data.py`), a XP ulazi u level i u ljestvicu. Dva sudionika s **identičnim** brojem
točnih rješenja mogu se razlikovati u XP-u samo po tome je li rad raspoređen na 7 uzastopnih
dana ili zbijen u jedan. Pod jednokratnom sesijom taj efekt nije postojao (nitko nije mogao
osvojiti bedž). Pri usporedbi sudionika i pri interpretaciji ljestvice XP treba čitati uz
badge-strukturu, ne kao čistu mjeru uspješnosti. Srodno #9 (kohortna izolacija) i
🔒 politici da se XP autoritativno čita iz `/profile`.

**Ostaje netaknuto:** `streak_7` je i dalje svjestan dugoročni retention element, ne defekt.
Bedž se ne mijenja.
```

---

## PRIJEDLOG 4 — `MASTER.md` §5 Motion: tri zastarjele najave rezane Faze 4.6

**Status prijedloga 1–3: PRIMIJENJENI** 2026-08-09 (commitovi `docs(4.7): #46 …` i
`docs(4.7): revizija opsega, #13 …`). Ovaj prijedlog **NIJE primijenjen** —
`design-system/sql-tutor/MASTER.md` je **nedirnut**, čeka OK.

### Zašto se ovo ne može otpisati kao „posljedica iste odluke"

U commitu `e05c6de` (stage 4c) ista je klasa netočnosti popravljena u `index.css`, a
MASTER.md je tada **ostavljen** uz obrazloženje „posljedica iste odluke, ne zaseban
defekt". **To obrazloženje ne stoji.** `index.css` čita razvijač koji već radi na
datoteci; **`MASTER.md` je SSOT dizajn-sustava koji CC čita na početku svake sljedeće
faze** (Faza 5, deployment). Zastarjela najava u SSOT-u nije komentar nego **uputa
budućem izvođaču**: „bez framer-motion **do 4.6**" čita se kao „u 4.6 dolazi", pa budući
izvođač očekuje motion lib koji nikad ne dolazi i `/review-animations` gate koji nikad
nije bio globalno pokrenut.

Pristup je **isti kao kod `index.css:139`**: vrijednost/token **ostaje**, mijenja se samo
opis — iz najave rada u opis zatečenog stanja.

### Zatečeno → predloženo, doslovno

**Linija 181** — uvodna rečenica tablice motion tokena.

Zatečeno:

```markdown
Tokeni u `@theme` (vrijednosti; bez framer-motion do 4.6):
```

Predloženo:

```markdown
Tokeni u `@theme` — **samo vrijednosti**. Motion lib (`framer-motion`/`motion`) **nije u
`package.json` i ne dolazi**: Faza 4.6 (motion + WebSocket) je REZANA (v. `docs/errata.md`,
§„Opseg implementacije — REZANE faze" + revizija 2026-08-09). Sav motion u aplikaciji je
CSS — `tw-animate-css` (`animate-in`, `fade-in`, `slide-in-*`) + ovi tokeni. Dodavanje
motion liba traži izričitu odluku, nije zatečeni plan:
```

**Linija 193** — redak `--duration-reward` u tablici.

Zatečeno:

```markdown
| `--duration-reward` | `700ms` | gamifikacijski momenti (count-up envelope) |
```

Predloženo:

```markdown
| `--duration-reward` | `700ms` | ⚠️ **NEKORIŠTEN** — bio rezerviran za count-up envelope NEIZVEDENE Faze 4.6 (provjereno grepom 2026-07-26: 0 pogodaka na `duration-reward` u `frontend/src`). OSTAJE radi cjelovitosti ljestvice instant→fast→base→slow→reward, ne kao najava rada |
```

> Napomena: `--ease-reward` (linija 188) se **NE** dira — on **jest** korišten
> (`FeedbackPanel.tsx:130` XP čip, `:169` level-up, `:185` badge unlock). Redak ostaje
> kakav jest da se ta dva tokena ne zamijene.

**Linija 197** — završetak rečenice o pravilima.

Zatečeno:

```markdown
Pravila: sve animacije poštuju `prefers-reduced-motion` · bez layout-shift hovera (translateY max 1–2px,
nikad scale koji pomiče susjede) · reward animacije SAMO na accent-warm događajima · svaka animacija
prolazi `/review-animations` gate (4.3/4.6).
```

Predloženo:

```markdown
Pravila: sve animacije poštuju `prefers-reduced-motion` · bez layout-shift hovera (translateY max 1–2px,
nikad scale koji pomiče susjede) · reward animacije SAMO na accent-warm događajima · svaka animacija
prolazi `/review-animations` gate.

⚠️ **Doseg gatea, zatečeno stanje:** `/review-animations` je stvarno pokrenut **samo nad
Task screenom** (4.3). Faza 4.6, koja ga je trebala pokrenuti globalno, je REZANA →
globalni prolaz **nikad se nije dogodio** i ne planira se. `prefers-reduced-motion` je
pokriven **univerzalnim** guardom u `index.css` (`@media (prefers-reduced-motion: reduce)`
nad `*`), ne per-komponentnim opt-inom, pa pravilo vrijedi i bez gatea. Za svaku NOVU
animiranu površinu gate ostaje obavezan.
```

### Opseg i rizik

| | |
| --- | --- |
| Datoteka | `design-system/sql-tutor/MASTER.md` — **jedna** |
| Linije | 181, 193, 197 (+ jedan dodani odlomak uz 197) |
| Izmjena vrijednosti tokena | **NULA** — mijenjaju se samo opisi |
| Rizik nad eval-verificiranim putem | 🟢 **NULA** — dokument se ne kompajlira ni ne servira |

---

## Sažetak — što traži tvoj OK

| #   | Prijedlog                                   | Zahvat                                        | Status                      |
| --- | ------------------------------------------- | --------------------------------------------- | --------------------------- |
| 1   | Revizija §REZANE faze (uklj. opseg motiona) | **dodaje** odjeljak; postojeći tekst netaknut | ✅ **primijenjen** 2026-08-09 |
| 2   | #13 → 📌 limitacija, vlastito obrazloženje  | mijenja status reda #13 + dodaje bilješku     | ✅ **primijenjen** 2026-08-09 |
| 3   | #24 → revidirana pretpostavka               | mijenja status reda #24 + dodaje bilješku     | ✅ **primijenjen** 2026-08-09 |
| 4   | `MASTER.md` §5 Motion — tri zastarjele najave | mijenja 3 linije opisa, nula vrijednosti    | 🔴 **ČEKA OK**              |

Uz njih, izvan errate: `docs/faza-4-plan.md:18` („prva se reže 4.6/4.7") — **također
nedirnut**, čeka odluku ide li ispravak ili bilješka.

**Prijedlog 4 nije primijenjen.** `MASTER.md` i `faza-4-plan.md` su nedirnuti —
`git diff --stat HEAD -- design-system/sql-tutor/MASTER.md docs/faza-4-plan.md` je prazan.
