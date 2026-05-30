"""Faza 2B-2 Korak 11 — manual writing for 19 zadataka.

Pokriva agregacijske koncepte koji se ne mogu LLM-generirati zbog
hallucination-a expected_result vrijednosti (per 2B-1E + 2B-2 nalaza):
- group_by × 5
- having_filter × 4
- agg_count × 4
- agg_sum_avg × 3
- agg_min_max × 3

Svaki task se kreira kroz:
1. Definiciju u TASKS list (concept, difficulty, title, description, query, misconception)
2. Pokretanje query-ja u sandbox-u (psycopg)
3. Formatiranje rezultata kao expected_result (list[dict])
4. Save kao GeneratedTaskMeta JSON u validated/ s generation_method=manual

Pokretanje:
    cd backend && uv run python -m scripts.manual_tasks_2b2
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import psycopg
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("manual_tasks_2b2")


# ── TASKS ─────────────────────────────────────────────────────────────────────
# Format: dict per task. expected_result se dohvaća automatski iz sandbox-a.

TASKS: list[dict] = [
    # ─── group_by × 5 ───────────────────────────────────────────────────────
    {
        "concept": "group_by",
        "difficulty": 1,
        "title": "Broj proizvoda po kategoriji",
        "description": (
            "Za svaki category_id u tablici products ispiši broj proizvoda u toj "
            "kategoriji. Koristi GROUP BY na coloni category_id i COUNT(*) agregat. "
            "Sortiraj uzlazno po category_id."
        ),
        "secondary": ["agg_count", "order_by"],
        "query": (
            "SELECT category_id, COUNT(*) AS broj_proizvoda "
            "FROM products "
            "GROUP BY category_id "
            "ORDER BY category_id ASC;"
        ),
        "misconception": "non_aggregated_column_not_in_group_by",
        "notes": (
            "Klasičan GROUP BY + COUNT(*) primjer. Student treba shvatiti da "
            "category_id u SELECT listi mora biti u GROUP BY jer nije unutar "
            "agregatne funkcije."
        ),
    },
    {
        "concept": "group_by",
        "difficulty": 2,
        "title": "Broj kupaca po zemlji — TOP 5",
        "description": (
            "Pronađi prvih 5 zemalja s najvećim brojem kupaca. Za svaku zemlju "
            "ispiši country i broj kupaca. GROUP BY na country, COUNT(*), sortiraj "
            "silazno po broju kupaca pa LIMIT 5."
        ),
        "secondary": ["agg_count", "limit_offset"],
        "query": (
            "SELECT country, COUNT(*) AS broj_kupaca "
            "FROM customers "
            "GROUP BY country "
            "ORDER BY broj_kupaca DESC, country ASC "
            "LIMIT 5;"
        ),
        "misconception": "non_aggregated_column_not_in_group_by",
        "notes": (
            "Demonstrira ORDER BY na agregatu (alias broj_kupaca u ORDER BY je "
            "validan u PostgreSQL-u). LIMIT primjenjuje na već agregirane redove."
        ),
    },
    {
        "concept": "group_by",
        "difficulty": 3,
        "title": "Ukupna količina prodanih proizvoda po proizvodu — TOP 10",
        "description": (
            "Za svaki proizvod (product_id) u tablici order_items izračunaj ukupnu "
            "količinu (SUM od quantity) i ukupan broj stavki narudžbe (COUNT(*)). "
            "Ispiši product_id, ukupna_kolicina i broj_stavki. Prikaži TOP 10 "
            "proizvoda po ukupnoj količini (silazno)."
        ),
        "secondary": ["agg_sum_avg", "agg_count", "limit_offset"],
        "query": (
            "SELECT product_id, SUM(quantity) AS ukupna_kolicina, COUNT(*) AS broj_stavki "
            "FROM order_items "
            "GROUP BY product_id "
            "ORDER BY ukupna_kolicina DESC, product_id ASC "
            "LIMIT 10;"
        ),
        "misconception": "group_by_column_not_in_select",
        "notes": (
            "Više agregatnih funkcija na istoj grupi. Tie-breaker po product_id ASC "
            "garantira deterministic order kad više proizvoda ima istu ukupnu količinu."
        ),
    },
    {
        "concept": "group_by",
        "difficulty": 3,
        "title": "Prosječna ocjena recenzija po proizvodu — sortiranje silazno",
        "description": (
            "Za svaki product_id u tablici reviews izračunaj prosječnu ocjenu "
            "(AVG od rating, zaokruženo na 2 decimale) i broj recenzija (COUNT(*)). "
            "Ispiši product_id, prosjecna_ocjena i broj_recenzija. Sortiraj od "
            "najveće prosječne ocjene prema najmanjoj. Prikaži samo prvih 5 zapisa."
        ),
        "secondary": ["agg_sum_avg", "agg_count", "limit_offset"],
        "query": (
            "SELECT product_id, "
            "ROUND(AVG(rating)::numeric, 2) AS prosjecna_ocjena, "
            "COUNT(*) AS broj_recenzija "
            "FROM reviews "
            "GROUP BY product_id "
            "ORDER BY prosjecna_ocjena DESC, product_id ASC "
            "LIMIT 5;"
        ),
        "misconception": "non_aggregated_column_not_in_group_by",
        "notes": (
            "ROUND s ::numeric cast — preporučeni PostgreSQL pattern. Demonstrira "
            "kombinaciju 2 različita agregata + LIMIT na agregirane rezultate."
        ),
    },
    {
        "concept": "group_by",
        "difficulty": 4,
        "title": "Ukupni iznos narudžbi po kupcu i statusu — multi-column GROUP BY",
        "description": (
            "Za svaku kombinaciju kupca (customer_id) i statusa narudžbe izračunaj "
            "ukupan iznos (SUM od total_amount). Ispiši customer_id, status i "
            "ukupni_iznos. Sortiraj po customer_id uzlazno, a unutar istog kupca "
            "po ukupnom iznosu silazno. Prikaži prvih 10 zapisa."
        ),
        "secondary": ["agg_sum_avg", "order_by", "limit_offset"],
        "query": (
            "SELECT customer_id, status, SUM(total_amount) AS ukupni_iznos "
            "FROM orders "
            "GROUP BY customer_id, status "
            "ORDER BY customer_id ASC, ukupni_iznos DESC "
            "LIMIT 10;"
        ),
        "misconception": "group_by_column_not_in_select",
        "notes": (
            "Multi-column GROUP BY — i customer_id i status moraju biti u GROUP BY "
            "jer su u SELECT listi i nisu agregirani."
        ),
    },
    # ─── having_filter × 4 ──────────────────────────────────────────────────
    {
        "concept": "having_filter",
        "difficulty": 2,
        "title": "Kategorije s više od 6 proizvoda — HAVING",
        "description": (
            "Pronađi kategorije (category_id) koje sadrže više od 6 proizvoda. "
            "Ispiši category_id i broj_proizvoda. Sortiraj silazno po broju. "
            "Filter na agregiranoj vrijednosti (COUNT(*) > 6) mora koristiti "
            "HAVING — WHERE ne podržava agregate."
        ),
        "secondary": ["group_by", "agg_count"],
        "query": (
            "SELECT category_id, COUNT(*) AS broj_proizvoda "
            "FROM products "
            "GROUP BY category_id "
            "HAVING COUNT(*) > 6 "
            "ORDER BY broj_proizvoda DESC, category_id ASC;"
        ),
        "misconception": "group_by_vs_where_confusion",
        "notes": (
            "Klasičan WHERE vs HAVING distinction. Pomaže fixate redoslijed klauza: "
            "WHERE → GROUP BY → HAVING → ORDER BY."
        ),
    },
    {
        "concept": "having_filter",
        "difficulty": 3,
        "title": "Zemlje s prosječnim ratingom dobavljača iznad 3.5",
        "description": (
            "Iz tablice suppliers pronađi sve zemlje (country) gdje je prosječna "
            "ocjena dobavljača (AVG od rating) veća od 3.5. Ispiši country i "
            "prosjecna_ocjena (zaokruženo na 2 decimale). Sortiraj silazno po "
            "prosječnoj ocjeni. Koristi HAVING za uvjet na agregatu."
        ),
        "secondary": ["group_by", "agg_sum_avg"],
        "query": (
            "SELECT country, ROUND(AVG(rating)::numeric, 2) AS prosjecna_ocjena "
            "FROM suppliers "
            "GROUP BY country "
            "HAVING AVG(rating) > 3.5 "
            "ORDER BY prosjecna_ocjena DESC, country ASC;"
        ),
        "misconception": "group_by_vs_where_confusion",
        "notes": (
            "HAVING + AVG combo. Suppliers tablica ima samo 30 redova pa je rezultat "
            "lako manuelno verificirati."
        ),
    },
    {
        "concept": "having_filter",
        "difficulty": 3,
        "title": "Kupci s ukupno više od 10 narudžbi — WHERE + HAVING",
        "description": (
            "Pronađi sve kupce (customer_id) koji su izvršili više od 10 narudžbi "
            "koje NISU u statusu 'cancelled'. Ispiši customer_id i broj_narudzbi. "
            "Sortiraj silazno po broju narudžbi. Koristi WHERE za filtriranje statusa "
            "(prije grupiranja) i HAVING za uvjet na broju (nakon grupiranja)."
        ),
        "secondary": ["where_filter", "group_by", "agg_count"],
        "query": (
            "SELECT customer_id, COUNT(*) AS broj_narudzbi "
            "FROM orders "
            "WHERE status != 'cancelled' "
            "GROUP BY customer_id "
            "HAVING COUNT(*) > 10 "
            "ORDER BY broj_narudzbi DESC, customer_id ASC;"
        ),
        "misconception": "group_by_vs_where_confusion",
        "notes": (
            "Bitan distinktivni primjer: WHERE filtrira PRIJE GROUP BY, HAVING "
            "filtrira NAKON GROUP BY (radi na agregatima)."
        ),
    },
    {
        "concept": "having_filter",
        "difficulty": 4,
        "title": "Top kategorije s visokim prosječnim prihodom — WHERE + GROUP BY + HAVING + ORDER",
        "description": (
            "Pronađi kategorije proizvoda gdje je prosječna cijena artikla (price "
            "iz tablice products) veća od 200 NOVAČA, i broj proizvoda u toj "
            "kategoriji je barem 3. Ispiši category_id, broj_proizvoda i "
            "prosjecna_cijena (zaokružena na 2 decimale). Sortiraj silazno po "
            "prosječnoj cijeni. Koristi WHERE samo ako ti treba pre-filter, ali ne za "
            "agregirani uvjet (oba uvjeta su na agregatima — HAVING)."
        ),
        "secondary": ["group_by", "agg_count", "agg_sum_avg"],
        "query": (
            "SELECT category_id, "
            "COUNT(*) AS broj_proizvoda, "
            "ROUND(AVG(price), 2) AS prosjecna_cijena "
            "FROM products "
            "GROUP BY category_id "
            "HAVING AVG(price) > 200 AND COUNT(*) >= 3 "
            "ORDER BY prosjecna_cijena DESC, category_id ASC;"
        ),
        "misconception": "group_by_vs_where_confusion",
        "notes": (
            "Multi-condition HAVING (AND između agregata). Ovo je tipičan d=4 "
            "primjer s 2-3 agregatne agregacije."
        ),
    },
    # ─── agg_count × 4 ──────────────────────────────────────────────────────
    {
        "concept": "agg_count",
        "difficulty": 1,
        "title": "Ukupan broj recenzija u sustavu",
        "description": (
            "Ispiši ukupan broj recenzija u tablici reviews. Koristi COUNT(*) "
            "agregatnu funkciju. Ispis ima jedan red s jednim stupcem ukupno."
        ),
        "secondary": [],
        "query": "SELECT COUNT(*) AS ukupno FROM reviews;",
        "misconception": "count_star_vs_count_column_distinction",
        "notes": (
            "Najjednostavniji agg_count primjer — COUNT(*) bez GROUP BY vraća "
            "ukupan broj redova."
        ),
    },
    {
        "concept": "agg_count",
        "difficulty": 2,
        "title": "Broj kupaca bez ikoje narudžbe",
        "description": (
            "Koliko kupaca u tablici customers nije izvršilo NITI jednu narudžbu? "
            "Koristi LEFT JOIN između customers i orders, pa COUNT na kupcima "
            "kojima je orders.id NULL. Ispiši jedan red s brojem kupaca_bez_narudzbi."
        ),
        "secondary": ["left_join", "null_handling"],
        "query": (
            "SELECT COUNT(*) AS kupaca_bez_narudzbi "
            "FROM customers c "
            "LEFT JOIN orders o ON c.id = o.customer_id "
            "WHERE o.id IS NULL;"
        ),
        "misconception": "count_star_vs_count_column_distinction",
        "notes": (
            "Klasičan LEFT JOIN + IS NULL pattern za 'kupci bez narudžbi'. "
            "COUNT(*) broji redove zadovoljavajuće uvjet (NULL on right side)."
        ),
    },
    {
        "concept": "agg_count",
        "difficulty": 3,
        "title": "Broj narudžbi po statusu — uključujući 0 za neaktivne statuse",
        "description": (
            "Za svaki status narudžbe iz orders ispiši status i broj narudžbi s tim "
            "statusom. Sortiraj abecedno po statusu. Koristi GROUP BY + COUNT(*)."
        ),
        "secondary": ["group_by", "order_by"],
        "query": (
            "SELECT status, COUNT(*) AS broj_narudzbi "
            "FROM orders "
            "GROUP BY status "
            "ORDER BY status ASC;"
        ),
        "misconception": "non_aggregated_column_not_in_group_by",
        "notes": (
            "Iako naslov spominje '0 za neaktivne', svi 5 statusa su zastupljeni "
            "u sandboxu (ground truth iz group_by.yaml domain_hints)."
        ),
    },
    {
        "concept": "agg_count",
        "difficulty": 4,
        "title": "Broj distinct kupaca koji su naručivali u svakoj kategoriji",
        "description": (
            "Za svaku kategoriju proizvoda izračunaj broj RAZLIČITIH kupaca koji "
            "su naručili barem jedan proizvod iz te kategorije. Koristi JOIN "
            "između order_items, products i orders, pa COUNT(DISTINCT customer_id) "
            "po category_id. Ispiši category_id i broj_distinct_kupaca. Sortiraj "
            "silazno po broju."
        ),
        "secondary": ["multi_table_join", "group_by", "distinct"],
        "query": (
            "SELECT p.category_id, COUNT(DISTINCT o.customer_id) AS broj_distinct_kupaca "
            "FROM order_items oi "
            "JOIN products p ON oi.product_id = p.id "
            "JOIN orders o ON oi.order_id = o.id "
            "GROUP BY p.category_id "
            "ORDER BY broj_distinct_kupaca DESC, p.category_id ASC;"
        ),
        "misconception": "count_distinct_vs_count_misuse",
        "notes": (
            "COUNT(DISTINCT col) — bitna distinct optimizacija nakon multi-table "
            "JOIN-a. Bez DISTINCT bi se brojali duplikati (kupac koji je više puta "
            "naručivao iz iste kategorije)."
        ),
    },
    # ─── agg_sum_avg × 3 ────────────────────────────────────────────────────
    {
        "concept": "agg_sum_avg",
        "difficulty": 2,
        "title": "Prosječna cijena proizvoda",
        "description": (
            "Izračunaj prosječnu cijenu (AVG) i ukupnu vrijednost (SUM) svih "
            "proizvoda u tablici products. Ispiši dvije vrijednosti — "
            "prosjecna_cijena (zaokruženo na 2 decimale) i ukupna_vrijednost "
            "(zaokruženo na 2 decimale)."
        ),
        "secondary": [],
        "query": (
            "SELECT ROUND(AVG(price), 2) AS prosjecna_cijena, "
            "ROUND(SUM(price), 2) AS ukupna_vrijednost "
            "FROM products;"
        ),
        "misconception": "avg_vs_sum_confusion",
        "notes": (
            "Najjednostavniji SUM/AVG primjer bez GROUP BY — jedan red rezultata."
        ),
    },
    {
        "concept": "agg_sum_avg",
        "difficulty": 3,
        "title": "Ukupna potrošnja po kupcu — TOP 5 najvećih spenders",
        "description": (
            "Za svakog kupca izračunaj ukupan iznos svih njegovih narudžbi "
            "(SUM od total_amount). Ispiši customer_id i ukupna_potrosnja "
            "(zaokruženo na 2 decimale). Prikaži TOP 5 kupaca po ukupnoj potrošnji "
            "(silazno)."
        ),
        "secondary": ["group_by", "limit_offset"],
        "query": (
            "SELECT customer_id, ROUND(SUM(total_amount), 2) AS ukupna_potrosnja "
            "FROM orders "
            "GROUP BY customer_id "
            "ORDER BY ukupna_potrosnja DESC, customer_id ASC "
            "LIMIT 5;"
        ),
        "misconception": "avg_vs_sum_confusion",
        "notes": "Tipičan SUM po grupi + sort + LIMIT pattern.",
    },
    {
        "concept": "agg_sum_avg",
        "difficulty": 4,
        "title": "Mjesečni prihod po kategoriji proizvoda u 2025",
        "description": (
            "Za svaki mjesec u 2025. godini i svaku kategoriju proizvoda izračunaj "
            "ukupan prihod kao SUM(quantity × unit_price) iz order_items, "
            "uzimajući u obzir samo narudžbe statusom 'delivered'. Ispiši mjesec "
            "(EXTRACT(MONTH FROM order_date)), category_id i ukupni_prihod "
            "(zaokruženo na 2 decimale). Sortiraj uzlazno po mjesecu pa silazno "
            "po prihodu. Prikaži prvih 10 redova."
        ),
        "secondary": ["multi_table_join", "group_by", "where_filter", "limit_offset"],
        "query": (
            "SELECT EXTRACT(MONTH FROM o.order_date)::int AS mjesec, "
            "p.category_id, "
            "ROUND(SUM(oi.quantity * oi.unit_price), 2) AS ukupni_prihod "
            "FROM orders o "
            "JOIN order_items oi ON o.id = oi.order_id "
            "JOIN products p ON oi.product_id = p.id "
            "WHERE o.status = 'delivered' "
            "AND EXTRACT(YEAR FROM o.order_date) = 2025 "
            "GROUP BY mjesec, p.category_id "
            "ORDER BY mjesec ASC, ukupni_prihod DESC "
            "LIMIT 10;"
        ),
        "misconception": "avg_vs_sum_confusion",
        "notes": (
            "Kompleksniji d=4 primjer: 3-table JOIN + WHERE + multi-column GROUP BY "
            "+ EXTRACT funkcija + SUM s aritmetikom. Demonstrira pun stack "
            "agregacijskih i join koncepata."
        ),
    },
    # ─── agg_min_max × 3 ────────────────────────────────────────────────────
    {
        "concept": "agg_min_max",
        "difficulty": 1,
        "title": "Najjeftiniji i najskuplji proizvod",
        "description": (
            "Pronađi cijenu najjeftinijeg i najskupljeg proizvoda u tablici products. "
            "Ispiši dvije vrijednosti — min_cijena i max_cijena."
        ),
        "secondary": [],
        "query": "SELECT MIN(price) AS min_cijena, MAX(price) AS max_cijena FROM products;",
        "misconception": "min_max_misapplication",
        "notes": "Najjednostavniji MIN/MAX primjer — jedan red rezultata.",
    },
    {
        "concept": "agg_min_max",
        "difficulty": 2,
        "title": "Najraniji i najkasniji datum narudžbe po statusu",
        "description": (
            "Za svaki status narudžbe iz tablice orders pronađi najraniji "
            "(MIN order_date) i najkasniji (MAX order_date) datum narudžbe. "
            "Ispiši status, najranija_narudzba i najkasnija_narudzba. Sortiraj "
            "abecedno po statusu."
        ),
        "secondary": ["group_by", "order_by"],
        "query": (
            "SELECT status, "
            "MIN(order_date) AS najranija_narudzba, "
            "MAX(order_date) AS najkasnija_narudzba "
            "FROM orders "
            "GROUP BY status "
            "ORDER BY status ASC;"
        ),
        "misconception": "min_max_misapplication",
        "notes": "MIN/MAX se primjenjuje na timestamp tip — vraća earliest/latest datum.",
    },
    {
        "concept": "agg_min_max",
        "difficulty": 3,
        "title": "Najveća pojedinačna stavka narudžbe po kategoriji proizvoda",
        "description": (
            "Za svaku kategoriju proizvoda pronađi najveću pojedinačnu stavku narudžbe "
            "po vrijednosti (quantity × unit_price) iz tablice order_items. "
            "Ispiši category_id i max_vrijednost_stavke (zaokruženo na 2 decimale). "
            "Sortiraj silazno po vrijednosti."
        ),
        "secondary": ["inner_join", "group_by"],
        "query": (
            "SELECT p.category_id, "
            "ROUND(MAX(oi.quantity * oi.unit_price), 2) AS max_vrijednost_stavke "
            "FROM order_items oi "
            "JOIN products p ON oi.product_id = p.id "
            "GROUP BY p.category_id "
            "ORDER BY max_vrijednost_stavke DESC, p.category_id ASC;"
        ),
        "misconception": "min_max_misapplication",
        "notes": (
            "MAX s aritmetičkim izrazom + JOIN. Demonstrira da MIN/MAX rade na "
            "expression-ima, ne samo single columns."
        ),
    },
]


# ── Utility ───────────────────────────────────────────────────────────────────


def _convert_decimal(value):
    """Convert Decimal → float for JSON serialization. Preserves int if integer-valued."""
    if isinstance(value, Decimal):
        f = float(value)
        # Preserve int if whole number
        if f.is_integer():
            return int(f)
        return f
    return value


def fetch_rows(conn, query: str) -> list[dict]:
    """Run query, return rows as list[dict] with proper type conversion."""
    with conn.cursor() as cur:
        cur.execute(query)
        cols = [d.name for d in cur.description]
        rows = cur.fetchall()
    result = []
    for row in rows:
        rec = {}
        for col, val in zip(cols, row):
            # JSON serialization needs str/int/float/None — coerce Decimal & datetime
            if val is None:
                rec[col] = None
            elif isinstance(val, Decimal):
                rec[col] = _convert_decimal(val)
            elif hasattr(val, "isoformat"):  # date/datetime
                rec[col] = val.isoformat()
            else:
                rec[col] = val
        result.append(rec)
    return result


def build_manual_meta_json(task_def: dict, expected_result: list[dict]) -> dict:
    """Build GeneratedTaskMeta-shaped JSON for a manual task."""
    estimated_time = 60 + 30 * task_def["difficulty"]  # 90..210 s
    return {
        "task": {
            "title": task_def["title"],
            "description": task_def["description"],
            "primary_concept": task_def["concept"],
            "secondary_concepts": task_def.get("secondary", []),
            "difficulty": task_def["difficulty"],
            "estimated_time_sec": min(estimated_time, 600),
            "sandbox_schema": "ecommerce_v1",
            "expected_query": task_def["query"],
            "expected_result": expected_result,
            "targets_misconception": task_def.get("misconception"),
            "pedagogical_notes": task_def.get("notes"),
        },
        "generation_id": str(uuid.uuid4()),
        "api_input_tokens": 0,
        "api_output_tokens": 0,
        "api_cached_tokens": 0,
        "retries": 0,
        "validation_passed": True,
        "validation_failures": [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_used": "manual",
        "extended_thinking": False,
        "generation_method": "manual",
    }


def save_task(meta: dict, output_dir: Path) -> Path:
    """Save manual task to output_dir/validated/<concept>_d<difficulty>_manual_<uuid8>.json."""
    out = output_dir / "validated"
    out.mkdir(parents=True, exist_ok=True)
    fname = (
        f"{meta['task']['primary_concept']}_"
        f"d{meta['task']['difficulty']}_"
        f"manual_{meta['generation_id'][:8]}.json"
    )
    path = out / fname
    path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    backend_root = Path(__file__).resolve().parents[1]
    load_dotenv(backend_root / ".env")

    sandbox_url = os.environ.get(
        "SANDBOX_DATABASE_URL",
        "postgresql+psycopg://sandbox_admin:sandbox_dev_password@localhost:5433/sandbox",
    ).replace("postgresql+psycopg://", "postgresql://")

    output_dir = backend_root.parent / "data" / "generated_tasks"

    log.info("Connecting to sandbox: %s", sandbox_url.split("@")[1])

    saved_paths = []
    with psycopg.connect(sandbox_url, autocommit=False) as conn:
        # Set read-only role i ecommerce_v1 search_path (tables žive u ecommerce_v1 schema-i)
        with conn.cursor() as cur:
            cur.execute("SET ROLE sandbox_readonly;")
            cur.execute("SET search_path TO ecommerce_v1, public;")
        for i, task_def in enumerate(TASKS, 1):
            log.info(
                "[%d/%d] %s d=%d — %s",
                i,
                len(TASKS),
                task_def["concept"],
                task_def["difficulty"],
                task_def["title"][:60],
            )
            try:
                rows = fetch_rows(conn, task_def["query"])
            except Exception as e:
                log.error("FAILED to run query: %s", e)
                conn.rollback()
                continue
            log.info("  → %d rows fetched", len(rows))

            meta = build_manual_meta_json(task_def, rows)
            path = save_task(meta, output_dir)
            saved_paths.append(path)
            log.info("  → saved %s", path.name)

    log.info("=" * 60)
    log.info("DONE: saved %d/%d manual tasks", len(saved_paths), len(TASKS))
    return 0 if len(saved_paths) == len(TASKS) else 1


if __name__ == "__main__":
    sys.exit(main())
