/**
 * Custom Monaco teme za SQL editor — izvedene iz design tokena (MASTER.md §6).
 *
 * VAŽNO: ovo je ČISTI vrijednosni objekt — paket `@monaco-editor/react` dolazi tek u 4.3,
 * koja ga primjenjuje kroz `monaco.editor.defineTheme("sql-tutor-dark", sqlTutorDark)`.
 * Monaco traži hex boje; vrijednosti su oklch tokeni konvertirani u sRGB hex
 * (kalibracijska skripta, gamut + kontrast verificirani) — uz svaku stoji izvorni token.
 */

/** Minimalni strukturni tip za monaco.editor.IStandaloneThemeData (bez monaco dependencyja). */
export interface MonacoThemeData {
  base: "vs" | "vs-dark" | "hc-black" | "hc-light"
  inherit: boolean
  rules: Array<{
    token: string
    foreground?: string
    background?: string
    fontStyle?: string
  }>
  colors: Record<string, string>
}

/** Jedina tema — aplikacija je dark-only od 4.7. Pozadina = --card, accent = --accent-warm. */
export const sqlTutorDark: MonacoThemeData = {
  base: "vs-dark",
  inherit: true,
  rules: [
    { token: "", foreground: "FAFAFA" }, //           --foreground        oklch(0.985 0 0)
    { token: "keyword", foreground: "53A3F2" }, //    --chart-1 (plava)   oklch(0.70 0.14 250)
    { token: "keyword.sql", foreground: "53A3F2" },
    { token: "operator", foreground: "9DA5B1" }, //   --neutral           oklch(0.72 0.02 260)
    { token: "string", foreground: "5DC879" }, //     --correct (zelena)  oklch(0.75 0.15 150)
    { token: "string.sql", foreground: "5DC879" },
    { token: "number", foreground: "36C6B8" }, //     --chart-2 (teal)    oklch(0.75 0.12 185)
    { token: "comment", foreground: "A1A1A1", fontStyle: "italic" }, // --muted-foreground
    { token: "predefined", foreground: "B191EA" }, // --chart-3 (violet)  oklch(0.72 0.13 300) — funkcije
    { token: "identifier", foreground: "FAFAFA" },
    { token: "delimiter", foreground: "A1A1A1" },
  ],
  colors: {
    "editor.background": "#171717", //                --card              oklch(0.205 0 0)
    "editor.foreground": "#FAFAFA", //                --foreground
    "editorLineNumber.foreground": "#A1A1A1", //      --muted-foreground
    "editorLineNumber.activeForeground": "#F0B135", // --accent-warm      oklch(0.80 0.15 80)
    "editorCursor.foreground": "#F0B135", //          --accent-warm
    "editor.selectionBackground": "#F0B13533", //     --accent-warm @ 20%
    "editor.inactiveSelectionBackground": "#F0B1351A",
    "editor.lineHighlightBackground": "#29292966", // --border pojas, suptilno
    "editorIndentGuide.background": "#292929",
    "editorBracketMatch.border": "#F0B13580",
    "editorWidget.background": "#171717",
    "editorWidget.border": "#292929",
    "editorSuggestWidget.selectedBackground": "#F0B13526",
    "scrollbarSlider.background": "#29292980",
    "scrollbarSlider.hoverBackground": "#292929CC",
  },
}

/** Zajedničke editor opcije za 4.3 (font iz --font-mono tokena). */
export const sqlTutorEditorOptions = {
  fontFamily: '"JetBrains Mono Variable", ui-monospace, monospace', // --font-mono
  fontSize: 14,
  fontLigatures: true,
  lineHeight: 1.6,
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  renderLineHighlight: "line" as const,
  padding: { top: 16, bottom: 16 },
} as const
