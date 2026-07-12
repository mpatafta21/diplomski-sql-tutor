/**
 * DashboardPage (Faza 4.2a) — composite: hero progres, "Nastavi ovdje" CTA,
 * mastery highlights, bedževi. Svi podaci sa živih ruta (nula mocka);
 * loading=skeleton / error=oporavljiv / empty=dizajniran onboarding (§3.4).
 */
import { Award, TrendingUp, Terminal } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { LoadingState } from "@/components/state/LoadingState"
import { ErrorState } from "@/components/state/ErrorState"
import { ProgressHero } from "@/components/dashboard/ProgressHero"
import { ContinueCard } from "@/components/dashboard/ContinueCard"
import { MasteryHighlights } from "@/components/dashboard/MasteryHighlights"
import { BadgeStrip } from "@/components/dashboard/BadgeStrip"
import { useAuth } from "@/hooks/useAuth"
import { useProfile } from "@/hooks/useProfile"
import { useModules } from "@/hooks/useModules"
import { useNextTask } from "@/hooks/useNextTask"
import { useBadges } from "@/hooks/useBadges"
import { buildConceptIndex, enrichMastery } from "@/lib/mastery"

/** Onboarding trio — kako sustav radi, za prvi dojam svježeg usera. */
const ONBOARDING_STEPS = [
  {
    icon: Terminal,
    title: "Riješi zadatak",
    text: "Piši SQL u editoru i odmah vidi je li upit točan.",
  },
  {
    icon: TrendingUp,
    title: "Prati napredak",
    text: "Model znanja procjenjuje svaki koncept dok vježbaš.",
  },
  {
    icon: Award,
    title: "Skupljaj nagrade",
    text: "XP, leveli i bedževi rastu s tvojim znanjem.",
  },
] as const

function OnboardingIntro() {
  return (
    <Card>
      <CardContent className="grid gap-6 sm:grid-cols-3">
        {ONBOARDING_STEPS.map(({ icon: Icon, title, text }) => (
          <div key={title} className="flex flex-col gap-2">
            <div className="flex size-10 items-center justify-center rounded-lg border border-border bg-muted">
              <Icon
                className="size-5 text-muted-foreground"
                aria-hidden="true"
              />
            </div>
            <h3 className="text-sm font-semibold">{title}</h3>
            <p className="text-sm text-muted-foreground">{text}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export function DashboardPage() {
  const { user } = useAuth()
  const profile = useProfile()
  const modules = useModules()
  const badges = useBadges()
  // Warm poziv: /next-task ne ovisi o profile/modules, a ContinueCard se mounta
  // tek nakon njihovog gatea — ovako najskuplji fetch kreće ODMAH, paralelno
  // (ContinueCardov hook dijeli cache pa nema dvostrukog poziva).
  useNextTask()

  if (profile.isPending || modules.isPending) {
    return (
      <div className="mx-auto max-w-5xl space-y-6">
        <LoadingState lines={2} label="Učitavanje dashboarda" />
        <Card aria-hidden="true">
          <CardContent>
            <LoadingState lines={3} label="" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (profile.isError || modules.isError) {
    return (
      <div className="mx-auto max-w-5xl">
        <ErrorState
          title="Dashboard nije dostupan"
          message="Ne mogu dohvatiti tvoj profil — pokušaj ponovno."
          onRetry={() => {
            if (profile.isError) void profile.refetch()
            if (modules.isError) void modules.refetch()
          }}
        />
      </div>
    )
  }

  const conceptIndex = buildConceptIndex(modules.data)
  const mastery = enrichMastery(profile.data.mastery, conceptIndex)
  const isFresh =
    profile.data.xp === 0 &&
    profile.data.mastery.length === 0 &&
    profile.data.badges.length === 0

  // Jedan zajednički page-shell za obje varijante (fresh/normal) — razlika je
  // samo copy + trailing sekcije, da promjene shella ne treba raditi dvaput.
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          {isFresh ? `Dobrodošao, ${user?.username}` : `Bok, ${user?.username}`}
        </h1>
        <p className="text-sm text-muted-foreground">
          {isFresh
            ? "Tvoj put kroz SQL kreće ovdje — prvi zadatak te već čeka."
            : "Pregled tvog napretka i sljedeći korak."}
        </p>
      </div>

      {!isFresh && <ProgressHero profile={profile.data} />}
      <ContinueCard conceptIndex={conceptIndex} onboarding={isFresh} />
      {isFresh && <OnboardingIntro />}

      {!isFresh && mastery.length > 0 && (
        <MasteryHighlights
          mastery={mastery}
          masteryThreshold={profile.data.mastery_threshold}
        />
      )}

      {!isFresh && badges.isPending && (
        <Card aria-busy="true">
          <CardContent>
            <LoadingState lines={1} label="Učitavanje bedževa" />
          </CardContent>
        </Card>
      )}
      {!isFresh && badges.isSuccess && (
        <BadgeStrip catalog={badges.data} earnedCodes={profile.data.badges} />
      )}
      {!isFresh && badges.isError && (
        <ErrorState
          title="Bedževi nisu dostupni"
          onRetry={() => void badges.refetch()}
        />
      )}
    </div>
  )
}
