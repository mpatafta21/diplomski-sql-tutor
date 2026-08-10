/**
 * AppShell (Faza 4.1c) — sidebar + header ljuska iza auth gatea.
 * Vuče 4.1b tokene (sidebar-* set); od 4.7 je aplikacija dark-only. Nav NIJE skica — sve su stavke
 * prave rute od 4.6-evala (vidi NAV_ITEMS ispod). Admin stavka je role-gated.
 */
import { useState } from "react"
import { NavLink, Outlet, useLocation } from "react-router-dom"
import {
  BookOpen,
  Database,
  LayoutDashboard,
  LogOut,
  Menu,
  ShieldCheck,
  Terminal,
  Trophy,
  User,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { ErrorBoundary } from "@/components/ErrorBoundary"
import { useAuth } from "@/hooks/useAuth"
import { cn } from "@/lib/utils"

// Nav (4.2 → 4.6-eval): sve stavke su prave rute. „Zadatak" (`/task`) je entry
// ruta koja razriješi tekuću preporuku i redirecta na `/task/:taskId`.
// `end` po stavci: exact match svugdje OSIM „Zadatak" — njemu `end: false` da
// ostane aktivan i dok si na konkretnom `/task/:taskId`. Dashboard (`/`) MORA
// ostati `end: true`, inače bi kao prefiks bio aktivan na svakoj ruti.
// ⟳ 4.7-r2: iste stavke, sada GRUPIRANE — grupa nosi mono section header
// (`-- učenje`). Redoslijed stavki unutar grupa je NEPROMIJENJEN.
const NAV_GROUPS = [
  {
    label: "učenje",
    items: [
      { label: "Dashboard", icon: LayoutDashboard, to: "/", end: true },
      { label: "Moduli", icon: BookOpen, to: "/modules", end: true },
      { label: "Zadatak", icon: Terminal, to: "/task", end: false },
    ],
  },
  {
    label: "napredak",
    items: [
      { label: "Profil", icon: User, to: "/profile", end: true },
      { label: "Ljestvica", icon: Trophy, to: "/leaderboard", end: true },
    ],
  },
] as const

// Section header: mono, `muted-foreground`, BEZ uppercasea (mala slova su dio
// dev-konzolnog glasa — v. MASTER §3.2). `aria-hidden` jer skupinu za čitač
// ekrana nosi `aria-label` na <ul>, ne vizualni tekst.
const SECTION_HEADER =
  "px-3 pt-4 pb-1 font-mono text-xs text-muted-foreground first:pt-0"

/**
 * Nav stavke. `onNavigate` je OPCIONALAN i koristi ga SAMO drawer (zatvara se nakon
 * odabira). Desktop sidebar ga ne prosljeđuje → njegovo ponašanje je nepromijenjeno.
 */
function SidebarNav({ onNavigate }: { onNavigate?: () => void } = {}) {
  const { user } = useAuth()

  return (
    <nav
      aria-label="Glavna navigacija"
      className="flex flex-1 flex-col gap-1 p-3"
    >
      {NAV_GROUPS.map((group) => (
        <div key={group.label}>
          <div className={SECTION_HEADER} aria-hidden="true">
            -- {group.label}
          </div>
          <ul aria-label={group.label} className="flex flex-col gap-1">
            {group.items.map(({ label, icon: Icon, to, end }) => (
              <li key={label}>
                <NavLink
                  to={to}
                  end={end}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    cn(
                      // Invarijanta (WCAG 2.5.5): h-11 = 44px touch target po stavci.
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
              </li>
            ))}
          </ul>
        </div>
      ))}

      {/* Role-gating skriva stavku; ZAŠTITU rute radi AdminRoute (4.5b DIO 1).
          Grupa „sustav" se NE renderira studentu — prazan section header bio bi
          obećanje sadržaja kojeg nema. */}
      {user?.role === "admin" && (
        <div>
          <div className={SECTION_HEADER} aria-hidden="true">
            -- sustav
          </div>
          <ul aria-label="sustav" className="flex flex-col gap-1">
            <li>
              <NavLink
                to="/admin"
                end
                onClick={onNavigate}
                className="flex h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium text-muted-foreground transition-colors duration-fast ease-standard hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
              >
                <ShieldCheck className="size-4 shrink-0" aria-hidden="true" />
                Admin
              </NavLink>
            </li>
          </ul>
        </div>
      )}
    </nav>
  )
}

/**
 * Mobilna navigacija (<768px) — NALAZ N-5.
 *
 * 🔴 IZLAZNI KRITERIJ: drawer MORA sadržavati **Profil** i **Odjavu**.
 * Profil nosi `ParticipationSection` (informacija o sudjelovanju, kontakt, brisanje
 * podataka). Do 1C je ispod 768px sidebar bio `hidden` bez zamjene, pa prijavljen
 * korisnik na telefonu do te informacije NIJE IMAO PUTA: `/register` mu je zatvoren
 * (`PublicOnlyRoute` → redirect), a Profil nedosežan.
 *
 * 🔴 Admin stavka je i ovdje role-gated — `SidebarNav` je JEDAN izvor istine za nav,
 * pa se uvjet `user?.role === "admin"` ne replicira nego NASLJEĐUJE. Da je drawer imao
 * vlastitu kopiju popisa, role-gate bi se mogao razići.
 */
function MobileNav() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const location = useLocation()

  // Zatvori na promjenu rute — pokriva i navigacije koje ne idu preko NavLinka
  // (npr. redirect iz `/task` na `/task/:id`).
  const close = () => setOpen(false)

  return (
    <Sheet open={open} onOpenChange={setOpen} key={location.pathname}>
      <SheetTrigger asChild>
        {/* `size="icon"` = 44px (WCAG 2.5.5). `aria-expanded` dolazi od Radixa. */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          aria-label="Otvori izbornik"
        >
          <Menu />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="md:hidden">
        <div className="flex h-16 shrink-0 items-center gap-2.5 border-b border-sidebar-border px-5">
          <Database
            className="size-5 [stroke:url(#brand-grad)]"
            aria-hidden="true"
          />
          <SheetTitle className="bg-[image:var(--grad-wordmark)] bg-clip-text text-base font-semibold tracking-tight text-transparent">
            SQL Tutor
          </SheetTitle>
        </div>
        <SheetDescription className="sr-only">
          Glavna navigacija, profil i odjava
        </SheetDescription>

        <div className="min-h-0 flex-1 overflow-y-auto">
          <SidebarNav onNavigate={close} />
        </div>

        {/* 🔴 Odjava je OVDJE jer je na mobitelu topbar pretijesan; bez nje bi
            korisnik na telefonu ostao bez izlaza iz sessiona. */}
        <div className="shrink-0 border-t border-sidebar-border p-3">
          {user && (
            <div className="mb-2 flex items-center gap-2 px-3">
              <span className="truncate text-sm font-medium">
                {user.username}
              </span>
              <span
                className={cn(
                  "shrink-0 rounded-full px-2 py-0.5 text-xs font-medium",
                  user.role === "admin"
                    ? "bg-accent-warm text-accent-warm-foreground"
                    : "bg-muted text-muted-foreground",
                )}
              >
                {user.role}
              </span>
            </div>
          )}
          <SheetClose asChild>
            <Button variant="outline" className="w-full" onClick={logout}>
              <LogOut data-icon="inline-start" />
              Odjava
            </Button>
          </SheetClose>
        </div>
      </SheetContent>
    </Sheet>
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
          {/* Mobilni brand + hamburger (sidebar skrivena) */}
          <div className="flex items-center gap-2 md:hidden">
            <MobileNav />
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
