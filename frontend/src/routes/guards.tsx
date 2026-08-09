/**
 * Route guardovi (Faza 4.1c) — layout rute nad useAuth statusom.
 *
 * 401 tok (invarijanta: 401 se hvata u runtimeu, ne kroz tipiziranu granu):
 * client middleware (401 runtime, NE tipizirana grana) →
 * AuthProvider setUnauthorizedHandler → status='anon' → <ProtectedRoute> deklarativno
 * <Navigate to="/login">. Hard redirect bez imperativnog router handlea u auth sloju.
 */
import { Link, Navigate, Outlet } from "react-router-dom"
import { ShieldAlert } from "lucide-react"
import { useAuth } from "@/hooks/useAuth"
import { Button } from "@/components/ui/button"
import { FullPageLoading } from "@/components/state/LoadingState"

/** Zaštićene rute: loading → skeleton; anon → /login; authed → children. */
export function ProtectedRoute() {
  const { status } = useAuth()

  if (status === "loading") {
    return <FullPageLoading label="Provjera prijave" />
  }
  if (status === "anon") {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}

/**
 * Admin rute (Faza 4.5b) — role guard nad `/me.role`.
 *
 * 🔴 `AppShell` role-gating (SidebarNav) skriva NAV STAVKU — to NIJE zaštita
 * rute. Ovaj guard blokira IZRAVAN URL: utipkan `/admin`, bookmark, refresh na
 * ruti. Bez njega bi student koji zna putanju otvorio ekran.
 *
 * 🔴 RACE NA HARD REFRESHU NE POSTOJI, i to je svojstvo AuthProvidera, ne
 * slučajnost: `setUser(me)` se izvršava PRIJE `setStatus("authed")`
 * (AuthProvider.tsx), pa je `user.role` zajamčeno poznat u trenutku kad status
 * prestane biti "loading". Zato je dovoljno čekati `status === "loading"` i tek
 * onda suditi o roli — admin se NE odbija zbog još-neučitanog `/me`, a student
 * se NE propušta dok se rola ne zna.
 * ⚠️ Ako se AuthProvider ikad promijeni tako da status postane "authed" prije
 * nego `user` bude postavljen, ovaj guard postaje propustan — držati taj
 * redoslijed.
 *
 * ODLUKA (403 ekran, ne redirect na "/"): tihi redirect skriva da ruta postoji
 * i da korisniku nedostaje ovlast — mentor prijavljen krivim računom vidio bi
 * samo „bačen sam na dashboard" bez razloga. 403 ekran je iskren i oporavljiv
 * (vodi natrag), a razlikuje „nemaš pravo" od „ruta ne postoji".
 */
export function AdminRoute() {
  const { status, user } = useAuth()

  if (status === "loading") {
    return <FullPageLoading label="Provjera ovlasti" />
  }
  if (status === "anon") {
    return <Navigate to="/login" replace />
  }
  if (user?.role !== "admin") {
    return <ForbiddenScreen />
  }
  return <Outlet />
}

/** 403 ekran — NIKAD bijeli ekran ni vječni spinner (DoD 4.5). */
function ForbiddenScreen() {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center gap-4 py-16 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-incorrect/10">
        <ShieldAlert className="size-6 text-incorrect" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <h1 className="text-xl font-semibold">Nemaš pristup ovom dijelu</h1>
        <p className="text-sm text-muted-foreground">
          Administratorski pregled dostupan je samo računima s ulogom
          <span className="font-medium"> admin</span>. Ako misliš da je ovo
          greška, provjeri jesi li prijavljen ispravnim računom.
        </p>
      </div>
      <Button asChild variant="outline">
        <Link to="/">Natrag na dashboard</Link>
      </Button>
    </div>
  )
}

/** Javne auth rute: već prijavljen user nema što tražiti na /login|/register. */
export function PublicOnlyRoute() {
  const { status } = useAuth()

  if (status === "loading") {
    return <FullPageLoading label="Provjera prijave" />
  }
  if (status === "authed") {
    return <Navigate to="/" replace />
  }
  return <Outlet />
}
