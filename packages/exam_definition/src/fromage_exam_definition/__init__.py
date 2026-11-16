"""Exam Definition and Item models and validation.

`generated.py` and `item_generated.py` are produced from `schema/*.schema.json`
(run `pnpm codegen`). `validation.py` and `item.py` add the checks JSON Schema cannot express.
"""

from .generated import ExamDefinition
from .item import ItemError, load_item, parse_item
from .item_generated import Item
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
    "Item",
    "ItemError",
    "load_exam_definition",
    "load_item",
    "parse_exam_definition",
    "parse_item",
]
