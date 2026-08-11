/** Zabilježi brojke PRIJE suitea — teardown ih uspoređuje. Poučak N-3: ne tvrdi „čisto", dokaži. */
import { writeFileSync } from "node:fs"
import { counts, COUNTED_TABLES } from "./db"

export const BASELINE_FILE = new URL("./.baseline.json", import.meta.url)
  .pathname

export default function globalSetup() {
  const before = counts()
  writeFileSync(BASELINE_FILE, JSON.stringify(before, null, 1))
  console.log("\n── BROJKE PRIJE SUITEA ──")
  for (const t of COUNTED_TABLES) console.log(`   ${t.padEnd(24)} ${before[t]}`)
  console.log("")
}
