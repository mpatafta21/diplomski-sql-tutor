/**
 * useBadges (Faza 4.2) — katalog SVIH bedževa (bez earned flaga — earned dolazi
 * iz /profile.badges kao lista codova; join radi komponenta). Katalog je
 * statičan → dulji staleTime.
 */
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export function useBadges() {
  return useQuery({
    queryKey: ["badges"],
    queryFn: async () => unwrap(await api.GET("/badges")),
    staleTime: 5 * 60 * 1000,
  })
}
