/**
 * Router (Faza 4.1c) — createBrowserRouter (react-router v7, data router).
 * /login, /register → javne (PublicOnlyRoute); / → protected shell.
 */
import { lazy, Suspense } from "react"
import { createBrowserRouter } from "react-router-dom"
import { AppShell } from "@/components/layout/AppShell"
import { LoadingState } from "@/components/state/LoadingState"
import { DashboardPage } from "@/pages/DashboardPage"
import { LoginPage } from "@/pages/LoginPage"
import { ModulesPage } from "@/pages/ModulesPage"
import { RegisterPage } from "@/pages/RegisterPage"
import { ConceptEntryPage } from "@/pages/ConceptEntryPage"
import { TaskEntryPage } from "@/pages/TaskEntryPage"
import { AdminRoute, ProtectedRoute, PublicOnlyRoute } from "./guards"

// Lazy (4.3a): TaskPage vuče monaco-editor (velik chunk) — code-split po ruti,
// glavni bundle ostaje bez monaca.
const TaskPage = lazy(() =>
  import("@/pages/TaskPage").then((m) => ({ default: m.TaskPage })),
)

// Lazy (4.4a): ProfilePage se code-splita po ruti — priprema za 4.4b chunk
// (BKT krivulje / chart lib) koji ne smije teretiti glavni bundle.
const ProfilePage = lazy(() =>
  import("@/pages/ProfilePage").then((m) => ({ default: m.ProfilePage })),
)

// Lazy (4.5a): ljestvica je sekundarni ekran — ne tereti glavni bundle.
const LeaderboardPage = lazy(() =>
  import("@/pages/LeaderboardPage").then((m) => ({
    default: m.LeaderboardPage,
  })),
)

// Lazy (4.5b): admin ekran vidi SAMO admin — nema ga u bundleu studentskog puta.
const AdminPage = lazy(() =>
  import("@/pages/AdminPage").then((m) => ({ default: m.AdminPage })),
)

export const router = createBrowserRouter([
  {
    element: <PublicOnlyRoute />,
    children: [
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          { path: "/", element: <DashboardPage /> },
          { path: "/modules", element: <ModulesPage /> },
          // Ulaz preko nav-stavke „Zadatak" (nema `:taskId`) → razriješi
          // /next-task i redirect na /task/:taskId. Eager import: lagana
          // komponenta (bez monaca), ne treba vlastiti chunk/Suspense.
          { path: "/task", element: <TaskEntryPage /> },
          // Ulaz preko KONCEPTA (Dashboard „Za ojačati", redak u Modulima).
          // Poslužitelj bira zadatak jer jedini zna što je student riješio —
          // `entry_task_id` iz /modules je statičan i vodio je na riješeno.
          { path: "/koncept/:code", element: <ConceptEntryPage /> },
          {
            path: "/task/:taskId",
            // LoadingState (ne FullPageLoading): fallback renderira UNUTAR
            // shella — min-h-svh bi uz header dao scrollbar flash.
            element: (
              <Suspense fallback={<LoadingState label="Učitavanje zadatka" />}>
                <TaskPage />
              </Suspense>
            ),
          },
          {
            path: "/profile",
            element: (
              <Suspense fallback={<LoadingState label="Učitavanje profila" />}>
                <ProfilePage />
              </Suspense>
            ),
          },
          {
            path: "/leaderboard",
            element: (
              <Suspense
                fallback={<LoadingState label="Učitavanje ljestvice" />}
              >
                <LeaderboardPage />
              </Suspense>
            ),
          },
          {
            // AdminRoute je UNUTAR ProtectedRoute/AppShell → anon korisnik
            // nikad ne dođe dovde, a student dobije 403 ekran U ljusci
            // (nav i odjava ostaju dostupni — nije slijepa ulica).
            element: <AdminRoute />,
            children: [
              {
                path: "/admin",
                element: (
                  <Suspense
                    fallback={<LoadingState label="Učitavanje pregleda" />}
                  >
                    <AdminPage />
                  </Suspense>
                ),
              },
            ],
          },
        ],
      },
    ],
  },
])
