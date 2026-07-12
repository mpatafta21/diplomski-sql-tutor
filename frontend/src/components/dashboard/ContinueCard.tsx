/**
 * ContinueCard (Faza 4.2) — "Nastavi ovdje" CTA, JEDINA primarna akcija ekrana.
 * /next-task je nullable na sva tri polja: task_id=null razlučujemo kroz
 * recommendationKind (done ≠ error); naslov zadatka dolazi iz /task/{id}
 * (preporuka nosi samo ID).
 */
import { Link } from "react-router-dom"
import { ArrowRight, CircleSlash2, PartyPopper } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import { ConceptChip } from "@/components/ConceptChip"
import { useNextTask } from "@/hooks/useNextTask"
import { useTask } from "@/hooks/useTask"
import { reasonText, recommendationKind } from "@/lib/recommendation"
import type { ConceptInfo } from "@/lib/mastery"

interface ContinueCardProps {
  conceptIndex: Map<string, ConceptInfo>
  /** Onboarding varijanta (svjež user): drugačiji naslov, ista mehanika. */
  onboarding?: boolean
}

export function ContinueCard({
  conceptIndex,
  onboarding = false,
}: ContinueCardProps) {
  const nextTask = useNextTask()
  const task = useTask(nextTask.data?.task_id)

  if (
    nextTask.isPending ||
    (nextTask.data?.task_id != null && task.isPending)
  ) {
    return (
      <Card aria-busy="true">
        <CardContent>
          <LoadingState lines={2} label="Učitavanje preporuke" />
        </CardContent>
      </Card>
    )
  }

  if (
    nextTask.isError ||
    task.isError ||
    (nextTask.data && recommendationKind(nextTask.data) === "error")
  ) {
    return (
      <ErrorState
        title="Preporuka nije dostupna"
        message="Ne mogu dohvatiti sljedeći zadatak — pokušaj ponovno."
        onRetry={() => {
          void nextTask.refetch()
          if (task.isError) void task.refetch()
        }}
      />
    )
  }

  const rec = nextTask.data

  if (recommendationKind(rec) === "done") {
    // exhausted ≠ "sve savladano": ponestalo je zadataka za PREPORUČENI koncept,
    // user može imati nesavladane koncepte — neutralna kartica, ne slavlje.
    const allMastered = rec.reason === "no_recommendation"
    const DoneIcon = allMastered ? PartyPopper : CircleSlash2
    return (
      <Card>
        <CardContent className="flex items-center gap-4">
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
          <div className="space-y-0.5">
            <h3 className="text-base font-semibold">
              {allMastered ? "Sve savladano" : "Nema novih zadataka"}
            </h3>
            <p className="text-sm text-muted-foreground">
              {reasonText(rec.reason)}
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  // kind === "task" → task_id != null, a task query je resolved (gate gore).
  const concept = rec.concept ? conceptIndex.get(rec.concept) : undefined

  return (
    <Card className="border-accent-warm/30">
      <CardHeader>
        <CardDescription className="text-xs font-medium tracking-wide text-accent-warm-text uppercase">
          {onboarding ? "Počni ovdje" : "Nastavi ovdje"}
        </CardDescription>
        <CardTitle className="text-lg">{task.data?.title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          {concept && <ConceptChip name={concept.name} tier={concept.tier} />}
          <p className="text-sm text-muted-foreground">
            {/* Svjež user još NEMA povijest — reason (npr. partial_continuation)
                dolazi iz tier PRIORA, pa bi "nastavi gdje si stao" lagao. */}
            {onboarding
              ? "Odabrano prema tvojoj trenutnoj razini znanja."
              : reasonText(rec.reason)}
          </p>
        </div>
        <Button asChild>
          <Link to={`/task/${rec.task_id}`}>
            {onboarding ? "Riješi prvi zadatak" : "Otvori zadatak"}
            <ArrowRight data-icon="inline-end" aria-hidden="true" />
          </Link>
        </Button>
      </CardContent>
    </Card>
  )
}
