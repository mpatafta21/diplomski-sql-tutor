/**
 * useAgentLogs (Faza 4.5b) — FIPA promet agenata, admin-only.
 *
 * 🔴 `limit` se TIHO CAPIRA NA 200 na backendu (NALAZ #36): zatraženo
 * `limit=1000` vraća 200 uz `total=552`. Zato hook NIKAD ne traži više od
 * `MAX_LIMIT` i UI prikazuje stvarni odnos prikazano/ukupno.
 *
 * 🔴 Filtri su SAMO `correlation_id` i `sender` — ugovor druge nema. Plan §4.5
 * spominje i filter po vremenu; on NE POSTOJI i ne izmišlja se na klijentu
 * (client-side filtriranje jedne stranice lagalo bi da filtrira cijeli skup —
 * isti razlog zbog kojeg povijest pokušaja nema filtere, NALAZ #15).
 *
 * Prazan string se NE šalje kao filter (backend bi ga tretirao kao vrijednost)
 * → `undefined` znači „bez filtra".
 */
import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

/** Server-side cap — vidi NALAZ #36. Traženje više od ovoga je besmisleno. */
export const MAX_LIMIT = 200

interface UseAgentLogsParams {
  correlationId?: string
  sender?: string
  limit: number
  offset: number
  enabled?: boolean
}

export function useAgentLogs({
  correlationId,
  sender,
  limit,
  offset,
  enabled = true,
}: UseAgentLogsParams) {
  const query = {
    limit: Math.min(limit, MAX_LIMIT),
    offset,
    ...(correlationId ? { correlation_id: correlationId } : {}),
    ...(sender ? { sender } : {}),
  }

  return useQuery({
    queryKey: ["agent-logs", query],
    queryFn: async () =>
      unwrap(await api.GET("/admin/agent-logs", { params: { query } })),
    placeholderData: keepPreviousData,
    enabled,
  })
}
