/**
 * KOMPLETAN PROLAZ kroz aplikaciju — jedan student, svih 88 aktivnih zadataka,
 * isključivo kroz sučelje.
 *
 * 🔴 OVO NIJE TEST. Ovo je proizvodnja materijala za diplomski rad: galerija
 * snimki, sekvenca preporuka, BKT krivulje, XP progresija i korpus savjeta.
 * Zato nema `expect` tvrdnji o ispravnosti sustava osim onih koje čuvaju sam
 * prolaz (npr. „upit je stvarno stigao u editor"). Sve što je pošlo po zlu ide
 * u dnevnik i poslije u erratu — skripta ništa ne popravlja i ništa ne prešućuje.
 *
 * 🔴 SVE IDE KROZ SUČELJE. Nijedan zahtjev se ne šalje mimo aplikacije:
 * upisuje se u Monaco, klikaju se gumbi, prati se „Sljedeći zadatak".
 * Mrežni promet se SAMO PROMATRA (`waitForResponse`) — to je jedini način da se
 * zabilježi točan `error_type`, `xp_delta` i `reason`, a promatranje ne pokreće
 * nijednu akciju koju student nije napravio.
 *
 * 🔴 PODACI OSTAJU U BAZI. Nema teardowna. Prolaz se ne vraća na baseline —
 * jedini put natrag je `make backup` snimljen prije pokretanja.
 *
 * Pokretanje:
 *     cd frontend
 *     npx playwright test --config=playwright.prolaz.config.ts
 *
 * Nastavak nakon prekida: stanje je u `e2e-prolaz/.stanje/stanje.json`; ponovno
 * pokretanje se prijavi na isti račun i preskoči već riješene zadatke.
 *
 * Probni prolaz (mehanika skripte; račun se poslije čisti `purgeE2eUsers`):
 *     PROLAZ_KORISNIK=e2e_proba PROLAZ_LIMIT=3 \
 *     PROLAZ_GALERIJA=/tmp/proba npx playwright test --config=playwright.prolaz.config.ts
 */
import { test, expect, type Page, type Response } from "@playwright/test"
import { existsSync, mkdirSync, readFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import { Dnevnik, type PlanZadatak } from "./dnevnik"

const OVDJE = dirname(fileURLToPath(import.meta.url))
const REPO = join(OVDJE, "..", "..")

// ── Račun ────────────────────────────────────────────────────────────────────
// 🔴 `username` je JEDINO polje identiteta koje sučelje prikazuje (Dashboard
// pozdrav, podnaslov Profila, topbar kartica, ljestvica). Zasebnog polja za ime
// NEMA, a e-adresa se ne renderira nigdje — provjereno u kodu prije prolaza.
// Zato je username doslovno „Maks": nijedna snimka ne može pokazati prefiks ni
// e-adresu. Posljedica koju treba znati: račun NEMA sentinel prefiks, pa ga
// `prepare_eval_baseline.py` neće prepoznati kao testni i neće ga obrisati —
// što je za ovaj prolaz i namjera.
const KORISNIK = process.env.PROLAZ_KORISNIK ?? "Maks"
const EMAIL = process.env.PROLAZ_EMAIL ?? `${KORISNIK.toLowerCase()}@example.com`
const LOZINKA = process.env.PROLAZ_LOZINKA ?? "prolaz-lozinka-2026"
/** Ograniči broj zadataka (probni prolaz). 0 = bez ograničenja. */
const LIMIT = Number(process.env.PROLAZ_LIMIT ?? "0")
const GALERIJA = process.env.PROLAZ_GALERIJA ?? join(REPO, "docs", "galerija")
const NAJVISE_SAVJETA = Number(process.env.PROLAZ_SAVJETI ?? "5")
/** Probni prolaz: traži savjet na SVAKOM zadatku s netočnom predajom (do limita). */
const HINT_SVUDA = process.env.PROLAZ_HINT_SVUDA === "1"

// ── Plan ─────────────────────────────────────────────────────────────────────
const PLAN = JSON.parse(readFileSync(join(OVDJE, "plan.json"), "utf-8")) as {
  meta: Record<string, unknown>
  zadaci: Record<string, PlanZadatak>
}

const dnevnik = new Dnevnik(KORISNIK, EMAIL, LOZINKA)

// ── Snimke ───────────────────────────────────────────────────────────────────
if (!existsSync(GALERIJA)) mkdirSync(GALERIJA, { recursive: true })

/**
 * Snimi ekran u galeriju. Idempotentno po imenu — kad se prolaz nastavlja,
 * već snimljeni kadrovi se ne presnimavaju (drugo stanje baze = druga slika).
 *
 * `animations: "disabled"` je default: CSS animacije se dovrše prije okidanja,
 * pa nema kadrova uhvaćenih u letu. Nagradni trenuci (konfeti, XP count-up) ga
 * izrijekom gase — njima je pokret sadržaj, ne smetnja.
 */
async function snimi(
  page: Page,
  ime: string,
  opcije: { fullPage?: boolean; uPokretu?: boolean } = {},
): Promise<boolean> {
  if (dnevnik.snimkaZabiljezena(ime)) return false
  await page.screenshot({
    path: join(GALERIJA, `${ime}.png`),
    fullPage: opcije.fullPage ?? false,
    animations: opcije.uPokretu ? "allow" : "disabled",
  })
  dnevnik.zabiljeziSnimku(ime)
  console.log(`   📷 ${ime}.png`)
  return true
}

// ── Pomoćnici za sučelje ─────────────────────────────────────────────────────

/** Normalizacija za usporedbu upisanog i namjeravanog SQL-a. */
function norm(s: string): string {
  return s
    .replace(/ /g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase()
}

/**
 * Upiši SQL u Monaco.
 *
 * 🔴 `insertText`, NIKAD `type()`: SQL autocomplete hvata pojedinačne pritiske i
 * sam dopunjava, pa unos stigne izobličen (dokumentirano u `e2e/README.md`).
 *
 * 🔴 Nakon upisa se sadržaj PROVJERAVA iz `.view-lines`. Bez provjere bi
 * izobličen upit otišao u bazu kao stvaran pokušaj, a prolaz se ne vraća na
 * baseline — kriva predaja se ne može poništiti.
 */
async function upisiSql(page: Page, sql: string): Promise<void> {
  const editor = page.locator(".monaco-editor").first()
  await expect(editor).toBeVisible({ timeout: 30_000 })
  const linije = page.locator(".monaco-editor .view-lines").first()
  await expect(linije).toBeVisible({ timeout: 30_000 })
  // Skriveni <textarea> je pravo mjesto unosa u Monacu.
  const unos = page.locator(".monaco-editor textarea.inputarea").first()

  // 🔴 Vrati stranicu na vrh prije unosa. `namjestiKadar` ju je zbog galerije
  // skrolao pri prethodnoj predaji, a s te pozicije geometrija editora više nije
  // predvidljiva (v. niže).
  await page.evaluate(() => window.scrollTo(0, 0))

  for (let pokusaj = 1; pokusaj <= 4; pokusaj++) {
    // 🔴 FOKUS, NE KLIK. Klik na `.view-lines` je na stvarnom prolazu pao s
    // „<p> s opisom zadatka presreće pointer events" (zadatak 33, 45 s čekanja):
    // Monacov `.view-lines` je apsolutno pozicioniran i njegov okvir ne mora
    // ležati nad vidljivim tekstom, pa Playwrightova točka klika padne izvan
    // editora. `focus()` ne radi hit-test — cilja element, ne koordinatu — pa je
    // cijela ta klasa pada nemoguća.
    await unos.focus({ timeout: 15_000 }).catch(async () => {
      // Rezerva: klik na CIJELI editor (obrazac iz `e2e/smoke.spec.ts`, koji je
      // radio) — njegov je okvir velik i središte uvijek nad tekstom.
      await editor.click({ timeout: 15_000 }).catch(() => null)
    })
    await expect(unos).toBeFocused({ timeout: 5_000 }).catch(() => null)
    await page.keyboard.press("ControlOrMeta+A")
    await page.keyboard.insertText(sql)
    // 🔴 Monaco iscrtava retke ASINKRONO, pa prvo čitanje `.view-lines` zna
    // vratiti samo prvi redak. Prva verzija je to čitala jednom i zaključivala
    // da je unos krnj — izmjereno na stvarnom prolazu (zadatak 63: „delete from
    // orders" umjesto tri retka), pa je prolaz stao. Provjera zato ANKETIRA do
    // 6 s umjesto da zaključuje iz jednog očitanja.
    try {
      await expect
        .poll(async () => norm(await linije.innerText()), {
          timeout: 6_000,
          intervals: [100, 200, 300, 500, 800, 1200],
        })
        .toBe(norm(sql))
      return
    } catch {
      console.log(
        `   ⚠️  upis u editor se ne poklapa (pokušaj ${pokusaj}) — ponavljam`,
      )
    }
  }
  throw new Error(
    `SQL nije ispravno upisan u editor.\nnamjera: ${norm(sql)}\n` +
      `u editoru: ${norm(await linije.innerText())}`,
  )
}

function putanja(r: Response): string {
  try {
    return new URL(r.url()).pathname
  } catch {
    return ""
  }
}

/** Klik na stavku glavne navigacije (isti put kojim ide student). */
async function nav(page: Page, ime: string): Promise<void> {
  await page.getByRole("link", { name: ime, exact: true }).first().click()
}

interface Ishod {
  status: number
  body: Record<string, unknown>
  ms: number
  poslano: string | null
}

/**
 * Postavi akcijski red na sredinu prozora.
 *
 * 🔴 Zbog galerije, ne zbog mehanike: panel s ocjenom i panel sa savjetom
 * ubacuju se ISPOD akcijskog reda, pa bi na dugom zadatku pali ispod ruba
 * prozora — probni prolaz je vratio kadrove odrezane na pola poruke. Skrol ide
 * PRIJE predaje da se ne izgubi XP count-up (~700 ms) čekajući skrol poslije.
 */
async function namjestiKadar(page: Page): Promise<void> {
  await page
    .getByTestId("action-row")
    .evaluate((el) => el.scrollIntoView({ block: "center" }))
    .catch(() => null)
}

/** Predaj upit kroz gumb Submit i pričekaj odgovor koji sučelje dobije. */
async function predaj(page: Page, sql: string): Promise<Ishod> {
  await upisiSql(page, sql)
  const gumb = page.getByRole("button", { name: /^Submit/ })
  await expect(gumb).toBeEnabled()
  await namjestiKadar(page)
  const t0 = Date.now()
  const [resp] = await Promise.all([
    page.waitForResponse(
      (r) => putanja(r) === "/attempt" && r.request().method() === "POST",
      { timeout: 120_000 },
    ),
    gumb.click(),
  ])
  const ms = Date.now() - t0
  let body: Record<string, unknown> = {}
  try {
    body = (await resp.json()) as Record<string, unknown>
  } catch {
    /* prazno tijelo — ostaje {} */
  }
  let poslano: string | null = null
  try {
    poslano = JSON.parse(resp.request().postData() ?? "{}").submitted_query ?? null
  } catch {
    /* nebitno */
  }
  return { status: resp.status(), body, ms, poslano }
}

/** Tekstualna oznaka verdikta onako kako je student vidi. */
async function procitajVerdikt(page: Page): Promise<string> {
  const panel = page.getByRole("status", { name: "Ocjena rješenja" })
  await expect(panel).toBeVisible({ timeout: 90_000 })
  const tekst = await panel.innerText()
  const m = tekst.match(/^(Točno|Djelomično|Netočno|Ocjenjivanje nije uspjelo)/m)
  return m ? m[1] : tekst.split("\n")[0]
}

// ── Glavni prolaz ────────────────────────────────────────────────────────────

test("kompletan prolaz: 88 zadataka kroz sučelje", async ({ page }) => {
  // 🔴 `Object.values` nad objektom s numeričkim ključevima vraća ASCENDENTAN
  // brojčani red, ne redoslijed upisa — zato se pedagoški red uspostavlja ovdje
  // izrijekom (isti red kojim su zadaci nabrojeni u planu).
  const REDOSLIJED = (PLAN.meta.redoslijed_zadataka ?? []) as number[]
  const mapa = PLAN.zadaci
  const svi: PlanZadatak[] = REDOSLIJED.length
    ? REDOSLIJED.map((id) => mapa[String(id)]).filter(Boolean)
    : Object.values(mapa)
  const ukupno = LIMIT > 0 ? Math.min(LIMIT, svi.length) : svi.length

  // ═══ 1. Ulazak ═════════════════════════════════════════════════════════════
  if (dnevnik.nastavak) {
    dnevnik.zapisi("nastavak", `nastavljam prolaz za ${KORISNIK}`, {
      gotovih: dnevnik.stanje.gotovi.length,
    })
    await page.goto("/login")
    await page.getByLabel("Korisničko ime").fill(KORISNIK)
    await page.getByLabel("Lozinka").fill(LOZINKA)
    await page.getByRole("button", { name: "Prijavi se" }).click()
    await expect(page).not.toHaveURL(/\/login/, { timeout: 30_000 })
  } else {
    await page.goto("/register")
    await page.getByLabel("Korisničko ime").fill(KORISNIK)
    await page.getByLabel("Email").fill(EMAIL)
    await page.getByLabel("Lozinka").fill(LOZINKA)
    await snimi(page, "01-registracija")
    await page.getByRole("button", { name: "Registriraj se" }).click()
    await expect(page).not.toHaveURL(/\/register/, { timeout: 30_000 })
    dnevnik.zapisi("racun", `registriran ${KORISNIK} <${EMAIL}>`)

    await expect(
      page.getByRole("heading", { name: new RegExp(`Dobrodošao, ${KORISNIK}`) }),
    ).toBeVisible({ timeout: 30_000 })
    await page.waitForTimeout(800)
    await snimi(page, "02-dashboard-prazan-novak", { fullPage: true })
    // 🔴 `/task` NEMA vlastiti sadržaj: `TaskEntryPage` razriješi preporuku i
    // odmah preusmjeri (`Navigate replace`), pa je jedini kadar te rute prazan
    // skeleton — provjereno snimanjem na probnom prolazu. Zato je „ulaz s
    // preporukom" ovdje KRUPNI PLAN kartice na Dashboardu: naslov preporučenog
    // zadatka, koncept i obrazloženje, dakle ono što student pročita PRIJE
    // nego uđe u zadatak.
    const karticaPreporuke = page
      .locator('[data-slot="card"]')
      .filter({ hasText: /Počni ovdje|Nastavi ovdje/ })
      .first()
    await karticaPreporuke.screenshot({
      path: join(GALERIJA, "04-taskentry-preporuka.png"),
      animations: "disabled",
    })
    dnevnik.zabiljeziSnimku("04-taskentry-preporuka")
    dnevnik.zapisi(
      "kadar",
      "04 = krupni plan kartice preporuke na Dashboardu; ruta /task nema " +
        "vlastiti sadržaj (preusmjerava), pa je njezin jedini kadar prazan skeleton",
    )
    console.log("   📷 04-taskentry-preporuka.png (krupni plan kartice)")

    await nav(page, "Moduli")
    await expect(page.getByRole("heading", { name: "Moduli" })).toBeVisible()
    await page.waitForTimeout(800)
    await snimi(page, "03-moduli-vecina-zakljucana", { fullPage: true })
  }

  // ═══ 2. Stanje petlje ══════════════════════════════════════════════════════
  const obradjeni = new Set<number>(dnevnik.stanje.gotovi)
  for (const id of dnevnik.stanje.preskoceni ?? []) obradjeni.add(id)
  const savjetTrazen = new Set<number>(dnevnik.stanje.hintovi.map((h) => h.task_id))
  let potroseniSavjeti = dnevnik.stanje.hintovi.filter((h) => !h.neuspjeh).length
  let uzastopnihPonavljanja = 0
  let dolazniReason: string | null = null
  let navigacija = "prvi ulazak (nav „Zadatak“)"

  /** Brojač „Preostalo savjeta: N" iz meta retka uz gumb. */
  async function procitajPreostalo(): Promise<number | null> {
    const meta = page.getByText(/Preostalo savjeta:\s*\d+/)
    if (!(await meta.count())) return null
    const m = (await meta.first().innerText()).match(/(\d+)/)
    return m ? Number(m[1]) : null
  }

  /** Klik na „Zatraži hint" + doslovni zapis odgovora. */
  async function zatraziSavjet(
    z: PlanZadatak,
    sql: string,
    errorType: string,
  ): Promise<boolean> {
    const gumb = page.getByRole("button", { name: "Zatraži hint" })
    if (!(await gumb.count())) {
      dnevnik.zapisi("hint", "gumb za savjet nije prikazan (USE_LLM_HINTS?)")
      return false
    }
    const prije = await procitajPreostalo()
    await namjestiKadar(page)
    const [resp] = await Promise.all([
      page.waitForResponse((r) => putanja(r) === "/hint", { timeout: 90_000 }),
      gumb.click(),
    ])
    let tijelo: Record<string, unknown> = {}
    try {
      tijelo = (await resp.json()) as Record<string, unknown>
    } catch {
      /* prazno */
    }
    const uspjeh = resp.status() === 200

    let tekst = ""
    if (uspjeh) {
      const panel = page.getByRole("status", { name: "Savjet" })
      await expect(panel).toBeVisible({ timeout: 30_000 })
      tekst = (await panel.innerText()).trim()
      const izvor = (tijelo.source ?? null) as string | null
      if (izvor === "llm") await snimi(page, "11-hint-llm")
      if (izvor === "fallback") await snimi(page, "12-hint-fallback")
    } else {
      await page.waitForTimeout(800)
      tekst = await page
        .locator("[role=status], [role=alert]")
        .first()
        .innerText()
        .catch(() => "")
      if (tijelo.detail === "hint_rate_limited")
        await snimi(page, "24-hint-potrosen")
    }
    await page.waitForTimeout(1200) // /profile se invalidira → brojač se osvježi
    const poslije = await procitajPreostalo()
    dnevnik.dodajHint({
      task_id: z.task_id,
      naslov: z.naslov,
      koncept: z.koncept,
      tier: z.tier,
      difficulty: z.difficulty,
      sql,
      error_type: errorType,
      tekst,
      izvor: (tijelo.source ?? null) as string | null,
      neuspjeh: uspjeh
        ? null
        : ((tijelo.detail ?? `HTTP ${resp.status()}`) as string),
      preostalo_prije: prije,
      preostalo_poslije: poslije,
    })
    console.log(
      `   💡 savjet (${tijelo.source ?? tijelo.detail ?? resp.status()}) · kredit ${prije} → ${poslije}`,
    )
    if (poslije === 0) await snimi(page, "13-hint-brojac-nula")
    return uspjeh
  }

  /** Riješi jedan zadatak prema planu. */
  async function rijesiZadatak(taskId: number): Promise<boolean> {
    const z = mapa[String(taskId)]
    if (!z) {
      dnevnik.zapisi("nepoznat_zadatak", `zadatak ${taskId} nije u planu`)
      obradjeni.add(taskId)
      return false
    }
    console.log(
      `\n▸ [${obradjeni.size + 1}/${ukupno}] zadatak ${taskId} · ${z.koncept} ` +
        `(M${z.modul}, ${z.tier}, težina ${z.difficulty}) — ${z.naslov}`,
    )

    if (!dnevnik.snimkaZabiljezena("05-zadatak-monaco-i-shema")) {
      await upisiSql(page, z.pokusaji[z.pokusaji.length - 1].query)
      await snimi(page, "05-zadatak-monaco-i-shema", { fullPage: true })
    }
    if (!dnevnik.snimkaZabiljezena("10-hint-gumb-zakljucan-s-razlogom")) {
      const gumb = page.getByRole("button", { name: "Zatraži hint" })
      // 🔴 BEZ klika. Zaključan gumb nosi `aria-disabled="true"` (namjerno —
      // mora ostati fokusabilan da čitač ekrana pročita razlog), a Playwright
      // `aria-disabled` tretira kao „nije spreman za akciju" i `click()` visi do
      // isteka. Razlog je ionako VIDLJIV bez klika: meta redak ispod gumba ga
      // prikazuje čim je gumb zaključan.
      if (
        (await gumb.count()) &&
        (await page.getByText(/Savjet se otključava nakon netočne predaje/).count())
      ) {
        await snimi(page, "10-hint-gumb-zakljucan-s-razlogom")
      }
    }

    const zadnjiNetocan = z.pokusaji
      .map((p, i) => (p.namjera === "netocno" ? i : -1))
      .filter((i) => i >= 0)
      .at(-1)

    // 🔴 Nastavak nakon prekida ne smije ponoviti predaju koja je VEĆ u bazi:
    // prolaz se ne vraća na baseline, pa bi ponavljanje udvostručilo pokušaj i
    // iskrivilo i BKT i statistiku. Predaje idu redom plana, pa je broj već
    // zabilježenih predaja za taj zadatak ujedno indeks od kojeg se nastavlja.
    const vecPredano = dnevnik.stanje.predaje.filter(
      (x) => x.task_id === taskId,
    ).length
    if (vecPredano > 0) {
      dnevnik.zapisi(
        "nastavak_zadatka",
        `zadatak ${taskId}: ${vecPredano} predaja već u bazi — nastavljam od ${vecPredano + 1}.`,
      )
    }

    for (let i = vecPredano; i < z.pokusaji.length; i++) {
      const p = z.pokusaji[i]
      const ishod = await predaj(page, p.query)

      if (ishod.status !== 200) {
        dnevnik.zapisi("predaja_pala", `HTTP ${ishod.status} na zadatku ${taskId}`, {
          tijelo: ishod.body,
        })
        throw new Error(
          `Predaja nije prošla (HTTP ${ishod.status}) — prolaz se prekida ` +
            `umjesto da se zaobiđe. V. dnevnik.`,
        )
      }
      // 🔴 Dokaz da je u bazu otišlo ono što je upisano u editor.
      if (ishod.poslano != null && norm(ishod.poslano) !== norm(p.query)) {
        throw new Error(
          `Predani upit se razlikuje od upisanog!\nupisano: ${norm(p.query)}\n` +
            `predano: ${norm(ishod.poslano)}`,
        )
      }

      const verdict = await procitajVerdikt(page)
      const fb = (ishod.body.feedback ?? {}) as Record<string, unknown>
      const rec = (ishod.body.recommendation ?? {}) as Record<string, unknown>
      const noviBedzevi = (ishod.body.new_badges ?? []) as string[]
      const et = (fb.error_type ?? null) as string | null

      const zapis = dnevnik.dodajPredaju({
        task_id: taskId,
        koncept: z.koncept,
        modul: z.modul,
        tier: z.tier,
        difficulty: z.difficulty,
        naslov: z.naslov,
        navigacija,
        dolazni_reason: dolazniReason,
        pokusaj_br: i + 1,
        mutacija: p.mutacija,
        opis_greske: p.mutacija ? p.opis : null,
        sql: p.query,
        ocekivano: p.ocekivano,
        verdict,
        is_correct: (fb.is_correct ?? null) as boolean | null,
        error_type: et,
        detail: (fb.detail ?? null) as string | null,
        xp: (ishod.body.xp ?? 0) as number,
        xp_delta: (ishod.body.xp_delta ?? 0) as number,
        level: (ishod.body.level ?? 0) as number,
        current_streak: (ishod.body.current_streak ?? 0) as number,
        new_badges: noviBedzevi,
        already_solved: (ishod.body.already_solved ?? false) as boolean,
        rec_task_id: (rec.task_id ?? null) as number | null,
        rec_concept: (rec.concept ?? null) as string | null,
        rec_reason: (rec.reason ?? null) as string | null,
        trajanje_ms: ishod.ms,
      })
      const odstupanje = p.ocekivano !== (et ?? "correct")
      console.log(
        `   ${i + 1}. ${p.mutacija ?? "točno rješenje"} → ${verdict} (${et ?? "—"})` +
          ` · +${zapis.xp_delta} XP · ukupno ${zapis.xp}, lvl ${zapis.level} · ${ishod.ms} ms` +
          (odstupanje ? `  ⚠️ očekivano ${p.ocekivano}` : ""),
      )
      if (odstupanje) {
        dnevnik.zapisi(
          "odstupanje",
          `zadatak ${taskId}, ${p.mutacija}: očekivano ${p.ocekivano}, dobiveno ${et ?? "correct"}`,
        )
      }

      // ── Kadrovi vezani uz ishod ──────────────────────────────────────────
      if (verdict === "Netočno") await snimi(page, "07-feedback-netocno")
      if (verdict === "Djelomično") await snimi(page, "08-feedback-djelomicno")
      if (et === "plan_mismatch") await snimi(page, "09-feedback-plan-mismatch")
      if (et === "timeout") await snimi(page, "25-feedback-timeout")
      if (et === "explain_submitted") await snimi(page, "26-feedback-explain-submitted")
      if (verdict === "Točno") await snimi(page, "06-feedback-tocno", { uPokretu: true })
      if (noviBedzevi.length > 0) {
        await snimi(page, "15-bedz-otkljucan", { uPokretu: true })
        dnevnik.zapisi("bedz", `otključan bedž: ${noviBedzevi.join(", ")}`, {
          task_id: taskId,
          xp: zapis.xp,
        })
      }
      const prethodni = dnevnik.stanje.predaje.at(-2)
      if (prethodni && zapis.level > prethodni.level) {
        await snimi(page, "14-level-up", { uPokretu: true })
        dnevnik.zapisi("level", `novi level ${zapis.level}`, {
          xp: zapis.xp,
          task_id: taskId,
        })
      }

      // ── Savjet: nakon ZADNJE planirane netočne predaje na tom zadatku ────
      if (
        fb.is_correct === false &&
        i === zadnjiNetocan &&
        !savjetTrazen.has(taskId)
      ) {
        const uPlanu = (z.hint || HINT_SVUDA) && potroseniSavjeti < NAJVISE_SAVJETA
        // 🔴 Kadar potrošenog kredita traži da je kredit STVARNO nula, a to
        // tvrdi SUČELJE (brojač iz `/profile`), ne naš brojač. Da se oslanja na
        // naš, jedan klik bi otišao u stvarni zahtjev i potrošio šesti savjet —
        // izmjereno na probnom prolazu, prije ispravka.
        const zaKadarPotrosenog =
          !uPlanu &&
          !dnevnik.snimkaZabiljezena("24-hint-potrosen") &&
          (await procitajPreostalo()) === 0
        if (uPlanu || zaKadarPotrosenog) {
          savjetTrazen.add(taskId)
          if (await zatraziSavjet(z, p.query, et ?? "?")) potroseniSavjeti += 1
        }
      }

      if (fb.is_correct === true) {
        dnevnik.oznaciGotov(taskId)
        obradjeni.add(taskId)
        return true
      }
    }
    dnevnik.zapisi(
      "nerijeseno",
      `zadatak ${taskId} nije došao do točnog rješenja unatoč planu`,
    )
    dnevnik.preskoci(taskId)
    obradjeni.add(taskId)
    return false
  }

  /** Kadrovi na pola puta (Dashboard + Moduli za usporedbu s početkom). */
  async function usputneSnimke(): Promise<void> {
    if (obradjeni.size !== Math.floor(ukupno / 2)) return
    if (dnevnik.snimkaZabiljezena("19-dashboard-na-pola")) return
    await nav(page, "Dashboard")
    await page.waitForTimeout(1200)
    await snimi(page, "19-dashboard-na-pola", { fullPage: true })
    await nav(page, "Moduli")
    await page.waitForTimeout(1200)
    await snimi(page, "20-moduli-otkljucani", { fullPage: true })
  }

  /** Traži preporuku kroz nav „Zadatak" → `/task` → redirect. */
  async function traziPreporuku(): Promise<{
    task_id: number | null
    concept: string | null
    reason: string | null
  }> {
    const cekanje = page
      .waitForResponse((r) => putanja(r) === "/next-task", { timeout: 15_000 })
      .catch(() => null)
    await nav(page, "Zadatak")
    const resp = await cekanje
    let body: { task_id?: number; concept?: string; reason?: string } | null = null
    if (resp) {
      try {
        body = (await resp.json()) as NonNullable<typeof body>
      } catch {
        /* prazno tijelo */
      }
    }

    // 🔴 Odsutnost mrežnog odgovora NE ZNAČI „nema preporuke". `useNextTask` ima
    // `staleTime: 60 s`, pa klik na „Zadatak" ubrzo nakon Dashboarda posluži
    // preporuku iz predmemorije BEZ zahtjeva. Prva verzija je taj slučaj čitala
    // kao „preporučivač je stao" i skakala na Module — dakle zaključivala iz
    // izostanka dokaza. Ishod se zato uvijek potvrđuje NA EKRANU: ili smo na
    // zadatku, ili stoji završna kartica.
    await Promise.race([
      page.waitForURL(/\/task\/\d+/, { timeout: 40_000 }).catch(() => null),
      page
        .getByRole("heading", {
          name: /Nema novih zadataka|Svi koncepti savladani/,
        })
        .waitFor({ timeout: 40_000 })
        .catch(() => null),
    ])
    const naZadatku = page.url().match(/\/task\/(\d+)/)
    if (!body) {
      dnevnik.zapisi(
        "cache",
        "/next-task poslužen iz predmemorije — ishod očitan s ekrana, reason nepoznat",
        { url: page.url() },
      )
      return {
        task_id: naZadatku ? Number(naZadatku[1]) : null,
        concept: null,
        reason: null,
      }
    }
    return {
      task_id: body.task_id ?? (naZadatku ? Number(naZadatku[1]) : null),
      concept: body.concept ?? null,
      reason: body.reason ?? null,
    }
  }

  // ── 2a. Faza preporučivača ───────────────────────────────────────────────
  let sigurnosniBrojac = 0
  while (
    dnevnik.stanje.faza === "preporucivac" &&
    obradjeni.size < ukupno &&
    sigurnosniBrojac++ < 400
  ) {
    let taskId: number | null = null

    const cta = page.getByRole("link", { name: /Sljedeći zadatak/i })
    if (await cta.count()) {
      const href = await cta.getAttribute("href")
      const kandidat = Number(href?.match(/\/task\/(\d+)/)?.[1] ?? 0)
      const zadnja = dnevnik.stanje.predaje.at(-1)
      if (kandidat && !obradjeni.has(kandidat)) {
        dolazniReason = zadnja?.rec_reason ?? null
        navigacija = "CTA „Sljedeći zadatak“"
        await cta.click()
        await expect(page).toHaveURL(new RegExp(`/task/${kandidat}$`))
        taskId = kandidat
        uzastopnihPonavljanja = 0
      } else if (kandidat) {
        uzastopnihPonavljanja += 1
        dnevnik.zapisi(
          "preporuka_ponavlja",
          `CTA nudi već obrađen zadatak ${kandidat} (reason: ${zadnja?.rec_reason})`,
          { uzastopno: uzastopnihPonavljanja },
        )
      }
    }

    if (taskId == null) {
      const rec = await traziPreporuku()
      dolazniReason = rec.reason
      navigacija = "nav „Zadatak“ → /next-task"
      if (rec.task_id == null) {
        dnevnik.zapisi(
          "preporucivac_stao",
          `preporučivač više ne nudi zadatke (reason: ${rec.reason})`,
          { rijeseno: obradjeni.size, preostalo: ukupno - obradjeni.size },
        )
        await page.waitForTimeout(600)
        await snimi(page, "22-sve-savladano")
        dnevnik.stanje.faza = "moduli"
        dnevnik.spremi()
        break
      }
      if (obradjeni.has(rec.task_id)) {
        uzastopnihPonavljanja += 1
        dnevnik.zapisi(
          "preporuka_ponavlja",
          `preporuka vodi na već obrađen zadatak ${rec.task_id} (reason: ${rec.reason})`,
          { uzastopno: uzastopnihPonavljanja },
        )
        if (uzastopnihPonavljanja >= 3) {
          dnevnik.zapisi(
            "preporucivac_stao",
            `tri uzastopne preporuke vode na već obrađene zadatke ` +
              `(reason: ${rec.reason}) — prelazim na klik po konceptu u Modulima`,
            { rijeseno: obradjeni.size, preostalo: ukupno - obradjeni.size },
          )
          dnevnik.stanje.faza = "moduli"
          dnevnik.spremi()
          break
        }
        continue
      }
      taskId = rec.task_id
      uzastopnihPonavljanja = 0
    }

    await rijesiZadatak(taskId)
    await usputneSnimke()
  }

  // ── 2b. Faza Modula (klik po konceptu) ───────────────────────────────────
  if (obradjeni.size < ukupno) {
    dnevnik.stanje.faza = "moduli"
    dnevnik.spremi()

    const poKonceptu = new Map<string, PlanZadatak[]>()
    for (const z of svi) {
      if (obradjeni.has(z.task_id)) continue
      const lista = poKonceptu.get(z.koncept) ?? []
      lista.push(z)
      poKonceptu.set(z.koncept, lista)
    }

    for (const [koncept, lista] of poKonceptu) {
      const modul = lista[0].modul
      for (let i = 0; i < lista.length; i++) {
        if (obradjeni.size >= ukupno) break
        await nav(page, "Moduli")
        await expect(page.getByRole("heading", { name: "Moduli" })).toBeVisible()
        const kartica = page.locator(`#module-${modul}`)
        // 🔴 Transverzalni modul (broj 0) NIJE `Collapsible` kao ostali: renderira
        // se kao sekcija s konceptima odmah vidljivima, pa nema gumb „Koncepti
        // modula …". Prva verzija je izostanak gumba čitala kao „nema kartice" i
        // odustajala — zbog toga je 5 zadataka modula 0 ostalo neposjećeno u
        // prvom pokretanju. Gumb se zato klika SAMO ako postoji.
        const trigger = kartica.getByRole("button", { name: /^Koncepti modula / })
        if (await trigger.count()) {
          await trigger.click()
        } else if (!(await kartica.count())) {
          dnevnik.zapisi("modul_bez_kartice", `nema sekcije za modul ${modul}`)
          break
        }
        const veza = kartica.locator(`a[href="/koncept/${koncept}"]`)
        if (!(await veza.count())) {
          dnevnik.zapisi(
            "koncept_neklikabilan",
            `koncept ${koncept} (M${modul}) nije klikabilan — zaključan ili bez zadataka`,
            { preostalo_zadataka: lista.length - i },
          )
          break
        }
        dolazniReason = null
        navigacija = `klik po konceptu u Modulima (${koncept})`
        await veza.click()
        await expect(page).toHaveURL(/\/task\/\d+/, { timeout: 40_000 })
        const id = Number(page.url().match(/\/task\/(\d+)/)?.[1] ?? 0)
        if (obradjeni.has(id)) {
          dnevnik.zapisi(
            "koncept_vraca_obradjeno",
            `klik na koncept ${koncept} vraća već obrađen zadatak ${id}`,
          )
          break
        }
        await rijesiZadatak(id)
        await usputneSnimke()
      }
    }
  }

  // ═══ 3. Završni kadrovi ════════════════════════════════════════════════════
  await nav(page, "Dashboard")
  await page.waitForTimeout(1500)
  await snimi(page, "21-dashboard-zavrsni", { fullPage: true })

  await nav(page, "Moduli")
  await page.waitForTimeout(1500)
  await snimi(page, "23-moduli-zavrsni", { fullPage: true })

  await nav(page, "Profil")
  await page.waitForTimeout(3000)
  // 🔴 Dva RAZLIČITA kadra, ne dvaput ista `fullPage` stranica: Profil je dug,
  // pa se bedževi i krivulje snimaju svaki u svom prozoru (probni prolaz je
  // pokazao da su dvije `fullPage` snimke istog ekrana bajt-identične).
  await page
    .getByText("Bedževi", { exact: true })
    .first()
    .scrollIntoViewIfNeeded()
    .catch(() => null)
  await page.waitForTimeout(600)
  await snimi(page, "16-profil-bedzevi")
  await page
    .getByText("Krivulje znanja (BKT)")
    .first()
    .scrollIntoViewIfNeeded()
    .catch(() => null)
  await page.waitForTimeout(900)
  await snimi(page, "17-profil-krivulje-mastery")
  await snimi(page, "27-profil-cijela-stranica", { fullPage: true })

  await nav(page, "Ljestvica")
  await page.waitForTimeout(1500)
  await snimi(page, "18-ljestvica", { fullPage: true })

  if (!dnevnik.snimkaZabiljezena("22-sve-savladano")) {
    await nav(page, "Zadatak")
    await page.waitForTimeout(4000)
    if (!/\/task\/\d+/.test(page.url())) await snimi(page, "22-sve-savladano")
  }

  // ═══ 4. Sažetak ════════════════════════════════════════════════════════════
  const p = dnevnik.stanje.predaje
  const zadnja = p.at(-1)
  console.log(`
════════════════════════════════════════════════
 PROLAZ ZAVRŠEN
   riješenih zadataka : ${dnevnik.stanje.gotovi.length} / ${ukupno}
   preskočenih        : ${(dnevnik.stanje.preskoceni ?? []).length}
   predaja            : ${p.length}
   savjeta            : ${dnevnik.stanje.hintovi.length}
   XP                 : ${zadnja?.xp ?? 0}  ·  level ${zadnja?.level ?? 1}
   snimki             : ${dnevnik.stanje.snimke.length}
   stanje             : e2e-prolaz/.stanje/stanje.json
════════════════════════════════════════════════`)
  expect(dnevnik.stanje.predaje.length).toBeGreaterThan(0)
})
