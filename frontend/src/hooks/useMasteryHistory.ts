/**
 * useMasteryHistory (Faza 4.4b) — BKT P(L) snapshotovi kroz vrijeme.
 *
 * Ruta je NEPAGINIRANA (`list[MasteryHistoryPoint]`) → JEDAN fetch cijele serije
 * pa grupiranje po konceptu na klijentu (lib/mastery-history.ts).
 * 🔴 NE koristiti `?concept=` po konceptu — to bi bio N+1 (26 zahtjeva za mrežu
 * krivulja) nad rutom koja ionako vraća sve odjednom.
 *
 * Redoslijed dolazi ORDER BY created_at ASC, id ASC i NE re-sortira se —
 * obrazloženje u lib/mastery-history.ts (točke istog attempta dijele timestamp).
 */
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export function useMasteryHistory() {
  return useQuery({
    queryKey: ["mastery-history"],
    queryFn: async () => unwrap(await api.GET("/mastery-history")),
  })
}
