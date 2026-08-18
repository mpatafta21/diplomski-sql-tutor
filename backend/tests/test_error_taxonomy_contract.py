"""🔴 Taksonomija grešaka je UGOVOR S PET POTROŠAČA — test ga zaključava.

**Povod:** ista greška se u ovoj grani ponovila TRI puta (wrapup §G2, nalazi 2, 3
i 5) — **novo ponašanje ugurano u zatečenu kategoriju umjesto novog imena**. A kad
je novo ime konačno uvedeno, posljedica je bila obrnuta: `plan_mismatch` nije bio
registriran u frontendu, pa je student na **ispravan SQL** vidio *„Ocjenjivanje
nije uspjelo — pokušaj ponovno predati rješenje."* Backend je bio točan cijelo
vrijeme; isporuka nije.

Nijedan od 819 testova to nije uhvatio, jer je svaki gledao **jedan** sloj.

Potrošači koje ovaj test provjerava:

| # | potrošač | što mora imati |
|---|---|---|
| 1 | `frontend/src/lib/feedback.ts` | unos u `ERROR_TEXT` |
| 2 | isti, prezentacija detalja | članstvo u TOČNO JEDNOM skupu (`TEXT`/`MONO`) |
| 3 | `agents/misconception_logic.py` | svjesna odluka: mehanički ili konceptualni |
| 4 | `agents/hint_payload.py` | TOČNO JEDNA politika payloada |
| 5 | `agents/hint_llm.py` | unos u `_TIP_OPIS` |

🔴 **Skup tipova se ČITA IZ IZVORA `evaluation.py`, ne prepisuje ovdje.** Popis
prepisan u test zastario bi tiho — a upravo je tiho zastarjevanje ono što ovaj
test treba spriječiti. Zato regex nad izvorom: novi `error_type=` bez registracije
obara test s imenom tog tipa u poruci.

🔴 **NOVA GRANICA (ERRATA #69):** ne smiju svi tipovi biti ishod pokušaja.
`plan_unavailable` je smetnja sustava — `EvaluatorAgent` na njega izlazi PRIJE
`persist_attempt`. Bez tvrdnje o toj granici mogao bi se sljedećom izmjenom tiho
vratiti u `attempts`, a s njim i BKT kazna za tuđi kvar.

Pokretanje: uv run pytest tests/test_error_taxonomy_contract.py -v
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from agents.evaluation import evaluate  # noqa: F401 — osigurava da modul postoji
from agents.hint_llm import _TIP_OPIS
from agents.hint_payload import (
    LLM_TYPES,
    UNDERDETERMINED_TYPES,
    CLASSIFICATION_ONLY_TYPES,
    DETAIL_SAFE_TYPES,
    RECONSTRUCT_COLUMNS_TYPE,
)
from agents.messages import ERROR_PLAN_UNAVAILABLE
from agents.misconception_logic import _MECHANICAL_ERRORS

_BACKEND = Path(__file__).resolve().parents[1]
_FEEDBACK_TS = _BACKEND.parent / "frontend" / "src" / "lib" / "feedback.ts"
_EVALUATION_PY = _BACKEND / "agents" / "evaluation.py"
_EVALUATOR_PY = _BACKEND / "agents" / "evaluator_agent.py"

#: Tipovi koji NE SMIJU biti ishod pokušaja — smetnja sustava, ne studentov rad.
#: 🔴 Jednočlana kategorija, i to je namjerno: `plan_unavailable` je jedini
#: `error_type` u kojem nije zakazao student.
NIJE_ISHOD_POKUSAJA = frozenset({ERROR_PLAN_UNAVAILABLE})

#: Naslijeđen tip: `evaluate()` ga više ne emitira (ERRATA #66), ali ga i dalje
#: sintetizira `hint_agent` na nedosežnoj grani, i nose ga povijesni retci.
#: Ostaje u ugovoru jer ga potrošači i dalje mogu vidjeti.
NASLIJEDJENI = frozenset({"unsupported_eval"})


def _emitirani_tipovi() -> set[str]:
    """Svi `error_type` koje `evaluate()` doista proizvodi — ČITANO IZ IZVORA."""
    izvor = _EVALUATION_PY.read_text(encoding="utf-8")
    # Hvata i `error_type="x"` (kwarg) i `error_type = "x"` (dodjela u grani).
    nadjeni = set(re.findall(r'error_type\s*=\s*"([a-z_]+)"', izvor))
    assert nadjeni, "regex nije našao nijedan error_type — izvor je promijenio oblik"
    return nadjeni


def _ts_skup(naziv: str) -> set[str]:
    """Izvuci članove `new Set([...])` ili `Record` literala iz feedback.ts."""
    ts = _FEEDBACK_TS.read_text(encoding="utf-8")
    if naziv == "ERROR_TEXT":
        blok = ts.split("const ERROR_TEXT", 1)[1].split("}", 1)[0]
        return set(re.findall(r"^\s*([a-z_]+):", blok, re.MULTILINE))
    blok = ts.split(f"const {naziv}", 1)[1].split("])", 1)[0]
    return set(re.findall(r'"([a-z_]+)"', blok))


SVI = sorted(_emitirani_tipovi() | NASLIJEDJENI)
ISHODI_POKUSAJA = sorted(t for t in SVI if t not in NIJE_ISHOD_POKUSAJA)


# ---------------------------------------------------------------------------
# Sam skup
# ---------------------------------------------------------------------------


def test_taksonomija_nije_prazna_i_sadrzi_poznate_clanove():
    """Brana protiv regexa koji tiho prestane hvatati (test bi inače bio prazan)."""
    assert len(SVI) >= 8, f"premalo tipova ({SVI}) — regex vjerojatno ne hvata"
    for ocekivan in ("row_mismatch", "plan_mismatch", "explain_submitted"):
        assert ocekivan in SVI, f"{ocekivan} nije nađen u izvoru"


# ---------------------------------------------------------------------------
# Nova granica: što SMIJE biti ishod pokušaja
# ---------------------------------------------------------------------------


def test_plan_unavailable_nije_ishod_pokusaja():
    """🔴 ERRATA #69 — smetnja sustava se NE zapisuje kao studentov rad.

    Tvrdi se nad IZVOROM evaluatora: rani izlaz mora stajati PRIJE
    `persist_attempt`. Test u `test_plan_unavailable_flow.py` mjeri posljedicu
    (0 redaka), ovaj čuva uzrok — da netko ne premjesti granu ispod perzistencije.
    """
    izvor = _EVALUATOR_PY.read_text(encoding="utf-8")
    # 🔴 Traži se POZIVNO MJESTO, ne spomen imena: `persist_attempt()` pojavljuje
    # se i u docstringu modula (D6 garancija), pa bi goli `find` uspoređivao
    # poziciju komentara — prva verzija ovog testa pala je upravo na tome.
    m_grana = re.search(r"^\s*if .*ERROR_PLAN_UNAVAILABLE", izvor, re.MULTILINE)
    m_persist = re.search(r"^\s*attempt_id = persist_attempt\(", izvor, re.MULTILINE)
    assert m_grana, "evaluator više ne grana na plan_unavailable"
    assert m_persist, "poziv persist_attempt više ne postoji u očekivanom obliku"
    assert m_grana.start() < m_persist.start(), (
        "rani izlaz za plan_unavailable je ISPOD persist_attempt — smetnja bi "
        "opet postala pokušaj"
    )


@pytest.mark.parametrize("tip", sorted(NIJE_ISHOD_POKUSAJA))
def test_tip_koji_nije_ishod_ne_treba_biti_u_UI_sloju(tip):
    """Ne smije se registrirati kao ishod — do UI-ja feedbacka ne dolazi.

    Njegovu poruku nosi `lib/submit.ts` (503), ne `lib/feedback.ts`.
    """
    assert tip not in _ts_skup("ERROR_TEXT"), (
        f"{tip} je u ERROR_TEXT — sugerira da je ishod pokušaja, a nije"
    )


# ---------------------------------------------------------------------------
# Pet potrošača × svaki ishod pokušaja
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tip", ISHODI_POKUSAJA)
def test_potrosac_1_frontend_ima_poruku(tip):
    """Bez unosa student vidi „Ocjenjivanje nije uspjelo" — nalaz koji je ovo izazvao."""
    assert tip in _ts_skup("ERROR_TEXT"), (
        f"`{tip}` nema poruku u feedback.ts → student dobiva generički fallback "
        "koji tvrdi kvar sustava"
    )


@pytest.mark.parametrize("tip", ISHODI_POKUSAJA)
def test_potrosac_2_frontend_zna_prikazati_detail(tip):
    """TOČNO JEDAN skup: `text` (pedagoški) ili `mono` (tehnički ispis)."""
    text_set = _ts_skup("TEXT_DETAIL_TYPES")
    mono_set = _ts_skup("MONO_DETAIL_TYPES")
    pripadnost = (tip in text_set) + (tip in mono_set)
    assert pripadnost == 1, (
        f"`{tip}` je u {pripadnost} skupa prezentacije detalja (treba točno 1) — "
        f"text={tip in text_set}, mono={tip in mono_set}"
    )


@pytest.mark.parametrize("tip", ISHODI_POKUSAJA)
def test_potrosac_3_misconception_ima_svjesnu_odluku(tip):
    """Članstvo u `_MECHANICAL_ERRORS` je odluka: omaška ili zabluda.

    🔴 Izostanak NIJE propust — znači „konceptualni, bilježi se". Zato se tvrdi
    da je tip svrstan u jednu od dvije kategorije, a poimence se čuvaju samo one
    gdje bi kriva strana imala posljedicu po studenta.
    """
    konceptualni = {"row_mismatch", "empty_result", "wrong_columns", "plan_mismatch"}
    if tip in konceptualni:
        assert tip not in _MECHANICAL_ERRORS, (
            f"`{tip}` je konceptualna greška — mora se bilježiti kao misconception"
        )
    else:
        assert tip in _MECHANICAL_ERRORS, (
            f"`{tip}` je mehanička greška — ne smije studentu upisati zabludu"
        )


@pytest.mark.parametrize("tip", ISHODI_POKUSAJA)
def test_potrosac_4_hint_payload_ima_tocno_jednu_politiku(tip):
    """Bijela lista po tipu: SAFE / REKONSTRUKCIJA / SAMO-KLASIFIKACIJA."""
    politike = (
        (tip in DETAIL_SAFE_TYPES)
        + (tip == RECONSTRUCT_COLUMNS_TYPE)
        + (tip in CLASSIFICATION_ONLY_TYPES)
    )
    assert politike == 1, (
        f"`{tip}` ima {politike} politike payloada (treba točno 1) — nula znači da "
        "tiho pada u default granu, dakle odluka nije donesena nego zatečena"
    )


@pytest.mark.parametrize("tip", ISHODI_POKUSAJA)
def test_potrosac_5_hint_llm_ima_citljiv_opis(tip):
    """Bez opisa model dobiva goli kod i nagađa što znači."""
    assert tip in _TIP_OPIS, (
        f"`{tip}` nema opis u hint_llm._TIP_OPIS → modelu ide sirovi kod"
    )


@pytest.mark.parametrize("tip", ISHODI_POKUSAJA)
def test_potrosac_6_izvor_hinta_je_odlucen(tip):
    """PRAVILO (ERRATA #72): svaki tip je u TOČNO JEDNOJ grani — LLM ili fallback.

    LLM se poziva samo kad klasifikacija i payload ZAJEDNO određuju dijagnozu.
    Nula grana znači da tip tiho pada u default (LLM), dakle odluka o njemu nije
    donesena nego zatečena — isti hazard koji `test_potrosac_4` hvata za payload.
    """
    grane = (tip in LLM_TYPES) + (tip in UNDERDETERMINED_TYPES)
    assert grane == 1, (
        f"`{tip}` je u {grane} grana izvora hinta (treba točno 1): "
        f"LLM_TYPES={tip in LLM_TYPES}, UNDERDETERMINED_TYPES="
        f"{tip in UNDERDETERMINED_TYPES}"
    )


def test_grane_izvora_particioniraju_taksonomiju():
    """Unija je cjelina, presjek prazan — bez toga bi partikularni test lagao."""
    assert not (LLM_TYPES & UNDERDETERMINED_TYPES), "tip u obje grane"
    assert LLM_TYPES | UNDERDETERMINED_TYPES == set(ISHODI_POKUSAJA), (
        "grane ne pokrivaju točno taksonomiju ishoda pokušaja; višak/manjak: "
        f"{(LLM_TYPES | UNDERDETERMINED_TYPES) ^ set(ISHODI_POKUSAJA)}"
    )
