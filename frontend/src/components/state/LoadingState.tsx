/**
 * LoadingState (Faza 4.1c, §3.4) — skeleton, NE spinner (MASTER.md §7).
 * Primitiv za sva loading stanja data komponenti od 4.2 nadalje.
 */
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

interface LoadingStateProps {
  /** Broj skeleton redova (default 3). */
  lines?: number
  /** Kratki opis za čitače ekrana (default „Učitavanje"). */
  label?: string
  className?: string
}

export function LoadingState({
  lines = 3,
  label = "Učitavanje",
  className,
}: LoadingStateProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className={cn("w-full space-y-3", className)}
    >
      <Skeleton className="h-5 w-2/5" />
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton
          key={i}
          className="h-4"
          style={{ width: `${90 - i * 12}%` }}
        />
      ))}
      <span className="sr-only">{label}…</span>
    </div>
  )
}

/** Varijanta preko cijele stranice (auth check, inicijalni mount). */
export function FullPageLoading({ label }: { label?: string }) {
  return (
    <div className="flex min-h-svh items-center justify-center p-8">
      <LoadingState lines={4} label={label} className="max-w-md" />
    </div>
  )
}
