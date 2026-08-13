/**
 * useResetHintCredit (Faza 5.2) — `POST /admin/hint-credit/reset`.
 *
 * 🔴 ADMIN-ONLY, i to se ne provjerava ovdje nego na ruti (`require_admin` →
 * 403 `admin_required`). UI sakriva gumb, ali sakrivanje NIJE kontrola pristupa
 * — isti obrazac kao `/hint` (gumb se sakriva, ruta svejedno provjerava).
 *
 * 🔴 Ruta briše isključivo retke POZIVATELJA i ne prima `user_id`. Mutacija ga
 * zato nema što slati: tijelo zahtjeva je prazno, pa se cilj ne može promašiti.
 *
 * `onSuccess` invalidira `["profile"]` — ondje živi brojač (C.3.2).
 */
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export function useResetHintCredit() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => unwrap(await api.POST("/admin/hint-credit/reset")),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["profile"] })
    },
  })
}
