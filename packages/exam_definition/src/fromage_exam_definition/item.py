from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .generated import ExamDefinition
from .item_generated import Item
from .validation import is_real_date


class ItemError(ValueError):
    """An Item failed validation."""


def parse_item(data: Any, definition: ExamDefinition | None = None) -> Item:
    """Validates an Item against the schema, then the checks JSON Schema cannot express.

    Pass the Exam Definition the Item belongs to, to also check that the Item points at it
    and names one of its Parts.
    """
    try:
        item = Item.model_validate(data)
    except ValidationError as error:
        lines = [f"{'.'.join(str(part) for part in e['loc'])}: {e['msg']}" for e in error.errors()]
        raise ItemError("Invalid Item:\n" + "\n".join(lines)) from error

    problems: list[str] = []
    variant = item.root
    if not is_real_date(variant.generation.date):
        problems.append(f"generation.date {variant.generation.date!r} is not a real date")
    if definition is not None:
        expected_ref = f"{definition.id}@{definition.version}"
        if variant.exam_definition.root != expected_ref:
            problems.append(
                f"exam_definition {variant.exam_definition.root!r} does not match "
                f"the Exam Definition it is checked against, {expected_ref!r}"
            )
        part_keys = [part.key for part in definition.parts]
        part = next((p for p in definition.parts if p.key == variant.part_key.root), None)
        if part is None:
            problems.append(
                f"part_key {variant.part_key.root!r} is not a Part of {expected_ref!r}: {part_keys}"
            )
        elif part.item_type is not None and part.item_type.value != variant.type:
            problems.append(
                f"Item type {variant.type!r} does not fit Part {part.key!r}, "
                f"which takes {part.item_type.value!r} Items"
            )
    if problems:
        raise ItemError("Invalid Item:\n" + "\n".join(problems))
    return item


def load_item(path: str | Path, definition: ExamDefinition | None = None) -> Item:
    path = Path(path)
    return parse_item(yaml.safe_load(path.read_text(encoding="utf-8")), definition)
