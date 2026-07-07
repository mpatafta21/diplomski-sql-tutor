/**
 * LoginPage (Faza 4.1c) — prijava po USERNAME + password (invarijanta #4, NE email).
 * RHF + zod v4; submit ide kroz useAuth.login() (B1 api.ts rješava form-encoding).
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

const loginSchema = z.object({
  username: z.string().min(1, "Unesi korisničko ime"),
  password: z.string().min(1, "Unesi lozinku"),
})

type LoginValues = z.infer<typeof loginSchema>

export function LoginPage() {
  const { login } = useAuth()
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  })

  const onSubmit = async (values: LoginValues) => {
    try {
      await login(values.username, values.password)
      // Redirect radi PublicOnlyRoute (status → authed → Navigate na "/").
    } catch (err) {
      const message =
        err instanceof AuthError && err.status === 401
          ? "Neispravno korisničko ime ili lozinka."
          : "Prijava nije uspjela — pokušaj ponovno."
      setError("root", { message })
      toast.error(message)
    }
  }

  return (
    <main className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-xl">Prijava</CardTitle>
          <CardDescription>
            SQL Tutor — prijavi se korisničkim imenom.
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
              <Label htmlFor="password">Lozinka</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
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
              {isSubmitting ? "Prijava…" : "Prijavi se"}
            </Button>
          </form>

          <p className="mt-4 text-center text-sm text-muted-foreground">
            Nemaš račun?{" "}
            <Link
              to="/register"
              className="inline-block py-2 font-medium text-foreground underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            >
              Registriraj se
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  )
}
