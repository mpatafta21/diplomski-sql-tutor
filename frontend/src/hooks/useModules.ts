/**
 * useModules (Faza 4.2) — taksonomija: moduli + koncepti (ime/tier/prereq graf).
 * Jedini izvor IMENA koncepta — /profile.mastery nosi samo code (join ovdje).
 * Katalog se rijetko mijenja → dulji staleTime.
 */
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export function useModules() {
  return useQuery({
    queryKey: ["modules"],
    queryFn: async () => unwrap(await api.GET("/modules")),
    staleTime: 5 * 60 * 1000,
  })
}
