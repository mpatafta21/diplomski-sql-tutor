/**
 * TaskDifficultyChip (Faza 4.3a) — čip TEŽINE ZADATKA (tasks.difficulty, int 1–5)
 * u DIFFICULTY skali (magenta ×5, MASTER.md §2.5). NE miješati s ConceptChip
 * (tier/violet ×3). Token klase vuče iz DIFFICULTY_CLASS (DifficultyChip.tsx —
 * jedna mapa za sve potrošače, bez dupliciranja).
 *
 * Mapiranje 1–5 → 4 rank tokena: skala ima 5 tokena, ali `cross_module` NIJE
 * rank (desaturirani token za transverzalni modul 0) — pa 4 i 5 dijele
 * `expert`. Numerička vrijednost ("3/5") nosi preciznost, boja nosi razred.
 */
import { DIFFICULTY_CLASS } from "@/components/DifficultyChip"
import { cn } from "@/lib/utils"

const RANK: Record<number, string> = {
  1: "beginner",
  2: "intermediate",
  3: "advanced",
  4: "expert",
  5: "expert",
}

interface TaskDifficultyChipProps {
  /** tasks.difficulty — backend garantira 1–5; izvan raspona → neutralan čip. */
  difficulty: number
  className?: string
}

export function TaskDifficultyChip({
  difficulty,
  className,
}: TaskDifficultyChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium tabular-nums",
        DIFFICULTY_CLASS[RANK[difficulty] ?? ""] ??
          "bg-muted text-muted-foreground",
        className,
      )}
    >
      Težina {difficulty}/5
    </span>
  )
}
