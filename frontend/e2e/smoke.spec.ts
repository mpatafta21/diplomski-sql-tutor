/**
 * Student happy path — JEDAN scenarij (NALAZ #17, Faza 4.7-1B).
 *
 *   register → login → /task → Run → Submit → feedback → „Sljedeći zadatak"
 *
 * 🔴 OPSEG: mehanika, ne točnost. Smoke NE zna točan odgovor na servirani zadatak (i ne
 * smije ga znati — rješenje nije u API-ju), pa NE tvrdi da je verdikt „Točno". Tvrdi da
 * je lanac prošao: editor prima unos, Run vraća panel s rezultatom, Submit vraća feedback
 * s NEKIM verdiktom, i CTA vodi na sljedeći zadatak. To je ono što gate treba.
 *
 * 🔴 Nijedna izmjena PONAŠANJA produkcijskog koda nije napravljena za ovaj test.
 */
import { test, expect, type Page } from "@playwright/test"
import { E2E_PREFIX } from "./db"

/** Jedinstven po runu — dva runa se ne smiju sudariti na UNIQUE username. */
const RUN_ID = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`
const USER = `${E2E_PREFIX}${RUN_ID}`
/**
 * `example.com` je IANA-rezerviran za dokumentaciju i nikad ne isporučuje poštu.
 * 🔴 NE koristiti `.local` — backend ga s pravom odbija s 422 („special-use or reserved
 * name"), pa bi test padao na vlastitim podacima i to izgledalo kao kvar registracije.
 */
const EMAIL = `${USER}@example.com`
const PASSWORD = "e2e-lozinka-123"

/**
 * Monaco ne prima `fill()`.
 *
 * 🔴 Ne prima ni `keyboard.type()`: SQL autocomplete hvata pojedinačne pritiske i sam
 * dopunjava, pa unos stigne izobličen — izmjereno u runu 2026-08-10, „SELECT id, name
 * FROM categories ORDER BY id;" završilo je kao „1ST id, ROM cateri Od;".
 * `insertText` ubacuje tekst BEZ key eventova, pa widget ne reagira.
 */
async function typeSql(page: Page, sql: string) {
  const editor = page.locator(".monaco-editor").first()
  await expect(editor).toBeVisible()
  await editor.click()
  await page.keyboard.press("ControlOrMeta+A")
  await page.keyboard.insertText(sql)
  await expect(editor).toContainText("SELECT")
}

test("student happy path: registracija → zadatak → Run → Submit → sljedeći", async ({
  page,
}) => {
  // ── 1. registracija ─────────────────────────────────────────────────────
  await page.goto("/register")
  await page.getByLabel("Korisničko ime").fill(USER)
  await page.getByLabel("Email").fill(EMAIL)
  await page.getByLabel("Lozinka").fill(PASSWORD)
  await page.getByRole("button", { name: "Registriraj se" }).click()

  // Registracija vodi u aplikaciju (Dashboard) — čekamo da izađemo s /register.
  await expect(page).not.toHaveURL(/\/register/, { timeout: 20_000 })

  // ── 2. odjava pa prijava (login se mora dokazati zasebno) ───────────────
  await page.getByRole("button", { name: /Odjava/i }).click()
  await expect(page).toHaveURL(/\/login/)
  await page.getByLabel("Korisničko ime").fill(USER)
  await page.getByLabel("Lozinka").fill(PASSWORD)
  await page.getByRole("button", { name: "Prijavi se" }).click()
  await expect(page).not.toHaveURL(/\/login/, { timeout: 20_000 })

  // ── 3. ulazak na zadatak preko /task (redirect na /task/:id) ────────────
  await page.goto("/task")
  await expect(page).toHaveURL(/\/task\/\d+/, { timeout: 30_000 })
  const firstTaskUrl = page.url()

  // ── 4. Run — proba bez bodovanja ────────────────────────────────────────
  await typeSql(page, "SELECT id, name FROM categories ORDER BY id;")
  const runBtn = page.getByRole("button", { name: "Run" })
  await expect(runBtn).toBeEnabled()
  await runBtn.click()
  // Rezultat ILI izvršna greška — oboje dokazuje da je sandbox odgovorio.
  await expect(
    page.getByText(/redak|redaka|Upit nije prošao|ms/i).first(),
  ).toBeVisible({ timeout: 30_000 })

  // ── 5. Submit — scored predaja kroz agentski lanac ──────────────────────
  const submitBtn = page.getByRole("button", { name: "Submit" })
  await expect(submitBtn).toBeEnabled()
  await submitBtn.click()

  // ── 6. feedback s NEKIM verdiktom ───────────────────────────────────────
  const verdict = page.getByText(
    /^(Točno|Djelomično|Netočno|Ocjenjivanje nije uspjelo)$/,
  )
  await expect(verdict.first()).toBeVisible({ timeout: 45_000 })

  // ── 7. CTA vodi na (sljedeći) zadatak ───────────────────────────────────
  // 🔴 NE tvrdimo da je ID različit. Pri netočnoj predaji preporučivač legitimno vraća
  // ISTI koncept, pa i isti zadatak — izmjereno u prvom runu (/task/15 → /task/15).
  // Smoke provjerava da CTA POSTOJI, da je link na rutu zadatka i da nas ostavlja na
  // valjanoj stranici zadatka. Da isti ID znači da CTA vizualno ne radi ništa
  // zabilježeno je kao nalaz (N-11), nije stvar ovog testa.
  const next = page.getByRole("link", { name: /Sljedeći zadatak/i })
  await expect(next).toBeVisible()
  await expect(next).toHaveAttribute("href", /\/task\/\d+/)
  await next.click()
  await expect(page).toHaveURL(/\/task\/\d+/)
  console.log(
    `   ℹ️  prvi zadatak: ${firstTaskUrl}\n   ℹ️  nakon CTA:    ${page.url()}` +
      (page.url() === firstTaskUrl ? "  (ISTI — v. N-11)" : ""),
  )
})
