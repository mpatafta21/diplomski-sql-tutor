/**
 * useProfile (Faza 4.2) — XP/level/streak/mastery/badges trenutnog usera.
 * level_step i mastery_threshold su BACKEND konstante koje putuju kroz ovaj
 * odgovor — frontend ih NIKAD ne hardkodira (invarijanta #6).
 */
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export function useProfile() {
  return useQuery({
    queryKey: ["profile"],
    queryFn: async () => unwrap(await api.GET("/profile")),
  })
}
