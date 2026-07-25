/**
 * ConceptRow (Faza 4.2b) — jedan koncept u detalju modula: 4 stanja (odluka B),
 * razlučena IKONOM + TEKSTOM + bojom (nikad samo bojom — a11y).
 * Progres isključivo kroz MasteryBar (invarijanta #1); p_l se prikazuje SAMO
 * ako je koncept diran (netaknut ≠ prior) — uključujući i zaključan-a-diran
 * (regresija preduvjeta ne smije sakriti zabilježeni napredak).
 */
import {
  CheckCircle2,
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

  return (
    <li
      // Anker za breadcrumb deep-link (`/modules#concept-<code>`). data-deeplinked
      // flash (2 s, postavlja ga ModulesPage) istakne redak prstenom + blagim tonom.
      id={`concept-${concept.code}`}
      className="scroll-mt-24 space-y-1.5 rounded-md py-3 transition-colors duration-base ease-standard data-[deeplinked=true]:bg-accent-warm/5 data-[deeplinked=true]:ring-2 data-[deeplinked=true]:ring-accent-warm/40 data-[deeplinked=true]:ring-inset motion-reduce:transition-none"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Icon className={cn("size-4 shrink-0", iconClass)} aria-hidden="true" />
        <span className="text-sm font-medium">{concept.name}</span>
        <ConceptChip
          name={TIER_LABEL[concept.tier] ?? concept.tier}
          tier={concept.tier}
        />
        <span className="ml-auto text-xs text-muted-foreground">
          {label}
          {pct !== null && <span className="tabular-nums"> · {pct} %</span>}
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
    </li>
  )
}
