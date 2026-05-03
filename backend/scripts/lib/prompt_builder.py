"""PromptBuilder — sastavlja system + user prompt iz YAML config-a."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class PromptPair:
    system: str
    user: str


class ConceptNotFoundError(KeyError):
    """Bačeno kad concept_code YAML ne postoji."""


class PromptBuilder:
    def __init__(
        self,
        concepts_config_dir: Path,
        sandbox_context_path: Path,
        templates_dir: Path,
    ) -> None:
        self.concepts_dir = Path(concepts_config_dir)
        self.sandbox_path = Path(sandbox_context_path)
        self.templates_dir = Path(templates_dir)

        self._sandbox_ctx = yaml.safe_load(
            self.sandbox_path.read_text(encoding="utf-8")
        )
        self._system_template = (self.templates_dir / "system_static.md").read_text(
            encoding="utf-8"
        )
        self._user_template = (self.templates_dir / "user_template.md").read_text(
            encoding="utf-8"
        )

    def build(self, concept_code: str, difficulty: int) -> PromptPair:
        if not (1 <= difficulty <= 5):
            raise ValueError(f"difficulty must be 1-5, got {difficulty}")

        concept_path = self.concepts_dir / f"{concept_code}.yaml"
        if not concept_path.exists():
            raise ConceptNotFoundError(f"No config for concept '{concept_code}'")

        concept = yaml.safe_load(concept_path.read_text(encoding="utf-8"))

        return PromptPair(
            system=self._render_system(),
            user=self._render_user(concept, difficulty),
        )

    def _render_system(self) -> str:
        schema_block = self._format_schema_block(self._sandbox_ctx["tables"])
        invariants_block = "\n".join(
            f"- {x}" for x in self._sandbox_ctx["key_invariants"]
        )
        indexes_block = "\n".join(f"- {x}" for x in self._sandbox_ctx["indexes"])
        sample_rows_block = self._format_sample_rows_block(
            self._sandbox_ctx.get("sample_rows", {})
        )
        return (
            self._system_template
            .replace("{{schema_block}}", schema_block)
            .replace("{{sample_rows_block}}", sample_rows_block)
            .replace("{{invariants_block}}", invariants_block)
            .replace("{{indexes_block}}", indexes_block)
        )

    @staticmethod
    def _format_sample_rows_block(sample_rows: dict[str, list[dict]]) -> str:
        if not sample_rows:
            return "(no sample rows configured)"
        out: list[str] = []
        for tbl, rows in sample_rows.items():
            out.append(f"### {tbl} (sample {len(rows)} rows):")
            for r in rows:
                kvs = ", ".join(f"{k}={v!r}" for k, v in r.items())
                out.append(f"  - {{{kvs}}}")
        return "\n".join(out)

    def _render_user(self, concept: dict, difficulty: int) -> str:
        misconceptions = "\n".join(
            f"- [{m['priority']}] {m['code']}: {m['description']}"
            for m in concept.get("target_misconceptions", [])
        )
        domain_hints = "\n".join(f"- {x}" for x in concept.get("domain_hints", []))
        anti_patterns = "\n".join(f"- {x}" for x in concept.get("anti_patterns", []))
        few_shot = yaml.safe_dump(
            concept.get("few_shot_examples", []),
            allow_unicode=True,
            sort_keys=False,
        )

        if difficulty >= 4 and concept.get("required_for_high_difficulty"):
            high = "## Dodatni zahtjevi za težinu ≥ 4:\n\n" + "\n".join(
                f"- {x}" for x in concept["required_for_high_difficulty"]
            )
        else:
            high = ""

        return (
            self._user_template
            .replace("{{concept_code}}", concept["concept_code"])
            .replace("{{concept_name}}", concept["concept_name"])
            .replace("{{difficulty}}", str(difficulty))
            .replace("{{module_number}}", str(concept["module_number"]))
            .replace("{{module_name}}", concept["module_name"])
            .replace("{{misconceptions_block}}", misconceptions)
            .replace("{{domain_hints_block}}", domain_hints)
            .replace("{{anti_patterns_block}}", anti_patterns)
            .replace("{{few_shot_block}}", few_shot)
            .replace("{{high_difficulty_block}}", high)
        )

    @staticmethod
    def _format_schema_block(tables: list[dict]) -> str:
        out = []
        for t in tables:
            out.append(f"### {t['name']} ({t['row_count']} rows)")
            for c in t["columns"]:
                out.append(f"  - {c['name']}: {c['type']}")
        return "\n".join(out)
