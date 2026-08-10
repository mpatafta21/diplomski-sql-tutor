/**
 * Sheet (Faza 4.7-1C) — bočni panel nad `radix-ui` Dialogom.
 *
 * 🔴 BEZ NOVE OVISNOSTI: `radix-ui@1.6.1` je već u `package.json` i već se koristi
 * (`Collapsible` u ModuleCard, `Slot` u Buttonu). Uzima se isti obrazac uvoza.
 *
 * Radix Dialog donosi ono što je za drawer a11y-kritično i što se ručno griješi:
 *   • fokus-trap unutar panela          • `Esc` zatvara
 *   • fokus se VRAĆA na trigger         • `aria-modal` + `aria-labelledby`
 *   • pozadina dobiva `aria-hidden`     • scroll-lock na <body>
 * Zato se ne piše ručno.
 */
import type { ComponentProps } from "react"
import { Dialog } from "radix-ui"
import { XIcon } from "lucide-react"
import { cn } from "@/lib/utils"

const Sheet = Dialog.Root
const SheetTrigger = Dialog.Trigger
const SheetClose = Dialog.Close
const SheetTitle = Dialog.Title
const SheetDescription = Dialog.Description

function SheetContent({
  className,
  children,
  side = "left",
  ...props
}: ComponentProps<typeof Dialog.Content> & { side?: "left" | "right" }) {
  return (
    <Dialog.Portal>
      <Dialog.Overlay
        className={cn(
          "fixed inset-0 z-50 bg-background/80",
          // `tw-animate-css` — isti izvor motiona kao ostatak aplikacije.
          "data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:duration-base",
          "data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:duration-fast",
          "ease-standard motion-reduce:animate-none",
        )}
      />
      <Dialog.Content
        className={cn(
          // Gradijent plohe (A.2a): isti par kao desktop sidebar u AppShellu,
          // da se plohe drawera i sidebara ne raziđu.
          "fixed inset-y-0 z-50 flex w-[min(20rem,85vw)] flex-col border-sidebar-border bg-sidebar bg-[image:var(--grad-sidebar)]",
          side === "left" ? "left-0 border-r" : "right-0 border-l",
          "data-[state=open]:animate-in data-[state=closed]:animate-out",
          side === "left"
            ? "data-[state=open]:slide-in-from-left data-[state=closed]:slide-out-to-left"
            : "data-[state=open]:slide-in-from-right data-[state=closed]:slide-out-to-right",
          // 🔴 IZLAZ JE BRŽI OD ULAZA (240 → 160 ms). Ulaz je trenutak kad korisnik
          // ČEKA da vidi sadržaj, pa smije disati; izlaz je trenutak kad je već
          // odlučio otići, pa svako zadržavanje čita kao tromost.
          "data-[state=open]:duration-base data-[state=closed]:duration-fast",
          "ease-standard motion-reduce:animate-none",
          className,
        )}
        {...props}
      >
        {children}
        <Dialog.Close
          // Invarijanta (WCAG 2.5.5): 44px touch target.
          className={cn(
            "absolute top-3 right-3 flex size-11 items-center justify-center rounded-lg",
            "text-muted-foreground transition-colors duration-fast ease-standard",
            "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            // Pritisak mora imati odgovor — inače gumb djeluje kao da nije čuo.
            // Isti obrazac kao `ui/button.tsx` (`active:translate-y-px`), samo je
            // ovdje ikona pa skala čita bolje od pomaka.
            "active:scale-[0.97]",
            "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
            "motion-reduce:transition-none",
          )}
        >
          <XIcon className="size-5" aria-hidden="true" />
          <span className="sr-only">Zatvori izbornik</span>
        </Dialog.Close>
      </Dialog.Content>
    </Dialog.Portal>
  )
}

export {
  Sheet,
  SheetTrigger,
  SheetClose,
  SheetContent,
  SheetTitle,
  SheetDescription,
}
