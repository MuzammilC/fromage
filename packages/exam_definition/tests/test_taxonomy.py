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
A2_TAXONOMY = ROOT / "content" / "taxonomy" / "a2.yaml"
A2_EXAM = ROOT / "content" / "exams" / "delf-a2-tp.yaml"


def _data():
    return yaml.safe_load(A2_TAXONOMY.read_text())


def test_a2_taxonomy_loads_against_the_a2_exam_definition():
    taxonomy = load_taxonomy(A2_TAXONOMY, load_exam_definition(A2_EXAM))
    assert [p.key.root for p in taxonomy.parts] == [
        "entretien_dirige",
        "monologue_suivi",
        "exercice_en_interaction",
    ]


def test_every_part_has_at_least_twelve_themes():
    for part in load_taxonomy(A2_TAXONOMY).parts:
        assert len(part.themes) >= 12, part.key


def test_every_theme_has_english_and_french_labels():
    for part in load_taxonomy(A2_TAXONOMY).parts:
        for theme in part.themes:
            label = theme.root.label
            assert label.en.root.strip() and label.fr.root.strip()


def test_theme_without_a_source_is_rejected():
    data = _data()
    del data["parts"][0]["themes"][0]["source"]
    with pytest.raises(TaxonomyError, match="source"):
        parse_taxonomy(data)


def test_personal_sphere_theme_needs_a_justification():
    data = _data()
    theme = next(t for p in data["parts"] for t in p["themes"] if t["source"] == "personal_sphere")
    del theme["justification"]
    with pytest.raises(TaxonomyError, match="justification"):
        parse_taxonomy(data)


def test_research_theme_needs_the_research_doc_name():
    data = _data()
    theme = next(t for p in data["parts"] for t in p["themes"] if t["source"] == "research")
    del theme["research_theme"]
    with pytest.raises(TaxonomyError, match="research_theme"):
        parse_taxonomy(data)


def test_duplicate_theme_key_in_a_part_is_rejected():
    data = _data()
    themes = data["parts"][0]["themes"]
    themes[1]["key"] = themes[0]["key"]
    with pytest.raises(TaxonomyError, match=rf"duplicate.*{themes[0]['key']}"):
        parse_taxonomy(data)


def test_part_missing_from_the_exam_definition_is_rejected():
    data = _data()
    data["parts"][0]["key"] = "not_a_part"
    with pytest.raises(TaxonomyError, match="not_a_part"):
        parse_taxonomy(data, load_exam_definition(A2_EXAM))


def test_exam_definition_part_without_themes_is_rejected():
    data = _data()
    data["parts"].pop()
    with pytest.raises(TaxonomyError, match="exercice_en_interaction"):
        parse_taxonomy(data, load_exam_definition(A2_EXAM))
