"""TDD testovi za SandboxRunner.explain() — dohvat izvedbenog plana (M6).

🔴 `EXPLAIN` BEZ `ANALYZE`: plan se traži, upit se NE izvršava. Ovo je sigurnosna
invarijanta, ne optimizacija — `EXPLAIN ANALYZE` nad DML-om bi stvarno pisao.

Pokretanje: uv run pytest tests/test_sandbox_explain.py -v
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Sretni put — plan se dohvaća i čvorovi se izvlače
# ---------------------------------------------------------------------------


def test_explain_vraca_cvorove_plana(sandbox_runner):
    res = sandbox_runner.explain("SELECT id FROM customers WHERE id = 1")

    assert res.success is True
    assert res.error is None
    assert len(res.node_types) > 0


def test_explain_hvata_index_scan_na_pkey(sandbox_runner):
    """orders po primarnom ključu → Index Scan (izmjereno 2026-08-14)."""
    res = sandbox_runner.explain("SELECT * FROM orders WHERE id = 77")

    assert res.success is True
    assert "Index Scan" in res.node_types


def test_explain_hvata_seq_scan_na_maloj_tablici(sandbox_runner):
    """🔴 customers ima 200 redaka → planer bira Seq Scan IAKO indeks postoji.

    Ovo je mjerenje koje je srušilo tri zatečena M6 zadatka (ERRATA #66):
    Seq Scan 5.50 vs Index Scan 8.16 — planer je u pravu, zadatak je bio kriv.
    """
    res = sandbox_runner.explain(
        "SELECT id FROM customers WHERE email = 'skodamartina@example.org'"
    )

    assert res.success is True
    assert "Seq Scan" in res.node_types
    assert "Index Scan" not in res.node_types


def test_explain_razlikuje_anti_pattern_od_index_friendly(sandbox_runner):
    """Ista tablica, isti rezultat, RAZLIČIT plan — cijeli razlog postojanja M6 grane."""
    dobar = sandbox_runner.explain("SELECT id FROM orders WHERE customer_id = 42")
    losiji = sandbox_runner.explain("SELECT id FROM orders WHERE customer_id::text = '42'")

    assert "Bitmap Index Scan" in dobar.node_types
    assert "Bitmap Index Scan" not in losiji.node_types
    assert "Seq Scan" in losiji.node_types


def test_explain_hvata_metodu_spoja(sandbox_runner):
    """explain_plan koncept: filtar mijenja strategiju spoja (izmjereno)."""
    bez_filtra = sandbox_runner.explain(
        "SELECT o.id, oi.quantity FROM orders o JOIN order_items oi ON oi.order_id = o.id"
    )
    s_filtrom = sandbox_runner.explain(
        "SELECT o.id, oi.quantity FROM orders o JOIN order_items oi "
        "ON oi.order_id = o.id WHERE o.customer_id = 42"
    )

    assert "Hash Join" in bez_filtra.node_types
    assert "Nested Loop" in s_filtrom.node_types


def test_explain_izvlaci_cvorove_iz_UGNIJEZDENIH_planova(sandbox_runner):
    """Plan je stablo — čvorovi ispod `Plans` moraju ući, inače spoj vidi samo korijen."""
    res = sandbox_runner.explain(
        "SELECT o.id FROM orders o JOIN order_items oi ON oi.order_id = o.id"
    )

    # Hash Join je korijen; Seq Scan i Hash su mu djeca.
    assert "Hash Join" in res.node_types
    assert len(res.node_types) >= 3


# ---------------------------------------------------------------------------
# Greške i sigurnost
# ---------------------------------------------------------------------------


def test_explain_neispravan_sql_vraca_gresku_a_ne_podize_iznimku(sandbox_runner):
    res = sandbox_runner.explain("SELECT iz_nepostojece FROM nepostojeca_tablica")

    assert res.success is False
    assert res.sqlstate is not None
    assert res.node_types == []


def test_explain_NE_IZVRSAVA_upit_dml_pada_na_readonly(sandbox_runner):
    """🔴 Dokaz da nema ANALYZE: pod readonly rolom DML ne smije proći ni kao plan.

    Testirano u NEGATIVNOM smjeru (poučak ERRATE #39): da `explain` interno
    koristi `ANALYZE` ili readwrite rolu, ovaj bi test prošao umjesto pao.
    """
    res = sandbox_runner.explain(
        "INSERT INTO customers (first_name, last_name, email) "
        "VALUES ('a', 'b', 'plan-test@example.org')"
    )

    assert res.success is False, "EXPLAIN nad DML-om je prošao pod readonly rolom"


def test_explain_ne_ostavlja_trag_u_bazi(sandbox_runner):
    """Broj redaka prije i poslije — before/after dokaz, ne tvrdnja o shemi."""
    prije = sandbox_runner.execute("SELECT COUNT(*) AS n FROM customers")
    sandbox_runner.explain("SELECT * FROM customers")
    poslije = sandbox_runner.execute("SELECT COUNT(*) AS n FROM customers")

    assert prije.rows[0]["n"] == poslije.rows[0]["n"]
