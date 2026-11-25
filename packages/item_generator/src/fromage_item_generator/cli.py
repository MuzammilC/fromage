"""`uv run gen-items --exam delf-a2-tp --part monologue_suivi --theme logement --n 3`"""

import argparse
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from fromage_exam_definition import ExamDefinitionError, load_exam_definition

from .generator import GenerationError, generate_items

EXAM_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _find_repo_root() -> Path | None:
    return next(
        (p for p in Path(__file__).resolve().parents if (p / "content" / "exams").is_dir()), None
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gen-items", description=__doc__)
    parser.add_argument("--exam", required=True, help="Exam Definition id, e.g. delf-a2-tp")
    parser.add_argument("--part", required=True, help="Part key, e.g. monologue_suivi")
    parser.add_argument("--theme", required=True, help="Topic Taxonomy theme, e.g. logement")
    parser.add_argument("--n", type=int, default=1, help="number of Items to generate")
    parser.add_argument("--model", default=None, help="model id (default: Claude Sonnet 5.5)")
    parser.add_argument("--out", type=Path, default=None, help="default: <repo>/content/items")
    args = parser.parse_args(argv)
    if args.n < 1:
        parser.error("--n must be at least 1")
    if not EXAM_ID.match(args.exam):
        parser.error(f"--exam {args.exam!r} is not an Exam Definition id like delf-a2-tp")
    repo_root = _find_repo_root()
    if repo_root is None:
        print(
            "Run gen-items from a checkout of the repo (content/exams not found).", file=sys.stderr
        )
        return 2

    exam_path = repo_root / "content" / "exams" / f"{args.exam}.yaml"
    try:
        definition = load_exam_definition(exam_path)
    except (OSError, ExamDefinitionError) as error:
        print(f"Cannot load Exam Definition {args.exam!r}: {error}", file=sys.stderr)
        return 2

    load_dotenv(repo_root / ".env")  # ANTHROPIC_API_KEY and LANGFUSE_* may also come from the shell

    from .llm import DEFAULT_MODEL, AnthropicLLM  # imported late: needs keys from the env

    model = args.model or DEFAULT_MODEL
    llm = AnthropicLLM(model)
    try:
        result = generate_items(
            definition,
            args.part,
            args.theme,
            args.n,
            llm,
            out_dir=args.out or repo_root / "content" / "items",
            model=model,
        )
    except GenerationError as error:
        print(error, file=sys.stderr)
        return 2
    finally:
        llm.flush()

    for path in result.paths:
        print(f"wrote {path}")
    for error in result.errors:
        print(f"skipped invalid Item: {error}", file=sys.stderr)
    cost = (
        "unknown (no price for this model)"
        if result.cost_usd is None
        else f"${result.cost_usd:.4f}"
    )
    print(
        f"{len(result.items)}/{args.n} Items, {result.input_tokens} in + "
        f"{result.output_tokens} out tokens, cost {cost}"
    )
    return 0 if len(result.items) == args.n else 1


if __name__ == "__main__":
    sys.exit(main())
