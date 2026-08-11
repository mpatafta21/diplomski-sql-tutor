import { defineConfig, devices } from "@playwright/test"

/**
 * Playwright smoke (Faza 4.7-1B, NALAZ #17).
 *
 * 🔴 OPSEG: JEDAN happy path studenta. Nula ambicija oko coveragea, bez unit testova,
 * bez snapshotova. Cilj je ulazni gate prije evaluacije: „prođe li student uopće kroz
 * sustav od registracije do sljedećeg zadatka".
 *
 * 🔴 NE POKRETATI TIJEKOM EVALUACIJSKE SESIJE — isto pravilo kao za `pytest` (#40).
 * Suite piše u ŽIVU `tutor_main`; teardown čisti svoje redove, ali `agent_messages_log`
 * nema `user_id` pa ga nijedan cleanup ne dohvaća. V. `e2e/README.md`.
 */
export default defineConfig({
  testDir: "./e2e",
  // Jedan spec, jedan worker — smoke ne smije utrkivati sam sa sobom u istoj bazi.
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"]],
  timeout: 60_000,
  // Agentski lanac (evaluator → knowledge → gamification) je sinkron i može trajati.
  expect: { timeout: 15_000 },

  globalSetup: "./e2e/global-setup.ts",
  globalTeardown: "./e2e/global-teardown.ts",

  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "retain-on-failure",
    video: "off",
    screenshot: "only-on-failure",
  },

  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],

  // Dev server se PONOVNO KORISTI ako već radi — ne dižemo drugi na istom portu.
  webServer: {
    command: "npm run dev -- --port 5173 --strictPort",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 60_000,
  },
})
