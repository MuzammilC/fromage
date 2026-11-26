import json

from fromage_item_checker.checks import CheckResult
from fromage_item_checker.level import LevelVerdict, check_level
from fromage_item_checker.report import ItemReport, render_report


class FakeLLM:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def complete(self, system, user):
        self.calls.append((system, user))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def test_level_parses_verdict():
    llm = FakeLLM(json.dumps({"a2_level": True, "playable": False, "comments": "Prix manquant"}))
    verdict = check_level("texte", llm)
    assert verdict == LevelVerdict(a2_level=True, playable=False, comments="Prix manquant")
    assert "texte" in llm.calls[0][1]


def test_level_accepts_fenced_json():
    llm = FakeLLM('```json\n{"a2_level": true, "playable": true, "comments": ""}\n```')
    assert check_level("t", llm).playable


def test_level_returns_none_on_garbage_or_failure():
    assert check_level("t", FakeLLM("not json")) is None
    assert check_level("t", FakeLLM(RuntimeError("boom"))) is None
    assert check_level("t", FakeLLM('{"a2_level": "yes"}')) is None


def test_report_is_readable_and_shows_advisory_separately():
    reports = [
        ItemReport(
            path="content/items/a.yaml",
            checks=[CheckResult("schema", True), CheckResult("fei-overlap", False, "5-gram x")],
            level=LevelVerdict(True, False, "Prix manquant"),
        ),
        ItemReport(
            path="content/items/b.yaml",
            checks=[CheckResult("fei-overlap", True, "skipped: no samples", skipped=True)],
            level=None,
        ),
    ]
    text = render_report(reports, warnings=["FEI samples folder absent"])
    assert "# Item check report" in text
    assert "1 of 2 Items failed" in text
    assert "`content/items/a.yaml`" in text
    assert "FAIL" in text and "5-gram x" in text
    assert "SKIPPED" in text
    assert "Prix manquant" in text
    assert "advisory" in text.lower()
    assert "FEI samples folder absent" in text
