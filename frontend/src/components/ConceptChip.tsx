/**
 * ConceptChip (Faza 4.2) — čip koncepta u TIER boji (MASTER.md §2.4, violet
 * skala; NE miješati s difficulty). Statični Record mape → Tailwind JIT vidi
 * pune literale.
 */
import { cn } from "@/lib/utils"

/** Ljudska oznaka tiera — JEDNA mapa za sve potrošače (chip, filteri 4.3+). */
export const TIER_LABEL: Record<string, string> = {
  easy: "Lako",
  medium: "Srednje",
  hard: "Teško",
}

const TIER_CLASS: Record<string, string> = {
  easy: "bg-tier-easy text-tier-easy-foreground",
  medium: "bg-tier-medium text-tier-medium-foreground",
  hard: "bg-tier-hard text-tier-hard-foreground",
}

interface ConceptChipProps {
  name: string
  tier: string
  className?: string
}

export function ConceptChip({ name, tier, className }: ConceptChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
        // Nepoznat tier (buduća migracija) → neutralan chip, ne kriva skala.
        TIER_CLASS[tier] ?? "bg-muted text-muted-foreground",
        className,
      )}
    >
      {name}
    </span>
  )
}
