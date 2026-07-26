/**
 * RegisterPage (Faza 4.1c) — username + email + password (invarijanta #4).
 * Client zod pravila su prva obrana (mapiranje po polju); server 409 (duplikat)
 * i 422 dobivaju poruke. B1 registerRequest ne izlaže response detail
 * (username_taken vs email_taken) — svjesno generička 409 poruka, ne diramo B1.
 *
 * 🔴 Faza 4.7-1a — ovo je NAJVIDLJIVIJA površina sustava. Evaluacija se izvodi
 * asinkrono na javnom URL-u, bez nadzora: studenti se sami registriraju, nema
 * usmenih uputa i nema nikoga da pomogne. Zato ekran nosi DVIJE stvari koje
 * prije nije imao:
 *  1. informaciju sudionika (iznad polja) — jedina točka kroz koju sudionik
 *     prođe PRIJE nego se prikupi ijedan podatak,
 *  2. pomoć uz `username` — jer se username prikazuje na JAVNOJ ljestvici
 *     (4.5a), a to mu dotad nigdje nije bilo rečeno.
 * Oba teksta žive u `lib/participation.ts` — ne inline, jer idu u rad i mijenjaju
 * se uz odluku, ne u prolazu.
 */
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link } from "react-router-dom"
import { toast } from "sonner"
import { Info, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { useAuth } from "@/hooks/useAuth"
import { AuthError } from "@/lib/auth/api"
import {
  KONTAKT,
  SUDJELOVANJE_KONTAKT_UVOD,
  SUDJELOVANJE_NASLOV,
  SUDJELOVANJE_ODLOMCI,
  USERNAME_POMOC,
} from "@/lib/participation"

const registerSchema = z.object({
  username: z
    .string()
    .min(3, "Korisničko ime mora imati bar 3 znaka")
    .max(50, "Korisničko ime može imati najviše 50 znakova"),
  email: z.email("Unesi ispravnu email adresu"),
  password: z.string().min(8, "Lozinka mora imati bar 8 znakova"),
})

type RegisterValues = z.infer<typeof registerSchema>

export function RegisterPage() {
  const { register: registerUser } = useAuth()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: "", email: "", password: "" },
  })

  const onSubmit = async (values: RegisterValues) => {
    try {
      await registerUser(values.username, values.email, values.password)
      // Redirect radi PublicOnlyRoute (status → authed → Navigate na "/").
    } catch (err) {
      let message = "Registracija nije uspjela — pokušaj ponovno."
      if (err instanceof AuthError) {
        if (err.status === 409) {
          message = "Korisničko ime ili email već postoji."
        } else if (err.status === 422) {
          message = "Neispravni podaci — provjeri unesena polja."
        }
      }
      setError("root", { message })
      toast.error(message)
    }
  }

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      {/* max-w-md (ne -sm kao Login): info blok nosi pet odlomaka — u 384px
          bi se slomio u uski stup teksta. min-h-svh (ne h-svh) → na niskom
          zaslonu kartica raste i stranica skrola, sadržaj se ne reže. */}
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-xl">Registracija</CardTitle>
          <CardDescription>
            Novi račun — uloga je uvijek student.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Informacija sudionika — ISPOD naslova, IZNAD polja: asinkroni eval
              bez nadzora nema usmenih uputa, a ovo je jedina točka kroz koju
              sudionik prođe prije nego se prikupi ijedan podatak.
              Tekst živi u lib/participation.ts (jedan odlomak = jedna izmjena).
              <section> + aria-labelledby → čitač ekrana ga najavljuje kao
              cjelinu, ne kao odlutali tekst iznad forme. */}
          <section
            aria-labelledby="sudjelovanje-naslov"
            className="mb-6 space-y-2 rounded-lg border border-border bg-muted/40 p-4"
          >
            <h2
              id="sudjelovanje-naslov"
              className="flex items-center gap-1.5 text-sm font-semibold"
            >
              <Info aria-hidden="true" className="size-4 shrink-0" />
              {SUDJELOVANJE_NASLOV}
            </h2>
            {/* 🔴 `text-foreground`, NE `text-muted-foreground`, i `text-sm`, NE
                `text-xs`. Izmjereno 2026-07-26 (alpha-kompozitirano vs card):
                muted-foreground na bg-muted/40 daje 4.57:1 light / 6.43:1 dark —
                light PROLAZI AA za 12px tekst, ali s marginom 1.5 %. Za tekst
                koji sudionik MORA pročitati to je pretanko, a `text-xs` + siva
                je točno obrazac „sitni sivi tekst suglasnosti".
                S `text-foreground`: 19.13:1 light / 15.97:1 dark. */}
            {SUDJELOVANJE_ODLOMCI.map((odlomak) => (
              <p key={odlomak} className="text-sm leading-relaxed">
                {odlomak}
              </p>
            ))}
            <p className="text-sm leading-relaxed">
              {SUDJELOVANJE_KONTAKT_UVOD}{" "}
              <a
                href={`mailto:${KONTAKT}`}
                className="rounded-sm font-medium underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
              >
                {KONTAKT}
              </a>
            </p>
          </section>

          <form
            onSubmit={handleSubmit(onSubmit)}
            className="space-y-4"
            noValidate
          >
            <div className="space-y-2">
              <Label htmlFor="username">Korisničko ime</Label>
              <Input
                id="username"
                autoComplete="username"
                aria-invalid={!!errors.username}
                // Pomoć je vezana PROGRAMATSKI (ne samo vizualno): bez ovoga je
                // čitač ekrana nikad ne pročita, a upozorenje o javnoj ljestvici
                // je upravo ono što sudionik mora čuti PRIJE unosa.
                aria-describedby="username-pomoc"
                {...register("username")}
              />
              {/* `text-sm`, ne `text-xs`: nakon što je info blok podignut na
                  text-sm/foreground, ova je pomoć na snimci (2026-07-26) ostala
                  NAJSLABIJI tekst na ekranu — a to je rečenica koja sprječava
                  sudionika da se izloži na javnoj ljestvici.
                  `muted-foreground` ostaje (idiomatska pomoć uz polje) i
                  izmjeren je: 6.91:1 dark / 4.73:1 light vs `card`. */}
              <p id="username-pomoc" className="text-sm text-muted-foreground">
                {USERNAME_POMOC}
              </p>
              {errors.username && (
                <p className="text-sm text-incorrect" role="alert">
                  {errors.username.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                aria-invalid={!!errors.email}
                {...register("email")}
              />
              {errors.email && (
                <p className="text-sm text-incorrect" role="alert">
                  {errors.email.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Lozinka</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                aria-invalid={!!errors.password}
                {...register("password")}
              />
              {errors.password && (
                <p className="text-sm text-incorrect" role="alert">
                  {errors.password.message}
                </p>
              )}
            </div>

            {errors.root && (
              <p
                className="rounded-md bg-incorrect-soft px-3 py-2 text-sm text-incorrect"
                role="alert"
              >
                {errors.root.message}
              </p>
            )}

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting && (
                <Loader2 className="animate-spin" data-icon="inline-start" />
              )}
              {isSubmitting ? "Registracija…" : "Registriraj se"}
            </Button>
          </form>

          <p className="mt-4 text-center text-sm text-muted-foreground">
            Već imaš račun?{" "}
            <Link
              to="/login"
              className="inline-block py-2 font-medium text-foreground underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            >
              Prijavi se
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  )
}
