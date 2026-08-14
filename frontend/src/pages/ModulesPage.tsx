/**
 * ModulesPage (Faza 4.2b) — Module overview: 6 modul-kartica (order_index) +
 * ODVOJENA transverzalna sekcija (odluka C — modul 0 nije ravnopravna kartica).
 * Sve iz /modules × /profile joina; prag iz mastery_threshold (invarijanta: prag iz /profile, nikad hardkodiran 0.85).
 */
import { useEffect, useMemo } from "react"
import { Link, useLocation } from "react-router-dom"
import { ArrowRight, BookOpen, Waypoints } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { LoadingState } from "@/components/state/LoadingState"
import { EmptyState } from "@/components/state/EmptyState"
import { ErrorState } from "@/components/state/ErrorState"
import { ModuleCard } from "@/components/modules/ModuleCard"
import { ConceptRow } from "@/components/modules/ConceptRow"
import { DifficultyChip } from "@/components/DifficultyChip"
import { useModules } from "@/hooks/useModules"
import { useProfile } from "@/hooks/useProfile"
import { deriveProgress } from "@/lib/progress"

export function ModulesPage() {
  const profile = useProfile()
  const modules = useModules()
  const location = useLocation()

  // useMemo PRIJE early returnova (rules-of-hooks); derive je jeftin, ali warn
  // ispod ne smije okidati na svaki render/refetch.
  const overview = useMemo(
    () =>
      modules.data && profile.data
        ? deriveProgress(
            modules.data,
            profile.data.mastery,
            profile.data.mastery_threshold,
          )
        : null,
    [modules.data, profile.data],
  )

  // Breadcrumb deep-link (task screen → `/modules#module-<n>` | `#concept-<code>`):
  // koji modul otvoriti da anker bude vidljiv. Za koncept nađemo modul koji ga
  // sadrži (transverzalni koncepti su uvijek vidljivi → null, bez auto-opena).
  const hashTarget = location.hash.slice(1)
  const openModuleNumber = useMemo(() => {
    if (!hashTarget || !overview) return null
    if (hashTarget.startsWith("module-")) {
      const n = Number(hashTarget.slice("module-".length))
      return Number.isInteger(n) ? n : null
    }
    if (hashTarget.startsWith("concept-")) {
      const code = hashTarget.slice("concept-".length)
      const owner = overview.main.find((p) =>
        p.concepts.some((c) => c.code === code),
      )
      return owner ? owner.module.number : null
    }
    return null
  }, [hashTarget, overview])

  // Integritetski signal (STANI-I-JAVI): jednom po promjeni podataka, ne po renderu.
  useEffect(() => {
    if (overview && overview.danglingPrereqs.length > 0) {
      console.warn(
        "Prereq codovi bez koncepta u /modules:",
        overview.danglingPrereqs,
      )
    }
  }, [overview])

  // Skrol + flash na anker iz hasha. Ciljani modul je otvoren od prvog rendera
  // (defaultOpen dolje), pa je anker već u DOM-u; rAF pričeka layout prije skrola.
  // Highlight je JS-vođen (data-deeplinked, 2 s) umjesto CSS `:target` — `:target`
  // je nepouzdan uz client-side routing (pushState ga ne re-evaluira dosljedno).
  // Ovisi o hashu I o tome da su podaci stigli (overview) — bez toga ankera nema.
  useEffect(() => {
    if (!hashTarget || !overview) return
    const el = document.getElementById(hashTarget)
    if (!el) return
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    const raf = requestAnimationFrame(() => {
      el.scrollIntoView({
        block: "center",
        behavior: reduce ? "auto" : "smooth",
      })
      el.setAttribute("data-deeplinked", "true")
    })
    const t = setTimeout(() => el.removeAttribute("data-deeplinked"), 2000)
    return () => {
      cancelAnimationFrame(raf)
      clearTimeout(t)
      el.removeAttribute("data-deeplinked")
    }
  }, [hashTarget, overview])

  if (profile.isPending || modules.isPending) {
    return (
      <div className="mx-auto max-w-5xl space-y-6">
        <LoadingState lines={2} label="Učitavanje modula" />
        <Card aria-hidden="true">
          <CardContent>
            <LoadingState lines={3} label="" />
          </CardContent>
        </Card>
      </div>
    )
  }

  if (profile.isError || modules.isError || overview === null) {
    return (
      <div className="mx-auto max-w-5xl">
        <ErrorState
          title="Moduli nisu dostupni"
          message="Ne mogu dohvatiti pregled modula — pokušaj ponovno."
          onRetry={() => {
            if (profile.isError) void profile.refetch()
            if (modules.isError) void modules.refetch()
          }}
        />
      </div>
    )
  }

  const { main, transversal } = overview
  const isFresh = profile.data.mastery.length === 0
  // Korijen grafa iz PODATAKA (ontologija je izvor istine), ne hardkodirano ime.
  const rootConcept = modules.data
    .flatMap((m) => m.concepts)
    .find((c) => c.prerequisites.length === 0)

  if (main.length === 0 && transversal === null) {
    return (
      <div className="mx-auto max-w-5xl space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight">Moduli</h1>
        <EmptyState
          icon={BookOpen}
          title="Nema modula"
          description="Katalog modula je prazan — baza vjerojatno nije seedana. Javi se administratoru."
        />
      </div>
    )
  }

  return (
    // `stagger-cards` (B.2): entrance stagger direktne djece — v. index.css.
    <div className="stagger-cards mx-auto max-w-5xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">Moduli</h1>
        <p className="text-sm text-muted-foreground">
          Put kroz SQL — koncepti se otključavaju savladavanjem preduvjeta.
        </p>
        {/* 🔴 Objašnjenje stoji JEDNOM po stranici, ne po retku. Prije je isti
            tekst bio `sr-only` u svakom ConceptRowu — ondje ga čitač ekrana ne
            bi ni pročitao (redak je `<Link aria-label>`, koji poništava
            sadržaj), a gdje bi ga pročitao, ponovio bi se ~30 puta. */}
        <p className="text-xs text-muted-foreground">
          Postotak uz koncept je procjena znanja iz modela, ne udio riješenih
          zadataka — raste i kad koncept riješiš kao sporedni dio drugog
          zadatka. Uz njega stoji broj riješenih zadataka tog koncepta.
        </p>
      </div>

      {isFresh && rootConcept && (
        <Card className="border-accent-warm/30">
          <CardContent className="flex flex-wrap items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              Sve je pred tobom — kreni od koncepta{" "}
              <span className="font-medium text-foreground">
                {rootConcept.name}
              </span>
              , jedinog bez preduvjeta.
            </p>
            <Button asChild>
              <Link to="/">
                Preporučeni zadatak
                <ArrowRight data-icon="inline-end" aria-hidden="true" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid items-start gap-6 lg:grid-cols-2">
        {main.map((p) => (
          <ModuleCard
            key={p.module.id}
            progress={p}
            defaultOpen={p.module.number === openModuleNumber}
          />
        ))}
      </div>

      {transversal && (
        <section
          id={`module-${transversal.module.number}`}
          aria-labelledby="transversal-heading"
          className="scroll-mt-24 space-y-3"
        >
          <div className="flex items-center gap-2">
            <Waypoints
              className="size-4 text-muted-foreground"
              aria-hidden="true"
            />
            <h2
              id="transversal-heading"
              className="text-base font-semibold tracking-tight"
            >
              {transversal.module.name}
            </h2>
            <DifficultyChip difficulty={transversal.module.difficulty} />
          </div>
          <Card className="border-dashed">
            <CardContent>
              <p className="mb-2 text-sm text-muted-foreground">
                {transversal.module.description ??
                  "Koncepti koji se protežu kroz više modula."}{" "}
                Vježbaju se kroz zadatke ostalih modula, ne izravno.
              </p>
              <ul className="divide-y divide-border">
                {transversal.concepts.map((c) => (
                  <ConceptRow key={c.code} concept={c} />
                ))}
              </ul>
            </CardContent>
          </Card>
        </section>
      )}
    </div>
  )
}
