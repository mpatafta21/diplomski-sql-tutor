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
import {
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock,
  LayoutDashboard,
  Lightbulb,
  MonitorSmartphone,
  Play,
  Send,
} from "lucide-react"
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
import { HintPanel } from "@/components/task/HintPanel"
import { ApiError } from "@/lib/api/query"
import { ErrorState } from "@/components/state/ErrorState"
import { LoadingState } from "@/components/state/LoadingState"
import { useAuth } from "@/hooks/useAuth"
import { useBadges } from "@/hooks/useBadges"
import { useHint, HintError } from "@/hooks/useHint"
import { useModules } from "@/hooks/useModules"
import { useProfile } from "@/hooks/useProfile"
import { useRun } from "@/hooks/useRun"
import { useSubmitAttempt } from "@/hooks/useSubmitAttempt"
import { useTask } from "@/hooks/useTask"
import type {
  AttemptResponse,
  ProfileResponse,
  RunResponse,
  TaskDetailResponse,
} from "@/lib/api/types"
import { buildConceptIndex, type ConceptInfo } from "@/lib/mastery"

const INITIAL_QUERY = "-- Napiši svoj SQL upit ovdje\n"

/**
 * Natpis je ZAMRZNUT i ISTI u oba stanja (H3.8, §C.4.2). Brojač NIKAD ne ulazi
 * u natpis — inače se natpis mijenja s brojkom i H3.8 pada.
 */
const HINT_NATPIS = "Zatraži hint"
/** Vidljiv razlog zaključanosti; vezan `aria-describedby`om (presedan RegisterPage:152). */
const HINT_RAZLOG = "Savjet se otključava nakon netočne predaje."
const HINT_RAZLOG_ID = "hint-razlog"

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

  // ── Hint (5.2) — NEOVISAN o submitSlot enumu; koegzistira s feedbackom. ────
  const { user } = useAuth()
  const profileQ = useProfile()
  const hintM = useHint(task.id)
  const { reset: resetHint } = hintM
  const [hintText, setHintText] = useState<string>()
  // Savjet se odnosi na `after_attempt_id`. Nakon nove predaje opisuje grešku
  // koje više nema — ali se NE BRIŠE (§C3.1): student ga je platio kreditom, a
  // idući klik nakon nove predaje troši NOVI kredit (idempotencija veže hint uz
  // pokušaj). Brisanje bi tiho uništilo plaćeni sadržaj; oznaka ne uništava ništa.
  const [hintStale, setHintStale] = useState(false)
  // Flag ugašen USRED sesije (C.2.1): 503 `hints_disabled` na klik znači „sakrij
  // gumb sada", ne „prikaži grešku".
  const [hintsHidden, setHintsHidden] = useState(false)
  // Objava za čitač ekrana pri kliku na zaključan gumb. Prazan međukorak je
  // nužan: aria-live objavljuje PROMJENU sadržaja, pa bi drugi klik s istim
  // tekstom prošao nečujno.
  const [hintObjava, setHintObjava] = useState("")

  const hintsEnabled = (user?.hints_enabled ?? false) && !hintsHidden
  const hintUnlocked = task.last_attempt_error_type != null
  const hintRemaining = profileQ.data?.remaining
  const hintFailureReason =
    hintM.error instanceof HintError
      ? hintM.error.reason
      : hintM.isError
        ? ("unknown" as const)
        : undefined

  /**
   * Vidljiv jednoredni meta tekst uz gumb — JEDAN element, jedan `id`, na koji
   * `aria-describedby` pokazuje u oba stanja:
   *   zaključano  → RAZLOG (ono što `aria-describedby` mora imenovati)
   *   otključano  → BROJAČ preostalih savjeta
   * 🔴 Brojač je OVDJE, nikad u natpisu gumba (§C.4.2) — natpis se ne smije
   * mijenjati s brojkom, inače H3.8 („isti natpis u oba stanja") pada.
   * 🔴 Brojka je iz `/profile` i AUTORITATIVNA — ne dekrementira se lokalno
   * (C.2.2: idempotentno ponavljanje ne troši kredit, pa bi lokalni dekrement
   * lagao na svakom ponovljenom kliku).
   */
  const hintMetaText = !hintsEnabled
    ? null
    : !hintUnlocked
      ? HINT_RAZLOG
      : hintRemaining != null
        ? `Preostalo savjeta: ${hintRemaining}`
        : null

  const handleHint = () => {
    // 🔴 Zaključan gumb: NULA mrežnog prometa (§C.5.2 t.1). `aria-disabled`
    // ostaje klikabilan namjerno — čitač ekrana ga vidi i pročita razlog.
    if (!hintUnlocked) {
      setHintObjava("")
      window.setTimeout(() => setHintObjava(HINT_RAZLOG), 80)
      return
    }
    hintM.mutate(undefined, {
      onSuccess: (data) => {
        setHintText(data.hint_text)
        setHintStale(false)
      },
      onError: (e) => {
        if (e instanceof HintError && e.reason === "hints_disabled") {
          setHintsHidden(true)
        }
      },
    })
  }

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
        // Nova predaja → postojeći savjet opisuje raniji pokušaj (§C3.1). Panel
        // ga OZNAČAVA, ne briše; kad savjeta nema, zastavica nema učinka.
        setHintStale(true)
        // Neuspjeli hint (npr. 409 iz utrke predaja i osvježenog /task) više ne
        // opisuje sadašnjost — poruka se gasi predajom, ne visi do reloada.
        resetHint()
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

  /**
   * 🔴 N-11 — preporuka vraća ISTI zadatak (netočna predaja, #44 breadth-first,
   * #16 saturiran P(L)). `Link` na istu rutu ne remounta keyed `TaskView`, pa
   * klik na CTA nije radio NIŠTA. Ovdje se ekran vraća u stanje „prije predaje"
   * BEZ navigacije: feedback i Run rezultat se čiste, editor se vraća u fokus.
   *
   * 🔴 SQL U EDITORU SE NAMJERNO NE BRIŠE (odstupanje od doslovnog „resetira
   * editor"): student koji je upravo pogriješio obično je blizu rješenja, a
   * brisanje njegova upita kaznilo bi upravo onoga koga ovaj popravak štiti.
   * Vidljiva promjena (panel nestaje, Submit se vraća) je ono što je N-11
   * tražio. Puni reset editora je jedna linija ako se odluka promijeni.
   *
   * `useCallback` — `FeedbackPanel` je `memo`, nestabilan callback bi ga
   * rerenderao na svaki keystroke u editoru.
   */
  const retrySameTask = useCallback(() => {
    setLastAttempt(undefined)
    setLevelUp(false)
    setLastResult(undefined)
    submittedQueryRef.current = ""
    document
      .querySelector(".monaco-editor")
      ?.scrollIntoView({ block: "center", behavior: "smooth" })
  }, [])

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

      {/* ── <768px: rješavanje traži veći zaslon (1C t.4) ────────────
          🔴 ADITIVNO. Ne dira `TaskView` logiku, keying ni registraciju hotkeya —
          samo dva wrappera oko postojećeg desnog panela. Opis, koncepti i shema
          (lijevi stupac) ostaju čitljivi i dostupni. */}
      <Card className="min-w-0 self-start md:hidden">
        <CardContent className="space-y-3 p-4">
          <div className="flex items-start gap-3">
            <MonitorSmartphone
              className="mt-0.5 size-5 shrink-0 text-muted-foreground"
              aria-hidden="true"
            />
            <div className="space-y-2">
              <h2 className="text-base font-medium">
                Rješavanje traži veći zaslon
              </h2>
              {/* 🔴 ISKRENA poruka: ne „uskoro" i ne „nije podržano", nego RAZLOG.
                  SQL editor traži tipkovnicu, a kratice koje pokreću i predaju upit
                  (Ctrl/Cmd+Enter, Shift+Enter) na telefonu ne postoje. */}
              <p className="text-sm text-muted-foreground">
                SQL editor traži tipkovnicu — a kratice kojima se upit pokreće i
                predaje (<Kbd aria-hidden="true">{RUN_KBD}</Kbd> i{" "}
                <Kbd aria-hidden="true">Shift ↵</Kbd>) na telefonu ne postoje.
                Opis zadatka i shema baze iznad su ti dostupni; za pisanje upita
                otvori isti zadatak na računalu.
              </p>
            </div>
          </div>
          {/* Poruka mora imati IZLAZ — inače je slijepa ulica. */}
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="outline">
              <Link to="/">
                <LayoutDashboard data-icon="inline-start" aria-hidden="true" />
                Dashboard
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link to="/modules">
                <BookOpen data-icon="inline-start" aria-hidden="true" />
                Moduli
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Desni panel: Monaco editor + Run/Submit ──────────────────
          `hidden md:block` (ne uvjetni render): komponenta OSTAJE MONTIRANA, pa
          `SqlEditor` mount-time registracija Ctrl/Shift+Enter i `keying` rade
          nepromijenjeno. `display:none` ju usput miče iz tab-reda i od čitača
          ekrana, što je na mobitelu i ispravno — editor ondje nije upotrebljiv. */}
      <Card className="hidden min-w-0 self-start md:block">
        <CardContent className="space-y-3 p-4">
          {/* focus-within prsten: Monaco fokus mora biti vidljiv i na kontejneru (MASTER §7). */}
          <div
            data-testid="editor-box"
            className="h-[420px] overflow-hidden rounded-md border border-border transition-[border-color,box-shadow] duration-fast ease-standard focus-within:border-ring focus-within:ring-2 focus-within:ring-ring/40 motion-reduce:transition-none xl:h-[520px]"
          >
            {/* ⚠️ onRun/onSubmit od PRVOG rendera — monaco akcije su mount-time. */}
            <SqlEditor
              value={query}
              onChange={setQuery}
              onRun={handleRun}
              onSubmit={handleSubmit}
            />
          </div>
          <div
            data-testid="action-row"
            className="flex flex-wrap items-center justify-end gap-3"
          >
            {/* 🔴 Gumb za savjet je PRVI child vanjskog flexa (§C2.1) i `mr-auto`
                ga drži uz lijevi rub — Run/Submit ostaju desno, nepomaknuti.
                `ghost` + neutralni `border-border`/`bg-muted`: nikad `default`,
                jer savjet nije primarna akcija ekrana (to je Submit).
                🔴 `aria-disabled`, NE `disabled`: zaključan gumb mora ostati
                fokusabilan da čitač ekrana pročita razlog (§C.5.2). */}
            {hintsEnabled && (
              <Button
                variant="ghost"
                className="mr-auto border-border bg-muted hover:bg-muted/70 aria-disabled:text-muted-foreground aria-disabled:hover:bg-muted"
                aria-disabled={!hintUnlocked}
                aria-describedby={hintMetaText ? HINT_RAZLOG_ID : undefined}
                onClick={handleHint}
              >
                <Lightbulb data-icon="inline-start" aria-hidden="true" />
                {HINT_NATPIS}
              </Button>
            )}
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
          {/* ── Hint slot (§C.6.2): ZASEBAN, iznad lanca `submitSlot`a ────────
              Hint i feedback KOEGZISTIRAJU — hint gore jer je akcija koju je
              student upravo pokrenuo i mora biti bliže gumbu koji ju je
              pokrenuo. Ulazak u `submitSlot` enum bi ih učinio isključivima. */}
          {hintsEnabled && (
            <>
              {hintMetaText && (
                // `text-sm`, ne `text-xs` — presedan RegisterPage.tsx:152, gdje
                // je pomoć uz polje podignuta upravo zbog kontrasta (N-4).
                <p
                  id={HINT_RAZLOG_ID}
                  className="text-sm text-muted-foreground"
                >
                  {hintMetaText}
                </p>
              )}
              {/* Klik na zaključan gumb ne mijenja ništa vidljivo, pa objava ide
                  ovuda. `sr-only` je izvan toka → ne dodaje visinu. */}
              <div aria-live="polite" className="sr-only">
                {hintObjava}
              </div>
              <HintPanel
                hintText={hintText}
                stale={hintStale}
                isPending={hintM.isPending}
                failure={hintFailureReason}
                nextRefillAt={profileQ.data?.next_refill_at}
                onRetry={handleHint}
              />
            </>
          )}
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
              currentTaskId={task.id}
              onRetrySameTask={retrySameTask}
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
