// Adaptirano: shadcn stub pretpostavlja next-themes (Next.js) — mi smo Vite.
// 🔴 `theme` prop MORA ostati eksplicitan: sonnerov default je "light", pa bi izostavljen
// prop dao svijetli toast usred tamne aplikacije. Ovisnosti o mehanizmu tema više nema —
// `sonner@2` nema `next-themes` ni u dependencies ni u peerDependencies (provjereno
// 2026-08-10), pa uklanjanje ThemeProvidera ovdje traži jedan literal, ne mehanizam.
import { Toaster as Sonner, type ToasterProps } from "sonner"
import { CircleCheckIcon, InfoIcon, TriangleAlertIcon, OctagonXIcon, Loader2Icon } from "lucide-react"

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="dark"
      className="toaster group"
      icons={{
        success: (
          <CircleCheckIcon className="size-4" />
        ),
        info: (
          <InfoIcon className="size-4" />
        ),
        warning: (
          <TriangleAlertIcon className="size-4" />
        ),
        error: (
          <OctagonXIcon className="size-4" />
        ),
        loading: (
          <Loader2Icon className="size-4 animate-spin" />
        ),
      }}
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
          "--border-radius": "var(--radius)",
        } as React.CSSProperties
      }
      toastOptions={{
        classNames: {
          toast: "cn-toast",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
