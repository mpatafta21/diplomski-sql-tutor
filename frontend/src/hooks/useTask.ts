/**
 * useTask (Faza 4.2) — detalj zadatka (naslov/opis/koncepti). Dashboard ga
 * koristi za NASLOV preporuke (/next-task vraća samo task_id); 4.3 nasljeđuje.
 * `enabled` gate: ne puca dok task_id ne postoji (nullable preporuka).
 */
import { skipToken, useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export function useTask(taskId: number | null | undefined) {
  return useQuery({
    queryKey: ["task", taskId],
    // skipToken umjesto enabled+cast: gating i tipizacija na JEDNOM mjestu —
    // queryFn tipski ne postoji dok je taskId null (nema `as number` rupe).
    queryFn:
      taskId == null
        ? skipToken
        : async () =>
            unwrap(
              await api.GET("/task/{task_id}", {
                params: { path: { task_id: taskId } },
              }),
            ),
  })
}
