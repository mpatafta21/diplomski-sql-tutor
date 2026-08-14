/**
 * Tooltip — tanki omotač oko `radix-ui` Tooltipa (paket je već u ovisnostima od
 * 4.x, ovime se NE dodaje nova).
 *
 * 🔴 Trigger je po defaultu `asChild` i NE postavlja `tabIndex`. Razlog nije
 * previd: jedini potrošač (`ConceptRow`) renderira postotak UNUTAR `<Link>`a koji
 * pokriva cijeli redak, a fokusabilan element unutar linka je ugniježđena
 * interaktivna kontrola (WCAG 4.1.2) i razbija tab redoslijed.
 *
 * Posljedica koju potrošač MORA pokriti: tipkovnica i čitači ekrana ne dohvaćaju
 * sadržaj tooltipa. Zato tekst tooltipa nikad ne smije biti JEDINI nositelj
 * informacije — potrošač uz njega stavlja `sr-only` inačicu (v. ConceptRow).
 * Tooltip je ovdje pojašnjenje za miša i dodir, ne kanal za nove podatke.
 */
import * as React from "react"
import { Tooltip as TooltipPrimitive } from "radix-ui"

import { cn } from "@/lib/utils"

function TooltipProvider({
  delayDuration = 200,
  ...props
}: React.ComponentProps<typeof TooltipPrimitive.Provider>) {
  return <TooltipPrimitive.Provider delayDuration={delayDuration} {...props} />
}

function Tooltip({
  ...props
}: React.ComponentProps<typeof TooltipPrimitive.Root>) {
  // Provider je ugrađen da se ne mora montirati na korijenu aplikacije —
  // Radix ga tolerira ugniježđenog.
  return (
    <TooltipProvider>
      <TooltipPrimitive.Root {...props} />
    </TooltipProvider>
  )
}

function TooltipTrigger({
  ...props
}: React.ComponentProps<typeof TooltipPrimitive.Trigger>) {
  return <TooltipPrimitive.Trigger {...props} />
}

function TooltipContent({
  className,
  sideOffset = 6,
  children,
  ...props
}: React.ComponentProps<typeof TooltipPrimitive.Content>) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        sideOffset={sideOffset}
        className={cn(
          // `card` ploha, ne `popover` — projekt nema popover tokene, a kontrast
          // teksta na `card` je izmjeren kroz cijelu 4.7 matricu.
          "z-50 max-w-xs rounded-md border border-border bg-card px-3 py-2 text-xs leading-relaxed text-foreground shadow-md",
          "animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95",
          "motion-reduce:animate-none",
          className,
        )}
        {...props}
      >
        {children}
        <TooltipPrimitive.Arrow className="fill-border" />
      </TooltipPrimitive.Content>
    </TooltipPrimitive.Portal>
  )
}

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider }
