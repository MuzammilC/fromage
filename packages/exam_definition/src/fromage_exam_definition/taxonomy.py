from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .generated import ExamDefinition
from .taxonomy_generated import TopicTaxonomy
from .validation import _duplicates


class TaxonomyError(ValueError):
    """A Topic Taxonomy failed validation."""


def parse_taxonomy(data: Any, definition: ExamDefinition | None = None) -> TopicTaxonomy:
    """Validates a Topic Taxonomy against the schema, then the checks JSON Schema cannot express.

    Pass the Exam Definition to also check the Parts line up with it.
    """
    try:
        taxonomy = TopicTaxonomy.model_validate(data)
    except ValidationError as error:
        lines = [f"{'.'.join(str(part) for part in e['loc'])}: {e['msg']}" for e in error.errors()]
        raise TaxonomyError("Invalid Topic Taxonomy:\n" + "\n".join(lines)) from error

    problems: list[str] = []
    part_keys = [p.key.root for p in taxonomy.parts]
    problems += [f"Duplicate Part key {k!r}" for k in sorted(_duplicates(part_keys))]
    for part in taxonomy.parts:
        theme_keys = [theme.root.key.root for theme in part.themes]
        problems += [
            f"Duplicate theme key {k!r} in Part {part.key.root!r}"
            for k in sorted(_duplicates(theme_keys))
        ]
    if definition is not None:
        expected_ref = f"{definition.id}@{definition.version}"
        if taxonomy.exam_definition.root != expected_ref:
            problems.append(
                f"exam_definition {taxonomy.exam_definition.root!r} does not match {expected_ref!r}"
            )
        defined = [p.key for p in definition.parts]
        for key in part_keys:
            if key not in defined:
                problems.append(f"Part {key!r} is not a Part of {expected_ref!r}: {defined}")
        for key in defined:
            if key not in part_keys:
                problems.append(f"Part {key!r} of {expected_ref!r} has no themes")
    if problems:
        raise TaxonomyError("Invalid Topic Taxonomy:\n" + "\n".join(problems))
    return taxonomy


def load_taxonomy(path: str | Path, definition: ExamDefinition | None = None) -> TopicTaxonomy:
    path = Path(path)
    return parse_taxonomy(yaml.safe_load(path.read_text(encoding="utf-8")), definition)
