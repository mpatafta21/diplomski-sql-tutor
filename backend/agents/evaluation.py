"""Čista evaluacijska jezgra — bez SPADE, bez DB write-ova.

Eksponira:
  EvaluationOutcome  — rezultat evaluacije jednog SQL pokušaja
  evaluate()         — (task, query, runner) → EvaluationOutcome

Taksonomija grešaka (redoslijed provjere):
  syntax_error      — prazan/whitespace upit (sqlparse vrati prazan parse)
  unsupported_eval  — explain_plan / index_usage (plan-presence put nije implementiran)
  execution_error   — runner.execute() success=False (timeout → poseban error_type="timeout")
  correct           — compare().matches == True
  empty_result      — 0 actual redova, > 0 expected
  wrong_columns     — set stupaca se razlikuje (jak signal krivog upita)
  row_mismatch      — stupci OK, redovi krivi → verdict="partial"

NAPOMENA za sqlparse: parser je lenijentan — keyword typo-vi ("SELECT FORM x") prolaze
kroz sintaktičku provjeru i padaju na execution_error. Za robustnu sintaktičku provjeru
treba pg_parse/libpg_query — out of scope za MVP.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

import sqlparse

from app.db.models import Task
from scripts.lib.sandbox_runner import PlanResult, SandboxRunner

# ---------------------------------------------------------------------------
# Domenske konstante — JEDAN izvor istine (dijele ih evaluator, recommender i
# dijagnostičke skripte; NE kopirati popise).
# ---------------------------------------------------------------------------

#: Koncepti koji se ocjenjuju USPOREDBOM IZVEDBENOG PLANA uz redovnu usporedbu
#: redaka (M6). Rezultatska usporedba sama ih NE MOŽE ocijeniti: anti-pattern
#: (`LOWER(email) = …`, `customer_id::text = …`) vraća bajt-identične retke kao
#: index-friendly verzija — izmjereno 2026-08-14, v. ERRATA #66.
#:
#: 🔴 Popis je uzak NAMJERNO. Plan-grana se izvodi samo za ove koncepte, pa je
#: regresija na 80 aktivnih zadataka M1–M5 dokazivo nemoguća.
PLAN_CHECKED_CONCEPTS = frozenset({"explain_plan", "index_usage"})

#: Zadržano ime za recommender i testove koji su ga koristili kao „koncepti koje
#: treba maskirati". 🔴 Značenje se NIJE promijenilo mehanički (isti skup), ali
#: JEST semantički: koncepti više nisu neevaluabilni. Alias postoji da promjena
#: bude jedan commit, a ne sweep po sedam datoteka; uklanja se u Fazi 6.
UNSUPPORTED_CONCEPTS = PLAN_CHECKED_CONCEPTS

#: Čvorovi plana koji znače „indeks je upotrijebljen". Tri različita čvora, JEDAN
#: ishod učenja — zato potpis, a ne jednakost skupova (v. `plan_signature`).
INDEX_ACCESS_NODES = frozenset({"Index Scan", "Index Only Scan", "Bitmap Index Scan"})

#: Strategije spoja — predmet koncepta `explain_plan` (kako filtar mijenja izbor).
JOIN_METHOD_NODES = frozenset({"Nested Loop", "Hash Join", "Merge Join"})

#: Predani upit koji je i sam EXPLAIN — hvata se prije izvršavanja (v. `evaluate`).
_IS_EXPLAIN_RE = re.compile(r"^\s*EXPLAIN\b", re.IGNORECASE)

#: Perturbacije planera za `plan_is_stable`. Obje samo DODAJU planeru opcije koje
#: bi inače odbacio, pa plan koji se pod njima ne pomakne nije na rubu odluke.
#:
#: 🔴 `enable_nestloop` NIJE ovdje: on izravno zabranjuje strategiju koju
#: `explain_plan` zadaci uče, pa bi gate odbacio upravo ono što treba propustiti.
#: Zastavica koja zabranjuje cilj nije test stabilnosti nego test postojanja.
STABILITY_FLAGS: tuple[str, ...] = ("enable_seqscan=off", "enable_hashjoin=off")


@dataclass(frozen=True)
class PlanSignature:
    """Svojstva plana koja SU predmet učenja — sve ostalo se namjerno odbacuje.

    `Sort`, `Limit`, `Aggregate`, `Hash` i `Bitmap Heap Scan` variraju s
    formulacijom upita i nisu cilj nijednog M6 koncepta; da ulaze u usporedbu,
    točno rješenje bi padalo na kozmetici.

    🔴 `index_names` je tu jer `uses_index` sam po sebi LAŽE. Zadatak 83 traži
    index-friendly filtar, ali mu `ORDER BY id LIMIT 1` uvuče `orders_pkey` u
    plan — pa i CAST anti-pattern ispadne „koristi indeks" i prođe kao točan.
    Tek ime indeksa razlikuje „koristi indeks koji zadatak uči" od „koristi bilo
    koji indeks usput". ERRATA #66.
    """

    uses_index: bool
    index_names: frozenset[str]
    join_methods: frozenset[str]


def plan_signature(
    node_types: Iterable[str], index_names: Iterable[str] = ()
) -> PlanSignature:
    """Svedi plan na ono što se uspoređuje."""
    nodes = set(node_types)
    return PlanSignature(
        uses_index=bool(nodes & INDEX_ACCESS_NODES),
        index_names=frozenset(index_names),
        join_methods=frozenset(nodes & JOIN_METHOD_NODES),
    )


def signature_of(plan: PlanResult) -> PlanSignature:
    """`PlanResult` → `PlanSignature`; jedini put kojim ide ocjenjivanje."""
    return plan_signature(plan.node_types, plan.index_names)


#: Koncepti čiji `expected_query` je DML (INSERT/UPDATE/DELETE) → moraju se
#: izvršiti kroz `sandbox_readwrite` rolu u transakciji koja se UVIJEK rollbacka
#: (SandboxRunner.execute(dml=True)). Pod readonly rolom padali bi na
#: "permission denied" i student bi vidio lažno "Greška u SQL-u" (4.4-0c nalaz).
#: Derivacija iz PRIMARNOG koncepta — provjereno na svih 83 taska: identična
#: derivaciji iz SVIH koncepata i 100 % poklapanje sa sqlparse ground truthom.
DML_CONCEPTS = frozenset({"insert", "update", "delete"})


@dataclass
class EvaluationOutcome:
    is_correct: bool
    verdict: str            # "correct" | "partial" | "incorrect"
    error_type: str | None  # taksonomija dolje; None ako correct
    execution_time_ms: int
    rows_returned: int
    detail: str             # kratki opis za log/hint, nije za klasifikaciju
    #: PG SQLSTATE (Faza 5.1) — popunjen SAMO za execution_error/timeout.
    #: 🔴 Bijela lista selektivnog B+: `sqlstate` smije LLM-u, `detail` za te dvije
    #: grane NE smije (nosi doslovni redak upita). V. docs/faza-5-korak-0.md §A1.
    sqlstate: str | None = None


def plan_is_stable(
    query: str,
    runner: SandboxRunner,
    schema: str = "ecommerce_v1",
) -> tuple[bool, str]:
    """Je li plan ovog upita dovoljno stabilan da se po njemu smije ocjenjivati?

    Uvozni gate za M6 zadatke. Vraća `(stabilan, razlog)`; `razlog` je prazan kad
    je stabilan.

    🔴 **Povod nije teorija nego flaky test.** Plan za `customers` (200 redaka,
    3 stranice) prebacuje se između Seq Scana i Index Scana na sitnu promjenu
    statistike — dovoljno je da rollbackani DML iz drugog testa ostavi mrtve
    retke i podigne `relpages`. Zadatak čija ocjena ovisi o tome je li autovacuum
    upravo prošao nije zadatak nego generator nasumičnih ocjena.

    **Kriterij:** potpis plana mora ostati NEPROMIJENJEN pod svakom zastavicom iz
    `STABILITY_FLAGS`. Te zastavice planeru samo dodaju opcije; ako se plan pod
    njima ne pomakne, nije bio na rubu odluke.

    Izmjereno 2026-08-14: `customers WHERE email = …` pada (margina 1.48x), a
    `orders WHERE customer_id = 42`, `order_items WHERE order_id = …`,
    `orders ORDER BY order_date DESC LIMIT 10` i spoj sa selektivnim filtrom
    prolaze (margina 1.00x — indeks je izabran bezuvjetno).
    """
    osnovni = runner.explain(query, schema=schema)
    if not osnovni.success:
        return False, f"plan nije dohvatljiv: {osnovni.error or 'nepoznata greška'}"

    osnovni_sig = signature_of(osnovni)

    for flag in STABILITY_FLAGS:
        pod_flagom = runner.explain(query, schema=schema, planner_flags=(flag,))
        if not pod_flagom.success:
            return False, f"plan nije dohvatljiv uz {flag}"
        if signature_of(pod_flagom) != osnovni_sig:
            return False, (
                f"potpis plana se mijenja uz {flag} — planer je na rubu odluke, "
                "pa bi ocjena ovisila o statistici umjesto o upitu"
            )

    return True, ""


def _verify_plan_if_needed(
    task: Task,
    submitted_query: str,
    runner: SandboxRunner,
    plan_checked: bool,
    correct_outcome: EvaluationOutcome,
) -> EvaluationOutcome:
    """Za M6 koncepte: točni redci NISU dovoljni — plan mora odgovarati referentnom.

    🔴 Tvrdnja o planu NIJE nigdje pohranjena. Zadatak je već nosi — to je njegov
    `expected_query` — pa se oba upita EXPLAIN-aju u ISTOM trenutku i uspoređuju
    im se potpisi. Posljedice tog izbora:

      - tvrdnja ne može zastarjeti (referentni upit i tvrdnja su isti objekt),
      - nema nove kolone ni popisa `source_id`-eva u kodu (koji bi zastario tiho,
        ista klasa kao netočan docstring iz ERRATE #45),
      - preživljava reseed sandboxa: obje strane mjere se nad istim podacima pa
        se pomiču zajedno.

    Redoslijed je bitan: ovo se zove TEK kad se redci poklapaju. Kad su redci
    krivi, korisnija je poruka o redcima — student još nije ni došao do pitanja
    plana.

    Ako EXPLAIN ne uspije (npr. upit prođe izvršavanje ali ne i planiranje),
    vraća se `unsupported_eval` — zadatak se NE proglašava točnim na temelju
    neprovjerene tvrdnje.
    """
    if not plan_checked:
        return correct_outcome

    submitted_plan = runner.explain(submitted_query, schema=task.sandbox_schema)
    reference_plan = runner.explain(task.expected_query, schema=task.sandbox_schema)

    if not submitted_plan.success or not reference_plan.success:
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="unsupported_eval",
            execution_time_ms=correct_outcome.execution_time_ms,
            rows_returned=correct_outcome.rows_returned,
            detail="Plan izvedbe nije bilo moguće dohvatiti.",
        )

    submitted_sig = signature_of(submitted_plan)
    reference_sig = signature_of(reference_plan)

    if submitted_sig == reference_sig:
        return correct_outcome

    return EvaluationOutcome(
        is_correct=False,
        verdict="incorrect",
        error_type="plan_mismatch",
        execution_time_ms=correct_outcome.execution_time_ms,
        rows_returned=correct_outcome.rows_returned,
        detail=_plan_mismatch_detail(submitted_sig, reference_sig),
    )


def _plan_mismatch_detail(submitted: PlanSignature, reference: PlanSignature) -> str:
    """Opis razlike planova — svojstvo PLANA, nikad tekst referentnog upita.

    🔴 Ovaj `detail` ide i u hint payload, pa ne smije nositi rješenje. Govori
    ŠTO plan radi (koristi li indeks, kojom strategijom spaja), a to je upravo
    ono što opis zadatka od studenta i traži — dakle ne otkriva ništa novo.
    """
    dijelovi: list[str] = []

    if submitted.uses_index != reference.uses_index:
        dijelovi.append(
            "upit ne koristi indeks, a rješenje ga koristi"
            if reference.uses_index
            else "upit koristi indeks, a traži se izvedba bez njega"
        )

    if submitted.join_methods != reference.join_methods:
        dobiveno = ", ".join(sorted(submitted.join_methods)) or "bez spoja"
        trazeno = ", ".join(sorted(reference.join_methods)) or "bez spoja"
        dijelovi.append(f"strategija spoja je {dobiveno}, a traži se {trazeno}")

    razlika = "; ".join(dijelovi) if dijelovi else "plan izvedbe se razlikuje"
    return f"Rezultat je točan, ali {razlika}."


def evaluate(
    task: Task,
    submitted_query: str,
    runner: SandboxRunner,
    primary_concept_code: str | None = None,
) -> EvaluationOutcome:
    """Evaluiraj submitted_query na zadanom tasku.

    Args:
        task: SQLAlchemy Task objekt s expected_result (JSONB lista diktova).
        submitted_query: SQL koji je student predao.
        runner: SandboxRunner spojen na sandbox bazu.
        primary_concept_code: Primarni koncept taska (npr. "explain_plan"). Ako je
            u _UNSUPPORTED_CONCEPTS, vraća unsupported_eval odmah.

    Returns:
        EvaluationOutcome s klasifikacijom i metrikama.
    """

    # ------------------------------------------------------------------
    # 1. Provjera syntax_error (samo očiti slučajevi — empty/whitespace)
    # ------------------------------------------------------------------
    stripped = submitted_query.strip()
    if not sqlparse.parse(stripped):
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="syntax_error",
            execution_time_ms=0,
            rows_returned=0,
            detail="Prazan ili neprepoznatljiv upit",
        )

    # ------------------------------------------------------------------
    # 2. M6 guard: predani upit je i sam EXPLAIN
    #    `EXPLAIN EXPLAIN …` je sintaksna greška, a student bi dobio nerazumljivu
    #    poruku iz baze. Plan se ovdje traži interno — student predaje OBIČAN upit.
    # ------------------------------------------------------------------
    plan_checked = primary_concept_code in PLAN_CHECKED_CONCEPTS
    if plan_checked and _IS_EXPLAIN_RE.match(stripped):
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="plan_mismatch",
            execution_time_ms=0,
            rows_returned=0,
            detail=(
                "Predaj obični upit, bez EXPLAIN. Plan izvedbe provjerava se "
                "automatski; EXPLAIN slobodno koristi kroz Pokreni dok istražuješ."
            ),
        )

    # ------------------------------------------------------------------
    # 3. Izvršavanje u sandboxu
    # ------------------------------------------------------------------
    # DML taskovi (M4) MORAJU ići kroz readwrite rolu + transakciju s ROLLBACK-om;
    # SELECT ostaje readonly. Bez ovoga svaki INSERT/UPDATE/DELETE pada na
    # "permission denied" (execution_error) — 9/83 taskova bilo je neocjenjivo.
    is_dml = primary_concept_code in DML_CONCEPTS
    result = runner.execute(
        submitted_query, schema=task.sandbox_schema, dml=is_dml
    )

    if not result.success:
        if "Statement timeout" in (result.error or ""):
            error_type = "timeout"
        else:
            error_type = "execution_error"
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type=error_type,
            execution_time_ms=result.execution_time_ms,
            rows_returned=0,
            detail=result.error or "",
            sqlstate=result.sqlstate,
        )

    # ------------------------------------------------------------------
    # 4. Rubni slučaj: expected_result prazan
    # ------------------------------------------------------------------
    expected: list[dict] = task.expected_result or []

    if not expected:
        if not result.rows:
            return _verify_plan_if_needed(
                task,
                submitted_query,
                runner,
                plan_checked,
                EvaluationOutcome(
                    is_correct=True,
                    verdict="correct",
                    error_type=None,
                    execution_time_ms=result.execution_time_ms,
                    rows_returned=0,
                    detail="OK",
                ),
            )
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="row_mismatch",
            execution_time_ms=result.execution_time_ms,
            rows_returned=len(result.rows),
            detail=f"Očekivano 0 redova, dobiveno {len(result.rows)}",
        )

    # ------------------------------------------------------------------
    # 5. Usporedba rezultata (runner.compare već normalizira Decimal/datetime)
    # ------------------------------------------------------------------
    cmp = runner.compare(result, expected, query=submitted_query)

    if cmp.matches:
        return _verify_plan_if_needed(
            task,
            submitted_query,
            runner,
            plan_checked,
            EvaluationOutcome(
                is_correct=True,
                verdict="correct",
                error_type=None,
                execution_time_ms=result.execution_time_ms,
                rows_returned=len(result.rows),
                detail="OK",
            ),
        )

    # ------------------------------------------------------------------
    # 6. Klasifikacija neuspjeha — STRUKTURNO (ne parsiraj diff_summary)
    # ------------------------------------------------------------------

    # 6a. Prazan rezultat (0 redova, a expected ima ≥1)
    if not result.rows:
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="empty_result",
            execution_time_ms=result.execution_time_ms,
            rows_returned=0,
            detail=f"Prazan rezultat, očekivano {len(expected)} redova",
        )

    # 6b. Krivi stupci → incorrect (jak signal pogrešnog pristupa)
    actual_cols = set(result.column_names)
    expected_cols = set(expected[0].keys())

    if actual_cols != expected_cols:
        return EvaluationOutcome(
            is_correct=False,
            verdict="incorrect",
            error_type="wrong_columns",
            execution_time_ms=result.execution_time_ms,
            rows_returned=len(result.rows),
            detail=(
                f"Stupci se razlikuju — dobiveni: {sorted(actual_cols)}, "
                f"očekivani: {sorted(expected_cols)}"
            ),
        )

    # 6c. Stupci OK, redovi krivi → partial
    return EvaluationOutcome(
        is_correct=False,
        verdict="partial",
        error_type="row_mismatch",
        execution_time_ms=result.execution_time_ms,
        rows_returned=len(result.rows),
        detail=cmp.diff_summary,
    )
