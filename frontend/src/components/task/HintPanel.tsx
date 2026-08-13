/**
 * HintPanel (Faza 5.2, §C3) — slot za savjet, IZNAD `FeedbackPanel`a.
 *
 * 🔴 NE ULAZI U `submitSlot` ENUM (§C.6.2). Enum je „točno jedno stanje predaje";
 * savjet je neovisan i KOEGZISTIRA s feedbackom — student traži savjet upravo
 * *nakon* što je vidio ocjenu netočne predaje. Da uđe u enum, jedan bi istisnuo
 * drugi.
 *
 * 🔴 BEZ ANIMACIJE ULAZA (C.2.2): ponovljeni zahtjev vraća bajt-identičan odgovor
 * iz pohrane, pa frontend NE MOŽE razlikovati „upravo generirano" od „vraćeno".
 * Animacija novosti bi lagala na svakom ponavljanju.
 *
 * 🔴 Boja NIJE verdikt. Ploha je neutralna (`muted`), ikona `muted-foreground` —
 * savjet nije ni točno ni netočno, pa ne posuđuje semantiku iz MASTER §2.2.
 * `neutral-soft` je namjerno izbjegnut: N-10 ga je rezervirao za KVAR aplikacije.
 */
import { Lightbulb } from "lucide-react"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import {
  hintFailureRetryable,
  hintFailureText,
  refillText,
  type HintFailure,
} from "@/lib/hint"

interface HintPanelProps {
  /** Tekst savjeta iz `HintResponse`; bez njega slot nema uspješno stanje. */
  hintText?: string
  /**
   * Savjet se odnosi na RANIJU predaju (§C3.1). Ne briše se — student ga je
   * platio kreditom i ne može ga vratiti besplatno — nego se OZNAČAVA.
   */
  stale: boolean
  isPending: boolean
  failure?: HintFailure
  /** Iz `/profile` — odbrojavanje u `rate-limited` stanju. */
  nextRefillAt?: string | null
  onRetry: () => void
}

export function HintPanel({
  hintText,
  stale,
  isPending,
  failure,
  nextRefillAt,
  onRetry,
}: HintPanelProps) {
  if (isPending) {
    return (
      <LoadingState
        lines={2}
        label="Dohvaćanje savjeta"
        className="rounded-md border border-border p-3"
      />
    )
  }

  if (failure === "hint_rate_limited") {
    const kada = refillText(nextRefillAt, Date.now())
    return (
      <div
        role="status"
        className="flex items-start gap-3 rounded-md border border-border bg-muted/40 p-3"
      >
        <Lightbulb
          aria-hidden="true"
          className="mt-0.5 size-4 shrink-0 text-muted-foreground"
        />
        <p className="text-sm text-muted-foreground">
          {hintFailureText("hint_rate_limited")}
          {kada ? ` Sljedeći savjet ${kada}.` : ""}
        </p>
      </div>
    )
  }

  if (failure) {
    // `hints_disabled` ovdje ne dolazi — gumb se sakriva i slot ostaje prazan.
    return (
      <ErrorState
        title="Savjet nije dohvaćen"
        message={hintFailureText(failure)}
        onRetry={hintFailureRetryable(failure) ? onRetry : undefined}
      />
    )
  }

  if (!hintText) return null

  return (
    <div
      role="status"
      aria-label="Savjet"
      className="flex items-start gap-3 rounded-md border border-border bg-muted/40 p-3"
    >
      <Lightbulb
        aria-hidden="true"
        className="mt-0.5 size-4 shrink-0 text-muted-foreground"
      />
      <div className="min-w-0 space-y-1">
        <p className="text-sm text-card-foreground">{hintText}</p>
        {stale && (
          <p className="text-sm text-muted-foreground">
            Savjet je zatražen uz prethodnu predaju.
          </p>
        )}
      </div>
    </div>
  )
}
