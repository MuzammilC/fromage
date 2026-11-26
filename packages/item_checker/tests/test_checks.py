from pathlib import Path

import pytest
from fromage_exam_definition import load_exam_definition
from fromage_item_checker.checks import check_completeness, check_schema, item_text
from fromage_item_checker.overlap import check_overlap, load_samples, ngrams

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def a2():
    return load_exam_definition(ROOT / "content" / "exams" / "delf-a2-tp.yaml")


def interaction(**overrides):
    data = {
        "type": "interaction_situation",
        "id": "a2-exercice-en-interaction-logement-001",
        "exam_definition": "delf-a2-tp@1",
        "part_key": "exercice_en_interaction",
        "topics": ["logement"],
        "status": "draft",
        "version": 1,
        "generation": {"model": "m", "prompt_version": "p-v1", "date": "2026-11-24"},
        "teacher_reviewed": False,
        "candidate_brief": "Vous cherchez un appartement. Vous parlez à l'agent.",
        "examiner_role": "Agent immobilier",
        "examiner_only_data": {"loyer_eur": 600, "visite": "samedi à 10 h"},
        "expected_speech_acts": ["saluer", "demander le prix"],
        "register": "formal",
    }
    return {**data, **overrides}


def test_schema_passes_for_valid_item(a2):
    assert check_schema(interaction(), a2).passed


def test_schema_fails_for_invalid_item(a2):
    result = check_schema(interaction(register="rude"), a2)
    assert not result.passed
    assert "register" in result.detail


def test_schema_fails_when_item_points_at_other_part(a2):
    assert not check_schema(interaction(part_key="monologue_suivi"), a2).passed


def test_completeness_passes_with_price_and_time(a2):
    item = check_schema(interaction(), a2).item
    assert check_completeness(item).passed


def test_completeness_fails_without_examiner_data(a2):
    item = check_schema(interaction(examiner_only_data={}), a2).item
    result = check_completeness(item)
    assert not result.passed
    assert "empty" in result.detail


def test_completeness_fails_with_no_figures(a2):
    item = check_schema(interaction(examiner_only_data={"lieu": "centre-ville"}), a2).item
    assert not check_completeness(item).passed


def test_completeness_fails_with_blank_values(a2):
    item = check_schema(interaction(examiner_only_data={"loyer_eur": 600, "visite": ""}), a2).item
    assert not check_completeness(item).passed


def test_completeness_not_applicable_to_other_types(a2):
    clean = {k: v for k, v in interaction().items() if k in _COMMON} | {
        "type": "question_bank",
        "part_key": "entretien_dirige",
        "questions": ["Où habitez-vous ?"],
    }
    item = check_schema(clean, a2).item
    assert item is not None
    assert check_completeness(item).passed


_COMMON = {
    "id",
    "exam_definition",
    "topics",
    "status",
    "version",
    "generation",
    "teacher_reviewed",
}


def test_item_text_has_content_but_not_metadata(a2):
    item = check_schema(interaction(), a2).item
    text = item_text(item)
    assert "Vous cherchez un appartement" in text
    assert "samedi à 10 h" in text
    assert "draft" not in text


COPIED = "Vous voulez organiser une fête pour l'anniversaire de votre meilleur ami"


def test_ngrams_normalise_case_accents_and_punctuation():
    assert ngrams("Où êtes-vous, Madame ?", 2) == ngrams("ou etes vous madame", 2)


def test_overlap_skipped_without_samples_folder(tmp_path):
    assert load_samples(tmp_path / "absent") is None
    result = check_overlap("peu importe", None)
    assert result.skipped and result.passed


def test_overlap_flags_copied_sentences(tmp_path):
    (tmp_path / "sample.txt").write_text(f"Texte. {COPIED}. Autre texte sans rapport.")
    samples = load_samples(tmp_path)
    result = check_overlap(f"Bonjour. {COPIED}.", samples)
    assert not result.passed
    assert "anniversaire" in result.detail


def test_overlap_passes_for_original_text(tmp_path):
    (tmp_path / "sample.txt").write_text(f"Texte. {COPIED}. Autre texte sans rapport.")
    samples = load_samples(tmp_path)
    original = (
        "Vous cherchez un appartement près de la gare et vous parlez avec un agent immobilier "
        "pour connaître le loyer, les charges, la date de visite et les conditions du contrat."
    )
    assert check_overlap(original, samples).passed


def test_empty_samples_folder_counts_as_absent(tmp_path):
    assert load_samples(tmp_path) is None


def test_completeness_accepts_time_words(a2):
    item = check_schema(interaction(examiner_only_data={"visite": "samedi", "prix": "gratuit"}), a2)
    assert check_completeness(item.item).passed


def test_overlap_does_not_span_fields(tmp_path):
    (tmp_path / "s.txt").write_text("un deux trois quatre cinq")
    samples = load_samples(tmp_path)
    assert check_overlap("un deux trois\nquatre cinq", samples).passed
    assert not check_overlap("un deux trois quatre cinq six sept huit neuf dix", samples).passed
