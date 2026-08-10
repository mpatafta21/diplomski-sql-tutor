# Slike za diplomski rad

> 🔴 **SVIH 9 SNIMKI JE NEVAŽEĆE od 2026-08-10** (Faza 4.7 redizajn, stage 1).
> Dva odvojena razloga:
> 1. **Paleta.** Aplikacija je prebojena u ink-indigo (hue 280); svih 9 snimki prikazuje
>    staru neutralno-sivu paletu.
> 2. **Tema.** `08-fipa-agent-log-light.png` i `09-profil-bkt-krivulje-light.png` su u
>    **light temi, koja više ne postoji**. One se ne presnimavaju nego **brišu** — postoje
>    samo da pokažu „isto, svijetla tema" uz `07` odnosno `03`, pa bez light teme nemaju
>    ni sadržaj ni svrhu.
>
> **Presnimavanje ide JEDNOM, na kraju svih vizualnih stageova** (redizajn stage 2,
> display font, stage 1C mobilna navigacija) — ne nakon svakog. Uz snimanje se bilježi
> `COUNT(*)` tablice `agent_messages_log` prije i poslije (NALAZ N-3): snimanje ide kroz
> žive agente i ostavlja promet koji nijedan cleanup po korisniku ne dohvaća.
>
> ⚠️ Popis ispod opisuje **što snimke prikazuju**, ne kako aplikacija danas izgleda.

Snimke zaslona koje ilustriraju implementirani sustav. **Pod verzijom su namjerno**
(NALAZ #38): do Faze 4.6-eval artefakti rada živjeli su u scratchpadu, koji nije
repozitorij — ista klasa problema kao NALAZ #17, #20 i #26.

## Popis

| datoteka | što prikazuje | gdje se koristi u radu |
|---|---|---|
| `01-dashboard-dark.png` | Dashboard: XP, level, streak, preporučeni zadatak | poglavlje o igrifikaciji |
| `02-moduli-pregled-dark.png` | Pregled modula s napretkom i stanjima otključavanja | poglavlje o strukturi gradiva |
| `03-profil-bkt-krivulje-dark.png` | **BKT krivulje** (small multiples po konceptu), bedževi, povijest | poglavlje o modelu znanja |
| `04-zadatak-prije-slanja-dark.png` | Ekran zadatka: opis, shema baze, Monaco editor s upitom | poglavlje o sučelju |
| `05-zadatak-feedback-dark.png` | **Feedback nakon točnog rješenja**: „Točno", +10 XP, preporuka | poglavlje o evaluaciji i igrifikaciji |
| `06-ljestvica-dark.png` | Ljestvica (global scope) | poglavlje o igrifikaciji |
| `07-fipa-agent-log-dark.png` | **FIPA tok** — puni ciklus attempta, svih 6 agenata | poglavlje o agentskoj arhitekturi |
| `08-fipa-agent-log-light.png` | isto, svijetla tema | isto |
| `09-profil-bkt-krivulje-light.png` | Profil s BKT krivuljama, svijetla tema | isto kao 03 |

Sve su snimljene na **1440×900 CSS px pri `deviceScaleFactor: 2`** (dakle 2880×1800
efektivnih piksela i više za duge stranice) — dovoljno za tisak.

## 🔴 Privatnost — što je provjereno

**Datum provjere: 2026-07-20.**

- Sve su snimke napravljene na **dev demo računu `demo44_student`** i na `admin`
  računu, **prije** ijedne evaluacijske sesije. Na slikama nema nijednog stvarnog
  sudionika.
- **E-mail se ne pojavljuje ni na jednoj snimci.** To nije procjena okom nego
  svojstvo koda: `grep` nad `frontend/src` (2026-07-20) pokazuje da se `email`
  renderira **samo** u registracijskoj formi (`RegisterPage`) i kao *naziv stupca*
  sintetičke sandbox sheme (`sandbox-schema.ts`, npr. `customers.email`).
  `ProfilePage` i `AppShell` ga ne prikazuju nigdje.
- Vrijednosti u sandbox bazi su **Faker-generirane** (deterministički seed), ne
  podaci stvarnih osoba.
- Vidljivi `username` (`demo44_student`, `admin`) su dev računi i brišu se/čiste
  u `prepare_eval_baseline.py` prije evala.

🔴 **Ako se snimke ikad ponove S PODACIMA SUDIONIKA**, prije commita ih treba
zamijeniti pseudonimima — vidi `docs/eval-runbook.md`.

## Kako su nastale

Bez Playwrighta (**NALAZ #17** — tada nije bio u `package.json`): goli
`chrome-headless-shell` vođen preko CDP-a iz scratchpad skripte, isti pristup kao ručne
verifikacije u fazama 4.1–4.5.

> ⟳ **Za presnimavanje NE ponavljati taj put.** Playwright je u repou od `7f7c9aa`
> (`frontend/e2e/`, `@playwright/test`), s gotovim `globalSetup`/`globalTeardown` koji
> broje i vraćaju bazu na baseline. Snimanje u redizajn-stageu 1 (t.4) išlo je tim putem i
> radi — v. NALAZ N-15. Dvije zamke ispod vrijede i dalje, `e2e/smoke.spec.ts:28-40` ih je
> neovisno potvrdio.

Dvije zamke koje su usput otkrivene i koje vrijedi zapamtiti pri sljedećem snimanju:

1. **Monaco ignorira `textarea.value`.** Editor koristi *skriveni* textarea; upis
   preko value settera ne stigne do modela. Prva verzija snimke pokazivala je
   placeholder u editoru, a panel „Netočno — prazan rezultat": poslan je bio
   prazan upit. Ispravno je tipkati kroz `Input.insertText` (CDP).
2. **Upit mora ići u NOVI redak.** Redak 1 je komentar-placeholder
   (`-- Napiši svoj SQL upit ovdje`); lijepljenje iza njega zakomentira cijeli
   upit i ishod je opet prazan rezultat. Skripta zato provjerava regexom da je
   upit na vlastitom retku i **prekida** ako nije — figura koja prikazuje
   pogrešan ishod zbog greške alata lagala bi o sustavu.
