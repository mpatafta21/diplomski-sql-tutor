"""TDD testovi za plan-provjeru u `evaluate()` (M6, ERRATA #66).

Jezgra: **točni redci više nisu dovoljni** za `explain_plan` / `index_usage`.
Anti-pattern vraća identičan rezultat kao ispravno rješenje, pa ga samo plan
razlikuje.

🔴 Testovi ne ovise o sadržaju kataloga — grade `Task` u memoriji s vlastitim
`expected_query`. Zadaci 79–83 se mijenjaju u istoj grani, pa bi vezanje za njih
značilo da test mjeri katalog umjesto logike.

Pokretanje: uv run pytest tests/test_evaluation_plan.py -v
"""

from __future__ import annotations

import pytest

from agents.evaluation import evaluate
from app.db.models import Task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _plan_task(expected_query: str, expected_result: list[dict]) -> Task:
    """Task u memoriji — ne dira bazu, pa ne ovisi o stanju kataloga."""
    return Task(
        id=999_001,
        source_id="plan_test_synthetic",
        module_id=6,
        title="Sintetski M6 zadatak",
        description="Test",
        sandbox_schema="ecommerce_v1",
        expected_query=expected_query,
        expected_result=expected_result,
        difficulty=3,
        is_active=True,
    )


#: Isti rezultat, dva plana. `customer_id = 42` → Bitmap Index Scan;
#: `customer_id::text = '42'` → Seq Scan. Izmjereno 2026-08-14.
_INDEX_FRIENDLY = "SELECT id FROM orders WHERE customer_id = 42 ORDER BY id"
_ANTI_PATTERN = "SELECT id FROM orders WHERE customer_id::text = '42' ORDER BY id"


@pytest.fixture
def index_task(sandbox_runner):
    rows = sandbox_runner.execute(_INDEX_FRIENDLY).rows
    assert rows, "Fixture pretpostavlja da customer_id=42 ima narudžbe"
    return _plan_task(_INDEX_FRIENDLY, rows)


# ---------------------------------------------------------------------------
# 🔴 Jezgra nalaza — isti redci, različit plan
# ---------------------------------------------------------------------------


def test_referentno_rjesenje_prolazi(index_task, sandbox_runner):
    outcome = evaluate(
        index_task, _INDEX_FRIENDLY, sandbox_runner, primary_concept_code="index_usage"
    )

    assert outcome.is_correct is True
    assert outcome.error_type is None


def test_anti_pattern_daje_ISTE_RETKE_ali_pada_na_planu(index_task, sandbox_runner):
    """Cijeli razlog postojanja ove grane.

    Prvo se dokazuje da su redci doista identični (inače bi test prolazio iz
    krivog razloga — pao bi na row_mismatch, ne na planu).
    """
    redci_dobri = sandbox_runner.execute(_INDEX_FRIENDLY).rows
    redci_losi = sandbox_runner.execute(_ANTI_PATTERN).rows
    assert redci_dobri == redci_losi, "Preduvjet testa: rezultati moraju biti identični"

    outcome = evaluate(
        index_task, _ANTI_PATTERN, sandbox_runner, primary_concept_code="index_usage"
    )

    assert outcome.is_correct is False
    assert outcome.error_type == "plan_mismatch"
    assert "indeks" in outcome.detail


def test_bez_plan_provjere_bi_anti_pattern_PROSAO(index_task, sandbox_runner):
    """Kontrolni test: isti upit BEZ M6 koncepta prolazi kao točan.

    Dokazuje da plan-grana stvarno radi razliku — a ne da anti-pattern pada iz
    nekog nevezanog razloga. Ovo je ujedno dokaz zatečenog stanja: da se M6 samo
    aktivirao, ovako bi izgledala ocjena.
    """
    outcome = evaluate(
        index_task, _ANTI_PATTERN, sandbox_runner, primary_concept_code="select_basic"
    )

    assert outcome.is_correct is True, (
        "Bez plan-provjere anti-pattern je 'točan' — to je nalaz #66"
    )


# ---------------------------------------------------------------------------
# Opseg — M1–M5 se ne dira
# ---------------------------------------------------------------------------


def test_zadatak_izvan_M6_nikad_ne_ulazi_u_plan_granu(db_session, sandbox_runner):
    """Regresijska brana za 80 aktivnih zadataka."""
    task = (
        db_session.query(Task)
        .filter_by(source_id="agg_sum_avg_d3_manual_f239bc99")
        .first()
    )
    assert task is not None

    outcome = evaluate(
        task, task.expected_query, sandbox_runner, primary_concept_code="agg_sum_avg"
    )

    assert outcome.is_correct is True
    assert outcome.error_type is None


@pytest.mark.parametrize("koncept", ["explain_plan", "index_usage"])
def test_oba_M6_koncepta_idu_kroz_plan_granu(koncept, index_task, sandbox_runner):
    outcome = evaluate(
        index_task, _ANTI_PATTERN, sandbox_runner, primary_concept_code=koncept
    )
    assert outcome.error_type == "plan_mismatch"


# ---------------------------------------------------------------------------
# Rubni slučajevi
# ---------------------------------------------------------------------------


def test_predani_EXPLAIN_daje_uputu_a_ne_gresku_baze(index_task, sandbox_runner):
    """`EXPLAIN EXPLAIN …` bi bila sintaksna greška iz baze — student dobiva uputu."""
    outcome = evaluate(
        index_task,
        f"EXPLAIN {_INDEX_FRIENDLY}",
        sandbox_runner,
        primary_concept_code="index_usage",
    )

    # 🔴 VLASTITI tip, ne `plan_mismatch` (nalaz code reviewa): ovo je omaška u
    # obliku predaje, a `plan_mismatch` je konceptualni signal koji nosi
    # misconception i BKT kaznu. Zalijepljen EXPLAIN nije zabluda o indeksima.
    assert outcome.error_type == "explain_submitted"
    assert "EXPLAIN" in outcome.detail
    assert outcome.rows_returned == 0


def test_krivi_redci_javljaju_REDKE_a_ne_plan(index_task, sandbox_runner):
    """Redoslijed provjera: dok redci ne valjaju, plan nije tema."""
    outcome = evaluate(
        index_task,
        "SELECT id FROM orders WHERE customer_id = 43 ORDER BY id",
        sandbox_runner,
        primary_concept_code="index_usage",
    )

    assert outcome.is_correct is False
    assert outcome.error_type in {"row_mismatch", "empty_result"}


def test_detail_NE_SADRZI_referentni_upit(index_task, sandbox_runner):
    """🔴 `detail` ide u hint payload — ne smije nositi rješenje.

    Čuva istu invarijantu kao `test_expected_query_is_never_read`, ali na novom
    putu koji taj test ne pokriva.
    """
    outcome = evaluate(
        index_task, _ANTI_PATTERN, sandbox_runner, primary_concept_code="index_usage"
    )

    assert "customer_id = 42" not in outcome.detail
    assert "SELECT" not in outcome.detail.upper()


def test_detail_imenuje_PROPUSTENI_INDEKS_kad_oba_plana_koriste_indeks(
    sandbox_runner,
):
    """🔴 Nalaz code reviewa: `uses_index` je jednak, pa je poruka bila prazna.

    Ovo je točno oblik zadatka 83: referentni upit koristi ciljani indeks, a
    anti-pattern usputni `orders_pkey` koji mu u plan uvuče `ORDER BY id LIMIT 1`.
    Oba „koriste indeks", pa bez grane po `index_names` student dobije
    „plan izvedbe se razlikuje" — što ne kaže ništa upotrebljivo.
    """
    ref = (
        "SELECT id, customer_id, status FROM orders "
        "WHERE customer_id = 108 ORDER BY id LIMIT 1"
    )
    anti = (
        "SELECT id, customer_id, status FROM orders "
        "WHERE CAST(customer_id AS TEXT) = '108' ORDER BY id LIMIT 1"
    )
    ref_sig = sandbox_runner.explain(ref)
    anti_sig = sandbox_runner.explain(anti)
    assert "Index Scan" in anti_sig.node_types or "Bitmap Index Scan" in anti_sig.node_types
    assert set(ref_sig.index_names) != set(anti_sig.index_names), (
        "Preduvjet: planovi moraju koristiti RAZLIČITE indekse"
    )

    task = _plan_task(ref, sandbox_runner.execute(ref).rows)
    outcome = evaluate(task, anti, sandbox_runner, primary_concept_code="index_usage")

    assert outcome.error_type == "plan_mismatch"
    assert "idx_orders_customer" in outcome.detail, (
        f"detail mora imenovati propušteni indeks, a glasi: {outcome.detail!r}"
    )
