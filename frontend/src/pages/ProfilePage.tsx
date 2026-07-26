/**
 * ProfilePage (Faza 4.4a + 4.4b) — profil: XP/level hero, statistika, galerija
 * bedževa, BKT krivulje znanja, povijest pokušaja.
 * Lazy-loadan (router) → recharts (4.4b) živi u OVOM chunku, ne u glavnom
 * bundleu (dokazano vite build outputom). Svi podaci sa živih ruta (nula mocka).
 *
 * XP JE JEDNOZNAČAN: hero (ProgressHero) je JEDINO mjesto s XP-om, iz /profile
 * (autoritativno). StatsSummary NE prikazuje XP (vidi njegov docstring).
 */
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { LoadingState } from "@/components/state/LoadingState"
import { ErrorState } from "@/components/state/ErrorState"
import { ProgressHero } from "@/components/dashboard/ProgressHero"
import { StatsSummary } from "@/components/profile/StatsSummary"
import { BadgeGallery } from "@/components/profile/BadgeGallery"
import { AttemptHistory } from "@/components/profile/AttemptHistory"
import { MasteryCurves } from "@/components/profile/MasteryCurves"
import { ParticipationSection } from "@/components/profile/ParticipationSection"
import { useAuth } from "@/hooks/useAuth"
import { useProfile } from "@/hooks/useProfile"
import { useBadges } from "@/hooks/useBadges"

export function ProfilePage() {
  const { user } = useAuth()
  const profile = useProfile()
  const badges = useBadges()

  if (profile.isPending) {
    return (
      <div className="mx-auto max-w-5xl space-y-6">
        <LoadingState lines={2} label="Učitavanje profila" />
        <Card aria-hidden="true">
          <CardContent>
            <LoadingState lines={3} label="" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (profile.isError) {
    return (
      <div className="mx-auto max-w-5xl">
        <ErrorState
          title="Profil nije dostupan"
          message="Ne mogu dohvatiti tvoj profil — pokušaj ponovno."
          onRetry={() => void profile.refetch()}
        />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Profil</h1>
        <p className="text-sm text-muted-foreground">
          {user?.username
            ? `Napredak, bedževi i povijest — ${user.username}`
            : "Napredak, bedževi i povijest."}
        </p>
      </div>

      {/* Jedini izvor XP-a na ekranu (autoritativno /profile). */}
      <ProgressHero profile={profile.data} />

      <StatsSummary />

      {badges.isPending && (
        <Card aria-busy="true">
          <CardContent>
            <LoadingState lines={2} label="Učitavanje bedževa" />
          </CardContent>
        </Card>
      )}
      {badges.isSuccess && (
        <BadgeGallery catalog={badges.data} earnedCodes={profile.data.badges} />
      )}
      {badges.isError && (
        <ErrorState
          title="Bedževi nisu dostupni"
          onRetry={() => void badges.refetch()}
        />
      )}

      {/* mastery_threshold putuje iz /profile — komponenta ga NE hardkodira. */}
      <MasteryCurves masteryThreshold={profile.data.mastery_threshold} />

      {/* Anchor cilj za linkove na pokušaj iz tooltipa/tablice krivulje.
          scroll-mt drži naslov ispod sticky headera nakon skoka. */}
      <div id="povijest" className="scroll-mt-20">
        <AttemptHistory />
      </div>

      {/* Separator je OBAVEZAN, ne ukras: bez njega sadržaj iza kontrole
          paginacije povijesti čita se kao njezin rep, a ne kao zaseban blok. */}
      <Separator />

      {/* Informacija o sudjelovanju — prijavljeni korisnik do nje inače NEMA
          puta (PublicOnlyRoute ga s /register vraća na /). Zadnja je namjerno:
          referentni sadržaj, ne dnevni. `username` dolazi iz `useAuth` gore —
          bez novog querya. */}
      <div id="sudjelovanje" className="scroll-mt-20">
        <ParticipationSection username={user?.username} />
      </div>
    </div>
  )
}
