/**
 * useAttempts (Faza 4.4a) — paginirana povijest pokušaja trenutnog usera.
 *
 * 🔴 queryKey POČINJE s "attempts" (prefiks) da ga pogodi invalidacija iz
 * useSubmitAttempt (`invalidateQueries({ queryKey: ["attempts"] })`,
 * useSubmitAttempt.ts:48) — submit na task screenu osvježi povijest bez
 * ručnog refresha. `{ limit, offset }` je dio ključa → svaka stranica ima
 * svoj cache, a prefiksna invalidacija svejedno hvata SVE stranice.
 *
 * placeholderData: keepPreviousData — pri prelasku stranice zadrži prethodne
 * retke dok novi stižu (bez skeleton-flasha; perceived performance).
 */
import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

interface UseAttemptsParams {
  limit: number
  offset: number
}

export function useAttempts({ limit, offset }: UseAttemptsParams) {
  return useQuery({
    queryKey: ["attempts", { limit, offset }],
    queryFn: async () =>
      unwrap(
        await api.GET("/attempts", { params: { query: { limit, offset } } }),
      ),
    placeholderData: keepPreviousData,
  })
}
