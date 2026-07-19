/**
 * BKT krivulje — grupiranje i kategorizacija (Faza 4.4b).
 *
 * Čisti izvod nad /mastery-history × /modules; nula dohvata, nula reacta.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * 🔴 OS X JE REDNI BROJ PRILIKE, NE VRIJEME
 * Krivulja se crta protiv indeksa prilike (1, 2, 3… po konceptu), ne protiv
 * timestampa. Dva razloga:
 *   1. Standard u BKT/learning-curve literaturi (Pelánek 2017; Yudelson 2013) —
 *      krivulja učenja je funkcija BROJA PRILIKA, ne proteklog vremena.
 *   2. Naši timestampovi su zgusnuti po sesijama: seed od 27 attempta stane
 *      unutar jedne minute, pa bi vremenska os dala nečitljivu nakupinu točaka
 *      uz prazan prostor.
 * Timestamp NIJE izgubljen — ide u tooltip.
 *
 * 🔴 REDOSLIJED SE NE DIRA
 * Backend vraća ORDER BY created_at ASC, id ASC. Točke istog attempta dijele
 * IDENTIČAN timestamp (BKT ažurira sve koncepte zadatka u jednom commitu —
 * provjereno živo: 3 koncepta na isti mikrosekundni created_at), pa bi
 * klijentski re-sort po created_at bio nestabilan i mogao bi permutirati lanac.
 * Oslanjamo se na dolazni redoslijed.
 *
 * 🔴 NALAZ #16 — P(L) SATURIRA I PLATO JE ISTINA, NE GREŠKA
 * Uz easy parametre (l0=.30, t=.30, g=.25, s=.08) P(L) brzo saturira blizu 1.0 i
 * nakon greške se jedva vraća: izmjereno na živim podacima 1.00000 → 0.99978
 * (4 uzastopne greške → 1.000 → 0.993), dakle regresija je praktički
 * nedetektabilna okom. To je POSLJEDICA IZBORA PARAMETARA, ne greška
 * implementacije — kanonska BKT formula (Corbett & Anderson 1994) ručno je
 * verificirana na živim podacima, poklapanje na 3 decimale.
 * UI to NE SKRIVA: Y-os je fiksna [0, 1] (vidi Y_DOMAIN), pa se plato vidi kao
 * plato. Auto-scale bi seriju 0.9998–1.0000 nacrtao kao dramatičan uspon — to bi
 * bila vizualna laž u diplomskom radu.
 */
import type { MasteryHistoryPoint, ModuleNode } from "@/lib/api/types"
import { buildConceptIndex, hasOwnTasks, type ConceptInfo } from "@/lib/mastery"

/**
 * Fiksna Y-domena za SVE grafove krivulja. P(L) je vjerojatnost — njezin raspon
 * je [0, 1] po definiciji, neovisno o tome što je u uzorku.
 * 🔴 NIKAD `domain={["auto", "auto"]}` (vidi NALAZ #16 gore).
 */
export const Y_DOMAIN: [number, number] = [0, 1]

/** Jedna točka krivulje — `opportunity` je 1-based redni broj prilike. */
export interface CurvePoint {
  opportunity: number
  p_l: number
  created_at: string
  attempt_id: number | null
}

/** Krivulja jednog koncepta + taksonomija za naslov/grupiranje. */
export interface ConceptCurve {
  code: string
  name: string
  /**
   * `tier` se NAMJERNO ne prenosi: krivulja ga ne prikazuje, a DB `concepts.tier`
   * divergira od Prolog tiera za 6/30 koncepata (errata #28) — prikaz uz BKT
   * krivulju sugerirao bi da je to težina koju model koristi, a nije.
   */
  moduleName: string
  moduleNumber: number
  points: CurvePoint[]
  /** Zadnja poznata vrijednost = trenutni P(L) (izvor boje krivulje). */
  currentPL: number
}

/**
 * Kategorizacija koncepta. Tri skupine, NE dvije — koncept bez točaka nije
 * automatski "još nema podataka".
 */
export type ConceptCategory =
  /** (A) Ima ili će imati točke → krivulja (ili "još nema podataka"). */
  | "trackable"
  /** (B) Izvan opsega evaluacije: M6 (`explain_plan`, `index_usage`) — NALAZ #19. */
  | "out_of_scope"
  /** (C) Strukturni/glue koncept modula 0 bez vlastitih zadataka (dizajn). */
  | "structural"

export interface CategorizedConcept extends ConceptInfo {
  category: ConceptCategory
}

/**
 * 🔴 DERIVACIJA IZ PODATAKA, NE IZ HARDKODIRANOG POPISA KODOVA.
 * Jedini ulaz je `primary_task_count` (+ broj modula) iz /modules — isti signal
 * kojim `deriveProgress` izvodi stanje `unavailable` (NALAZ #10b/#19). Popis
 * kodova bi zastario čim se task bank promijeni; ovako se skupine same presele.
 *
 * Provjereno živo (30 koncepata): `primary_task_count === 0` daje TOČNO 4
 * koncepta — `column_alias` i `join_condition` (modul 0 → strukturni) te
 * `explain_plan` i `index_usage` (M6 → izvan opsega). Preostalih 26 je (A).
 *
 * 🔴 (B) i (C) NIKAD ne idu u listu "još nema podataka": to bi bilo isto
 * obećanje otključavanja koje je maknuto iz module overviewa u 0e — obećanje
 * napretka za koncept koji ga po konstrukciji ne može ostvariti.
 */
export function categorizeConcept(concept: ConceptInfo): ConceptCategory {
  // Predikat „ima vlastite zadatke" dolazi iz lib/mastery.ts — isti izvor koji
  // koristi deriveProgress, da se klasifikacija istog koncepta ne raziđe
  // između Module overviewa i Profila.
  if (hasOwnTasks(concept)) return "trackable"
  return concept.moduleNumber === 0 ? "structural" : "out_of_scope"
}

export interface MasteryCurvesModel {
  /** (A) s bar jednom točkom, grupirano po modulu (redoslijed /modules). */
  byModule: {
    moduleName: string
    moduleNumber: number
    curves: ConceptCurve[]
  }[]
  /** (A) bez ijedne točke — legitimno "još nema podataka" (novi user). */
  awaitingData: CategorizedConcept[]
  /** (B) izvan opsega evaluacije. */
  outOfScope: CategorizedConcept[]
  /** (C) strukturni koncepti modula 0. */
  structural: CategorizedConcept[]
  /** Ukupan broj točaka — 0 znači "novi user", ne greška. */
  totalPoints: number
}

/**
 * Grupira povijest po konceptu i spaja s taksonomijom.
 *
 * Točke koncepta kojeg /modules ne poznaje SE PRESKAČU (ne izmišljamo ime ni
 * modul — isti dogovor kao enrichMastery). Modul se izvodi ISKLJUČIVO joinom
 * `concept` × /modules[].concepts[].code — 🔴 NIKAD preko `task.module_id`,
 * koji je kriv za 3/85 zadataka (NALAZ #7).
 */
export function buildMasteryCurves(
  history: MasteryHistoryPoint[],
  modules: ModuleNode[],
): MasteryCurvesModel {
  const index = buildConceptIndex(modules)

  // Grupiranje ČUVA dolazni redoslijed (Map čuva insertion order, push je
  // append) — nema re-sorta, vidi zaglavlje datoteke.
  const pointsByConcept = new Map<string, CurvePoint[]>()
  for (const point of history) {
    if (!index.has(point.concept)) continue
    const bucket = pointsByConcept.get(point.concept)
    const curvePoint: CurvePoint = {
      // Redni broj prilike = pozicija u lancu tog koncepta (1-based).
      opportunity: (bucket?.length ?? 0) + 1,
      p_l: point.p_l,
      created_at: point.created_at,
      attempt_id: point.attempt_id,
    }
    if (bucket) bucket.push(curvePoint)
    else pointsByConcept.set(point.concept, [curvePoint])
  }

  const byModule: MasteryCurvesModel["byModule"] = []
  const awaitingData: CategorizedConcept[] = []
  const outOfScope: CategorizedConcept[] = []
  const structural: CategorizedConcept[] = []

  for (const module of modules) {
    const curves: ConceptCurve[] = []
    for (const concept of module.concepts) {
      const info = index.get(concept.code)
      if (!info) continue
      const category = categorizeConcept(info)
      const categorized: CategorizedConcept = { ...info, category }
      const points = pointsByConcept.get(concept.code)

      // 🔴 IZMJERENI PODATAK NADJAČAVA KATEGORIJU.
      // Kategorija je predviđanje ("ovaj koncept neće imati krivulju"), točke su
      // činjenica. Koncept s 0 PRIMARNIH zadataka svejedno skuplja BKT povijest
      // ako se pojavljuje kao SEKUNDARNI: `column_alias` ima 0 primarnih i 4
      // aktivna sekundarna, pa student rješavanjem `inner_join_d2_b39dec5d`
      // dobije stvarnu točku (živo provjereno: p_l=0.7284). Ako bi se kategorija
      // provjeravala PRIJE točaka, ta bi se točka tiho odbacila, a UI bi uz
      // koncept tvrdio „nema zasebnu krivulju" — neistina o vlastitim podacima.
      // Zato: ima točaka → krivulja, bez obzira na skupinu.
      if (!points || points.length === 0) {
        if (category === "out_of_scope") {
          outOfScope.push(categorized)
          continue
        }
        if (category === "structural") {
          structural.push(categorized)
          continue
        }
        awaitingData.push(categorized)
        continue
      }
      curves.push({
        code: info.code,
        name: info.name,
        moduleName: info.moduleName,
        moduleNumber: info.moduleNumber,
        points,
        currentPL: points[points.length - 1].p_l,
      })
    }
    if (curves.length > 0) {
      byModule.push({
        moduleName: module.name,
        moduleNumber: module.number,
        curves,
      })
    }
  }

  let totalPoints = 0
  for (const points of pointsByConcept.values()) totalPoints += points.length

  return { byModule, awaitingData, outOfScope, structural, totalPoints }
}

/**
 * Formatira timestamp točke (tooltip + a11y tablica).
 *
 * 🔴 ISTE opcije kao `DT_FMT` u AttemptRow (4.4a): krivulje i povijest pokušaja
 * stoje JEDNA ISPOD DRUGE na Profilu i prikazuju iste timestampove — dva
 * formata na istom ekranu čitaju se kao dva različita podatka.
 * Formatter je na razini modula (konstrukcija `Intl.DateTimeFormat` je skupa, a
 * tablica ga zove po retku — serija od 21 točke inače znači 21 konstrukciju po
 * renderu).
 * Specifikacija formata je namjerno duplicirana umjesto dijeljena, jer je
 * AttemptRow 4.4a komponenta izvan opsega ove pod-faze; objedinjavanje u
 * `lib/datetime.ts` je kandidat za 4.7.
 */
const POINT_DT_FMT = new Intl.DateTimeFormat("hr-HR", {
  dateStyle: "medium",
  timeStyle: "short",
})

export function formatPointTimestamp(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return "—"
  return POINT_DT_FMT.format(date)
}

/** P(L) na 3 decimale — dovoljna razlučivost da se plato VIDI kao plato. */
export function formatPL(pL: number): string {
  return pL.toFixed(3)
}

/**
 * Hrvatski plural za "prilika", nominativ (1 prilika · 2–4 prilike · 5+ prilika).
 * Isti obrazac kao rowNoun u RunResultPanelu (4.3b).
 */
export function opportunityNoun(n: number): string {
  const d = n % 10
  const dd = n % 100
  if (d === 1 && dd !== 11) return "prilika"
  if (d >= 2 && d <= 4 && (dd < 12 || dd > 14)) return "prilike"
  return "prilika"
}
