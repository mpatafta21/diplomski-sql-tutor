/**
 * Regresijski gate — klik na koncept vodi kroz RESOLVER, ne na statičan zadatak.
 *
 * Kvar koji čuva: `entry_task_id` iz `/modules` je statičan i bez korisničkog
 * konteksta, pa je klik na koncept vodio na već riješen zadatak — to češće što je
 * student dalje, jer najlakše rješava prvi a link je uvijek nudio najlakši.
 *
 * 🔴 OPSEG: ovaj test tvrdi da LANAC radi (link → `/koncept/:code` → poslužitelj
 * bira → `/task/:id`). NE tvrdi „preskače riješeno" — to se dokazuje pouzdanije u
 * `tests/test_api_task_for_concept.py` (`test_skips_solved_task`,
 * `test_is_per_user`), gdje se stanje seeda izravno umjesto da se kroz UI
 * pogađa točan SQL. Ovdje bi ista tvrdnja bila sporija i flaky.
 *
 * Ono što gate hvata: povratak `to={`/task/${entryTaskId}`}` u bilo koji od dva
 * potrošača (`MasteryHighlights`, `ConceptRow`).
 */
import { test, expect } from "@playwright/test"
import { E2E_PREFIX } from "./db"

const RUN_ID = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
const USER = `${E2E_PREFIX}kn${RUN_ID}`
const EMAIL = `${USER}@example.com`
const PASSWORD = "e2e-lozinka-123"

test("klik na koncept u Modulima razrješava zadatak kroz poslužitelj", async ({
  page,
}) => {
  await page.goto("/register")
  await page.getByLabel("Korisničko ime").fill(USER)
  await page.getByLabel("Email").fill(EMAIL)
  await page.getByLabel("Lozinka").fill(PASSWORD)
  await page.getByRole("button", { name: "Registriraj se" }).click()
  await expect(page).not.toHaveURL(/\/register/, { timeout: 20_000 })

  // Moduli su collapsible i svježem korisniku nijedan nije auto-otvoren
  // (`openModuleNumber` je null bez hasha), pa se koristi postojeći deep-link
  // `#module-<n>` — isti put kojim dolazi breadcrumb s Task ekrana.
  await page.goto("/modules#module-1")

  const conceptLink = page
    .getByRole("link", { name: /^Otvori zadatak za koncept / })
    .first()
  await expect(conceptLink).toBeVisible({ timeout: 20_000 })

  // 🔴 Jezgra: odredište je KONCEPT, ne zadatak. Da se link vrati na
  // `/task/${entryTaskId}`, ova tvrdnja pada prije ijedne navigacije.
  await expect(conceptLink).toHaveAttribute("href", /\/koncept\/[a-z_]+$/)

  await conceptLink.click()

  // Resolver preusmjerava na konkretan zadatak...
  await expect(page).toHaveURL(/\/task\/\d+/, { timeout: 30_000 })

  // ...i `/koncept/:code` NE ostaje u historyju (inače bi Back ponovno
  // razriješio koncept i vratio na isti zadatak — zamka iz TaskEntryPage).
  await page.goBack()
  await expect(page).toHaveURL(/\/modules/)
})
