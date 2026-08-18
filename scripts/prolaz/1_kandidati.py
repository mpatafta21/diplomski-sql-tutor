"""KORAK 1 pripreme prolaza: kandidati za netocne predaje.

Iz `tasks.expected_query` izvodi IMENOVANE studentske greske (zaboravljen GROUP BY,
krivi smjer sortiranja, tipfeler u stupcu, CAST koji ponistava indeks...) i svaku
VERIFICIRA kroz pravu evaluacijsku jezgru `agents.evaluation.evaluate` -- isti put
kojim ide studentov upit, samo bez perzistencije.

🔴 Zasto verifikacija: bez nje bi se u prolaz uslo s pretpostavkom o tome sto
koja greska proizvodi. Prolaz se NE VRACA na baseline, pa pogresna pretpostavka
znaci pogresan podatak u bazi koji se ne moze povuci.

🔴 READ-ONLY: ne pise u `tutor_main`, ne stvara attempte, ne budi agente.

Pokreni iz `backend/`::

    cd backend && uv run python ../scripts/prolaz/1_kandidati.py

Izlaz: `frontend/e2e-prolaz/kandidati.json`
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "backend"))

from sqlalchemy import select  # noqa: E402

from agents.evaluation import evaluate  # noqa: E402
from agents.evaluator_agent import _sandbox_conn_string  # noqa: E402
from app.db.models import Concept, Module, Task, TaskConcept  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from scripts.lib.sandbox_runner import SandboxRunner  # noqa: E402

# ---------------------------------------------------------------------------
# Mutacije -- svaka je IMENOVANA studentska greska, ne nasumicna perturbacija
# ---------------------------------------------------------------------------

def _clean(q: str) -> str:
    return q.strip().rstrip(";").strip()


def m_smjer_sortiranja(q: str, **_) -> str | None:
    """Krivi smjer sortiranja: prvi ASC<->DESC u ORDER BY."""
    m = re.search(r"\bORDER\s+BY\b", q, re.I)
    if not m:
        return None
    head, tail = q[: m.end()], q[m.end():]
    if re.search(r"\bDESC\b", tail, re.I):
        return head + re.sub(r"\bDESC\b", "ASC", tail, count=1, flags=re.I)
    if re.search(r"\bASC\b", tail, re.I):
        return head + re.sub(r"\bASC\b", "DESC", tail, count=1, flags=re.I)
    return None


def m_bez_order_by(q: str, **_) -> str | None:
    """Zaboravljen ORDER BY (ostatak upita netaknut)."""
    m = re.search(r"\bORDER\s+BY\b", q, re.I)
    if not m:
        return None
    tail = q[m.end():]
    lim = re.search(r"\bLIMIT\b", tail, re.I)
    return q[: m.start()].rstrip() + (" " + tail[lim.start():].strip() if lim else "")


def m_bez_group_by(q: str, **_) -> str | None:
    """Zaboravljen GROUP BY uz agregat u SELECT listi."""
    m = re.search(r"\bGROUP\s+BY\b", q, re.I)
    if not m:
        return None
    tail = q[m.end():]
    nxt = re.search(r"\b(HAVING|ORDER\s+BY|LIMIT)\b", tail, re.I)
    return q[: m.start()].rstrip() + (" " + tail[nxt.start():].strip() if nxt else "")


def m_zaboravljen_alias(q: str, **_) -> str | None:
    """Zaboravljen AS alias na agregatu -> stupac se zove count/sum/max..."""
    m = re.search(
        r"\b(COUNT|SUM|AVG|MIN|MAX|ROUND)\s*\([^()]*(?:\([^()]*\)[^()]*)*\)\s+AS\s+\w+",
        q, re.I,
    )
    if not m:
        return None
    bez = re.sub(r"\s+AS\s+\w+$", "", m.group(0), flags=re.I)
    return q[: m.start()] + bez + q[m.end():]


def m_krivi_literal(q: str, **_) -> str | None:
    """Krivo napisan tekstualni literal (velicina slova) -> prazan rezultat."""
    for lit in re.finditer(r"'([A-Za-z][A-Za-z _-]{2,})'", q):
        val = lit.group(1)
        if val.lower() == val:                 # 'delivered' -> 'Delivered'
            novi = val.capitalize()
        elif val[0].isupper():                 # 'Croatia'   -> 'croatia'
            novi = val.lower()
        else:
            continue
        return q[: lit.start()] + f"'{novi}'" + q[lit.end():]
    return None


def m_tipfeler_stupca(q: str, **_) -> str | None:
    """Tipfeler u nazivu stupca u SELECT listi (dupli suglasnik ispada)."""
    m = re.match(r"(?is)\s*SELECT\s+(?:DISTINCT\s+)?(.*?)\s+FROM\b", q)
    if not m:
        return None
    lista = m.group(1)
    for ident in re.finditer(r"\b([a-z][a-z_]{4,})\b", lista):
        naziv = ident.group(1)
        if naziv.upper() in {"COUNT", "DISTINCT", "ROUND", "EXTRACT", "MONTH", "YEAR"}:
            continue
        if "_" in naziv:
            krivi = naziv.replace("_", "", 1)          # first_name -> firstname
        else:
            krivi = naziv + "s"                        # status -> statuss
        s, e = m.start(1) + ident.start(1), m.start(1) + ident.end(1)
        return q[:s] + krivi + q[e:]
    return None


def m_agregat_u_where(q: str, **_) -> str | None:
    """HAVING uvjet prebacen u WHERE -- agregat u WHERE, PG odbija."""
    m = re.search(r"\bHAVING\b(.*?)(?=\bORDER\s+BY\b|\bLIMIT\b|$)", q, re.I | re.S)
    if not m:
        return None
    uvjet = m.group(1).strip()
    bez_having = (q[: m.start()] + q[m.end():]).rstrip()
    g = re.search(r"\bGROUP\s+BY\b", bez_having, re.I)
    if not g:
        return None
    return bez_having[: g.start()].rstrip() + f" WHERE {uvjet} " + bez_having[g.start():]


def m_bez_uvjeta_spajanja(q: str, **_) -> str | None:
    """Zaboravljen uvjet spajanja -> kartezijev produkt."""
    if not re.search(r"\bJOIN\b", q, re.I):
        return None
    out = re.sub(r"\b(?:INNER\s+|LEFT\s+|RIGHT\s+|FULL\s+(?:OUTER\s+)?)?JOIN\b", ",", q, flags=re.I)
    out = re.sub(r"\bON\s+[\w.]+\s*=\s*[\w.]+", "", out, flags=re.I)
    return out if "ON " not in out.upper() else None


def m_bez_distinct(q: str, **_) -> str | None:
    """Zaboravljen DISTINCT."""
    if not re.search(r"\bSELECT\s+DISTINCT\b", q, re.I):
        return None
    return re.sub(r"\bSELECT\s+DISTINCT\b", "SELECT", q, count=1, flags=re.I)


def m_krivi_limit(q: str, **_) -> str | None:
    """Krivo procitan broj redaka u LIMIT-u."""
    m = re.search(r"\bLIMIT\s+(\d+)", q, re.I)
    if not m:
        return None
    n = int(m.group(1))
    return q[: m.start(1)] + str(n + 2) + q[m.end(1):]


def m_bez_returning(q: str, **_) -> str | None:
    """DML bez RETURNING -- student ne vidi da mora vratiti retke."""
    m = re.search(r"\bRETURNING\b", q, re.I)
    if not m:
        return None
    return q[: m.start()].rstrip()


def m_update_bez_where(q: str, **_) -> str | None:
    """UPDATE/DELETE bez WHERE -- klasicna greska, zahvati sve retke."""
    if not re.match(r"(?is)\s*(UPDATE|DELETE)\b", q):
        return None
    m = re.search(r"\bWHERE\b.*?(?=\bRETURNING\b|$)", q, re.I | re.S)
    if not m:
        return None
    return (q[: m.start()] + " " + q[m.end():]).strip()


def m_explain_prefiks(q: str, **_) -> str | None:
    """M6: student zalijepi EXPLAIN u editor."""
    return "EXPLAIN " + _clean(q)


#: M6 anti-patterni -- doslovno iz backend/scripts/manual_tasks_m6.py (gate
#: diskriminacije jamci: ISTI retci, DRUGI plan -> plan_mismatch).
ANTI_PATTERN = {
    3782: "SELECT order_id, product_id, quantity, unit_price FROM order_items "
          "WHERE CAST(order_id AS TEXT) = '500' ORDER BY product_id",
    3783: "SELECT id, product_id, customer_id, rating FROM reviews "
          "WHERE product_id + 0 = 3 ORDER BY id",
    3784: "SELECT o.id, o.status, oi.product_id, oi.quantity FROM orders o "
          "JOIN order_items oi ON oi.order_id = o.id "
          "WHERE CAST(o.customer_id AS TEXT) = '42' ORDER BY o.id, oi.product_id",
    3785: "SELECT o.id, o.order_date, oi.product_id, oi.quantity "
          "FROM orders o JOIN order_items oi ON oi.order_id = o.id "
          "WHERE o.customer_id + 0 = 108 ORDER BY o.id, oi.product_id",
    81:   "SELECT id, customer_id, status, total_amount FROM orders "
          "WHERE CAST(customer_id AS TEXT) = '108' ORDER BY id ASC LIMIT 1",
}


def m_cast_ubija_indeks(q: str, *, task_id: int, **_) -> str | None:
    return ANTI_PATTERN.get(task_id)


MUTACIJE = {
    "smjer_sortiranja": (m_smjer_sortiranja, "krivi smjer sortiranja (ASC/DESC zamijenjeni)"),
    "bez_order_by": (m_bez_order_by, "zaboravljen ORDER BY"),
    "bez_group_by": (m_bez_group_by, "zaboravljen GROUP BY uz agregat"),
    "zaboravljen_alias": (m_zaboravljen_alias, "zaboravljen AS alias na agregatu"),
    "krivi_literal": (m_krivi_literal, "krivo napisan tekstualni literal"),
    "tipfeler_stupca": (m_tipfeler_stupca, "tipfeler u nazivu stupca"),
    "agregat_u_where": (m_agregat_u_where, "agregatni uvjet stavljen u WHERE umjesto HAVING"),
    "bez_uvjeta_spajanja": (m_bez_uvjeta_spajanja, "zaboravljen uvjet spajanja (kartezijev produkt)"),
    "bez_distinct": (m_bez_distinct, "zaboravljen DISTINCT"),
    "krivi_limit": (m_krivi_limit, "krivo procitan broj redaka u LIMIT-u"),
    "bez_returning": (m_bez_returning, "DML bez RETURNING"),
    "update_bez_where": (m_update_bez_where, "UPDATE/DELETE bez WHERE"),
    "explain_prefiks": (m_explain_prefiks, "predan EXPLAIN umjesto samog upita"),
    "cast_ubija_indeks": (m_cast_ubija_indeks, "CAST/aritmetika nad stupcem ponistava indeks"),
}

#: Redoslijed pokusaja mutacija po konceptu -- prvo ono sto je za taj koncept
#: najvjerodostojnija greska.
PREFERENCIJE = {
    "group_by": ["bez_group_by", "smjer_sortiranja", "zaboravljen_alias"],
    "having_filter": ["agregat_u_where", "smjer_sortiranja", "zaboravljen_alias"],
    "agg_count": ["zaboravljen_alias", "bez_group_by", "smjer_sortiranja"],
    "agg_sum_avg": ["zaboravljen_alias", "bez_group_by", "smjer_sortiranja"],
    "agg_min_max": ["zaboravljen_alias", "bez_group_by", "smjer_sortiranja"],
    "distinct": ["bez_distinct", "smjer_sortiranja"],
    "limit_offset": ["krivi_limit", "smjer_sortiranja"],
    "order_by": ["smjer_sortiranja", "bez_order_by", "krivi_limit"],
    "where_filter": ["krivi_literal", "tipfeler_stupca", "smjer_sortiranja"],
    "select_basic": ["tipfeler_stupca", "smjer_sortiranja", "krivi_limit"],
    "from_clause": ["tipfeler_stupca", "krivi_limit", "smjer_sortiranja"],
    "column_alias": ["zaboravljen_alias", "smjer_sortiranja", "tipfeler_stupca"],
    "null_handling": ["zaboravljen_alias", "krivi_limit", "smjer_sortiranja"],
    "insert": ["bez_returning", "tipfeler_stupca"],
    "update": ["update_bez_where", "bez_returning"],
    "delete": ["update_bez_where", "bez_returning"],
    "index_usage": ["cast_ubija_indeks", "explain_prefiks", "smjer_sortiranja"],
    "explain_plan": ["cast_ubija_indeks", "explain_prefiks", "smjer_sortiranja"],
}
ZADANO = ["smjer_sortiranja", "zaboravljen_alias", "krivi_limit",
          "tipfeler_stupca", "bez_group_by", "krivi_literal"]

#: 🔴 Namjerne pokrivenosti: task -> (redni pokusaj, mutacija). Bez ovoga
#: taksonomija ne bi bila potpuna (timeout/plan_mismatch/explain_submitted se
#: ne pojavljuju spontano).
POKRIVENOST = {
    51: ["bez_uvjeta_spajanja"],          # timeout
    3782: ["cast_ubija_indeks"],          # plan_mismatch
    3784: ["cast_ubija_indeks"],          # plan_mismatch
    3783: ["explain_prefiks"],            # explain_submitted
    81: ["explain_prefiks"],              # explain_submitted
    17: ["krivi_literal"],                # empty_result
    30: ["bez_group_by"],                 # execution_error
    13: ["bez_order_by"],                 # provjera: prolazi li bez ORDER BY?
}


def main() -> None:
    runner = SandboxRunner(_sandbox_conn_string())
    plan: dict[str, dict] = {}
    with SessionLocal() as session:
        tasks = session.execute(
            select(Task).where(Task.is_active.is_(True)).order_by(Task.id)
        ).scalars().all()
        primary = dict(session.execute(
            select(TaskConcept.task_id, Concept.code)
            .join(Concept, Concept.id == TaskConcept.concept_id)
            .where(TaskConcept.is_primary.is_(True))
        ).all())
        cmeta = {c.code: (c.tier, c.module_id) for c in
                 session.execute(select(Concept)).scalars().all()}
        modnum = dict(session.execute(select(Module.id, Module.number)).all())

        for task in tasks:
            code = primary.get(task.id)
            tier, mod_id = cmeta.get(code, ("?", -1))
            kandidati: list[dict] = []
            redoslijed = POKRIVENOST.get(task.id, []) + \
                PREFERENCIJE.get(code, ZADANO) + ZADANO
            vidjeni = set()
            for ime in redoslijed:
                if ime in vidjeni:
                    continue
                vidjeni.add(ime)
                fn, opis = MUTACIJE[ime]
                try:
                    mutirano = fn(_clean(task.expected_query), task_id=task.id)
                except Exception as e:                      # noqa: BLE001
                    print(f"  ! {task.id} {ime}: {e}")
                    continue
                if not mutirano or _clean(mutirano) == _clean(task.expected_query):
                    continue
                ishod = evaluate(task, mutirano, runner, code)
                kandidati.append({
                    "mutacija": ime,
                    "opis": opis,
                    "query": mutirano.strip(),
                    "error_type": ishod.error_type,
                    "is_correct": ishod.is_correct,
                    "detail": (ishod.detail or "")[:200],
                })
            plan[str(task.id)] = {
                "task_id": task.id,
                "koncept": code,
                "tier": tier,
                "modul": modnum.get(mod_id, -1),
                "difficulty": task.difficulty,
                "naslov": task.title,
                "tocan_upit": _clean(task.expected_query),
                "kandidati": kandidati,
            }
            ok = [k["error_type"] for k in kandidati if not k["is_correct"]]
            print(f"  {task.id:>5} {code:<20} {len(kandidati)} kand -> {ok}")

    out = _REPO / "frontend" / "e2e-prolaz" / "kandidati.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)
    print(f"\nZapisano: {out}")


if __name__ == "__main__":
    main()
