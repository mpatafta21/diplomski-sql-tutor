"""KORAK 2 pripreme prolaza: konacni plan iz verificiranih kandidata.

Raspodjela: ~60 % tocno iz prve, ~30 % jedna netocna, ~10 % dvije netocne.
Dodjela je DETERMINISTICKA (rotacija 6/3/1 po pedagoskom redoslijedu), ne
nasumicna -- da se prolaz moze ponoviti i da se u radu moze reci po cemu je
"prosjecan student" prosjecan.

Uz rotaciju idu dvije rucne intervencije, obje eksplicitne:
  * POKRIVENOST -- zadaci kojima se namjerno namece tip greske, jer se
    `timeout`, `plan_mismatch` i `explain_submitted` spontano ne pojave;
  * HINT_ZADACI -- zadaci na kojima se trazi savjet (5 komada, limit sustava).

Pokreni::

    python3 scripts/prolaz/2_plan.py

Ulaz: `frontend/e2e-prolaz/kandidati.json` · Izlaz: `frontend/e2e-prolaz/plan.json`
"""
from __future__ import annotations

import json
from collections import Counter

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
ULAZ = _REPO / "frontend" / "e2e-prolaz" / "kandidati.json"
IZLAZ = _REPO / "frontend" / "e2e-prolaz" / "plan.json"

kand = json.load(open(ULAZ, encoding="utf-8"))

# Rucno dodan kandidat: timeout se ne pojavi spontano ni na jednoj mutaciji
# (izmjereno: 3-tablicni kartezijev produkt 200x1000x3000 -> 6359 ms > 5000 ms).
kand["52"]["kandidati"].insert(0, {
    "mutacija": "bez_uvjeta_spajanja",
    "opis": "zaboravljen uvjet spajanja u troclanom JOIN-u (kartezijev produkt)",
    "query": "SELECT COUNT(*) AS total_order_items,\n"
             "       COUNT(DISTINCT o.id) AS distinct_orders,\n"
             "       COUNT(DISTINCT c.id) AS distinct_customers\n"
             "FROM customers c, orders o, order_items oi",
    "error_type": "timeout",
    "is_correct": False,
    "detail": "Statement timeout after 5000ms",
})

# 🔴 Mutacije koje su pogodile tekstualni literal unutar CASE-a, a ne naziv
# stupca -- nisu vjerodostojan "tipfeler u stupcu" i sustav ih ocjenjuje tocnima.
for tid in ("41", "42", "43"):
    kand[tid]["kandidati"] = [
        k for k in kand[tid]["kandidati"]
        if not (k["mutacija"] == "tipfeler_stupca" and k["is_correct"])
    ]

# ---------------------------------------------------------------------------
# Pedagoski redoslijed (isti kojim su zadaci izlistani u Modulima)
# ---------------------------------------------------------------------------
REDOSLIJED_KONCEPATA = [
    "select_basic", "from_clause", "where_filter", "order_by", "limit_offset", "distinct",
    "group_by", "having_filter", "agg_count", "agg_sum_avg", "agg_min_max",
    "inner_join", "left_join", "right_join", "full_outer_join", "cross_join",
    "self_join", "multi_table_join",
    "insert", "update", "delete",
    "scalar_subquery", "in_subquery", "exists_subquery", "correlated_subquery",
    "null_handling", "column_alias", "explain_plan", "index_usage",
]
def kljuc(v):
    c = v["koncept"]
    i = REDOSLIJED_KONCEPATA.index(c) if c in REDOSLIJED_KONCEPATA else 99
    return (i, v["difficulty"], v["task_id"])

zadaci = sorted(kand.values(), key=kljuc)

# ---------------------------------------------------------------------------
# 🔴 Namjerne pokrivenosti taksonomije + zadaci na kojima se trazi savjet.
# Svaki od njih MORA imati barem jednu netocnu predaju.
# ---------------------------------------------------------------------------
TRAZENI_TIP = {
    52: "timeout",
    3782: "plan_mismatch",
    3784: "plan_mismatch",
    3783: "explain_submitted",
    81: "explain_submitted",
    17: "empty_result",
    30: "execution_error",
    55: "wrong_columns",
    35: "row_mismatch",
    62: "row_mismatch",
}
# Zadatak 13: mutacija koju sustav OCJENJUJE TOCNOM (zaboravljen ORDER BY).
# Nije "netocna predaja" po ishodu -- vodi se zasebno, kao provjera ponasanja.
SONDA_BEZ_ORDER_BY = 13

HINT_ZADACI = [30, 35, 55, 3784, 62]  # tocno 5, redoslijed = redoslijed trosenja

# ---------------------------------------------------------------------------
# Rotacija 6/3/1 -> 60/30/10
# ---------------------------------------------------------------------------
profil = {}
for i, v in enumerate(zadaci):
    r = i % 10
    profil[v["task_id"]] = 0 if r <= 5 else (1 if r <= 8 else 2)

# Zadaci s trazenim tipom moraju imati >=1 netocnu; kompenziraj tako da se
# jednom zadatku s 1 netocnom (koji nije trazen) profil spusti na 0.
slobodni = [v["task_id"] for v in zadaci
            if profil[v["task_id"]] == 1 and v["task_id"] not in TRAZENI_TIP]
for tid in TRAZENI_TIP:
    if profil.get(tid, 0) == 0:
        profil[tid] = 1
        if slobodni:
            profil[slobodni.pop()] = 0

def odaberi(v, tip=None, osim=()):
    """Prvi kandidat trazenog tipa (ili bilo koji netocan), bez ponavljanja mutacije."""
    for k in v["kandidati"]:
        if k["is_correct"] or k["mutacija"] in osim:
            continue
        if tip is None or k["error_type"] == tip:
            return k
    return None

plan = {"meta": {}, "zadaci": {}}
nepokriveni = []
for v in zadaci:
    tid = v["task_id"]
    n = profil[tid]
    pokusaji = []
    korišteno = []
    for j in range(n):
        tip = TRAZENI_TIP.get(tid) if j == 0 else None
        k = odaberi(v, tip, korišteno) or odaberi(v, None, korišteno)
        if k is None:
            nepokriveni.append(tid)
            continue
        korišteno.append(k["mutacija"])
        pokusaji.append({**k, "namjera": "netocno", "ocekivano": k["error_type"]})
    # 🔴 Sonda ide POSLIJE netocnih, ne prije: student koji je pogrijesio smjer
    # sortiranja realno pokusa "pa dobro, maknut cu ORDER BY". Ako sustav to
    # ocijeni tocnim, zadatak je time rijesen i posljednji (stvarno tocan) upit
    # se ne predaje -- upravo to je nalaz koji se sondom mjeri.
    if tid == SONDA_BEZ_ORDER_BY:
        sonda = next(k for k in v["kandidati"] if k["mutacija"] == "bez_order_by")
        pokusaji.append({**sonda, "namjera": "sonda", "ocekivano": "correct"})
    pokusaji.append({
        "mutacija": None, "opis": "tocno rjesenje", "query": v["tocan_upit"],
        "error_type": None, "is_correct": True, "namjera": "tocno", "ocekivano": "correct",
    })
    plan["zadaci"][str(tid)] = {
        "task_id": tid, "koncept": v["koncept"], "tier": v["tier"], "modul": v["modul"],
        "difficulty": v["difficulty"], "naslov": v["naslov"],
        "profil": n, "hint": tid in HINT_ZADACI, "pokusaji": pokusaji,
    }

raspodjela = Counter(profil.values())
tipovi = Counter(p["ocekivano"] for z in plan["zadaci"].values()
                 for p in z["pokusaji"] if p["namjera"] == "netocno")
plan["meta"] = {
    "opis": "Plan e2e prolaza kroz svih 88 aktivnih zadataka. Netocni upiti su "
            "izvedeni iz expected_query imenovanim studentskim greskama i "
            "VERIFICIRANI kroz agents.evaluation.evaluate prije prolaza.",
    "broj_zadataka": len(plan["zadaci"]),
    "raspodjela": {"tocno_iz_prve": raspodjela[0], "jedna_netocna": raspodjela[1],
                   "dvije_netocne": raspodjela[2]},
    "ocekivani_tipovi_gresaka": dict(tipovi),
    "hint_zadaci": HINT_ZADACI,
    # 🔴 JSON objekt s brojcanim kljucevima u JS-u iterira ASCENDENTNO, ne
    # redoslijedom upisa -- pedagoski red se zato prenosi eksplicitno.
    "redoslijed_zadataka": [v["task_id"] for v in zadaci],
    "sonda_bez_order_by": SONDA_BEZ_ORDER_BY,
}
json.dump(plan, open(IZLAZ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

uk = len(plan["zadaci"])
print("zadataka:", uk)
print("raspodjela:", {k: f"{v} ({100*v/uk:.1f} %)" for k, v in
      [("tocno iz prve", raspodjela[0]), ("jedna netocna", raspodjela[1]),
       ("dvije netocne", raspodjela[2])]})
print("ocekivani tipovi:", dict(tipovi))
print("ukupno predaja:", sum(len(z["pokusaji"]) for z in plan["zadaci"].values()))
print("bez kandidata:", nepokriveni)
print("->", IZLAZ)
