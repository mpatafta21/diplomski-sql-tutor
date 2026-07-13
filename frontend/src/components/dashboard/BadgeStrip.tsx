/**
 * BadgeStrip (Faza 4.2) — osvojeni bedževi + brojač kataloga.
 * earned = /profile.badges (codovi) × /badges (katalog; bez earned flaga —
 * join ovdje). `icon` iz kataloga je lucide ime (seed: compass/star/link/
 * ghost/fire) → statična mapa, Award fallback (nikad emoji — MASTER.md §7).
 * Puna galerija locked+unlocked je teren 4.4.
 */
import { BADGE_ICON, BADGE_ICON_FALLBACK } from "@/lib/badge-icons"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { BadgeCatalogItem } from "@/lib/api/types"

interface BadgeStripProps {
  catalog: BadgeCatalogItem[]
  earnedCodes: string[]
}

export function BadgeStrip({ catalog, earnedCodes }: BadgeStripProps) {
  const earnedSet = new Set(earnedCodes)
  const earned = catalog.filter((b) => earnedSet.has(b.code))

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Bedževi</CardTitle>
        <CardDescription>
          Osvojeno {earned.length} od {catalog.length}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {earned.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Još nijedan — prvi te čeka nakon prvog točno riješenog zadatka.
          </p>
        ) : (
          <ul className="flex flex-wrap gap-3">
            {earned.map((badge) => {
              const Icon = BADGE_ICON[badge.icon ?? ""] ?? BADGE_ICON_FALLBACK
              return (
                <li
                  key={badge.code}
                  className="flex items-center gap-2 rounded-lg border border-accent-warm/40 bg-accent-warm/10 px-3 py-2"
                  title={badge.description ?? undefined}
                >
                  <Icon
                    className="size-4 text-accent-warm-text"
                    aria-hidden="true"
                  />
                  <span className="text-sm font-medium">{badge.name}</span>
                </li>
              )
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
