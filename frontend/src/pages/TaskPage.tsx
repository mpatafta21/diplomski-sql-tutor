/**
 * TaskPage (Faza 4.3a) — Task screen, statika + editor (Run/Submit žice 4.3b/c).
 *
 * Layout: split — lijevo opis zadatka + shema referenca, desno Monaco editor.
 * Editor je primarna radna površina → dobiva širi stupac (xl:5fr/7fr);
 * ispod xl se slaže vertikalno (opis prvo, editor ispod).
 *
 * 🔴 NALAZ #7: breadcrumb modul se izvodi IZ PRIMARNOG KONCEPTA
 * (concepts[is_primary] → buildConceptIndex → moduleName), NIKAD iz
 * task.module_id — on je KRIV za 3/83 taskova (71–73: module_id kaže
 * "DML operacije", a primarni koncept correlated_subquery je u "Podupiti").
 */
import { useCallback, useMemo, useRef, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { ChevronRight, Clock, Play, Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Kbd } from "@/components/ui/kbd"
import { Skeleton } from "@/components/ui/skeleton"
import { ConceptChip } from "@/components/ConceptChip"
import { TaskDifficultyChip } from "@/components/task/TaskDifficultyChip"
import { SchemaReference } from "@/components/task/SchemaReference"
import { SqlEditor } from "@/components/task/SqlEditor"
import { RunResultPanel } from "@/components/task/RunResultPanel"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import { useModules } from "@/hooks/useModules"
import { useRun } from "@/hooks/useRun"
import { useTask } from "@/hooks/useTask"
import { useTheme } from "@/hooks/useTheme"
import type { RunResponse, TaskDetailResponse } from "@/lib/api/types"
import { buildConceptIndex, type ConceptInfo } from "@/lib/mastery"

const INITIAL_QUERY = "-- Napiši svoj SQL upit ovdje\n"

// Platform-aware oznaka prečaca: monaco KeyMod.CtrlCmd je ⌘ na macOS-u —
// label i aria-keyshortcuts moraju reći isto što tipka stvarno radi.
const IS_MAC = /Mac|iP(hone|ad|od)/.test(navigator.platform)
const RUN_KBD = IS_MAC ? "⌘ ↵" : "Ctrl ↵"
const RUN_ARIA = IS_MAC ? "Meta+Enter" : "Control+Enter"

export function TaskPage() {
  const { taskId } = useParams()
  // Kanonski ID: samo znamenke ("0x2A"/"1e2"/" 5" bi kroz Number() aliasirali
  // drugi task pod istim query keyem umjesto da padnu u invalid granu).
  const validId = /^\d+$/.test(taskId ?? "") && Number(taskId) > 0
  const parsed = Number(taskId)

  const taskQ = useTask(validId ? parsed : null)
  const modulesQ = useModules()

  // useMemo PRIJE early returnova (rules of hooks — isti obrazac kao
  // ModulesPage): bez toga se Map rebuilda na svaki keystroke u editoru.
  const conceptIndex = useMemo(
    () => (modulesQ.data ? buildConceptIndex(modulesQ.data) : null),
    [modulesQ.data],
  )

  if (!validId) {
    return (
      <ErrorState
        title="Zadatak ne postoji"
        message={`"${taskId}" nije valjan ID zadatka.`}
      />
    )
  }

  if (taskQ.isPending || modulesQ.isPending) {
    // Skeleton zrcali finalni grid — bez layout shifta kad podaci stignu.
    return (
      <div className="grid gap-6 xl:grid-cols-[minmax(360px,5fr)_7fr]">
        <div className="space-y-6">
          <LoadingState lines={6} label="Učitavanje zadatka" />
        </div>
        <Skeleton className="h-[480px]" />
      </div>
    )
  }

  if (taskQ.isError || modulesQ.isError) {
    return (
      <ErrorState
        title="Zadatak nije učitan"
        message="Provjeri vezu ili pokušaj ponovno — možda zadatak ne postoji."
        onRetry={() => {
          void taskQ.refetch()
          void modulesQ.refetch()
        }}
      />
    )
  }

  // key={task.id}: promjena :taskId NE remounta TaskPage (isti route element) —
  // key resetira per-task stanje (SQL u editoru, zadnji Run rezultat) da ne
  // procuri iz prethodnog zadatka u sljedeći.
  return (
    <TaskView
      key={taskQ.data.id}
      task={taskQ.data}
      conceptIndex={conceptIndex}
    />
  )
}

interface TaskViewProps {
  task: TaskDetailResponse
  conceptIndex: Map<string, ConceptInfo> | null
}

function TaskView({ task, conceptIndex }: TaskViewProps) {
  const { dark } = useTheme()
  const runM = useRun(task.id)
  const { mutate } = runM // v5: mutate je referencijski stabilan
  const [query, setQuery] = useState(INITIAL_QUERY)
  // Zadnji USPJEŠNI rezultat: mutation.data se briše na svaki mutate() (v5
  // pending reset) — bez ovoga bi se na svaki re-Run bljesnuo skeleton preko
  // postojeće tablice (flash-of-skeleton na frekventnoj akciji).
  const [lastResult, setLastResult] = useState<RunResponse>()
  // Zadnji POSLANI upit — retry ponavlja NJEGA (ne trenutni sadržaj editora,
  // koji je u međuvremenu mogao biti obrisan → retry ne smije biti tihi no-op).
  const lastQueryRef = useRef("")

  // Client-side guard: prazan/whitespace upit se NE šalje (nula requestova).
  const canRun = query.trim().length > 0 && !runM.isPending
  const handleRun = () => {
    // Guard i ovdje (ne samo na gumbu) — Ctrl/Cmd+Enter iz editora ga zaobilazi.
    if (!canRun) return
    lastQueryRef.current = query
    mutate(query, { onSuccess: setLastResult })
  }
  // Stabilan identitet (memo na RunResultPanelu se oslanja na ovo — inače bi
  // se tablica do 200 redaka rekoncilirala na svaki keystroke u editoru).
  const retryRun = useCallback(() => {
    const q = lastQueryRef.current
    if (!q.trim()) return
    mutate(q, { onSuccess: setLastResult })
  }, [mutate])

  // 🔴 NALAZ #7 — modul IZ PRIMARNOG KONCEPTA, ne iz task.module_id.
  const primary = task.concepts.find((c) => c.is_primary)
  const primaryInfo = primary ? conceptIndex?.get(primary.code) : undefined
  const secondary = task.concepts.filter((c) => !c.is_primary)
  const estMin = task.estimated_time_sec
    ? Math.max(1, Math.round(task.estimated_time_sec / 60))
    : null

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(360px,5fr)_7fr]">
      {/* ── Lijevi panel: opis + shema ─────────────────────────────── */}
      <div className="min-w-0 space-y-6">
        <nav aria-label="Putanja">
          {/* Separatori žive u <li aria-hidden> — <ol> smije imati samo <li>
              djecu, a chevron se renderira SAMO iza postojeće stavke (bez
              visećeg '›' kad task nema primarni koncept). */}
          <ol className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
            {primaryInfo && (
              <>
                <li>
                  <Link
                    to="/modules"
                    className="rounded-sm underline-offset-4 hover:text-foreground hover:underline focus-visible:outline-2 focus-visible:outline-ring"
                  >
                    {primaryInfo.moduleName}
                  </Link>
                </li>
                <li aria-hidden="true">
                  <ChevronRight className="size-3" />
                </li>
              </>
            )}
            {primary && (
              <>
                <li>{primary.name}</li>
                <li aria-hidden="true">
                  <ChevronRight className="size-3" />
                </li>
              </>
            )}
            <li aria-current="page" className="text-foreground">
              Zadatak #{task.id}
            </li>
          </ol>
        </nav>

        <header className="space-y-3">
          <h1 className="text-2xl font-semibold tracking-tight text-balance">
            {task.title}
          </h1>
          <div className="flex flex-wrap items-center gap-2">
            <TaskDifficultyChip difficulty={task.difficulty} />
            {primary && primaryInfo && (
              <ConceptChip name={primary.name} tier={primaryInfo.tier} />
            )}
            {estMin !== null && (
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <Clock aria-hidden="true" className="size-3.5" />~{estMin} min
              </span>
            )}
          </div>
        </header>

        <p className="max-w-prose text-[0.9375rem] leading-relaxed">
          {task.description}
        </p>

        {secondary.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted-foreground">Usput vježba:</span>
            {secondary.map((c) => {
              const info = conceptIndex?.get(c.code)
              return (
                <ConceptChip
                  key={c.code}
                  name={c.name}
                  tier={info?.tier ?? ""}
                />
              )
            })}
          </div>
        )}

        <Card>
          <CardContent className="px-4 py-3">
            <SchemaReference />
          </CardContent>
        </Card>
      </div>

      {/* ── Desni panel: Monaco editor + Run/Submit ────────────────── */}
      <Card className="min-w-0 self-start">
        <CardContent className="space-y-3 p-4">
          {/* focus-within prsten: Monaco fokus mora biti vidljiv i na kontejneru (MASTER §7). */}
          <div className="h-[420px] overflow-hidden rounded-md border border-border transition-[border-color,box-shadow] duration-fast ease-standard focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/40 motion-reduce:transition-none xl:h-[520px]">
            {/* ⚠️ onRun od PRVOG rendera — monaco akcije se registriraju na mountu. */}
            <SqlEditor
              value={query}
              onChange={setQuery}
              dark={dark}
              onRun={handleRun}
            />
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-muted-foreground">
              Predaja rješenja (Submit) aktivira se u sljedećem koraku.
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                disabled={!canRun}
                onClick={handleRun}
                aria-keyshortcuts={RUN_ARIA}
              >
                <Play data-icon="inline-start" aria-hidden="true" />
                Run
                <Kbd aria-hidden="true">{RUN_KBD}</Kbd>
              </Button>
              {/* Submit žice 4.3c (/attempt). */}
              <Button disabled aria-keyshortcuts="Shift+Enter">
                <Send data-icon="inline-start" aria-hidden="true" />
                Submit
                <Kbd aria-hidden="true">Shift ↵</Kbd>
              </Button>
            </div>
          </div>
          <RunResultPanel
            result={lastResult}
            isPending={runM.isPending}
            infraError={runM.isError}
            onRetry={retryRun}
            runKbd={RUN_KBD}
          />
        </CardContent>
      </Card>
    </div>
  )
}
