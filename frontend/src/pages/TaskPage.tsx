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
import { useQueryClient } from "@tanstack/react-query"
import { Link, useParams } from "react-router-dom"
import { CheckCircle2, ChevronRight, Clock, Play, Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Kbd } from "@/components/ui/kbd"
import { Skeleton } from "@/components/ui/skeleton"
import { ConceptChip } from "@/components/ConceptChip"
import { TaskDifficultyChip } from "@/components/task/TaskDifficultyChip"
import { SchemaReference } from "@/components/task/SchemaReference"
import { SqlEditor } from "@/components/task/SqlEditor"
import { RunResultPanel } from "@/components/task/RunResultPanel"
import { FeedbackPanel } from "@/components/task/FeedbackPanel"
import { ApiError } from "@/lib/api/query"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import { useBadges } from "@/hooks/useBadges"
import { useModules } from "@/hooks/useModules"
import { useRun } from "@/hooks/useRun"
import { useSubmitAttempt } from "@/hooks/useSubmitAttempt"
import { useTask } from "@/hooks/useTask"
import { useTheme } from "@/hooks/useTheme"
import type {
  AttemptResponse,
  ProfileResponse,
  RunResponse,
  TaskDetailResponse,
} from "@/lib/api/types"
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

  // ── Submit (4.3c) — SCORED predaja; feedback je per-task (keyed TaskView). ──
  const queryClient = useQueryClient()
  const badgesQ = useBadges()
  const submitM = useSubmitAttempt(task.id)
  const [lastAttempt, setLastAttempt] = useState<AttemptResponse>()
  const [levelUp, setLevelUp] = useState(false)
  const submittedQueryRef = useRef("")

  const canSubmit = query.trim().length > 0 && !submitM.isPending
  const submitQuery = (q: string) => {
    // level_up NEMA flag u odgovoru → prethodni level iz /profile cachea, koji
    // useSubmitAttempt nakon svakog odgovora patcha autoritativnim snapshotom
    // (svjež i bez observera na ovoj ruti). Cache-miss (direktan ulazak na
    // /task bez dashboarda) → bez celebracije (nikad lažni level-up).
    const prevLevel = queryClient.getQueryData<ProfileResponse>([
      "profile",
    ])?.level
    submitM.mutate(q, {
      onSuccess: (data) => {
        setLastAttempt(data)
        // Level-up SAMO uz bodovani pokušaj: level je best-effort read (Gam
        // teče paralelno) — bez xp_delta uvjeta bi zakašnjeli snapshot mogao
        // objesiti "Novi level!" na NETOČAN pokušaj.
        setLevelUp(
          prevLevel != null && data.level > prevLevel && data.xp_delta > 0,
        )
      },
    })
  }
  const handleSubmit = () => {
    // Guard i ovdje — Shift+Enter iz editora zaobilazi disabled gumb.
    if (!canSubmit) return
    submittedQueryRef.current = query
    submitQuery(query)
  }
  // Retry ponavlja zadnju POSLANU predaju (editor mogao biti obrisan u međuvremenu).
  const retrySubmit = () => {
    const q = submittedQueryRef.current
    if (q.trim()) submitQuery(q)
  }

  // Točno jedan slot renderira: v5 status je enum (isError ⇒ !isPending).
  // 504 (agent pipeline ne odgovara) ≠ error_type:"timeout" (200, SQL predug).
  const submitSlot = submitM.isPending
    ? ("pending" as const)
    : submitM.isError
      ? submitM.error instanceof ApiError && submitM.error.status === 504
        ? ("gateway" as const)
        : ("infra" as const)
      : lastAttempt
        ? ("feedback" as const)
        : null

  // code→ime koncepta za CTA (nepoznat code → sirovi code bolji od ničega).
  const conceptName = useCallback(
    (code: string | null | undefined) =>
      code ? (conceptIndex?.get(code)?.name ?? code) : undefined,
    [conceptIndex],
  )

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
                  {/* Deep-link: /modules skrola na modul i otvori mu koncepte. */}
                  <Link
                    to={{
                      pathname: "/modules",
                      hash: `#module-${primaryInfo.moduleNumber}`,
                    }}
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
                <li>
                  {/* Deep-link: /modules otvori modul i istakne redak koncepta. */}
                  <Link
                    to={{
                      pathname: "/modules",
                      hash: `#concept-${primary.code}`,
                    }}
                    className="rounded-sm underline-offset-4 hover:text-foreground hover:underline focus-visible:outline-2 focus-visible:outline-ring"
                  >
                    {primary.name}
                  </Link>
                </li>
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
            {/* Indikator „Riješeno" — task.solved (bilo koji raniji točan pokušaj).
                Ponovni Submit se i dalje smije predati (vježba), ali NE nosi XP;
                to poručuje i FeedbackPanel nakon predaje. */}
            {task.solved && (
              <span className="inline-flex items-center gap-1 rounded-md border border-correct/40 bg-correct-soft px-2 py-0.5 text-xs font-medium text-correct">
                <CheckCircle2 aria-hidden="true" className="size-3.5" />
                Riješeno
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
            {/* ⚠️ onRun/onSubmit od PRVOG rendera — monaco akcije su mount-time. */}
            <SqlEditor
              value={query}
              onChange={setQuery}
              dark={dark}
              onRun={handleRun}
              onSubmit={handleSubmit}
            />
          </div>
          <div className="flex flex-wrap items-center justify-end gap-3">
            <div className="flex items-center gap-2">
              {/* Run = proba bez bodovanja; Submit = scored predaja. */}
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
              <Button
                disabled={!canSubmit}
                onClick={handleSubmit}
                aria-keyshortcuts="Shift+Enter"
              >
                <Send data-icon="inline-start" aria-hidden="true" />
                Submit
                <Kbd aria-hidden="true">Shift ↵</Kbd>
              </Button>
            </div>
          </div>
          {submitSlot === "pending" && (
            <LoadingState
              lines={2}
              label="Ocjenjivanje rješenja"
              className="rounded-md border border-border p-3"
            />
          )}
          {submitSlot === "gateway" && (
            <ErrorState
              title="Sustav ne odgovara"
              message="Evaluacija je predugo trajala — pokušaj ponovno predati."
              onRetry={retrySubmit}
            />
          )}
          {submitSlot === "infra" && (
            <ErrorState
              title="Predaja nije uspjela"
              message="Veza prema poslužitelju nije uspjela — rješenje nije ocijenjeno."
              onRetry={retrySubmit}
            />
          )}
          {submitSlot === "feedback" && lastAttempt && (
            <FeedbackPanel
              attempt={lastAttempt}
              levelUp={levelUp}
              badgeCatalog={badgesQ.data}
              conceptName={conceptName}
            />
          )}
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
