"""`uv run check-items`: checks every Item under content/items and writes a report."""

import argparse
import re
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fromage_exam_definition import (
    ExamDefinition,
    ExamDefinitionError,
    TaxonomyError,
    load_exam_definition,
    load_taxonomy,
)

from . import level
from .checks import (
    CheckResult,
    check_completeness,
    check_schema,
    check_topics,
    item_text,
    level_text,
)
from .overlap import DEFAULT_THRESHOLD, check_overlap, load_samples
from .report import ItemReport, render_report

EXAM_ID = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def _find_repo_root() -> Path | None:
    return next(
        (p for p in Path(__file__).resolve().parents if (p / "content" / "exams").is_dir()), None
    )


def main(argv: list[str] | None = None) -> int:
    root = _find_repo_root()
    parser = argparse.ArgumentParser(prog="check-items", description=__doc__)
    parser.add_argument("--items", type=Path, default=root and root / "content" / "items")
    parser.add_argument("--exams", type=Path, default=root and root / "content" / "exams")
    parser.add_argument(
        "--taxonomy",
        type=Path,
        default=root and root / "content" / "taxonomy",
        help="folder of Topic Taxonomy files (default: content/taxonomy)",
    )
    parser.add_argument(
        "--samples",
        type=Path,
        default=root and root / "content" / "fei-samples",
        help="local, gitignored folder of FEI sample text (default: content/fei-samples)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=root and root / "item-check-report.md",
        help="Markdown report",
    )
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--model", default=level.DEFAULT_MODEL, help="model for the level check")
    parser.add_argument(
        "--no-llm", action="store_true", help="skip the level and playability check"
    )
    args = parser.parse_args(argv)
    if (
        args.items is None
        or args.exams is None
        or args.taxonomy is None
        or args.report is None
        or args.samples is None
    ):
        print("Run check-items from a checkout of the repo.", file=sys.stderr)
        return 2
    if root:
        load_dotenv(root / ".env")

    warnings: list[str] = []
    samples = load_samples(args.samples)
    if samples is None:
        warnings.append(
            f"FEI overlap check skipped: no sample text in {args.samples} "
            "(expected in CI, where the folder is absent)"
        )
    checker = None
    if args.no_llm:
        warnings.append("Level and playability check skipped (--no-llm)")
    else:
        try:
            checker = level.AnthropicChecker(args.model)
        except Exception as error:  # noqa: BLE001 - no API key: the check is advisory anyway
            warnings.append(f"Level and playability check skipped: {error}")
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

    paths = sorted(args.items.glob("*.yaml"))
    if not paths:
        print(f"No Items found in {args.items}", file=sys.stderr)
        return 2
    definitions: dict[str, ExamDefinition | None] = {}
    taxonomies = _load_taxonomies(args.taxonomy)
    reports = [
        _check_file(path, args.exams, definitions, taxonomies, samples, args.threshold, checker)
        for path in paths
    ]

    args.report.write_text(render_report(reports, warnings), encoding="utf-8")
    failed = [r for r in reports if r.failed]
    print(f"{len(reports) - len(failed)}/{len(reports)} Items passed; report: {args.report}")
    for r in failed:
        for check in r.checks:
            if not check.passed:
                print(f"FAIL {r.path} [{check.name}]: {check.detail}", file=sys.stderr)
    return 1 if failed else 0


def _check_file(
    path: Path,
    exams_dir: Path,
    definitions: dict[str, ExamDefinition | None],
    taxonomies: dict[str, dict[str, set[str]]],
    samples: set[tuple[str, ...]] | None,
    threshold: float,
    checker: level.Checker | None,
) -> ItemReport:
    report = ItemReport(path=path.name)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        report.checks.append(_fail("schema", f"cannot read file: {error}"))
        return report
    definition = _definition_for(data, exams_dir, definitions)
    if definition is None:
        report.checks.append(_fail("schema", "Item does not name a loadable Exam Definition"))
        return report
    schema = check_schema(data, definition)
    report.checks.append(schema)
    if schema.item is None:
        return report
    text = item_text(schema.item)
    report.checks.append(check_completeness(schema.item))
    ref = f"{definition.id}@{definition.version}"
    report.checks.append(check_topics(schema.item, taxonomies.get(ref)))
    report.checks.append(check_overlap(text, samples, threshold))
    if checker is not None:
        report.level_asked = True
        report.level = level.check_level(level_text(schema.item), checker)
    return report


def _load_taxonomies(folder: Path) -> dict[str, dict[str, set[str]]]:
    """Theme keys per Part, for each Exam Definition (`id@version`) that has a Topic Taxonomy."""
    result: dict[str, dict[str, set[str]]] = {}
    for path in sorted(folder.glob("*.yaml")):
        try:
            taxonomy = load_taxonomy(path)
        except (OSError, TaxonomyError):
            continue
        result[taxonomy.exam_definition.root] = {
            part.key.root: {theme.root.key.root for theme in part.themes} for part in taxonomy.parts
        }
    return result


def _fail(name: str, detail: str) -> CheckResult:
    return CheckResult(name, False, detail)


def _definition_for(data, exams_dir: Path, cache: dict) -> ExamDefinition | None:
    ref = data.get("exam_definition") if isinstance(data, dict) else None
    if not isinstance(ref, str) or "@" not in ref:
        return None
    exam_id = ref.split("@")[0]
    if not EXAM_ID.fullmatch(exam_id):
        return None
    if exam_id not in cache:
        try:
            cache[exam_id] = load_exam_definition(exams_dir / f"{exam_id}.yaml")
        except (OSError, ExamDefinitionError):
            cache[exam_id] = None
    return cache[exam_id]


if __name__ == "__main__":
    sys.exit(main())
