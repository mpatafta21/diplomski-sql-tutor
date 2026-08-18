"""Sweep integriteta zadataka (Faza 4.4-0b, KORAK 1) — READ-ONLY dijagnostika.

Pokreni iz ``backend/``::

    uv run python -m scripts.sweep_task_integrity            # tablica + JSON sažetak
    uv run python -m scripts.sweep_task_integrity --json     # samo JSON
    uv run python -m scripts.sweep_task_integrity --deep 5   # + duboka usporedba za N padova

INVARIJANTA KOJU TESTIRA: referentni upit (``tasks.expected_query``) MORA na
vlastitom tasku dati ``is_correct=True``. Svaki drugi ishod znači pokvaren task
(referenca ne reproducira ``expected_result``).

🔴 NE POPRAVLJA NIŠTA. Ne piše u bazu, ne stvara attempte, ne dira agente:
koristi ČISTU evaluacijsku jezgru ``agents.evaluation.evaluate`` — ISTI put
kojim ide studentov upit (ista taksonomija grešaka, ista ``runner.compare``
normalizacija) — samo bez perzistencije.

🔴 ERRATA #66: koncepti ``explain_plan``/``index_usage`` (modul 6) VIŠE NE vraćaju
``unsupported_eval`` — ocjenjuju se plan-presence evaluacijom i njihovi padovi su
STVARNI padovi. Uz redovni sweep za njih se pokreće i ``check_plan_stability``:
referentni upit mora birati indeks (ili strategiju spoja) bezuvjetno, inače bi
ocjena ovisila o statistici umjesto o upitu.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agents.evaluation import (
    PLAN_CHECKED_CONCEPTS,
    evaluate,
    plan_is_stable,
    signature_of,
)
from agents.evaluator_agent import _sandbox_conn_string
from app.db.models import Attempt, Concept, Module, Task, TaskConcept
from app.db.session import SessionLocal
from scripts.lib.sandbox_runner import SandboxRunner

# 🔴 PRAZAN od ERRATE #66. Dotad su M6 koncepti vraćali `unsupported_eval` po
# dizajnu, pa su se njihovi padovi izuzimali iz `failing_genuine`. Sada su M6
# zadaci AKTIVNI i evaluabilni — da je popis ostao, svaki bi njihov pad bio tiho
# izuzet iz gatea i sweep bi prolazio zelen nad pokvarenim zadatkom.
_BY_DESIGN_UNSUPPORTED: frozenset[str] = frozenset()


@dataclass
class TaskRow:
    task_id: int
    #: STABILNI ključ (NALAZ #21) — task_id je runtime detalj koji se mijenja
    #: pri svakom reseedu (SERIAL), source_id ne. Izvještaji citiraju source_id.
    source_id: str
    title: str
    difficulty: int
    module_number: int
    primary_concept: str | None
    is_correct: bool
    error_type: str | None
    detail: str
    rows_returned: int


def _load_tasks(session: Session) -> list[tuple[Task, str | None, int]]:
    """(Task, primary_concept_code, module_number) za SVE aktivne taskove, po id-u."""
    tasks = (
        session.execute(select(Task).where(Task.is_active.is_(True)).order_by(Task.id))
        .scalars()
        .all()
    )
    primary = dict(
        session.execute(
            select(TaskConcept.task_id, Concept.code)
            .join(Concept, Concept.id == TaskConcept.concept_id)
            .where(TaskConcept.is_primary.is_(True))
        ).all()
    )
    modules = dict(session.execute(select(Module.id, Module.number)).all())
    return [(t, primary.get(t.id), modules.get(t.module_id, -1)) for t in tasks]


def run_sweep() -> list[TaskRow]:
    runner = SandboxRunner(_sandbox_conn_string())
    out: list[TaskRow] = []
    with SessionLocal() as session:
        for task, primary, module_number in _load_tasks(session):
            outcome = evaluate(task, task.expected_query, runner, primary)
            out.append(
                TaskRow(
                    task_id=task.id,
                    source_id=task.source_id or "",
                    title=task.title,
                    difficulty=task.difficulty,
                    module_number=module_number,
                    primary_concept=primary,
                    is_correct=outcome.is_correct,
                    error_type=outcome.error_type,
                    detail=outcome.detail,
                    rows_returned=outcome.rows_returned,
                )
            )
    return out


def deep_compare(task_id: int) -> dict:
    """DOSLOVNA usporedba: expected_query rezultat vs expected_result."""
    runner = SandboxRunner(_sandbox_conn_string())
    with SessionLocal() as session:
        task = session.get(Task, task_id)
        if task is None:
            return {"task_id": task_id, "error": "task not found"}
        res = runner.execute(task.expected_query, schema=task.sandbox_schema, dml=False)
        expected: list[dict] = task.expected_result or []
        return {
            "task_id": task_id,
            "title": task.title,
            "expected_query": task.expected_query,
            "exec_success": res.success,
            "exec_error": res.error,
            "actual_row_count": len(res.rows),
            "expected_row_count": len(expected),
            "actual_columns": sorted(res.column_names),
            "expected_columns": sorted(expected[0].keys()) if expected else [],
            "actual_first3": res.rows[:3],
            "expected_first3": expected[:3],
        }


def check_plan_stability() -> list[tuple[str, str]]:
    """Uvozni gate za M6: referentni upit mora imati STABILAN plan.

    Vraća `[(source_id, razlog), …]` za aktivne zadatke koji padaju.

    🔴 **Zašto gate postoji.** Tri zatečena M6 zadatka (79, 80, 82) tražila su od
    studenta index-friendly upit, a njihov referentni upit nad `customers` (200
    redaka) daje **Seq Scan** — planer je u pravu, zadatak nije. Nijedna
    provjera to nije hvatala jer se integritet mjerio samo usporedbom redaka, a
    redci su se poklapali. ERRATA #66.

    Zadatak čiji plan ovisi o prolaznoj statistici daje **nasumične ocjene**:
    isti upit istog studenta prolazi ili pada ovisno o tome je li autovacuum
    upravo prošao. Provjerava se samo za `PLAN_CHECKED_CONCEPTS` — ostali se po
    planu i ne ocjenjuju.
    """
    runner = SandboxRunner(_sandbox_conn_string())
    out: list[tuple[str, str]] = []
    with SessionLocal() as session:
        for task, primary, _module in _load_tasks(session):
            if primary not in PLAN_CHECKED_CONCEPTS:
                continue
            stabilan, razlog = plan_is_stable(
                task.expected_query, runner, schema=task.sandbox_schema
            )
            if not stabilan:
                out.append((task.source_id or f"task:{task.id}", razlog))
    return out


def _sandbox_index_names(runner: SandboxRunner, schema: str) -> set[str]:
    """Imena indeksa sheme, iz `pg_indexes`.

    🔴 Izvor istine je BAZA, ne popis u kodu. Popis bi bio sadržaj kataloga u
    evaluacijskoj jezgri — konstanta koju je `m6-transverzalni-korak-0.md` §C.1
    odbio, i koja bi tiho zastarjela pri prvoj promjeni sheme sandboxa.
    `current_schema()` je ispravan jer `execute` postavi `search_path`.
    """
    res = runner.execute(
        "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema()",
        schema=schema,
    )
    if not res.success:
        return set()
    return {str(r["indexname"]) for r in res.rows}


def check_plan_claim() -> list[tuple[str, str]]:
    """Gate: svojstvo koje zadatak IZGOVARA mora stajati u referentnom planu.

    Vraća `[(source_id, razlog), …]` za aktivne zadatke koji padaju.

    🔴 **Zašto postoji.** Gate diskriminacije živi pri autorstvu
    (`manual_tasks_m6.py`) i pokriva samo zadatke koje je ta skripta napisala.
    Zadatak 81 je došao kroz `import_dataset`, nema `anti_pattern`, i ondje ga
    grana `anti is None` propušta bez ijedne provjere — tiho (ERRATA #78).
    Ovaj gate ne treba katalog u kodu: zadatak sam nosi svoju tvrdnju, isto
    načelo koje §C.2 već primjenjuje na `expected_query`.

    **Pravilo je PO KONCEPTU**, jer se koncepti ne poučavaju istim svojstvom:

    * ``index_usage``  — indeks imenovan u `description` mora biti u
      `index_names` potpisa referentnog plana. Traži se DOSLOVAN niz; provjereno
      da nijedno ime indeksa nije podniz drugog, pa križni pogodak nije moguć.
    * ``explain_plan`` — `join_methods` referentnog plana ne smije biti prazan.
      To je §C.4 („potpis referentnog upita nije prazan") primijenjen na polje
      koje taj koncept poučava.

    🔴 Spojna grana je NAMJERNO slabija: tvrdi da referenca izvodi NEKU
    strategiju spoja, ne onu koju opis poučava. Jača tvrdnja iz opisa nije
    izvediva jer je pedagogija `explain_plan`-a kontrastivna po konstrukciji —
    opis mora imenovati OBA plana da bi poučavao razliku. Svojstvo koncepta, ne
    rupa u gateu; v. `docs/m6-plan-presence-wrapup.md` §I.4.

    🔴 **TVRDO PRAVILO PROTIV ŠUTNJE.** Zadatak koji ne potpada ni pod jedno
    pravilo PADA s vlastitim `source_id`. Tiho preskakanje je točno mana zbog
    koje varijanta B nije izabrana — gate ne smije ponoviti istu.
    """
    runner = SandboxRunner(_sandbox_conn_string())
    indeksi_po_shemi: dict[str, set[str]] = {}
    out: list[tuple[str, str]] = []

    with SessionLocal() as session:
        for task, primary, _module in _load_tasks(session):
            if primary not in PLAN_CHECKED_CONCEPTS:
                continue

            sid = task.source_id or f"task:{task.id}"
            schema = task.sandbox_schema
            plan = runner.explain(task.expected_query, schema=schema)
            if not plan.success:
                out.append((sid, f"EXPLAIN referentnog upita ne uspijeva: {plan.error}"))
                continue
            potpis = signature_of(plan)

            if primary == "index_usage":
                if schema not in indeksi_po_shemi:
                    indeksi_po_shemi[schema] = _sandbox_index_names(runner, schema)
                imenovani = sorted(
                    i for i in indeksi_po_shemi[schema] if i in (task.description or "")
                )
                if not imenovani:
                    out.append(
                        (sid, "opis ne imenuje nijedan indeks — zadatak ne izgovara "
                              "što poučava, pa se tvrdnja o planu ne može provjeriti")
                    )
                    continue
                fali = [i for i in imenovani if i not in potpis.index_names]
                if fali:
                    out.append(
                        (sid, f"opis obećava {fali}, a plan koristi "
                              f"{sorted(potpis.index_names) or '[]'}")
                    )

            elif primary == "explain_plan":
                if not potpis.join_methods:
                    out.append(
                        (sid, "join_methods referentnog plana je PRAZAN — zadatak "
                              "koncepta explain_plan ne poučava nijednu strategiju spoja")
                    )

            else:
                out.append(
                    (sid, f"koncept {primary!r} je u PLAN_CHECKED_CONCEPTS, a gate za "
                          "njega nema pravilo — ne zna što tvrditi")
                )

    return out

def count_unsupported_attempts() -> int:
    """Broj perzistiranih attempta s error_type='unsupported_eval'.

    MORA biti 0: takav attempt daje 0 XP i BKT KAZNU (uz redak u
    skill_mastery_history) za zadatak koji sustav ne zna ocijeniti — a zna
    procuriti i na evaluabilne sekundarne koncepte (4.4-0d KORAK 6: jedan takav
    attempt zagadio je `where_filter`). Ako ih ima, recommender ih je opet
    ponudio → maska Kat. C je probijena.
    """
    with SessionLocal() as session:
        return int(
            session.scalar(
                select(func.count())
                .select_from(Attempt)
                .where(Attempt.error_type == "unsupported_eval")
            )
            or 0
        )


def _summarize(rows: list[TaskRow]) -> dict:
    failures = [r for r in rows if not r.is_correct]
    by_design = [
        r for r in failures if (r.primary_concept or "") in _BY_DESIGN_UNSUPPORTED
    ]
    genuine = [r for r in failures if r not in by_design]
    return {
        "total_active_tasks": len(rows),
        "passing": len(rows) - len(failures),
        "failing_total": len(failures),
        "failing_by_design_unsupported": len(by_design),
        "failing_genuine": len(genuine),
        "failing_by_error_type": dict(Counter(r.error_type or "?" for r in failures)),
        "genuine_by_error_type": dict(Counter(r.error_type or "?" for r in genuine)),
        "genuine_by_difficulty": dict(Counter(r.difficulty for r in genuine)),
        "genuine_difficulty_4_5": sum(1 for r in genuine if r.difficulty >= 4),
        "genuine_by_module": dict(Counter(r.module_number for r in genuine)),
        # STABILNI ključevi (NALAZ #21); task_id je uz njih samo informativan.
        "genuine_source_ids": [r.source_id for r in genuine],
        "genuine_task_ids": [r.task_id for r in genuine],
    }


def _print_table(rows: list[TaskRow]) -> None:
    failures = [r for r in rows if not r.is_correct]
    print(f"\n{'=' * 100}")
    print("SWEEP INTEGRITETA ZADATAKA — referentni upit na vlastitom tasku")
    print(f"{'=' * 100}")
    print(f"Aktivnih taskova: {len(rows)} | PROLAZI: {len(rows) - len(failures)} | PADA: {len(failures)}")
    if not failures:
        print("\nSvi referentni upiti reproduciraju expected_result. ✓")
        return
    print(
        f"\n{'id':>4}  {'mod':>3}  {'dif':>3}  {'error_type':<18}  "
        f"{'source_id (STABILNI ključ)':<34}  title"
    )
    print("-" * 116)
    for r in sorted(failures, key=lambda x: (x.error_type or "", x.task_id)):
        print(
            f"{r.task_id:>4}  {r.module_number:>3}  {r.difficulty:>3}  "
            f"{(r.error_type or '?'):<18}  {r.source_id:<34}  {r.title[:34]}"
        )
    print("\nDETALJI padova:")
    for r in sorted(failures, key=lambda x: (x.error_type or "", x.task_id)):
        print(f"  [{r.source_id}] {r.error_type}: {r.detail[:150]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only sweep integriteta taskova.")
    parser.add_argument("--json", action="store_true", help="samo JSON sažetak")
    parser.add_argument("--deep", type=int, default=0, help="duboka usporedba za N prvih padova")
    args = parser.parse_args()

    rows = run_sweep()
    summary = _summarize(rows)
    summary["unsupported_eval_attempts"] = count_unsupported_attempts()
    unstable = check_plan_stability()
    summary["unstable_plan_tasks"] = [sid for sid, _ in unstable]
    bad_claim = check_plan_claim()
    summary["bad_plan_claim_tasks"] = [sid for sid, _ in bad_claim]

    if not args.json:
        _print_table(rows)

    if args.deep:
        genuine_ids = summary["genuine_task_ids"][: args.deep]
        print(f"\n{'=' * 100}\nDUBOKA USPOREDBA (prvih {len(genuine_ids)} stvarnih padova)\n{'=' * 100}")
        for tid in genuine_ids:
            d = deep_compare(tid)
            print(json.dumps(d, ensure_ascii=False, indent=2, default=str))

    print("\n--- JSON SAŽETAK ---")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # Gate bi na praznoj bazi "prošao" s 0/0 — a prazan task bank znači
    # neseedanu bazu, ne zdravlje. Actionable poruka umjesto tihog zelenila.
    if summary["total_active_tasks"] == 0:
        print(
            "\n🔴 GATE PAO: nula AKTIVNIH taskova u bazi. Pokreni prvi-boot korake:\n"
            "   make db-tasks && make sandbox-seed"
        )
        raise SystemExit(1)

    # Gate: nijedan referentni upit ne smije pasti.
    if summary["failing_genuine"]:
        print(
            f"\n🔴 GATE PAO: {summary['failing_genuine']} referentni upit(a) ne "
            f"reproducira expected_result: {summary['genuine_source_ids']}. "
            "Vidi tablicu iznad; regeneracija: scripts.regenerate_expected_result."
        )
        raise SystemExit(1)

    # Gate (ERRATA #66): aktivan M6 zadatak mora imati stabilan plan, inače mu je
    # ocjena nasumična. Prije ovog gatea tri su zadatka tvrdila Index Scan a
    # dobivala Seq Scan, i to je preživjelo tri faze jer se mjerila samo
    # usporedba redaka — a redci su se poklapali.
    if unstable:
        print("\n🔴 GATE PAO: M6 zadatak s NESTABILNIM planom izvedbe:")
        for source_id, razlog in unstable:
            print(f"   [{source_id}] {razlog}")
        print(
            "   Referentni upit mora birati indeks (ili strategiju spoja) BEZUVJETNO.\n"
            "   Tipičan uzrok: upit gađa premalu tablicu (npr. customers, 200 redaka),\n"
            "   gdje je Seq Scan stvarno jeftiniji pa planer indeks odbija."
        )
        raise SystemExit(1)

    # Gate (ERRATA #78): svojstvo koje zadatak IZGOVARA mora stajati u planu.
    # Pravilo je po konceptu — `index_usage` imenuje indeks, `explain_plan` mora
    # imati nepraznu strategiju spoja. Zadatak koji ne potpada ni pod jedno
    # pravilo PADA: tiho preskakanje je mana zbog koje gate diskriminacije nije
    # prenesen ovamo, pa je ovaj ne smije ponoviti.
    if bad_claim:
        print("\n🔴 GATE PAO: M6 zadatak ne izgovara ono što mu plan radi:")
        for source_id, razlog in bad_claim:
            print(f"   [{source_id}] {razlog}")
        print(
            "   Opis je izvor tvrdnje (isto načelo kao expected_query, §C.2).\n"
            "   Imena indeksa se provjeravaju prema pg_indexes, ne prema popisu u kodu."
        )
        raise SystemExit(1)

    # Tvrdnja (4.4-0d KORAK 6c): nula perzistiranih unsupported_eval attempta.
    polluted = summary["unsupported_eval_attempts"]
    if polluted:
        print(
            f"\n🔴 TVRDNJA PALA: {polluted} attempt(a) s error_type='unsupported_eval' "
            "u bazi — BKT je zagađen (0 XP + kazna). Provjeri Kat. C masku u "
            "recommender_logic i očisti retke (attempts + skill_mastery_history + xp_log)."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
