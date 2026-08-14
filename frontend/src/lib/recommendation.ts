/**
 * Mapiranje Recommenderovog STROJNOG `reason` stringa → ljudski hrvatski tekst
 * + semantička kategorija (Faza 4.2; 4.3 nasljeđuje isti mapper za /attempt
 * recommendation).
 *
 * Izvor istine za vrijednosti (pročitano, ne pretpostavljeno):
 *  - backend/prolog/rules.pl:81-90 → weak_with_prereqs_met, partial_continuation,
 *    unlock_new, fallback
 *  - backend/agents/recommender_logic.py:232-237 → exhausted (task_id=null,
 *    concept postavljen), no_recommendation (sve null)
 *  - backend/agents/recommender_agent.py:108 → error (agent exception put)
 *  - backend/agents/coordinator.py:63 → recommend_timeout (samo u /attempt
 *    recommendation polju — pokriveno za 4.3)
 */
import type { NextTaskResponse } from "@/lib/api/types"

/** Kako UI tretira preporuku: zadatak / završno stanje / oporavljiva greška. */
export type RecommendationKind = "task" | "done" | "error"

const REASON_TEXT: Record<string, string> = {
  weak_with_prereqs_met:
    "Ovaj koncept ti je trenutno najslabiji, a preduvjete već imaš — vrijeme je da ga ojačaš.",
  partial_continuation:
    "Nastavi gdje si stao — ovaj koncept je djelomično savladan.",
  unlock_new: "Preduvjeti su ispunjeni — vrijeme je za novi koncept.",
  fallback: "Sljedeći logičan korak na tvom putu učenja.",
  exhausted:
    "Riješio si sve dostupne zadatke za preporučeni koncept — nove preporuke stižu kako budeš napredovao.",
  no_recommendation: "Trenutno nema koncepta za preporuku — sve je savladano.",
  // Rezervna grana preporučivača: ponestalo je NERIJEŠENIH zadataka unutar
  // dosega, pa se nudi već riješen zadatak. Task ekran ga označava bedžom
  // „Riješeno"; ponovna predaja ne nosi XP, ali diže mastery kroz BKT.
  repeat_practice:
    "Ovaj si zadatak već riješio — ponovi ga za vježbu. Ne nosi XP, ali učvršćuje koncept.",
}

const FALLBACK_TEXT = "Preporučeni sljedeći korak."

/** Ljudski tekst za reason; nepoznat/izostavljen reason → neutralni fallback. */
export function reasonText(reason: string | null | undefined): string {
  if (!reason) return FALLBACK_TEXT
  return REASON_TEXT[reason] ?? FALLBACK_TEXT
}

/**
 * Legitimna završna stanja su ZATVOREN skup (recommender_logic.py:232/237);
 * error stringovi su otvoren skup (agenti/coordinator mogu dodati nove u 4.3).
 * Zato fail-CLOSED: nepoznat reason uz task_id=null → "error" (retry), nikad
 * slavljenička kartica na grešci.
 */
const DONE_REASONS = new Set(["exhausted", "no_recommendation"])

/**
 * Semantika preporuke: task_id != null → zadatak; null s poznatim završnim
 * reasonom → legitimno završno stanje; sve ostalo → oporavljiva greška.
 *
 * NAPOMENA za potrošače: "done" NIJE nužno "sve savladano" — `exhausted` znači
 * da je ponestalo zadataka za PREPORUČENI koncept (user može imati nesavladane
 * koncepte); samo `no_recommendation` znači potpunu savladanost.
 */
export function recommendationKind(rec: NextTaskResponse): RecommendationKind {
  if (rec.task_id != null) return "task"
  if (rec.reason != null && DONE_REASONS.has(rec.reason)) return "done"
  return "error"
}
