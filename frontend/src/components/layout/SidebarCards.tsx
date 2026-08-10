/**
 * Kartice na dnu sidebara (Faza 4.7-1C, t.2) — level/streak i korisnik.
 *
 * 🔴 LEVEL KARTICA NAMJERNO NE PRIKAZUJE XP. Invarijanta (`ProfilePage.tsx:7-8`,
 * `StatsSummary.tsx:8-10`): „hero (`ProgressHero`) je JEDINO mjesto s XP-om …
 * dvije XP brojke na ekranu = bug". Sidebar je PERSISTENTAN, pa bi na Dashboardu i
 * Profilu — gdje `ProgressHero` već stoji — dao dvije XP brojke u istom kadru.
 * Zato: level + streak, bez XP brojke i bez XP bara. Varijanta (C) iz 1C t.2.
 *
 * 🔴 `accent-warm` JE DOPUŠTEN OVDJE. MASTER §2.1 ga rezervira za „XP, level, streak,
 * badge, progres" — level i streak su doslovno na tom popisu. NE „popravljati" po
 * ERRATA #53: #53 se tiče mjesta koja NISU gamifikacija (brand mark, poruke o limitu).
 */
import { Flame } from "lucide-react"
import { LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"
import { useProfile } from "@/hooks/useProfile"
import { cn } from "@/lib/utils"

/**
 * Level + streak. Podaci iz `/profile` — BEZ novog poziva: `useProfile` dijeli
 * `queryKey: ["profile"]` s Dashboardom i Profilom, pa TanStack servira isti cache.
 *
 * ⚠️ POSLJEDICA KOJU TREBA ZNATI: ovo je PRVI trajni observer nad `["profile"]`.
 * `useSubmitAttempt.ts:34-48` ima `setQueryData` patch uz komentar „na /task ruti nema
 * aktivnog profile observera pa invalidacija samo označi stale". Od sada observer
 * POSTOJI, pa `invalidateQueries(["profile"])` (`:49`) i stvarno refetcha. Patch time
 * ne postaje suvišan — on je i dalje ono što karticu osvježi ODMAH, prije mrežnog
 * odgovora. Neto: jedan `GET /profile` više po Submitu, i svježiji podatak.
 */
export function SidebarLevelCard() {
  const { data, isPending } = useProfile()

  if (isPending) {
    return (
      <div className="rounded-lg border border-sidebar-border p-3">
        <Skeleton className="h-9 w-full" />
      </div>
    )
  }
  if (!data) return null

  return (
    <div className="flex items-center gap-3 rounded-lg border border-sidebar-border p-3">
      <div className="flex min-w-0 flex-col">
        <span className="font-mono text-xs text-muted-foreground">level</span>
        {/* Display font — isto pravilo kao hero numeral (MASTER §3.1). */}
        <span className="font-heading text-2xl leading-none font-semibold text-accent-warm-text tabular-nums">
          {data.level}
        </span>
      </div>
      <div className="ml-auto flex flex-col items-end">
        <span className="font-mono text-xs text-muted-foreground">streak</span>
        <span className="flex items-center gap-1">
          {/* lucide, NE emoji: emoji čitač ekrana izgovara imenom, a set nam je
              zaključan na lucide (MASTER §6). */}
          <Flame
            className={cn(
              "size-3.5",
              data.current_streak > 0
                ? "text-accent-warm-text"
                : "text-muted-foreground",
            )}
            aria-hidden="true"
          />
          <span className="text-sm leading-none font-semibold tabular-nums">
            {data.current_streak}
          </span>
          <span className="sr-only">
            {data.current_streak === 1 ? "dan zaredom" : "dana zaredom"}
          </span>
        </span>
      </div>
    </div>
  )
}

/**
 * Korisnik + odjava. JEDNA komponenta za sidebar I drawer — da se rola-badge i
 * ponašanje odjave ne raziđu između dva mjesta.
 * `onAction` koristi samo drawer (zatvori nakon klika).
 */
export function SidebarUserCard({ onAction }: { onAction?: () => void } = {}) {
  const { user, logout } = useAuth()
  if (!user) return null

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 px-1">
        <span className="min-w-0 truncate text-sm font-medium">
          {user.username}
        </span>
        <span
          className={cn(
            "shrink-0 rounded-full px-2 py-0.5 font-mono text-xs font-medium",
            user.role === "admin"
              ? "bg-accent-warm text-accent-warm-foreground"
              : "bg-muted text-muted-foreground",
          )}
        >
          {user.role}
        </span>
      </div>
      <Button
        variant="outline"
        className="w-full"
        onClick={() => {
          onAction?.()
          logout()
        }}
      >
        <LogOut data-icon="inline-start" />
        Odjava
      </Button>
    </div>
  )
}
