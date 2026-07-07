import { useContext } from "react"
import { ThemeContext, type ThemeContextValue } from "@/lib/theme/context"

/** Pristup temi (dark/toggle). Mora biti unutar <ThemeProvider>. */
export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext)
  if (ctx === null) {
    throw new Error("useTheme mora biti korišten unutar <ThemeProvider>")
  }
  return ctx
}
