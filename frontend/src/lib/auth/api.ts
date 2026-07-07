/**
 * Auth API pozivi (Faza 4.1c) — register/login/me kroz typed klijent.
 * Flow (KORAK 0 V): register/login vraćaju SAMO {access_token} → spremi → GET /me za usera.
 */
import { api } from "@/lib/api/client"
import type { MeResponse } from "@/lib/api/types"

export class AuthError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "AuthError"
    this.status = status
  }
}

/** POST /register (JSON) → access_token. */
export async function registerRequest(
  username: string,
  email: string,
  password: string,
): Promise<string> {
  const { data, error, response } = await api.POST("/register", {
    body: { username, email, password },
  })
  if (error || !data) {
    throw new AuthError(response.status, "register_failed")
  }
  return data.access_token
}

/**
 * POST /login — ⚠️ application/x-www-form-urlencoded (OAuth2PasswordRequestForm),
 * NE JSON. Login je po `username`, ne email. bodySerializer + form content-type
 * SAMO za ovaj poziv (ne globalno).
 */
export async function loginRequest(
  username: string,
  password: string,
): Promise<string> {
  const { data, error, response } = await api.POST("/login", {
    // `scope` je u generiranom tipu required (default "" u OAuth2 form modelu).
    body: { username, password, scope: "" },
    bodySerializer(body) {
      return new URLSearchParams(
        body as unknown as Record<string, string>,
      ).toString()
    },
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  })
  if (error || !data) {
    throw new AuthError(response.status, "invalid_credentials")
  }
  return data.access_token
}

/**
 * GET /me (Bearer) → trenutni user.
 * /me nema dokumentiran non-2xx u OpenAPI-ju (401 dolazi iz security dep-a), pa openapi-fetch
 * tipizira samo uspjeh → gate ide na `response.ok`, ne na `error` (401 se runtime svejedno dogodi).
 */
export async function fetchMe(): Promise<MeResponse> {
  const { data, response } = await api.GET("/me")
  if (!response.ok || !data) {
    throw new AuthError(response.status, "me_failed")
  }
  return data
}
