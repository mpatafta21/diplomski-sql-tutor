/**
 * Router (Faza 4.1c) — createBrowserRouter (react-router v7, data router).
 * /login, /register → javne (PublicOnlyRoute); / → protected shell.
 */
import { createBrowserRouter } from "react-router-dom"
import { AppShell } from "@/components/layout/AppShell"
import { DashboardPlaceholder } from "@/pages/DashboardPlaceholder"
import { LoginPage } from "@/pages/LoginPage"
import { RegisterPage } from "@/pages/RegisterPage"
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
        children: [{ path: "/", element: <DashboardPlaceholder /> }],
      },
    ],
  },
])
