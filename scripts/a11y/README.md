# `scripts/a11y` — ponovljivo mjerenje kontrasta

Alat za mjerenje WCAG kontrasta nad **stvarnim** tokenima iz `frontend/src/index.css`.

## Zašto je ovo u repou

Prva verzija ovog harnessa (Faza 4.7-4c) živjela je u scratchpadu i **nestala je između
sesija** — pa je za sljedeće mjerenje trebalo pisati sve ispočetka. Ista klasa kao #17
(e2e verifikacije bez runnera), #20 (task bank izvan verzije) i #38 (slike za rad u
scratchpadu): mjerenje koje nije u repou nije mjerenje nego anegdota.

S promjenom palete mjerenje se ponavlja pri **svakoj iteraciji**, pa mora biti jedna
naredba, a ne ručni posao.

## Naredbe

```bash
# puna matrica u terminal — izlazni kod 1 ako išta padne
python3 scripts/a11y/contrast_matrix.py

# markdown za docs/faza-4.7-kontrast-matrica.md
python3 scripts/a11y/contrast_matrix.py --md > docs/faza-4.7-kontrast-matrica.md

# jedan par, brzo tijekom iteriranja palete
python3 scripts/a11y/contrast_matrix.py --pair muted-foreground incorrect-soft
python3 scripts/a11y/contrast_matrix.py --pair accent-warm-text accent-warm/20

# ΔE nad SUKORIŠTENIM parovima — cross-scale guard (MASTER §2.7)
# izlazni kod 1 ako ima neprihvaćene kolizije
python3 scripts/a11y/contrast_matrix.py --delta-e
python3 scripts/a11y/contrast_matrix.py --delta-e --md   # sve, i ✅ retke

# je li Monaco tema još u skladu s tokenima
python3 scripts/a11y/monaco_check.py
```

Bez dependencyja — čisti Python 3.11 iz standardne biblioteke.

## Datoteke

| Datoteka | Uloga |
| --- | --- |
| `palette.py` | oklch → sRGB, WCAG omjer, **ΔE (Oklab)**, gamut-upozorenje, **parser `index.css`**, samotest konvertora |
| `pairs.py` | **podaci**: plohe, stvarni parovi s citatima, čipovi, pragovi, **sukorišteni skup** |
| `contrast_matrix.py` | CLI: puna matrica / jedan par / **ΔE** / markdown |
| `monaco_check.py` | drift između `monaco-theme.ts` (hex kopija) i tokena |

## Tri pravila koja alat utjelovljuje

**1. Tokeni se ČITAJU iz `index.css`, ne hardkodiraju.** Zato alat preživi promjenu
palete: promijeni `index.css`, pokreni istu naredbu, dobiješ nove brojke. Ako se
struktura CSS-a promijeni (očekuje se `:root` → `@layer base`), parser **prekida s
greškom** umjesto da tiho vrati krive brojke. Od 4.7 je aplikacija **dark-only**: pojava
`.dark` bloka također je prekid, jer bi značila da parser čita samo pola palete.

> 🔴 **Prolaz izvršen tijekom nestabilne infrastrukture PONAVLJA SE prije nego uđe u
> `nalazi.md`.** Povod (4.7-r2, t.0a): zapisao sam da `Collapsible` u `ModuleCard` ne
> otvara koncepte klikom — na temelju jednog neuspjelog prolaza koji je pao **odmah nakon
> što su docker kontejneri i backend pali usred sesije i bili ponovno dignuti**. Ponovna
> provjera (14 pokušaja, 4 uvjeta) pokazala je da komponenta radi savršeno, uključujući
> tipkovnicu. Nalaz je povučen. Šum u `nalazi.md` skuplji je od šutnje jer se čita kao dug.

**2. Konvertor se validira prije svakog mjerenja.** `SELF_TEST` u `palette.py` nosi šest
brojki koje su **objavljene u dokumentaciji projekta prije nego je ova skripta
postojala** (npr. `foreground × card` = 17,16). Ako ih konvertor ne reproducira, skripta
**izlazi s kodom 2** i ne mjeri ništa. Poučak iz #39: guard koji nije testiran u oba
smjera nije guard.

> Kad se paleta namjerno promijeni, dio `SELF_TEST` brojki će pasti — to je **očekivano**.
> Tada se `SELF_TEST` ažurira **uz obrazloženje u commitu**, i tek nakon što je nova
> brojka provjerena ručno. Nikad „samo da prođe".

**3. Mjere se samo STVARNI parovi, ne kartezijev produkt.** Prvi pokušaj iscrpne matrice
išao je produktom i dao **40+ lažnih padova** (npr. `text-foreground` na `bg-primary` =
1,21:1 — par koji ne postoji, jer za tu plohu služi `primary-foreground`). Provjera koja
utopi prave padove u lažnima jednako je neupotrebljiva kao ona koje nema (🔒 DOC, #50).

### Oznake dokaza

| Oznaka | Značenje |
| :---: | --- |
| **●** | ploha i tekst su u **istom `className`** — dokazano čitanjem koda |
| **○** | tekst je u **podstablu** elementa koji nosi plohu — naslijeđeno |

Svaki par nosi citat (`Datoteka.tsx:redak`). **Bez citata se par ne dodaje** — tvrdnja bez
dokaza je ista klasa kao tvrdnja bez plohe.

## Kako dodati novi par

1. nađi ga u kodu: `grep -rn "bg-<ploha>" frontend/src` pa pročitaj koji tekst tokeni
   stoje na njemu (u istom `className` ili u podstablu);
2. ako ploha nije u `SURFACES` (`pairs.py`), dodaj je — alpha-varijante idu kao
   `("token", alpha, "ploha-ispod")`, jer se mjeri **kompozit**, ne čist token;
3. dodaj redak u `PAIRS` s oznakom ● / ○ i citatom;
4. pokreni `contrast_matrix.py` i provjeri da je izlaz očekivan.

Ako je „tekst" zapravo **ikona** (nema glifova), upiši par u `GRAPHIC_ONLY` → prag postaje
3,00 umjesto 4,50.

## Druga mjera: ΔE nad sukorištenim parovima

**Kontrast i ΔE odgovaraju na različita pitanja.** Kontrast: *„vidi li se ovo na ovome?"*
ΔE: *„razlikuju li se ovo dvoje?"* Druga mjera postoji zbog cross-scale guarda
(MASTER §2.7): kroma-token (`ring`, `primary`, ploha…) **ne smije se čitati kao član
semantičke skale** — inače tier-čip i gumb postanu ista boja i skala prestane značiti.

### 🔴 Mjeri se SAMO sukorišteni par (NALAZ N-12)

Prva verzija računala je ΔE do **najbližeg semantičkog tokena uopće**. To je pogrešna
mjera i dala je **obrnut odgovor**: `--ring` je pod njom ispao lošiji kao akromatski
(0,067) nego kao tintan (0,102), jer mu je „najbliži" bio `difficulty-cross-module` — a
`DifficultyChip` **nije ni na jednom fokusabilnom elementu**, pa se s prstenom nikad ne
renderira zajedno.

**Sukorišten = renderira se na istom elementu ili mu je neposredno susjedan.**

| izvor | što daje |
| --- | --- |
| `PAIRS` (izvedeno) | tekst na plohi ⇒ sukorišten je s tom plohom **i** s ostalim tekstom na njoj |
| `CO_USED_EXTRA["ring"]` | što god živi **unutar** fokusabilnog elementa (PAIRS ne poznaje fokus) |
| `CO_USED_EXTRA["primary"]` | gumb: tier čipovi na istom ekranu, `-soft` ploha ispod CTA-a |
| `MONACO` | svi tokeni editora — dijele jedan pravokutnik, pa su svi sa svima |

⚠️ **Susjedstvo prekida visokokontrastna ploha.** `primary-foreground` (tekst u gumbu)
**ne** nasljeđuje skup od `primary` (fill gumba): između teksta i `-soft` plohe iza gumba
stoji pun `primary` fill (14,24:1). Prvi pokušaj ga je nasljedio i odmah dao lažni pozitiv
(`primary-foreground × incorrect-soft` = 0,0495). Isti poučak kao #50.

### Pragovi

| ΔE | oznaka | značenje |
| --- | :---: | --- |
| < 0,05 | 🔴 | jedva razlučivo — kroma-token se **može čitati kao član skale** |
| < 0,10 | 🟡 | blizu — dopušteno uz obrazloženje (oblik ili kontekst razdvajaju) |
| ≥ 0,10 | ✅ | jasno različito |
| — | 🟨 | u `DE_ACCEPTED`: ispod praga, ali **svjesno prihvaćeno s razlogom** |

### Kako dopuniti skup kad nastane novi fokusabilni element

```bash
grep -rn "outline-ring\|ring-ring" frontend/src --include=*.tsx
```

Za svaki **novi** pogodak pročitaj što je unutar tog elementa i neposredno uz njega, pa
svaki semantički token upiši u `CO_USED_EXTRA["ring"]` **s citatom**. Isto za nov gumb
(`CO_USED_EXTRA["primary"]`) i za nov Monaco token (`MONACO`). Zatim:

```bash
python3 scripts/a11y/contrast_matrix.py --delta-e
```

🔴 **Bez ove dopune sljedeći prolaz mjeri stari skup i dobiva drugi odgovor.**

## Gamut: klampanje se prijavljuje, ne prešućuje

`_lin_to_srgb` klampa na `[0,1]`. Vrijednost izvan sRGB gamuta zato **ne bi pukla** — alat
bi vratio brojku za boju koja **nije deklarirana**. Zato `palette.py` pri svakom čitanju
CSS-a ispisuje upozorenje s imenom tokena i **veličinom viška chrome**:

```
⚠️  IZVAN sRGB GAMUTA — `_lin_to_srgb` klampa, mjeri se KLAMPANA boja:
   • --destructive: oklch(0.704 0.191 22.216) — višak chrome +0.0033 …
```

Ne prekida izvođenje (kod nas su svi viškovi ≤ 0,01, dakle ΔE ≤ 0,009 — ispod praga
vidljivosti), ali razlika mora biti **vidljiva**, ne prešućena. ⚠️ Uz to: preglednik radi
**vlastito** gamut-mapiranje (CSS Color 4 smanjuje chromu), koje nije isto što i naš
klamp po kanalu — pa je izmjereni hex za takav token približan, ne točan.

## Što alat NE mjeri

- 🔴 **Približavanje PLOHE susjednom pojasu percepcije čipa.** ΔE nad sukorištenim skupom
  mjeri **par**, a ne koliko je ploha „ušla u prostor" skale. Primjer iz 4.7-r2, t.0b —
  kandidat **B** za kromu ploha (C 0,044 / 0,066 / 0,082 na hue 280):

  | provjera | ishod za B |
  | --- | :---: |
  | matrica kontrasta (49 parova + 12 čipova) | **0 padova** ✅ |
  | ΔE nad sukorištenim parovima | **0 kolizija** ✅ |
  | ΔE `-soft` ploha prema `card` | **porastao** (0,0895–0,1060) ✅ |
  | ΔE `card` × `tier-easy` | ≫ prag, nije ni blizu ✅ |
  | **oko na snimci Dashboarda** | 🔴 **violet `tier` i magenta `difficulty` čipovi počinju se stapati s plohom** |

  Alat je rekao „prolazi" po svakoj brojci koju zna izmjeriti. Odluka je ipak pala na
  **A** (C 0,032 / 0,048 / 0,060), i to **ne zbog gamuta** (dopušta 0,088 / 0,124 / 0,163)
  nego zbog referentnog dizajna: A već premašuje kromu mockupa na sva tri sloja
  (0,026 / 0,039 / 0,056, KORAK 0 §C.1). **Strop nije gamut nego referentni dizajn.**

  **Zašto metrika to ne hvata:** ΔE(ploha, čip) ostaje velik jer ih razdvaja svjetlina
  (L 0,205 vs 0,60–0,80). Ono što se stapa nije *par* nego **kromatski kontekst** — čip
  prestaje biti jedina obojena stvar u kadru. Za to nema brojke u ovom alatu; ima je samo
  snimka. Ako netko ikad opet pojača kromu ploha, **provjera je snimka, ne `--delta-e`.**

- 🔴 **Postojanje potrošača.** Alat mjeri **vrijednosti**, ne dosežnost. Tvrdnja „token
  nema potrošača" ne smije se izvesti grepom po **imenu**: token može biti posredovan
  **aliasom** (`--font-heading: var(--font-sans)`), `@theme` mapiranjem, shadcn registry
  setupom ili dinamičnim pristupom. Povod: u 4.7 je `--font-heading` prijavljen kao „0
  potrošača", a imao ih je dva — nisu se vidjeli jer alias nije imao **učinak**.
  Dokaz mora biti o učinku: `var(--token)` i generirane utility klase u
  `frontend/dist/assets/index-*.css`, a za obrisane stavke `git log -S` po **svakom**
  identifikatoru koji su nosile. ⚠️ Prisutnost klase u `dist` NIJE dokaz dosežnosti koda —
  Tailwind je emitira i iz mrtvog koda. Puna politika: 🔒 DOC u `docs/errata.md`.

- **Vizualnu hijerarhiju.** Izračun mjeri element, snimka mjeri kompoziciju. Token može
  proći AA i pritom se stopiti sa susjedom (poučak iz 4.7-1a: pomoć uz `username` prolazila
  je 4,73:1 a bila je najslabiji tekst na ekranu).
- ~~**Međusobnu razlučivost boja sintakse** u Monacu~~ — **sad mjeri**, kroz `--delta-e`
  (`MONACO` u `pairs.py`). Prvi nalaz te provjere: `rules[comment]` (`--muted-foreground`)
  i `rules[operator]` (`--neutral`) su na **ΔE 0,0233** — komentar i operator su u editoru
  gotovo iste boje. Zatečeno, ne uzrokovano redizajnom.
- **Stvarni routing** — mjeri tokene, ne renderirane ekrane. Živa verifikacija ostaje
  zaseban korak.
- **Deuteranopiju/protanopiju.** Za to je postojala zasebna analiza u 4.3c (ΔE + simulacija).
