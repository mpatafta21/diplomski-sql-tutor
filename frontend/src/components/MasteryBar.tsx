/**
 * MasteryBar (Faza 4.2) — jedini dopušteni način renderiranja mastery/XP
 * progresa. INVARIJANTA #1: mastery-0/25 fillovi su <3:1 kontrast prema
 * pozadini → fill se SMIJE renderirati samo unutar vidljivog border-anog
 * tracka (border-border ≥3:1 u obje teme). Track je nosač informacije, fill
 * je vrijednost.
 */
import { cn } from "@/lib/utils"

interface MasteryBarProps {
  /** Vrijednost 0–1 (P(L) ili xp_in_level/level_step). */
  value: number
  /** Tailwind klasa filla (npr. bg-mastery-50, bg-accent-warm). */
  fillClass: string
  /** Pristupačan opis (npr. "Savladanost: GROUP BY 62 %"). */
  label: string
  className?: string
}

export function MasteryBar({
  value,
  fillClass,
  label,
  className,
}: MasteryBarProps) {
  const pct = Math.round(Math.min(Math.max(value, 0), 1) * 100)

  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      aria-label={label}
      className={cn(
        // Border-ani track — invarijanta #1, NE uklanjati border.
        "h-2.5 w-full overflow-hidden rounded-full border border-border bg-muted/40",
        className,
      )}
    >
      {/* Fill je full-width + translateX (transform-only → GPU, bez layouta);
          track ga clippa. Na 0 % fill je potpuno izvan — border track ostaje
          vidljiv (invarijanta #1 nosi TRACK, ne fill). */}
      <div
        className={cn(
          "h-full w-full rounded-full transition-transform duration-base ease-standard motion-reduce:transition-none",
          fillClass,
        )}
        style={{ transform: `translateX(-${100 - pct}%)` }}
      />
    </div>
  )
}
