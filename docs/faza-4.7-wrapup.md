# Faza 4.7 — wrapup

**Razdoblje:** 2026-07-26 (oživljavanje faze) → 2026-08-11 (zatvaranje)
**Grana:** `faza-4-7-polish` · **72 commitova** od `main` · 87 datoteka, +10 346 / −752
**Zatvoreno tagom:** `faza-4-7-complete`

> Ovaj dokument je zapis onoga što je isporučeno, izmjereno, odbijeno i ostalo otvoreno.
> Brojke su izmjerene, ne procijenjene; uz svaku stoji datum mjerenja. Ondje gdje je
> mjerenje demantiralo raniju tvrdnju, ostaje i tvrdnja i demanti.

---

## 1. Dokaz o opsegu: backend nije dirnut

Zamrznuće backenda (od 4.4-0f) drži kroz cijelu fazu:

```
$ git diff --stat main...HEAD -- backend/
(prazno)

$ git diff --stat main...HEAD -- 'frontend/src/lib/api/schema.d.ts'
(prazno)
```

**Nula izmjena u `backend/`, `schema.d.ts` byte-identičan.** Sve što je faza promijenila je
prezentacijski sloj, dokumentacija i jedan e2e test. Jedina nova ovisnost u cijeloj fazi je
`canvas-confetti` (4,20 kB gzip, odgođeni chunk — početni bundle nepromijenjen).

---

## 2. Isporučeno po stageu

### Stage 0–2 (2026-07-26 → 2026-08-10)
Metapodaci i informacija sudionika (`lang="hr"`, title/og, uputa i kontakt na `/register` i
Profilu) · mobilna navigacija ispod 768 px (N-5 zatvoren) · ink-indigo paleta (hue 280) ·
display font i mono identitet · dot-grid i glow · gradijenti na chromeu.

### Stage 3, dio A — površine (tag `faza-4-7-r3-povrsine`)

Uveden **drugi kriterij za dekorativne slojeve**: dotad se mjerilo samo „ne smije pokvariti
kontrast", sada i „mora se vidjeti", pikselno na snimci žive aplikacije, prag Δ ≥ 15 po
sRGB kanalu.

| površina | prije | poslije | pikselni Δ (R·G·B) |
|---|---|---|---|
| dot-grid | α 3,5 % | **12 %** | 7·7·7 → **21·21·23** |
| glow | α 6 % / 4 % | **18 % / 12 %** | 4·4·7 → **13·14·21** |
| CTA gradijent | L 0,90 C 0,045 | **L 0,85 C 0,065** | 24·22·2 → **40·37·5** |

Kontrast unatrag na najgoroj točki (2026-08-10): `foreground` **11,31** · `muted-foreground`
**4,74** konzervativno; u kadru (glow × 0,62) **12,77** / **5,35**. Glow je zaustavljen na
18 % iako bi 24 % podiglo sve kanale — ta kombinacija ruši `muted-foreground` na 4,24.

Uz to: gradijent plohe sidebara i drawera · gradijent kartica + hairline (min ΔE prema svim
skalama **0,20**) · korisnička kartica u topbar (obrat 1C t.2, N-17).

### Stage 3, dio B — Faza 4.6 (tagovi `faza-4-6-b1…b5`, `faza-4-6-complete`)

Faza 4.6 je od 2026-07-20 vodila kao rezana; izvedena je **osim WebSocketa, ⌘K palete i
page tranzicija**. Bez `framer-motion` — sve CSS + minimalni JS kroz postojeće motion tokene.

| skupina | isporučeno |
|---|---|
| B.1 hover/press | lift kartica + sjena; nav stavke klize u stranu, ikona 1,08 |
| B.2 entrance stagger | kaskadni ulaz 60 ms; **nigdje na Task ekranu** |
| B.3 nav indikator | klizni pill, pozicija iz `offsetTop`, radi i u draweru |
| B.4 progres i streak | trake se pune od nule; plamen 3 × 600 ms = 1,8 s |
| B.5 povratna sprega | XP count-up, puls levela + konfeti, otključavanje bedža |

**B.5 je jedini dodir eval-verificiranog puta** i re-verificiran je ručno na živom
agentskom lancu poslije svake izmjene (v. §4).

### Zatvaranje (2026-08-11)

N-11 (mrtvi CTA) · N-10 (`ErrorState` na `neutral-soft`) · #44 (obrazloženje izmjene teme) ·
A.1c (curenje trajanja) · zraka pod reduced-motion · presnimljene figure · errata #55–#58 ·
nalazi N-18, N-19.

---

## 3. Izmjerene vrijednosti (sve 2026-08-10 / 08-11)

### Motion — nakon popravka N-18

| element | trajanje | | element | trajanje |
|---|:---:|---|---|:---:|
| nav stavka | 0,16 s | | panel ocjene | 0,24 s |
| kartica (hover) | 0,24 s | | gumb (press) | 0,10 s |
| ulazna animacija | 0,40 s | | XP zraka | 2 s (1,3 s prolaz) |
| drawer (ulaz) | 0,24 s | | count-up XP | 0,70 s |

### Kontrast pod staklom (metoda dviju snimki, tekst prozirni)

| kadar | najgori tekst | kontrast |
|---|---|:---:|
| desktop sidebar | „Moduli" nad rgb(21,22,38) | **6,86** ✅ |
| drawer nad CTA gumbom + scrim | badge „student" | **5,86** ✅ |

Na desktopu ispod sidebara **ništa ne prolazi** — preklapanje s `main` je 0 px, a pozadina
je `background-attachment: fixed`, pa je kompozit isti na svakoj ruti.

### Skale razina (hue rampe)

Susjedne razine: tier 0,1011 / 0,1238 · difficulty 0,1027 / 0,0588 / 0,0696 / 0,1102.
Unakrsno tier × difficulty: **0,3754** (razdvojeni registrom, ne hueom).
Tekst na fillu: tier 7,60–8,91 · difficulty 8,49–10,58.
Min prema ostalim skalama: **0,0643** (`difficulty-beginner × mastery-0`) — v. §5.

### Bundle

| | prije | poslije |
|---|---|---|
| početni JS | 495,84 kB (152,75 gzip) | **496,12 kB** (152,68 gzip) |
| CSS | 64,69 kB (13,96 gzip) | 68,64 kB (14,71 gzip) |
| konfeti | — | 10,57 kB **odgođeni chunk** (4,20 gzip) |

---

## 4. Re-verifikacija eval-verificiranog puta

Sva četiri stanja panela s ocjenom, na živom agentskom lancu, nakon **svake** izmjene koja
ga je dirala (B.5, N-11, #44) — 2026-08-11:

| stanje | XP | oznake | CTA |
|---|---|---|---|
| Netočno | bez čipa | — | **„Pokušaj ponovno"** (N-11 grana) |
| Djelomično | +8 XP (10 × 0,5 × 1,5) | — | „Pokušaj ponovno" |
| Točno | +10 XP | bedž otključan | „Sljedeći zadatak" |
| Već riješeno | bez čipa | „Već riješeno · bez XP" | „Sljedeći zadatak" |
| Level-up | +20 XP | „Novi level — 2!" | konfeti ✓ |

XP aritmetika odgovara backend formuli — **formula nije dirnuta**. Rečenica #44 prisutna u
svim stanjima. Konfeti pod `prefers-reduced-motion`: chunk **nije ni zatražen**, canvas 0.

---

## 5. Što je odbijeno i zašto

**PRIJEDLOG F (skale razina uz ΔE ≥ 0,10)** — izračunat, provjeren, **nije primijenjen**.
Prag 0,10 bio je ad hoc kriterij iz recenzije; projektni prag je **0,05**, koji sve
sadašnje vrijednosti prolaze. Zamrznuta skala je i sama imala tri para ispod 0,10 i susjede
na 0,0583. Regresija se ne prešućuje: `difficulty-beginner × mastery-0` pao je s **0,1101 na
0,0643**, uz poboljšanje na osi susjednih razina. Uz to je mjerenjem pokazano da je taj par
**teško dosežan na zaslonu**: `mastery-0` (p(L) < 0,125) nedostižan je za easy (donja
granica 0,3358) i medium (0,2286), a `difficulty-beginner` badge nosi isključivo modul sa
samo easy konceptima → par se **ne može pojaviti u istoj kartici**. Pune vrijednosti F-a
stoje u errati #56 kao kandidat za Fazu 6.

**Odluka „nula konfeta" (4.3)** — svjesno **povučena** 2026-08-10, s razlogom i datumom:
literatura mehanizam gamifikacije opisuje kao *istaknutost* povratne sprege, a sustav je
dotad imao tihe brojke. Konfeti idu samo na level-up; „konfeti-spam" (MASTER §8) ostaje
zabranjen.

**Page tranzicije (B.6)** — rezane unutar dijela B: entrance stagger već animira ulaz
svake ne-Task stranice, a Task ekran mora ostati bez ulazne animacije.

**Puni reset editora uz „Pokušaj ponovno"** — odbijen: student koji je pogriješio obično je
blizu rješenja; brisanje njegova upita kaznilo bi upravo onoga koga popravak štiti.

---

## 6. Otvoreni nalazi, s vlasnikom

| nalaz | status | vlasnik / odluka |
|---|---|---|
| **#46 — brisanje pojedinog sudionika nije dokazano izvedivo** | 🔴 **BLOKATOR prije slanja linka** | Korisnik: (a) izgraditi i verificirati proceduru, ili (b) preformulirati obećanje na Profilu. `agent_messages_log` nema `user_id`; briše se samo `TRUNCATE`-om |
| **N-19 — level i streak dvaput u kadru** | 🟡 zatečeno od 1C t.2, nije popravljeno | Korisnik: uvjetovani chrome / hero bez levela i streaka / sužena invarijanta na XP |
| #13 — partial hue blizu accent-warm | 📌 prihvaćeno kao limitacija | Ikona + tekst su obavezan kanal, boja je pojačanje |
| #33 — `border`/`input` ne dosežu 3:1 | 📌 prihvaćeno kao limitacija | Doseći 3:1 traži alfu 48–50 % = drugi vizualni jezik |
| N-4 — prsten fokusa | 🟡 token-level, izvan 4.7 | Tokeni zamrznuti |
| #52 — `--destructive` pada 3:1 | 🟡 mjereno, nije regresija | Jedini dosežni render je obrub nevaljanog polja; tekst greške nosi značenje |
| #53 — sustav nema WARNING semantiku | 🔴 strukturni | Traži novi token → Faza 6 |
| **PRIJEDLOG F** | 📐 izračunat | Kandidat za Fazu 6, vrijednosti u errati #56 |

---

## 7. 🔴 Metodološki zaključak faze

**Projekt ima mjerni instrument za jednu dimenziju — boju — i nijedan za vrijeme,
dosežnost i izvršenje.** To je najprenosiviji rezultat 4.7, i jedini koji ne ovisi o ovom
sučelju.

`scripts/a11y/` mjeri kontraste i ΔE do razine alpha-kompozita. Ništa nikad nije mjerilo
koliko nešto traje, doseže li se uopće i izvršava li se. U tim dimenzijama kvarovi su
preživjeli po **tri faze**:

| primjerak | deklarirano | stvarno | trajanje |
|---|---|---|---|
| `--font-heading` | „0 potrošača" | dva potrošača, alias bez učinka | do 1C |
| `--duration-*` (**N-18**) | 160/240/400/700 ms | **sve na 150 ms** (klase se nisu generirale) | tri faze |
| **#23** `dml=False` | evaluator podržava DML | svaki DML „permission denied", bez testa | tri faze |
| **smoke suite** (#57) | „CTA je link" | asertacija je snimila **kvar** kao ugovor | od 1B |

Zajednički obrazac, i za rad najvažnija rečenica:

> **Instrument kalibriran prema zatečenom stanju potvrđuje zatečeno stanje.**

Grep po imenu nalazi deklaraciju, ne učinak. Gate proveden nad zatečenim sustavom odobrava
zatečeni sustav. Test pisan promatranjem sučelja zaključava sučelje, uključujući njegove
kvarove. Dokaz o učinku ima tri oblika i **nijedan nije grep**: `getComputedStyle` nad živim
elementom, pikselno mjerenje snimke, i test koji izvrši put.

Praktična posljedica koju faza ostavlja iza sebe: pikselni kriterij vidljivosti (A.1),
metoda mjerenja kompozita ispod `backdrop-filter` (`scripts/a11y/README`), pravilo o
eksplicitnom trajanju i easingu uz grep-provjeru u oba smjera (MASTER §5), i zahtjev da
svaka nova asertacija odgovori na pitanje *„je li ovo očekivanje izvedeno iz zahtjeva ili
prepisano s ekrana?"*.

---

## 8. Kapije na zatvaranju (2026-08-11)

`tsc -b` ✅ · `vite build` ✅ · `oxlint` ✅ · `prettier` ✅ · matrica kontrasta ✅ ·
`monaco_check.py` ✅ · `schema.d.ts` byte-identičan ✅ · backend 0 izmjena ✅ ·
`npm run e2e` ✅ (uz ažuriran smoke — v. #57).

**N-3, trag u `agent_messages_log`:** 1575 (početak stagea 3) → **3063** (zatvaranje).
Zapisi nemaju `user_id`; brišu se isključivo `TRUNCATE`-om u `prepare_eval_baseline.py`
prije evaluacije. Svi `e2e_` i `demo44_` računi su počišćeni (0 preostalih).

**Figure:** svih 7 presnimljeno 2026-08-11 (metoda i brojke u `docs/figures/README.md`);
dvije light snimke obrisane jer light tema ne postoji.
