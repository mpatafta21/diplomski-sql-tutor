import { defineConfig, devices } from "@playwright/test"

/**
 * Konfiguracija za KOMPLETAN PROLAZ kroz aplikaciju (`e2e-prolaz/`).
 *
 * 🔴 ZAŠTO ZASEBNA KONFIGURACIJA, a ne novi spec u `e2e/`:
 *
 *  1. **`e2e/` ima `globalTeardown` koji BRIŠE podatke** i puca ako baza ne padne
 *     natrag na baseline. Prolaz radi točno suprotno — njegovi podaci OSTAJU u
 *     `tutor_main` kao materijal za rad. Da spec živi u `e2e/`, teardown bi ga
 *     pobrisao, ili bi puknuo i ostavio pola stanja.
 *  2. **`testDir` je ovdje `./e2e-prolaz`**, izvan `./e2e`, pa `npm run e2e`
 *     (ulazni gate, traje sekunde) NIKAD ne pokupi prolaz koji traje sat vremena.
 *     Odvojenost je mehanička, ne dogovorna.
 *
 * 🔴 NEMA `globalSetup`/`globalTeardown`. Brojke prije/poslije se bilježe RUČNO
 * (`docs/prolaz-podaci/counted-tables-*.txt`) jer prolaz nema baseline na koji
 * bi se vraćao.
 *
 * Snimanje galerije: 1440×900 @2× — ista metoda kao `docs/figures/README.md`
 * (Faza 4.7), uz JEDNU namjernu razliku: `reducedMotion` NIJE `"reduce"`.
 * Galerija mora uhvatiti nagradne trenutke (level-up konfeti, XP count-up,
 * badge-pop), a `reduce` ih po dizajnu gasi (`FeedbackPanel` ima rani izlaz).
 *
 * Pokretanje:
 *     cd frontend && npx playwright test --config=playwright.prolaz.config.ts
 * Traži: docker compose gore, backend na :8000, dev server na :5173.
 */
export default defineConfig({
  testDir: "./e2e-prolaz",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"]],
  // Prolaz je JEDAN test kroz 88 zadataka i ~131 predaju — mjeri se u desecima
  // minuta. 0 = bez gornje granice; pojedinačni koraci imaju svoje `expect`
  // timeoute, pa zaglavljivanje i dalje pada, samo ne po ukupnom trajanju.
  timeout: 0,
  expect: { timeout: 20_000 },

  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    // 🔴 Playwrightov default za akcije je BEZ granice, a `timeout: 0` na testu
    // je uklanja i s druge strane: jedan `click()` koji nikad ne postane
    // izvediv visi zauvijek. Izmjereno na prolazu 2026-08-18 — 16 minuta bez
    // ijedne poruke. Granica pretvara vis u pad koji ima trag.
    actionTimeout: 45_000,
    navigationTimeout: 45_000,
    trace: "retain-on-failure",
    video: "off",
    screenshot: "off",
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
    // Aplikacija je dark-only od Faze 4.7 (`ThemeProvider` uklonjen), pa je ovo
    // podudaranje s produkcijom, ne izbor teme.
    colorScheme: "dark",
  },

  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],

  webServer: {
    command: "npm run dev -- --port 5173 --strictPort",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 60_000,
  },
})
