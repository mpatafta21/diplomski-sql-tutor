import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "radix-ui"

import { cn } from "@/lib/utils"

/**
 * ⟳ 2026-08-11 (zatvaranje 4.7, A.1c): dodani `duration-instant` + `ease-standard`.
 * 🔴 RAZLOG NIJE ESTETIKA nego POSLJEDICA N-18 popravka: `--tw-duration` je
 * NASLJEDNA varijabla, pa je gumb unutar kartice (`duration-base`) nasljeđivao
 * 240 ms i press feedback (`active:translate-y-px`) postao je trom — izmjereno
 * `getComputedStyle` = 0,24 s na gumbu BEZ ijedne klase trajanja.
 * MASTER §5 `--duration-instant` je ionako namijenjen „hover, press".
 */
const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center rounded-lg border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap transition-all duration-instant ease-standard outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive/50 aria-invalid:ring-3 aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/80",
        // 4.7 dark-only: `dark:border-input dark:bg-input/30 dark:hover:bg-input/50`
        // GAZILE su light vrijednosti `border-border bg-background hover:bg-muted`.
        // Prefiks se ne briše — briše se PREGAŽENA light grana, inače ostaje mrtav CSS
        // koji izgleda kao namjera.
        outline:
          "border-input bg-input/30 hover:bg-input/50 hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-[color-mix(in_oklch,var(--secondary),var(--foreground)_5%)] aria-expanded:bg-secondary aria-expanded:text-secondary-foreground",
        ghost:
          "hover:bg-muted/50 hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground",
        // ⚠️ MRTVA VARIJANTA — `grep -rn 'variant="destructive"' frontend/src` daje 0
        // pogodaka (provjereno 2026-08-10). ZADRŽANA namjerno, isti obrazac kao
        // `--duration-reward` i `verdict-ui.ts` `soft`: cjelovitost skupa varijanti
        // (`default`/`outline`/`secondary`/`ghost`/`destructive`/`link`) nije najava
        // rada. Ako ikad dobije potrošača, treba je izmjeriti — `--destructive` je u
        // ERRATA #52 (jedini dosežni render je danas obrub nevaljanog polja).
        destructive:
          "bg-destructive/20 text-destructive hover:bg-destructive/30 focus-visible:border-destructive/40 focus-visible:ring-destructive/40",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        // Invarijanta (WCAG 2.5.5): default/lg/icon/icon-lg ≥44px touch target.
        // xs/sm/icon-xs/icon-sm su svjesni escape-hatch za gusti sekundarni UI — NE za primarne akcije.
        default:
          "h-11 gap-1.5 px-4 has-data-[icon=inline-end]:pr-3 has-data-[icon=inline-start]:pl-3",
        xs: "h-6 gap-1 rounded-[min(var(--radius-md),10px)] px-2 text-xs in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-7 gap-1 rounded-[min(var(--radius-md),12px)] px-2.5 text-[0.8rem] in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3.5",
        lg: "h-12 gap-1.5 px-5 has-data-[icon=inline-end]:pr-3 has-data-[icon=inline-start]:pl-3",
        icon: "size-11",
        "icon-xs":
          "size-6 rounded-[min(var(--radius-md),10px)] in-data-[slot=button-group]:rounded-lg [&_svg:not([class*='size-'])]:size-3",
        "icon-sm":
          "size-7 rounded-[min(var(--radius-md),12px)] in-data-[slot=button-group]:rounded-lg",
        "icon-lg": "size-12",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot.Root : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
