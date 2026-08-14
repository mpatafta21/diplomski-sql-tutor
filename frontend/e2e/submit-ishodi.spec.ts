/**
 * Regresijski gate — predaja razlikuje TRI ishoda, ne dva.
 *
 * Kvar koji čuva: do 2026-08-14 je `TaskPage` granao samo na `status === 504`, pa
 * je `503 coordinator_busy` (uveden popravkom #62) padao u poruku „Veza prema
 * poslužitelju nije uspjela". Ta poruka je bila NETOČNA — veza je uspjela,
 * poslužitelj je odgovorio, sustav je bio zauzet i ponovni pokušaj odmah ima
 * smisla. `fix-62-63-wrapup.md` §F.1 propisuje podjelu na tri ishoda.
 *
 * 🔴 Odgovori se PODMEĆU (`page.route`), ne izazivaju stvarnom konkurentnošću.
 * Razlog: ovaj test tvrdi da se `detail` ISPRAVNO MAPIRA u poruku, a to je
 * svojstvo klijenta. Izazivanje pravog `coordinator_busy` tražilo bi utrku više
 * paralelnih predaja — sporo, flaky, i mjerilo bi backend koji ima vlastite
 * testove (`test_coordinator_concurrency.py`).
 *
 * Nuspojava koja je ovdje korist: nijedan podmetnuti zahtjev ne dođe do baze, pa
 * teardown ostaje čist.
 */
import { test, expect } from "@playwright/test"
import { E2E_PREFIX } from "./db"

const RUN_ID = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
const USER = `${E2E_PREFIX}si${RUN_ID}`

/** Ishodi koje ruta doista vraća, i ono što student mora pročitati. */
const ISHODI = [
  {
    status: 503,
    detail: "coordinator_busy",
    naslov: /zauzet/i,
    // Zauzeće je prolazno — poruka mora zvati na TRENUTNI ponovni pokušaj.
    poruka: /odmah/i,
  },
  {
    status: 504,
    detail: "evaluation_timeout",
    naslov: /nije stigla/i,
    poruka: /nije zabilježeno/i,
  },
  {
    status: 504,
    detail: "orchestration_timeout",
    naslov: /ne odgovara/i,
    poruka: /nije zabilježeno/i,
  },
] as const

test("predaja razlikuje tri ishoda po `detail`, ne po statusu", async ({
  page,
}) => {
  await page.goto("/register")
  await page.getByLabel("Korisničko ime").fill(USER)
  await page.getByLabel("Email").fill(`${USER}@example.com`)
  await page.getByLabel("Lozinka").fill("e2e-lozinka-123")
  await page.getByRole("button", { name: "Registriraj se" }).click()
  await expect(page).not.toHaveURL(/\/register/, { timeout: 20_000 })

  await page.goto("/modules#module-1")
  const conceptLink = page
    .getByRole("link", { name: /^Otvori zadatak za koncept / })
    .first()
  await expect(conceptLink).toBeVisible({ timeout: 20_000 })
  await conceptLink.click()
  await expect(page).toHaveURL(/\/task\/\d+/, { timeout: 30_000 })

  await page.locator(".monaco-editor").click()
  await page.keyboard.type("SELECT 1;")

  const vidjeni: string[] = []

  for (const ishod of ISHODI) {
    await page.route("**/attempt", async (route) => {
      await route.fulfill({
        status: ishod.status,
        contentType: "application/json",
        body: JSON.stringify({ detail: ishod.detail }),
      })
    })

    await page.getByRole("button", { name: /^Submit/ }).click()

    const alert = page.getByRole("alert").first()
    await expect(alert).toBeVisible({ timeout: 15_000 })
    const tekst = await alert.innerText()
    vidjeni.push(tekst)

    expect(tekst, `[${ishod.detail}] naslov`).toMatch(ishod.naslov)
    expect(tekst, `[${ishod.detail}] poruka`).toMatch(ishod.poruka)

    await page.unroute("**/attempt")
    await page.reload()
    await page.locator(".monaco-editor").click()
    await page.keyboard.type("SELECT 1;")
  }

  // 🔴 Jezgra: tri RAZLIČITA teksta. Da se mapira po statusu, dva 504 ishoda bi
  // dala isti tekst, a 503 bi pao u generičku granu — i ova tvrdnja bi pala.
  expect(new Set(vidjeni).size, `poruke se ne razlikuju: ${vidjeni}`).toBe(3)
})
