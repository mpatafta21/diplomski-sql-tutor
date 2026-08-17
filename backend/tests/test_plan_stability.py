"""TDD testovi za `plan_is_stable` — uvozni gate za M6 zadatke (ERRATA #66).

🔴 **Povod je bio FLAKY TEST, ne teorija.** Test koji tvrdi ishod za zadatak 79
prošao je izolirano a pao u punoj datoteci: plan za `customers` prebacuje se
između Seq Scana i Index Scana ovisno o prolaznom stanju statistike (mrtvi redci
iz rollbackanog DML-a mijenjaju `relpages`, a time i cijenu Seq Scana).

Izmjereno 2026-08-14 — margina izbora plana (cijena alternative / cijena
odabranog):

| upit | margina | stabilan |
|---|---|---|
| `customers WHERE email = …` (task 79/80/82) | **1.48x** | 🔴 NE |
| `orders WHERE customer_id = 42` | 1.00x | ✅ |
| `order_items WHERE order_id = 500` | 1.00x | ✅ |
| `orders ORDER BY order_date DESC LIMIT 10` | 1.00x | ✅ |
| spoj orders×order_items BEZ filtra | — | 🔴 NE (`seqscan off` prevrne indeks) |
| spoj orders×order_items S filtrom | — | ✅ |

Margina 1.00x znači da gašenje seq scana ne mijenja cijenu — planer indeks bira
**bezuvjetno**, nema ruba s kojeg bi se prebacio.

Gate zato traži da potpis bude **nepromijenjen pod perturbacijom planera**.
Zadatak čiji plan ovisi o tome je li autovacuum upravo prošao nije zadatak nego
generator flaky ocjena.

Pokretanje: uv run pytest tests/test_plan_stability.py -v
"""

from __future__ import annotations

from agents.evaluation import STABILITY_FLAGS, plan_is_stable, plan_signature

# ---------------------------------------------------------------------------
# Upiti iz mjerenja
# ---------------------------------------------------------------------------

_NESTABILAN_MALA_TABLICA = (
    "SELECT id FROM customers WHERE email = 'skodamartina@example.org'"
)
_STABILAN_ORDERS = "SELECT id FROM orders WHERE customer_id = 42"
_STABILAN_ORDER_ITEMS = "SELECT product_id FROM order_items WHERE order_id = 500"
_STABILAN_LIMIT = "SELECT id FROM orders ORDER BY order_date DESC LIMIT 10"
_NESTABILAN_SPOJ = (
    "SELECT o.id, oi.quantity FROM orders o JOIN order_items oi ON oi.order_id = o.id"
)
_STABILAN_SPOJ = (
    "SELECT o.id, oi.quantity FROM orders o JOIN order_items oi "
    "ON oi.order_id = o.id WHERE o.customer_id = 42"
)


# ---------------------------------------------------------------------------
# Gate odbija ono što je flaky
# ---------------------------------------------------------------------------


def test_odbija_upit_nad_malom_tablicom(sandbox_runner):
    """🔴 Točno onaj upit na kojem su pala tri zatečena M6 zadatka."""
    stabilan, razlog = plan_is_stable(_NESTABILAN_MALA_TABLICA, sandbox_runner)

    assert stabilan is False
    assert razlog, "Gate mora reći ZAŠTO je odbio, inače je neupotrebljiv"


def test_odbija_spoj_bez_selektivnog_filtra(sandbox_runner):
    """Bez filtra `uses_index` ovisi o tome preferira li planer Seq Scan."""
    stabilan, _ = plan_is_stable(_NESTABILAN_SPOJ, sandbox_runner)

    assert stabilan is False


# ---------------------------------------------------------------------------
# Gate propušta ono što je izmjereno kao stabilno
# ---------------------------------------------------------------------------


def test_propusta_stabilne_kandidate(sandbox_runner):
    for upit in (
        _STABILAN_ORDERS,
        _STABILAN_ORDER_ITEMS,
        _STABILAN_LIMIT,
        _STABILAN_SPOJ,
    ):
        stabilan, razlog = plan_is_stable(upit, sandbox_runner)
        assert stabilan is True, f"{upit!r} odbijen: {razlog}"


def test_stabilan_spoj_zadrzava_nested_loop_pod_perturbacijom(sandbox_runner):
    """Potpis spoja s filtrom je isti pod svakom zastavicom iz gatea."""
    osnovni = plan_signature(sandbox_runner.explain(_STABILAN_SPOJ).node_types)

    for flag in STABILITY_FLAGS:
        pod_flagom = plan_signature(
            sandbox_runner.explain(_STABILAN_SPOJ, planner_flags=(flag,)).node_types
        )
        assert pod_flagom == osnovni, f"Potpis se promijenio pod {flag}"

    assert osnovni.join_methods == frozenset({"Nested Loop"})
    assert osnovni.uses_index is True


# ---------------------------------------------------------------------------
# Negativan smjer (poučak ERRATE #39) — gate mora moći i odbiti i propustiti
# ---------------------------------------------------------------------------


def test_gate_nije_uvijek_true(sandbox_runner):
    """Da gate uvijek vraća True, prva dva testa bi prošla iz krivog razloga."""
    odbijeni = [
        plan_is_stable(q, sandbox_runner)[0]
        for q in (_NESTABILAN_MALA_TABLICA, _NESTABILAN_SPOJ)
    ]
    propusteni = [
        plan_is_stable(q, sandbox_runner)[0] for q in (_STABILAN_ORDERS, _STABILAN_SPOJ)
    ]

    assert odbijeni == [False, False]
    assert propusteni == [True, True]


def test_neispravan_sql_je_nestabilan_a_ne_iznimka(sandbox_runner):
    stabilan, razlog = plan_is_stable("SELECT * FROM nepostojeca", sandbox_runner)

    assert stabilan is False
    assert "plan" in razlog.lower()
