/**
 * AttemptHistory (Faza 4.4a) — paginirana povijest pokušaja.
 *
 * Vlastiti query (useAttempts, limit=20) + offset state. `total` iz envelope
 * (Page: {items,total,limit,offset} — NEMA page/size). BEZ filter kontrola:
 * server-side filtera nema, a client-side filter nad JEDNOM stranicom lagao bi
 * da filtrira cijelu povijest (NALAZ #15). Prazan user → EmptyState s CTA.
 */
import { useState } from "react"
import { ClipboardList } from "lucide-react"
import { Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Pagination } from "@/components/ui/pagination"
import { EmptyState } from "@/components/state/EmptyState"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import { AttemptRow } from "@/components/profile/AttemptRow"
import { useAttempts } from "@/hooks/useAttempts"
import { cn } from "@/lib/utils"

const PAGE_SIZE = 20

export function AttemptHistory() {
  const [offset, setOffset] = useState(0)
  const query = useAttempts({ limit: PAGE_SIZE, offset })

  if (query.isPending) {
    return (
      <Card aria-busy="true">
        <CardHeader>
          <CardTitle className="text-base">Povijest pokušaja</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingState lines={4} label="Učitavanje povijesti" />
        </CardContent>
      </Card>
    )
  }

  if (query.isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Povijest pokušaja</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorState
            title="Povijest nije dostupna"
            message="Ne mogu dohvatiti tvoje pokušaje — pokušaj ponovno."
            onRetry={() => void query.refetch()}
          />
        </CardContent>
      </Card>
    )
  }

  const { items, total } = query.data

  if (total === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Povijest pokušaja</CardTitle>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={ClipboardList}
            title="Još nema pokušaja"
            description="Kad riješiš prvi zadatak, ovdje se gradi tvoja povijest — svaki upit, ocjena i osvojeni XP."
            action={
              <Button asChild>
                <Link to="/">Riješi prvi zadatak</Link>
              </Button>
            }
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Povijest pokušaja</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <ul
          className={cn(
            "space-y-2 transition-opacity duration-fast ease-standard",
            // keepPreviousData: pri prelasku stranice suptilno zatamni stare retke
            query.isPlaceholderData && "opacity-60",
          )}
          aria-busy={query.isFetching}
        >
          {items.map((attempt) => (
            <AttemptRow key={attempt.id} attempt={attempt} />
          ))}
        </ul>

        <Pagination
          total={total}
          limit={PAGE_SIZE}
          offset={offset}
          onOffsetChange={setOffset}
          label="povijest pokušaja"
        />
      </CardContent>
    </Card>
  )
}
