"""Gradnja payloada za LLM hint — selektivni B+ (Faza 5.1, §C).

🔴 OVO JE JEDINA TOČKA na kojoj podaci o studentovom radu napuštaju sustav.
Presuda §A1 plana 5.0 donesena je nakon mjerenja nad živom bazom, i mjerenje ju je
SUZILO u odnosu na prvotnu namjeru:

  - `execution_error` `detail` nosi **doslovni redak studentovog upita** (PG `LINE n:`
    kontekst); jedan živi uzorak sadrži i zaostali komentar iz editora,
  - `wrong_columns` `detail` nabraja **studentove aliase** (`product_count`, `count`).

Zato je bijela lista **po `error_type`**, a **default grana je ODBIJANJE**: nov tip
greške u budućnosti ne smije tiho procuriti time što nitko nije ažurirao ovaj modul.

🔴 `ComparisonResult.first_mismatch` nosi STVARNE RETKE PODATAKA. Danas se ne
perzistira i 5.1 ga NE SMIJE početi koristiti. Ne uvoziti ga ovamo ni pod čim.
"""

from __future__ import annotations

from typing import Any

from app.db.models import Task

#: Tipovi kojima cijeli `detail` smije van — sadrže isključivo brojeve, indekse
#: redaka ili konstantan tekst. Provjereno nad svim granama `evaluation.py`.
DETAIL_SAFE_TYPES = frozenset(
    {"row_mismatch", "empty_result", "syntax_error", "unsupported_eval"}
)

#: Tip kojem se `detail` NE šalje, nego se oblik rješenja REKONSTRUIRA iz sheme.
#: Ključevi (`expected_result[0].keys()`) su oblik rješenja i pod B+ smiju van;
#: vrijednosti redaka nikad. Pohranjeni `detail` se NIKAD ne parsira.
RECONSTRUCT_COLUMNS_TYPE = "wrong_columns"

#: Tipovi koji šalju samo klasifikaciju. `execution_error` uz nju nosi `sqlstate`
#: (zatvoren šifrarnik, bez ijednog studentovog znaka); `timeout` nema ni to jer
#: mu čistoća poruke nije dokazana — nema živih uzoraka.
CLASSIFICATION_ONLY_TYPES = frozenset({"execution_error", "timeout"})

#: 🔴 Pragovi se MORAJU poklapati s `prolog/rules.pl`: `weak_threshold(0.30)` i
#: `mastery_threshold(0.85)`. Isti obrazac kao `recommender_logic._MASTERED_THRESHOLD`.
_WEAK_THRESHOLD = 0.30
_MASTERED_THRESHOLD = 0.85


def _detect_order(rows: list[dict]) -> dict[str, str] | None:
    """Je li očekivani rezultat strogo monoton po nekom stupcu → (stupac, smjer).

    STROGA monotonost namjerno: kod jednakih vrijednosti poredak nije određen tim
    stupcem, pa bi tvrdnja „sortirano po X" bila nagađanje — a nagađanje je upravo
    ono što ERRATA #64 popravlja.

    Vraća oblik, ne vrijednosti: ime stupca (ključ, ne podatak) i smjer.
    """
    if len(rows) < 2:
        return None
    for col in rows[0]:
        vals = [r.get(col) for r in rows]
        if any(v is None for v in vals):
            continue
        try:
            if all(a < b for a, b in zip(vals, vals[1:])):
                return {"column": col, "direction": "asc"}
            if all(a > b for a, b in zip(vals, vals[1:])):
                return {"column": col, "direction": "desc"}
        except TypeError:
            # Nehomogen tip u stupcu — usporedba nije definirana, preskoči.
            continue
    return None


def expected_shape(task: Task) -> dict[str, Any]:
    """Strukturni opis OČEKIVANOG rezultata — oblik, nikad vrijednosti.

    🔴 ERRATA #64. Za `row_mismatch` je payload nosio samo `detail`, a taj string
    zna biti `Row 0 differs` — interna dijagnostika bez ijedne činjenice o tome
    ŠTO se očekuje. Model je prazninu popunjavao izmišljanjem i u jednom mjerenju
    dao **netočan SQL** („prvo LIMIT, pa ORDER BY"). Kad payload nosi tvrdu
    činjenicu (kao `expected_columns` kod `wrong_columns`), savjet je bio točan.

    Sve troje se izvodi iz `expected_result`, **bez ijednog znaka studentovog
    upita** — privatnosna odluka 5.0 (selektivni B+) ostaje netaknuta.
    """
    expected = task.expected_result or []
    if not expected or not isinstance(expected[0], dict):
        return {}
    # 🔴 Šalje se SAMO poredak, i to je suženo DVAPUT nakon mjerenja na živom
    # modelu (2026-08-14). Obje odbačene stavke izgledale su korisno na papiru:
    #
    #   `expected_columns` — model sortiranu listu čita kao PROPISANI REDOSLIJED
    #   stupaca i savjetuje preslagivanje SELECT-a („stupci su (country, id,
    #   name)" — to je abecedni poredak, ne poredak rezultata). Uz to je suvišan:
    #   `row_mismatch` po definiciji znači da su stupci TOČNI.
    #
    #   `expected_row_count` — kad se brojevi RAZLIKUJU, `detail` ih već nosi
    #   („Row count mismatch: actual=30 vs expected=3"). Kad se poklapaju (oblik
    #   „Row 0 differs"), broj retka navodi model da govori o broju redaka,
    #   dakle o nečemu što nije problem.
    #
    # Ostaje jedina činjenica koju `detail` NIKAD ne nosi: očekivani poredak.
    order = _detect_order(expected)
    return {"expected_order": order} if order is not None else {}


def mastery_band(p_l: float | None) -> str | None:
    """Pretvori BKT vjerojatnost u grubu oznaku.

    🔴 Zašto ne šaljemo `p_l` kao broj (odluka korisnika 2026-08-12): sirova
    vrijednost je preciznija procjena studenta nego što hint traži, a njezine
    znamenke su se sudarale s brojčanim vrijednostima iz `expected_result` pri
    guard provjeri (105 pogodaka). Gruba oznaka rješava oboje: **manje podataka o
    studentu izlazi iz sustava**, a guard ostaje čitljiv.

    Granice su iste kao u Prologu, pa oznaka znači isto što i ondje.
    """
    if p_l is None:
        return None
    if p_l < _WEAK_THRESHOLD:
        return "nisko"
    if p_l < _MASTERED_THRESHOLD:
        return "srednje"
    return "visoko"


def build_hint_payload(
    *,
    task: Task,
    error_type: str,
    detail: str | None,
    sqlstate: str | None,
    concept_code: str | None,
    p_l: float | None,
) -> dict[str, Any]:
    """Sastavi payload za LLM. Zatvoren skup polja, bijela lista po `error_type`.

    Args:
        task: Zadatak — koriste se SAMO `description` i (za `wrong_columns`)
            ključevi prvog retka `expected_result`. `expected_query` se NE dira.
        error_type: Klasifikacija iz `evaluation.py`.
        detail: `attempts.detail`. Prosljeđuje se SAMO za `DETAIL_SAFE_TYPES`.
        sqlstate: PG SQLSTATE, samo za `execution_error`.
        concept_code: Koncept koji student vježba.
        p_l: BKT procjena znanja tog koncepta. Šalje se kao GRUBA oznaka
            (`mastery_band`), nikad kao sirovi broj.

    Returns:
        Dict s poljima: `task_description`, `concept`, `mastery`, `error_type`,
        te najviše jedan NOSAČ SIGNALA O STUDENTU (`error_detail` / `sqlstate`).

        🔴 Pravilo „najviše jedno polje" prošireno je 2026-08-14 (ERRATA #64):
        `row_mismatch` uz `error_detail` nosi i strukturni opis očekivanog
        rezultata (`expected_row_count`, `expected_columns`, `expected_order`).
        To NIJE slabljenje: ta polja se izvode iz `expected_result` i ne nose
        nijedan znak studentovog rada, pa se ne zbrajaju s nosačem o studentu.
        Ograničenje koje ostaje: iz `expected_result` izlazi samo OBLIK (broj
        redaka, imena stupaca, smjer sortiranja) — nikad vrijednost retka.

    🔴 `task_description` je JEDINO polje koje se doslovno citira iz zadatka.
    Izuzeto je iz guard provjere VRIJEDNOSTI jer je problemski tekst koji student
    ionako vidi u sučelju — izmjereno, 11 od 80 opisa sadrži vrijednost koja se
    pojavljuje i u `expected_result` (npr. „samousluga", „processing"). Slanje ne
    otkriva ništa novo. Protiv `expected_query` se i dalje provjerava.
    """
    payload: dict[str, Any] = {
        "task_description": task.description,
        "concept": concept_code,
        "mastery": mastery_band(p_l),
        "error_type": error_type,
    }

    if error_type in DETAIL_SAFE_TYPES:
        if detail:
            payload["error_detail"] = detail
        if error_type == "row_mismatch":
            # 🔴 ERRATA #64: `detail` sam („Row 0 differs") ne kaže NIŠTA o tome
            # što se očekuje, pa je model izmišljao. Strukturni opis dolazi uz
            # njega, ne umjesto njega — `detail` u drugim oblicima nosi brojeve
            # redaka koji su korisni („actual=30 vs expected=3").
            payload.update(expected_shape(task))
    elif error_type == RECONSTRUCT_COLUMNS_TYPE:
        # 🔴 REKONSTRUKCIJA, ne parsiranje pohranjenog `detail`a: taj string
        # miješa očekivane stupce sa STUDENTOVIM ALIASIMA.
        expected = task.expected_result or []
        if expected and isinstance(expected[0], dict):
            payload["expected_columns"] = sorted(expected[0].keys())
    elif error_type in CLASSIFICATION_ONLY_TYPES:
        if error_type == "execution_error" and sqlstate:
            payload["sqlstate"] = sqlstate
    # 🔴 DEFAULT: ništa se ne dodaje. Nepoznat `error_type` prolazi kroz sve
    # grane i izlazi sa samom klasifikacijom — fail-closed, bez tihog curenja.

    return payload
