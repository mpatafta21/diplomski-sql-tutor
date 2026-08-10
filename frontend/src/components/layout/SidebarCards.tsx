/**
 * Kartice chromea — level (sidebar footer), streak čip i user kartica (topbar),
 * te user kartica za drawer.
 *
 * ⟳ A.3 (2026-08-10) — OBRAT ODLUKE 1C t.2, zabilježen u nalazi.md (N-17):
 * user kartica (username, rola, odjava) SELI iz sidebar footera u topbar, a
 * streak SELI iz sidebar level kartice u topbar čip koji postaje vidljiv na
 * SVIM širinama. To je PREMJEŠTANJE, ne dodavanje — svaka brojka i dalje
 * postoji točno jednom po kadru (`docs/invarijante.md#jedan-prikaz-po-kadru`).
 *
 * 🔴 LEVEL KARTICA NAMJERNO NE PRIKAZUJE XP. Invarijanta (`ProfilePage.tsx:7-8`,
 * `StatsSummary.tsx:8-10`): „hero (`ProgressHero`) je JEDINO mjesto s XP-om …
 * dvije XP brojke na ekranu = bug". Sidebar je PERSISTENTAN, pa bi na Dashboardu
 * i Profilu — gdje `ProgressHero` već stoji — dao dvije XP brojke u istom kadru.
 * XP čip u topbar NE ide iz istog razloga.
 *
 * 🔴 `accent-warm` JE DOPUŠTEN OVDJE. MASTER §2.1 ga rezervira za „XP, level,
 * streak, badge, progres" — level i streak su doslovno na tom popisu. NE
 * „popravljati" po ERRATA #53: #53 se tiče mjesta koja NISU gamifikacija.
 */
import { Flame } from "lucide-react"
import { LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"
import { useProfile } from "@/hooks/useProfile"
import { cn } from "@/lib/utils"

/**
 * Level — podaci iz `/profile` — BEZ novog poziva: `useProfile` dijeli
 * `queryKey: ["profile"]` s Dashboardom i Profilom, pa TanStack servira isti
 * cache.
 *
 * ⚠️ POSLJEDICA KOJU TREBA ZNATI: ovo je PRVI trajni observer nad `["profile"]`.
 * `useSubmitAttempt.ts:34-48` ima `setQueryData` patch uz komentar „na /task ruti
 * nema aktivnog profile observera pa invalidacija samo označi stale". Od 1C
 * observer POSTOJI, pa `invalidateQueries(["profile"])` (`:49`) i stvarno
 * refetcha. Patch time ne postaje suvišan — on je i dalje ono što karticu
 * osvježi ODMAH, prije mrežnog odgovora. Neto: jedan `GET /profile` više po
 * Submitu, i svježiji podatak.
 *
 * ⟳ A.3: streak je iseljen u `TopbarStreakChip` (vidljiv na svim širinama) —
 * da je ostao i ovdje, na ≥768px bile bi DVIJE streak brojke u istom kadru.
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
    </div>
  )
}

/**
 * Streak čip u topbaru — od A.3 vidljiv na SVIM širinama.
 *
 * ⟳ OBRAT 1C t.2 (bio `md:hidden`): dotad je na desktopu streak živio u sidebar
 * level kartici, pa bi čip u topbaru dao dvije iste brojke u kadru. A.3 je
 * streak IZ level kartice uklonio — čip je sada JEDINO mjesto sa streakom, na
 * svakoj širini, i uvijek u kadru (istaknutost povratne sprege, stup 4.6).
 *
 * 🔴 XP ČIPA NEMA, ni na jednoj širini. XP je pod invarijantom jednoznačnosti
 * (`ProfilePage.tsx:7-8`) — `ProgressHero` je jedino mjesto s XP-om.
 *
 * `accent-warm` je dopušten po §2.1 (streak je na popisu). Ne „popravljati" po #53.
 */
export function TopbarStreakChip() {
  const { data } = useProfile()
  if (!data) return null

  return (
    <span
      className="flex items-center gap-1.5 rounded-full border border-border px-2.5 py-1"
      title={`Streak: ${data.current_streak} ${data.current_streak === 1 ? "dan" : "dana"} zaredom`}
    >
      <Flame
        className={cn(
          "size-3.5",
          data.current_streak > 0
            ? "text-accent-warm-text"
            : "text-muted-foreground",
        )}
        aria-hidden="true"
      />
      <span className="text-xs font-medium tabular-nums">
        {data.current_streak}
      </span>
      <span className="sr-only">
        {data.current_streak === 1 ? "dan zaredom" : "dana zaredom"}
      </span>
    </span>
  )
}

/**
 * Rola badge — JEDAN izvor za topbar i drawer varijantu user kartice, da se
 * boje/oblik ne raziđu (ista briga zbog koje je 1C držao jednu komponentu).
 */
function RoleBadge({ role }: { role: string }) {
  return (
    <span
      className={cn(
        "shrink-0 rounded-full px-2 py-0.5 font-mono text-xs font-medium",
        role === "admin"
          ? "bg-accent-warm text-accent-warm-foreground"
          : "bg-muted text-muted-foreground",
      )}
    >
      {role}
    </span>
  )
}

/**
 * User kartica u topbaru (A.3) — ≥768px. Ispod 768px je skrivena: ondje
 * username/rolu/odjavu nosi drawer (`DrawerUserCard`), jer je topbar pretijesan.
 * Odjava je dostupna na SVAKOM breakpointu: topbar ≥768 · drawer <768.
 */
export function TopbarUserCard() {
  const { user, logout } = useAuth()
  if (!user) return null

  return (
    <div className="hidden min-w-0 items-center gap-2 md:flex">
      <span className="max-w-40 min-w-0 truncate text-sm font-medium">
        {user.username}
      </span>
      <RoleBadge role={user.role} />
      <Button variant="outline" onClick={logout}>
        <LogOut data-icon="inline-start" />
        Odjava
      </Button>
    </div>
  )
}

/**
 * User kartica za DRAWER (<768px) — do A.3 živjela i u sidebar footeru pod
 * imenom `SidebarUserCard`; sidebar ju je predao topbaru, drawer je zadržava
 * jer na telefonu topbar nema mjesta (v. AppShell `MobileNav`).
 * `onAction` zatvara drawer nakon klika.
 */
export function DrawerUserCard({ onAction }: { onAction?: () => void } = {}) {
  const { user, logout } = useAuth()
  if (!user) return null

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 px-1">
        <span className="min-w-0 truncate text-sm font-medium">
          {user.username}
        </span>
        <RoleBadge role={user.role} />
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
