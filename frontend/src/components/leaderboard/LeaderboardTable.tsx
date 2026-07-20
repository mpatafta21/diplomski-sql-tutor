/**
 * LeaderboardTable (Faza 4.5a) — tablica ljestvice.
 *
 * 🔴 `username`, NIKAD email. `/leaderboard` email uopće ne vraća (provjereno
 * živo u 4.5 KORAK 0: sken odgovora na "@"/"email" → 0 pogodaka) — ovdje se
 * dakle nema što ni procuriti, ali komponenta namjerno ne prima ni jedno polje
 * osim onih iz `LeaderboardItem`.
 *
 * A11Y (izmjereno 2026-07-19, poučak iz NALAZ #33 — tvrdnja nosi brojku):
 *  - prava `<table>` s `<caption>` i `scope="col"` na svim zaglavljima → rang je
 *    čitaču ekrana dostupan kao PODATAK (stupac "Mjesto"), ne kao vizualni
 *    redoslijed redaka;
 *  - trenutni korisnik NIJE označen samo bojom: nosi `aria-current="true"`,
 *    tekstualnu oznaku „(ti)" i ikonu — isti tro-kanalni obrazac kao verdict
 *    čipovi iz 4.3c (NALAZ #13).
 */
import { CircleUserRound } from "lucide-react"
import type { LeaderboardItem } from "@/lib/api/types"
import { cn } from "@/lib/utils"

interface LeaderboardTableProps {
  items: LeaderboardItem[]
  /** `username` trenutnog usera iz /me; null dok /me nije stigao. */
  currentUsername: string | null
  caption: string
}

export function LeaderboardTable({
  items,
  currentUsername,
  caption,
}: LeaderboardTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-border text-xs text-muted-foreground">
            <th scope="col" className="px-3 py-2 text-left font-medium">
              Mjesto
            </th>
            <th scope="col" className="px-3 py-2 text-left font-medium">
              Korisnik
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium">
              XP
            </th>
            <th scope="col" className="px-3 py-2 text-right font-medium">
              Razina
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const isMe =
              currentUsername !== null && item.username === currentUsername
            return (
              <tr
                key={item.username}
                // aria-current: čitač ekrana najavi redak kao "trenutni"
                aria-current={isMe ? "true" : undefined}
                className={cn(
                  "border-b border-border/60 last:border-0",
                  isMe && "bg-accent-warm/10",
                )}
              >
                <td className="px-3 py-2.5 tabular-nums text-muted-foreground">
                  {item.rank}.
                </td>
                <td className="px-3 py-2.5">
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5",
                      isMe && "font-semibold",
                    )}
                  >
                    {isMe && (
                      <CircleUserRound
                        className="size-4 shrink-0 text-accent-warm-text"
                        aria-hidden="true"
                      />
                    )}
                    {item.username}
                    {/* Tekstualni kanal — oznaka ne smije biti samo boja/ikona. */}
                    {isMe && (
                      <span className="text-xs font-normal text-accent-warm-text">
                        (ti)
                      </span>
                    )}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {item.xp}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums text-muted-foreground">
                  {item.level}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
