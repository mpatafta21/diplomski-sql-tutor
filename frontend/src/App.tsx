import { cn } from "@/lib/utils"

function App() {
  return (
    <main
      className={cn(
        "flex min-h-svh flex-col items-center justify-center gap-2",
      )}
    >
      <h1 className="text-2xl font-semibold tracking-tight">SQL Tutor</h1>
      <p className="text-sm text-muted-foreground">Faza 4.1a — scaffold</p>
    </main>
  )
}

export default App
