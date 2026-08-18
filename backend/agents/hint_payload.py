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
#: 🔴 `plan_mismatch` je dodan 2026-08-14 (ERRATA #66): njegov `detail` sastavlja
#: `_plan_mismatch_detail` iz IMENA ČVOROVA I INDEKSA plana, bez ijednog znaka
#: studentovog upita i bez teksta referentnog rješenja (tvrdi test
#: `test_detail_NE_SADRZI_referentni_upit`).
DETAIL_SAFE_TYPES = frozenset(
    {
        "row_mismatch",
        "empty_result",
        "syntax_error",
        "unsupported_eval",
        "plan_mismatch",
    }
)

#: Tip kojem se `detail` NE šalje, nego se oblik rješenja REKONSTRUIRA iz sheme.
#: Ključevi (`expected_result[0].keys()`) su oblik rješenja i pod B+ smiju van;
#: vrijednosti redaka nikad. Pohranjeni `detail` se NIKAD ne parsira.
RECONSTRUCT_COLUMNS_TYPE = "wrong_columns"

#: Tipovi koji šalju samo klasifikaciju. `execution_error` uz nju nosi `sqlstate`
#: (zatvoren šifrarnik, bez ijednog studentovog znaka); `timeout` nema ni to jer
#: mu čistoća poruke nije dokazana — nema živih uzoraka.
CLASSIFICATION_ONLY_TYPES = frozenset(
    {"execution_error", "timeout", "explain_submitted"}
)

#: 🔴 `explain_submitted` je ovdje, a NE u `DETAIL_SAFE_TYPES`, i razlog NIJE
#: privatnost — njegov je `detail` konstantan tekst bez ijednog studentovog znaka
#: i smio bi van. Razlog je što taj tekst ne nosi nikakav podatak o studentovoj
#: GREŠCI: on je uputa sučelja („predaj upit bez EXPLAIN"), ne opis onoga što je
#: student krivo zaključio. `DETAIL_SAFE_TYPES` propušta podatke o POKUŠAJU, a
#: ovdje pokušaja u tom smislu nema.
#:
#: 🔴 `plan_unavailable` se ovdje NE pojavljuje jer od ERRATE #69 uopće nije ishod
#: pokušaja — hint sloj ga ne može ni vidjeti (`unlocking_attempt` traži redak u
#: `attempts`, a njega nema).

#: 🔴 Tipovi kod kojih se LLM NE POZIVA — ide deterministički fallback.
#:
#: **PRAVILO:** LLM se poziva samo kad klasifikacija i payload ZAJEDNO određuju
#: dijagnozu. Inače ide deterministički fallback; ako fallbacka nema, hint se ne
#: nudi.
#:
#: Izvor pravila je preformulirana ERRATA #72, izmjerena nad 12 stvarnih hintova
#: kroz pun lanac: *kad klasifikacija NE određuje dijagnozu jednoznačno, a
#: `detail` se ne šalje, model rupu popuni iz `task_description` i to izgovori
#: kao činjenicu o studentovom upitu.* `task_description` ide UVIJEK, pa „bez
#: detalja" nikad nije značilo „bez konteksta" — samo bez konteksta o STUDENTU.
#:
#: Izmjereni primjerci (2/2 prolaza svaki):
#:   * `execution_error` — student je napisao `SELECT nepostojeca_kolona FROM
#:     orders`, payload je nosio samo `sqlstate=42703`, a model je odgovorio
#:     „provjeri naziv stupca `status`" — stupac koji student nije ni spomenuo,
#:     preuzet iz opisa zadatka.
#:   * `timeout` — student je napisao `SELECT count(*) FROM orders a, orders b,
#:     orders c, orders d`, a model je odgovorio „`DISTINCT` je primijenjen na
#:     previše stupaca"; `DISTINCT`a u upitu nema.
#:
#: 🔴 `explain_submitted` NIJE član iako je i on `CLASSIFICATION_ONLY`. Izmjereno
#: je siguran jer mu IME KLASE JEST dijagnoza: odgovor „dao si EXPLAIN plan
#: umjesto samog upita" je potpun bez ijednog podatka o upitu. Opasnost dakle ne
#: nosi izostanak detalja sam po sebi, nego NEDOODREĐENOST klasifikacije — i
#: zato konstanta nosi to ime, a ne popis.
UNDERDETERMINED_TYPES = frozenset({"execution_error", "timeout"})

#: Druga polovica iste podjele: tipovi kod kojih se LLM POZIVA.
#:
#: 🔴 Postoji EKSPLICITNO, a ne kao „sve što nije `UNDERDETERMINED_TYPES`". Da je
#: izveden komplementom, novi tip bi tiho upao u LLM granu i odluka o njemu ne bi
#: bila donesena nego zatečena — obrazac koji `test_potrosac_4` već sprječava za
#: politiku payloada. Ugovorni test tvrdi da ova dva skupa PARTICIONIRAJU
#: taksonomiju ishoda pokušaja: unija je cjelina, presjek je prazan.
LLM_TYPES = frozenset(
    {
        "syntax_error",
        "explain_submitted",
        "empty_result",
        "wrong_columns",
        "row_mismatch",
        "plan_mismatch",
        # Naslijeđen: više se ne emitira, ali ga nose zatečeni `attempts` retci.
        "unsupported_eval",
    }
)

#: 🔴 Pragovi se MORAJU poklapati s `prolog/rules.pl`: `weak_threshold(0.30)` i
#: `mastery_threshold(0.85)`. Isti obrazac kao `recommender_logic._MASTERED_THRESHOLD`.
_WEAK_THRESHOLD = 0.30
_MASTERED_THRESHOLD = 0.85


# 🔴 ERRATA #64 — POKUŠAJ POVUČEN 2026-08-14, prije mergea.
#
# Ovdje su stajali `_detect_order` i `expected_shape`: iz `expected_result` se
# izvodio očekivani poredak (stupac + smjer) i slao modelu, da za `row_mismatch`
# ne mora nagađati.
#
# IZMJERENO nad svih 80 aktivnih zadataka: poredak je detektiran u 40, a u **10**
# je PROTURJEČIO `ORDER BY`-u referentnog upita; još 2 zadatka poredak uopće
# nemaju. Najgori oblik su zadaci s višestrukim ključem (`ORDER BY
# prosjecna_ocjena DESC, product_id ASC`): primarni ključ ima izjednačenja pa nije
# monoton, sekundarni jest — pa bi se TIEBREAKER proglasio poretkom.
#
# Sužavanje na „točno jedan monoton stupac" ne spašava: 4 od 24 i dalje
# proturječe. Uz to Python uspoređuje stringove po codepointu, a `expected_result`
# je poredao PostgreSQL pod svojom kolacijom — za `['apple', 'Banana']` Python
# zaključi `desc`, dakle obrnuto od istine.
#
# 🔴 Poanta: tvrdnja bi išla uz prompt pravilo „osloni se na dane podatke", pa bi
# model netočan poredak iznosio SIGURNIJE nego kad nagađa. To je ista klasa kvara
# koju #64 opisuje, samo sustavna umjesto povremene.
#
# Jedini pouzdan izvor poretka je `ORDER BY` referentnog upita — a ovaj modul ga
# po dizajnu NE SMIJE ni spomenuti (`test_expected_query_is_never_read`). Proširenje
# tog opsega je odluka korisnika, ne izvedbeni detalj. ERRATA #64 ostaje OTVORENA.


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
        te NAJVIŠE JEDNO od `error_detail` / `expected_columns` / `sqlstate`.

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
