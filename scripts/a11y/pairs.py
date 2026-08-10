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
        "neutral": "○ ConceptChip",
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
]

AA_TEXT = 4.50
AA_NON_TEXT = 3.00
