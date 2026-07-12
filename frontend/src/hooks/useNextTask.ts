/**
 * useNextTask (Faza 4.2) — Recommenderova preporuka. SVA polja nullable:
 * task_id === null je legitiman ishod (exhausted / no_recommendation), NE greška
 * — semantiku razlučuje lib/recommendation.ts.
 */
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export function useNextTask() {
  return useQuery({
    queryKey: ["next-task"],
    queryFn: async () => unwrap(await api.GET("/next-task")),
    // Najskuplji read u sustavu (XMPP → Recommender → Prolog+BKT), a preporuka
    // se mijenja tek nakon attempta — bez staleTime svaki tab-focus okida cijeli
    // agentski pipeline i može zamijeniti CTA pod rukom. 4.3 invalidira
    // ["next-task"] nakon submita.
    staleTime: 60 * 1000,
  })
}
