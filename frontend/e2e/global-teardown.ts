/**
 * Teardown: obriši `e2e_` račune i DOKAŽI brojkom da je baza vraćena na baseline.
 *
 * 🔴 Ako ijedna tablica osim `agent_messages_log` ne padne natrag na polaznu brojku,
 * teardown puca. Suite koji zagađuje bazu gori je od suitea koji ne postoji (#9, #40).
 */
import { readFileSync, unlinkSync } from "node:fs"
import { counts, COUNTED_TABLES, purgeE2eUsers, remainingE2eUsers } from "./db"
import { BASELINE_FILE } from "./global-setup"

export default function globalTeardown() {
  const before: Record<string, number> = JSON.parse(
    readFileSync(BASELINE_FILE, "utf-8"),
  )

  console.log("\n── TEARDOWN ──")
  const deleted = purgeE2eUsers()
  for (const [t, n] of Object.entries(deleted)) {
    if (n !== 0) console.log(`   obrisano  ${t.padEnd(24)} ${n}`)
  }

  const after = counts()
  console.log("\n── PRIJE → POSLIJE ──")
  const drift: string[] = []
  for (const t of COUNTED_TABLES) {
    const d = after[t] - before[t]
    const mark = d === 0 ? "✅" : t === "agent_messages_log" ? "⚠️ " : "🔴"
    console.log(
      `   ${mark} ${t.padEnd(24)} ${before[t]} → ${after[t]}  (${d >= 0 ? "+" : ""}${d})`,
    )
    if (d !== 0 && t !== "agent_messages_log")
      drift.push(`${t}: ${before[t]} → ${after[t]}`)
  }

  const left = remainingE2eUsers()
  if (left > 0) drift.push(`preostalo ${left} e2e_ računa`)

  const logDelta = after["agent_messages_log"] - before["agent_messages_log"]
  if (logDelta > 0) {
    console.log(
      `\n   ⚠️  agent_messages_log +${logDelta} zapisa OSTAJE — tablica nema \`user_id\`,\n` +
        `      pa je nijedan cleanup po korisniku ne dohvaća (ERRATA #40/#46).\n` +
        `      Briše se samo TRUNCATE-om u prepare_eval_baseline.py, prije evaluacije.`,
    )
  }

  try {
    unlinkSync(BASELINE_FILE)
  } catch {
    /* nebitno */
  }

  if (drift.length) {
    console.error("\n🔴 TEARDOWN NIJE ČIST:")
    for (const d of drift) console.error(`   • ${d}`)
    throw new Error("e2e teardown je ostavio redove u bazi — v. ispis iznad")
  }
  console.log(
    "\n✅ Baza vraćena na baseline (osim agent_messages_log, v. gore).\n",
  )
}
