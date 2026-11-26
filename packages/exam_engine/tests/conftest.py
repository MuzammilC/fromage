from pathlib import Path

import pytest
import yaml
from fromage_exam_definition import load_exam_definition, parse_item

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def a2():
    return load_exam_definition(ROOT / "content" / "exams" / "delf-a2-tp.yaml")


@pytest.fixture(scope="session")
def items(a2):
    return [
        parse_item(yaml.safe_load(path.read_text(encoding="utf-8")), a2)
        for path in sorted((ROOT / "content" / "items").glob("a2-*.yaml"))
    ]
