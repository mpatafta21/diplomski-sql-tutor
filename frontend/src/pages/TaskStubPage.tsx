/**
 * TaskStubPage (Faza 4.2a) — PLACEHOLDER rute /task/:id da Dashboard CTA
 * navigacija ne puca. Pravi Task screen (Monaco, Run/Submit, feedback) je 4.3.
 */
import { Link, useParams } from "react-router-dom"
import { ArrowLeft, Terminal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/state/EmptyState"

export function TaskStubPage() {
  const { taskId } = useParams()

  return (
    <div className="mx-auto max-w-3xl">
      <EmptyState
        icon={Terminal}
        title={`Zadatak #${taskId ?? "?"}`}
        description="Ekran zadatka (SQL editor, Run/Submit, feedback) stiže u pod-fazi 4.3 — ruta je već spremna."
        action={
          <Button asChild variant="outline">
            <Link to="/">
              <ArrowLeft data-icon="inline-start" aria-hidden="true" />
              Natrag na dashboard
            </Link>
          </Button>
        }
      />
    </div>
  )
}
