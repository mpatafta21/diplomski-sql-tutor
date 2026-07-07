/**
 * Protected placeholder (Faza 4.1c) — pravi Dashboard dolazi u 4.2.
 * Postoji da dokaže auth gate + shell; koristi EmptyState primitiv.
 */
import { LayoutDashboard } from "lucide-react"
import { EmptyState } from "@/components/state/EmptyState"
import { useAuth } from "@/hooks/useAuth"

export function DashboardPlaceholder() {
  const { user } = useAuth()

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          Bok, {user?.username} 👋
        </h1>
        <p className="text-sm text-muted-foreground">
          Prijavljen si — auth gate i shell rade.
        </p>
      </div>
      <EmptyState
        icon={LayoutDashboard}
        title="Dashboard dolazi u 4.2"
        description="XP, level, streak, preporučeni zadatak i mastery pregled stižu u sljedećoj pod-fazi."
      />
    </div>
  )
}
