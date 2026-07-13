/**
 * useRun (Faza 4.3b) — POST /run: čisti sandbox exec BEZ bodovanja.
 *
 * Mutation (akcija), ne query. 🔴 Ugovor: /run UVIJEK vraća HTTP 200 — SQL/
 * timeout greška stiže kao `error` string U PODACIMA (normalan ishod učenja,
 * ne mrežna greška). `mutation.error` (ApiError) je zato SAMO infra kvar
 * (401/5xx/mreža). Ništa se ne persistira → NULA invalidacija (/profile,
 * /next-task i ostali cachevi ostaju netaknuti — ništa se nije promijenilo).
 */
import { useMutation } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export function useRun(taskId: number) {
  return useMutation({
    mutationFn: async (query: string) =>
      unwrap(
        await api.POST("/run", {
          // task_id je čisti kontekst — ne mijenja izvršavanje (routes.py).
          body: { query, task_id: taskId },
        }),
      ),
  })
}
