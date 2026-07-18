/**
 * BadgeGallery (Faza 4.4a) — PUNA galerija: osvojeni + zaključani bedževi.
 *
 * earned = /profile.badges (KODOVI) × /badges (katalog; join ovdje, bez earned
 * flaga u API-ju). Osvojeni idu prvi (slavlje), zaključani ispod (poziv na
 * akciju) — user bez ijednog bedža vidi PUNU zaključanu galeriju, ne prazan ekran.
 *
 * 🔴 IKONA: BADGE_ICON je keyed po `badge.icon` (lucide slug: compass/star/link/
 * ghost/fire), NE po `badge.code`. BADGE_ICON[badge.code] bi SVE srušio na Award
 * fallback (kodovi nisu ključevi mape). Ako ikad promijeniš na .code → galerija
 * postane 5× Award, tiho.
 * 🔴 BEZ DATUMA OSVAJANJA — API ne izlaže `earned_at` (badges je list[str]);
 * NE improvizirati datum ni iz čega (NALAZ #14). Zaključano/osvojeno stanje NE
 * nosi samo boja: ikona (Lock/Check) + tekstualna oznaka (NALAZ #13).
 */
import { Check, Lock } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { BADGE_ICON, BADGE_ICON_FALLBACK } from "@/lib/badge-icons"
import type { BadgeCatalogItem } from "@/lib/api/types"
import { cn } from "@/lib/utils"

interface BadgeGalleryProps {
  catalog: BadgeCatalogItem[]
  earnedCodes: string[]
}

export function BadgeGallery({ catalog, earnedCodes }: BadgeGalleryProps) {
  const earnedSet = new Set(earnedCodes)
  // Osvojeni prvi, zatim zaključani; unutar grupa zadržan redoslijed kataloga.
  const ordered = [...catalog].sort(
    (a, b) => Number(earnedSet.has(b.code)) - Number(earnedSet.has(a.code)),
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Bedževi</CardTitle>
        <CardDescription>
          Osvojeno <span className="tabular-nums">{earnedSet.size}</span> od{" "}
          <span className="tabular-nums">{catalog.length}</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {ordered.map((badge, i) => {
            const earned = earnedSet.has(badge.code)
            // keyed po `badge.icon` (lucide slug), NIKAD po `badge.code`.
            const Icon = BADGE_ICON[badge.icon ?? ""] ?? BADGE_ICON_FALLBACK
            return (
              <li
                key={badge.code}
                className={cn(
                  "flex gap-3 rounded-lg border p-3 duration-base ease-entrance animate-in fade-in fill-mode-backwards motion-reduce:animate-none",
                  earned
                    ? "border-accent-warm/40 bg-accent-warm/10"
                    : "border-border bg-muted/30",
                )}
                // Suptilni stagger na mount (occasional ekran) — samo fade,
                // reduced-motion ga gasi kroz motion-reduce guard.
                style={{ animationDelay: `${i * 40}ms` }}
              >
                <div
                  className={cn(
                    "flex size-10 shrink-0 items-center justify-center rounded-lg",
                    earned
                      ? "bg-accent-warm/20 text-accent-warm-text"
                      : "bg-muted text-muted-foreground",
                  )}
                >
                  <Icon
                    className={cn("size-5", !earned && "opacity-60")}
                    aria-hidden="true"
                  />
                </div>
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <h3
                      className={cn(
                        "truncate text-sm font-semibold",
                        !earned && "text-muted-foreground",
                      )}
                    >
                      {badge.name}
                    </h3>
                    {/* stanje NE nosi samo boja: ikona + tekst */}
                    <span
                      className={cn(
                        "inline-flex shrink-0 items-center gap-1 rounded-full px-1.5 py-0.5 text-[0.65rem] font-medium",
                        earned
                          ? "bg-accent-warm/20 text-accent-warm-text"
                          : "bg-muted text-muted-foreground",
                      )}
                    >
                      {earned ? (
                        <>
                          <Check className="size-3" aria-hidden="true" />
                          Osvojeno
                        </>
                      ) : (
                        <>
                          <Lock className="size-3" aria-hidden="true" />
                          Zaključano
                        </>
                      )}
                    </span>
                  </div>
                  {/* description JE kriterij osvajanja (provjereno u katalogu) */}
                  {badge.description && (
                    <p className="text-xs leading-relaxed text-muted-foreground">
                      {badge.description}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground tabular-nums">
                    Nagrada: {badge.xp_reward} XP
                  </p>
                </div>
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}
