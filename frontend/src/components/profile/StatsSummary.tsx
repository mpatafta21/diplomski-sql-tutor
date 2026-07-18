/**
 * StatsSummary (Faza 4.4a) — sažetak nad PROZOROM zadnjih ≤100 pokušaja.
 *
 * Vlastiti query (useAttempts, limit=100) — jedan ograničen zahtjev.
 * 🔴 LABELIRANJE OBAVEZNO: "zadnjih N pokušaja", nikad gol "Accuracy" (API nema
 *    agregat; prozor je jedini iskren način).
 * 🔴 `total` (ukupno pokušaja) je iz Page.total — jedini pravi ukupni broj.
 * 🔴 NE sumira `xp_awarded` i NE prikazuje XP (badge XP ide kroz xp_log s
 *    attempt_id=NULL → Σ delti < /profile.xp; autoritativni XP je SAMO /profile,
 *    prikazuje ga ProgressHero). Dvije XP brojke na ekranu = bug.
 * 🔴 NEMA metrike "vrijeme" — execution_time_ms je trajanje SQL-a, ne učenja.
 */
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LoadingState } from "@/components/state/LoadingState"
import { useAttempts } from "@/hooks/useAttempts"
import { summarizeAttempts } from "@/lib/attempt-stats"

const WINDOW = 100

function pct(value: number): string {
  return `${Math.round(value * 100)} %`
}

export function StatsSummary() {
  const query = useAttempts({ limit: WINDOW, offset: 0 })

  if (query.isPending) {
    return (
      <Card aria-busy="true">
        <CardContent>
          <LoadingState lines={2} label="Učitavanje statistike" />
        </CardContent>
      </Card>
    )
  }

  // Greška ili prazan skup → ništa (povijest ispod nosi error/CTA, bez duplog šuma).
  if (query.isError || query.data.total === 0) {
    return null
  }

  const { total, items } = query.data
  const stats = summarizeAttempts(items)
  const windowLabel = `zadnjih ${stats.windowSize} ${
    stats.windowSize === total ? "pokušaja" : `od ${total} pokušaja`
  }`

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Statistika</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-0.5">
          <p className="text-3xl font-semibold tracking-tight tabular-nums">
            {total}
          </p>
          <p className="text-sm text-muted-foreground">Ukupno pokušaja</p>
        </div>
        <div className="space-y-0.5">
          <p className="text-3xl font-semibold tracking-tight text-correct tabular-nums">
            {pct(stats.accuracy)}
          </p>
          <p className="text-sm text-muted-foreground">
            Točnost <span className="text-xs">({windowLabel})</span>
          </p>
        </div>
        <div className="space-y-0.5">
          <p className="text-3xl font-semibold tracking-tight text-partial tabular-nums">
            {pct(stats.partialShare)}
          </p>
          <p className="text-sm text-muted-foreground">
            Djelomično <span className="text-xs">({windowLabel})</span>
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
