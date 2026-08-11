/**
 * MasteryHighlights (Faza 4.2) — najslabiji/najjači DIRANI koncepti.
 * Ime koncepta dolazi iz joina s /modules (mastery nosi samo code!).
 * Prag "savladano" = profile.mastery_threshold (backend istina, invarijanta: prag iz /profile).
 * Netaknuti koncepti se NE prikazuju (to je teren 4.2b Module overviewa).
 */
import { Link } from "react-router-dom"
import { CheckCircle2, ChevronRight } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { MasteryBar } from "@/components/MasteryBar"
import type { EnrichedMastery } from "@/lib/mastery"
import { masteryFillClass } from "@/lib/mastery"

const HIGHLIGHT_COUNT = 3

interface MasteryHighlightsProps {
  /** Obogaćen i UZLAZNO sortiran mastery (enrichMastery). */
  mastery: EnrichedMastery[]
  masteryThreshold: number
}

function MasteryRow({
  item,
  masteryThreshold,
  clickable,
}: {
  item: EnrichedMastery
  masteryThreshold: number
  /** Redak vodi na zadatak koncepta (samo ako koncept ima vlastiti zadatak). */
  clickable: boolean
}) {
  const pct = Math.round(item.p_l * 100)
  const mastered = item.p_l >= masteryThreshold
  const isLink = clickable && item.entryTaskId !== null

  const body = (
    <>
      <div className="flex items-baseline justify-between gap-2">
        <span className="flex items-center gap-1.5 font-mono text-sm font-medium">
          {item.name}
          {mastered && (
            <CheckCircle2
              role="img"
              className="size-3.5 text-correct"
              aria-label="Savladano"
            />
          )}
          {isLink && (
            <ChevronRight
              aria-hidden="true"
              className="size-3.5 shrink-0 text-muted-foreground"
            />
          )}
        </span>
        <span className="text-xs text-muted-foreground tabular-nums">
          {pct} %
        </span>
      </div>
      <MasteryBar
        value={item.p_l}
        fillClass={masteryFillClass(item.p_l)}
        label={`Savladanost: ${item.name} ${pct} %`}
      />
      <p className="text-xs text-muted-foreground">{item.moduleName}</p>
    </>
  )

  return (
    <li>
      {isLink ? (
        <Link
          to={`/task/${item.entryTaskId}`}
          aria-label={`Otvori zadatak za koncept ${item.name}`}
          // -mx-2 px-2: hover diše u padding kartice, sadržaj se ne pomiče.
          className="-mx-2 block space-y-1.5 rounded-md px-2 py-1.5 transition-colors duration-fast ease-standard hover:bg-sidebar-accent/40 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring motion-reduce:transition-none"
        >
          {body}
        </Link>
      ) : (
        <div className="space-y-1.5">{body}</div>
      )}
    </li>
  )
}

function HighlightCard({
  title,
  description,
  items,
  masteryThreshold,
  clickable = false,
}: {
  title: string
  description: string
  items: EnrichedMastery[]
  masteryThreshold: number
  /** Retci vode na zadatak koncepta (za „Za ojačati" karticu). */
  clickable?: boolean
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-4">
          {items.map((item) => (
            <MasteryRow
              key={item.code}
              item={item}
              masteryThreshold={masteryThreshold}
              clickable={clickable}
            />
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

export function MasteryHighlights({
  mastery,
  masteryThreshold,
}: MasteryHighlightsProps) {
  // Podjela po BACKEND pragu (mastery_threshold iz /profile), NE po poziciji:
  // "za ojačati" smije sadržavati SAMO nesavladane koncepte.
  const weakest = mastery
    .filter((m) => m.p_l < masteryThreshold)
    .slice(0, HIGHLIGHT_COUNT)
  const strongest = mastery
    .filter((m) => m.p_l >= masteryThreshold)
    .slice(-HIGHLIGHT_COUNT)
    .reverse()

  // Usamljena kartica zauzima jednu grid ćeliju — wrapper je bezuvjetan.
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {weakest.length > 0 && (
        <HighlightCard
          title="Za ojačati"
          description="Koncepti s najnižom procjenom znanja — klikni za zadatak."
          items={weakest}
          masteryThreshold={masteryThreshold}
          clickable
        />
      )}
      {strongest.length > 0 && (
        <HighlightCard
          title="Savladani koncepti"
          description="Ovdje ti model znanja daje najviše povjerenja."
          items={strongest}
          masteryThreshold={masteryThreshold}
        />
      )}
    </div>
  )
}
