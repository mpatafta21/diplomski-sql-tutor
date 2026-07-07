import { useContext } from "react"
import { AuthContext, type AuthContextValue } from "@/lib/auth/context"

/** Pristup auth stanju/akcijama. Mora biti unutar <AuthProvider>. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (ctx === null) {
    throw new Error("useAuth mora biti korišten unutar <AuthProvider>")
  }
  return ctx
}
