import { cn } from "@/lib/utils"

/**
 * Kbd (Faza 4.3b) — JEDAN chip za prečace (gumbi + hint u rezultat panelu).
 * Uz gumb s `aria-keyshortcuts` proslijedi `aria-hidden` (vizualni kbd bi
 * ušao u accessible name); u tekstu gdje je prečac SADRŽAJ ostavi vidljivim.
 */
export function Kbd({ className, ...props }: React.ComponentProps<"kbd">) {
  return (
    <kbd
      className={cn(
        "rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[0.65rem] text-muted-foreground",
        className,
      )}
      {...props}
    />
  )
}
