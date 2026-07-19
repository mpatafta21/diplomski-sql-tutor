/**
 * Agregacija statistike povijesti (Faza 4.4a) — ČISTA funkcija (testabilna).
 *
 * 🔴 Računa se nad PROZOROM (zadnjih ≤100 pokušaja), NE nad cijelom poviješću —
 * API nema agregat, pa je prozor jedini iskren način (labeliranje je obavezno u
 * UI-ju: "Zadnjih N pokušaja", nikad gol "Accuracy"). `windowSize` je stvarni
 * broj promatranih redaka; ukupan broj pokušaja dolazi ODVOJENO iz Page.total.
 *
 * Verdict se derivira ISKLJUČIVO kroz deriveVerdict (isti izvor kao task screen
 * i redak povijesti) — nema druge definicije "točno/djelomično".
 */
import type { AttemptItem } from "@/lib/api/types"
import { deriveVerdict } from "@/lib/feedback"

export interface AttemptStats {
  /** broj promatranih pokušaja u prozoru (≤ limit) */
  windowSize: number
  correct: number
  partial: number
  /** udio točnih u prozoru [0,1]; 0 ako je prozor prazan */
  accuracy: number
  /** udio djelomičnih (row_mismatch) u prozoru [0,1] */
  partialShare: number
}

export function summarizeAttempts(items: AttemptItem[]): AttemptStats {
  const windowSize = items.length
  let correct = 0
  let partial = 0
  for (const it of items) {
    const verdict = deriveVerdict(it.is_correct, it.error_type)
    if (verdict === "correct") correct++
    else if (verdict === "partial") partial++
  }
  return {
    windowSize,
    correct,
    partial,
    accuracy: windowSize > 0 ? correct / windowSize : 0,
    partialShare: windowSize > 0 ? partial / windowSize : 0,
  }
}
