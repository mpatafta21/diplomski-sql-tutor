"""Popis PLOHA i STVARNIH parova (tekst-token × ploha) — podaci, ne logika.

🔴 Ovo NIJE kartezijev produkt. Mjeri se samo par koji u kodu postoji, jer je prvi
pokušaj punog produkta dao 40+ lažnih padova (npr. `text-foreground` na `bg-primary`
= 1,21:1 — par koji ne postoji, za tu plohu služi `primary-foreground`). Provjera koja
utopi prave padove u lažnima jednako je neupotrebljiva kao ona koje nema (🔒 DOC, #50).

OZNAKE DOKAZA
  ●  ploha i tekst su u ISTOM `className` — dokazano čitanjem koda
  ○  tekst je u PODSTABLU elementa koji nosi plohu — naslijeđeno

KAKO DODATI NOVI PAR
  1. nađi ga u kodu (`grep -rn "bg-<ploha>" frontend/src`) i pročitaj koji tekst tokeni
     stoje na njemu;
  2. ako ploha nije u SURFACES, dodaj je — alpha-varijante idu kao ("token", alpha,
     "ploha ispod"), jer se kontrast mjeri nad KOMPOZITOM, ne nad čistim tokenom;
  3. dodaj redak u PAIRS s oznakom ● ili ○ i citatom (`Datoteka.tsx:redak`);
  4. pokreni `python3 scripts/a11y/contrast_matrix.py` i provjeri da je izlaz očekivan.

Bez citata se par NE dodaje — tvrdnja bez dokaza je ista klasa kao tvrdnja bez plohe.

DVIJE MJERE, DVA PITANJA — v. `CO_USED_EXTRA` na dnu
  Kontrast (WCAG)  odgovara: „vidi li se ovo na ovome?"  → PAIRS
  ΔE (Oklab)       odgovara: „razlikuju li se ovo dvoje?" → CO_USED
Druga mjera postoji zbog cross-scale guarda (MASTER §2.7): kroma-token ne smije se čitati
kao član semantičke skale. Mjeri se SAMO nad sukorištenim parom — v. NALAZ N-12.
"""

#: Plohe. Vrijednost je ili ime tokena, ili (token, alpha, ploha-ispod) za kompozit.
SURFACES: dict[str, object] = {
    "background": "background",
    "card": "card",
    "popover": "popover",
    "sidebar": "sidebar",
    "secondary": "secondary",
    "muted": "muted",
    "muted/30": ("muted", 0.30, "card"),
    "muted/40": ("muted", 0.40, "card"),
    "muted/50": ("muted", 0.50, "card"),
    "muted/60": ("muted", 0.60, "card"),
    "background/60": ("background", 0.60, "card"),
    "card/50": ("card", 0.50, "card"),
    "sidebar-accent/40": ("sidebar-accent", 0.40, "card"),
    "sidebar-accent/60": ("sidebar-accent", 0.60, "card"),
    "input/30": ("input", 0.30, "card"),
    "input/50": ("input", 0.50, "card"),
    "correct-soft": "correct-soft",
    "incorrect-soft": "incorrect-soft",
    "partial-soft": "partial-soft",
    "accent-warm/5": ("accent-warm", 0.05, "card"),
    "accent-warm/10": ("accent-warm", 0.10, "card"),
    "accent-warm/20": ("accent-warm", 0.20, "card"),
    "incorrect/10": ("incorrect", 0.10, "card"),
    # ── `--destructive` (ERRATA #52) ────────────────────────────────────────
    # JEDINI dosežni render je nevaljano polje: `ui/input.tsx:12`
    # `dark:aria-invalid:border-destructive/50` + `dark:aria-invalid:ring-destructive/40`.
    # `variant="destructive"` (ui/button.tsx:19-20) i `ui/field.tsx` NEMAJU ijednog
    # potrošača (grep 2026-08-10) — mrtav kod, ne mjeri se.
    # `under` je ovdje DRUGA PLOHA, ne token: obrub se kompozitira nad VLASTITOM
    # pozadinom polja (`bg-input/30`), ne nad karticom ispod nje.
    "destructive/50@input": ("destructive", 0.50, "input/30"),
    "destructive/50": ("destructive", 0.50, "card"),
    "destructive/40": ("destructive", 0.40, "card"),
    # ── obrubi: alpha 1.0 znači „zadrži vlastitu alfu tokena”, samo kompozitiraj ──
    "border@card": ("border", 1.0, "card"),
    "border@background": ("border", 1.0, "background"),
    "border@muted": ("border", 1.0, "muted"),
    "input@card": ("input", 1.0, "card"),
    "input@background": ("input", 1.0, "background"),
    "input@muted": ("input", 1.0, "muted"),
    "sidebar-border@sidebar": ("sidebar-border", 1.0, "sidebar"),
}

#: Gdje se ploha koristi — ide u izlaznu tablicu da se brojka može smjestiti.
SURFACE_USE: dict[str, str] = {
    "background": "ploha stranice",
    "card": "kartice, paneli",
    "popover": "popover / tooltip",
    "sidebar": "lijeva navigacija",
    "secondary": "secondary gumb",
    "muted": "čipovi, prazna stanja",
    "muted/30": "BadgeGallery — neosvojen bedž",
    "muted/40": "info blok /register, odabrana krivulja",
    "muted/50": "hover stanja",
    "muted/60": "mono blok u povijesti pokušaja",
    "background/60": "mono blok detalja greške",
    "card/50": "stale-dim rezultata",
    "sidebar-accent/40": "ConceptRow hover",
    "sidebar-accent/60": "nav hover",
    "input/30": "input (dark varijanta)",
    "input/50": "disabled input",
    "correct-soft": "FeedbackPanel, čip „Riješeno”",
    "incorrect-soft": "FeedbackPanel, ErrorState, Run greška, Login/Register",
    "partial-soft": "FeedbackPanel",
    "accent-warm/5": "ConceptRow deep-link flash",
    "accent-warm/10": "BadgeStrip, ContinueCard, ljestvica „ja”",
    "accent-warm/20": "BadgeGallery — osvojen bedž",
    "incorrect/10": "ErrorState — krug ikone",
    "destructive/50@input": "obrub nevaljanog polja, unutarnji rub",
    "destructive/50": "obrub nevaljanog polja, vanjski rub",
    "destructive/40": "halo nevaljanog polja (ring-3)",
    "border@card": "obrub kartica, gumba, mono blokova",
    "border@background": "obrub na plohi stranice",
    "border@muted": "obrub na muted plohi",
    "input@card": "obrub polja (Login/Register)",
    "input@background": "obrub polja na plohi stranice",
    "input@muted": "obrub polja na muted plohi",
    "sidebar-border@sidebar": "granica sidebara (AppShell.tsx:88,89)",
}

#: ploha → {tekst-token: dokaz}
PAIRS: dict[str, dict[str, str]] = {
    "background": {"foreground": "○ AppShell", "muted-foreground": "○ AppShell"},
    "card": {
        "foreground": "○ svi ekrani",
        "muted-foreground": "○ svi ekrani",
        "accent-warm-text": "○ ProgressHero, AttemptRow.tsx:67",
        "correct": "○ ConceptRow",
        "incorrect": "○ AttemptRow",
        "partial": "○ StatsSummary.tsx:69",
        # ⚠️ UKLONJEN par `neutral` (dokaz je glasio „○ ConceptChip") — v. nalaz R-5.
        # `ConceptChip.tsx:33` za nepoznat tier renderira `text-muted-foreground`, NE
        # `text-neutral`. Riječ „neutralan" u komentaru :32 opisuje NAMJERU, ne token.
        # `grep -rn "neutral" frontend/src` → 0 Tailwind klasa. `--neutral` ima 0
        # potrošača u komponentama; jedini izvedeni potrošač je `monaco-theme.ts`
        # `rules[operator]`, a to je vrijednosna kopija koju mjeri `monaco_check.py`.
    },
    "popover": {"foreground": "○ ui/popover", "muted-foreground": "○ ui/popover"},
    "sidebar": {"muted-foreground": "● AppShell.tsx:71", "accent-warm-text": "○ AppShell"},
    "secondary": {"foreground": "○ ui/button variant=secondary"},
    "muted": {
        "muted-foreground": "● BadgeGallery.tsx:73,97",
        "foreground": "○ EmptyState",
        "accent-warm-text": "○ BadgeGallery",
    },
    "muted/30": {"muted-foreground": "○ BadgeGallery.tsx:62"},
    "muted/40": {
        "muted-foreground": "○ ConceptCurveCard, RegisterPage info blok",
        "foreground": "○ RegisterPage info blok",
        "accent-warm-text": "○ ConceptCurveCard",
    },
    "muted/50": {"muted-foreground": "○ ConceptCurveCard hover", "foreground": "○ hover"},
    "muted/60": {"muted-foreground": "○ AttemptRow.tsx:117"},
    "background/60": {"muted-foreground": "● FeedbackPanel.tsx:163, AttemptRow.tsx:138"},
    "card/50": {"muted-foreground": "○ RunResultPanel stale-dim"},
    "sidebar-accent/40": {"muted-foreground": "○ ConceptRow.tsx:117", "correct": "○ ConceptRow"},
    "sidebar-accent/60": {"muted-foreground": "○ AppShell.tsx:71 hover"},
    "input/30": {"foreground": "○ ui/input", "muted-foreground": "○ placeholder"},
    "input/50": {"muted-foreground": "○ disabled input"},
    "correct-soft": {
        "correct": "● FeedbackPanel.tsx:52-53, ContinueCard.tsx:129, TaskPage.tsx:288",
        "foreground": "○ FeedbackPanel.tsx:123",
        "muted-foreground": "○ FeedbackPanel.tsx:138,143,156,177,198",
        "accent-warm-text": "○ FeedbackPanel.tsx:147,169",
    },
    "incorrect-soft": {
        "incorrect": "● FeedbackPanel.tsx:64-65, LoginPage.tsx:105, RegisterPage.tsx:205",
        "foreground": "○ FeedbackPanel.tsx:123, ErrorState.tsx:35, RunResultPanel.tsx:114",
        "muted-foreground": "○ ErrorState.tsx:36, RunResultPanel.tsx:130, FeedbackPanel ×5",
        "accent-warm-text": "○ FeedbackPanel.tsx:147,169",
    },
    "partial-soft": {
        "partial": "● FeedbackPanel.tsx:58-59",
        "foreground": "○ FeedbackPanel.tsx:123",
        "muted-foreground": "○ FeedbackPanel ×5",
        "accent-warm-text": "○ FeedbackPanel.tsx:147,169",
    },
    "accent-warm/5": {"muted-foreground": "○ ConceptRow.tsx:110", "correct": "○ ConceptRow"},
    "accent-warm/10": {
        "accent-warm-text": "● BadgeStrip.tsx:47+51, ContinueCard.tsx:86",
        "muted-foreground": "○ LeaderboardTable.tsx:64",
    },
    "accent-warm/20": {"accent-warm-text": "● BadgeGallery.tsx:72, :96"},
    "incorrect/10": {"incorrect": "● ErrorState.tsx:32, guards.tsx:69"},
}

#: Parovi u kojima je „tekst” zapravo IKONA → prag je 3,00 (grafika), ne 4,50.
#: Ako isti par negdje nosi i pravi tekst, ostaje na 4,50 i to se ovdje NE upisuje.
GRAPHIC_ONLY: set[tuple[str, str]] = {
    ("incorrect/10", "incorrect"),  # samo AlertTriangle, bez teksta
}

#: Čipovi: vlastiti `-foreground` na vlastitom fillu. (fg-token, bg-token)
CHIPS: list[tuple[str, str]] = [
    ("accent-warm-foreground", "accent-warm"),
    ("primary-foreground", "primary"),
    ("secondary-foreground", "secondary"),
    ("sidebar-accent-foreground", "sidebar-accent"),
    ("tier-easy-foreground", "tier-easy"),
    ("tier-medium-foreground", "tier-medium"),
    ("tier-hard-foreground", "tier-hard"),
    ("difficulty-beginner-foreground", "difficulty-beginner"),
    ("difficulty-intermediate-foreground", "difficulty-intermediate"),
    ("difficulty-advanced-foreground", "difficulty-advanced"),
    ("difficulty-expert-foreground", "difficulty-expert"),
    ("difficulty-cross-module-foreground", "difficulty-cross-module"),
]

#: Plohe koje SAME nose značenje → mjere se prema okolnoj plohi, prag 3,00 (SC 1.4.11).
#: Ako padnu, a stanje nosi i ikona/tekst, to NIJE prekršaj nego ukras — v. #51.
SURFACE_VS_SURROUND: list[tuple[str, str]] = [
    ("accent-warm/5", "card"),
    ("accent-warm/10", "card"),
    ("accent-warm/20", "card"),
    ("muted/40", "card"),
    # ── obrubi: SC 1.4.11 traži 3:1 za „granicu komponente” ──────────────────
    # 🔴 Poučak #33: docstring je tvrdio „border ≥3:1", izmjereno je 1,25–1,62.
    # Ovi se retci zapisuju da tvrdnja više ne može živjeti nemjerena.
    ("border@card", "card"),
    ("border@background", "background"),
    ("border@muted", "muted"),
    ("input@card", "card"),
    ("input@background", "background"),
    ("input@muted", "muted"),
    ("sidebar-border@sidebar", "sidebar"),
    # ── nevaljano polje (ERRATA #52) ────────────────────────────────────────
    ("destructive/50@input", "input/30"),
    ("destructive/50", "card"),
    ("destructive/40", "card"),
]

AA_TEXT = 4.50
AA_NON_TEXT = 3.00


# ══════════════════════════════════════════════════════════════════════════════
#  SUKORIŠTENI SKUP — ulaz za ΔE provjeru cross-scale guarda (MASTER §2.7)
# ══════════════════════════════════════════════════════════════════════════════
#
# 🔴 ZAŠTO POSTOJI (NALAZ N-12). ΔE „do najbližeg semantičkog tokena" nad PUNIM skupom je
# pogrešna mjera: kažnjava kroma-token zbog boja koje se s njim nikad ne renderiraju
# zajedno. Pod tom je mjerom `--ring` ispao lošiji kao akromatski (0,067) nego kao tintan
# (0,102) — obrnuto od istine, jer je „najbliži" bio `difficulty-cross-module`, a
# `DifficultyChip` nije ni na jednom fokusabilnom elementu.
#
# SUKORIŠTEN = renderira se na ISTOM elementu ili mu je neposredno susjedan.
#
# Većina skupa IZVODI SE IZ `PAIRS` (tekst na plohi ⇒ sukorišten s tom plohom i s ostalim
# tekstom na njoj) — v. `co_used_map()` u `contrast_matrix.py`. Ovdje su samo dopune koje
# `PAIRS` ne može izraziti, jer `PAIRS` poznaje plohe, a ne fokus ni sadržaj editora.
#
# KAKO DOPUNITI KAD NASTANE NOVI FOKUSABILNI ELEMENT
#   1. `grep -rn "outline-ring\|ring-ring" frontend/src --include=*.tsx`
#   2. za svaki NOVI pogodak pročitaj što je UNUTAR tog elementa (i neposredno uz njega);
#   3. svaki semantički token koji ondje živi upiši u `CO_USED_EXTRA["ring"]` S CITATOM;
#   4. `python3 scripts/a11y/contrast_matrix.py --delta-e` i provjeri da nema 🔴.
# Isto vrijedi za nov gumb (`CO_USED_EXTRA["primary"]`) i za nov Monaco token (`MONACO`).

#: Pragovi ΔE (Oklab, euklidski). Nisu WCAG — orijentacija za razlučivost boja.
DE_COLLISION = 0.05   # 🔴 jedva razlučivo → kroma-token može se čitati kao član skale
DE_CLOSE = 0.10       # 🟡 blizu — dopušteno samo uz obrazloženje (oblik/kontekst razdvaja)

#: Monaco: SVI ovi tokeni dijele jedan pravokutnik (`TaskPage.tsx:327`, focus-within
#: kontejner), pa su međusobno sukorišteni SVI SA SVIMA. `monaco_check.py` mjeri samo
#: drift prema tokenu, a izrijekom NE mjeri razlučivost sintaksnih boja međusobno.
MONACO: dict[str, str] = {
    "foreground": "rules[''] / editor.foreground",
    "muted-foreground": "rules[comment] + editorLineNumber.foreground",
    "neutral": "rules[operator] + rules[delimiter]",
    "correct": "rules[string]",
    "chart-1": "rules[keyword]",
    "chart-2": "rules[number]",
    "chart-3": "rules[predefined]",
    "accent-warm": "editorCursor + editorLineNumber.activeForeground",
    "card": "editor.background",
}

#: kroma-token → {semantički token: citat}. Samo ono što PAIRS ne vidi.
CO_USED_EXTRA: dict[str, dict[str, str]] = {
    # ── fokus: prsten OKRUŽUJE sadržaj, pa mu je sve unutra sukorišteno ──
    "ring": {
        "tier-easy": "ConceptRow.tsx:75 (ConceptChip) unutar <Link> ConceptRow.tsx:117",
        "tier-medium": "isto — TIER_CLASS pokriva sva tri tiera",
        "tier-hard": "isto",
        "mastery-0": "MasteryBar ConceptRow.tsx:90 / MasteryHighlights.tsx:66, oba unutar <Link>",
        "mastery-25": "isto",
        "mastery-50": "isto + ikona stanja `text-mastery-50` ConceptRow.tsx:40",
        "mastery-75": "isto",
        "mastery-100": "isto",
        "correct": "CheckCircle2 ConceptRow.tsx:45 / MasteryHighlights.tsx:49 / ConceptCurveCard.tsx:64",
        "accent-warm": "XP čip FeedbackPanel.tsx:130 u istom flex redu kao CTA gumb",
        "accent-warm-text": "ConceptRow.tsx:110 deep-link flash na fokusiranom retku",
        "chart-1": "Monaco keyword unutar focus-within kontejnera TaskPage.tsx:327",
        "chart-2": "Monaco number, isto",
        "chart-3": "Monaco predefined, isto",
        "neutral": "Monaco operator, isto",
    },
    # ── primarni gumb: dijeli ekran s tier čipom i stoji NA verdict plohama ──
    "primary": {
        "tier-easy": "Submit gumb TaskPage.tsx:340 i ConceptChip TaskPage.tsx:277 — isti ekran",
        "tier-medium": "isto",
        "tier-hard": "isto",
        "accent-warm": "CTA i XP čip u istom redu, FeedbackPanel.tsx:130",
        "correct-soft": "CTA `Sljedeći zadatak` leži NA verdict plohi",
        "incorrect-soft": "isto",
        "partial-soft": "isto",
    },
}
CO_USED_EXTRA["sidebar-ring"] = CO_USED_EXTRA["ring"]

# 🔴 `primary-foreground` NAMJERNO NE nasljeđuje skup od `primary`. Prvi pokušaj ga je
# nasljedio i odmah dao LAŽNI POZITIV: `primary-foreground × incorrect-soft` = 0,0495 →
# „kolizija". Nije. `primary-foreground` je tekst UNUTAR gumba, a `-soft` je ploha IZA
# gumba; između njih stoji pun `primary` fill (14,24:1). Sukorištenost traži isti element
# ili NEPOSREDNU susjednost — visokokontrastna ploha između njih to prekida.
# Isti poučak kao #50: provjera koja utopi prave nalaze u lažnima neupotrebljiva je kao i
# ona koje nema. Zato: bez unosa (PAIRS mu ionako ne daje nijedan semantički susjed).

#: Parovi koji SU sukorišteni i JESU blizu, ali su svjesno prihvaćeni — s razlogom.
#: Bez ovoga bi provjera vikala na svakom pokretanju i prestala se čitati.
DE_ACCEPTED: dict[tuple[str, str], str] = {
    ("muted-foreground", "neutral"):
        "Monaco: komentar × operator. Zatečeno 0,0233 → predloženo 0,0213 — NIJE regresija "
        "palete nego posljedica toga što je `--neutral` (0 potrošača u komponentama) "
        "definiran gotovo kao `--muted-foreground`. Popravak je izbor DRUGOG tokena za "
        "`rules[operator]`, dizajnerska odluka o sintaksnim bojama — v. N-13 i #52.",
    ("correct", "chart-2"):
        "Monaco: string × number, 0,0861. Zatečeno i nepromijenjeno — obje su "
        "SEMANTIČKE (zamrznute), redizajn palete ih ne dira.",
}
