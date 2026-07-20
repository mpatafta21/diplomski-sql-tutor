/**
 * AdminPage (Faza 4.5b) — FIPA agent-log viewer iza `AdminRoute` guarda.
 *
 * 🔴 VOLUMEN: 12 zapisa po attemptu (KORAK 0) → za eval ~7 200 zapisa, a
 * `limit` se TIHO capira na 200 (NALAZ #36). Zato je filter po
 * `correlation_id` PRIMARNI ulaz, a odnos prikazano/ukupno je uvijek vidljiv —
 * prešutjeti cap značilo bi tvrditi da vidiš sve, a ne vidiš.
 *
 * 🔴 FILTRI SU SAMO `correlation_id` i `sender` — ugovor druge nema. Plan §4.5
 * traži i filter po vremenu; on NE POSTOJI i ne izmišlja se klijentski.
 *
 * 🔴 403: ako guard ikad zakaže (ili se rola promijeni u drugom tabu), backend
 * vraća 403 i to se prikazuje kao JASNA PORUKA — nikad crash ni vječni spinner.
 *
 * OPSEG: „osnovne eval-statistike" iz plana §4.5 NISU ovdje (zasebna odluka).
 */
import { useState } from "react"
import { Inbox, Search, SearchX } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Pagination } from "@/components/ui/pagination"
import { EmptyState } from "@/components/state/EmptyState"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import { AgentFlowCard } from "@/components/admin/AgentFlowCard"
import { useAgentLogs, MAX_LIMIT } from "@/hooks/useAgentLogs"
import { groupIntoFlows } from "@/lib/agent-logs"
import { ApiError } from "@/lib/api/query"

const PAGE_SIZE = 50

export function AdminPage() {
  // Odvojeno: ono što je u poljima (draft) vs ono što je poslano (applied).
  // Tipkanje correlation_id-a ne smije okidati zahtjev po znaku.
  const [draftCid, setDraftCid] = useState("")
  const [draftSender, setDraftSender] = useState("")
  const [applied, setApplied] = useState({ cid: "", sender: "" })
  const [offset, setOffset] = useState(0)

  const query = useAgentLogs({
    correlationId: applied.cid || undefined,
    sender: applied.sender || undefined,
    limit: PAGE_SIZE,
    offset,
  })

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    setApplied({ cid: draftCid.trim(), sender: draftSender.trim() })
    setOffset(0)
  }

  const reset = () => {
    setDraftCid("")
    setDraftSender("")
    setApplied({ cid: "", sender: "" })
    setOffset(0)
  }

  const hasFilter = applied.cid !== "" || applied.sender !== ""
  const flows = query.data ? groupIntoFlows(query.data.items) : []
  const forbidden =
    query.error instanceof ApiError && query.error.status === 403

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">
          Administratorski pregled
        </h1>
        <p className="text-sm text-muted-foreground">
          Komunikacija agenata po zadatku — alat za praćenje evaluacije.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Filtri</CardTitle>
          <CardDescription>
            Promet je velik (12 poruka po predanom zadatku) — filtriraj po
            correlation_id-u da vidiš jedan cjelovit tok.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
            <div className="min-w-[16rem] flex-1 space-y-1.5">
              <Label htmlFor="cid">correlation_id</Label>
              <Input
                id="cid"
                value={draftCid}
                onChange={(e) => setDraftCid(e.target.value)}
                placeholder="npr. 3b27bbbf-a398-44af-911a-b67445954c74"
                autoComplete="off"
              />
            </div>
            <div className="min-w-[12rem] flex-1 space-y-1.5">
              <Label htmlFor="sender">sender</Label>
              <Input
                id="sender"
                value={draftSender}
                onChange={(e) => setDraftSender(e.target.value)}
                placeholder="npr. evaluator@localhost"
                autoComplete="off"
              />
            </div>
            <div className="flex items-center gap-2">
              <Button type="submit">
                <Search data-icon="inline-start" aria-hidden="true" />
                Primijeni
              </Button>
              {hasFilter && (
                <Button type="button" variant="outline" onClick={reset}>
                  Poništi
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {query.isPending && (
        <Card aria-busy="true">
          <CardContent>
            <LoadingState lines={5} label="Učitavanje prometa agenata" />
          </CardContent>
        </Card>
      )}

      {/* 403 — guard zaobiđen ili rola promijenjena; jasna poruka, ne crash. */}
      {forbidden && (
        <ErrorState
          title="Nemaš ovlasti za dohvat agentskih logova"
          message="Poslužitelj je odbio zahtjev (403). Ovaj pregled je dostupan samo administratorima."
        />
      )}

      {query.isError && !forbidden && (
        <ErrorState
          title="Logovi nisu dostupni"
          message="Ne mogu dohvatiti promet agenata — pokušaj ponovno."
          onRetry={() => void query.refetch()}
        />
      )}

      {query.isSuccess && (
        <>
          {/* 🔴 Cap MORA biti vidljiv — nikad prešutjeti da se ne vidi sve. */}
          <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
            <p className="text-muted-foreground">
              Prikazano{" "}
              <span className="tabular-nums text-foreground">
                {query.data.items.length}
              </span>{" "}
              od{" "}
              <span className="tabular-nums text-foreground">
                {query.data.total}
              </span>{" "}
              zapisa
              {hasFilter && " (uz filtar)"} ·{" "}
              <span className="tabular-nums">{flows.length}</span>{" "}
              {flows.length === 1 ? "tok" : "tokova"}
            </p>
            {query.data.total > MAX_LIMIT && (
              <p className="text-xs text-accent-warm-text">
                Poslužitelj vraća najviše {MAX_LIMIT} zapisa po zahtjevu — suzi
                filtrom ili prelistaj.
              </p>
            )}
          </div>

          {query.data.total === 0 &&
            // 🔴 Dva RAZLIČITA prazna stanja: nema prometa vs filtar bez pogodaka.
            (hasFilter ? (
              <EmptyState
                icon={SearchX}
                title="Nema zapisa za zadani filtar"
                description="Provjeri correlation_id ili sender — filtar je egzaktan, ne pretražuje djelomično."
                action={
                  <Button variant="outline" onClick={reset}>
                    Poništi filtar
                  </Button>
                }
              />
            ) : (
              <EmptyState
                icon={Inbox}
                title="Još nema zabilježenog prometa"
                description="Čim netko preda zadatak, ovdje se pojavi cijeli lanac poruka između agenata."
              />
            ))}

          <div className="space-y-4">
            {flows.map((flow) => (
              <AgentFlowCard key={flow.correlationId ?? "none"} flow={flow} />
            ))}
          </div>

          {query.data.total > 0 && (
            <Pagination
              total={query.data.total}
              limit={PAGE_SIZE}
              offset={offset}
              onOffsetChange={setOffset}
              label="promet agenata"
            />
          )}
        </>
      )}
    </div>
  )
}
