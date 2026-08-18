"""Gate „tvrdnja iz opisa vs referentni plan" (varijanta O, pravilo PO KONCEPTU).

🔴 ZAŠTO POSTOJI. Gate diskriminacije (`manual_tasks_m6.py`) provjerava samo
zadatke koje je ta skripta autorirala — zadatak 81 je došao kroz
`import_dataset`, nema `anti_pattern`, i grana `anti is None` bi ga tiho
propustila kao „nije M6" (ERRATA #78). Ovaj gate ne treba katalog u kodu:
zadatak sam nosi svoju tvrdnju (isto načelo kao `m6-transverzalni-korak-0.md`
§C.2, ondje primijenjeno na `expected_query`).

Pravilo je PO KONCEPTU jer se koncepti ne poučavaju istim svojstvom plana:
  * `index_usage`  → indeks imenovan u `description` mora biti u `index_names`
  * `explain_plan` → `join_methods` referentnog plana ne smije biti prazan

🔴 Spojna grana je SLABIJA i to je svojstvo koncepta, ne rupa — v. wrapup §I.4:
pedagogija `explain_plan`-a je KONTRASTIVNA, opis mora imenovati OBA plana da bi
poučavao razliku, pa iz njega nije izvediva jednoznačna tvrdnja o referentnom.

🔴 TVRDO PRAVILO PROTIV ŠUTNJE: svaki `PLAN_CHECKED` zadatak koji ne potpada ni
pod jedno pravilo PADA s vlastitim `source_id`. Tiho preskakanje je točno mana
zbog koje varijanta B nije izabrana; gate ne smije imati istu.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, update

from app.db.models import Concept, Task, TaskConcept
from app.db.session import SessionLocal
from scripts import sweep_task_integrity as sweep


def _set_active(task_id: int, active: bool) -> None:
    with SessionLocal() as s:
        s.execute(update(Task).where(Task.id == task_id).values(is_active=active))
        s.commit()


def _sid(task_id: int) -> str:
    with SessionLocal() as s:
        return s.scalar(select(Task.source_id).where(Task.id == task_id))


def _failed_sids(rows: list[tuple[str, str]]) -> set[str]:
    return {sid for sid, _ in rows}


def test_gate_je_zelen_na_zatecenom_katalogu():
    """Kontrola: nad 5 aktivnih PLAN_CHECKED zadataka gate ne smije naći ništa."""
    assert sweep.check_plan_claim() == []


def test_a_zadatak_83_obecava_indeks_koji_plan_ne_koristi():
    """83: opis obećava `idx_orders_customer`, plan daje `orders_pkey`.

    Točno kvar zbog kojeg gate postoji — i on je pri autorstvu prošao, jer je
    zadatak tek kasnije prestao razlikovati (`ORDER BY id LIMIT 1` uvuče pkey).
    """
    sid = _sid(83)
    _set_active(83, True)
    try:
        pali = sweep.check_plan_claim()
    finally:
        _set_active(83, False)

    assert sid in _failed_sids(pali), f"83 mora pasti; palo: {_failed_sids(pali)}"
    razlog = next(r for s, r in pali if s == sid)
    assert "idx_orders_customer" in razlog and "orders_pkey" in razlog, razlog


@pytest.mark.parametrize("task_id", [79, 80])
def test_b_explain_plan_bez_ijedne_metode_spoja(task_id: int):
    """79/80 su jednotablični — `join_methods` je prazan, pa ne uče ništa o spoju."""
    sid = _sid(task_id)
    _set_active(task_id, True)
    try:
        pali = sweep.check_plan_claim()
    finally:
        _set_active(task_id, False)

    assert sid in _failed_sids(pali), f"{task_id} mora pasti; palo: {_failed_sids(pali)}"
    assert "join_methods" in next(r for s, r in pali if s == sid)


def test_c_index_usage_bez_imenovanog_indeksa_pada_sa_svojim_sid():
    """Opis koji ne imenuje indeks ne izgovara što poučava → PAD, ne šutnja."""
    sid = _sid(3782)
    with SessionLocal() as s:
        original = s.scalar(select(Task.description).where(Task.id == 3782))
    okrnjen = original.replace("idx_order_items_order", "tim indeksom")
    assert "idx_order_items_order" not in okrnjen

    with SessionLocal() as s:
        s.execute(update(Task).where(Task.id == 3782).values(description=okrnjen))
        s.commit()
    try:
        pali = sweep.check_plan_claim()
    finally:
        with SessionLocal() as s:
            s.execute(update(Task).where(Task.id == 3782).values(description=original))
            s.commit()

    assert sid in _failed_sids(pali), f"3782 mora pasti; palo: {_failed_sids(pali)}"
    assert "ne imenuje" in next(r for s, r in pali if s == sid)


def test_d_plan_checked_koncept_bez_pravila_pada(monkeypatch):
    """Nepoznat koncept u PLAN_CHECKED znači da gate ne zna što tvrditi.

    To MORA biti glasno: tiho preskakanje je mana zbog koje varijanta B nije
    izabrana (ERRATA #78).
    """
    monkeypatch.setattr(
        sweep, "PLAN_CHECKED_CONCEPTS", frozenset({"explain_plan", "index_usage", "column_alias"})
    )
    pali = sweep.check_plan_claim()

    with SessionLocal() as s:
        ca_sids = set(
            s.execute(
                select(Task.source_id)
                .join(TaskConcept, TaskConcept.task_id == Task.id)
                .join(Concept, Concept.id == TaskConcept.concept_id)
                .where(
                    TaskConcept.is_primary.is_(True),
                    Task.is_active.is_(True),
                    Concept.code == "column_alias",
                )
            ).scalars()
        )
    assert ca_sids, "fixture pretpostavlja aktivne column_alias zadatke"
    assert ca_sids <= _failed_sids(pali), (
        f"svaki column_alias zadatak mora pasti kao nepokriven; palo: {_failed_sids(pali)}"
    )
    assert "nema pravilo" in next(r for s, r in pali if s in ca_sids)
