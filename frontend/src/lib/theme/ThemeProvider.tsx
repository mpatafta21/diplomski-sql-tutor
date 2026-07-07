/**
 * ThemeProvider (Faza 4.1c) — dark-first tema na `.dark` klasi <html> (4.1b token sustav),
 * persist u localStorage. Preuzima logiku iz 4.1b token-preview stranice.
 */
import { useCallback, useEffect, useState, type ReactNode } from "react"
import { ThemeContext } from "./context"

const THEME_KEY = "sql_tutor_theme"

function initialDark(): boolean {
  // Dark-first: bez spremljene preferencije default je dark (MASTER.md §1).
  return localStorage.getItem(THEME_KEY) !== "light"
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [dark, setDark] = useState<boolean>(initialDark)

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark)
    localStorage.setItem(THEME_KEY, dark ? "dark" : "light")
  }, [dark])

  const toggle = useCallback(() => setDark((d) => !d), [])

  return (
    <ThemeContext.Provider value={{ dark, toggle }}>
      {children}
    </ThemeContext.Provider>
  )
}
