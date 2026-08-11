/**
 * MasteryCurves (Faza 4.4b) — sekcija BKT krivulja na Profilu.
 *
 * LAYOUT: small multiples (mreža mini-krivulja, 1 koncept = 1 graf), grupirano
 * po modulu — NE špagete-graf sa svim serijama u jednom okviru. S 13+ aktivnih
 * koncepata jedan zajednički graf postaje nečitljiv, a ovdje je pitanje „kako
 * napreduje SVAKI koncept", ne „koji je iznad kojeg".
 *
 * Klik na mini-krivulju → uvećani detalj (ConceptCurveDetail) s tooltipom.
 *
 * IZVORI: /mastery-history (točke) × /modules (taksonomija + primary_task_count)
 * × /profile (mastery_threshold — 🔴 NIKAD hardkodiran 0.85; invarijanta: prag iz /profile).
 */
import { useId, useMemo, useState } from "react"
import { TrendingUp } from "lucide-react"
import { Link } from "react-router-dom"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/state/EmptyState"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import { ConceptCurveCard } from "@/components/profile/ConceptCurveCard"
import { ConceptCurveDetail } from "@/components/profile/ConceptCurveDetail"
import { UntrackedConcepts } from "@/components/profile/UntrackedConcepts"
import { useMasteryHistory } from "@/hooks/useMasteryHistory"
import { useModules } from "@/hooks/useModules"
import { buildMasteryCurves } from "@/lib/mastery-history"

interface MasteryCurvesProps {
  masteryThreshold: number
}

export function MasteryCurves({ masteryThreshold }: MasteryCurvesProps) {
  const history = useMasteryHistory()
  const modules = useModules()
  const [selected, setSelected] = useState<string | null>(null)
  const detailId = useId()

  // Join je čist izvod → memo po referencama odgovora (ne po svakom renderu).
  const model = useMemo(() => {
    if (!history.data || !modules.data) return null
    return buildMasteryCurves(history.data, modules.data)
  }, [history.data, modules.data])

  const selectedCurve = useMemo(() => {
    if (!model || !selected) return null
    for (const group of model.byModule) {
      const found = group.curves.find((c) => c.code === selected)
      if (found) return found
    }
    return null
  }, [model, selected])

  if (history.isPending || modules.isPending) {
    return (
      <Card aria-busy="true">
        <CardContent>
          <LoadingState lines={3} label="Učitavanje krivulja napretka" />
        </CardContent>
      </Card>
    )
  }

  if (history.isError || modules.isError) {
    return (
      <ErrorState
        title="Krivulje napretka nisu dostupne"
        message="Ne mogu dohvatiti povijest znanja — pokušaj ponovno."
        onRetry={() => {
          if (history.isError) void history.refetch()
          if (modules.isError) void modules.refetch()
        }}
      />
    )
  }

  if (!model) return null

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Krivulje znanja (BKT)</CardTitle>
          <CardDescription>
            Procjena P(L) — vjerojatnost da si savladao koncept — nakon svake
            prilike. Vodoravna crta je prag ovladanosti.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Novi user: 200 s praznim nizom NIJE greška. */}
          {model.totalPoints === 0 ? (
            <EmptyState
              icon={TrendingUp}
              title="Krivulje se pojavljuju nakon prvih riješenih zadataka"
              description="Svaki predani pokušaj — točan ili ne — dodaje točku na krivulju koncepata koje zadatak pokriva."
              action={
                <Button asChild>
                  <Link to="/">Riješi zadatak</Link>
                </Button>
              }
            />
          ) : (
            model.byModule.map((group) => (
              <section key={group.moduleNumber} className="space-y-2">
                <h3 className="text-sm font-medium text-muted-foreground">
                  {group.moduleName}
                </h3>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {group.curves.map((curve) => (
                    <ConceptCurveCard
                      key={curve.code}
                      curve={curve}
                      masteryThreshold={masteryThreshold}
                      detailId={detailId}
                      selected={curve.code === selected}
                      onSelect={(code) =>
                        // Ponovni klik na isti koncept zatvara detalj.
                        setSelected((prev) => (prev === code ? null : code))
                      }
                    />
                  ))}
                </div>
              </section>
            ))
          )}

          {/* (A) bez ijedne točke — legitimno „još nema podataka".
              Kod novog usera (totalPoints === 0) se PRESKAČE: EmptyState iznad
              već nosi tu poruku, a lista svih 26 koncepata pretvorila bi
              dizajnirano prazno stanje u zid čipova. */}
          {model.totalPoints > 0 && model.awaitingData.length > 0 && (
            <section className="space-y-1.5">
              <h3 className="text-sm font-medium text-muted-foreground">
                Još nema podataka
              </h3>
              <p className="text-xs text-muted-foreground">
                Ove koncepte još nisi dodirnuo — krivulja kreće od prvog
                pokušaja.
              </p>
              <ul className="flex flex-wrap gap-1.5">
                {model.awaitingData.map((concept) => (
                  <li
                    key={concept.code}
                    className="rounded-md border border-dashed border-border px-2 py-1 text-xs text-muted-foreground"
                  >
                    {concept.name}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </CardContent>
      </Card>

      {selectedCurve && (
        <div
          id={detailId}
          role="region"
          aria-label={`Detalj krivulje — ${selectedCurve.name}`}
        >
          <ConceptCurveDetail
            curve={selectedCurve}
            masteryThreshold={masteryThreshold}
          />
        </div>
      )}

      <UntrackedConcepts
        outOfScope={model.outOfScope}
        structural={model.structural}
      />
    </div>
  )
}
