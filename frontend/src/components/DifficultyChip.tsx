/**
 * DifficultyChip (Faza 4.2b) — čip MODULA u DIFFICULTY boji (MASTER.md §2.5,
 * magenta skala, 5 koraka). NE miješati s ConceptChip (tier/violet) — dvije
 * odvojene backend skale (modules.difficulty vs concepts.tier).
 */
import { cn } from "@/lib/utils"

const DIFFICULTY_CLASS: Record<string, string> = {
  beginner: "bg-difficulty-beginner text-difficulty-beginner-foreground",
  intermediate:
    "bg-difficulty-intermediate text-difficulty-intermediate-foreground",
  advanced: "bg-difficulty-advanced text-difficulty-advanced-foreground",
  expert: "bg-difficulty-expert text-difficulty-expert-foreground",
  cross_module:
    "bg-difficulty-cross-module text-difficulty-cross-module-foreground",
}

const DIFFICULTY_LABEL: Record<string, string> = {
  beginner: "Početna",
  intermediate: "Srednja",
  advanced: "Napredna",
  expert: "Ekspertna",
  cross_module: "Transverzalno",
}

interface DifficultyChipProps {
  difficulty: string
  className?: string
}

export function DifficultyChip({ difficulty, className }: DifficultyChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
        DIFFICULTY_CLASS[difficulty] ?? "bg-muted text-muted-foreground",
        className,
      )}
    >
      {DIFFICULTY_LABEL[difficulty] ?? difficulty}
    </span>
  )
}
