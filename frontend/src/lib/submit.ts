/**
 * Mapiranje neuspjeha `POST /attempt` → stanje UI-ja + hrvatska poruka.
 *
 * 🔴 MAPIRA SE PO `detail`, NE PO HTTP STATUSU — isti obrazac kao `lib/hint.ts`.
 * Nakon popravaka #62/#63 postoje TRI ishoda, a ne dva, i dijele dva statusa:
 *
 *   • `503 coordinator_busy`      — tok NIJE ni primljen; ništa nije upisano,
 *                                   a ponovni pokušaj odmah ima smisla
 *   • `503 plan_unavailable`      — plan izvedbe se nije mogao dohvatiti (M6);
 *                                   pokušaj NIJE ni nastao (ERRATA #69)
 *   • `504 evaluation_timeout`    — evaluacija nije stigla, ništa nije upisano
 *   • `504 orchestration_timeout` — gateway odustao, ništa nije upisano
 *
 * 🔴 Od `plan_unavailable` (2026-08-14) su ČETIRI ishoda na DVA statusa, i status
 * 503 nose DVA različita razloga — što je i konačni razlog zašto se mapira po
 * `detail`u: granananje po statusu ovdje više nije ni izvedivo.
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
  | "plan_unavailable"
  | "evaluation_timeout"
  | "orchestration_timeout"
  | "unknown"

const POZNATI: ReadonlySet<string> = new Set([
  "coordinator_busy",
  "plan_unavailable",
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
  // 🔴 Smetnja sustava, NE studentova greška — poruka to mora reći izrijekom,
  // jer student na M6 zadatku inače pomisli da mu je upit pogrešan. Pokušaj nije
  // upisan i BKT nije diran (ERRATA #69).
  plan_unavailable: {
    title: "Plan izvedbe nije bilo moguće dohvatiti",
    message:
      "Ovo nije greška u tvom upitu — sustav nije uspio pročitati plan izvedbe. Rješenje nije ocijenjeno; pokušaj ponovno predati.",
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
