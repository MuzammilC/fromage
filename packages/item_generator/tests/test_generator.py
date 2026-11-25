import json
from datetime import date
from pathlib import Path

import pytest
import yaml
from fromage_exam_definition import load_exam_definition, load_item
from fromage_item_generator import GenerationError, LLMResult, generate_items
from fromage_item_generator.prompts import load_prompt

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def a2():
    return load_exam_definition(ROOT / "content" / "exams" / "delf-a2-tp.yaml")


MONOLOGUE = {
    "candidate_brief": "Vous parlez de votre logement.",
    "suggested_angles": ["Où", "Comment", "Pourquoi"],
}
INTERACTION = {
    "candidate_brief": "Vous cherchez un appartement.",
    "examiner_role": "Agent immobilier",
    "examiner_only_data": {"loyer_eur": 600},
    "expected_speech_acts": ["saluer", "demander le prix"],
    "register": "formal",
}
QUESTIONS = {"questions": ["Où habitez-vous ?", "Comment est votre logement ?"]}


class FakeLLM:
    def __init__(self, *payloads):
        self.payloads = list(payloads)
        self.calls = []

    def complete(self, system, user, metadata=None):
        self.calls.append((system, user))
        self.metadata = metadata
        payload = self.payloads.pop(0)
        if isinstance(payload, Exception):
            raise payload
        text = payload if isinstance(payload, str) else json.dumps(payload)
        return LLMResult(text=text, input_tokens=1000, output_tokens=500)


def run(a2, tmp_path, llm, part="monologue_suivi", n=1):
    return generate_items(
        a2,
        part,
        "logement",
        n,
        llm,
        out_dir=tmp_path,
        model="claude-sonnet-5-5",
        today=date(2026, 11, 22),
    )


def test_generates_n_valid_draft_items_stamped_with_metadata(a2, tmp_path):
    result = run(a2, tmp_path, FakeLLM(MONOLOGUE, MONOLOGUE, MONOLOGUE), n=3)
    assert len(result.items) == 3
    files = sorted(tmp_path.glob("*.yaml"))
    assert [f.name for f in files] == [
        "a2-monologue-suivi-logement-001.yaml",
        "a2-monologue-suivi-logement-002.yaml",
        "a2-monologue-suivi-logement-003.yaml",
    ]
    item = load_item(files[0], a2)
    data = yaml.safe_load(files[0].read_text())
    assert data["status"] == "draft"
    assert data["teacher_reviewed"] is False
    assert data["topics"] == ["logement"]
    assert data["exam_definition"] == "delf-a2-tp@1"
    assert data["generation"] == {
        "model": "claude-sonnet-5-5",
        "prompt_version": "monologue_subject-v1",
        "date": "2026-11-22",
    }
    assert item.root.type == "monologue_subject"


@pytest.mark.parametrize(
    ("part", "payload", "item_type"),
    [
        ("entretien_dirige", QUESTIONS, "question_bank"),
        ("exercice_en_interaction", INTERACTION, "interaction_situation"),
    ],
)
def test_each_part_uses_its_item_type_prompt(a2, tmp_path, part, payload, item_type):
    llm = FakeLLM(payload)
    run(a2, tmp_path, llm, part=part)
    assert llm.calls[0][0] == load_prompt(item_type).text
    assert load_item(next(tmp_path.glob("*.yaml")), a2).root.type == item_type


def test_ids_continue_after_existing_files(a2, tmp_path):
    run(a2, tmp_path, FakeLLM(MONOLOGUE))
    run(a2, tmp_path, FakeLLM(MONOLOGUE))
    assert (tmp_path / "a2-monologue-suivi-logement-002.yaml").exists()


def test_cost_comes_from_token_usage(a2, tmp_path):
    result = run(a2, tmp_path, FakeLLM(MONOLOGUE, MONOLOGUE), n=2)
    assert result.input_tokens == 2000
    assert result.output_tokens == 1000
    assert result.cost_usd > 0


def test_unknown_part_is_rejected(a2, tmp_path):
    with pytest.raises(GenerationError, match="nope"):
        run(a2, tmp_path, FakeLLM(), part="nope")


def test_invalid_theme_is_rejected(a2, tmp_path):
    with pytest.raises(GenerationError, match="theme"):
        generate_items(
            a2, "monologue_suivi", "Bad Theme", 1, FakeLLM(), out_dir=tmp_path, model="m"
        )


def test_invalid_output_is_skipped_not_written(a2, tmp_path):
    result = run(a2, tmp_path, FakeLLM("not json", {"candidate_brief": "x"}, MONOLOGUE), n=3)
    assert len(result.items) == 1
    assert len(result.errors) == 2
    assert [f.name for f in tmp_path.glob("*.yaml")] == ["a2-monologue-suivi-logement-001.yaml"]


def test_json_in_code_fence_is_accepted(a2, tmp_path):
    fenced = "```json\n" + json.dumps(MONOLOGUE) + "\n```"
    assert len(run(a2, tmp_path, FakeLLM(fenced)).items) == 1


def test_llm_cannot_override_metadata(a2, tmp_path):
    run(a2, tmp_path, FakeLLM({**MONOLOGUE, "status": "reviewed", "id": "evil"}))
    data = yaml.safe_load(next(tmp_path.glob("*.yaml")).read_text())
    assert data["status"] == "draft"
    assert data["id"] == "a2-monologue-suivi-logement-001"


def test_prompts_are_versioned_files_and_never_ask_to_copy_fei():
    for item_type in ("question_bank", "monologue_subject", "interaction_situation"):
        prompt = load_prompt(item_type)
        assert prompt.version == f"{item_type}-v1"
        assert "original" in prompt.text.lower()


def test_api_failure_keeps_earlier_items_and_cost(a2, tmp_path):
    result = run(a2, tmp_path, FakeLLM(MONOLOGUE, RuntimeError("rate limited"), MONOLOGUE), n=3)
    assert len(result.items) == 1
    assert "rate limited" in result.errors[0]
    assert result.cost_usd > 0


def test_truncated_output_is_reported(a2, tmp_path):
    class Truncating(FakeLLM):
        def complete(self, system, user, metadata=None):
            return LLMResult('{"candidate_brief": "x', 10, 10, truncated=True)

    result = run(a2, tmp_path, Truncating())
    assert result.items == []
    assert "cut off" in result.errors[0]


def test_later_calls_are_told_about_existing_items(a2, tmp_path):
    llm = FakeLLM(MONOLOGUE, MONOLOGUE)
    run(a2, tmp_path, llm, n=2)
    assert "Vous parlez de votre logement." not in llm.calls[0][1]
    assert "Vous parlez de votre logement." in llm.calls[1][1]


def test_unknown_model_cost_is_unknown(a2, tmp_path):
    result = generate_items(
        a2, "monologue_suivi", "logement", 1, FakeLLM(MONOLOGUE), out_dir=tmp_path, model="other"
    )
    assert result.cost_usd is None


def test_metadata_is_passed_to_the_llm(a2, tmp_path):
    llm = FakeLLM(MONOLOGUE)
    run(a2, tmp_path, llm)
    assert llm.metadata == {
        "exam": "delf-a2-tp@1",
        "part": "monologue_suivi",
        "theme": "logement",
        "prompt_version": "monologue_subject-v1",
    }


def test_never_overwrites_a_file_taken_since_the_id_was_chosen(a2, tmp_path, monkeypatch):
    from fromage_item_generator import generator

    real = generator._next_id
    taken = tmp_path / "a2-monologue-suivi-logement-001.yaml"

    def racing(out_dir, slug):
        item_id = real(out_dir, slug)
        if not taken.exists():
            taken.write_text("other run")
        return item_id

    monkeypatch.setattr(generator, "_next_id", racing)
    run(a2, tmp_path, FakeLLM(MONOLOGUE))
    assert taken.read_text() == "other run"
    assert (tmp_path / "a2-monologue-suivi-logement-002.yaml").exists()
