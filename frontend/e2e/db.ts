/**
 * Pristup bazi za e2e higijenu — kroz `docker compose exec psql`, bez novog dependencyja
 * i bez ijedne izmjene backenda.
 *
 * 🔴 Tablice se brišu OVIM REDOM (djeca prije roditelja). `users` ide zadnji; CASCADE
 * bi pokrio dio, ali se ne oslanjamo na njega — #9 disciplina: Submit stvara redove u
 * attempts/xp_log/skill_mastery/skill_mastery_history/streaks, a badge i preporuke
 * dolaze iz gamifikacije i recommendera.
 */
import { execFileSync } from "node:child_process"

/** Prefiks po kojem `prepare_eval_baseline.py` prepoznaje i čisti testne račune. */
export const E2E_PREFIX = "e2e_"

/** Tablice koje se broje prije/poslije — dokaz da je teardown stvarno očistio. */
export const COUNTED_TABLES = [
  "users",
  "attempts",
  "xp_log",
  "skill_mastery",
  "skill_mastery_history",
  "streaks",
  "user_badges",
  "misconceptions",
  "recommendations_log",
  "agent_messages_log",
] as const

const COMPOSE_ARGS = [
  "compose",
  "exec",
  "-T",
  "postgres-main",
  "psql",
  "-U",
  "tutor",
  "-d",
  "tutor_main",
  "-At",
  "-c",
]

function psql(sql: string): string {
  return execFileSync("docker", [...COMPOSE_ARGS, sql], {
    encoding: "utf-8",
    cwd: new URL("../..", import.meta.url).pathname,
    stdio: ["ignore", "pipe", "pipe"],
  }).trim()
}

export function counts(): Record<string, number> {
  const sql = COUNTED_TABLES.map(
    (t) => `SELECT '${t}', count(*)::text FROM ${t}`,
  ).join(" UNION ALL ")
  const out: Record<string, number> = {}
  for (const line of psql(sql).split("\n")) {
    const [table, n] = line.split("|")
    if (table) out[table] = Number(n)
  }
  return out
}

/**
 * Obriši SVE `e2e_` račune i sve što o njima visi.
 *
 * 🔴 `agent_messages_log` NIJE ovdje i ne može biti — tablica nema `user_id`
 * (ERRATA #40/#46). Njezin rast ostaje vidljiv u before/after brojkama i to je namjerno:
 * broj koji se ne može očistiti mora biti VIDLJIV, ne prešućen.
 */
export function purgeE2eUsers(): Record<string, number> {
  const ids = `(SELECT id FROM users WHERE username LIKE '${E2E_PREFIX}%')`
  const deleted: Record<string, number> = {}
  /**
   * 🔴 REDOSLIJED JE ODREĐEN FK GRAFOM, ne abecedom ni intuicijom. Provjereno upitom nad
   * `information_schema` (2026-08-10):
   *
   *   xp_log                → attempts (attempt_id), users
   *   skill_mastery_history → attempts (attempt_id), users
   *   attempts              → users
   *   skill_mastery / streaks / user_badges / misconceptions / recommendations_log → users
   *
   * Dakle `attempts` NE SMIJE ići prvi — dvije tablice vise o njemu. Isti redoslijed
   * već koristi `backend/scripts/purge_demo_users.py:61-75`.
   */
  const order = [
    "xp_log",
    "skill_mastery_history",
    "attempts",
    "skill_mastery",
    "streaks",
    "user_badges",
    "misconceptions",
    "recommendations_log",
  ]
  for (const table of order) {
    // Tablica možda ne postoji u nekoj migraciji — ne rušimo teardown zbog toga.
    try {
      deleted[table] = Number(
        psql(`WITH d AS (DELETE FROM ${table} WHERE user_id IN ${ids} RETURNING 1)
              SELECT count(*)::text FROM d`),
      )
    } catch (e) {
      deleted[table] = -1
      console.warn(
        `  ⚠️  ${table}: brisanje nije uspjelo — ${(e as Error).message.split("\n")[0]}`,
      )
    }
  }
  deleted["users"] = Number(
    psql(`WITH d AS (DELETE FROM users WHERE username LIKE '${E2E_PREFIX}%' RETURNING 1)
          SELECT count(*)::text FROM d`),
  )
  return deleted
}

export function remainingE2eUsers(): number {
  return Number(
    psql(
      `SELECT count(*)::text FROM users WHERE username LIKE '${E2E_PREFIX}%'`,
    ),
  )
}
