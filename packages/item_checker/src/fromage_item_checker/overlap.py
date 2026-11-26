import re
import unicodedata
from pathlib import Path

from .checks import CheckResult

N = 5
DEFAULT_THRESHOLD = 0.05  # share of the Item's 5-grams found in the FEI samples


def normalise(text: str) -> list[str]:
    decomposed = unicodedata.normalize("NFD", text.lower())
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", stripped)


def ngrams(text: str, n: int = N) -> set[tuple[str, ...]]:
    """The n-grams of each line, never spanning two lines (two fields of an Item)."""
    grams: set[tuple[str, ...]] = set()
    for line in text.splitlines():
        words = normalise(line)
        grams |= {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}
    return grams


def load_samples(folder: Path) -> set[tuple[str, ...]] | None:
    """The 5-grams of every text file under `folder`, or None when it is absent or has none."""
    if not folder.is_dir():
        return None
    grams: set[tuple[str, ...]] = set()
    found = False
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}:
            found = True
            grams |= ngrams(path.read_text(encoding="utf-8", errors="ignore"))
    return grams if found else None


def check_overlap(
    text: str, samples: set[tuple[str, ...]] | None, threshold: float = DEFAULT_THRESHOLD
) -> CheckResult:
    if samples is None:
        return CheckResult("fei-overlap", True, "no FEI samples available", skipped=True)
    grams = ngrams(text)
    shared = grams & samples
    share = len(shared) / len(grams) if grams else 0.0
    if share > threshold:
        example = " ".join(min(shared))
        return CheckResult(
            "fei-overlap",
            False,
            f"{len(shared)} of {len(grams)} 5-grams ({share:.0%}) appear in FEI samples, "
            f"above {threshold:.0%}; for example: “{example}”",
        )
    return CheckResult("fei-overlap", True, f"{len(shared)} of {len(grams)} 5-grams shared")
