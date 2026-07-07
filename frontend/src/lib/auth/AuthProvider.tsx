/**
 * AuthProvider (Faza 4.1c) — token storage + register/login/me wiring.
 * Flow: register/login → spremi token → GET /me → set user (KORAK 0 V).
 * Na mount: postojeći token se validira kroz /me; 401 → anon.
 */
import { useCallback, useEffect, useState, type ReactNode } from "react"
import { toast } from "sonner"
import { setUnauthorizedHandler } from "@/lib/api/client"
import { fetchMe, loginRequest, registerRequest } from "@/lib/auth/api"
import { clearToken, getToken, setToken } from "@/lib/auth/storage"
import type { MeResponse } from "@/lib/api/types"
import { AuthContext, type AuthStatus } from "./context"

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<MeResponse | null>(null)
  const [status, setStatus] = useState<AuthStatus>("loading")

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
    setStatus("anon")
  }, [])

  // 401 na zaštićenoj ruti (istekao/nevažeći token) → client middleware pozove ovo.
  // B2 wire: status='anon' okida deklarativni <Navigate to="/login"> u ProtectedRoute
  // (hard redirect) + toast objašnjava zašto je user izbačen.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null)
      setStatus("anon")
      toast.error("Sesija je istekla — prijavi se ponovno.")
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  // Mount: validiraj postojeći token kroz /me.
  useEffect(() => {
    const token = getToken()
    if (token === null) {
      setStatus("anon")
      return
    }
    fetchMe()
      .then((me) => {
        setUser(me)
        setStatus("authed")
      })
      .catch(() => {
        clearToken()
        setUser(null)
        setStatus("anon")
      })
  }, [])

  const register = useCallback(
    async (username: string, email: string, password: string) => {
      const token = await registerRequest(username, email, password)
      setToken(token)
      const me = await fetchMe()
      setUser(me)
      setStatus("authed")
    },
    [],
  )

  const login = useCallback(async (username: string, password: string) => {
    const token = await loginRequest(username, password)
    setToken(token)
    const me = await fetchMe()
    setUser(me)
    setStatus("authed")
  }, [])

  return (
    <AuthContext.Provider value={{ user, status, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
