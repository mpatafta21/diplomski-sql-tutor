/**
 * ParticipationSection (Faza 4.7-1a-dopuna) — informacija o sudjelovanju na Profilu.
 *
 * 🔴 ZAŠTO POSTOJI: `PublicOnlyRoute` (guards.tsx:87-97) preusmjerava prijavljenog
 * korisnika s `/register` na `/` uz `replace` — dakle tekst koji je sudionik
 * pročitao PRIJE registracije nakon prijave više NIJE dosežan, ni Backom. Bez
 * ove sekcije obećanje o brisanju podataka i kontakt žive točno jednom u životu
 * računa.
 *
 * 🔴 NULA DUPLIKATA TEKSTA: isti `SUDJELOVANJE_*` izvozi iz `lib/participation.ts`
 * koje renderira `RegisterPage`. Razlikuje se samo KOMPOZICIJA (kartica + mailto
 * s kontekstom), nikad sadržaj — inače bi se dvije verzije obećanja razišle.
 *
 * Što Profil može a `/register` ne: `mailto` nosi prefilled subject s korisničkim
 * imenom, pa zahtjev dolazi već identificiran (na `/register` račun još ne postoji).
 */
import { Info } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  KONTAKT,
  SUDJELOVANJE_KONTAKT_UVOD,
  SUDJELOVANJE_NASLOV,
  SUDJELOVANJE_ODLOMCI,
} from "@/lib/participation"

interface ParticipationSectionProps {
  /**
   * Korisničko ime iz POSTOJEĆEG auth konteksta (ProfilePage ga već ima iz
   * `useAuth`) — bez novog querya i bez ponovnog `/me`.
   * `undefined` je legitiman ulaz: tada ide čist `mailto` bez subjekta.
   */
  username: string | undefined
}

/**
 * `mailto` s kontekstom. Kad `username` nije poznat vraća GOLI mailto — nikad
 * subject s literalom „undefined" u njemu.
 */
function mailtoHref(username: string | undefined): string {
  if (!username) return `mailto:${KONTAKT}`
  const subject = `Zahtjev vezan uz podatke — korisnik ${username}`
  return `mailto:${KONTAKT}?subject=${encodeURIComponent(subject)}`
}

export function ParticipationSection({ username }: ParticipationSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-1.5 text-base">
          <Info aria-hidden="true" className="size-4 shrink-0" />
          {SUDJELOVANJE_NASLOV}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {SUDJELOVANJE_ODLOMCI.map((odlomak) => (
          <p key={odlomak} className="text-sm leading-relaxed">
            {odlomak}
          </p>
        ))}
        <p className="text-sm leading-relaxed">
          {SUDJELOVANJE_KONTAKT_UVOD}{" "}
          {/* Vidljivi tekst je ČITLJIVA ADRESA, ne „klikni ovdje" — poveznica
              mora imati smisla i kad je izvučena iz konteksta (SR lista
              poveznica, WCAG 2.4.4). Kontekst putuje kroz subject, ne kroz
              vidljivi tekst. */}
          <a
            href={mailtoHref(username)}
            className="rounded-sm font-medium underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
          >
            {KONTAKT}
          </a>
        </p>
      </CardContent>
    </Card>
  )
}
