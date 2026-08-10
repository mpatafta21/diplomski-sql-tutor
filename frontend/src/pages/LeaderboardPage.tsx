/**
 * LeaderboardPage (Faza 4.5a) — ljestvica, global + weekly.
 *
 * 🔴 ISTICANJE TRENUTNOG USERA JE KLIJENTSKO: `/leaderboard` ga NE označava
 * (nema `is_current_user` ni `id` u `LeaderboardItem` — provjereno u KORAK 0).
 * Poklapanje ide preko `username` jer je to JEDINO zajedničko polje `/me` ×
 * `LeaderboardItem`, i jer `users.username` ima UNIQUE constraint u bazi
 * (provjereno: `users_username_key`) — dakle poklapanje ne može pogoditi krivog
 * korisnika. Poklapanje po `id` NIJE moguće: ljestvica ga ne vraća.
 *
 * 🔴 RANG SE NE IZMIŠLJA: ako user nije na dohvaćenoj stranici, envelope nema
 * „moj rank" polje, pa se prikazuje diskretna napomena — nikad izračunata
 * pozicija.
 *
 * 🔴 WEEKLY PROZOR: backend računa „zadnjih 7 dana, cutoff TZ-aware
 * (Europe/Zagreb)" (routes.py:614), ali granicu NE vraća u odgovoru. Zato
 * generički tekst — klijentski izračunat datum mogao bi promašiti backend
 * definiciju za sat ili dan i lagati korisniku (ista logika kao invarijanta
 * o backend konstantama: ne rekonstruiraju se na klijentu).
 */
import { useState } from "react"
import { Trophy } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Pagination } from "@/components/ui/pagination"
import { EmptyState } from "@/components/state/EmptyState"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import { LeaderboardTable } from "@/components/leaderboard/LeaderboardTable"
import { useAuth } from "@/hooks/useAuth"
import { useLeaderboard, type LeaderboardScope } from "@/hooks/useLeaderboard"
import { cn } from "@/lib/utils"

const PAGE_SIZE = 20

const SCOPE_META: Record<
  LeaderboardScope,
  { label: string; description: string }
> = {
  global: {
    label: "Ukupno",
    description: "Ukupan XP od početka — svi korisnici.",
  },
  weekly: {
    // Granica prozora NIJE u odgovoru → generički opis, nikad izračunat datum.
    description: "Osvojeni XP u tekućem tjednu (Europe/Zagreb).",
    label: "Ovaj tjedan",
  },
}

export function LeaderboardPage() {
  const [scope, setScope] = useState<LeaderboardScope>("global")
  const [offset, setOffset] = useState(0)
  const { user } = useAuth()
  const query = useLeaderboard({ scope, limit: PAGE_SIZE, offset })

  const switchScope = (next: LeaderboardScope) => {
    setScope(next)
    // Nova ljestvica → natrag na prvu stranicu (offset 12 na kratkoj weekly
    // listi dao bi praznu stranicu).
    setOffset(0)
  }

  const currentUsername = user?.username ?? null
  const items = query.data?.items ?? []
  const meOnPage =
    currentUsername !== null &&
    items.some((item) => item.username === currentUsername)

  return (
    // `stagger-cards` (B.2): entrance stagger direktne djece — v. index.css.
    <div className="stagger-cards mx-auto max-w-4xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Ljestvica</h1>
        <p className="text-sm text-muted-foreground">
          Usporedba napretka s ostalim korisnicima.
        </p>
      </div>

      <Card>
        <CardHeader className="gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-1">
              <CardTitle className="text-base">
                {SCOPE_META[scope].label}
              </CardTitle>
              <CardDescription>{SCOPE_META[scope].description}</CardDescription>
            </div>
            {/* Dva načina — aria-pressed je ovdje ISPRAVAN (toggle stanje,
                ne disclosure kao kod krivulja u 4.4b). */}
            <div
              role="group"
              aria-label="Razdoblje ljestvice"
              className="flex items-center gap-2"
            >
              {(Object.keys(SCOPE_META) as LeaderboardScope[]).map((key) => (
                <Button
                  key={key}
                  variant={scope === key ? "default" : "outline"}
                  aria-pressed={scope === key}
                  onClick={() => switchScope(key)}
                >
                  {SCOPE_META[key].label}
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {query.isPending && (
            <LoadingState lines={5} label="Učitavanje ljestvice" />
          )}

          {query.isError && (
            <ErrorState
              title="Ljestvica nije dostupna"
              message="Ne mogu dohvatiti ljestvicu — pokušaj ponovno."
              onRetry={() => void query.refetch()}
            />
          )}

          {query.isSuccess && query.data.total === 0 && (
            <EmptyState
              icon={Trophy}
              title={
                scope === "weekly"
                  ? "Ovaj tjedan još nema osvojenog XP-a"
                  : "Ljestvica je još prazna"
              }
              description="Čim netko riješi zadatak i osvoji XP, pojavit će se ovdje."
            />
          )}

          {query.isSuccess && query.data.total > 0 && (
            <>
              <div
                className={cn(
                  "transition-opacity duration-fast",
                  query.isPlaceholderData && "opacity-60",
                )}
                aria-busy={query.isFetching}
              >
                <LeaderboardTable
                  items={items}
                  currentUsername={currentUsername}
                  caption={`Ljestvica — ${SCOPE_META[scope].label}, mjesta ${
                    offset + 1
                  } do ${Math.min(offset + PAGE_SIZE, query.data.total)}`}
                />
              </div>

              {/* Rang se NE izmišlja — samo činjenica da nije na ovoj stranici. */}
              {!meOnPage && currentUsername !== null && (
                <p className="text-xs text-muted-foreground">
                  Nisi na ovoj stranici ljestvice.
                </p>
              )}

              <Pagination
                total={query.data.total}
                limit={PAGE_SIZE}
                offset={offset}
                onOffsetChange={setOffset}
                label="ljestvica"
              />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
