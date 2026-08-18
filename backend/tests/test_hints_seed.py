"""Katalog hintova (Faza 5.0, sekcija C) — 32 retka i njihov kriterij prihvaćanja.

Tri sloja provjere:
  1. seed daje točno 32 retka, svi s `concept_id`, i idempotentan je,
  2. §G5.4 — svaki tekst imenuje SQL konstrukt svog KONCEPTA i nije parafraza
     `ERROR_TEXT[error_type]` iz frontenda,
  3. §G2.3 (guard) — nijedan tekst ne propušta `expected_query` ni vrijednost iz
     `expected_result` ijednog zadatka tog koncepta.

🔴 Kriterij je mehanički. Hint koji ga ne prođe se NE popravlja tiho — pada test.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.db.hints_data import (
    BEGINNER_EXEC_CONCEPTS,
    CONCEPT_ERROR_TYPES,
    CONCEPT_TERMS,
    HINTS,
    TOP_CONCEPTS,
)
from app.db.models import Concept, Hint, Task, TaskConcept
from app.db.session import SessionLocal
from scripts.seed_hints import seed_hints

_FEEDBACK_TS = (
    Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "feedback.ts"
)

#: Udio sadržajnih riječi ERROR_TEXT-a koje smiju završiti u hintu. Preko toga je
#: hint parafraza generičke poruke, a ne pedagoški dodatak.
_PARAPHRASE_LIMIT = 0.5


@pytest.fixture(scope="module", autouse=True)
def seeded():
    """Seedaj katalog jednom za cijeli modul (idempotentno — ne briše ništa)."""
    with SessionLocal() as session:
        seed_hints(session)


def _error_text_map() -> dict[str, str]:
    """Pročitaj ERROR_TEXT iz frontenda — JEDAN izvor, bez kopiranja stringova.

    Kad se poruka u `feedback.ts` promijeni, kriterij se mijenja s njom.
    """
    src = _FEEDBACK_TS.read_text(encoding="utf-8")
    block = re.search(
        r"const ERROR_TEXT: Record<string, string> = \{(.*?)\n\}", src, re.DOTALL
    )
    assert block, f"ERROR_TEXT nije pronađen u {_FEEDBACK_TS}"
    pairs = re.findall(r"(\w+):\s*\n?\s*\"((?:[^\"\\]|\\.)*)\"", block.group(1))
    out = {k: json.loads(f'"{v}"') for k, v in pairs}
    missing = set(CONCEPT_ERROR_TYPES) - set(out)
    assert not missing, f"ERROR_TEXT nema tipove: {missing}"
    return out


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[\wÀ-ɏ]+", text.lower()))


def _content_words(text: str) -> set[str]:
    return {w for w in _tokens(text) if len(w) >= 4}


# ---------------------------------------------------------------------------
# 1. Oblik kataloga i idempotencija
# ---------------------------------------------------------------------------


def test_catalog_is_8x4_plus_beginner_exec() -> None:
    """8 koncepata x 4 tipa, PLUS 8 pocetnickih koncepata samo za `execution_error`.

    🔴 Drugi blok je posljedica ERRATE #72: `execution_error` od odluke
    2026-08-18 ne ide LLM-u, pa bez kataloga ondje hinta uopce ne bi bilo.
    """
    assert len(HINTS) == 40
    assert {(e, c) for e, c, _ in HINTS} == (
        {(e, c) for e in CONCEPT_ERROR_TYPES for c in TOP_CONCEPTS}
        | {("execution_error", c) for c in BEGINNER_EXEC_CONCEPTS}
    )


def test_row_mismatch_block_comes_first() -> None:
    """H3.2 — `row_mismatch` × koncept je prvih 8 redaka, prije svega ostalog."""
    assert [e for e, _, _ in HINTS[:8]] == ["row_mismatch"] * 8
    assert "row_mismatch" not in [e for e, _, _ in HINTS[8:]]


def test_seed_produces_all_rows_with_concept() -> None:
    with SessionLocal() as s:
        with_concept = s.scalar(
            select(func.count()).select_from(Hint).where(Hint.concept_id.isnot(None))
        )
        without = s.scalar(
            select(func.count()).select_from(Hint).where(Hint.concept_id.is_(None))
        )
    assert with_concept == 40
    assert without == 0


def test_seed_is_idempotent() -> None:
    """Drugo pokretanje ne dira nijedan redak i ne stvara nove."""
    with SessionLocal() as s:
        before = s.scalar(select(func.count()).select_from(Hint))
        counts = seed_hints(s)
        after = s.scalar(select(func.count()).select_from(Hint))
    assert counts == {"inserted": 0, "updated": 0, "unchanged": 40}
    assert before == after == 40


def test_no_duplicate_error_type_concept_pairs() -> None:
    """`hints` nema UNIQUE nad (error_type, concept_id) — jedinstvenost drži seeder."""
    with SessionLocal() as s:
        dupes = s.execute(
            select(Hint.error_type, Hint.concept_id, func.count())
            .group_by(Hint.error_type, Hint.concept_id)
            .having(func.count() > 1)
        ).all()
    assert dupes == [], f"Duplikati u hints: {dupes}"


# ---------------------------------------------------------------------------
# 2. §G5.4 — kriterij prihvaćanja
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("error_type", "concept", "hint_text"), HINTS)
def test_hint_names_a_concept_specific_construct(error_type, concept, hint_text) -> None:
    """Hint mora imenovati SQL konstrukt/pravilo vezano uz SVOJ koncept."""
    terms = CONCEPT_TERMS[concept]
    hit = [t for t in terms if t.lower() in hint_text.lower()]
    assert hit, (
        f"[{error_type}/{concept}] ne spominje nijedan pojam koncepta {terms}:\n"
        f"  {hint_text}"
    )


@pytest.mark.parametrize(("error_type", "concept", "hint_text"), HINTS)
def test_hint_is_not_a_paraphrase_of_generic_error_text(
    error_type, concept, hint_text
) -> None:
    """Hint ne smije prepričavati poruku koju student ionako već vidi."""
    generic = _content_words(_error_text_map()[error_type])
    overlap = generic & _tokens(hint_text)
    ratio = len(overlap) / len(generic)
    assert ratio < _PARAPHRASE_LIMIT, (
        f"[{error_type}/{concept}] preklapa se {ratio:.0%} s ERROR_TEXT "
        f"(riječi: {sorted(overlap)}):\n  {hint_text}"
    )


@pytest.mark.parametrize(("error_type", "concept", "hint_text"), HINTS)
def test_hint_is_croatian_prose_of_useful_length(error_type, concept, hint_text) -> None:
    """Prekratak hint ne navodi ni na što; predug se ne čita."""
    assert 80 <= len(hint_text) <= 320, (
        f"[{error_type}/{concept}] duljina {len(hint_text)} izvan [80, 320]"
    )


# ---------------------------------------------------------------------------
# 3. §G2.3 — guard: nijedan hint ne propušta rješenje
# ---------------------------------------------------------------------------


def _tasks_by_concept() -> dict[str, list[Task]]:
    with SessionLocal() as s:
        rows = s.execute(
            select(Concept.code, Task)
            .join(TaskConcept, TaskConcept.concept_id == Concept.id)
            .join(Task, Task.id == TaskConcept.task_id)
            .where(
                Concept.code.in_(TOP_CONCEPTS + BEGINNER_EXEC_CONCEPTS),
                TaskConcept.is_primary.is_(True),
            )
        ).all()
        out: dict[str, list[Task]] = {
            c: [] for c in TOP_CONCEPTS + BEGINNER_EXEC_CONCEPTS
        }
        for code, task in rows:
            out[code].append(task)
        return out


_TASKS = _tasks_by_concept()


@pytest.mark.parametrize(("error_type", "concept", "hint_text"), HINTS)
def test_hint_does_not_leak_expected_query(error_type, concept, hint_text) -> None:
    norm_hint = " ".join(hint_text.split()).lower()
    for task in _TASKS[concept]:
        norm_query = " ".join(task.expected_query.split()).lower()
        assert norm_query not in norm_hint, (
            f"[{error_type}/{concept}] sadrži expected_query zadatka {task.id}"
        )


@pytest.mark.parametrize(("error_type", "concept", "hint_text"), HINTS)
def test_hint_does_not_leak_expected_result_values(
    error_type, concept, hint_text
) -> None:
    """🔴 VRIJEDNOSTI redaka, ne ključevi.

    Izuzeće iz A1-dop-2: KLJUČEVI (`expected_result[0].keys()`) su oblik rješenja
    i pod selektivnim B+ smiju van; vrijednosti nikad. Kratke i brojčane vrijednosti
    uspoređuju se kao CIJELI tokeni — inače bi „vraća nulu" pao na vrijednosti 0.
    Token koji je i ključ i vrijednost tretira se kao vrijednost (fail-closed).
    """
    hint_tokens = _tokens(hint_text)
    lowered = hint_text.lower()
    for task in _TASKS[concept]:
        for row in task.expected_result or []:
            for value in row.values():
                if value is None:
                    continue
                sval = str(value).strip().lower()
                if not sval:
                    continue
                if len(sval) < 3 or sval.replace(".", "", 1).isdigit():
                    assert sval not in hint_tokens, (
                        f"[{error_type}/{concept}] sadrži vrijednost '{sval}' "
                        f"iz expected_result zadatka {task.id}"
                    )
                else:
                    assert sval not in lowered, (
                        f"[{error_type}/{concept}] sadrži vrijednost '{sval}' "
                        f"iz expected_result zadatka {task.id}"
                    )
