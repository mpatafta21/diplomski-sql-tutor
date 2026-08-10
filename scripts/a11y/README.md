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
# puna matrica u terminal (obje teme) — izlazni kod 1 ako išta padne
python3 scripts/a11y/contrast_matrix.py

# markdown za docs/faza-4.7-kontrast-matrica.md
python3 scripts/a11y/contrast_matrix.py --md > docs/faza-4.7-kontrast-matrica.md

# jedan par, brzo tijekom iteriranja palete
python3 scripts/a11y/contrast_matrix.py --pair muted-foreground incorrect-soft
python3 scripts/a11y/contrast_matrix.py --pair accent-warm-text accent-warm/20

# samo jedna tema
python3 scripts/a11y/contrast_matrix.py --theme light

# je li Monaco tema još u skladu s tokenima
python3 scripts/a11y/monaco_check.py
```

Bez dependencyja — čisti Python 3.11 iz standardne biblioteke.

## Datoteke

| Datoteka | Uloga |
| --- | --- |
| `palette.py` | oklch → sRGB, WCAG omjer, **parser `index.css`**, samotest konvertora |
| `pairs.py` | **podaci**: plohe, stvarni parovi s citatima, čipovi, pragovi |
| `contrast_matrix.py` | CLI: puna matrica / jedan par / markdown |
| `monaco_check.py` | drift između `monaco-theme.ts` (hex kopija) i tokena |

## Tri pravila koja alat utjelovljuje

**1. Tokeni se ČITAJU iz `index.css`, ne hardkodiraju.** Zato alat preživi promjenu
palete: promijeni `index.css`, pokreni istu naredbu, dobiješ nove brojke. Ako se
struktura CSS-a promijeni (redoslijed `:root` → `.dark` → `@layer base`), parser
**prekida s greškom** umjesto da tiho vrati krive brojke.

**2. Konvertor se validira prije svakog mjerenja.** `SELF_TEST` u `palette.py` nosi šest
brojki koje su **objavljene u dokumentaciji projekta prije nego je ova skripta
postojala** (npr. `foreground × card` = 19,79 light / 17,16 dark). Ako ih konvertor ne
reproducira, skripta **izlazi s kodom 2** i ne mjeri ništa. Poučak iz #39: guard koji
nije testiran u oba smjera nije guard.

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

## Što alat NE mjeri

- **Vizualnu hijerarhiju.** Izračun mjeri element, snimka mjeri kompoziciju. Token može
  proći AA i pritom se stopiti sa susjedom (poučak iz 4.7-1a: pomoć uz `username` prolazila
  je 4,73:1 a bila je najslabiji tekst na ekranu).
- **Međusobnu razlučivost boja sintakse** u Monacu (keyword vs string vs number).
- **Stvarni routing** — mjeri tokene, ne renderirane ekrane. Živa verifikacija ostaje
  zaseban korak.
- **Deuteranopiju/protanopiju.** Za to je postojala zasebna analiza u 4.3c (ΔE + simulacija).
