/**
 * UntrackedConcepts (Faza 4.4b) — koncepti koji NIKAD neće imati krivulju.
 *
 * 🔴 ZAŠTO POSTOJI KAO ZASEBNA SEKCIJA
 * Ovi koncepti NE SMIJU pasti u listu „još nema podataka" — to bi bilo isto
 * obećanje koje je maknuto iz module overviewa u 4.4-0e (NALAZ #10b): tekst koji
 * implicira „riješi zadatke pa će se pojaviti", za koncept čiji zadaci ne
 * postoje ili nisu evaluabilni. Zato: bez bara, bez postotka, bez preduvjeta,
 * bez CTA — samo činjenica i razlog.
 *
 * DVIJE SKUPINE, dva RAZLIČITA razloga (ne spajati u jednu poruku):
 *  (B) izvan opsega evaluacije — M6 (`explain_plan`, `index_usage`); evaluacijska
 *      jezgra ih ne zna ocijeniti pa su zadaci neaktivni (NALAZ #19).
 *  (C) strukturni/glue koncepti modula 0 (`join_condition`, `column_alias`) —
 *      po dizajnu nemaju vlastite zadatke; pojavljuju se kao dio drugih.
 *
 * Pripadnost se IZVODI iz `primary_task_count` + broja modula (lib/mastery-history),
 * nikad iz hardkodiranog popisa kodova.
 *
 * 🔴 OVDJE ZAVRŠAVAJU SAMO KONCEPTI BEZ IJEDNE TOČKE. Koncept iz (B)/(C) koji
 * JEST skupio BKT povijest (npr. `column_alias` kroz sekundarno pojavljivanje u
 * 4 aktivna zadatka) dobiva punu krivulju u mreži — izmjereni podatak
 * nadjačava kategoriju, inače bi tekst ispod lagao o vlastitim podacima.
 */
import { Info } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type { CategorizedConcept } from "@/lib/mastery-history"

interface UntrackedConceptsProps {
  outOfScope: CategorizedConcept[]
  structural: CategorizedConcept[]
}

function ConceptList({ concepts }: { concepts: CategorizedConcept[] }) {
  return (
    <ul className="flex flex-wrap gap-1.5">
      {concepts.map((concept) => (
        <li
          key={concept.code}
          className="rounded-md border border-border bg-muted/40 px-2 py-1 text-xs text-muted-foreground"
        >
          {concept.name}
        </li>
      ))}
    </ul>
  )
}

export function UntrackedConcepts({
  outOfScope,
  structural,
}: UntrackedConceptsProps) {
  if (outOfScope.length === 0 && structural.length === 0) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Info className="size-4 text-muted-foreground" aria-hidden="true" />
          Koncepti bez krivulje
        </CardTitle>
        <CardDescription>
          Za ove se koncepte napredak ne mjeri — nisu izostavljeni greškom.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {structural.length > 0 && (
          <div className="space-y-1.5">
            <h3 className="text-sm font-medium">
              Strukturni koncepti bez vlastitih zadataka
            </h3>
            <p className="text-xs text-muted-foreground">
              Nemaju vlastite zadatke — vježbaju se kao dio drugih. Krivulja se
              pojavi tek ako ih neki riješeni zadatak dodirne.
            </p>
            <ConceptList concepts={structural} />
          </div>
        )}
        {outOfScope.length > 0 && (
          <div className="space-y-1.5">
            <h3 className="text-sm font-medium">Izvan opsega ove verzije</h3>
            <p className="text-xs text-muted-foreground">
              Sustav još ne zna automatski ocijeniti rješenja ovih koncepata, pa
              njihovi zadaci nisu aktivni.
            </p>
            <ConceptList concepts={outOfScope} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
