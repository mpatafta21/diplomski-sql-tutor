/**
 * PRIVREMENA token-preview stranica (Faza 4.1b) — živi katalog design tokena.
 * Zamjenjuje se app shellom + routerom u 4.1c. Izvor istine: design-system/sql-tutor/MASTER.md.
 */
import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"
import { cn } from "@/lib/utils"

function Swatch({
  label,
  className,
  note,
}: {
  label: string
  className: string
  note?: string
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div
        className={cn("h-14 w-full rounded-md border border-border", className)}
      />
      <span className="font-mono text-xs text-muted-foreground">{label}</span>
      {note && <span className="text-xs text-muted-foreground/70">{note}</span>}
    </div>
  )
}

function Section({
  title,
  children,
  hint,
}: {
  title: string
  children: React.ReactNode
  hint?: string
}) {
  return (
    <section className="space-y-4">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        {hint && <p className="text-sm text-muted-foreground">{hint}</p>}
      </div>
      {children}
    </section>
  )
}

const TYPE_SCALE = [
  { cls: "text-xs", label: "text-xs · 0.64rem" },
  { cls: "text-sm", label: "text-sm · 0.8rem" },
  { cls: "text-base", label: "text-base · 1rem" },
  { cls: "text-lg", label: "text-lg · 1.25rem" },
  { cls: "text-xl", label: "text-xl · 1.563rem" },
  { cls: "text-2xl", label: "text-2xl · 1.953rem" },
  { cls: "text-3xl", label: "text-3xl · 2.441rem" },
] as const

const MOTION_TOKENS = [
  ["--ease-standard", "cubic-bezier(0.2, 0, 0, 1)", "opći prijelazi"],
  ["--ease-entrance", "cubic-bezier(0.16, 1, 0.3, 1)", "ulazi panela"],
  ["--ease-exit", "cubic-bezier(0.4, 0, 1, 1)", "izlazi"],
  ["--ease-reward", "cubic-bezier(0.34, 1.25, 0.64, 1)", "XP/badge/level"],
  ["--duration-instant", "100ms", "hover, press"],
  ["--duration-fast", "160ms", "mikrointerakcije"],
  ["--duration-base", "240ms", "paneli, fade"],
  ["--duration-slow", "400ms", "page transitions"],
  ["--duration-reward", "700ms", "gamifikacija"],
] as const

function App() {
  // Dark-first: dark je default, light ravnopravan (MASTER.md §1)
  const [dark, setDark] = useState(true)

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark)
  }, [dark])

  return (
    <main className="mx-auto min-h-svh max-w-5xl space-y-12 px-6 py-12">
      <header className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-semibold tracking-tight">
            SQL Tutor — design tokeni
          </h1>
          <p className="text-sm text-muted-foreground">
            Faza 4.1b · živi katalog ·{" "}
            <span className="font-mono">design-system/sql-tutor/MASTER.md</span>
          </p>
        </div>
        <button
          type="button"
          onClick={() => setDark((d) => !d)}
          aria-label={dark ? "Prebaci na light temu" : "Prebaci na dark temu"}
          className="flex cursor-pointer items-center gap-2 rounded-md border border-border bg-card px-3 py-2 text-sm transition-[background-color,transform] duration-fast ease-standard hover:bg-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring active:scale-[0.97]"
        >
          {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
          {dark ? "Light" : "Dark"}
        </button>
      </header>

      <Section
        title="Semantika verdicta"
        hint="partial je REZERVIRAN token (ERRATA #8 — nema verdict kolone): definiran, ali UI ga ne koristi."
      >
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Swatch label="--correct" className="bg-correct" />
          <Swatch label="--incorrect" className="bg-incorrect" />
          <Swatch label="--partial" className="bg-partial" note="rezerviran" />
          <Swatch label="--neutral" className="bg-neutral" />
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="rounded-md bg-correct-soft p-4 text-sm text-correct">
            Točno! Upit vraća očekivani rezultat. (tekst --correct na
            --correct-soft)
          </div>
          <div className="rounded-md bg-incorrect-soft p-4 text-sm text-incorrect">
            Netočno — provjeri JOIN uvjet. (tekst --incorrect na
            --incorrect-soft)
          </div>
        </div>
      </Section>

      <Section
        title="Topli amber accent"
        hint="Jedini warm u sustavu — rezerviran za XP, level, streak, badge, progres."
      >
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <Swatch label="--accent-warm" className="bg-accent-warm" />
          <div className="flex flex-col gap-1.5">
            <div className="flex h-14 w-full items-center justify-center rounded-md bg-accent-warm">
              <span className="text-sm font-semibold text-accent-warm-foreground">
                +25 XP
              </span>
            </div>
            <span className="font-mono text-xs text-muted-foreground">
              foreground na fillu
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            <div className="flex h-14 w-full items-center justify-center rounded-md border border-border">
              <span className="text-sm font-semibold text-accent-warm-text">
                Level 4 · streak 6
              </span>
            </div>
            <span className="font-mono text-xs text-muted-foreground">
              --accent-warm-text na pozadini
            </span>
          </div>
        </div>
        <div className="space-y-1.5">
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full w-2/3 rounded-full bg-accent-warm" />
          </div>
          <span className="text-xs text-muted-foreground">
            XP bar · 640 / 960
          </span>
        </div>
      </Section>

      <Section
        title="Mastery gradient — P(L) low→high"
        hint="CB-safe (plavo→cijan), monoton po svjetlini. Ista skala u barovima i BKT krivuljama."
      >
        <div className="grid grid-cols-5 gap-2">
          <Swatch label="0" className="bg-mastery-0" />
          <Swatch label="25" className="bg-mastery-25" />
          <Swatch label="50" className="bg-mastery-50" />
          <Swatch label="75" className="bg-mastery-75" />
          <Swatch label="100" className="bg-mastery-100" />
        </div>
      </Section>

      <Section
        title="Concept-tier — 3 koraka (violet)"
        hint="concepts.tier ∈ {easy, medium, hard} — ODVOJENA skala od module-difficulty."
      >
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-tier-easy px-3 py-1 text-sm font-medium text-tier-easy-foreground">
            easy
          </span>
          <span className="rounded-full bg-tier-medium px-3 py-1 text-sm font-medium text-tier-medium-foreground">
            medium
          </span>
          <span className="rounded-full bg-tier-hard px-3 py-1 text-sm font-medium text-tier-hard-foreground">
            hard
          </span>
        </div>
      </Section>

      <Section
        title="Module-difficulty — 5 koraka (magenta)"
        hint="modules.difficulty ∈ {beginner, intermediate, advanced, expert, cross_module} — cross_module transverzalan (desaturiran)."
      >
        <div className="flex flex-wrap gap-2">
          {(
            [
              [
                "beginner",
                "bg-difficulty-beginner text-difficulty-beginner-foreground",
              ],
              [
                "intermediate",
                "bg-difficulty-intermediate text-difficulty-intermediate-foreground",
              ],
              [
                "advanced",
                "bg-difficulty-advanced text-difficulty-advanced-foreground",
              ],
              [
                "expert",
                "bg-difficulty-expert text-difficulty-expert-foreground",
              ],
              [
                "cross_module",
                "bg-difficulty-cross-module text-difficulty-cross-module-foreground",
              ],
            ] as const
          ).map(([label, cls]) => (
            <span
              key={label}
              className={cn("rounded-full px-3 py-1 text-sm font-medium", cls)}
            >
              {label}
            </span>
          ))}
        </div>
      </Section>

      <Section
        title="Data-viz paleta (Recharts)"
        hint="Kategorijska — hue-razmaknuta, razlučiva i po svjetlini. Sekvencijalna = mastery gradient."
      >
        <div className="grid grid-cols-5 gap-2">
          <Swatch label="--chart-1" className="bg-chart-1" />
          <Swatch label="--chart-2" className="bg-chart-2" />
          <Swatch label="--chart-3" className="bg-chart-3" />
          <Swatch label="--chart-4" className="bg-chart-4" />
          <Swatch label="--chart-5" className="bg-chart-5" />
        </div>
      </Section>

      <Section
        title="Tipografska skala — 1.250"
        hint="Geist Variable (sans) · JetBrains Mono Variable (mono)."
      >
        <div className="space-y-2">
          {TYPE_SCALE.map(({ cls, label }) => (
            <div key={cls} className="flex items-baseline gap-4">
              <span className="w-40 shrink-0 font-mono text-xs text-muted-foreground">
                {label}
              </span>
              <span className={cn(cls, "truncate")}>
                SELECT znanje FROM vježba
              </span>
            </div>
          ))}
        </div>
      </Section>

      <Section
        title="Mono uzorak — SQL (Monaco tema preview)"
        hint="Boje mapirane kao u src/lib/monaco-theme.ts: keyword=chart-1, string=correct, broj=chart-2, funkcija=chart-3, komentar=muted."
      >
        <pre className="overflow-x-auto rounded-lg border border-border bg-card p-4 font-mono text-sm leading-relaxed">
          <code>
            <span className="text-muted-foreground">
              -- prosječna vrijednost narudžbe po kupcu
            </span>
            {"\n"}
            <span className="text-chart-1">SELECT</span> c.name,{" "}
            <span className="text-chart-3">AVG</span>(o.total_amount){" "}
            <span className="text-chart-1">AS</span> avg_order{"\n"}
            <span className="text-chart-1">FROM</span> customers c{"\n"}
            <span className="text-chart-1">JOIN</span> orders o{" "}
            <span className="text-chart-1">ON</span> o.customer_id = c.id{"\n"}
            <span className="text-chart-1">WHERE</span> o.status ={" "}
            <span className="text-correct">'completed'</span>
            {"\n"}
            <span className="text-chart-1">GROUP BY</span> c.name{"\n"}
            <span className="text-chart-1">HAVING</span>{" "}
            <span className="text-chart-3">AVG</span>(o.total_amount) {">"}{" "}
            <span className="text-chart-2">100</span>;
          </code>
        </pre>
      </Section>

      <Section
        title="Spacing · radijusi · elevacija"
        hint="4px baza (Tailwind default) · radijusi iz --radius · dark elevacija = surface step + border, ne sjena."
      >
        <div className="flex flex-wrap items-end gap-4">
          {([1, 2, 4, 6, 8, 12] as const).map((s) => (
            <div key={s} className="flex flex-col items-center gap-1.5">
              <div
                className="w-6 rounded-sm bg-mastery-50"
                style={{ height: `${s * 4}px` }}
              />
              <span className="font-mono text-xs text-muted-foreground">
                {s * 4}px
              </span>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-sm border border-border bg-card p-4 text-xs text-muted-foreground">
            rounded-sm
          </div>
          <div className="rounded-md border border-border bg-card p-4 text-xs text-muted-foreground">
            rounded-md
          </div>
          <div className="rounded-lg border border-border bg-card p-4 text-xs text-muted-foreground">
            rounded-lg
          </div>
          <div className="rounded-xl border border-border bg-card p-4 text-xs text-muted-foreground shadow-sm">
            + shadow-sm (light)
          </div>
        </div>
      </Section>

      <Section
        title="Motion tokeni"
        hint="Vrijednosti bez motion liba (dolazi 4.6). Hover na kartici koristi --duration-fast + --ease-standard."
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <tbody>
              {MOTION_TOKENS.map(([token, value, use]) => (
                <tr key={token} className="border-b border-border">
                  <td className="py-2 pr-4 font-mono text-xs">{token}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-muted-foreground">
                    {value}
                  </td>
                  <td className="py-2 text-xs text-muted-foreground">{use}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="cursor-pointer rounded-lg border border-border bg-card p-4 text-sm transition-colors duration-fast ease-standard hover:bg-muted">
          Hover demo — transition-colors · duration-fast · ease-standard
        </div>
      </Section>

      <footer className="border-t border-border pt-6 text-xs text-muted-foreground">
        Privremena stranica — 4.1c donosi app shell i router. Tokeni:
        frontend/src/index.css · SSOT: design-system/sql-tutor/MASTER.md
      </footer>
    </main>
  )
}

export default App
