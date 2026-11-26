from pathlib import Path

import yaml
from fromage_item_checker import cli, level

ROOT = Path(__file__).resolve().parents[3]

ITEM = {
    "type": "monologue_subject",
    "id": "a2-monologue-suivi-logement-001",
    "exam_definition": "delf-a2-tp@1",
    "part_key": "monologue_suivi",
    "topics": ["housing"],
    "status": "draft",
    "version": 1,
    "generation": {"model": "m", "prompt_version": "p-v1", "date": "2026-11-24"},
    "teacher_reviewed": False,
    "candidate_brief": "Vous parlez de votre logement idéal.",
    "suggested_angles": ["Où ?", "Comment ?"],
}


def write(directory: Path, name: str, data: dict) -> None:
    (directory / f"{name}.yaml").write_text(yaml.safe_dump(data, allow_unicode=True))


def run(items, samples, report, *extra):
    return cli.main(
        [
            "--items", str(items),
            "--samples", str(samples),
            "--report", str(report),
            "--exams", str(ROOT / "content" / "exams"),
            "--no-llm",
            *extra,
        ]
    )  # fmt: skip


def test_passes_and_warns_when_samples_absent(tmp_path, capsys):
    write(tmp_path, "ok", ITEM)
    report = tmp_path / "report.md"
    assert run(tmp_path, tmp_path / "absent", report) == 0
    assert "warning" in capsys.readouterr().err.lower()
    assert "SKIPPED" in report.read_text()


def test_fails_on_invalid_item(tmp_path):
    write(tmp_path, "bad", {**ITEM, "status": "nope"})
    assert run(tmp_path, tmp_path / "absent", tmp_path / "r.md") == 1


def test_fails_on_copied_fei_text(tmp_path):
    items, samples = tmp_path / "items", tmp_path / "samples"
    items.mkdir()
    samples.mkdir()
    write(items, "copied", ITEM)
    (samples / "fei.txt").write_text("Vous parlez de votre logement idéal. Autre phrase.")
    assert run(items, samples, tmp_path / "r.md") == 1
    assert "fei-overlap" in (tmp_path / "r.md").read_text()


def test_level_check_is_advisory(tmp_path, monkeypatch):
    write(tmp_path, "ok", ITEM)

    class FakeHaiku:
        def __init__(self, model):
            pass

        def complete(self, system, user):
            return '{"a2_level": false, "playable": false, "comments": "Trop dur"}'

    monkeypatch.setattr(level, "AnthropicChecker", FakeHaiku)
    report = tmp_path / "r.md"
    code = cli.main(
        ["--items", str(tmp_path), "--samples", str(tmp_path / "x"), "--report", str(report),
         "--exams", str(ROOT / "content" / "exams")]
    )  # fmt: skip
    assert code == 0
    assert "Trop dur" in report.read_text()


def test_fails_when_no_items(tmp_path):
    assert run(tmp_path, tmp_path / "absent", tmp_path / "r.md") == 2


def test_report_says_when_level_check_gave_no_answer(tmp_path, monkeypatch):
    write(tmp_path, "ok", ITEM)

    class Garbage:
        def __init__(self, model):
            pass

        def complete(self, system, user):
            return "nope"

    monkeypatch.setattr(level, "AnthropicChecker", Garbage)
    report = tmp_path / "r.md"
    cli.main(
        ["--items", str(tmp_path), "--samples", str(tmp_path / "x"), "--report", str(report),
         "--exams", str(ROOT / "content" / "exams")]
    )  # fmt: skip
    assert "no usable answer" in report.read_text()


def test_fails_on_topic_missing_from_taxonomy(tmp_path):
    write(tmp_path, "bad", {**ITEM, "topics": ["logement"]})
    assert run(tmp_path, tmp_path / "absent", tmp_path / "r.md") == 1
    assert "topics" in (tmp_path / "r.md").read_text()
