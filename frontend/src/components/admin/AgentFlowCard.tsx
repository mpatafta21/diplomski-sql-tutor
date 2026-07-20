/**
 * AgentFlowCard (Faza 4.5b) — JEDAN `correlation_id` tok kao vremenska linija.
 *
 * Ovo je artefakt za obranu: otvoriš jedan tok i vidi se lanac
 * RECEIVE → EVALUATE → UPDATE → RECOMMEND → RESPOND, s performativom,
 * pošiljateljem, primateljem, vremenom i sadržajem svake poruke.
 *
 * 🔴 DUPLIKATI SU OZNAČENI, NE SKRIVENI (NALAZ #34) — vidi lib/agent-logs.ts.
 * 🔴 Sadržaj ide u mono blok s `whitespace-pre` + vlastitim `overflow-x`
 * (obrazac iz 4.3b RunResultPanela): dugačak JSON ne smije razvući layout
 * stranice.
 */
import { useState } from "react"
import { ArrowRight, ChevronDown, Copy } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  agentName,
  formatContent,
  type AgentFlow,
  type FlowEntry,
} from "@/lib/agent-logs"
import { cn } from "@/lib/utils"

/** hr-HR, do sekunde + milisekunde: poruke unutar toka su milisekunde razmaknute. */
const TIME_FMT = new Intl.DateTimeFormat("hr-HR", {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
})

function timeOf(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return "—"
  const ms = String(d.getMilliseconds()).padStart(3, "0")
  return `${TIME_FMT.format(d)}.${ms}`
}

/** Performativ → token boje. FIPA performativi su KATEGORIJE, ne ocjene —
 *  namjerno neutralna/chart paleta, nikad correct/incorrect semantika. */
const PERFORMATIVE_CLASS: Record<string, string> = {
  request: "border-chart-1/40 text-chart-1",
  inform: "border-chart-2/40 text-chart-2",
}

function LogEntry({ entry }: { entry: FlowEntry }) {
  const [open, setOpen] = useState(false)
  const { item, isDuplicate } = entry

  return (
    <li className="border-t border-border/60 first:border-t-0">
      <div className="flex flex-wrap items-center gap-2 px-3 py-2">
        <span className="font-mono text-xs tabular-nums text-muted-foreground">
          {timeOf(item.created_at)}
        </span>

        <span
          className={cn(
            "rounded-md border px-1.5 py-0.5 font-mono text-[0.7rem] font-medium",
            PERFORMATIVE_CLASS[item.performative] ??
              "border-border text-muted-foreground",
          )}
        >
          {item.performative}
        </span>

        <span className="flex items-center gap-1 text-xs">
          <span className="font-medium">{agentName(item.sender)}</span>
          <ArrowRight
            className="size-3 text-muted-foreground"
            aria-hidden="true"
          />
          <span className="font-medium">{agentName(item.receiver)}</span>
        </span>

        {/* 🔴 Duplikat se OZNAČAVA, ne skriva (NALAZ #34). */}
        {isDuplicate && (
          <span
            className="rounded-md border border-accent-warm/40 px-1.5 py-0.5 text-[0.7rem] text-accent-warm-text"
            title="Identičan zapis već postoji u ovom toku — zabilježen je dvaput"
          >
            duplikat zabilježenog prometa
          </span>
        )}

        <Button
          variant="ghost"
          size="sm"
          className="ml-auto"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
        >
          Sadržaj
          <ChevronDown
            data-icon="inline-end"
            aria-hidden="true"
            className={cn(
              "transition-transform duration-fast motion-reduce:transition-none",
              open && "rotate-180",
            )}
          />
        </Button>
      </div>

      {open && (
        <div className="px-3 pb-3">
          {/* Vlastiti overflow-x — dugačak JSON scrolla U SEBI, ne razvlači stranicu. */}
          <pre className="max-h-72 overflow-auto rounded-lg border border-border bg-muted/40 p-3 font-mono text-xs whitespace-pre">
            {formatContent(item.content)}
          </pre>
        </div>
      )}
    </li>
  )
}

export function AgentFlowCard({ flow }: { flow: AgentFlow }) {
  const cid = flow.correlationId
  const copyCid = () => {
    if (cid) void navigator.clipboard?.writeText(cid)
  }

  return (
    <Card>
      <CardHeader className="gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted-foreground">correlation_id</span>
          <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
            {cid ?? "(bez correlation_id)"}
          </code>
          {cid && (
            <Button
              variant="ghost"
              size="sm"
              onClick={copyCid}
              aria-label={`Kopiraj correlation_id ${cid}`}
            >
              <Copy aria-hidden="true" />
            </Button>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          <span className="tabular-nums">{flow.entries.length}</span>{" "}
          {flow.entries.length === 1 ? "poruka" : "poruka"} ·{" "}
          {flow.participants.join(" · ")}
          {flow.duplicateCount > 0 && (
            <>
              {" · "}
              <span className="text-accent-warm-text">
                {flow.duplicateCount} duplikata
              </span>
            </>
          )}
        </p>
      </CardHeader>
      <CardContent>
        <ol className="rounded-lg border border-border">
          {flow.entries.map((entry) => (
            <LogEntry key={entry.item.id} entry={entry} />
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}
