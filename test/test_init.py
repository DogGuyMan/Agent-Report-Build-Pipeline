import pytest
from viz.init import parseSpecFilename, findSimilar, DOC_DIRS

def test_parse_spec_filename_splits_date_and_slug():
    assert parseSpecFilename("2026-07-27-geometry-winding-ownership-design.md") == {
        "date": "2026-07-27", "slug": "geometry-winding-ownership"
    }

def test_parse_spec_filename_handles_many_hyphens():
    assert parseSpecFilename("2026-05-20-sp1-shader-program-resource-consolidation-design.md") == {
        "date": "2026-05-20", "slug": "sp1-shader-program-resource-consolidation"
    }

def test_parse_spec_filename_null_if_not_ending_with_design():
    assert parseSpecFilename("2026-07-27-geometry-winding-ownership-before.svg") is None
    assert parseSpecFilename("2026-07-27-geometry-winding-ownership-design-review.html") is None

def test_parse_spec_filename_null_if_not_date():
    assert parseSpecFilename("26-7-27-my-topic-design.md") is None
    assert parseSpecFilename("not-a-date-my-topic-design.md") is None

def test_parse_spec_filename_null_for_unrelated_files():
    assert parseSpecFilename("README.md") is None
    assert parseSpecFilename("data.ts") is None

def test_doc_dirs_has_specs_and_plans():
    assert [d["dir"] for d in DOC_DIRS] == ["specs", "plans"]

def test_plans_matched_by_date_and_slug_without_suffix():
    assert parseSpecFilename("2026-08-30-symbol-resolution-survey.md", "plans") == {
        "date": "2026-08-30", "slug": "symbol-resolution-survey"
    }

def test_plans_convention_does_not_work_for_specs():
    assert parseSpecFilename("2026-08-30-symbol-resolution-survey.md", "specs") is None

def test_specs_convention_works_in_plans_if_filename_matches():
    assert parseSpecFilename("2026-08-30-foo-design.md", "plans") == {
        "date": "2026-08-30", "slug": "foo-design"
    }

def test_parse_spec_filename_defaults_to_specs():
    assert parseSpecFilename("2026-07-27-geometry-winding-ownership-design.md") == {
        "date": "2026-07-27", "slug": "geometry-winding-ownership"
    }

def test_plans_null_if_not_date():
    assert parseSpecFilename("README.md", "plans") is None
    assert parseSpecFilename("not-a-date-topic.md", "plans") is None

def test_find_similar_proposes_candidates_for_typo():
    candidates = ["geometry-winding-ownership", "matrix-rain-parameterization"]
    assert findSimilar("geometry-winding-ownershp", candidates) == ["geometry-winding-ownership"]

def test_find_similar_finds_substrings():
    candidates = ["geometry-winding-ownership"]
    assert findSimilar("geometry-winding", candidates) == ["geometry-winding-ownership"]

def test_find_similar_returns_empty_for_unrelated():
    candidates = ["geometry-winding-ownership", "matrix-rain-parameterization"]
    assert findSimilar("totally-unrelated-topic", candidates) == []
