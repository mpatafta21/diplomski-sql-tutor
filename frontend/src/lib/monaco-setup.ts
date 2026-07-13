/**
 * Monaco self-hosted setup (Faza 4.3a) — NULA CDN requestova.
 *
 * @monaco-editor/react defaultno vuče monaco s jsdelivr CDN-a kroz
 * @monaco-editor/loader; projekt ima self-hosted obrazac (fontsource, ne CDN)
 * pa se loaderu daje BUNDLANI monaco (`loader.config({ monaco })`).
 *
 * Worker: SQL nema vlastiti language worker → dovoljan je editorWorkerService
 * (core editor servisi). Vite `?worker` import radi bundlanje workera.
 *
 * Ovaj modul se importa SAMO iz SqlEditor.tsx (lazy /task ruta) — monaco ne
 * ulazi u glavni bundle.
 */
import { loader } from "@monaco-editor/react"
import * as monaco from "monaco-editor"
import EditorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker"

self.MonacoEnvironment = {
  getWorker: () => new EditorWorker(),
}

loader.config({ monaco })

export { monaco }
