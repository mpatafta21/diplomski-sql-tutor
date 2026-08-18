"""Ručno autorski zadaci za M6 (plan-presence) i `column_alias` — ERRATA #66.

Obrazac je `manual_tasks_2b2.py`: zadatak se definira ovdje, `expected_result` se
DOHVAĆA iz sandboxa (nikad ne piše rukom), a rezultat ide u `final_dataset.json`.
🔴 NE ide kroz LLM — #20 zabranjuje regeneraciju kataloga bez izričite odluke.

🔴 **Svaki M6 zadatak mora proći DVA gatea prije nego uđe u katalog:**

1. **stabilnost** (`plan_is_stable`) — potpis plana ne smije se mijenjati pod
   perturbacijom planera. Zadaci 79/80/82 padaju upravo ovdje: gađaju
   `customers` (200 redaka), gdje je Seq Scan stvarno jeftiniji.
2. **diskriminacija** — deklarirani anti-pattern mora vratiti ISTE RETKE ali
   DRUGI potpis. Zadatak 83 pada ovdje: `ORDER BY id LIMIT 1` uvuče `orders_pkey`
   u oba plana, pa CAST anti-pattern prolazi kao točan.

Gate 2 se ne da izraziti u shemi (anti-pattern nije svojstvo zadatka nego
njegove pouke), pa `anti_pattern` živi ovdje i u testu — ne u bazi.

Pokretanje:
    cd backend && uv run python -m scripts.manual_tasks_m6          # dry-run
    cd backend && uv run python -m scripts.manual_tasks_m6 --write  # upiši
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from agents.evaluation import plan_is_stable, signature_of
from agents.evaluator_agent import _sandbox_conn_string
from scripts.lib.sandbox_runner import SandboxRunner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("manual_tasks_m6")

DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "generated_tasks"
    / "final_dataset.json"
)

# ---------------------------------------------------------------------------
# Zadaci
#
# `anti_pattern` je upit koji vraća ISTI rezultat a krivo se izvodi. Postoji SAMO
# za M6 i služi kao dokaz da zadatak nešto razlikuje.
# ---------------------------------------------------------------------------

TASKS: list[dict[str, Any]] = [
    # ─── index_usage ────────────────────────────────────────────────────────
    {
        "primary_concept": "index_usage",
        "module": 6,
        "difficulty": 3,
        "title": "Stavke narudžbe — indeks na order_id vs. CAST anti-pattern",
        "description": (
            "Dohvati sve stavke narudžbe s order_id = 500. Ispiši stupce "
            "order_id, product_id, quantity i unit_price, sortirano po "
            "product_id uzlazno.\n\n"
            "Tablica order_items ima indeks idx_order_items_order na koloni "
            "order_id. Napiši uvjet tako da ga baza može upotrijebiti — "
            "usporedi kolonu izravno s brojem. Ako kolonu omotaš u funkciju "
            "ili je pretvoriš u drugi tip (npr. CAST(order_id AS TEXT) = "
            "'500'), indeks postaje neupotrebljiv i baza mora pročitati svih "
            "3000 redaka. Rezultat će biti isti, ali način izvođenja neće — "
            "a upravo se on ovdje ocjenjuje."
        ),
        "secondary_concepts": ["where_filter", "order_by"],
        "query": (
            "SELECT order_id, product_id, quantity, unit_price\n"
            "FROM order_items\n"
            "WHERE order_id = 500\n"
            "ORDER BY product_id;"
        ),
        "anti_pattern": (
            "SELECT order_id, product_id, quantity, unit_price "
            "FROM order_items WHERE CAST(order_id AS TEXT) = '500' "
            "ORDER BY product_id;"
        ),
    },
    {
        "primary_concept": "index_usage",
        "module": 6,
        "difficulty": 4,
        "title": "Recenzije proizvoda — aritmetika nad kolonom poništava indeks",
        "description": (
            "Dohvati sve recenzije proizvoda s product_id = 3. Ispiši stupce "
            "id, product_id, customer_id i rating, sortirano po id uzlazno.\n\n"
            "Nad kolonom product_id postoji indeks idx_reviews_product. "
            "Uvjet mora usporediti kolonu izravno s vrijednošću. Čest previd je "
            "napisati WHERE product_id + 0 = 3 ili neku sličnu aritmetiku — "
            "izraz je matematički jednak, ali baza tada mora izračunati "
            "product_id + 0 za svaki redak i indeks ne može pomoći. Isto "
            "vrijedi za CAST i pozive funkcija nad indeksiranom kolonom."
        ),
        "secondary_concepts": ["where_filter", "order_by"],
        "query": (
            "SELECT id, product_id, customer_id, rating\n"
            "FROM reviews\n"
            "WHERE product_id = 3\n"
            "ORDER BY id;"
        ),
        "anti_pattern": (
            "SELECT id, product_id, customer_id, rating FROM reviews "
            "WHERE product_id + 0 = 3 ORDER BY id;"
        ),
    },
    # ─── explain_plan ───────────────────────────────────────────────────────
    {
        "primary_concept": "explain_plan",
        "module": 6,
        "difficulty": 3,
        "title": "Selektivan filtar mijenja strategiju spoja u Nested Loop",
        "description": (
            "Dohvati stavke svih narudžbi kupca s customer_id = 42. Ispiši "
            "o.id, o.status, oi.product_id i oi.quantity, sortirano po o.id pa "
            "po oi.product_id.\n\n"
            "Kad spajaš orders i order_items BEZ filtra, baza mora pročitati "
            "obje tablice u cijelosti i spaja ih preko Hash Joina. Selektivan "
            "filtar na customer_id mijenja račun: baza indeksom nađe nekoliko "
            "narudžbi tog kupca, pa za svaku indeksom potraži stavke — Nested "
            "Loop. Ako filtar napišeš tako da poništi indeks (npr. "
            "CAST(o.customer_id AS TEXT) = '42'), rezultat ostaje isti, ali se "
            "plan vraća na Hash Join uz puno čitanje obje tablice. Pogledaj "
            "razliku sam: pokreni EXPLAIN nad obje verzije kroz Pokreni."
        ),
        "secondary_concepts": ["inner_join", "where_filter", "order_by"],
        "query": (
            "SELECT o.id, o.status, oi.product_id, oi.quantity\n"
            "FROM orders o\n"
            "JOIN order_items oi ON oi.order_id = o.id\n"
            "WHERE o.customer_id = 42\n"
            "ORDER BY o.id, oi.product_id;"
        ),
        "anti_pattern": (
            "SELECT o.id, o.status, oi.product_id, oi.quantity FROM orders o "
            "JOIN order_items oi ON oi.order_id = o.id "
            "WHERE CAST(o.customer_id AS TEXT) = '42' "
            "ORDER BY o.id, oi.product_id;"
        ),
    },
    {
        "primary_concept": "explain_plan",
        "module": 6,
        "difficulty": 4,
        "title": "Aritmetika u uvjetu spoja vraća plan na Hash Join",
        "description": (
            "Dohvati stavke svih narudžbi kupca s customer_id = 108. Ispiši "
            "o.id, o.order_date, oi.product_id i oi.quantity, sortirano po "
            "o.id pa po oi.product_id.\n\n"
            "Zadatak je isti oblik kao prethodni, ali s drugom zamkom: umjesto "
            "CAST-a, uvjet se pokvari aritmetikom (WHERE o.customer_id + 0 = "
            "108). Posljedica je jednaka — indeks idx_orders_customer se ne "
            "može upotrijebiti, pa baza čita cijelu tablicu narudžbi i prelazi "
            "s Nested Loopa na Hash Join. Pravilo koje treba zapamtiti: "
            "indeksirana kolona u WHERE uvjetu mora stajati SAMA s jedne "
            "strane usporedbe."
        ),
        "secondary_concepts": ["inner_join", "where_filter", "order_by"],
        "query": (
            "SELECT o.id, o.order_date, oi.product_id, oi.quantity\n"
            "FROM orders o\n"
            "JOIN order_items oi ON oi.order_id = o.id\n"
            "WHERE o.customer_id = 108\n"
            "ORDER BY o.id, oi.product_id;"
        ),
        "anti_pattern": (
            "SELECT o.id, o.order_date, oi.product_id, oi.quantity "
            "FROM orders o JOIN order_items oi ON oi.order_id = o.id "
            "WHERE o.customer_id + 0 = 108 ORDER BY o.id, oi.product_id;"
        ),
    },
    # ─── column_alias (modul 0) ─────────────────────────────────────────────
    # 🔴 TRI zadatka, ne dva. Čim dobije zadatke, column_alias ispada iz Kat. A;
    # kako je modul 0, subfloor (modul != 0) ga NE hvata, pa nema zaštitu koju
    # ima Kat. B. Ako student riješi sve a ostane ispod praga 0.85, nizvodni
    # `group_by` mu ostaje zaključan. V. simulaciju u testovima.
    {
        "primary_concept": "column_alias",
        "module": 0,
        "difficulty": 1,
        "title": "Preimenuj stupce u ispisu kupaca",
        "description": (
            "Iz tablice customers ispiši ime i prezime kupaca iz grada "
            "Zagreba, ali tako da se stupci u rezultatu zovu ime i prezime "
            "(umjesto first_name i last_name). Za preimenovanje stupca koristi "
            "ključnu riječ AS. Sortiraj po id uzlazno."
        ),
        "secondary_concepts": ["select_basic", "where_filter", "order_by"],
        "query": (
            "SELECT first_name AS ime, last_name AS prezime\n"
            "FROM customers\n"
            "WHERE city = 'Zagreb'\n"
            "ORDER BY id;"
        ),
    },
    {
        "primary_concept": "column_alias",
        "module": 0,
        "difficulty": 2,
        "title": "Alias nad izračunatim stupcem — cijena s PDV-om",
        "description": (
            "Iz tablice products ispiši naziv proizvoda i njegovu cijenu "
            "uvećanu za 25 % PDV-a, zaokruženu na 2 decimale. Stupci u "
            "rezultatu moraju se zvati naziv i cijena_s_pdv. Izračunati stupac "
            "BEZ aliasa dobiva ime koje generira baza (npr. ?column?), pa je "
            "alias ovdje obavezan, ne kozmetika. Koristi ROUND(price * 1.25, "
            "2). Sortiraj po id uzlazno i ograniči na 10 redaka."
        ),
        "secondary_concepts": ["select_basic", "order_by", "limit_offset"],
        "query": (
            "SELECT name AS naziv, ROUND(price * 1.25, 2) AS cijena_s_pdv\n"
            "FROM products\n"
            "ORDER BY id\n"
            "LIMIT 10;"
        ),
    },
    {
        "primary_concept": "column_alias",
        "module": 0,
        "difficulty": 2,
        "title": "Sortiranje po aliasu stupca",
        "description": (
            "Iz tablice products ispiši naziv proizvoda kao naziv i količinu "
            "na zalihi kao zaliha. Rezultat sortiraj silazno po zalihi, pa "
            "uzlazno po nazivu, koristeći ALIASE u ORDER BY klauzuli (ne "
            "izvorna imena stupaca). PostgreSQL to dopušta jer se ORDER BY "
            "izvodi nakon SELECT-a — za razliku od WHERE, koji alias NE vidi. "
            "Ograniči na 10 redaka."
        ),
        "secondary_concepts": ["select_basic", "order_by", "limit_offset"],
        "query": (
            "SELECT name AS naziv, stock AS zaliha\n"
            "FROM products\n"
            "ORDER BY zaliha DESC, naziv ASC\n"
            "LIMIT 10;"
        ),
    },
]


#: Zatečeni M6 zadaci koji se NE aktiviraju, s razlogom (ERRATA #66).
#:
#: 🔴 Ne brišu se. Zadatak koji je pao na mjerenju dokaz je nalaza; brisanjem bi
#: ostala samo tvrdnja u errati, a `sweep_task_integrity` i testovi izgubili bi
#: negativan primjer na kojem se gate provjerava (poučak #39).
DEACTIVATE: dict[str, str] = {
    "explain_plan_d3_60b9eaee": (
        "referentni upit daje Seq Scan nad customers (200 redaka) — opis tvrdi "
        "Index Scan; planer je u pravu, zadatak nije. Gate stabilnosti ga odbija."
    ),
    "explain_plan_d4_54c05243": (
        "isti kvar kao explain_plan_d3_60b9eaee — Seq Scan nad customers."
    ),
    "index_usage_d4_68049f11": (
        "isti kvar — Seq Scan nad customers umjesto obećanog Index Scana."
    ),
    "index_usage_d5_258d461b": (
        "referentni upit i CAST anti-pattern daju IDENTIČAN plan (Index Scan "
        "preko orders_pkey): ORDER BY id LIMIT 1 uvuče pkey, a ciljani "
        "idx_orders_customer se uopće ne dira. Zadatak ne razlikuje ništa."
    ),
}


def _source_id(task: dict[str, Any]) -> str:
    """`<koncept>_d<težina>_manual_<hash8>` — obrazac iz 4.4-0h."""
    digest = hashlib.sha256(task["query"].encode("utf-8")).hexdigest()[:8]
    return f"{task['primary_concept']}_d{task['difficulty']}_manual_{digest}"


def _validate(task: dict[str, Any], runner: SandboxRunner) -> list[dict]:
    """Izvrši referentni upit, provjeri gateove, vrati `expected_result`."""
    sid = _source_id(task)

    result = runner.execute(task["query"])
    if not result.success:
        raise SystemExit(f"🔴 [{sid}] referentni upit pada: {result.error}")
    if not result.rows:
        raise SystemExit(f"🔴 [{sid}] referentni upit vraća 0 redaka")

    anti = task.get("anti_pattern")
    if anti is None:
        log.info("  [%s] %d redaka (bez plan-gatea, nije M6)", sid, len(result.rows))
        return result.rows

    # Gate 1 — stabilnost plana.
    stabilan, razlog = plan_is_stable(task["query"], runner)
    if not stabilan:
        raise SystemExit(f"🔴 [{sid}] GATE STABILNOSTI: {razlog}")

    # Gate 2 — diskriminacija: isti redci, drugi potpis.
    anti_result = runner.execute(anti)
    if not anti_result.success:
        raise SystemExit(f"🔴 [{sid}] anti-pattern ne izvodi se: {anti_result.error}")
    if anti_result.rows != result.rows:
        raise SystemExit(
            f"🔴 [{sid}] anti-pattern vraća DRUGE retke — tada ga hvata već "
            "usporedba redaka i zadatak ne dokazuje ništa o planu"
        )

    ref_sig = signature_of(runner.explain(task["query"]))
    anti_sig = signature_of(runner.explain(anti))
    if ref_sig == anti_sig:
        raise SystemExit(
            f"🔴 [{sid}] GATE DISKRIMINACIJE: anti-pattern ima ISTI potpis "
            f"({ref_sig}) — zadatak bi ga prihvatio kao točan (kvar zadatka 83)"
        )

    log.info(
        "  [%s] %d redaka | ref idx=%s join=%s | anti idx=%s join=%s ✓",
        sid,
        len(result.rows),
        sorted(ref_sig.index_names),
        sorted(ref_sig.join_methods),
        sorted(anti_sig.index_names),
        sorted(anti_sig.join_methods),
    )
    return result.rows


def build_entries() -> list[dict[str, Any]]:
    runner = SandboxRunner(_sandbox_conn_string())
    entries: list[dict[str, Any]] = []
    for task in TASKS:
        rows = _validate(task, runner)
        # 🔴 IZVORNI tipovi, ne stringovi. `module` i `difficulty` su int, a
        # `secondary_concepts` i `expected_result` liste — točno kako ih pišu
        # zatečeni unosi. Prva verzija ove skripte serijalizirala ih je kroz
        # str() i import je pao na „nepoznat module number 6" (mapa je po int-u).
        entries.append(
            {
                "task_id": _source_id(task),
                "title": task["title"],
                "description": task["description"],
                "module": int(task["module"]),
                "primary_concept": task["primary_concept"],
                "secondary_concepts": list(task["secondary_concepts"]),
                "difficulty": int(task["difficulty"]),
                "estimated_time_sec": 90,
                "sandbox_schema": "ecommerce_v1",
                "expected_query": task["query"],
                "expected_result": rows,
                "generation_method": "manual",
                "approved_by_human": True,
                "recovery_applied": False,
                "is_active": True,
            }
        )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", action="store_true", help="upiši u final_dataset.json"
    )
    args = parser.parse_args()

    log.info("Validacija %d zadataka…", len(TASKS))
    entries = build_entries()
    log.info("Svi zadaci prošli gateove ✓")

    if not args.write:
        log.info("DRY-RUN — ništa nije upisano. Pokreni s --write.")
        return

    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    postojeci = {t["task_id"] for t in data["tasks"]}
    novi = [e for e in entries if e["task_id"] not in postojeci]

    # Svaki zatečeni zadatak dobiva EKSPLICITAN `is_active` — dosad je za M6
    # bio izveden iz `UNSUPPORTED_CONCEPTS`, a taj kriterij više ne vrijedi
    # (koncepti su evaluabilni; neispravni su POJEDINI zadaci).
    oznaceno = 0
    for t in data["tasks"]:
        sid = t["task_id"]
        if sid in DEACTIVATE:
            t["is_active"] = False
            t["deactivation_reason"] = DEACTIVATE[sid]
            oznaceno += 1
        else:
            t.setdefault("is_active", True)

    data["tasks"].extend(novi)
    data["total"] = len(data["tasks"])
    data["version"] = "2b-3+4.4-0h+m6-plan-presence"
    data.setdefault("changelog", []).append(
        {
            "version": "m6-plan-presence",
            "date": "2026-08-14",
            "note": (
                f"ERRATA #66: {len(novi)} ručno autorskih zadataka "
                f"(index_usage ×2, explain_plan ×2, column_alias ×3); "
                f"{oznaceno} zatečena M6 zadatka trajno deaktivirana uz razlog. "
                "is_active je od sada EKSPLICITAN po zadatku, ne izveden iz koncepta."
            ),
        }
    )
    DATASET_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    log.info(
        "Upisano %d novih, deaktivirano %d zatečenih; ukupno %d.",
        len(novi),
        oznaceno,
        data["total"],
    )


if __name__ == "__main__":
    main()
