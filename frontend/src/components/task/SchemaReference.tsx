/**
 * SchemaReference (Faza 4.3a) — statička referenca sandbox sheme `ecommerce_v1`.
 *
 * Izvor podataka: lib/sandbox-schema.ts (⚠️ zamrznuti mirror init.sql —
 * guard komentar i SHA tamo). Referenca koju student stalno gleda dok piše
 * upit: tablice su collapsible (otvori onu koju trebaš), identifikatori u
 * mono fontu, FK veze prikazane kao "→ tablica.stupac".
 */
import { memo, useState } from "react"
import { Collapsible } from "radix-ui"
import { ChevronDown, Table2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  SANDBOX_SCHEMA_NAME,
  SANDBOX_TABLES,
  type SchemaTable,
} from "@/lib/sandbox-schema"
import { cn } from "@/lib/utils"

function ColumnBadge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded bg-muted px-1.5 py-0.5 text-[0.65rem] font-medium tracking-wide text-muted-foreground">
      {children}
    </span>
  )
}

function TableEntry({ table }: { table: SchemaTable }) {
  const [open, setOpen] = useState(false)

  return (
    <Collapsible.Root open={open} onOpenChange={setOpen}>
      <Collapsible.Trigger asChild>
        <Button
          variant="ghost"
          className="w-full justify-between px-2"
          aria-label={`Stupci tablice ${table.name}`}
        >
          <span className="flex items-center gap-2">
            <Table2
              aria-hidden="true"
              className="size-4 text-muted-foreground"
            />
            <span className="font-mono text-sm">{table.name}</span>
            <span className="text-xs text-muted-foreground tabular-nums">
              {table.columns.length} stupaca
            </span>
          </span>
          <ChevronDown
            aria-hidden="true"
            className={cn(
              "size-4 shrink-0 transition-transform duration-fast ease-standard motion-reduce:transition-none",
              open && "rotate-180",
            )}
          />
        </Button>
      </Collapsible.Trigger>
      <Collapsible.Content>
        <ul className="mb-1 space-y-0.5 border-l border-border pb-1 pl-4 ml-4">
          {table.columns.map((col) => (
            <li
              key={col.name}
              className="flex flex-wrap items-center gap-x-2 gap-y-0.5 py-0.5 text-sm"
            >
              <span className="font-mono">{col.name}</span>
              <span className="font-mono text-xs text-muted-foreground">
                {col.type}
              </span>
              {col.pk && <ColumnBadge>PK</ColumnBadge>}
              {col.fk && (
                <ColumnBadge>
                  FK <span aria-hidden="true">→</span>
                  <span className="sr-only">referencira</span>
                  <span className="font-mono">{col.fk}</span>
                </ColumnBadge>
              )}
              {col.unique && <ColumnBadge>UNIQUE</ColumnBadge>}
              {col.notNull && !col.pk && (
                <span className="text-[0.65rem] text-muted-foreground">
                  NOT NULL
                </span>
              )}
            </li>
          ))}
          {table.uniques?.map((u) => (
            <li key={u} className="py-0.5 text-xs text-muted-foreground">
              UNIQUE <span className="font-mono">{u}</span>
            </li>
          ))}
        </ul>
      </Collapsible.Content>
    </Collapsible.Root>
  )
}

// memo: čisto statički sadržaj (nema propsa) — TaskPage se re-rendera na svaki
// keystroke u editoru, shema se ne mora rekoncilirati s njim.
export const SchemaReference = memo(function SchemaReference() {
  return (
    <section aria-labelledby="schema-heading" className="space-y-1">
      <div className="flex items-baseline justify-between gap-2 px-2">
        <h2 id="schema-heading" className="text-sm font-semibold">
          Shema baze
        </h2>
        <span className="font-mono text-xs text-muted-foreground">
          {SANDBOX_SCHEMA_NAME}
        </span>
      </div>
      <p className="px-2 text-xs text-muted-foreground">
        Sve tablice dostupne u zadacima — otvori tablicu za popis stupaca.
      </p>
      <div className="divide-y divide-border/50">
        {SANDBOX_TABLES.map((t) => (
          <TableEntry key={t.name} table={t} />
        ))}
      </div>
    </section>
  )
})
