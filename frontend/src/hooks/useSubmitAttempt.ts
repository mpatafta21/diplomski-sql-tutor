/**
 * useSubmitAttempt (Faza 4.3c) — POST /attempt: SCORED predaja kroz pun
 * agentski pipeline (Evaluator→KM→Gamification→Recommender).
 *
 * 🔴 Za razliku od /run: attempt SE persistira (attempts, XP, BKT, streak) →
 * nakon SVAKOG 200 odgovora (i netočnog! BKT/streak/attempt-count se mijenjaju)
 * invalidiraju se ["profile"], ["next-task"], ["attempts"], ["mastery-history"].
 * `mastery-history` (4.4b): KM upisuje snapshot po SVAKOM BKT updateu, dakle i
 * na netočnom pokušaju → bez ove invalidacije krivulje na Profilu zaostaju za
 * mastery barovima koji čitaju iz /profile.
 * `/next-task` je skup (XMPP→Prolog) — invalidacija, NE poll (4.2a odluka).
 *
 * Greške: HTTP 504 = AGENT PIPELINE ne odgovara (orchestration/evaluation
 * timeout) — NIJE isto što i error_type:"timeout" (200; studentov SQL predug).
 * ApiError.status razlikuje grane u UI-ju.
 */
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { ProfileResponse } from "@/lib/api/types"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export function useSubmitAttempt(taskId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (submittedQuery: string) =>
      unwrap(
        await api.POST("/attempt", {
          // attempt_number NE šaljemo — backend ga računa sam (COUNT+1).
          body: { task_id: taskId, submitted_query: submittedQuery },
        }),
      ),
    onSuccess: (data) => {
      // Patch /profile cachea autoritativnim gamification snapshotom PRIJE
      // invalidacije: na /task ruti nema aktivnog profile observera pa
      // invalidacija samo označi stale (refetchType 'active') — bez patcha bi
      // level-up derivacija čitala ZASTARJELI level i slavila isti level-up na
      // svakom sljedećem tasku (CTA lanac bez povratka na dashboard).
      queryClient.setQueryData<ProfileResponse>(["profile"], (old) =>
        old
          ? {
              ...old,
              xp: data.xp,
              level: data.level,
              current_streak: data.current_streak,
            }
          : old,
      )
      void queryClient.invalidateQueries({ queryKey: ["profile"] })
      void queryClient.invalidateQueries({ queryKey: ["next-task"] })
      void queryClient.invalidateQueries({ queryKey: ["attempts"] })
      void queryClient.invalidateQueries({ queryKey: ["mastery-history"] })
      // Prvi točan pokušaj mijenja /task.solved (false→true) → osvježi da se
      // „Riješeno" indikator pojavi bez reloada. Ostali queryji su per-user
      // agregati; ovaj je per-task pa se invalidira uz taskId.
      void queryClient.invalidateQueries({ queryKey: ["task", taskId] })
    },
  })
}
