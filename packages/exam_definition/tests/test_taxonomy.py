from pathlib import Path

import pytest
import yaml
from fromage_exam_definition import (
    TaxonomyError,
    load_exam_definition,
    load_taxonomy,
    parse_taxonomy,
)

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "schema" / "fixtures"
TAXONOMY_FIXTURES = FIXTURES / "taxonomy"
FIXTURE_EXAM = load_exam_definition(FIXTURES / "valid.yaml")
A2_TAXONOMY = ROOT / "content" / "taxonomy" / "a2.yaml"
A2_EXAM = ROOT / "content" / "exams" / "delf-a2-tp.yaml"


def _valid():
    return yaml.safe_load((TAXONOMY_FIXTURES / "valid.yaml").read_text(encoding="utf-8"))


def test_valid_fixture_loads_against_its_exam_definition():
    taxonomy = load_taxonomy(TAXONOMY_FIXTURES / "valid.yaml", FIXTURE_EXAM)
    assert [p.key.root for p in taxonomy.parts] == ["guided_interview", "monologue"]


def test_duplicate_theme_key_in_a_part_is_rejected():
    with pytest.raises(TaxonomyError, match=r"Duplicate theme key 'family'.*guided_interview"):
        load_taxonomy(TAXONOMY_FIXTURES / "invalid-duplicate-theme.yaml")


def test_personal_sphere_theme_without_justification_is_rejected():
    with pytest.raises(TaxonomyError, match="justification"):
        load_taxonomy(TAXONOMY_FIXTURES / "invalid-missing-justification.yaml")


def test_part_not_in_the_exam_definition_is_rejected():
    with pytest.raises(TaxonomyError, match=r"Part 'role_play' is not a Part"):
        load_taxonomy(TAXONOMY_FIXTURES / "invalid-part-not-in-definition.yaml", FIXTURE_EXAM)


def test_exam_definition_part_without_themes_is_rejected():
    data = _valid()
    data["parts"].pop()
    with pytest.raises(TaxonomyError, match=r"Part 'monologue'.*has no themes"):
        parse_taxonomy(data, FIXTURE_EXAM)


def test_wrong_exam_definition_ref_is_rejected():
    data = _valid()
    data["exam_definition"] = "fixture-a2@2"
    with pytest.raises(TaxonomyError, match=r"does not match 'fixture-a2@1'"):
        parse_taxonomy(data, FIXTURE_EXAM)


def test_research_theme_without_the_research_name_is_rejected():
    data = _valid()
    del data["parts"][0]["themes"][0]["research_theme"]
    with pytest.raises(TaxonomyError, match="research_theme"):
        parse_taxonomy(data)


def test_theme_with_a_bad_key_is_rejected():
    data = _valid()
    data["parts"][0]["themes"][0]["key"] = "Not A Key"
    with pytest.raises(TaxonomyError, match="key"):
        parse_taxonomy(data)


def test_a2_taxonomy_loads_against_the_a2_exam_definition():
    taxonomy = load_taxonomy(A2_TAXONOMY, load_exam_definition(A2_EXAM))
    assert [p.key.root for p in taxonomy.parts] == [
        "entretien_dirige",
        "monologue_suivi",
        "exercice_en_interaction",
    ]


def test_a2_taxonomy_has_at_least_twelve_themes_per_part():
    # Issue #19: "Aim for 12 or more themes per Part".
    for part in load_taxonomy(A2_TAXONOMY).parts:
        assert len(part.themes) >= 12, part.key.root
