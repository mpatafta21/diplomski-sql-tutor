/**
 * Pagination (Faza 4.5a) — offset paginacija nad `Page<T>` envelopeom
 * (`{items, total, limit, offset}` — 🔴 backend NEMA page/size, ne izmišljati ih).
 *
 * Izvučeno iz `AttemptHistory` (4.4a) bez promjene ponašanja; treći potrošač je
 * `/admin/agent-logs` u 4.5b (isti envelope na sve tri rute).
 *
 * INVARIJANTA #3: gumbi ostaju na default `size` (h-11 = 44 px touch target,
 * WCAG 2.5.5) — mjereno 44 px prije i poslije ekstrakcije. NE spuštati na `sm`.
 *
 * Komponenta je BEZ vlastitog state-a: offset drži roditelj (isti obrazac kao
 * prije), pa se ponašanje pri promjeni stranice ne mijenja.
 */
import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"

interface PaginationProps {
  /** Ukupan broj stavki iz `Page.total` — NE broj stranica. */
  total: number
  /** Veličina stranice (`Page.limit`). */
  limit: number
  /** Trenutni offset (`Page.offset`). */
  offset: number
  onOffsetChange: (offset: number) => void
  /** Opis skupa za čitač ekrana, npr. "povijest pokušaja". */
  label: string
}

export function Pagination({
  total,
  limit,
  offset,
  onOffsetChange,
  label,
}: PaginationProps) {
  const start = offset + 1
  const end = Math.min(offset + limit, total)
  const hasPrev = offset > 0
  const hasNext = offset + limit < total

  return (
    <div className="flex items-center justify-between gap-3 border-t border-border/60 pt-3">
      <p className="text-xs text-muted-foreground tabular-nums">
        Prikaz {start}–{end} od {total}
      </p>
      {/* default size = h-11 (44px touch target, invarijanta #3) */}
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
          disabled={!hasPrev}
          aria-label={`Prethodna stranica — ${label}`}
        >
          <ChevronLeft data-icon="inline-start" aria-hidden="true" />
          Prethodna
        </Button>
        <Button
          variant="outline"
          onClick={() => onOffsetChange(offset + limit)}
          disabled={!hasNext}
          aria-label={`Sljedeća stranica — ${label}`}
        >
          Sljedeća
          <ChevronRight data-icon="inline-end" aria-hidden="true" />
        </Button>
      </div>
    </div>
  )
}
