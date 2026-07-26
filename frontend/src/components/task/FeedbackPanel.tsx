/**
 * FeedbackPanel (Faza 4.3c) — ocjena /attempt odgovora: pedagoško srce ekrana.
 *
 * TRI stanja (lib/feedback.ts — partial tokeni iz 4.1b OVDJE se aktiviraju):
 *   correct → ✅ zeleno · partial → ⚠️ žuto (xp_delta>0!) · incorrect → ❌ crveno.
 * Verdict NIKAD ne nosi samo boja: ikona + tekstualna oznaka uz svaku granu
 * (WCAG 1.4.1; partial hue 55–60 je blizu accent-warm 70–85 — zato je
 * ikona+tekst OBAVEZAN kanal, boja je pojačanje).
 *
 * XP pravila (živi dokazi iz KORAK 0):
 *  - prikaz APSOLUTNOG `xp` iz odgovora; xp_delta je SAMO task-delta (badge XP
 *    NIJE u delti: delte 0+15=15 a xp=25 — suma bi divergirala)
 *  - level_up NEMA flag → deriviran (prop) usporedbom s prethodnim levelom
 *  - new_badges su KOZMETIKA (flag #3) — unlock prikaz odavde, autoritativno
 *    stanje bedževa čita /profile (invalidiran u useSubmitAttempt)
 *
 * Motion: jedino mjesto gdje motion nosi nagradu (MASTER §5 — suzdržano, bez
 * konfeta): pop-in ulaz panela + reward-ease na XP/badge čipovima, sve kroz
 * tokene i s motion-reduce guardom.
 */
import { memo } from "react"
import { Link } from "react-router-dom"
import {
  ArrowRight,
  Award,
  CheckCircle2,
  CircleAlert,
  Flame,
  TriangleAlert,
  XCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { BADGE_ICON, BADGE_ICON_FALLBACK } from "@/lib/badge-icons"
import type { AttemptResponse, BadgeCatalogItem } from "@/lib/api/types"
import {
  deriveVerdict,
  detailPresentation,
  feedbackText,
  type Verdict,
} from "@/lib/feedback"
import { reasonText, recommendationKind } from "@/lib/recommendation"
import { cn } from "@/lib/utils"

/** Vizual po verdictu — boja je POJAČANJE, ikona+oznaka nose značenje. */
const VERDICT_UI: Record<
  Verdict,
  { label: string; icon: typeof CheckCircle2; wrap: string; chip: string }
> = {
  correct: {
    label: "Točno",
    icon: CheckCircle2,
    wrap: "border-correct/40 bg-correct-soft",
    chip: "text-correct",
  },
  partial: {
    label: "Djelomično",
    icon: TriangleAlert,
    wrap: "border-partial/40 bg-partial-soft",
    chip: "text-partial",
  },
  incorrect: {
    label: "Netočno",
    icon: XCircle,
    wrap: "border-incorrect/40 bg-incorrect-soft",
    chip: "text-incorrect",
  },
  unknown: {
    label: "Ocjenjivanje nije uspjelo",
    icon: CircleAlert,
    wrap: "border-border bg-muted",
    chip: "text-muted-foreground",
  },
}

interface FeedbackPanelProps {
  attempt: AttemptResponse
  /** Deriviran u TaskView (nema flaga u odgovoru); false i na cache-miss. */
  levelUp: boolean
  /** Katalog bedževa (code→name/icon) za new_badges kozmetiku. */
  badgeCatalog: BadgeCatalogItem[] | undefined
  /** code→ime koncepta za CTA ("Sljedeći zadatak · <koncept>"). */
  conceptName: (code: string | null | undefined) => string | undefined
}

export const FeedbackPanel = memo(function FeedbackPanel({
  attempt,
  levelUp,
  badgeCatalog,
  conceptName,
}: FeedbackPanelProps) {
  const verdict = deriveVerdict(
    attempt.feedback.is_correct,
    attempt.feedback.error_type,
  )
  const ui = VERDICT_UI[verdict]
  const Icon = ui.icon
  const message = feedbackText(verdict, attempt.feedback.error_type)
  const detailMode = detailPresentation(
    attempt.feedback.error_type,
    attempt.feedback.detail,
  )
  const rec = attempt.recommendation
  const recKind = recommendationKind(rec)
  const nextConcept = conceptName(rec.concept)

  return (
    <section
      aria-label="Ocjena rješenja"
      role="status"
      // Pop-in ulaz (jedina "nagradna" pojava panela): scale 0.97→1 + fade,
      // entrance ease; bez pokreta uz reduced-motion (samo fade kroz global guard).
      className={cn(
        "rounded-md border p-4 duration-base ease-entrance animate-in fade-in zoom-in-95 motion-reduce:animate-none",
        ui.wrap,
      )}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <p className={cn("flex items-center gap-1.5 font-semibold", ui.chip)}>
            <Icon aria-hidden="true" className="size-4.5 shrink-0" />
            {ui.label}
          </p>
          <p className="text-sm leading-relaxed">{message}</p>
        </div>

        {/* XP/streak čipovi — accent-warm ISKLJUČIVO za gamifikaciju (§2.1).
            Uvijek APSOLUTNI xp; delta je zasebna oznaka. */}
        <div className="flex shrink-0 items-center gap-2">
          {attempt.xp_delta > 0 && (
            <span className="rounded-md bg-accent-warm px-2 py-0.5 text-xs font-semibold text-accent-warm-foreground tabular-nums duration-base ease-reward animate-in zoom-in-90 motion-reduce:animate-none">
              +{attempt.xp_delta} XP
            </span>
          )}
          {/* First-solve gate: već riješen task ne nosi XP ponovno. Prikazuje se
              umjesto +XP čipa (xp_delta je tada 0) — jasan razlog, bez „zašto
              nisam dobio XP?" konfuzije. */}
          {attempt.already_solved && (
            <span className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-0.5 text-xs font-medium text-muted-foreground">
              <CheckCircle2 aria-hidden="true" className="size-3.5" />
              Već riješeno · bez XP
            </span>
          )}
          <span className="text-xs text-muted-foreground tabular-nums">
            Ukupno {attempt.xp} XP · Level {attempt.level}
          </span>
          {attempt.current_streak > 1 && (
            <span className="inline-flex items-center gap-1 text-xs text-accent-warm-text tabular-nums">
              <Flame aria-hidden="true" className="size-3.5" />
              {attempt.current_streak}
            </span>
          )}
        </div>
      </div>

      {detailMode === "text" && (
        <p className="mt-2 text-sm text-muted-foreground">
          {attempt.feedback.detail}
        </p>
      )}
      {detailMode === "mono" && (
        // Tehnički detalj (PG poruka / interni string) — diskretno, mono,
        // NIKAD kao glavna poruka (glavna je hrvatska, iz mape).
        <pre className="mt-2 overflow-x-auto rounded bg-background/60 px-2 py-1.5 font-mono text-xs leading-relaxed whitespace-pre text-muted-foreground">
          {attempt.feedback.detail}
        </pre>
      )}

      {levelUp && (
        <p className="mt-3 flex items-center gap-1.5 text-sm font-semibold text-accent-warm-text duration-base ease-reward animate-in fade-in slide-in-from-bottom-1 motion-reduce:animate-none">
          <Award aria-hidden="true" className="size-4" />
          Novi level — {attempt.level}!
        </p>
      )}

      {attempt.new_badges.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted-foreground">Novi bedž:</span>
          {attempt.new_badges.map((code, i) => {
            const badge = badgeCatalog?.find((b) => b.code === code)
            const BadgeIcon =
              BADGE_ICON[badge?.icon ?? ""] ?? BADGE_ICON_FALLBACK
            return (
              <span
                key={code}
                className="inline-flex items-center gap-1 rounded-md bg-accent-warm px-2 py-0.5 text-xs font-medium text-accent-warm-foreground duration-base ease-reward animate-in zoom-in-90 fill-mode-backwards motion-reduce:animate-none"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <BadgeIcon aria-hidden="true" className="size-3.5" />
                {badge?.name ?? code}
              </span>
            )
          })}
        </div>
      )}

      {/* CTA iz recommendation — reuse 4.2a mappera (fail-closed: error ≠ slavlje). */}
      <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-border/60 pt-3">
        <p className="text-xs text-muted-foreground">
          {reasonText(rec.reason)}
        </p>
        {recKind === "task" && rec.task_id != null && (
          <Button
            asChild
            variant={verdict === "correct" ? "default" : "outline"}
          >
            <Link to={`/task/${rec.task_id}`}>
              Sljedeći zadatak
              {nextConcept && (
                <span className="text-xs opacity-80">· {nextConcept}</span>
              )}
              <ArrowRight data-icon="inline-end" aria-hidden="true" />
            </Link>
          </Button>
        )}
        {recKind === "done" && (
          <span className="text-sm font-medium">
            Nema daljnjih zadataka za sada — odlično odrađeno!
          </span>
        )}
        {recKind === "error" && (
          <span className="text-xs text-muted-foreground">
            Preporuka trenutno nije dostupna — odaberi zadatak kroz Module.
          </span>
        )}
      </div>
    </section>
  )
})
