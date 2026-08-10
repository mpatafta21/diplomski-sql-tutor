/**
 * SqlEditor (Faza 4.3a) — Monaco SQL editor s custom temama iz 4.1b tokena.
 *
 * - Self-hosted monaco (vidi lib/monaco-setup.ts — nula CDN-a).
 * - Tema: sql-tutor-dark (lib/monaco-theme.ts, MASTER.md §6). Od 4.7 je aplikacija
 *   dark-only, pa nema light varijante ni `dark` propa koji bi je birao.
 * - Hotkeys: Ctrl/Cmd+Enter = Run, Shift+Enter = Submit — callbacke žice
 *   4.3b/4.3c; ovdje su opcionalni (no-op dok ne postoje).
 * - `automaticLayout` prati resize kontejnera (editor ne lomi layout).
 */
import { useEffect, useRef } from "react"
import { Editor, type OnMount } from "@monaco-editor/react"
import { monaco } from "@/lib/monaco-setup"
import { sqlTutorDark, sqlTutorEditorOptions } from "@/lib/monaco-theme"
import { LoadingState } from "@/components/state/LoadingState"

interface SqlEditorProps {
  value: string
  onChange: (value: string) => void
  /** Ctrl/Cmd+Enter — žici 4.3b (/run). */
  onRun?: () => void
  /** Shift+Enter — žici 4.3c (/attempt). */
  onSubmit?: () => void
}

// defineTheme je idempotentan (redefinicija istog imena samo prepiše objekt) —
// bez guard flaga, poziv po mountu je bezopasan.
function defineThemes() {
  monaco.editor.defineTheme("sql-tutor-dark", sqlTutorDark)
}

export function SqlEditor({
  value,
  onChange,
  onRun,
  onSubmit,
}: SqlEditorProps) {
  // Refs drže svježe callbacke — monaco akcije se registriraju JEDNOM (onMount),
  // a 4.3b/c će mijenjati handlere po renderu.
  const onRunRef = useRef(onRun)
  const onSubmitRef = useRef(onSubmit)
  useEffect(() => {
    onRunRef.current = onRun
    onSubmitRef.current = onSubmit
  }, [onRun, onSubmit])

  const handleMount: OnMount = (editor) => {
    // ⚠️ Registracija SAMO ako handler postoji pri mountu: monaco konzumira
    // resolvirani keybinding bez obzira što run() radi — bezuvjetna registracija
    // s praznim handlerom tiho guta Shift+Enter (newline) / Ctrl+Enter.
    // Posljedica za 4.3b/c: onRun/onSubmit moraju biti proslijeđeni od PRVOG
    // rendera (refovi ih drže svježima poslije).
    if (onRunRef.current) {
      editor.addAction({
        id: "sql-tutor-run",
        label: "Pokreni upit (Run)",
        keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter],
        run: () => onRunRef.current?.(),
      })
    }
    if (onSubmitRef.current) {
      editor.addAction({
        id: "sql-tutor-submit",
        label: "Predaj rješenje (Submit)",
        keybindings: [monaco.KeyMod.Shift | monaco.KeyCode.Enter],
        run: () => onSubmitRef.current?.(),
      })
    }
  }

  return (
    <Editor
      language="sql"
      value={value}
      onChange={(v) => onChange(v ?? "")}
      beforeMount={defineThemes}
      onMount={handleMount}
      theme="sql-tutor-dark"
      loading={<LoadingState lines={4} label="Učitavanje editora" />}
      options={{
        ...sqlTutorEditorOptions,
        automaticLayout: true,
        ariaLabel: "SQL editor",
        tabSize: 2,
      }}
    />
  )
}
