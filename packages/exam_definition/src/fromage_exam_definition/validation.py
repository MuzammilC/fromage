from datetime import date
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .generated import ExamDefinition

GRID_TOTAL_POINTS = 25


class ExamDefinitionError(ValueError):
    """An Exam Definition failed validation."""


def parse_exam_definition(data: Any) -> ExamDefinition:
    try:
        definition = ExamDefinition.model_validate(data)
    except ValidationError as error:
        lines = [f"{'.'.join(str(part) for part in e['loc'])}: {e['msg']}" for e in error.errors()]
        raise ExamDefinitionError("Invalid Exam Definition:\n" + "\n".join(lines)) from error
    _check_semantics(definition)
    return definition


def load_exam_definition(path: str | Path) -> ExamDefinition:
    path = Path(path)
    return parse_exam_definition(yaml.safe_load(path.read_text(encoding="utf-8")))


def _check_semantics(definition: ExamDefinition) -> None:
    problems: list[str] = []

    part_keys = [part.key for part in definition.parts]
    problems += [f"Duplicate Part key {k!r}" for k in sorted(_duplicates(part_keys))]
    criterion_keys = [criterion.key for criterion in definition.grid]
    problems += [f"Duplicate Criterion key {k!r}" for k in sorted(_duplicates(criterion_keys))]

    for part in definition.parts:
        target = part.target_duration_seconds
        if target.min > target.max:
            problems.append(
                f"Part {part.key!r}: target duration min {target.min} is above max {target.max}"
            )

    covered: list[str] = []
    for period in definition.prep_periods or []:
        for covered_part in (p.root for p in period.parts):
            if covered_part not in part_keys:
                problems.append(
                    f"Prep Time covers Part {covered_part!r}, "
                    f"which is not one of the Parts: {part_keys}"
                )
            covered.append(covered_part)
    problems += [
        f"Part {k!r} is covered by more than one Prep Time" for k in sorted(_duplicates(covered))
    ]

    for criterion in definition.grid:
        scope = criterion.scope.root
        if scope.kind == "part" and scope.part not in part_keys:
            problems.append(
                f"Criterion {criterion.key!r} is scoped to Part {scope.part!r}, "
                f"which is not one of the Parts: {part_keys}"
            )
        points = list(criterion.band_points)
        if points[0] != 0 or points != sorted(points):
            problems.append(
                f"Criterion {criterion.key!r}: Band Points {points} must start at 0 "
                "and never decrease"
            )

    total = sum(_top_band_points(criterion.band_points) for criterion in definition.grid)
    if total != GRID_TOTAL_POINTS:
        problems.append(
            f"The Band Points of the top Band must add up to {GRID_TOTAL_POINTS}, got {total:g}"
        )

    if not is_real_date(definition.provenance.retrieved_on):
        problems.append(
            f"provenance.retrieved_on {definition.provenance.retrieved_on!r} is not a real date"
        )

    if problems:
        raise ExamDefinitionError("Invalid Exam Definition:\n" + "\n".join(problems))


def _top_band_points(band_points: list[float]) -> float:
    """Points for Band 3, the top Band."""
    return band_points[-1]


def is_real_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _duplicates(items: list[str]) -> set[str]:
    return {item for item in items if items.count(item) > 1}
