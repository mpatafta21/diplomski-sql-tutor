/**
 * Typed API klijent (Faza 4.1c) — openapi-fetch nad generiranim `paths` iz schema.d.ts.
 * Auth je Bearer u Authorization headeru (CORS allow_credentials=False → NE cookie).
 */
import createClient, { type Middleware } from "openapi-fetch"
import type { paths } from "./schema"
import { clearToken, getToken } from "@/lib/auth/storage"

// 401-handler se registrira iz auth contexta (izbjegava cirkularni import context↔client).
// B1: callback, NE hard redirect (redirect je B2).
let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

const authMiddleware: Middleware = {
  onRequest({ request }) {
    const token = getToken()
    if (token) {
      request.headers.set("Authorization", `Bearer ${token}`)
    }
    return request
  },
  onResponse({ response }) {
    // 401 SAMO kad je token bio poslan (istekao/nevažeći) → clear + logout.
    // Login 401 (krivi kredencijali) nema spremljen token → preskače, login() obrađuje grešku.
    if (response.status === 401 && getToken()) {
      clearToken()
      onUnauthorized?.()
    }
    return response
  },
}

export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_URL,
})
api.use(authMiddleware)
