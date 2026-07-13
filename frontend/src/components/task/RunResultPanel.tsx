/**
 * RunResultPanel (Faza 4.3b) — izlaz POST /run ispod editora (konzola, ne ocjena).
 *
 * 🔴 Ugovorne nijanse (živi spec 4.3 KORAK 0):
 * - `columns` ARRAY je AUTORITET za redoslijed i broj stupaca — rows su dictovi
 *   pa se ćelija čita `row[col]`, NIKAD Object.keys(row).
 *   ⚠️ Poznati limit ugovora: duplikat imena s RAZLIČITIM vrijednostima
 *   (SELECT o.id, c.id ...) backend kolabira u dictu (zadnji pobjeđuje) —
 *   klijentski NENADOKNADIVO, pa tablica uz duplikate prikazuje caveat
 *   (preporuka AS aliasa). Pravi fix = contract promjena (rows kao arrayevi).
 * - `error` je NORMALAN ishod (HTTP 200) — sirovi PG string s "LINE n" + caret
 *   koji se poklapa s Monaco linijama → mono blok, whitespace-pre. NIJE ocjena
 *   ("netočno") nego izvršna greška ("upit nije prošao").
 * - 0 redaka bez errora = legitiman rezultat, ne greška.
 * - NIKAKAV verdict/checkmark na Run rezultatu — usporedba s očekivanim ne
 *   postoji ovdje (to je /attempt, 4.3c).
 */
import { memo } from "react"
import { Terminal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Kbd } from "@/components/ui/kbd"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import type { RunResponse } from "@/lib/api/types"
import { cn } from "@/lib/utils"

/** Cap renderanih redaka — čuva UI od smrzavanja na velikim rezultatima
 *  (backend rows nisu paginirani); ostatak je vidljiv kroz notu ispod tablice. */
const MAX_RENDERED_ROWS = 200

/** Hrvatski plural za "redak", nominativ (1 redak · 2–4 retka · 5+ redaka). */
function rowNoun(n: number): string {
  const d = n % 10
  const dd = n % 100
  if (d === 1 && dd !== 11) return "redak"
  if (d >= 2 && d <= 4 && (dd < 12 || dd > 14)) return "retka"
  return "redaka"
}

/** Genitiv iza "od" ("od 201 retka" — nominativ bi bio gramatički kriv). */
function rowNounGenitive(n: number): string {
  const d = n % 10
  const dd = n % 100
  if (d >= 1 && d <= 4 && (dd < 11 || dd > 14)) return "retka"
  return "redaka"
}

function CellValue({ value }: { value: unknown }) {
  if (value === null || value === undefined) {
    // NULL mora biti VIDLJIV (≠ prazan string) — studentu je razlika gradivo.
    return <span className="italic text-muted-foreground">NULL</span>
  }
  if (typeof value === "boolean") return <>{value ? "true" : "false"}</>
  if (typeof value === "object") return <>{JSON.stringify(value)}</>
  return <>{String(value)}</>
}

interface RunResultPanelProps {
  /** Zadnji USPJEŠNI /run odgovor; undefined prije prvog uspjeha. */
  result: RunResponse | undefined
  isPending: boolean
  /** Infra kvar mutationa (401/5xx/mreža) — NE SQL greška (ona je u result.error). */
  infraError: boolean
  /** Ponovi ZADNJI POSLANI upit (stabilan identitet — memo se oslanja na to). */
  onRetry: () => void
  /** Vizualni hint prečaca (platform-aware, iz TaskPage-a). */
  runKbd: string
}

export const RunResultPanel = memo(function RunResultPanel({
  result,
  isPending,
  infraError,
  onRetry,
  runKbd,
}: RunResultPanelProps) {
  return (
    <section aria-label="Rezultat upita" aria-busy={isPending}>
      {isPending && result === undefined ? (
        // Skeleton SAMO za prvi Run — na re-run se zadržava stari rezultat
        // (dim) da frekventna akcija ne bljeska skeletonom (review-animations).
        <LoadingState
          lines={2}
          label="Izvršavanje upita"
          className="rounded-md border border-border p-3"
        />
      ) : !isPending && infraError && result === undefined ? (
        <ErrorState
          title="Upit nije poslan"
          message="Veza prema poslužitelju nije uspjela — rezultat nije stigao."
          onRetry={onRetry}
        />
      ) : result === undefined ? (
        <div className="flex items-center gap-2 rounded-md border border-dashed border-border px-3 py-4 text-sm text-muted-foreground">
          <Terminal aria-hidden="true" className="size-4 shrink-0" />
          <span>
            Pokreni upit da vidiš rezultat — <Kbd>{runKbd}</Kbd>
          </span>
        </div>
      ) : (
        // Jedan dim-wrapper za SVE rezultat grane (bez triplikata) + tranzicija
        // umjesto instant snapa (MASTER §8), uz reduced-motion guard.
        <div
          className={cn(
            "transition-opacity duration-fast ease-standard motion-reduce:transition-none",
            isPending && "opacity-60",
          )}
        >
          {!isPending && infraError && (
            // Infra kvar na RE-runu: stari rezultat OSTAJE vidljiv (isti
            // razlog kao stale-dim) — banner umjesto punog ErrorStatea.
            <div
              role="alert"
              className="mb-2 flex flex-wrap items-center justify-between gap-2 rounded-md border border-incorrect/40 bg-incorrect-soft px-3 py-2 text-xs"
            >
              <span>
                Ponovno pokretanje nije uspjelo — prikazan je prethodni
                rezultat.
              </span>
              <Button variant="outline" size="sm" onClick={onRetry}>
                Pokušaj ponovno
              </Button>
            </div>
          )}
          {result.error != null ? (
            // Izvršna greška — NE ocjena. Sirovi PG string (LINE/caret ↔ Monaco linije).
            <div className="rounded-md border border-incorrect/40 bg-incorrect-soft p-3">
              <p className="mb-2 text-sm font-medium">
                Upit nije prošao{" "}
                <span className="font-normal text-muted-foreground tabular-nums">
                  · {result.exec_ms} ms
                </span>
              </p>
              <pre className="overflow-x-auto font-mono text-xs leading-relaxed whitespace-pre">
                {result.error}
              </pre>
            </div>
          ) : result.rows.length === 0 ? (
            // 0 redaka BEZ errora = legitiman rezultat (ne greška, ne "netočno").
            <div className="rounded-md border border-border px-3 py-4 text-sm text-muted-foreground">
              Upit nije vratio nijedan redak{" "}
              <span className="tabular-nums">· {result.exec_ms} ms</span>
            </div>
          ) : (
            <ResultTable result={result} />
          )}
        </div>
      )}
    </section>
  )
})

// memo: result referenca se mijenja samo na novi uspješan Run — tablica (do
// 200 redaka) se NE rekoncilira dok student tipka u editoru.
const ResultTable = memo(function ResultTable({
  result,
}: {
  result: RunResponse
}) {
  const total = result.rows.length
  const rendered = result.rows.slice(0, MAX_RENDERED_ROWS)
  const hasDuplicateColumns =
    new Set(result.columns).size < result.columns.length

  return (
    <div className="space-y-1.5">
      <p className="text-xs text-muted-foreground tabular-nums">
        {total} {rowNoun(total)} · {result.exec_ms} ms
      </p>
      {hasDuplicateColumns && (
        // ⚠️ Ugovorni limit (header datoteke): duplikat imena → backend dict
        // čuva samo zadnju vrijednost; sve duplikat-ćelije prikazuju NJU.
        <p className="rounded-md border border-border bg-muted px-3 py-2 text-xs text-muted-foreground">
          Neki stupci dijele isto ime pa prikazane vrijednosti mogu biti netočne
          za duplikate — dodaj <code className="font-mono">AS</code> alias za
          točan prikaz.
        </p>
      )}
      <div className="max-h-80 overflow-auto rounded-md border border-border">
        {/* border-separate: uz border-collapse sticky th "ostavlja" donji rub
            pri scrollu (collapsed borderi ne putuju sa sticky ćelijama). */}
        <table className="w-full border-separate border-spacing-0 font-mono text-xs">
          <caption className="sr-only">Rezultat SQL upita</caption>
          <thead className="sticky top-0 bg-card">
            <tr>
              {/* columns je autoritet: duplikat imena → dva stupca (key po indexu). */}
              {result.columns.map((col, i) => (
                <th
                  key={`${col}-${i}`}
                  scope="col"
                  className="border-b border-border px-3 py-2 text-left font-semibold"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rendered.map((row, ri) => (
              <tr key={ri} className={cn(ri % 2 === 1 && "bg-muted/40")}>
                {result.columns.map((col, ci) => (
                  <td
                    key={`${col}-${ci}`}
                    className="px-3 py-1.5 align-top whitespace-nowrap"
                  >
                    <CellValue value={row[col]} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {total > MAX_RENDERED_ROWS && (
        <p className="text-xs text-muted-foreground tabular-nums">
          Prikazano prvih {MAX_RENDERED_ROWS} od {total}{" "}
          {rowNounGenitive(total)}.
        </p>
      )}
    </div>
  )
})
