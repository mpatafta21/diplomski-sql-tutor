/**
 * ProgressHero (Faza 4.2) — level + XP progres + streak. Amber accent je
 * REZERVIRAN za gamifikaciju (MASTER.md §2.1) — ovdje je doma.
 * XP progres: ISKLJUČIVO xp_in_level/level_step/xp_to_next iz /profile
 * (invarijanta #6 — nula lokalnih konstanti).
 */
import { Flame } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { MasteryBar } from "@/components/MasteryBar"
import type { ProfileResponse } from "@/lib/api/types"

interface ProgressHeroProps {
  profile: ProfileResponse
}

export function ProgressHero({ profile }: ProgressHeroProps) {
  const { xp, level, xp_in_level, xp_to_next, level_step } = profile

  return (
    <Card>
      <CardContent className="grid gap-6 sm:grid-cols-[auto_1fr_auto] sm:items-center">
        <div className="flex items-baseline gap-2 sm:flex-col sm:gap-0">
          <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Level
          </span>
          <span className="text-4xl font-semibold tracking-tight text-accent-warm-text tabular-nums">
            {level}
          </span>
        </div>

        <div className="space-y-2">
          <div className="flex items-baseline justify-between gap-2">
            <span className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground tabular-nums">
                {xp_in_level}
              </span>
              {" / "}
              <span className="tabular-nums">{level_step}</span> XP u levelu
            </span>
            <span className="text-xs text-muted-foreground tabular-nums">
              još {xp_to_next} XP do levela {level + 1}
            </span>
          </div>
          <MasteryBar
            value={xp_in_level / level_step}
            fillClass="bg-accent-warm"
            label={`XP napredak: ${xp_in_level} od ${level_step} u trenutnom levelu`}
          />
          <p className="text-xs text-muted-foreground">
            Ukupno <span className="tabular-nums">{xp}</span> XP
          </p>
        </div>

        <div className="flex items-center gap-3 sm:flex-col sm:items-end sm:gap-0">
          <span className="flex items-center gap-1.5 text-xs font-medium tracking-wide text-muted-foreground uppercase">
            <Flame
              className={
                profile.current_streak > 0
                  ? "size-3.5 text-accent-warm-text"
                  : "size-3.5"
              }
              aria-hidden="true"
            />
            Streak
          </span>
          <span className="text-4xl font-semibold tracking-tight tabular-nums">
            {profile.current_streak}
          </span>
          <span className="text-xs text-muted-foreground tabular-nums">
            najduži: {profile.longest_streak}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
