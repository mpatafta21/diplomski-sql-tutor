/**
 * Izvod stanja koncepata i modula za Module overview (Faza 4.2b).
 *
 * 4 stanja koncepta (odluka B): nije-započeto · zaključan · u-tijeku · savladan.
 * Prag "savladano" DOLAZI iz /profile.mastery_threshold (invarijanta #2 — nikad
 * lokalna konstanta). Netaknuti koncepti NEMAJU p_l (prior se NE prikazuje).
 *
 * UNLOCK (odluka A + dokumentirano odstupanje): prereq je zadovoljen ako je
 * savladan sirovim p_l ILI ako je TRANSVERZALNI (modul 0) čvor čiji su SVI
 * TRANZITIVNI ne-modul-0 preci savladani. Razlog: Recommender
 * (recommender_logic.py, build_mastery_snapshot korak 4) tretira modul-0
 * čvorove bez taskova kao "prozirne" (0.99 čim su im all_prereqs — tranzitivni
 * zatvarač! — savladani); bez zrcaljenja UI bi trajno pokazivao "zaključano"
 * za koncepte (inner_join, group_by, cross_join) koje Recommender legitimno
 * preporučuje.
 *
 * POZNATI REZIDUALI (backend signal "ima aktivnih taskova" NIJE u API-ju,
 * ispravna dubina popravka je budući contract dodatak — vidi izvještaj 4.2b):
 *  1. null_handling: modul 0 S taskovima — Recommender ga tretira NORMALNO,
 *     UI prozirno → UI može prikazati agg_count/left_join/in_subquery kao
 *     otključane prije nego Recommender to smatra (samo informativni smjer;
 *     CTA na Dashboardu i dalje slijedi Recommendera).
 *  2. subfloor (right_join → full_outer_join): Recommender maskira right_join
 *     kao savladan, UI ne zna za masku → full_outer_join u UI-ju ostaje
 *     "zaključano" dulje nego u Recommenderu.
 */
import type { MasteryItem, ModuleNode } from "@/lib/api/types"
import { buildConceptIndex, hasOwnTasks, type ConceptInfo } from "@/lib/mastery"

export type ConceptState =
  | "not_started"
  | "locked"
  | "in_progress"
  | "mastered"
  /**
   * 🔴 NALAZ #10b / #19 — koncept BEZ ijednog aktivnog primary taska
   * (`hasOwnTasks === false`) izvan modula 0. Polje `primary_task_count` je
   * izloženo u 4.3 Stage 0 (NALAZ #10) i do 4.4-0e stajalo NEISKORIŠTENO, zbog
   * čega je M6 izgledao kao otključiv modul iako nijedan njegov zadatak nije
   * evaluabilan. NE brisati kao "mrtvo polje".
   *
   * Od 4.4b polje ima DVA potrošača — ovaj i `categorizeConcept`
   * (lib/mastery-history.ts, skupine (B)/(C) na Profilu). Zajednički predikat
   * je `hasOwnTasks` u lib/mastery.ts; prag se mijenja SAMO ondje.
   */
  | "unavailable"

export interface ConceptProgress {
  code: string
  name: string
  tier: string
  state: ConceptState
  /** Sirovi P(L) iz /profile.mastery; null = netaknut (prior se NE izmišlja). */
  pL: number | null
  /** Imena nezadovoljenih preduvjeta (samo za state === "locked"). */
  missingPrereqs: string[]
  /**
   * Meta za klik na koncept → `/task/<id>` (self-test fix 4.6-eval). Reprezentativan
   * aktivan primary zadatak (najlakši prvi, iz `/modules`). null ⟺ koncept nema
   * vlastitih zadataka (glue/izvan opsega). UI čini redak klikabilnim samo kad je
   * ne-null I koncept NIJE "locked".
   */
  entryTaskId: number | null
}

export interface ModuleProgress {
  module: ModuleNode
  concepts: ConceptProgress[]
  masteredCount: number
  totalCount: number
  /** Koncepti koji IMAJU aktivne zadatke. 0 → modul je izvan opsega (M6). */
  availableCount: number
}

export interface ProgressOverview {
  /** Moduli 1–6, sortirani po order_index. */
  main: ModuleProgress[]
  /** Transverzalni modul (number === 0), null ako ne postoji u odgovoru. */
  transversal: ModuleProgress | null
  /** Prereq codovi koji ne postoje ni u jednom modulu (integritet — STANI-I-JAVI). */
  danglingPrereqs: string[]
}

export function deriveProgress(
  modules: ModuleNode[],
  mastery: MasteryItem[],
  masteryThreshold: number,
): ProgressOverview {
  const pLByCode = new Map(mastery.map((m) => [m.concept, m.p_l]))
  // Isti index kao Dashboard join (lib/mastery.ts) — jedan izvor taksonomije.
  const index: Map<string, ConceptInfo> = buildConceptIndex(modules)

  const dangling = new Set<string>()

  const isMastered = (code: string): boolean => {
    const pL = pLByCode.get(code)
    return pL !== undefined && pL >= masteryThreshold
  }

  // Prozirnost modul-0 čvora zrcali Recommenderov engine.all_prereqs: prolazi
  // se TRANZITIVNI zatvarač predaka i SVAKI ne-modul-0 predak mora biti sirovo
  // savladan (modul-0 preci ništa ne traže sami — njihovi su preci već u
  // zatvaraču). `seen` ujedno štiti od ciklusa na pokvarenim podacima.
  const transparentMemo = new Map<string, boolean>()
  const transparent = (code: string): boolean => {
    const cached = transparentMemo.get(code)
    if (cached !== undefined) return cached

    let ok = true
    const seen = new Set<string>([code])
    const stack = [...(index.get(code)?.prerequisites ?? [])]
    while (stack.length > 0) {
      const p = stack.pop() as string
      if (seen.has(p)) continue
      seen.add(p)
      const info = index.get(p)
      if (info === undefined) {
        dangling.add(p)
        ok = false
        continue
      }
      if (info.moduleNumber !== 0 && !isMastered(p)) ok = false
      stack.push(...info.prerequisites)
    }
    transparentMemo.set(code, ok)
    return ok
  }

  // "Zadovoljen" prereq: savladan sirovo ILI prozirni modul-0 čvor.
  const satisfied = (code: string): boolean => {
    const info = index.get(code)
    if (info === undefined) {
      dangling.add(code)
      return false
    }
    if (isMastered(code)) return true
    return info.moduleNumber === 0 && transparent(code)
  }

  const toProgress = (mod: ModuleNode): ModuleProgress => {
    const concepts = mod.concepts.map((c): ConceptProgress => {
      const pL = pLByCode.get(c.code) ?? null

      // Savladan koncept preskače prereq walk (missing je irelevantan) —
      // jedan predikat (isMastered) za stanje I za satisfied, da se ne raziđu.
      if (isMastered(c.code)) {
        return {
          code: c.code,
          name: c.name,
          tier: c.tier,
          state: "mastered",
          pL,
          missingPrereqs: [],
          entryTaskId: c.entry_task_id ?? null,
        }
      }

      // Nema aktivnih zadataka → koncept se NE može vježbati; ne smije izgledati
      // kao da ga se otključava (bez prereq teksta, bara i postotka — ConceptRow).
      // Modul 0 je iznimka: transverzalni po dizajnu nemaju vlastite zadatke i
      // već imaju vlastito objašnjenje u UI-ju (4.2b), pa ostaju nepromijenjeni.
      if (mod.number !== 0 && !hasOwnTasks(c)) {
        return {
          code: c.code,
          name: c.name,
          tier: c.tier,
          state: "unavailable",
          pL,
          missingPrereqs: [],
          entryTaskId: c.entry_task_id ?? null,
        }
      }

      const missing = c.prerequisites.filter((p) => !satisfied(p))
      const state: ConceptState =
        missing.length > 0
          ? "locked"
          : pL !== null
            ? "in_progress"
            : "not_started"

      return {
        code: c.code,
        name: c.name,
        tier: c.tier,
        state,
        pL,
        missingPrereqs: missing.map((p) => index.get(p)?.name ?? p),
        entryTaskId: c.entry_task_id ?? null,
      }
    })

    return {
      module: mod,
      concepts,
      masteredCount: concepts.filter((c) => c.state === "mastered").length,
      totalCount: concepts.length,
      availableCount: concepts.filter((c) => c.state !== "unavailable").length,
    }
  }

  const sorted = [...modules].sort((a, b) => a.order_index - b.order_index)
  const main = sorted.filter((m) => m.number !== 0).map(toProgress)
  const transversalNode = sorted.find((m) => m.number === 0)
  const transversal = transversalNode ? toProgress(transversalNode) : null

  return { main, transversal, danglingPrereqs: [...dangling].sort() }
}
