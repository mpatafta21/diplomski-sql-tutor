/**
 * ErrorState (Faza 4.1c, §3.4) — oporavljivo error stanje s retry akcijom.
 * Vuče semantičke tokene (incorrect/-soft, MASTER.md §2.2). Za mrežne greške
 * (TanStack Query error) i kao ErrorBoundary fallback.
 */
import { AlertTriangle, RotateCcw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface ErrorStateProps {
  title?: string
  message?: string
  /** Retry callback — bez njega se gumb ne prikazuje. */
  onRetry?: () => void
  className?: string
}

export function ErrorState({
  title = "Nešto je pošlo po zlu",
  message = "Pokušaj ponovno — ako se greška ponavlja, javi se administratoru.",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        "flex w-full flex-col items-center justify-center gap-3 rounded-xl border border-incorrect/30 bg-incorrect-soft px-6 py-12 text-center",
        className,
      )}
    >
      <div className="flex size-12 items-center justify-center rounded-full bg-incorrect/10">
        <AlertTriangle className="size-6 text-incorrect" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <h3 className="text-base font-semibold">{title}</h3>
        <p className="max-w-sm text-sm text-muted-foreground">{message}</p>
      </div>
      {onRetry && (
        <Button variant="outline" onClick={onRetry} className="mt-2">
          <RotateCcw data-icon="inline-start" />
          Pokušaj ponovno
        </Button>
      )}
    </div>
  )
}
