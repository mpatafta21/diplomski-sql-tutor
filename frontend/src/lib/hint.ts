/**
 * Mapiranje ishoda `POST /hint` → stanje UI-ja + hrvatska poruka (Faza 5.2, §C1).
 *
 * 🔴 MAPIRA SE PO `detail`, NE PO HTTP STATUSU (§C.2.1). Status `503` nosi DVA
 * suprotna značenja:
 *   • `hints_disabled`   — značajka ne postoji na ovom poslužitelju → gumb NESTAJE
 *   • `hint_unavailable` — značajka postoji, ovaj put nema savjeta → gumb OSTAJE
 * Grananje po statusu bi ta dva stanja spojilo u jedno i sakrilo gumb zbog jednog
 * pada providera.
 *
 * 🔴 FAIL-CLOSED, obrazac `lib/feedback.ts` za nepoznat `error_type`: nepoznat
 * `detail` → `unknown` s generičkom porukom. Nikad prazan slot — student koji je
 * kliknuo mora vidjeti ishod, i onda kad ishod nismo predvidjeli.
 */

export type HintFailure =
  | "hints_disabled"
  | "hint_not_unlocked"
  | "hint_rate_limited"
  | "hint_unavailable"
  | "hint_timeout"
  | "unknown"

/** Ishodi koje ruta doista vraća (§C.2, uhvaćeno protiv živog poslužitelja). */
const POZNATI: ReadonlySet<string> = new Set([
  "hints_disabled",
  "hint_not_unlocked",
  "hint_rate_limited",
  "hint_unavailable",
  "hint_timeout",
])

/**
 * `detail` iz tijela greške → `HintFailure`.
 *
 * Tijelo može biti bilo što (mreža, proxy, 422 s nizom ValidationError objekata),
 * pa se ne pretpostavlja oblik: sve što nije poznat string je `unknown`.
 */
export function hintFailure(body: unknown): HintFailure {
  const detail = (body as { detail?: unknown } | null | undefined)?.detail
  if (typeof detail === "string" && POZNATI.has(detail)) {
    return detail as HintFailure
  }
  return "unknown"
}

const PORUKA: Record<HintFailure, string> = {
  // Gumb se sakriva, pa se ova poruka u praksi ne prikazuje — postoji da grana
  // nikad ne ostane bez teksta ako se prikaz jednom promijeni.
  hints_disabled: "Savjeti nisu dostupni na ovom poslužitelju.",
  hint_not_unlocked:
    "Savjet se otključava tek nakon netočne predaje — predaj rješenje pa pokušaj ponovno.",
  hint_rate_limited: "Potrošio si sve savjete za sada.",
  hint_unavailable:
    "Savjet trenutno nije dostupan — pokušaj ponovno za koji trenutak.",
  hint_timeout: "Savjet nije stigao na vrijeme — pokušaj ponovno.",
  unknown: "Savjet nije dohvaćen — pokušaj ponovno.",
}

export function hintFailureText(reason: HintFailure): string {
  return PORUKA[reason]
}

/**
 * Nudi li se retry uz poruku.
 *
 * `hint_not_unlocked` NEMA retry: ponavljanje bez nove predaje daje isti 409, a
 * gumb koji ne može uspjeti je gori od nikakvog. `hints_disabled` nema retry jer
 * značajke nema.
 */
export function hintFailureRetryable(reason: HintFailure): boolean {
  return (
    reason === "hint_unavailable" ||
    reason === "hint_timeout" ||
    reason === "unknown"
  )
}

/** Odbrojavanje do `next_refill_at` — „za 3 h 12 min", „za 45 min", „uskoro". */
export function refillText(
  nextRefillAt: string | null | undefined,
  now: number,
): string | null {
  if (!nextRefillAt) return null
  const ms = Date.parse(nextRefillAt) - now
  if (Number.isNaN(ms)) return null
  if (ms <= 0) return "uskoro"
  const minute = Math.ceil(ms / 60_000)
  if (minute < 60) return `za ${minute} min`
  const sati = Math.floor(minute / 60)
  const ostatak = minute % 60
  return ostatak === 0 ? `za ${sati} h` : `za ${sati} h ${ostatak} min`
}

// ---------------------------------------------------------------------------
// Minimalni Markdown u tekstu savjeta (5.2 dopuna — NALAZ „doslovni Markdown")
// ---------------------------------------------------------------------------

/**
 * 🔴 POVOD: model vraća Markdown iako ga prompt ne traži, a slot ga je
 * prikazivao doslovno — student je čitao „konstrukt koji će **ograničiti broj
 * redaka**" sa zvjezdicama. Izmjereno 2026-08-13: 2 od 4 živa savjeta nose
 * `**` ili `` ` ``.
 *
 * 🔴 OPSEG JE NAMJERNO SITAN: samo `**podebljano**` i `` `kod` ``. Ovo NIJE
 * Markdown parser i ne smije to postati — savjet je jedna do dvije rečenice, a
 * puni parser (ili nova ovisnost) bio bi nerazmjeran i otvorio bi pitanje
 * sanitizacije teksta koji dolazi od modela.
 *
 * 🔴 FAIL-SAFE: nesparen `*` ili `` ` `` ostaje DOSLOVAN znak, kao i dosad.
 * Regex traži par; što ga nema, prolazi kroz `text` granu netaknuto. Gore od
 * zvjezdice u tekstu bila bi progutana rečenica.
 */
export type HintSegment = { kind: "text" | "bold" | "code"; value: string }

const MD = /\*\*([^*\n]+)\*\*|`([^`\n]+)`/g

/** Jedan odlomak → segmenti. Nikad ne gubi znakove: spoj `value`a vraća ulaz. */
export function hintSegments(text: string): HintSegment[] {
  const out: HintSegment[] = []
  let zadnji = 0
  for (const m of text.matchAll(MD)) {
    if (m.index > zadnji) {
      out.push({ kind: "text", value: text.slice(zadnji, m.index) })
    }
    out.push(
      m[1] !== undefined
        ? { kind: "bold", value: m[1] }
        : { kind: "code", value: m[2] },
    )
    zadnji = m.index + m[0].length
  }
  if (zadnji < text.length) {
    out.push({ kind: "text", value: text.slice(zadnji) })
  }
  return out
}

/**
 * Tekst savjeta → odlomci → segmenti.
 *
 * Prazan redak dijeli odlomke (model ih zna vratiti dva). Jednostruki prijelom
 * unutar odlomka postaje razmak — inače bi `white-space` morao biti `pre-line`,
 * pa bi i slučajni prijelom iz modela postao vidljiv prelom u sučelju.
 */
export function hintParagraphs(text: string): HintSegment[][] {
  return text
    .split(/\n\s*\n/)
    .map((odlomak) => odlomak.replace(/\s*\n\s*/g, " ").trim())
    .filter((odlomak) => odlomak.length > 0)
    .map(hintSegments)
}
