/**
 * useTaskForConcept — razriješi koncept u konkretan zadatak ZA OVOG korisnika.
 *
 * Postoji jer je `entry_task_id` iz `/modules` statičan katalog bez korisničkog
 * konteksta, pa je klik na koncept vodio na već riješen zadatak. Ova ruta
 * preskače riješene server-side.
 *
 * `repeat: true` znači da su svi zadaci koncepta riješeni pa se vraća najlakši
 * za ponavljanje — Task ekran ga označava bedžom „Riješeno" i ponovna predaja
 * ne nosi XP.
 *
 * 🔴 BEZ staleTime: skup riješenih se mijenja svakom točnom predajom, a ovo je
 * navigacijski razrješivač — zastarjeli odgovor vodi točno na zadatak koji fix
 * uklanja. Suprotno od `useModules` (staleTime 5 min), koji smije biti star jer
 * je katalog.
 */
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api/client"
import { unwrap } from "@/lib/api/query"

export function useTaskForConcept(code: string | undefined) {
  return useQuery({
    queryKey: ["task-for-concept", code],
    queryFn: async () =>
      unwrap(
        await api.GET("/task-for-concept/{code}", {
          params: { path: { code: code as string } },
        }),
      ),
    enabled: Boolean(code),
    staleTime: 0,
    gcTime: 0,
    retry: false,
  })
}
