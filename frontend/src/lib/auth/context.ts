/**
 * Auth context definicija (Faza 4.1c) — odvojeno od providera radi react-fast-refresh
 * (only-export-components). Tipovi izvedeni iz schema.d.ts (MeResponse).
 */
import { createContext } from "react"
import type { MeResponse } from "@/lib/api/types"

export type AuthStatus = "loading" | "authed" | "anon"

export interface AuthContextValue {
  user: MeResponse | null
  status: AuthStatus
  register: (username: string, email: string, password: string) => Promise<void>
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
