/**
 * ConceptCurveCard (Faza 4.4b) — JEDNA mini-krivulja u mreži (small multiples).
 *
 * 🔴 A11Y: krivulja NIJE jedini nosilac informacije. SVG je `aria-hidden`, a uz
 * njega OBAVEZNO stoji tekstualni trenutni P(L) + status prema pragu
 * ovladanosti. Čitač ekrana i korisnik koji ne razlikuje boje dobiju istu
 * informaciju kao i onaj koji vidi krivulju (isti kanal-dupliciranje kao
 * verdict ikona+tekst iz 4.3c, NALAZ #13).
 *
 * 🔴 BOJA = MAGNITUDA, ne kategorija: stroke dolazi iz mastery gradijenta prema
 * TRENUTNOM p_l (MASTER.md §2.3/§2.6 — sekvencijalna skala). Kategorijska
 * paleta (--chart-1..5) je rezervirana za usporedbu VIŠE serija, gdje boja
 * razlikuje seriju, a ne veličinu.
 */
import {
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  YAxis,
} from "recharts"
import { Check } from "lucide-react"
import type { ConceptCurve } from "@/lib/mastery-history"
import { formatPL, opportunityNoun, Y_DOMAIN } from "@/lib/mastery-history"
import { masteryStrokeVar } from "@/lib/mastery"
import { cn } from "@/lib/utils"

interface ConceptCurveCardProps {
  curve: ConceptCurve
  masteryThreshold: number
  selected: boolean
  onSelect: (code: string) => void
  /** id panela s detaljem — veže karticu i sadržaj koji otvara (aria-controls). */
  detailId: string
}

export function ConceptCurveCard({
  curve,
  masteryThreshold,
  selected,
  onSelect,
  detailId,
}: ConceptCurveCardProps) {
  const mastered = curve.currentPL >= masteryThreshold
  const stroke = masteryStrokeVar(curve.currentPL)
  const single = curve.points.length === 1

  return (
    <button
      type="button"
      onClick={() => onSelect(curve.code)}
      // Kartica OTKRIVA panel s detaljem → disclosure semantika
      // (aria-expanded + aria-controls), ne toggle-gumb (aria-pressed):
      // čitač ekrana tako najavi da se sadržaj otvara i kamo vodi.
      aria-expanded={selected}
      aria-controls={selected ? detailId : undefined}
      className={cn(
        // min-h-11 => 44px touch target (WCAG 2.5.5).
        "flex min-h-11 w-full flex-col gap-2 rounded-lg border p-3 text-left transition-colors duration-fast ease-standard",
        "hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        selected ? "border-ring bg-muted/40" : "border-border",
      )}
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="truncate text-sm font-medium">{curve.name}</span>
        {mastered && (
          <Check
            className="size-3.5 shrink-0 text-correct"
            aria-hidden="true"
          />
        )}
      </div>

      {/* Grafika je dekoracija NAD tekstom ispod — nikad jedini nosilac. */}
      <div className="h-16 w-full" aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={curve.points}
            margin={{ top: 4, right: 4, bottom: 4, left: 4 }}
            // 🔴 Recharts v3 po defaultu stavlja tabindex="0" + role="application"
            // na SVAKI chart surface. Uz aria-hidden wrapper to stvara „crnu rupu
            // fokusa": tipkovnica stane na element o kojem čitač ekrana ne kaže
            // ništa (izmjereno: 15 takvih stopova na Profilu). Mini-graf je čista
            // dekoracija — sve što crta stoji kao tekst ispod — pa mu se
            // accessibility sloj gasi, a detaljni graf ga zadržava.
            accessibilityLayer={false}
            tabIndex={-1}
          >
            {/* 🔴 FIKSNA domena [0,1] — vidi Y_DOMAIN / NALAZ #16. */}
            <YAxis domain={Y_DOMAIN} hide allowDataOverflow={false} />
            <ReferenceLine
              y={masteryThreshold}
              stroke="var(--color-muted-foreground)"
              strokeDasharray="3 3"
              strokeOpacity={0.6}
            />
            <Line
              type="monotone"
              dataKey="p_l"
              stroke={stroke}
              strokeWidth={2}
              dot={single ? { r: 3, fill: stroke } : false}
              // 🔴 Recharts animira JS-om (react-smooth) i NE poštuje
              // prefers-reduced-motion → gasimo na SVAKOJ seriji.
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-baseline justify-between gap-2 text-xs">
        <span className="tabular-nums font-medium">
          P(L) {formatPL(curve.currentPL)}
        </span>
        <span className="text-muted-foreground">
          {mastered ? "savladano" : "u tijeku"}
          {" · "}
          <span className="tabular-nums">{curve.points.length}</span>{" "}
          {opportunityNoun(curve.points.length)}
        </span>
      </div>
    </button>
  )
}
