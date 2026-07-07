/**
 * Route guardovi (Faza 4.1c) — layout rute nad useAuth statusom.
 *
 * 401 tok (invarijanta #1): client middleware (401 runtime, NE tipizirana grana) →
 * AuthProvider setUnauthorizedHandler → status='anon' → <ProtectedRoute> deklarativno
 * <Navigate to="/login">. Hard redirect bez imperativnog router handlea u auth sloju.
 */
import { Navigate, Outlet } from "react-router-dom"
import { useAuth } from "@/hooks/useAuth"
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
