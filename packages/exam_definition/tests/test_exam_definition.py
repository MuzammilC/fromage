from pathlib import Path

import pytest
import yaml
from fromage_exam_definition import ExamDefinitionError, load_exam_definition, parse_exam_definition

FIXTURES = Path(__file__).resolve().parents[3] / "schema" / "fixtures"


def test_valid_fixture_loads():
    exam = load_exam_definition(FIXTURES / "valid.yaml")
    assert exam.id == "fixture-a2"
    assert [p.key for p in exam.parts] == ["guided_interview", "monologue"]


def test_wrong_band_points_total_is_rejected_with_clear_error():
    with pytest.raises(ExamDefinitionError, match=r"Band Points.*25.*23"):
        load_exam_definition(FIXTURES / "invalid-band-points-total.yaml")


def test_criterion_scoped_to_missing_part_is_rejected_with_clear_error():
    with pytest.raises(ExamDefinitionError, match=r"monologue_achievement.*monologue"):
        load_exam_definition(FIXTURES / "invalid-missing-part.yaml")


def test_schema_violation_is_rejected():
    data = yaml.safe_load((FIXTURES / "valid.yaml").read_text())
    data["grid"][0]["band_points"] = [0, 1, 2]
    with pytest.raises(ExamDefinitionError, match="band_points"):
        parse_exam_definition(data)


def test_impossible_retrieval_date_is_rejected():
    data = yaml.safe_load((FIXTURES / "valid.yaml").read_text())
    data["provenance"]["retrieved_on"] = "2026-99-99"
    with pytest.raises(ExamDefinitionError, match="retrieved_on.*not a real date"):
        parse_exam_definition(data)
