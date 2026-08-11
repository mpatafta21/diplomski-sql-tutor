/**
 * Monaco tema za SQL editor — SVAKA vrijednost izvedena iz design tokena (MASTER.md §6).
 *
 * Monaco traži hex i ne vidi CSS varijable, pa je ovo nužno **vrijednosna kopija**. Zato
 * vrijedi jedno pravilo, bez iznimke:
 *
 * 🔴 NIJEDAN HEX OVDJE NE SMIJE BITI RUČNO ODABRAN. Svaki mora imati izvor u
 *    `frontend/src/index.css` iz kojeg ga `scripts/a11y/palette.py` može reproducirati —
 *    ili kao čist token, ili kao token s alfom, ili kao kompozit nad plohom.
 *    `scripts/a11y/monaco_check.py` to **provjerava za SVAKI hex u datoteci**: vrijednost
 *    koju `MAP` ne pokriva je GREŠKA, ne bilješka. Do 4.7 su tri vrijednosti bile ručne
 *    (`#292929` i njezine alfe) i nisu imale iz čega se preračunati pri promjeni palete —
 *    upravo zato je zamijenjena kompozitom `--border` nad `--card`.
 *
 * Alfa se piše kao 8-znamenkasti hex (`RRGGBBAA`) — Monaco ga tako i očekuje.
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
    { token: "", foreground: "F3F4FE" }, //           --foreground
    { token: "identifier", foreground: "F3F4FE" }, //  --foreground
    { token: "keyword", foreground: "53A3F2" }, //    --chart-1 (plava)
    { token: "keyword.sql", foreground: "53A3F2" }, // --chart-1
    { token: "operator", foreground: "9DA5B1" }, //   --neutral
    { token: "delimiter", foreground: "9C9FB7" }, //  --muted-foreground
    { token: "string", foreground: "5DC879" }, //     --correct (zelena)
    { token: "string.sql", foreground: "5DC879" }, // --correct
    { token: "number", foreground: "36C6B8" }, //     --chart-2 (teal)
    { token: "comment", foreground: "9C9FB7", fontStyle: "italic" }, // --muted-foreground
    { token: "predefined", foreground: "B191EA" }, // --chart-3 (violet) — funkcije
  ],
  colors: {
    "editor.background": "#13142C", //                --card
    "editor.foreground": "#F3F4FE", //                --foreground
    "editorLineNumber.foreground": "#9C9FB7", //      --muted-foreground
    "editorLineNumber.activeForeground": "#F0B135", // --accent-warm
    "editorCursor.foreground": "#F0B135", //          --accent-warm
    "editor.selectionBackground": "#F0B13533", //     --accent-warm @ 20 %
    "editor.inactiveSelectionBackground": "#F0B1351A", // --accent-warm @ 10 %
    "editorBracketMatch.border": "#F0B13580", //      --accent-warm @ 50 %
    "editorSuggestWidget.selectedBackground": "#F0B13526", // --accent-warm @ 15 %
    // ⟳ 4.7: bilo #292929 — ručna vrijednost bez izvora. Sada KOMPOZIT --border nad --card.
    "editorIndentGuide.background": "#2B2C46", //     --border nad --card
    "editorWidget.border": "#2B2C46", //              --border nad --card
    "editor.lineHighlightBackground": "#2B2C4666", // --border nad --card @ 40 %
    "scrollbarSlider.background": "#2B2C4680", //     --border nad --card @ 50 %
    "scrollbarSlider.hoverBackground": "#2B2C46CC", // --border nad --card @ 80 %
    "editorWidget.background": "#13142C", //          --card
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
