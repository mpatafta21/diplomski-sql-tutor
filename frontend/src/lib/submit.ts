/**
 * Mapiranje neuspjeha `POST /attempt` → stanje UI-ja + hrvatska poruka.
 *
 * 🔴 MAPIRA SE PO `detail`, NE PO HTTP STATUSU — isti obrazac kao `lib/hint.ts`.
 * Nakon popravaka #62/#63 postoje TRI ishoda, a ne dva, i dijele dva statusa:
 *
 *   • `503 coordinator_busy`      — tok NIJE ni primljen; ništa nije upisano,
 *                                   a ponovni pokušaj odmah ima smisla
 *   • `504 evaluation_timeout`    — evaluacija nije stigla, ništa nije upisano
 *   • `504 orchestration_timeout` — gateway odustao, ništa nije upisano
 *
 * `fix-62-63-wrapup.md` §F.1 propisuje upravo ovu podjelu i ostavlja je Fazi 5.2,
 * koja ju nije izvela — do 2026-08-14 je `TaskPage` granao samo na `status === 504`,
 * pa je `coordinator_busy` padao u generičku poruku „Veza prema poslužitelju nije
 * uspjela". Ta poruka je bila NETOČNA: veza je uspjela, poslužitelj je odgovorio,
 * sustav je bio zauzet.
 *
 * 🔴 Slučaj „upisano je, ali odgovor kasni" VIŠE NE POSTOJI — takav zahtjev od
 * #63 vraća 200 sa stvarnim ishodom. Zato sve tri poruke smiju reći da rješenje
 * NIJE ocijenjeno, bez ograde.
 *
 * 🔴 FAIL-CLOSED: nepoznat `detail` → `unknown` s generičkom porukom i retryjem.
 * Nikad prazan slot.
 */

export type SubmitFailure =
  | "coordinator_busy"
  | "evaluation_timeout"
  | "orchestration_timeout"
  | "unknown"

const POZNATI: ReadonlySet<string> = new Set([
  "coordinator_busy",
  "evaluation_timeout",
  "orchestration_timeout",
])

/** `detail` iz tijela greške → `SubmitFailure`. Oblik tijela se ne pretpostavlja. */
export function submitFailure(body: unknown): SubmitFailure {
  const detail = (body as { detail?: unknown } | null | undefined)?.detail
  return typeof detail === "string" && POZNATI.has(detail)
    ? (detail as SubmitFailure)
    : "unknown"
}

interface SubmitPoruka {
  title: string
  message: string
}

const PORUKE: Record<SubmitFailure, SubmitPoruka> = {
  // Zauzeće je PROLAZNO i kratko (jedan FSM, serijalizirano) — zato „odmah",
  // za razliku od isteka gdje čekanje ne pomaže.
  coordinator_busy: {
    title: "Sustav je trenutno zauzet",
    message:
      "Netko drugi upravo predaje rješenje. Rješenje nije ocijenjeno — pokušaj odmah ponovno.",
  },
  evaluation_timeout: {
    title: "Evaluacija nije stigla na vrijeme",
    message: "Rješenje nije zabilježeno ni ocijenjeno — predaj ga ponovno.",
  },
  orchestration_timeout: {
    title: "Sustav ne odgovara",
    message: "Rješenje nije zabilježeno ni ocijenjeno — predaj ga ponovno.",
  },
  unknown: {
    title: "Predaja nije uspjela",
    message: "Rješenje nije ocijenjeno — pokušaj ponovno.",
  },
}

export function submitPoruka(failure: SubmitFailure): SubmitPoruka {
  return PORUKE[failure]
}
