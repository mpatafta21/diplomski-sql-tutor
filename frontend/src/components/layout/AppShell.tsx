/**
 * AppShell (Faza 4.1c) — sidebar + header ljuska iza auth gatea.
 * Vuče 4.1b tokene (sidebar-* set); od 4.7 je aplikacija dark-only. Nav NIJE skica — sve su stavke
 * prave rute od 4.6-evala (vidi NAV_ITEMS ispod). Admin stavka je role-gated.
 */
import { NavLink, Outlet } from "react-router-dom"
import {
  BookOpen,
  Database,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  Terminal,
  Trophy,
  User,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ErrorBoundary } from "@/components/ErrorBoundary"
import { useAuth } from "@/hooks/useAuth"
import { cn } from "@/lib/utils"

// Nav (4.2 → 4.6-eval): sve stavke su prave rute. „Zadatak" (`/task`) je entry
// ruta koja razriješi tekuću preporuku i redirecta na `/task/:taskId`.
// `end` po stavci: exact match svugdje OSIM „Zadatak" — njemu `end: false` da
// ostane aktivan i dok si na konkretnom `/task/:taskId`. Dashboard (`/`) MORA
// ostati `end: true`, inače bi kao prefiks bio aktivan na svakoj ruti.
const NAV_ITEMS = [
  { label: "Dashboard", icon: LayoutDashboard, to: "/", end: true },
  { label: "Moduli", icon: BookOpen, to: "/modules", end: true },
  { label: "Zadatak", icon: Terminal, to: "/task", end: false },
  { label: "Profil", icon: User, to: "/profile", end: true },
  { label: "Ljestvica", icon: Trophy, to: "/leaderboard", end: true },
] as const

function SidebarNav() {
  const { user } = useAuth()

  return (
    <nav
      aria-label="Glavna navigacija"
      className="flex flex-1 flex-col gap-1 p-3"
    >
      {NAV_ITEMS.map(({ label, icon: Icon, to, end }) => (
        <NavLink
          key={label}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              // Invarijanta (WCAG 2.5.5): h-11 = 44px touch target po nav stavci.
              "flex h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors duration-fast ease-standard",
              "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
              isActive
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
            )
          }
        >
          <Icon className="size-4 shrink-0" aria-hidden="true" />
          {label}
        </NavLink>
      ))}
      {/* Role-gating skriva stavku; ZAŠTITU rute radi AdminRoute (4.5b DIO 1). */}
      {user?.role === "admin" && (
        <NavLink
          to="/admin"
          end
          className="flex h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium text-muted-foreground transition-colors duration-fast ease-standard hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          <ShieldCheck className="size-4 shrink-0" aria-hidden="true" />
          Admin
        </NavLink>
      )}
    </nav>
  )
}

export function AppShell() {
  const { user, logout } = useAuth()

  return (
    <div className="flex min-h-svh">
      {/* Jedan <defs> za cijelu aplikaciju — lucide ikone crtaju `stroke`, pa im
          gradijent mora doći kroz SVG referencu, ne kroz CSS `background`.
          Srednji stop je upisan jer SVG interpolira u sRGB, a brojke su mjerene
          na oklch-sredini (v. `--grad-brand` u index.css). */}
      <svg width="0" height="0" aria-hidden="true" className="absolute">
        <defs>
          <linearGradient id="brand-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="oklch(0.55 0.15 280)" />
            <stop offset="50%" stopColor="oklch(0.665 0.13 280)" />
            <stop offset="100%" stopColor="oklch(0.78 0.11 280)" />
          </linearGradient>
        </defs>
      </svg>

      {/* Sidebar — desktop primaran (plan §4.7); na užem ekranu skrivena, header ostaje. */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
        <div className="flex h-16 items-center gap-2.5 border-b border-sidebar-border px-5">
          <Database
            className="size-5 [stroke:url(#brand-grad)]"
            aria-hidden="true"
          />
          <span className="bg-[image:var(--grad-wordmark)] bg-clip-text text-base font-semibold tracking-tight text-transparent">
            SQL Tutor
          </span>
        </div>
        <SidebarNav />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between gap-3 border-b border-border px-4 md:px-6">
          {/* Mobilni brand (sidebar skrivena) */}
          <div className="flex items-center gap-2 md:hidden">
            <Database
              className="size-5 [stroke:url(#brand-grad)]"
              aria-hidden="true"
            />
            <span className="bg-[image:var(--grad-wordmark)] bg-clip-text font-semibold text-transparent">
              SQL Tutor
            </span>
          </div>
          <div className="hidden md:block" />

          {/* Faza 4.7 stage 1: toggle teme uklonjen — aplikacija je dark-only. */}
          <div className="flex items-center gap-2">
            {user && (
              <div className="flex items-center gap-2 rounded-lg border border-border px-3 py-1.5">
                <span className="text-sm font-medium">{user.username}</span>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-xs font-medium",
                    user.role === "admin"
                      ? "bg-accent-warm text-accent-warm-foreground"
                      : "bg-muted text-muted-foreground",
                  )}
                >
                  {user.role}
                </span>
              </div>
            )}

            <Button variant="outline" onClick={logout}>
              <LogOut data-icon="inline-start" />
              Odjava
            </Button>
          </div>
        </header>

        <main className="flex-1 p-4 md:p-8">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
