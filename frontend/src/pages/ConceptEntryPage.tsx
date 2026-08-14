/**
 * ConceptEntryPage — ulaz u zadatak preko KONCEPTA (`/koncept/:code`).
 *
 * Kartica „Za ojačati" (Dashboard) i redak koncepta (Moduli) prije su linkali
 * izravno na `/task/${entry_task_id}`, a to je polje bilo statično i bez korisničkog
 * konteksta — vodilo je na već riješen zadatak. Sada linkaju ovamo, a zadatak
 * bira poslužitelj (`resolve_task_for_concept`), koji jedini zna što je riješeno.
 *
 * Ista mehanika kao TaskEntryPage (`/task`), samo s drugim izvorom.
 *
 * 🔴 `replace`: entry ruta NE smije ostati u historyju — inače bi Back s task
 * screena opet pao ovamo, ponovno razriješio koncept i vratio na isti zadatak
 * (zamka beskonačnog vraćanja, dokumentirana u TaskEntryPage).
 */
import { Link, Navigate, useParams } from "react-router-dom"
import { CircleSlash2 } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingState } from "@/components/state/LoadingState"
import { ErrorState } from "@/components/state/ErrorState"
import { ApiError } from "@/lib/api/query"
import { useTaskForConcept } from "@/hooks/useTaskForConcept"

export function ConceptEntryPage() {
  const { code } = useParams<{ code: string }>()
  const query = useTaskForConcept(code)

  // 🔴 Bez `code` upit je `enabled: false`, a onemogućen TanStack upit ostaje
  // `isPending` ZAUVIJEK — spinner bez izlaza. Danas se ne može dogoditi (ruta je
  // `/koncept/:code`, pa parametar uvijek postoji), ali refaktor rutera ili novo
  // pozivno mjesto to tiho mijenjaju, a simptom bi bio ekran koji se vrti bez
  // greške u konzoli. Zato eksplicitna grana prije provjere `isPending`.
  if (!code) {
    return (
      <div className="mx-auto max-w-2xl">
        <ErrorState
          title="Koncept nije naveden"
          message="Ova adresa treba kod koncepta. Odaberi koncept u Modulima."
        />
      </div>
    )
  }

  if (query.isPending) {
    return <LoadingState label="Tražim zadatak za taj koncept" />
  }

  // 404 je OČEKIVAN ishod, ne kvar: koncept ne postoji ili nema vježbivih
  // zadataka (transverzalni, deaktivirani M6). Retry ondje ne bi pomogao, pa
  // se nudi izlaz umjesto gumba koji ponavlja isti odgovor.
  const notFound = query.error instanceof ApiError && query.error.status === 404

  if (query.isError && !notFound) {
    return (
      <div className="mx-auto max-w-2xl">
        <ErrorState
          title="Zadatak nije dostupan"
          message="Ne mogu dohvatiti zadatak za taj koncept — pokušaj ponovno."
          onRetry={() => void query.refetch()}
        />
      </div>
    )
  }

  if (!notFound && query.data) {
    return <Navigate to={`/task/${query.data.task_id}`} replace />
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardContent className="flex flex-col items-center gap-4 py-10 text-center">
          <div className="flex size-12 shrink-0 items-center justify-center rounded-full border border-border bg-muted">
            <CircleSlash2
              className="size-6 text-muted-foreground"
              aria-hidden="true"
            />
          </div>
          <div className="space-y-1">
            <h1 className="text-lg font-semibold">
              Nema zadataka za taj koncept
            </h1>
            <p className="text-sm text-muted-foreground">
              Ovaj koncept se uvježbava kroz druge zadatke — otvori Module i
              odaberi neki od njih.
            </p>
          </div>
          <Button asChild variant="outline">
            <Link to="/modules">Natrag na Module</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
