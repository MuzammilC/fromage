import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Protocol

import yaml
from fromage_exam_definition import ExamDefinition, Item, ItemError, parse_item

from .cost import cost_usd
from .prompts import load_prompt

THEME_PATTERN = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")


class GenerationError(ValueError):
    """The request cannot be run (bad Part or theme)."""


@dataclass(frozen=True)
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int


class LLM(Protocol):
    def complete(self, system: str, user: str) -> LLMResult: ...


@dataclass
class GenerationResult:
    items: list[Item] = field(default_factory=list)
    paths: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


def generate_items(
    definition: ExamDefinition,
    part_key: str,
    theme: str,
    n: int,
    llm: LLM,
    *,
    out_dir: Path,
    model: str,
    today: date | None = None,
) -> GenerationResult:
    """Asks the LLM for `n` Items of a Part and theme, writing each valid one as a draft YAML file.

    Invalid LLM output is collected in `errors` and never written.
    """
    part = next((p for p in definition.parts if p.key == part_key), None)
    if part is None:
        raise GenerationError(
            f"{part_key!r} is not a Part of {definition.id}: {[p.key for p in definition.parts]}"
        )
    if part.item_type is None:
        raise GenerationError(f"Part {part_key!r} takes no Items")
    if not THEME_PATTERN.match(theme):
        raise GenerationError(f"theme {theme!r} must be lowercase snake_case, such as 'logement'")

    item_type = part.item_type.value
    prompt = load_prompt(item_type)
    today = today or date.today()
    ref = f"{definition.id}@{definition.version}"
    slug = (
        f"{definition.level.value.lower()}-{part_key.replace('_', '-')}-{theme.replace('_', '-')}"
    )
    user = (
        f"Niveau : {definition.level.value}\nPartie : {part_key}\nThème : {theme}\n"
        "Écris un nouvel Item original."
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    result = GenerationResult()
    for _ in range(n):
        response = llm.complete(prompt.text, user)
        result.input_tokens += response.input_tokens
        result.output_tokens += response.output_tokens
        result.cost_usd += cost_usd(model, response.input_tokens, response.output_tokens)
        try:
            fields = _parse_json_object(response.text)
            item_id = _next_id(out_dir, slug)
            data = {
                "type": item_type,
                "id": item_id,
                "exam_definition": ref,
                "part_key": part_key,
                "topics": [theme],
                "status": "draft",
                "version": 1,
                "generation": {
                    "model": model,
                    "prompt_version": prompt.version,
                    "date": today.isoformat(),
                },
                "teacher_reviewed": False,
                **{k: v for k, v in fields.items() if k not in _RESERVED},
            }
            item = parse_item(data, definition)
        except (ValueError, TypeError, ItemError) as error:
            result.errors.append(str(error))
            continue
        path = out_dir / f"{item_id}.yaml"
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=100),
            encoding="utf-8",
        )
        result.items.append(item)
        result.paths.append(path)
    return result


_RESERVED = {
    "type", "id", "exam_definition", "part_key", "topics", "status", "version",
    "generation", "teacher_reviewed",
}  # fmt: skip


def _parse_json_object(text: str) -> dict:
    stripped = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, re.DOTALL)
    try:
        value = json.loads(fenced.group(1) if fenced else stripped)
    except json.JSONDecodeError as error:
        raise ValueError(f"LLM output is not valid JSON: {error}") from error
    if not isinstance(value, dict):
        raise TypeError("LLM output is not a JSON object")
    return value


def _next_id(out_dir: Path, slug: str) -> str:
    taken = [
        int(m.group(1))
        for path in out_dir.glob(f"{slug}-*.yaml")
        if (m := re.fullmatch(rf"{re.escape(slug)}-(\d+)\.yaml", path.name))
    ]
    return f"{slug}-{max(taken, default=0) + 1:03d}"
