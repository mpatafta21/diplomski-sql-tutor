/**
 * ModuleCard (Faza 4.2b) — kartica modula: difficulty chip (MODUL skala,
 * MASTER.md §2.5), "X/Y savladano" + agregatni MasteryBar, te Collapsible
 * detalj s konceptima (in-place expand — svi podaci već stigli jednim
 * /modules fetchom pa ruta ne bi donijela ništa osim novih loading stanja).
 */
import { useState } from "react"
import { ChevronDown } from "lucide-react"
import { Collapsible } from "radix-ui"
import {
  Card,
  CardContent,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { DifficultyChip } from "@/components/DifficultyChip"
import { MasteryBar } from "@/components/MasteryBar"
import { ConceptRow } from "@/components/modules/ConceptRow"
import { masteryFillClass } from "@/lib/mastery"
import type { ModuleProgress } from "@/lib/progress"
import { cn } from "@/lib/utils"

export function ModuleCard({ progress }: { progress: ModuleProgress }) {
  const [open, setOpen] = useState(false)
  const { module, concepts, masteredCount, totalCount, availableCount } =
    progress
  const fraction = totalCount > 0 ? masteredCount / totalCount : 0
  // NALAZ #19: modul bez ijednog koncepta s aktivnim zadacima je IZVAN OPSEGA.
  // "0 / N savladano" + bar bi implicirali dostižnost koje nema.
  const outOfScope = availableCount === 0

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{module.name}</CardTitle>
        <CardAction>
          <DifficultyChip difficulty={module.difficulty} />
        </CardAction>
        {/* description je nullable — bez opisa ne renderiramo prazan red. */}
        {module.description !== null && (
          <CardDescription>{module.description}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {outOfScope ? (
          <p className="text-sm text-muted-foreground">
            Nema dostupnih zadataka — modul je izvan opsega ove verzije.
          </p>
        ) : (
          <div className="space-y-1.5">
            <div className="flex items-baseline justify-between">
              <span className="text-sm text-muted-foreground">
                <span className="font-medium text-foreground tabular-nums">
                  {masteredCount}
                </span>
                {" / "}
                <span className="tabular-nums">{totalCount}</span> koncepata
                savladano
              </span>
            </div>
            <MasteryBar
              value={fraction}
              fillClass={masteryFillClass(fraction)}
              label={`${module.name}: savladano ${masteredCount} od ${totalCount} koncepata`}
            />
          </div>
        )}

        <Collapsible.Root open={open} onOpenChange={setOpen}>
          <Collapsible.Trigger asChild>
            <Button
              variant="ghost"
              className="w-full justify-between"
              aria-label={`Koncepti modula ${module.name}`}
            >
              Koncepti
              <ChevronDown
                data-icon="inline-end"
                aria-hidden="true"
                className={cn(
                  "transition-transform duration-fast ease-standard motion-reduce:transition-none",
                  open && "rotate-180",
                )}
              />
            </Button>
          </Collapsible.Trigger>
          <Collapsible.Content>
            <ul className="divide-y divide-border">
              {concepts.map((c) => (
                <ConceptRow key={c.code} concept={c} />
              ))}
            </ul>
          </Collapsible.Content>
        </Collapsible.Root>
      </CardContent>
    </Card>
  )
}
