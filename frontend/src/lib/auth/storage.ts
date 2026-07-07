/**
 * Token storage (Faza 4.1c) — localStorage, Bearer u Authorization headeru (NE cookie).
 * XSS-razmatranje svjesno prihvaćeno: backend nema cookie/refresh infra (KORAK 0 Z),
 * token traje 24h (eval sesije). Dovoljno za tezu.
 */

const TOKEN_KEY = "sql_tutor_token"

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}
