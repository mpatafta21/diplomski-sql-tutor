/**
 * TaskEntryPage (Faza 4.6-eval) — ulaz u zadatak preko nav-stavke „Zadatak".
 *
 * Nav nema konkretan `:taskId` (ruta zadatka je `/task/:taskId`), pa ova ruta
 * razriješi TEKUĆU preporuku (`/next-task`) i preusmjeri na `/task/:taskId`.
 * Ista mehanika kao Dashboard „Nastavi ovdje" CTA (ContinueCard), samo bez
 * naslova zadatka — ne treba `/task/{id}` prefetch jer ionako odmah navigiramo.
 *
 * Nullable ishodi `/next-task` (isti mapper kao ContinueCard):
 *  - task  (task_id != null)                → Navigate `replace` na zadatak
 *  - done  (exhausted / no_recommendation)  → neutralna poruka + natrag na Dashboard
 *  - error (nepoznat reason uz task_id=null)→ oporavljivo (retry)
 *
 * `replace`: entry ruta NE smije ostati u historyju — inače bi Back s task
 * screena opet pao ovamo, ponovno razriješio preporuku i vratio na isti zadatak
 * (zamka beskonačnog vraćanja).
 */
import { Link, Navigate } from "react-router-dom"
import { CircleSlash2, PartyPopper } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingState } from "@/components/state/LoadingState"
import { ErrorState } from "@/components/state/ErrorState"
import { useNextTask } from "@/hooks/useNextTask"
import { reasonText, recommendationKind } from "@/lib/recommendation"

export function TaskEntryPage() {
  const nextTask = useNextTask()

  if (nextTask.isPending) {
    return <LoadingState label="Tražim tvoj sljedeći zadatak" />
  }

  // isError (mrežni/transport) i kind==="error" (agent exception put) → isti
  // oporavljivi ekran; task_id=null uz nepoznat reason fail-CLOSED je "error".
  if (nextTask.isError || recommendationKind(nextTask.data) === "error") {
    return (
      <div className="mx-auto max-w-2xl">
        <ErrorState
          title="Preporuka nije dostupna"
          message="Ne mogu dohvatiti sljedeći zadatak — pokušaj ponovno."
          onRetry={() => void nextTask.refetch()}
        />
      </div>
    )
  }

  const rec = nextTask.data
  const kind = recommendationKind(rec)

  if (kind === "task") {
    // rec.task_id != null je zajamčen kindom "task" (recommendation.ts).
    return <Navigate to={`/task/${rec.task_id}`} replace />
  }

  // kind === "done": exhausted ≠ „sve savladano" — ponestalo je zadataka za
  // PREPORUČENI koncept (user može imati nesavladane koncepte), pa neutralna
  // kartica, ne slavlje. Samo `no_recommendation` znači potpunu savladanost.
  const allMastered = rec.reason === "no_recommendation"
  const DoneIcon = allMastered ? PartyPopper : CircleSlash2

  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardContent className="flex flex-col items-center gap-4 py-10 text-center">
          <div
            className={
              allMastered
                ? "flex size-12 shrink-0 items-center justify-center rounded-full border border-accent-warm/40 bg-accent-warm/10"
                : "flex size-12 shrink-0 items-center justify-center rounded-full border border-border bg-muted"
            }
          >
            <DoneIcon
              className={
                allMastered
                  ? "size-6 text-accent-warm-text"
                  : "size-6 text-muted-foreground"
              }
              aria-hidden="true"
            />
          </div>
          <div className="space-y-1">
            <h1 className="text-lg font-semibold">
              {allMastered ? "Sve savladano" : "Nema novih zadataka"}
            </h1>
            <p className="text-sm text-muted-foreground">
              {reasonText(rec.reason)}
            </p>
          </div>
          <Button asChild variant="outline">
            <Link to="/">Natrag na Dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
