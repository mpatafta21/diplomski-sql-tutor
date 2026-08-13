/**
 * useHint (Faza 5.2, §C1) — `POST /hint`: savjet za zadnju netočnu predaju.
 *
 * 🔴 NE koristi `unwrap` iz `lib/api/query`: `ApiError` nosi samo `status`, a
 * ovdje se ishod mora razlučiti po `detail` (§C.2.1 — `503` ima dva suprotna
 * značenja). Zato se tijelo greške čita ovdje i pretvara u `HintError.reason`.
 *
 * 🔴 `onSuccess` invalidira `["profile"]` (C.3.3): kredit se troši HINTOM, ne
 * predajom. Bez ove invalidacije brojač bi se osvježio tek pri sljedećem
 * `POST /attempt` — student potroši savjet i vidi staru brojku.
 *
 * 🔴 NE invalidira ništa drugo. Hint ne mijenja ni BKT, ni XP, ni preporuku;
 * `hint_requests` je jedina tablica u koju se piše, a nju frontend ne čita
 * (isti obrazac kao `useRun`: invalidira se ono što se stvarno promijenilo).
 */
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { hintFailure, type HintFailure } from "@/lib/hint"

export class HintError extends Error {
  readonly status: number
  readonly reason: HintFailure

  constructor(status: number, reason: HintFailure) {
    super(`hint ${status}: ${reason}`)
    this.name = "HintError"
    this.status = status
    this.reason = reason
  }
}

export function useHint(taskId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const { data, error, response } = await api.POST("/hint", {
        body: { task_id: taskId },
      })
      if (!response.ok || data === undefined) {
        throw new HintError(response.status, hintFailure(error))
      }
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["profile"] })
    },
  })
}
