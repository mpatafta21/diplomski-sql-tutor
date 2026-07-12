/**
 * MasteryHighlights (Faza 4.2) — najslabiji/najjači DIRANI koncepti.
 * Ime koncepta dolazi iz joina s /modules (mastery nosi samo code!).
 * Prag "savladano" = profile.mastery_threshold (backend istina, invarijanta #6).
 * Netaknuti koncepti se NE prikazuju (to je teren 4.2b Module overviewa).
 */
import { CheckCircle2 } from "lucide-react"
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
}: {
  item: EnrichedMastery
  masteryThreshold: number
}) {
  const pct = Math.round(item.p_l * 100)
  const mastered = item.p_l >= masteryThreshold

  return (
    <li className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="flex items-center gap-1.5 text-sm font-medium">
          {item.name}
          {mastered && (
            <CheckCircle2
              role="img"
              className="size-3.5 text-correct"
              aria-label="Savladano"
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
    </li>
  )
}

function HighlightCard({
  title,
  description,
  items,
  masteryThreshold,
}: {
  title: string
  description: string
  items: EnrichedMastery[]
  masteryThreshold: number
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
          description="Koncepti s najnižom procjenom znanja — dobar sljedeći fokus."
          items={weakest}
          masteryThreshold={masteryThreshold}
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
