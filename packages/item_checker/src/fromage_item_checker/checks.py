import re
from dataclasses import dataclass

import yaml
from fromage_exam_definition import ExamDefinition, Item, ItemError, parse_item


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    skipped: bool = False


@dataclass(frozen=True)
class SchemaResult(CheckResult):
    item: Item | None = None


def check_schema(data: object, definition: ExamDefinition) -> SchemaResult:
    """The Item validates against the schema and fits its Exam Definition and Part."""
    try:
        item = parse_item(data, definition)
    except ItemError as error:
        return SchemaResult("schema", False, str(error))
    return SchemaResult("schema", True, item=item)


# A figure: a digit, or a time/day word that carries a time without a digit.
_FIGURE = re.compile(
    r"\d|\b(midi|minuit|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche|gratuit)\b",
    re.IGNORECASE,
)


def check_completeness(item: Item) -> CheckResult:
    """An interaction situation carries the figures (prices, times) the Examiner needs to answer."""
    variant = item.root
    if variant.type != "interaction_situation":
        return CheckResult("completeness", True, "not an interaction situation", skipped=True)
    data = variant.examiner_only_data
    if not data:
        return CheckResult("completeness", False, "examiner_only_data is empty")
    blank = [key for key, value in data.items() if _is_blank(value)]
    if blank:
        return CheckResult("completeness", False, f"examiner_only_data has blank values: {blank}")
    if not any(_FIGURE.search(text) for text in _leaf_strings(data)):
        return CheckResult(
            "completeness", False, "examiner_only_data has no price, time or other figure"
        )
    return CheckResult("completeness", True)


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (dict, list)):
        return not value or any(_is_blank(v) for v in _members(value))
    return False


def _members(value: dict | list) -> list:
    return list(value.values()) if isinstance(value, dict) else value


def _leaf_strings(value: object) -> list[str]:
    if isinstance(value, (dict, list)):
        return [text for child in _members(value) for text in _leaf_strings(child)]
    return [str(value)]


def _content(item: Item) -> dict:
    return item.root.model_dump(
        mode="json",
        exclude={"type", "id", "exam_definition", "part_key", "topics", "status", "version"}
        | {"generation", "teacher_reviewed", "register"},
    )


def item_text(item: Item) -> str:
    """All the French text of an Item (not its metadata), one field per line."""
    return "\n".join(_leaf_strings(_content(item)))


def level_text(item: Item) -> str:
    """The Item's content with its field names, so the level check can tell what each value means."""
    return yaml.safe_dump(_content(item), allow_unicode=True, sort_keys=False)


def check_topics(item: Item, themes: dict[str, set[str]] | None) -> CheckResult:
    """Every topic is a theme of the Item's Part in the Topic Taxonomy."""
    if themes is None:
        return CheckResult(
            "topics", True, "no Topic Taxonomy for this Exam Definition", skipped=True
        )
    variant = item.root
    part = getattr(variant.part_key, "root", variant.part_key)
    topics = [getattr(t, "root", t) for t in getattr(variant.topics, "root", variant.topics)]
    unknown = [t for t in topics if t not in themes.get(part, set())]
    if unknown:
        return CheckResult("topics", False, f"not in the Topic Taxonomy for {part}: {unknown}")
    return CheckResult("topics", True)
