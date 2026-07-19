/**
 * AttemptRow (Faza 4.4a) — jedan redak povijesti, proširiv (submitted_query + detail).
 *
 * 🔴 Verdict = deriveVerdict(is_correct, error_type) — ISTI izvor kao task screen
 * (lib/feedback.ts). feedbackText + detailPresentation također reusani: povijest i
 * task screen MORAJU reći isto o istom pokušaju. Verdict nosi ikona + tekst (chip),
 * boja je pojačanje (NALAZ #13).
 *
 * Naslov je <Link> na /task/{id} (van expand-buttona — <a> se ne smije ugnijezditi
 * u <button>). Expand je zaseban icon-button (44px, aria-expanded/aria-controls).
 */
import { useId, useState } from "react"
import { Link } from "react-router-dom"
import { ChevronDown } from "lucide-react"
import type { AttemptItem } from "@/lib/api/types"
import { deriveVerdict, detailPresentation, feedbackText } from "@/lib/feedback"
import { VERDICT_META } from "@/lib/verdict-ui"
import { cn } from "@/lib/utils"

const DT_FMT = new Intl.DateTimeFormat("hr-HR", {
  dateStyle: "medium",
  timeStyle: "short",
})

interface AttemptRowProps {
  attempt: AttemptItem
}

export function AttemptRow({ attempt }: AttemptRowProps) {
  const [open, setOpen] = useState(false)
  const detailId = useId()

  const verdict = deriveVerdict(attempt.is_correct, attempt.error_type)
  const meta = VERDICT_META[verdict]
  const VerdictIcon = meta.icon
  const message = feedbackText(verdict, attempt.error_type)
  const detailMode = detailPresentation(attempt.error_type, attempt.detail)

  return (
    <li className={cn("rounded-lg border", meta.border)}>
      <div className="flex items-center gap-3 p-3">
        {/* Verdict chip — ikona + tekst (ne samo boja) */}
        <span
          className={cn(
            "inline-flex shrink-0 items-center gap-1.5 text-sm font-medium",
            meta.chip,
          )}
        >
          <VerdictIcon className="size-4 shrink-0" aria-hidden="true" />
          {/* sr-only na mobitelu (ikona nosi vizual), ali UVIJEK u a11y stablu
              → čitač ekrana čuje verdict na svakom viewportu (NALAZ #13). */}
          <span className="sr-only sm:not-sr-only">{meta.label}</span>
        </span>

        <Link
          to={`/task/${attempt.task_id}`}
          className="min-w-0 flex-1 truncate text-sm font-medium hover:underline focus-visible:underline focus-visible:outline-none"
        >
          {attempt.task_title}
        </Link>

        <div className="hidden items-center gap-3 text-xs text-muted-foreground tabular-nums md:flex">
          <span title="Redni broj pokušaja za ovaj zadatak">
            #{attempt.attempt_number}
          </span>
          {attempt.xp_awarded > 0 && (
            <span className="text-accent-warm-text">
              +{attempt.xp_awarded} XP
            </span>
          )}
          <time dateTime={attempt.created_at}>
            {DT_FMT.format(new Date(attempt.created_at))}
          </time>
        </div>

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls={detailId}
          className="flex size-11 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors duration-fast ease-standard hover:bg-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          <span className="sr-only">
            {open ? "Sakrij detalje pokušaja" : "Prikaži detalje pokušaja"}
          </span>
          <ChevronDown
            className={cn(
              "size-4 transition-transform duration-base ease-standard motion-reduce:transition-none",
              open && "rotate-180",
            )}
            aria-hidden="true"
          />
        </button>
      </div>

      {open && (
        <div
          id={detailId}
          className="space-y-3 border-t border-border/60 px-3 py-3 duration-base ease-entrance animate-in fade-in motion-reduce:animate-none"
        >
          {/* Hrvatska poruka gore (isti tretman kao 4.3c FeedbackPanel) */}
          <p className="text-sm">{message}</p>

          {/* Meta koja je na užem ekranu skrivena iz retka */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground tabular-nums md:hidden">
            <span>Pokušaj #{attempt.attempt_number}</span>
            {attempt.xp_awarded > 0 && <span>+{attempt.xp_awarded} XP</span>}
            <time dateTime={attempt.created_at}>
              {DT_FMT.format(new Date(attempt.created_at))}
            </time>
          </div>

          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">
              Tvoj upit
            </p>
            <pre className="overflow-x-auto rounded bg-muted/60 px-2 py-1.5 font-mono text-xs leading-relaxed whitespace-pre-wrap">
              {attempt.submitted_query}
            </pre>
          </div>

          {attempt.rows_returned != null && (
            <p className="text-xs text-muted-foreground tabular-nums">
              Vraćeno redaka: {attempt.rows_returned}
              {attempt.execution_time_ms != null && (
                <>
                  {" · "}trajanje upita: {attempt.execution_time_ms} ms
                </>
              )}
            </p>
          )}

          {/* Tehnički detalj — hrvatski text ili mono blok (detailPresentation) */}
          {detailMode === "text" && attempt.detail && (
            <p className="text-sm text-muted-foreground">{attempt.detail}</p>
          )}
          {detailMode === "mono" && attempt.detail && (
            <pre className="overflow-x-auto rounded bg-background/60 px-2 py-1.5 font-mono text-xs leading-relaxed whitespace-pre text-muted-foreground">
              {attempt.detail}
            </pre>
          )}
        </div>
      )}
    </li>
  )
}
