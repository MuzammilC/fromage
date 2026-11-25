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
    truncated: bool = False


class LLM(Protocol):
    def complete(
        self, system: str, user: str, metadata: dict[str, str] | None = None
    ) -> LLMResult: ...


@dataclass
class GenerationResult:
    items: list[Item] = field(default_factory=list)
    paths: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float | None = 0.0  # None when the model has no known price


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
    out_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "exam": ref,
        "part": part_key,
        "theme": theme,
        "prompt_version": prompt.version,
    }

    result = GenerationResult()
    for _ in range(n):
        user = _user_message(
            definition.level.value, part_key, theme, _existing_summaries(out_dir, slug)
        )
        try:
            response = llm.complete(prompt.text, user, metadata)
        except Exception as error:  # noqa: BLE001 - any API failure must still report the run so far
            result.errors.append(f"LLM call failed, stopping: {type(error).__name__}: {error}")
            break
        result.input_tokens += response.input_tokens
        result.output_tokens += response.output_tokens
        call_cost = cost_usd(model, response.input_tokens, response.output_tokens)
        result.cost_usd = (
            None if call_cost is None or result.cost_usd is None else result.cost_usd + call_cost
        )
        if response.truncated:
            result.errors.append("LLM output was cut off at the token limit")
            continue
        try:
            fields = _parse_json_object(response.text)
            metadata_fields = {
                "type": item_type,
                "id": "",
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
            }
            data = {
                **metadata_fields,
                **{k: v for k, v in fields.items() if k not in metadata_fields},
            }
            item, path = _write_new_item(out_dir, slug, data, definition)
        except (ValueError, TypeError, ItemError) as error:
            result.errors.append(str(error))
            continue
        result.items.append(item)
        result.paths.append(path)
    return result


def _user_message(level: str, part_key: str, theme: str, existing: list[str]) -> str:
    message = (
        f"Niveau : {level}\nPartie : {part_key}\nThème : {theme}\nÉcris un nouvel Item original."
    )
    if existing:
        avoid = "\n".join(f"- {text}" for text in existing)
        message += f"\nIl existe déjà ces Items. Choisis un angle clairement différent :\n{avoid}"
    return message


def _existing_summaries(out_dir: Path, slug: str) -> list[str]:
    """One line per existing Item of this Part and theme, so new ones can differ from them."""
    summaries = []
    for path in sorted(out_dir.glob(f"{slug}-*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        text = data.get("candidate_brief") or (data.get("questions") or [None])[0]
        if isinstance(text, str):
            summaries.append(" ".join(text.split()))
    return summaries


def _write_new_item(
    out_dir: Path, slug: str, data: dict, definition: ExamDefinition
) -> tuple[Item, Path]:
    """Validates and writes the Item under the next free id, never overwriting a file."""
    while True:
        item_id = _next_id(out_dir, slug)
        data["id"] = item_id
        item = parse_item(data, definition)
        path = out_dir / f"{item_id}.yaml"
        try:
            with path.open("x", encoding="utf-8") as file:
                yaml.safe_dump(data, file, allow_unicode=True, sort_keys=False, width=100)
        except FileExistsError:
            continue  # another run took this id since we looked; try the next one
        return item, path


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
