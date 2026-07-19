/**
 * AdminPage (Faza 4.5b) — administratorski pregled.
 *
 * DIO 1 (ovaj commit): samo ljuska iza `AdminRoute` guarda — sadržaj (FIPA
 * agent-log viewer) dolazi u DIO 2. Ruta postoji od sada da bi guard imao što
 * čuvati i da bi se blokada izravnog URL-a mogla dokazati.
 *
 * 🔴 OPSEG: plan §4.5 spominje i „osnovne eval-statistike" — one se NE grade
 * ovdje (izvan opsega 4.5b). Ako zatrebaju, to je zasebna odluka.
 */
export function AdminPage() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          Administratorski pregled
        </h1>
        <p className="text-sm text-muted-foreground">
          Komunikacija agenata po zadatku — alat za praćenje evaluacije.
        </p>
      </div>
    </div>
  )
}
