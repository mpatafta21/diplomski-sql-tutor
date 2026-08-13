/**
 * N-20 regresijski gate za akcijski red (Faza 5.2, §D).
 *
 * 🔴 ŠTO OVAJ TEST ČUVA: gumb „Zatraži hint" je treći element u redu koji na
 * 768 px ima **432 px** stvarne širine (mjereno 2026-08-13; sidebar + grid uzimaju
 * ostatak). Run + Submit ondje troše 298,5 px, pa gumbu ostaje ~121 px. Natpis
 * dulji od zamrznutog („Zatraži hint") gurne red u `flex-wrap` → red naraste s
 * 44 na ~100 px i editor se pomakne. Baš to je N-20.
 *
 * Brojke NISU izmišljene: 44 i 420 su referentne vrijednosti snimljene PRIJE
 * uvođenja gumba (§A plana 5.2) i nepromijenjene nakon njega.
 *
 * 🔴 Test se preskače kad je `USE_LLM_HINTS=false` — tada gumba nema, red je
 * trivijalno uzak i tvrdnja ne bi mjerila ništa. Preskakanje je GLASNO (poruka),
 * ne tiho.
 */
import { test, expect } from "@playwright/test"
import { E2E_PREFIX } from "./db"

const RUN_ID = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
const USER = `${E2E_PREFIX}n20${RUN_ID}`
const EMAIL = `${USER}@example.com`
const PASSWORD = "e2e-lozinka-123"

/** Referentne visine iz §A — snimljene prije gumba, moraju preživjeti gumb. */
const RED_VISINA = 44
const EDITOR_VISINA_768 = 420

test("N-20: gumb za hint ne prelama akcijski red na 768 px", async ({
  page,
}) => {
  await page.setViewportSize({ width: 768, height: 1000 })

  await page.goto("/register")
  await page.getByLabel("Korisničko ime").fill(USER)
  await page.getByLabel("Email").fill(EMAIL)
  await page.getByLabel("Lozinka").fill(PASSWORD)
  await page.getByRole("button", { name: "Registriraj se" }).click()
  await expect(page).not.toHaveURL(/\/register/, { timeout: 20_000 })

  await page.goto("/task")
  await expect(page).toHaveURL(/\/task\/\d+/, { timeout: 30_000 })
  const red = page.getByTestId("action-row")
  const editor = page.getByTestId("editor-box")
  await expect(editor).toBeVisible()

  const gumb = page.getByRole("button", { name: "Zatraži hint" })
  if ((await gumb.count()) === 0) {
    test.skip(
      true,
      "USE_LLM_HINTS=false → gumba nema; N-20 mjeri red S gumbom, pa bi tvrdnja bila prazna.",
    )
  }

  // Natpis je zamrznut i identičan u oba stanja (H3.8) — dio ugovora koji ovaj
  // test čuva zajedno s visinom.
  await expect(gumb).toHaveText("Zatraži hint")

  const redBox = await red.boundingBox()
  const editorBox = await editor.boundingBox()
  expect(redBox?.height).toBe(RED_VISINA)
  expect(editorBox?.height).toBe(EDITOR_VISINA_768)

  // Prelamanje se dokazuje geometrijom, ne visinom: sva djeca reda dijele istu
  // gornju liniju. Visina bi mogla ostati 44 i da red naraste u širinu.
  const istaLinija = await red.evaluate(
    (el) =>
      new Set(
        [...el.children].map((k) => Math.round(k.getBoundingClientRect().top)),
      ).size === 1,
  )
  expect(istaLinija, "akcijski red se prelomio na 768 px").toBe(true)
})
