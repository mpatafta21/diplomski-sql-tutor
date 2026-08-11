/**
 * Topbar breadcrumb (Faza 4.7-1C, t.3) — `sql_tutor.dashboard` obrazac, u monou.
 *
 * 🔴 IZVEDEN IZ RUTE, ne hardkodiran: novi segment u routeru pojavi se ovdje sam, uz
 * fallback na sam segment. Time ne može zaostati za `router.tsx`.
 *
 * ⚠️ Ovo NIJE isti breadcrumb kao onaj na Task screenu (`TaskPage.tsx:221-268`). Taj
 * opisuje GRADIVO (modul › koncept › zadatak); ovaj opisuje MJESTO U APLIKACIJI. Dvije
 * su osi, pa stoje jedan ispod drugoga — v. bilješku u 1C t.3.
 */
import { useLocation, useParams } from "react-router-dom"

/** ruta → segment. Nepoznata ruta pada na sam pathname, ne na prazno. */
const SEGMENT: Record<string, string> = {
  "": "dashboard",
  modules: "moduli",
  task: "zadatak",
  profile: "profil",
  leaderboard: "ljestvica",
  admin: "admin",
}

export function Breadcrumb() {
  const { pathname } = useLocation()
  const { taskId } = useParams()

  const first = pathname.split("/")[1] ?? ""
  const parts = [SEGMENT[first] ?? first]
  // `/task/:taskId` → `sql_tutor.zadatak.15` — broj je dio mjesta, ne ukras.
  if (first === "task" && taskId) parts.push(taskId)

  return (
    <nav aria-label="Mjesto u aplikaciji" className="min-w-0">
      <p className="truncate font-mono text-xs text-muted-foreground">
        sql_tutor
        {parts.map((p, i) => (
          <span key={p}>
            <span aria-hidden="true">.</span>
            {/* Zadnji segment je tekuće mjesto → nosi `foreground`, ostalo muted. */}
            <span className={i === parts.length - 1 ? "text-foreground" : ""}>
              {p}
            </span>
          </span>
        ))}
      </p>
    </nav>
  )
}
