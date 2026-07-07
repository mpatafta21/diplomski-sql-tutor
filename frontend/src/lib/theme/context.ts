/**
 * Theme context (Faza 4.1c) — odvojen od providera radi react-fast-refresh
 * (isti obrazac kao lib/auth/context.ts).
 */
import { createContext } from "react"

export interface ThemeContextValue {
  /** true = dark tema (dark-first default, MASTER.md §1). */
  dark: boolean
  toggle: () => void
}

export const ThemeContext = createContext<ThemeContextValue | null>(null)
