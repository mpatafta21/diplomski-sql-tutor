/**
 * MasteryBar (Faza 4.2) — jedini dopušteni način renderiranja mastery/XP
 * progresa.
 *
 * INVARIJANTA MasteryBara (ISPRAVLJENA u 4.4c — vidi NALAZ #33): mastery-0/25 fillovi
 * su ispod 3:1 prema pozadini (izmjereno na `card` oklch(0.205)/oklch(1)):
 * mastery-0 = 2.13:1 dark / 1.58:1 light, mastery-25 = 3.41:1 dark / 2.28:1
 * light. To je SVOJSTVO sekvencijalne skale — niski P(L) namjerno recedira.
 *
 * 🔴 RANIJA FORMULACIJA OVOG KOMENTARA BILA JE NETOČNA: tvrdila je da je
 * mitigacija „border-border ≥3:1 u obje teme". Izmjereno (uz ispravno alpha
 * kompozitiranje preko kartice): border je **1.32:1 dark / 1.26:1 light** —
 * dakle NIJE nosač od 3:1 i nikad nije bio.
 *
 * STVARNA mitigacija (i ona koja se NE smije ukloniti):
 *   1. `role="progressbar"` + `aria-valuenow` + `aria-label` — vrijednost je
 *      dostupna asistivnoj tehnologiji neovisno o boji;
 *   2. svaki potrošač ispisuje postotak kao TEKST uz bar (ConceptRow „· NN %",
 *      MasteryHighlights „NN %").
 * Boja je time redundantan kanal, pa 1.4.11 ne grize (grafika nije JEDINI
 * nosilac informacije). Border ostaje jer omeđuje track na 0 %, ne zbog kontrasta.
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
        // Border-ani track — invarijanta MasteryBara, NE uklanjati border.
        "h-2.5 w-full overflow-hidden rounded-full border border-border bg-muted/40",
        className,
      )}
    >
      {/* Fill je full-width + translateX (transform-only → GPU, bez layouta);
          track ga clippa. Na 0 % fill je potpuno izvan — border track ostaje
          vidljiv (invarijanta nosi TRACK, ne fill). */}
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
