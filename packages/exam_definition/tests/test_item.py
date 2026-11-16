from pathlib import Path

import pytest
import yaml
from fromage_exam_definition import ItemError, load_exam_definition, parse_item

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "schema" / "fixtures" / "items"


def fixture(name):
    return yaml.safe_load((FIXTURES / name).read_text())


@pytest.fixture
def a2():
    return load_exam_definition(ROOT / "content" / "exams" / "delf-a2-tp.yaml")


def test_a2_definition_validates_with_band_points_adding_up_to_25(a2):
    assert a2.id == "delf-a2-tp"
    assert sum(c.band_points[3] for c in a2.grid) == 25


def test_a2_has_three_parts_with_turn_modes(a2):
    assert [(p.key, p.turn_mode.value) for p in a2.parts] == [
        ("entretien_dirige", "interactive"),
        ("monologue_suivi", "listen_only"),
        ("exercice_en_interaction", "interactive"),
    ]


def test_a2_band_points(a2):
    points = {c.key: c.band_points for c in a2.grid}
    assert points == {
        "entretien_dirige": [0, 1, 2.5, 4],
        "monologue_suivi": [0, 1, 2.5, 4],
        "exercice_en_interaction": [0, 1, 2.5, 4],
        "lexique": [0, 1, 3, 5],
        "morphosyntaxe": [0, 1, 2.5, 4],
        "phonologie": [0, 1, 2.5, 4],
    }


def test_a2_describes_every_criterion_and_links_sources(a2):
    assert all(c.descriptors is not None for c in a2.grid)
    assert a2.provenance.links


@pytest.mark.parametrize(
    ("file", "type_"),
    [
        ("valid-question-bank.yaml", "question_bank"),
        ("valid-monologue-subject.yaml", "monologue_subject"),
        ("valid-interaction-situation.yaml", "interaction_situation"),
    ],
)
def test_valid_items(file, type_):
    assert parse_item(fixture(file)).root.type == type_


def test_item_for_existing_part_is_accepted(a2):
    item = parse_item(fixture("valid-interaction-situation.yaml"), a2)
    assert item.root.part_key.root == "exercice_en_interaction"


@pytest.mark.parametrize(
    ("file", "message"),
    [
        ("invalid-missing-examiner-role.yaml", "examiner_role"),
        ("invalid-status.yaml", "status"),
        ("invalid-exam-definition-ref.yaml", "exam_definition"),
        ("invalid-type.yaml", "type"),
        ("invalid-generation-date.yaml", r"generation\.date.*not a real date"),
        ("invalid-missing-teacher-reviewed.yaml", "teacher_reviewed"),
        ("invalid-teacher-reviewed-true.yaml", "teacher_reviewed"),
    ],
)
def test_invalid_items_fail_with_clear_errors(file, message):
    with pytest.raises(ItemError, match=message):
        parse_item(fixture(file))


def test_item_for_missing_part_is_rejected(a2):
    data = fixture("valid-question-bank.yaml")
    data["part_key"] = "dialogue_simule"
    with pytest.raises(ItemError, match=r"dialogue_simule.*Part"):
        parse_item(data, a2)


def test_item_pointing_at_another_definition_is_rejected(a2):
    data = fixture("valid-question-bank.yaml")
    data["exam_definition"] = "delf-a2-tp@2"
    with pytest.raises(ItemError, match=r"delf-a2-tp@2.*delf-a2-tp@1"):
        parse_item(data, a2)
