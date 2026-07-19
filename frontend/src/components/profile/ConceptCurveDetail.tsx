/**
 * ConceptCurveDetail (Faza 4.4b) — uvećana krivulja JEDNOG koncepta.
 *
 * Ovdje boja NIJE magnituda nego identitet serije → `--chart-1` (kategorijska
 * paleta, MASTER.md §2.6). Mini-krivulje u mreži koriste mastery gradijent jer
 * ondje boja kodira VELIČINU; ovdje je serija jedna pa je magnituda već na osi.
 *
 * 🔴 Os X = redni broj prilike (1, 2, 3…), NE vrijeme. Timestamp je u tooltipu.
 * 🔴 Os Y = fiksno [0, 1] (Y_DOMAIN). Nikad auto-scale — vidi NALAZ #16.
 */
import {
  CartesianGrid,
  Label,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { ConceptCurve, CurvePoint } from "@/lib/mastery-history"
import {
  formatPL,
  formatPointTimestamp,
  opportunityNoun,
  Y_DOMAIN,
} from "@/lib/mastery-history"

interface ConceptCurveDetailProps {
  curve: ConceptCurve
  masteryThreshold: number
}

interface TooltipPayloadEntry {
  payload: CurvePoint
}

function CurveTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: TooltipPayloadEntry[]
}) {
  if (!active || !payload || payload.length === 0) return null
  const point = payload[0].payload

  return (
    <div className="rounded-lg border border-border bg-popover p-3 text-xs shadow-md">
      <div className="font-medium tabular-nums">P(L) {formatPL(point.p_l)}</div>
      <dl className="mt-1.5 space-y-0.5 text-muted-foreground">
        <div className="flex gap-2">
          <dt>Prilika</dt>
          <dd className="tabular-nums text-foreground">{point.opportunity}.</dd>
        </div>
        <div className="flex gap-2">
          <dt>Vrijeme</dt>
          <dd className="tabular-nums text-foreground">
            {formatPointTimestamp(point.created_at)}
          </dd>
        </div>
        {point.attempt_id !== null && (
          <div className="flex gap-2">
            <dt>Pokušaj</dt>
            <dd className="tabular-nums text-foreground">
              #{point.attempt_id}
            </dd>
          </div>
        )}
      </dl>
    </div>
  )
}

export function ConceptCurveDetail({
  curve,
  masteryThreshold,
}: ConceptCurveDetailProps) {
  const single = curve.points.length === 1
  const mastered = curve.currentPL >= masteryThreshold

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{curve.name}</CardTitle>
        <CardDescription>
          {curve.moduleName} · trenutni P(L){" "}
          <span className="tabular-nums text-foreground">
            {formatPL(curve.currentPL)}
          </span>{" "}
          ({mastered ? "savladano" : "u tijeku"}) ·{" "}
          <span className="tabular-nums">{curve.points.length}</span>{" "}
          {opportunityNoun(curve.points.length)}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={curve.points}
              margin={{ top: 8, right: 16, bottom: 24, left: 8 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--color-border)"
              />
              <XAxis
                dataKey="opportunity"
                type="number"
                domain={[1, "dataMax"]}
                allowDecimals={false}
                tick={{ fontSize: 12, fill: "var(--color-muted-foreground)" }}
                stroke="var(--color-border)"
              >
                <Label
                  value="Redni broj prilike"
                  position="insideBottom"
                  offset={-12}
                  style={{
                    fontSize: 12,
                    fill: "var(--color-muted-foreground)",
                  }}
                />
              </XAxis>
              {/* 🔴 FIKSNA domena — auto-scale bi plato 0.9998–1.0 nacrtao kao
                  dramatičan uspon (NALAZ #16). Tickovi su fiksni iz istog razloga. */}
              <YAxis
                domain={Y_DOMAIN}
                ticks={[0, 0.25, 0.5, 0.75, 1]}
                tickFormatter={(v: number) => v.toFixed(2)}
                tick={{ fontSize: 12, fill: "var(--color-muted-foreground)" }}
                stroke="var(--color-border)"
                width={44}
              />
              <ReferenceLine
                y={masteryThreshold}
                stroke="var(--color-accent-warm)"
                strokeDasharray="4 4"
              >
                <Label
                  value={`prag ovladanosti (${formatPL(masteryThreshold)})`}
                  position="insideTopRight"
                  style={{
                    fontSize: 11,
                    fill: "var(--color-accent-warm-text)",
                  }}
                />
              </ReferenceLine>
              <Tooltip
                content={<CurveTooltip />}
                cursor={{ stroke: "var(--color-border)" }}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="p_l"
                stroke="var(--chart-1)"
                strokeWidth={2}
                dot={single ? { r: 4, fill: "var(--chart-1)" } : { r: 2 }}
                activeDot={{ r: 5 }}
                // 🔴 react-smooth ne poštuje prefers-reduced-motion.
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {single && (
          <p className="text-xs text-muted-foreground">
            Samo jedna prilika — točka, ne trend. Krivulja se oblikuje nakon
            više pokušaja nad ovim konceptom.
          </p>
        )}

        {/* 🔴 Tablica NIJE dekoracija nego A11Y KANAL: sve što krivulja crta
            postoji i kao tekst (NALAZ #13 obrazac). Deep-link po pokušaju nije
            moguć — /attempts nema server-side filtere (NALAZ #15) i filter se
            NE dodaje zbog ovoga; link vodi na povijest kao cjelinu. */}
        <details className="rounded-lg border border-border">
          <summary className="cursor-pointer px-3 py-2 text-xs font-medium hover:bg-muted/50">
            Točke krivulje kao tablica
          </summary>
          <div className="max-h-64 overflow-auto border-t border-border">
            <table className="w-full text-xs">
              <caption className="sr-only">
                Vrijednosti P(L) za koncept {curve.name} po prilici
              </caption>
              <thead className="sticky top-0 bg-card">
                <tr className="text-left text-muted-foreground">
                  <th scope="col" className="px-3 py-1.5 font-medium">
                    Prilika
                  </th>
                  <th scope="col" className="px-3 py-1.5 font-medium">
                    P(L)
                  </th>
                  <th scope="col" className="px-3 py-1.5 font-medium">
                    Vrijeme
                  </th>
                  <th scope="col" className="px-3 py-1.5 font-medium">
                    Pokušaj
                  </th>
                </tr>
              </thead>
              <tbody>
                {curve.points.map((point) => (
                  <tr
                    key={`${point.opportunity}-${point.created_at}`}
                    className="border-t border-border"
                  >
                    <td className="px-3 py-1.5 tabular-nums">
                      {point.opportunity}.
                    </td>
                    <td className="px-3 py-1.5 tabular-nums">
                      {formatPL(point.p_l)}
                    </td>
                    <td className="px-3 py-1.5 tabular-nums text-muted-foreground">
                      {formatPointTimestamp(point.created_at)}
                    </td>
                    <td className="px-3 py-1.5 tabular-nums">
                      {point.attempt_id === null ? (
                        <span className="text-muted-foreground">—</span>
                      ) : (
                        // Povijest je na OVOJ stranici → nativni anchor
                        // (preglednik sam skrola). Router <Link> s hashom ne
                        // skrola pouzdano bez ScrollRestoration handlera.
                        <a
                          href="#povijest"
                          className="underline underline-offset-2 hover:text-foreground"
                        >
                          #{point.attempt_id}
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </CardContent>
    </Card>
  )
}
