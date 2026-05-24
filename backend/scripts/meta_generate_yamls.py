"""
Meta-generation CLI: generira concept YAML config-ove koji nedostaju u
backend/config/concepts/ koristeći Anthropic tool-use API s few-shot strategijom.

Upotreba:
    uv run python -m scripts.meta_generate_yamls
    uv run python -m scripts.meta_generate_yamls --concepts where_filter,group_by
    uv run python -m scripts.meta_generate_yamls --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from scripts.lib.api_client import AnthropicClient
from scripts.lib.meta_gen import collect_few_shot_yamls, generate_one_yaml

MISSING_CONCEPTS = [
    # Modul 1 — Osnove SELECT-a
    "from_clause",
    "where_filter",
    "order_by",
    "limit_offset",
    "distinct",
    # Modul 2 — Agregacije i grupiranje
    "group_by",
    "having_filter",
    "agg_count",
    "agg_sum_avg",
    "agg_min_max",
    # Modul 3 — JOIN-ovi
    "right_join",
    "full_outer_join",
    "cross_join",
    # Modul 4 — DML operacije
    "insert",
    "update",
    "delete",
    # Modul 5 — Podupiti
    "scalar_subquery",
    "in_subquery",
    "exists_subquery",
    # Modul 6 — Optimizacija
    "explain_plan",
    # Transverzalni koncepti
    "null_handling",
    "column_alias",
    "join_condition",
]

CONCEPT_META: dict[str, dict] = {
    # ── Modul 1 ──────────────────────────────────────────────────────────
    "from_clause": {
        "module_number": 1,
        "module_name": "Osnove SELECT-a",
        "tier": "easy",
        "description": (
            "FROM klauzula — identifikacija tablice iz koje se dohvaćaju podaci. "
            "Misconception: zaboravlja FROM, miješa nazive tablica i stupaca, "
            "ne zna da se tablice mogu aliasati."
        ),
    },
    "where_filter": {
        "module_number": 1,
        "module_name": "Osnove SELECT-a",
        "tier": "easy",
        "description": (
            "WHERE klauzula — filtriranje redova po uvjetu. "
            "Klasični misconception: miješa WHERE i HAVING (WHERE ne može koristiti "
            "agregirane vrijednosti). Logički operatori AND/OR/NOT."
        ),
    },
    "order_by": {
        "module_number": 1,
        "module_name": "Osnove SELECT-a",
        "tier": "easy",
        "description": (
            "ORDER BY klauzula — sortiranje rezultata. "
            "Misconception: ORDER BY misli da ide prije WHERE u logičkom redoslijedu, "
            "ne zna razliku ASC/DESC, sortira po stupcu koji nije u SELECT listi."
        ),
    },
    "limit_offset": {
        "module_number": 1,
        "module_name": "Osnove SELECT-a",
        "tier": "easy",
        "description": (
            "LIMIT i OFFSET klauzule — paginacija rezultata. "
            "Misconception: LIMIT bez ORDER BY daje nedeterministički rezultat. "
            "Ne razumije da OFFSET preskače prvih N redova."
        ),
    },
    "distinct": {
        "module_number": 1,
        "module_name": "Osnove SELECT-a",
        "tier": "easy",
        "description": (
            "DISTINCT klauzula — uklanjanje dupliciranih redova iz rezultata. "
            "Misconception: koristi DISTINCT redundantno nakon GROUP BY, "
            "ne razumije da DISTINCT djeluje na čitav red (sve stupce), "
            "ne zna performance cost DISTINCT-a."
        ),
    },
    # ── Modul 2 ──────────────────────────────────────────────────────────
    "group_by": {
        "module_number": 2,
        "module_name": "Agregacije i grupiranje",
        "tier": "medium",
        "description": (
            "GROUP BY klauzula — grupiranje redova po vrijednosti stupca. "
            "Klasični misconception: SELECT sadrži nenagregirani stupac koji nije "
            "u GROUP BY (SQL standard violation). Sandbox: ecommerce_v1 orders, "
            "order_items, products tablice."
        ),
    },
    "having_filter": {
        "module_number": 2,
        "module_name": "Agregacije i grupiranje",
        "tier": "medium",
        "description": (
            "HAVING klauzula — filtriranje grupa (nakon GROUP BY). "
            "Klasični misconception WHERE vs HAVING: WHERE filtrira redove prije "
            "grupiranja, HAVING filtrira grupe nakon. WHERE ne može koristiti "
            "agregirane funkcije (COUNT, SUM, AVG...)."
        ),
    },
    "agg_count": {
        "module_number": 2,
        "module_name": "Agregacije i grupiranje",
        "tier": "medium",
        "description": (
            "COUNT agregatna funkcija — brojanje redova ili vrijednosti. "
            "Ključne razlike: COUNT(*) broji sve retke uključujući NULL-ove, "
            "COUNT(col) ignorira NULL-ove, COUNT(DISTINCT col) broji unikatne "
            "ne-NULL vrijednosti. Sandbox: orders, customers."
        ),
    },
    "agg_sum_avg": {
        "module_number": 2,
        "module_name": "Agregacije i grupiranje",
        "tier": "medium",
        "description": (
            "SUM i AVG agregatne funkcije — suma i prosjek numeričkih vrijednosti. "
            "Obje ignoriraju NULL-ove (ne tretiraju NULL kao 0). "
            "Misconception: AVG(col) nije isto što SUM(col)/COUNT(*) kad ima NULL-ova. "
            "Sandbox: order_items.unit_price, employees.salary."
        ),
    },
    "agg_min_max": {
        "module_number": 2,
        "module_name": "Agregacije i grupiranje",
        "tier": "easy",
        "description": (
            "MIN i MAX agregatne funkcije — minimalna i maksimalna vrijednost. "
            "Rade i na tekstualnim i numeričkim stupcima (leksikografski/numerički red). "
            "Ignoriraju NULL-ove. Sandbox: products.price, orders.total_amount."
        ),
    },
    # ── Modul 3 ──────────────────────────────────────────────────────────
    "right_join": {
        "module_number": 3,
        "module_name": "JOIN-ovi",
        "tier": "medium",
        "description": (
            "RIGHT OUTER JOIN — zadržava sve retke desne tablice, NULL za stupce "
            "lijeve tablice gdje nema poklapanja. Simetričan LEFT JOIN-u (mogu se "
            "uvijek zamijeniti promjenom redoslijeda tablica). Rijetko korišten u praksi."
        ),
    },
    "full_outer_join": {
        "module_number": 3,
        "module_name": "JOIN-ovi",
        "tier": "hard",
        "description": (
            "FULL OUTER JOIN — zadržava sve retke iz obje tablice, NULL gdje nema "
            "poklapanja. Semantički različit od kombinacije LEFT + RIGHT JOIN-a. "
            "PostgreSQL sintaksa: FULL OUTER JOIN ... ON. "
            "Sandbox: customers i orders (kupci bez narudžbi i narudžbe bez kupca)."
        ),
    },
    "cross_join": {
        "module_number": 3,
        "module_name": "JOIN-ovi",
        "tier": "medium",
        "description": (
            "CROSS JOIN — Kartezijev produkt svih kombinacija redova dviju tablica. "
            "N × M redova u rezultatu. Misconception: slučajno stvaranje CROSS JOIN-a "
            "kroz nedostajuću ON klauzulu ili INNER JOIN bez uvjeta. "
            "Sandbox primjer: kombiniranje kategorija i statusa narudžbi."
        ),
    },
    # ── Modul 4 ──────────────────────────────────────────────────────────
    "insert": {
        "module_number": 4,
        "module_name": "DML operacije",
        "tier": "easy",
        "description": (
            "INSERT INTO — unos novih redova u tablicu. "
            "Misconception: krivi redoslijed vrijednosti u VALUES, constraint violations "
            "(UNIQUE, NOT NULL, FK), INSERT bez navođenja stupaca (brittle). "
            "Sandbox: sandbox_readwrite role, sve promjene se rollback-aju."
        ),
    },
    "update": {
        "module_number": 4,
        "module_name": "DML operacije",
        "tier": "medium",
        "description": (
            "UPDATE — izmjena postojećih redova u tablici. "
            "Kritični misconception: UPDATE bez WHERE klauze mijenja SVE retke "
            "(destruktivna operacija). Ispravna upotreba WHERE za ciljanje. "
            "Sandbox: sandbox_readwrite role, sve promjene se rollback-aju."
        ),
    },
    "delete": {
        "module_number": 4,
        "module_name": "DML operacije",
        "tier": "medium",
        "description": (
            "DELETE FROM — brisanje redova iz tablice. "
            "Kritični misconception: DELETE bez WHERE briše SVE retke. "
            "Razlika od TRUNCATE (DDL, ne može rollback) i DROP TABLE (briše shemu). "
            "FK constraint violation ako se referencirani red briše. "
            "Sandbox: sandbox_readwrite role, sve promjene se rollback-aju."
        ),
    },
    # ── Modul 5 ──────────────────────────────────────────────────────────
    "scalar_subquery": {
        "module_number": 5,
        "module_name": "Podupiti",
        "tier": "medium",
        "description": (
            "Skalarni podupit — vraća točno 1 vrijednost (1 red × 1 stupac). "
            "Može se koristiti u SELECT, WHERE, HAVING. "
            "Misconception: podupit vraća više od 1 reda → 'more than one row returned' "
            "runtime error. Sandbox: usporedba s prosjecima, MAX/MIN podupiti."
        ),
    },
    "in_subquery": {
        "module_number": 5,
        "module_name": "Podupiti",
        "tier": "medium",
        "description": (
            "IN i NOT IN s podupitom — membership test. "
            "Kritični misconception: NOT IN + NULL — vraća 0 redova umjesto očekivanih "
            "zbog 3-valued logike SQL-a (NULL IN (...) je UNKNOWN, ne FALSE). "
            "Sandbox: customers IN (SELECT customer_id FROM orders WHERE ...)."
        ),
    },
    "exists_subquery": {
        "module_number": 5,
        "module_name": "Podupiti",
        "tier": "medium",
        "description": (
            "EXISTS i NOT EXISTS — test egzistencije redova u podupitu. "
            "Alternativa IN-u, robusniji s NULL vrijednostima. "
            "Misconception: ne razumije da SELECT lista u EXISTS nije bitna "
            "(konvencija SELECT 1 ili SELECT *). Sandbox: EXISTS u WHERE klauzuli."
        ),
    },
    # ── Modul 6 ──────────────────────────────────────────────────────────
    "explain_plan": {
        "module_number": 6,
        "module_name": "Optimizacija",
        "tier": "hard",
        "description": (
            "EXPLAIN i EXPLAIN ANALYZE — čitanje query execution plana. "
            "Razlika Seq Scan vs Index Scan, Hash Join vs Nested Loop. "
            "Misconception: ne razumije zašto planer bira Seq Scan umjesto indeksa "
            "(npr. mali stol, neselektivni uvjet, funkcija na stupcu). "
            "Sandbox: PostgreSQL EXPLAIN output format."
        ),
    },
    # ── Transverzalni ────────────────────────────────────────────────────
    "null_handling": {
        "module_number": 0,
        "module_name": "Transverzalni koncepti",
        "tier": "medium",
        "description": (
            "NULL handling — IS NULL, IS NOT NULL, COALESCE, NULLIF. "
            "3-valued logika SQL-a: TRUE, FALSE, UNKNOWN. "
            "Prerequisite za: LEFT JOIN (NULL u vanjskim redovima), "
            "NOT IN + NULL (vraća 0 redova), COUNT(col) ignorira NULL-ove. "
            "Sandbox: orders.employee_id (nullable), products.description (nullable)."
        ),
    },
    "column_alias": {
        "module_number": 0,
        "module_name": "Transverzalni koncepti",
        "tier": "easy",
        "description": (
            "AS klauzula za preimenovanje stupaca i tablica. "
            "Misconception: koristi alias u WHERE klauzuli (ne može — logički redoslijed "
            "WHERE → SELECT, alias nije vidljiv u WHERE). "
            "U PostgreSQL-u alias se može koristiti u GROUP BY i ORDER BY. "
            "Sandbox: prikazivanje rezultata s čitljivim imenima stupaca."
        ),
    },
    "join_condition": {
        "module_number": 0,
        "module_name": "Transverzalni koncepti",
        "tier": "medium",
        "description": (
            "ON klauzula — semantika uvjeta spajanja u JOIN-u. "
            "Kritični misconception: filter u ON vs WHERE kod LEFT JOIN-a potpuno "
            "mijenja rezultat — filter u ON zadržava NULL-ove vanjskih redova, "
            "filter u WHERE pretvara LEFT JOIN u INNER JOIN. "
            "Sandbox: orders LEFT JOIN customers ON ... WHERE ..."
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generira concept YAML config-ove kroz Anthropic tool-use API."
    )
    parser.add_argument(
        "--concepts",
        type=str,
        default=None,
        help="Comma-separated lista koncepta za generiranje (default: svi iz MISSING_CONCEPTS)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="config/concepts",
        help="Direktorij za pisanje YAML-ova (default: config/concepts)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=1,
        help="Broj auto-retry pokušaja po konceptu (default: 1)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="claude-sonnet-4-6",
        help="Anthropic model (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--hard-cap-usd",
        type=float,
        default=0.50,
        help="Abort ako kumulativni trošak premaši ovaj iznos (default: $0.50)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ispiši što bi se generiralo, ali ne pozivaj API i ne piši YAML-ove",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY env var nije postavljen.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    targets = (
        [c.strip() for c in args.concepts.split(",")]
        if args.concepts
        else MISSING_CONCEPTS
    )

    if args.dry_run:
        print(f"DRY RUN — {len(targets)} koncepta za generiranje:")
        for code in targets:
            meta = CONCEPT_META.get(code, {})
            print(f"  {code}: M{meta.get('module_number','?')} | {meta.get('tier','?')}")
        return

    client = AnthropicClient(api_key=api_key, model=args.model)
    # Few-shot fiksan na originalnih 7 — ne raste s generiranim YAML-ovima
    # (rastući few-shot invalida prompt cache i povećava trošak linearno)
    _FEW_SHOT_BASE = {
        "correlated_subquery", "index_usage", "inner_join",
        "left_join", "multi_table_join", "select_basic", "self_join",
    }
    all_yamls = collect_few_shot_yamls(output_dir)
    few_shot = {k: v for k, v in all_yamls.items() if k in _FEW_SHOT_BASE}
    print(f"Few-shot primjeri: {list(few_shot.keys())}")

    results = []
    cumulative_cost = 0.0
    # Konzervativna procjena cijene jednog YAML-a — koristi se za pre-flight
    # cap check. ~$0.06 po pozivu (Sonnet 4.6 s big system prompt + few-shot).
    EXPECTED_COST_PER_YAML = 0.06

    for concept_code in targets:
        if concept_code not in CONCEPT_META:
            print(f"⚠  Preskačem '{concept_code}': nema u CONCEPT_META")
            continue

        existing_path = output_dir / f"{concept_code}.yaml"
        if existing_path.exists():
            print(f"⏭  Preskačem '{concept_code}': YAML već postoji")
            continue

        # Pre-flight cap — sprječava prekoračenje za cijenu jednog poziva
        if cumulative_cost + EXPECTED_COST_PER_YAML > args.hard_cap_usd:
            print(
                f"\nHARD CAP ${args.hard_cap_usd:.2f} preventivno aktiviran "
                f"(trenutni ${cumulative_cost:.4f} + procjena "
                f"${EXPECTED_COST_PER_YAML:.4f} bi prešao cap). Zaustavljam."
            )
            break

        print(f"→  Generiram '{concept_code}'...", end=" ", flush=True)

        result = generate_one_yaml(
            client=client,
            concept_code=concept_code,
            concept_meta=CONCEPT_META[concept_code],
            few_shot_examples=few_shot,
            output_dir=output_dir,
            max_retries=args.max_retries,
        )
        results.append(result)
        cumulative_cost += result["cost_usd"]

        icon = "✓" if result["status"] == "success" else "⚠"
        print(
            f"{icon} {result['attempts']} pokušaj/a, "
            f"${result['cost_usd']:.4f} | ukupno ${cumulative_cost:.4f}"
        )

        # Post-flight cap kao backup — npr. ako je stvarni trošak bio veći od
        # procjene zbog retry-a.
        if cumulative_cost > args.hard_cap_usd:
            print(
                f"\nHARD CAP ${args.hard_cap_usd:.2f} dostignut "
                f"(trenutni trošak ${cumulative_cost:.4f}). Zaustavljam."
            )
            break

    # Summary
    n_success = sum(1 for r in results if r["status"] == "success")
    n_manual = len(results) - n_success
    print(f"\n{'='*50}")
    print(f"META-GEN COMPLETE")
    print(f"  Success:       {n_success}/{len(results)}")
    print(f"  Manual review: {n_manual}/{len(results)}")
    print(f"  Ukupni trošak: ${cumulative_cost:.4f}")

    if n_manual > 0:
        print("\nKoncepti za manual review:")
        for r in results:
            if r["status"] == "manual_review":
                print(f"  - {r['concept_code']}: {r['error']}")

    # Spremi results report
    report_path = output_dir / "_meta_gen_report.json"
    report_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nReport: {report_path}")


if __name__ == "__main__":
    main()
