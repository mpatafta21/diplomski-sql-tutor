/**
 * RegisterPage (Faza 4.1c) — username + email + password (invarijanta #4).
 * Client zod pravila su prva obrana (mapiranje po polju); server 409 (duplikat)
 * i 422 dobivaju poruke. B1 registerRequest ne izlaže response detail
 * (username_taken vs email_taken) — svjesno generička 409 poruka, ne diramo B1.
 */
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link } from "react-router-dom"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"
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
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-xl">Registracija</CardTitle>
          <CardDescription>
            Novi račun — uloga je uvijek student.
          </CardDescription>
        </CardHeader>
        <CardContent>
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
                {...register("username")}
              />
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
