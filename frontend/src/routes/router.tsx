/**
 * Router (Faza 4.1c) — createBrowserRouter (react-router v7, data router).
 * /login, /register → javne (PublicOnlyRoute); / → protected shell.
 */
import { createBrowserRouter } from "react-router-dom"
import { AppShell } from "@/components/layout/AppShell"
import { DashboardPage } from "@/pages/DashboardPage"
import { LoginPage } from "@/pages/LoginPage"
import { ModulesPage } from "@/pages/ModulesPage"
import { RegisterPage } from "@/pages/RegisterPage"
import { TaskStubPage } from "@/pages/TaskStubPage"
import { ProtectedRoute, PublicOnlyRoute } from "./guards"

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
          // STUB (4.2a): drži Dashboard CTA navigaciju živom; ekran gradi 4.3.
          { path: "/task/:taskId", element: <TaskStubPage /> },
        ],
      },
    ],
  },
])
