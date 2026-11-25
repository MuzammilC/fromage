"""Version-controlled generation prompts, one file per Item type: `prompts/<type>.v<N>.md`.

The highest version present is used, and its `<type>-v<N>` name is stamped into every Item.
"""

import re
from dataclasses import dataclass
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass(frozen=True)
class Prompt:
    version: str
    text: str


def load_prompt(item_type: str) -> Prompt:
    versions = {}
    for path in PROMPTS_DIR.glob(f"{item_type}.v*.md"):
        match = re.fullmatch(rf"{re.escape(item_type)}\.v(\d+)\.md", path.name)
        if match:
            versions[int(match.group(1))] = path
    if not versions:
        raise FileNotFoundError(f"No generation prompt for Item type {item_type!r}")
    latest = max(versions)
    return Prompt(f"{item_type}-v{latest}", versions[latest].read_text(encoding="utf-8").strip())
