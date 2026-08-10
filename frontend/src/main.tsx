import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { RouterProvider } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import "./index.css"
import { AuthProvider } from "@/lib/auth/AuthProvider"
import { ErrorBoundary } from "@/components/ErrorBoundary"
import { Toaster } from "@/components/ui/sonner"
import { ApiError } from "@/lib/api/query"
import { router } from "@/routes/router"

// TanStack Query provider (Faza 4.1c) — cache/loading/error za data hookove (4.2 nadalje).
// Retry (4.2a code-review): 4xx je deterministički (404 obrisan task, 401 istekao
// token) — retry ne kupuje ništa osim sekundi skeletona; mrežne/5xx greške
// zadržavaju default 3 pokušaja.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) =>
        failureCount < 3 &&
        !(
          error instanceof ApiError &&
          error.status >= 400 &&
          error.status < 500
        ),
    },
  },
})

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      {/* Faza 4.7 stage 1: `ThemeProvider` uklonjen — aplikacija je dark-only.
          Tokeni stoje u `:root` (index.css), pa nema klase koju bi netko togglao. */}
      <AuthProvider>
        <ErrorBoundary>
          <RouterProvider router={router} />
        </ErrorBoundary>
        <Toaster position="top-right" />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
)
