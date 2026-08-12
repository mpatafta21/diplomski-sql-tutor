# Invarijante projekta — kanonski popis

> **Ovo je jedini kanonski popis.** Kod referencira invarijante **opisno**, a ovaj ih
> dokument definira. Nastao konsolidacijom **NALAZA N-8** (`docs/faza-4.7-nalazi.md`).

## 🔴 BEZ BROJEVA — i to je cijela poanta

Numeracija je bila **uzrok** N-8, ne rješenje. Samo tri invarijante su ikad bile
numerirane (`docs/faza-4.1-wrapup.md:85-87`); kasniji wrapupi (4.2 §5, 4.3 §5, 4.4b)
nabrajali su ih **bez brojeva**, pa su komentari u kodu naknadno izmislili `#4` i `#6`
kojih nigdje nema, a `#1` i `#2` upotrijebili za **druga pravila** nego što su definirana.
Dva broja su time postala dvoznačna, a jedno isto pravilo nosilo je dva broja.

**Konvencija od 4.7:** opisni naslov + **stabilno sidro** (`#xp-autoritativni-izvor`).
Sidro se ne mijenja ni kad se naslov preformulira. U kodu se referencira opisno, uz sidro:

```ts
// Invarijanta: prag iz /profile (docs/invarijante.md#prag-iz-profila)
```

`docs/faza-4.1-wrapup.md:85-87` **ostaje nepromijenjen kao povijesni zapis** — ondje je
dodan pokazivač na ovaj dokument. Ne prepisuje se.

---

## <a id="401-runtime"></a>401 se hvata u runtimeu, ne kroz tipiziranu granu

**Pravilo.** Security dependency nije u OpenAPI shemi, pa je tipizirana `error` grana
`never`. Auth greške se **nikad** ne hvataju kroz nju — uvijek `response.ok` + middleware.
Vrijedi za **sve** zaštićene pozive.

**Hazard.** Tiho progutan 401: TypeScript tvrdi da grana ne postoji, kod je ne piše, a
korisnik ostaje na ekranu koji se ne puni i bez poruke.

**Zapisano u kodu:** `routes/guards.tsx:4`.
**Izvor:** `docs/faza-4.1-wrapup.md:85`.

---

## <a id="ts6-erasable"></a>Bez TS parameter-properties (`erasableSyntaxOnly`)

**Pravilo.** TypeScript 6 s `erasableSyntaxOnly` ne dopušta parameter-properties — polja
klase pišu se eksplicitno.

**Hazard.** Build puca, i to tek na CI-ju.

**Zapisano u kodu:** `components/ErrorBoundary.tsx:5`.
**Izvor:** `docs/faza-4.1-wrapup.md:86`.

---

## <a id="touch-targeti"></a>Touch targeti ≥ 44 px (WCAG 2.5.5)

**Pravilo.** shadcn Nova je kompaktan (`h-8`), pa su vendorani defaulti podignuti:
`button default h-11 / lg h-12 / icon size-11`, `input h-11`. Varijante `xs`/`sm` su
**svjestan escape-hatch za gusti sekundarni UI**, nikad za primarne akcije.

**Hazard.** Nedodirljiv gumb na telefonu — a evaluacija je asinkrona i nenadzirana, pa
nema nikoga da pomogne.

**Zapisano u kodu:** `ui/button.tsx:34`, `ui/input.tsx:11`, `ui/sheet.tsx:60`,
`layout/AppShell.tsx:93`.
**Izvor:** `docs/faza-4.1-wrapup.md:87`.
**Presedan:** 1C — drawer je izmjeren na živoj aplikaciji (hamburger 44×44, nav stavka
295×44, Zatvori 44×44); v. N-16.

---

## <a id="prag-iz-profila"></a>Backend konstante dolaze iz `/profile`, nikad se ne hardkodiraju

**Pravilo.** `mastery_threshold`, `level_step` i srodne konstante putuju kroz
`/profile` odgovor. Frontend ih **nikad** ne piše kao literal (npr. `0.85`).

**Hazard.** Backend promijeni prag, frontend nastavi crtati po starom — i **laže o
savladanosti**, tiho i dosljedno.

**Zapisano u kodu:** `hooks/useProfile.ts:4`, `lib/mastery.ts:6`, `lib/progress.ts:5`,
`pages/ModulesPage.tsx:4`, `components/dashboard/MasteryHighlights.tsx:4`,
`components/profile/MasteryCurves.tsx:12`, `components/dashboard/ProgressHero.tsx:5`.

> ⚠️ Ovo je pravilo koje je u N-8 nosilo **dva različita broja** (`#2` na dva mjesta,
> `#6` na šest). Sada nosi jedno sidro.

---

## <a id="xp-autoritativni-izvor"></a>XP dolazi iz `/profile` — nikad se ne izvodi

**Pravilo.** Autoritativni XP je **isključivo** `/profile.xp`. Ne sumira se
`attempt.xp_awarded`, ne računa se iz povijesti pokušaja.

**Hazard — neusklađene brojke.** Bedž-XP ulazi u `xp_log` s `attempt_id = NULL`, pa je
`Σ xp_awarded` po pokušajima **manji** od `/profile.xp`. Dvije brojke bi se **razilazile**,
a obje bi izgledale točno.

**Zapisano u kodu:** `components/profile/StatsSummary.tsx:8-10`
(*„NE sumira `xp_awarded` i NE prikazuje XP … autoritativni XP je SAMO `/profile`"*).
**Presedan:** `StatsSummary` (4.4a) — sažetak nad prozorom pokušaja **namjerno** izostavlja
XP iako ga ima u podacima.

---

## <a id="jedan-prikaz-po-kadru"></a>Ista autoritativna brojka ne stoji dvaput u kadru

**Pravilo.** Jedna vrijednost — jedno mjesto prikaza **u istom kadru**. Persistentni
elementi (sidebar, topbar) računaju se u kadar svake rute na kojoj su vidljivi.

**Hazard — redundancija.** Dvije **jednake** brojke tjeraju čitatelja da traži razliku koje
nema. Nije problem točnosti nego čitljivosti.

🔴 **Ovo je ODVOJENA invarijanta od [autoritativnog izvora](#xp-autoritativni-izvor), i to
namjerno.** Spojene bi se čitale preširoko: prva je **tvrda i mjerljiva** (brojke se
razilaze, to je bug), druga je **dizajnerska i podložna iznimci** (brojke su identične,
smeta samo dvostrukost). Kad se ikad procjenjuje iznimka, mora biti jasno **kojoj** se od
te dvije traži.

**Presedani (oba iz 1C):**

| slučaj | ishod |
|---|---|
| sidebar level/XP kartica (t.2) | XP izbačen iz kartice → **varijanta C** (level + streak). Sidebar je persistentan, `ProgressHero` stoji na Dashboardu i Profilu |
| topbar streak čip (t.3) | `md:hidden` — čip postoji **samo** ondje gdje sidebara nema |

**Provjereno:** Dashboard @1440 — XP niske u kadru: **1** (u `<main>`), u `<aside>`: **0**.
Drawer otvoren @380 — vidljivih streak niski: **1**. V. N-16.

---

## <a id="mastery-bar"></a>Progres se crta isključivo kroz `MasteryBar`

**Pravilo.** Nema drugog progres-renderera. `MasteryBar` nosi **border-ani track**, koji se
ne uklanja.

**Hazard.** Mastery `0`/`25` fillovi ne dosežu 3:1 prema podlozi (#33). Vidljivost stanja
nosi **track**, ne fill — pa bi uklanjanje bordera učinilo niske vrijednosti nevidljivima.

**Zapisano u kodu:** `components/MasteryBar.tsx:5,51,58`,
`components/modules/ConceptRow.tsx:4`.

---

## <a id="prijava-po-usernameu"></a>Prijava ide po `username`, ne po e-mailu

**Pravilo.** `/login` prima `username`. E-mail se traži **samo** pri registraciji.

**Hazard.** Korisnik upiše e-mail, dobije „neispravni podaci", i to izgleda kao pokvarena
prijava umjesto kao krivo polje.

**Zapisano u kodu:** `pages/LoginPage.tsx:2`, `pages/RegisterPage.tsx:2`.

---

## <a id="tokeni-ne-boje"></a>Komponente vuku tokene — nula hardkodiranih boja

**Pravilo.** Nijedna komponenta ne piše boju kao literal. `design-system/sql-tutor/MASTER.md`
je SSOT.

**Hazard.** Promjena palete zaobiđe hardkodiranu vrijednost i ona tiho ostane stara —
točno ono što se dogodilo `monaco-theme.ts` vrijednosti `#292929` (v. 4.7-r1).

**Iznimka s vlastitim guardom:** `lib/monaco-theme.ts` **mora** biti hex (Monaco ne vidi
CSS varijable). Zato ga `scripts/a11y/monaco_check.py` provjerava **u cijelosti** —
vrijednost koju `MAP` ne tvrdi je greška, ne bilješka.

---

## <a id="povucena-errata"></a>Povučena errata stavka se OZNAČAVA, nikad ne briše

**Pravilo.** Kad se nalaz ili tvrdnja unutar nalaza pokaže netočnom, u `docs/errata.md`:

1. **broj ostaje** — ne reciklira se i ne popunjava se drugim nalazom
   (postojeća konvencija „broj je trajan"),
2. povučeni tekst ostaje **precrtan** (`~~…~~`), ne briše se,
3. uz njega ide **vidljiva oznaka** `🔴 POVUČENO (datum)` s **razlogom** i s onim što
   **ostaje** istinito nakon povlačenja,
4. ako je povučena samo tvrdnja unutar nalaza, nalaz zadržava status; ako je povučen
   **cijeli** nalaz, status postaje `🚫 povučen` u tablici statusa.

**Hazard.** Tiho brisanje ostavlja commitove, wrapupe i kod koji referenciraju nalaz bez
ičega na što bi pokazivali — točno mehanizam visećih referenci `#14`, `#15`, `#26` zbog
kojeg je errata i konsolidirana. Gore od toga: povučena tvrdnja koja je jednom bila u
tekstu **nastavi se citirati** iz starijih dokumenata, a čitatelj nema kako doznati da je
opovrgnuta.

**Presedan.** `#60` (2026-08-12): odjeljak „trag u produkcijskim podacima" precrtan je i
označen kao POVUČEN, dok sam nalaz o nedeterminizmu ostaje valjan; izvedena uputa
(„izuzeti preporuke od 2026-08-11") povučena je zasebno jer bi bacila ispravne podatke.
`#49` je presedan za **umirovljen broj** — nikad dodijeljen, trajno se ne dodjeljuje.

**Zašto je uopće zapisano.** Praksa je postojala u dva primjera, ali nigdje kao pravilo,
pa je sljedeće povlačenje ovisilo o tome sjeća li se autor kako se to radilo.

---

## <a id="brojka-nosi-konkurentnost"></a>Brojka o performansama nosi broj istovremenih korisnika

**Pravilo.** Nijedna izmjerena vrijednost (p50, p95, throughput, trajanje) ne navodi se
bez broja **istovremenih korisnika** pod kojim je izmjerena. To vrijedi u kodu, u
wrapupima i u tekstu rada.

**Hazard.** Brojka bez tog broja opisuje **drugi sustav** nego što čitatelj misli.
Izmjereno: `p95 = 135 ms` bilo je istinito i stabilno mjesecima — pri **jednom**
korisniku. Pri dvoje se polovica predaja **gubila**, a p95 uspjelih je ostajao 120 ms,
jer su izgubljeni zahtjevi ispadali iz uzorka. Ista brojka, sustav koji ne radi.

**Presedan.** ERRATA #62: sva mjerenja do 2026-08-12 (p95 iz 5.1, `pilot_run`,
Playwright uz `workers: 1`, svih 6 coordinator testova) bila su sekvencijalna, pa
nijedno nije opisivalo ponašanje s dvoje korisnika. Nijedno nije bilo netočno — sva su
bila **uža** nego što su izgledala.

**Kako se piše.** „p95 = 197 ms (20 studenata, predaja svakih ~19 s)", nikad „p95 = 197 ms".

---

## <a id="jedan-uvicorn-radnik"></a>`--workers 1` je invarijanta, ne postavka

**Pravilo.** Gateway se pokreće kao **jedan** uvicorn proces. `--workers > 1` nije
dopušten bez arhitektonske promjene.

**Hazard.** Svaki radnik pokreće vlastiti `start_gateway_stack` i prijavljuje se na
Prosody **istim JID-om** iz `.env`. Isporuka poruka tada ovisi o prioritetu XMPP
resursa, a `AgentBridge` je **in-process dict**: Future čeka u radniku A, odgovor može
stići radniku B i ondje se tiho izgubiti (`resolve` vrati `False`, ostane `_log.debug`).
To je ista klasa gubitka kao ERRATA #62, samo teža za dijagnozu jer se ne vidi ni u
`agent_messages_log`.

**Što bi trebalo za više radnika:** JID po radniku **i** korelacijski registry izvan
procesa (Redis ili sl.). To je druga arhitektura, ne zastavica.

**Zapisano u kodu:** `Makefile:168` (jedan proces, `--reload` u devu).
**Izvor:** `docs/fix-62-korak-0.md` §E.3.

---

## Kako dodati invarijantu

1. Opisni naslov + **novo stabilno sidro** (`<a id="...">`).
2. **Pravilo**, **hazard koji sprječava**, **citat mjesta u kodu**, i **presedan** ako
   postoji (slučaj u kojem je promijenila ishod).
3. U kodu referencirati **opisno + sidrom**, nikad brojem.
4. Ako pravilo ima dva različita hazarda — **razdvojiti ga na dvije invarijante**
   (v. XP par gore). Spojena invarijanta se čita preširoko.
