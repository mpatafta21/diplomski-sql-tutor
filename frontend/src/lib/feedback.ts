/**
 * Mapiranje /attempt feedbacka → verdict + hrvatska poruka (Faza 4.3c).
 *
 * 🔴 TRI stanja (ERRATA #8-revidiran): `verdict` kolona ne postoji u bazi,
 * ali je PARTIAL izvediv iz odgovora — backend row_mismatch ⇔ interni verdict
 * "partial" (i polovičan XP; živo: row_mismatch → xp_delta 5/8). Bez ovoga
 * student s točnim stupcima a krivim redoslijedom
 * vidi crveno "Netočno" uz +5 XP — kontradiktoran signal.
 *
 * 🔴 error_type NAZIVI VARAJU (evaluation.py, mapirano po ZNAČENJU):
 *  - syntax_error  = PRAZAN/neprepoznatljiv upit (sqlparse), NE prava sintaksa!
 *  - execution_error = prave SQL greške (SELEKT → PG poruka) + ostale PG greške
 * FAIL-CLOSED (obrazac recommendation.ts): nepoznat error_type → generička
 * greška, NIKAD slavlje.
 */

export type Verdict = "correct" | "partial" | "incorrect" | "unknown"

/**
 * Derivacija verdicta: is_correct → correct; netočno + row_mismatch → partial;
 * ostalo netočno → incorrect. is_correct null (degradirani odgovor) → unknown.
 *
 * ⚠️ Partial se derivira iz error_type, NE iz xp_delta: backend row_mismatch ⇔
 * interni verdict "partial" TOČNO (evaluation.py:186 je jedini partial izvor),
 * dok je xp_delta best-effort read (Gamification teče PARALELNO s RESPOND-om,
 * coordinator.py odluka 7.3) — na degradiranom putu xp_delta=0 bi partial
 * pokušaj obojio crvenim "Netočno" uz poruku "Stupci su točni…" (upravo
 * kontradikcija koju ovaj modul uklanja). XP čip neovisno prikazuje xp_delta.
 */
export function deriveVerdict(
  isCorrect: boolean | null | undefined,
  errorType: string | null | undefined,
): Verdict {
  if (isCorrect === true) return "correct"
  if (isCorrect === false)
    return errorType === "row_mismatch" ? "partial" : "incorrect"
  return "unknown"
}

/** Glavna hrvatska poruka po error_type (izvor značenja: evaluation.py). */
const ERROR_TEXT: Record<string, string> = {
  syntax_error: "Nisi poslao upit — editor je prazan ili sadržaj nije SQL.",
  execution_error: "Greška u SQL-u — baza nije mogla izvršiti upit.",
  timeout: "Tvoj upit je predugo trajao — pojednostavi ga pa pokušaj ponovno.",
  unsupported_eval:
    "Ovaj tip zadatka se još ne ocjenjuje automatski — rješenje vježbaj kroz Run.",
  empty_result: "Upit nije vratio nijedan redak, a rezultat se očekuje.",
  wrong_columns: "Upit vraća krive stupce.",
  row_mismatch: "Skoro! Stupci su točni, ali redovi nisu.",
}

const FALLBACK_ERROR_TEXT =
  "Ocjenjivanje nije uspjelo — pokušaj ponovno predati rješenje."

/** Poruka za prikaz: correct ima svoju, ostalo iz mape (fail-closed fallback). */
export function feedbackText(
  verdict: Verdict,
  errorType: string | null | undefined,
): string {
  if (verdict === "correct") return "Bravo — rezultat je točan!"
  if (verdict === "unknown") return FALLBACK_ERROR_TEXT
  if (errorType && errorType in ERROR_TEXT) return ERROR_TEXT[errorType]
  return FALLBACK_ERROR_TEXT
}

/**
 * Kako prikazati feedback.detail (Stage 0b — pedagoška dopuna, NIKAD zamjena
 * za hrvatsku glavnu poruku):
 *  - "text"   → hrvatski pedagoški detail (wrong_columns nabraja stupce,
 *               empty_result broj redova) — čitljiva dopuna
 *  - "mono"   → sirovi/tehnički string: PG poruke (execution_error/timeout,
 *               LINE/caret ↔ Monaco) i INTERNI ENGLESKI row_mismatch stringovi
 *               ("Row 0 differs", "Set diff: …") — diskretan mono blok označen
 *               kao tehnički detalj, da ne izgleda kao da je sustav pukao
 *  - "hidden" → bez detaila (correct, ili detail ne postoji)
 */
export type DetailPresentation = "text" | "mono" | "hidden"

const TEXT_DETAIL_TYPES = new Set([
  "wrong_columns",
  "empty_result",
  "syntax_error",
  "unsupported_eval",
])
const MONO_DETAIL_TYPES = new Set([
  "execution_error",
  "timeout",
  "row_mismatch",
])

export function detailPresentation(
  errorType: string | null | undefined,
  detail: string | null | undefined,
): DetailPresentation {
  if (!detail) return "hidden"
  if (errorType && TEXT_DETAIL_TYPES.has(errorType)) return "text"
  if (errorType && MONO_DETAIL_TYPES.has(errorType)) return "mono"
  // Nepoznat error_type s detaljem → diskretno mono (fail-closed, ne kao
  // glavna poruka).
  return "mono"
}
