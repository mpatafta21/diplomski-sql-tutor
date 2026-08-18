# Galerija — kompletan prolaz kroz sučelje (2026-08-18)

26 snimki iz **jednog neprekinutog prolaza jednog studenta kroz svih 88 aktivnih
zadataka**, redoslijedom kojim ih student vidi. Nastale su tijekom prolaza, ne
naknadnom režijom: svaki je kadar okinut u trenutku u kojem se prikazano stanje
doista dogodilo.

- **Račun:** `Maks` (student). Sučelje prikazuje **isključivo `username`** —
  zasebnog polja za ime nema, a e-adresa se ne renderira nigdje. Zato ni na
  jednoj snimci nema prefiksa ni e-adrese.
- **Metoda:** Playwright, 1440×900, `deviceScaleFactor: 2`, dark tema (aplikacija
  je dark-only od Faze 4.7).
- **Skripta:** [`frontend/e2e-prolaz/prolaz.spec.ts`](../../frontend/e2e-prolaz/prolaz.spec.ts)
  uz [`playwright.prolaz.config.ts`](../../frontend/playwright.prolaz.config.ts).
- **Podaci prolaza:** [`docs/prolaz-podaci/`](../prolaz-podaci/) ·
  **tijek i nalazi:** [`docs/e2e-kompletan-prolaz-wrapup.md`](../e2e-kompletan-prolaz-wrapup.md)

## 🔴 Jedna namjerna razlika od metode iz `docs/figures/README.md`

Ondje je snimano uz `reducedMotion: "reduce"`, radi determinizma. **Ovdje NIJE**,
i to je odluka, ne propust: galerija mora uhvatiti nagradne trenutke (level-up
konfeti, XP count-up, badge-pop), a `reduce` ih po dizajnu gasi — `FeedbackPanel`
ima rani izlaz za konfete, a count-up odmah skače na konačnu brojku. Kadrovi
14, 15 i 06 pod `reduce` režimom ne bi postojali.

Posljedica koju treba znati: na snimkama nastalima **neposredno nakon level-upa**
vide se čestice konfeta i preko drugih kartica (npr. `21`). To je stvarno stanje
ekrana u tom trenutku, ne artefakt snimanja.

## Popis

| # | datoteka | što prikazuje |
|---|---|---|
| 01 | `01-registracija.png` | Obrazac registracije s ispunjenim poljima |
| 02 | `02-dashboard-prazan-novak.png` | Dashboard novaka: 0 XP, bez bedževa, onboarding tekst |
| 03 | `03-moduli-vecina-zakljucana.png` | Moduli na početku — većina koncepata zaključana |
| 04 | `04-taskentry-preporuka.png` | **Krupni plan** kartice preporuke („Počni ovdje") |
| 05 | `05-zadatak-monaco-i-shema.png` | Ekran zadatka: opis, čipovi koncepata, shema baze, Monaco |
| 06 | `06-feedback-tocno.png` | Povratna sprega **Točno** — XP count-up uhvaćen u letu |
| 07 | `07-feedback-netocno.png` | Povratna sprega **Netočno** |
| 08 | `08-feedback-djelomicno.png` | Povratna sprega **Djelomično** (`row_mismatch`, polovičan XP) |
| 09 | `09-feedback-plan-mismatch.png` | **M6 `plan_mismatch`** — redci točni, plan izvedbe nije |
| 10 | `10-hint-gumb-zakljucan-s-razlogom.png` | Gumb za savjet zaključan, uz vidljiv razlog |
| 11 | `11-hint-llm.png` | Zatražen savjet — **izvor `llm`** |
| 12 | `12-hint-fallback.png` | Zatražen savjet — **izvor `fallback`** (katalog) |
| 13 | `13-hint-brojac-nula.png` | Brojač nakon petog savjeta: „Preostalo savjeta: 0" |
| 14 | `14-level-up.png` | Trenutak level-upa (konfeti + „Novi level") |
| 15 | `15-bedz-otkljucan.png` | Otključan bedž u panelu s ocjenom |
| 16 | `16-profil-bedzevi.png` | Profil — bedževi (4 osvojena, `streak_7` zaključan) |
| 17 | `17-profil-krivulje-mastery.png` | Profil — **BKT krivulje** (small multiples po konceptu) |
| 18 | `18-ljestvica.png` | Ljestvica |
| 19 | `19-dashboard-na-pola.png` | Dashboard na pola prolaza |
| 20 | `20-moduli-otkljucani.png` | Moduli na pola prolaza — otključavanje u tijeku |
| 21 | `21-dashboard-zavrsni.png` | Dashboard na kraju (88/88, level 47) |
| 23 | `23-moduli-zavrsni.png` | Moduli na kraju |
| 24 | `24-hint-potrosen.png` | Šesti klik na savjet → „Potrošio si sve savjete za sada" |
| 25 | `25-feedback-timeout.png` | `timeout` — kartezijev produkt prekinut nakon 5 s |
| 26 | `26-feedback-explain-submitted.png` | `explain_submitted` — predan `EXPLAIN` umjesto upita |
| 27 | `27-profil-cijela-stranica.png` | Profil, cijela stranica (za pregled cjeline) |

**Usporedba kroz vrijeme** (isti ekran u tri točke prolaza):

- Dashboard: `02` (početak) → `19` (sredina) → `21` (kraj)
- Moduli: `03` (početak) → `20` (sredina) → `23` (kraj)

## 🔴 Što NIJE snimljeno i zašto

**`22-sve-savladano` ne postoji.** Traženo je stanje „sve savladano"
(`TaskEntryPage`, `reason: no_recommendation`). **Ono se u ovom prolazu nikad
nije dogodilo** — ni sa svih 88 riješenih zadataka. Preporučivač i tada vraća
`task_id` uz `reason: repeat_practice`, pa `/task` uredno preusmjeri na zadatak i
završni ekran se ne renderira. Nije propust snimanja nego **nalaz**; opisan je u
wrapupu (§Nalazi, ERRATA #82).

**`04` je krupni plan kartice, ne puni prozor.** Ruta `/task` nema vlastiti
sadržaj — `TaskEntryPage` razriješi preporuku i odmah preusmjeri, pa je njezin
jedini mogući kadar prazan skeleton (provjereno snimanjem). Preporuka koju
student stvarno pročita prije ulaska u zadatak je kartica na Dashboardu, i to je
ono što `04` prikazuje.

**Broj 22 se ne dodjeljuje ponovno.** Praznina u numeraciji je namjerna — da se
poslije ne pomisli da je kadar zaboravljen.
