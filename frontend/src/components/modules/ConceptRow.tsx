/**
 * ConceptRow (Faza 4.2b) — jedan koncept u detalju modula: 4 stanja (odluka B),
 * razlučena IKONOM + TEKSTOM + bojom (nikad samo bojom — a11y).
 * Progres isključivo kroz MasteryBar (invarijanta: nema drugog progres-renderera); p_l se prikazuje SAMO
 * ako je koncept diran (netaknut ≠ prior) — uključujući i zaključan-a-diran
 * (regresija preduvjeta ne smije sakriti zabilježeni napredak).
 */
import { Link } from "react-router-dom"
import {
  CheckCircle2,
  ChevronRight,
  CircleDashed,
  CircleDot,
  CircleSlash,
  Lock,
} from "lucide-react"
import { ConceptChip, TIER_LABEL } from "@/components/ConceptChip"
import { MasteryBar } from "@/components/MasteryBar"
import { masteryFillClass } from "@/lib/mastery"
import type { ConceptProgress, ConceptState } from "@/lib/progress"
import { cn } from "@/lib/utils"

const STATE_META: Record<
  ConceptState,
  { label: string; icon: typeof Lock; iconClass: string }
> = {
  not_started: {
    label: "Nije započeto",
    icon: CircleDashed,
    iconClass: "text-muted-foreground",
  },
  locked: {
    label: "Zaključano",
    icon: Lock,
    iconClass: "text-muted-foreground",
  },
  in_progress: {
    label: "U tijeku",
    icon: CircleDot,
    iconClass: "text-mastery-50",
  },
  mastered: {
    label: "Savladano",
    icon: CheckCircle2,
    iconClass: "text-correct",
  },
  // NALAZ #10b/#19: nema aktivnih zadataka → NIJE "zaključano" (ne otključava se).
  unavailable: {
    label: "Nema zadataka",
    icon: CircleSlash,
    iconClass: "text-muted-foreground",
  },
}

export function ConceptRow({ concept }: { concept: ConceptProgress }) {
  const { label, icon: Icon, iconClass } = STATE_META[concept.state]
  // "unavailable": NIŠTA što sugerira dostižnost — bez postotka, bez bara, bez
  // "Traži: …". Koncept nema zadataka, pa napredak nije ni definiran.
  const unavailable = concept.state === "unavailable"
  const pL = unavailable ? null : concept.pL
  // floor, ne round: 0.849 se NE smije prikazati kao prag-postotak dok je
  // stanje još "U tijeku" (prikaz mora biti konzistentan sa stanjem).
  const pct = pL !== null ? Math.floor(pL * 100) : null

  // Klik → otvara zadatak koncepta. Dopušteno SAMO kad koncept ima vlastitih
  // zadataka I nije zaključan — zaključani (nezadovoljeni preduvjeti) i oni bez
  // vlastitih zadataka (glue/izvan opsega) ostaju neklikabilni.
  const clickable = concept.hasOwnTasks && concept.state !== "locked"

  const body = (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <Icon className={cn("size-4 shrink-0", iconClass)} aria-hidden="true" />
        <span className="font-mono text-sm font-medium">{concept.name}</span>
        <ConceptChip
          name={TIER_LABEL[concept.tier] ?? concept.tier}
          tier={concept.tier}
        />
        <span className="ml-auto flex items-center gap-1 text-xs text-muted-foreground">
          {label}
          {pct !== null && <span className="tabular-nums"> · {pct} %</span>}
          {/* 🔴 ERRATA #42 — postotak je BKT procjena ZNANJA, ne napredak kroz
              zadatke, i to dvoje se razilazi u OBA smjera: 99 % uz dva
              neriješena zadatka, 77 % uz sve riješeno. Bez ovog brojača ekran
              odgovara na „koliko znam", a čita se kao „koliko mi je ostalo" —
              pa klik na koncept s visokim postotkom izgleda kao kvar kad vrati
              već riješen zadatak. `solved` iz /profile, `total` iz /modules. */}
          {concept.hasOwnTasks && (
            <span className="tabular-nums">
              {" "}
              · {concept.solvedTaskCount}/{concept.totalTaskCount} zadataka
            </span>
          )}
          {clickable && (
            // Afordancija klika (uz hover/cursor) — strelica „otvori".
            <ChevronRight aria-hidden="true" className="size-3.5 shrink-0" />
          )}
        </span>
      </div>

      {pL !== null && (
        <MasteryBar
          value={pL}
          fillClass={masteryFillClass(pL)}
          label={`Savladanost: ${concept.name} ${pct ?? 0} %`}
        />
      )}

      {concept.state === "locked" && concept.missingPrereqs.length > 0 && (
        <p className="pl-6 text-xs text-muted-foreground">
          Traži: {concept.missingPrereqs.join(", ")}
        </p>
      )}
    </>
  )

  return (
    <li
      // Anker za breadcrumb deep-link (`/modules#concept-<code>`). data-deeplinked
      // flash (2 s, postavlja ga ModulesPage) istakne redak prstenom + blagim tonom.
      id={`concept-${concept.code}`}
      className="scroll-mt-24 rounded-md transition-colors duration-base ease-standard data-[deeplinked=true]:bg-accent-warm/5 data-[deeplinked=true]:ring-2 data-[deeplinked=true]:ring-accent-warm/40 data-[deeplinked=true]:ring-inset motion-reduce:transition-none"
    >
      {clickable ? (
        <Link
          // Odredište je KONCEPT, ne zadatak — v. MasteryHighlights.
          to={`/koncept/${concept.code}`}
          aria-label={`Otvori zadatak za koncept ${concept.name}`}
          // -mx-2 px-2: hover pozadina diše u padding kartice, sadržaj se ne pomiče.
          className="-mx-2 block space-y-1.5 rounded-md px-2 py-3 transition-colors duration-fast ease-standard hover:bg-sidebar-accent/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring motion-reduce:transition-none"
        >
          {body}
        </Link>
      ) : (
        <div className="space-y-1.5 py-3">{body}</div>
      )}
    </li>
  )
}
