/**
 * Mastery helperi (Faza 4.2) — klijentski join /profile.mastery (concept→p_l)
 * × /modules (concept→ime/tier/modul) + mapiranje P(L) na tokene mastery skale.
 *
 * Prag "savladano" NIJE ovdje — dolazi iz /profile.mastery_threshold
 * (backend istina, invarijanta #6).
 */
import type { ConceptNode, MasteryItem, ModuleNode } from "@/lib/api/types"

export interface ConceptInfo extends ConceptNode {
  moduleName: string
  moduleNumber: number
}

/** Index concept code → koncept + modul (izvor imena za mastery prikaze). */
export function buildConceptIndex(
  modules: ModuleNode[],
): Map<string, ConceptInfo> {
  const index = new Map<string, ConceptInfo>()
  for (const m of modules) {
    for (const c of m.concepts) {
      index.set(c.code, { ...c, moduleName: m.name, moduleNumber: m.number })
    }
  }
  return index
}

/** Mastery stavka obogaćena taksonomijom (null name se NE izmišlja — skip). */
export interface EnrichedMastery {
  code: string
  name: string
  tier: string
  moduleName: string
  p_l: number
  /** Meta za klik → `/task/<id>` (self-test fix 4.6-eval). null = koncept nema
   *  vlastitog zadatka (glue/sekundarni) → nije klikabilan. */
  entryTaskId: number | null
}

/** Join + sort po p_l uzlazno. Koncepti bez unosa u /modules se preskaču. */
export function enrichMastery(
  mastery: MasteryItem[],
  index: Map<string, ConceptInfo>,
): EnrichedMastery[] {
  const out: EnrichedMastery[] = []
  for (const item of mastery) {
    const info = index.get(item.concept)
    if (!info) continue
    out.push({
      code: item.concept,
      name: info.name,
      tier: info.tier,
      moduleName: info.moduleName,
      p_l: item.p_l,
      entryTaskId: info.entry_task_id ?? null,
    })
  }
  out.sort((a, b) => a.p_l - b.p_l)
  return out
}

/**
 * P(L) → stopa mastery skale (MASTER.md §2.3, 5 stopova).
 * Bucket granice su VIZUALNA kvantizacija kontinuirane skale (design-system
 * odluka), ne backend semantika — backend prag savladanosti je
 * mastery_threshold iz /profile.
 *
 * JEDAN izvor granica za SVE potrošače skale: Tailwind klase (barovi) i CSS
 * varijable (SVG stroke krivulja, 4.4b). Bez ovog helpera dvije bi kopije
 * granica tiho divergirale — bar i krivulja istog koncepta u različitim bojama.
 */
/**
 * Ima li koncept ijedan AKTIVAN primarni zadatak (`primary_task_count > 0`).
 *
 * 🔴 JEDAN izvor ovog predikata za cijeli frontend. Konzumenti:
 *  - `deriveProgress` (lib/progress.ts) — stanje `unavailable` na Module overviewu
 *  - `categorizeConcept` (lib/mastery-history.ts) — skupine (B)/(C) na Profilu
 * Prije 4.4b pravilo je bilo prepisano na oba mjesta; promjena praga na jednom
 * (npr. subfloor `<2` iz errate #27) tiho bi razišla klasifikaciju istog
 * koncepta na dva ekrana. Mijenjati SAMO ovdje.
 */
export function hasOwnTasks(
  concept: Pick<ConceptNode, "primary_task_count">,
): boolean {
  return concept.primary_task_count > 0
}

export type MasteryStep = 0 | 25 | 50 | 75 | 100

export function masteryStep(pL: number): MasteryStep {
  if (pL >= 0.875) return 100
  if (pL >= 0.625) return 75
  if (pL >= 0.375) return 50
  if (pL >= 0.125) return 25
  return 0
}

/**
 * Tailwind fill klasa mastery skale (mastery barovi).
 * 🔴 Klase su LITERALI, nikad `bg-mastery-${step}` — Tailwind v4 skenira izvor
 * staticki, pa interpolirano ime klase nikad ne bi bilo generirano (bar bi
 * ostao neobojen, tiho).
 */
const MASTERY_FILL: Record<MasteryStep, string> = {
  0: "bg-mastery-0",
  25: "bg-mastery-25",
  50: "bg-mastery-50",
  75: "bg-mastery-75",
  100: "bg-mastery-100",
}

export function masteryFillClass(pL: number): string {
  return MASTERY_FILL[masteryStep(pL)]
}

/**
 * CSS varijabla mastery skale — za SVG atribute (`stroke`/`fill`) gdje Tailwind
 * klasa ne dopire. Vraća `var(--mastery-N)`: theme-reaktivno bez getComputedStyle
 * (varijablu razrješava preglednik pri promjeni teme, bez remounta grafa).
 */
export function masteryStrokeVar(pL: number): string {
  return `var(--mastery-${masteryStep(pL)})`
}
