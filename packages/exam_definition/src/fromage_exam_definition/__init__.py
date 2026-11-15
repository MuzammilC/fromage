"""Exam Definition models and validation.

`generated.py` is produced from `schema/exam-definition.schema.json` (run `pnpm codegen`).
`validation.py` adds the checks JSON Schema cannot express.
"""

from .generated import ExamDefinition
from .validation import (
    GRID_TOTAL_POINTS,
    ExamDefinitionError,
    load_exam_definition,
    parse_exam_definition,
)

__all__ = [
    "GRID_TOTAL_POINTS",
    "ExamDefinition",
    "ExamDefinitionError",
    "load_exam_definition",
    "parse_exam_definition",
]
