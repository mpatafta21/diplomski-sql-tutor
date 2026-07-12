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
    })
  }
  out.sort((a, b) => a.p_l - b.p_l)
  return out
}

/**
 * P(L) → token klasa mastery skale (MASTER.md §2.3, 5 stopova).
 * Bucket granice su VIZUALNA kvantizacija kontinuirane skale (design-system
 * odluka), ne backend semantika — backend prag savladanosti je
 * mastery_threshold iz /profile.
 */
export function masteryFillClass(pL: number): string {
  if (pL >= 0.875) return "bg-mastery-100"
  if (pL >= 0.625) return "bg-mastery-75"
  if (pL >= 0.375) return "bg-mastery-50"
  if (pL >= 0.125) return "bg-mastery-25"
  return "bg-mastery-0"
}
