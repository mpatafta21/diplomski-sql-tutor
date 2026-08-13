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
 * 🔴 Boja NIJE verdikt. Ploha je `hint` (cyan, hue 195) — VLASTITI token uveden
 * u 5.2, ne posuđena semantika: 45° od `correct`, 135° od `partial`, 170° od
 * `incorrect`, pa se ne može pročitati kao ocjena. Obrazloženje izbora huea i
 * zašto je amber odbijen stoji uz `--hint` u `index.css`.
 * `neutral-soft` je namjerno izbjegnut: N-10 ga je rezervirao za KVAR aplikacije,
 * a `ErrorState` u grani neuspjeha i dalje ostaje NEUTRALAN — kvar dohvata nije
 * savjet i ne smije nositi njegovu boju.
 *
 * 🔴 Ploha ostaje na disciplini `-soft` obitelji (L 0.24, C 0.04). Savjet stoji
 * IZNAD panela s ocjenom i ne smije ga nadglasati — isticanje nosi gumb.
 */
import { Lightbulb } from "lucide-react"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import {
  hintFailureRetryable,
  hintFailureText,
  hintParagraphs,
  refillText,
  type HintFailure,
} from "@/lib/hint"

/**
 * Tekst savjeta s minimalnim Markdownom (`**bold**`, `` `kod` ``).
 *
 * 🔴 Segmenti se renderiraju kao React čvorovi, NIKAD kroz
 * `dangerouslySetInnerHTML`: tekst dolazi od modela i ne smije moći unijeti
 * oznake u DOM. Ovako je najgori mogući ishod ružna rečenica, ne injekcija.
 */
function HintTekst({ text }: { text: string }) {
  return (
    <>
      {hintParagraphs(text).map((odlomak, i) => (
        <p key={i} className="text-sm text-card-foreground">
          {odlomak.map((s, j) =>
            s.kind === "bold" ? (
              <strong key={j} className="font-semibold">
                {s.value}
              </strong>
            ) : s.kind === "code" ? (
              // 🔴 BEZ `text-xs`, za razliku od mono bloka u `FeedbackPanel`u:
              // ondje je tehnički detalj koji se namjerno prigušuje, ovdje su
              // imena stupaca koja student mora PROČITATI I UTIPKATI. Izmjereno:
              // `text-xs` daje 10,24 px (root skala je ~14 px, ne 16), a to je
              // ista greška koju je platio `RegisterPage` (N-4). Nasljeđuje
              // `text-sm` odlomka; `py-px` drži visinu retka mirnom.
              <code
                key={j}
                className="rounded bg-background/60 px-1 py-px font-mono"
              >
                {s.value}
              </code>
            ) : (
              <span key={j}>{s.value}</span>
            ),
          )}
        </p>
      ))}
    </>
  )
}

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
        className="rounded-md border border-hint/30 p-3"
      />
    )
  }

  if (failure === "hint_rate_limited") {
    const kada = refillText(nextRefillAt, Date.now())
    return (
      <div
        role="status"
        className="flex items-start gap-3 rounded-md border border-hint/25 bg-hint-soft/60 p-3"
      >
        <Lightbulb
          aria-hidden="true"
          className="mt-0.5 size-4 shrink-0 text-hint/70"
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
      className="flex items-start gap-3 rounded-md border border-hint/40 bg-hint-soft p-3"
    >
      <Lightbulb
        aria-hidden="true"
        className="mt-0.5 size-4 shrink-0 text-hint"
      />
      <div className="min-w-0 space-y-1">
        <HintTekst text={hintText} />
        {stale && (
          <p className="text-sm text-muted-foreground">
            Savjet je zatražen uz prethodnu predaju.
          </p>
        )}
      </div>
    </div>
  )
}
