/**
 * useLeaderboard (Faza 4.5a) — paginirana ljestvica, global ili weekly.
 *
 * `scope` je DIO queryKeya → prebacivanje global↔weekly ne gazi tuđi cache i
 * povratak na prethodni scope je instantan.
 *
 * 🔴 NEMA invalidacije iz useSubmitAttempt: ljestvica je tuđi agregat (ovisi o
 * SVIM korisnicima, ne samo o mom XP-u), pa bi "osvježi nakon mog attempta"
 * ionako bio nepotpun. Svjež podatak dolazi pri ulasku na rutu.
 *
 * 🔴 placeholderData je SCOPE-SVJESTAN, ne goli `keepPreviousData`:
 * prethodni podaci se zadržavaju SAMO unutar istog scopea (prelazak stranice →
 * bez skeleton-flasha, isti obrazac kao useAttempts). Pri prebacivanju
 * global↔weekly se ODBACUJU — inače bi tablica na trenutak prikazivala brojke
 * jednog razdoblja ispod naslova drugog („Zadnjih 7 dana" nad ukupnim XP-om), što
 * je tiha neistina o podatku, a ne samo kozmetički flash.
 */
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export type LeaderboardScope = "global" | "weekly"

interface UseLeaderboardParams {
  scope: LeaderboardScope
  limit: number
  offset: number
}

export function useLeaderboard({ scope, limit, offset }: UseLeaderboardParams) {
  return useQuery({
    queryKey: ["leaderboard", { scope, limit, offset }],
    queryFn: async () =>
      unwrap(
        await api.GET("/leaderboard", {
          params: { query: { scope, limit, offset } },
        }),
      ),
    placeholderData: (previousData, previousQuery) => {
      const previousScope = (
        previousQuery?.queryKey?.[1] as { scope?: LeaderboardScope } | undefined
      )?.scope
      // Isti scope → zadrži (paginacija). Drugi scope → undefined = loading.
      return previousScope === scope ? previousData : undefined
    },
  })
}
