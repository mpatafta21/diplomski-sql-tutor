"""Guard §G2.3 + bijela lista §C nad `build_hint_payload` (Faza 5.1).

🔴 Ovo je jedini test koji stoji između studentovog upita i vanjske usluge.
Provjera je nad SADRŽAJEM serijaliziranog payloada, ne nad imenima polja — polje
se može preimenovati, sadržaj ne može pobjeći.

Izuzeće (A1-dop-2): za `wrong_columns` KLJUČEVI `expected_result[0]` smiju van jer
su oblik rješenja i pod B+ su dopušteni. VRIJEDNOSTI redaka nikad, ni za jedan tip.
Token koji je i ključ i vrijednost tretira se kao vrijednost — fail-closed.
"""

from __future__ import annotations

import json
import re

import pytest
from sqlalchemy import select

from agents.hint_payload import (
    CLASSIFICATION_ONLY_TYPES,
    DETAIL_SAFE_TYPES,
    build_hint_payload,
)
from app.db.models import Task
from app.db.session import SessionLocal

#: Svi dosežni `error_type`ovi iz `evaluation.py`.
SVI_TIPOVI = (
    "row_mismatch",
    "empty_result",
    "syntax_error",
    "unsupported_eval",
    "wrong_columns",
    "execution_error",
    "timeout",
)

#: Realni `detail` uzorci iz žive baze — uključujući ona dva koja CURE.
DETAIL_UZORCI = {
    "row_mismatch": "Row count mismatch: actual=30 vs expected=3",
    "empty_result": "Prazan rezultat, očekivano 3 redova",
    "syntax_error": "Prazan ili neprepoznatljiv upit",
    "unsupported_eval": "Koncept 'explain_plan' zahtijeva plan-presence evaluaciju",
    # 🔴 CURI: studentovi aliasi
    "wrong_columns": (
        "Stupci se razlikuju — dobiveni: ['category_id', 'product_count'], "
        "očekivani: ['broj_proizvoda', 'category_id']"
    ),
    # 🔴 CURI: doslovni redak upita
    "execution_error": (
        'column "county" does not exist\n'
        "LINE 1: SELECT id, name, county from suppliers limit 3;\n"
        "                          ^"
    ),
    "timeout": "Statement timeout after 5000ms: canceling statement",
}


def _aktivni_zadaci() -> list[Task]:
    with SessionLocal() as s:
        return list(s.scalars(select(Task).where(Task.is_active.is_(True))).all())


_ZADACI = _aktivni_zadaci()


def _tokeni(text: str) -> set[str]:
    return set(re.findall(r"[\wÀ-ɏ]+", text.lower()))


def _vrijednosti(task: Task) -> list[str]:
    """Sve string-oblike VRIJEDNOSTI iz `expected_result` (ne ključeve)."""
    out: list[str] = []
    for row in task.expected_result or []:
        if not isinstance(row, dict):
            continue
        for v in row.values():
            if v is None:
                continue
            s = str(v).strip().lower()
            if s:
                out.append(s)
    return out


def _blob(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False).lower()


# ---------------------------------------------------------------------------
# Bijela lista §C
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("error_type", sorted(DETAIL_SAFE_TYPES))
def test_safe_types_forward_detail(error_type) -> None:
    p = build_hint_payload(
        task=_ZADACI[0],
        error_type=error_type,
        detail=DETAIL_UZORCI[error_type],
        sqlstate=None,
        concept_code="group_by",
        p_l=0.4,
    )
    assert p["error_detail"] == DETAIL_UZORCI[error_type]


def test_wrong_columns_never_forwards_detail() -> None:
    """🔴 Pohranjeni `detail` nosi STUDENTOVE ALIASE — ne smije izaći ni u tragu."""
    task = next(t for t in _ZADACI if t.expected_result)
    p = build_hint_payload(
        task=task,
        error_type="wrong_columns",
        detail=DETAIL_UZORCI["wrong_columns"],
        sqlstate=None,
        concept_code="group_by",
        p_l=0.2,
    )
    assert "error_detail" not in p
    assert "product_count" not in _blob(p)  # studentov alias iz detaila
    assert p["expected_columns"] == sorted(task.expected_result[0].keys())


def test_execution_error_sends_sqlstate_not_detail() -> None:
    """🔴 `detail` ondje nosi doslovni redak upita; van ide samo šifra."""
    p = build_hint_payload(
        task=_ZADACI[0],
        error_type="execution_error",
        detail=DETAIL_UZORCI["execution_error"],
        sqlstate="42703",
        concept_code="multi_table_join",
        p_l=0.3,
    )
    assert "error_detail" not in p
    assert p["sqlstate"] == "42703"
    blob = _blob(p)
    # 🔴 `county` je STUDENTOV token iz njegovog upita — to je ono što ne smije van.
    # (Ranija verzija ovog testa tvrdila je i da `suppliers` ne smije izaći; ime
    # tablice legitimno stoji u opisu zadatka, pa je tvrdnja bila prestroga.)
    assert "county" not in blob
    assert "limit 3" not in blob


def test_timeout_sends_classification_only() -> None:
    p = build_hint_payload(
        task=_ZADACI[0],
        error_type="timeout",
        detail=DETAIL_UZORCI["timeout"],
        sqlstate="57014",
        concept_code="group_by",
        p_l=0.5,
    )
    assert "error_detail" not in p
    assert "sqlstate" not in p
    assert p["error_type"] == "timeout"


def test_unknown_error_type_is_rejected_by_default() -> None:
    """🔴 FAIL-CLOSED: nov tip u budućnosti ne smije tiho procuriti."""
    p = build_hint_payload(
        task=_ZADACI[0],
        error_type="neki_novi_tip_iz_2027",
        detail="tajna: SELECT * FROM users WHERE password = 'x'",
        sqlstate="42703",
        concept_code="group_by",
        p_l=0.5,
    )
    assert "error_detail" not in p
    assert "sqlstate" not in p
    assert "expected_columns" not in p
    assert "tajna" not in _blob(p)


def test_payload_fields_are_a_closed_set() -> None:
    """Dio A guarda: skup polja je zatvoren i provjerava se, ne pretpostavlja."""
    dopusteno = {
        "task_description",
        "concept",
        "mastery",
        "error_type",
        "error_detail",
        "expected_columns",
        "sqlstate",
    }
    for et in SVI_TIPOVI:
        p = build_hint_payload(
            task=_ZADACI[0],
            error_type=et,
            detail=DETAIL_UZORCI[et],
            sqlstate="42703",
            concept_code="group_by",
            p_l=0.5,
        )
        assert set(p) <= dopusteno, f"[{et}] nepoznata polja: {set(p) - dopusteno}"
        # Najviše JEDAN nosač signala greške.
        nosaci = {"error_detail", "expected_columns", "sqlstate"} & set(p)
        assert len(nosaci) <= 1, f"[{et}] više nosača odjednom: {nosaci}"


def test_expected_query_is_never_read() -> None:
    """Guard nad implementacijom: modul ne smije ni spominjati `expected_query`."""
    import inspect

    import agents.hint_payload as m

    src = inspect.getsource(m)
    kod = "\n".join(
        r for r in src.splitlines() if not r.lstrip().startswith("#")
    )
    assert "expected_query" not in kod.replace("`expected_query`", "")


# ---------------------------------------------------------------------------
# 🔴 Guard §G2.3 nad SVIM aktivnim zadacima × SVIM tipovima
# ---------------------------------------------------------------------------


def test_guard_no_expected_query_leaks_for_any_active_task() -> None:
    assert len(_ZADACI) >= 80, f"očekivano ≥80 aktivnih zadataka, nađeno {len(_ZADACI)}"
    for task in _ZADACI:
        norm_q = " ".join(task.expected_query.split()).lower()
        for et in SVI_TIPOVI:
            p = build_hint_payload(
                task=task,
                error_type=et,
                detail=DETAIL_UZORCI[et],
                sqlstate="42703",
                concept_code="group_by",
                p_l=0.4,
            )
            blob = " ".join(_blob(p).split())
            assert norm_q not in blob, f"task {task.id} / {et}: procurio expected_query"


#: Polja koja payload SINTETIZIRA — nad njima guard vrijedi bez izuzetka.
_SINTETIZIRANA = ("error_detail", "expected_columns", "sqlstate", "error_type", "mastery")


def test_guard_no_expected_result_values_in_synthesized_fields() -> None:
    """🔴 Jezgra guarda §G2.3: ništa što payload KONSTRUIRA ne nosi vrijednost retka.

    Opseg je sužen na sintetizirana polja, i to je odluka s razlogom (2026-08-12):

    - `task_description` je IZUZET jer je problemski tekst koji student ionako vidi.
      Izmjereno: 11 od 80 opisa sadrži vrijednost koja se pojavljuje i u
      `expected_result` („samousluga", „processing", „delivered"…). Guard nad njim
      bi padao na sadržaju koji ne otkriva ništa novo. Protiv `expected_query` se
      opis i dalje provjerava — v. test iznad.
    - Provjeravaju se TEKSTUALNE vrijednosti. Gole znamenke nisu provjerljive:
      `„expected=3"` je dopušten broj redaka, a `3` je i legitimna rezultatska
      vrijednost. Broj bez naziva stupca ne nosi rješenje, a strukturni dio guarda
      (zatvoren skup polja + najviše jedan nosač signala) sprečava uparivanje.

    Guard time NIJE oslabljen ondje gdje ima zube: nad sintetiziranim poljima danas
    je 0 pogodaka, pa svaka regresija pada.
    """
    pogodci: list[str] = []
    for task in _ZADACI:
        tekstualne = [
            v
            for v in _vrijednosti(task)
            if len(v) >= 3 and not v.replace(".", "", 1).isdigit()
        ]
        if not tekstualne:
            continue
        for et in SVI_TIPOVI:
            p = build_hint_payload(
                task=task,
                error_type=et,
                detail=DETAIL_UZORCI[et],
                sqlstate="42703",
                concept_code="group_by",
                p_l=0.4,
            )
            sint = {k: p[k] for k in _SINTETIZIRANA if k in p}
            blob = _blob(sint)
            for v in tekstualne:
                if v in blob:
                    pogodci.append(f"task {task.id} / {et}: vrijednost {v!r}")
    assert not pogodci, "Guard §G2.3 pao:\n  " + "\n  ".join(pogodci[:25])


def test_guard_covers_every_active_task_and_type() -> None:
    """Guard nije prazan hod: pokriva ≥80 zadataka × 7 tipova, i to se broji."""
    assert len(_ZADACI) >= 80, f"aktivnih zadataka {len(_ZADACI)}, očekivano ≥80"
    s_vrijednostima = sum(1 for t in _ZADACI if _vrijednosti(t))
    assert s_vrijednostima >= 70, (
        f"samo {s_vrijednostima} zadataka ima vrijednosti u expected_result — "
        "guard bi bio slabiji nego što izgleda"
    )


def test_mastery_is_a_coarse_band_never_a_number() -> None:
    """🔴 Sirovi `p_l` NE izlazi iz sustava — samo gruba oznaka."""
    for p_l, ocekivano in ((0.05, "nisko"), (0.29, "nisko"), (0.30, "srednje"),
                           (0.84, "srednje"), (0.85, "visoko"), (0.99, "visoko")):
        p = build_hint_payload(
            task=_ZADACI[0],
            error_type="row_mismatch",
            detail=DETAIL_UZORCI["row_mismatch"],
            sqlstate=None,
            concept_code="group_by",
            p_l=p_l,
        )
        assert p["mastery"] == ocekivano, f"p_l={p_l} → {p['mastery']!r}"
        assert str(p_l) not in _blob(p), f"sirovi p_l={p_l} procurio u payload"
