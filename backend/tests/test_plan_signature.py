"""TDD testovi za plan-presence evaluaciju (M6) — potpis izvedbenog plana.

Jezgra nalaza koji je ovo izazvao: rezultatska evaluacija NE MOŽE ocijeniti M6.
Anti-pattern (`LOWER(email) = …`, `customer_id::text = …`) vraća **bajt-identične
retke** kao index-friendly verzija, pa usporedba redaka oba proglasi točnima.
Razlika je isključivo u izvedbenom planu.

🔴 Potpis, a NE jednakost skupova čvorova. `Sort`, `Limit`, `Aggregate`, `Hash` i
`Bitmap Heap Scan` variraju s formulacijom i nisu predmet ovih koncepata, dok su
`Index Scan` i `Bitmap Index Scan` za cilj učenja ISTI ishod (indeks upotrijebljen).

Pokretanje: uv run pytest tests/test_plan_signature.py -v
"""

from __future__ import annotations

from agents.evaluation import PlanSignature, plan_signature

# ---------------------------------------------------------------------------
# plan_signature — čista funkcija nad popisom čvorova
# ---------------------------------------------------------------------------


def test_seq_scan_ne_koristi_indeks():
    sig = plan_signature(["Seq Scan"])
    assert sig.uses_index is False
    assert sig.join_methods == frozenset()


def test_sva_tri_index_cvora_znace_koristi_indeks():
    """Index Scan / Index Only Scan / Bitmap Index Scan → svi `uses_index=True`."""
    for node in ("Index Scan", "Index Only Scan", "Bitmap Index Scan"):
        assert plan_signature([node]).uses_index is True, node


def test_index_scan_i_bitmap_index_scan_daju_JEDNAK_potpis():
    """🔴 Jezgra dizajna: dva različita čvora, isti ishod učenja.

    Da se uspoređivao goli skup čvorova, student koji dobije Bitmap Index Scan
    ondje gdje referentni upit daje Index Scan bio bi proglašen netočnim — a
    isti je indeks upotrijebio, što je cijeli cilj koncepta.
    """
    a = plan_signature(["Index Scan", "Limit"], ["idx_orders_customer"])
    b = plan_signature(
        ["Bitmap Index Scan", "Bitmap Heap Scan"], ["idx_orders_customer"]
    )
    assert a == b


def test_isti_cvor_ali_DRUGI_indeks_daje_RAZLICIT_potpis():
    """🔴 Ovo je tvrdnja koja je propustila zadatak 83 (ERRATA #66).

    Referentni upit i CAST anti-pattern oba su davali `Index Scan` — ali
    referentni preko `idx_orders_customer`, a anti-pattern preko `orders_pkey`
    (koji mu je u plan uvukao `ORDER BY id LIMIT 1`). Bez imena indeksa potpisi
    su bili jednaki i anti-pattern je prolazio kao točan.
    """
    ciljani = plan_signature(["Index Scan"], ["idx_orders_customer"])
    usputni = plan_signature(["Index Scan"], ["orders_pkey"])

    assert ciljani.uses_index is usputni.uses_index is True
    assert ciljani != usputni, "uses_index nije dovoljno — bitno je KOJI indeks"


def test_kozmeticki_cvorovi_ne_ulaze_u_potpis():
    """Sort/Limit/Aggregate/Hash/Bitmap Heap Scan ne smiju mijenjati potpis."""
    goli = plan_signature(["Seq Scan"])
    okicen = plan_signature(
        ["Seq Scan", "Sort", "Limit", "Aggregate", "Hash", "Bitmap Heap Scan"]
    )
    assert goli == okicen


def test_metode_spoja_ulaze_u_potpis():
    """explain_plan se uči kroz strategiju spoja — ona MORA biti u potpisu."""
    hash_join = plan_signature(["Hash Join", "Hash", "Seq Scan"])
    nested = plan_signature(["Nested Loop", "Bitmap Index Scan", "Bitmap Heap Scan"])

    assert hash_join.join_methods == frozenset({"Hash Join"})
    assert nested.join_methods == frozenset({"Nested Loop"})
    assert hash_join != nested


def test_potpis_je_hashabilan_i_usporediv():
    """Koristi se kao vrijednost u usporedbi — mora biti frozen dataclass."""
    assert plan_signature(["Seq Scan"]) == PlanSignature(
        uses_index=False, index_names=frozenset(), join_methods=frozenset()
    )
    assert len({plan_signature(["Seq Scan"]), plan_signature(["Seq Scan"])}) == 1


def test_prazan_plan_daje_prazan_potpis():
    sig = plan_signature([])
    assert sig.uses_index is False
    assert sig.join_methods == frozenset()
