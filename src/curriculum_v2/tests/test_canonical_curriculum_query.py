import pytest

from curriculum_v2.processors.canonical_curriculum_query import CanonicalCurriculumQuery


def test_query_by_grade_uses_locked_baseline():
    query = CanonicalCurriculumQuery()
    assert len(query.by_grade(6)) == 80
    assert len(query.by_grade(7)) == 68
    assert len(query.by_grade(8)) == 68
    assert len(query.by_grade(9)) == 74


def test_query_by_node_returns_only_requested_node():
    query = CanonicalCurriculumQuery()
    node_id = "CURR-NODE-MATH-G9-004"
    results = query.by_node(9, node_id)
    assert results
    assert all(r.curriculum_node_ref == node_id for r in results)


def test_query_by_id_finds_requirement():
    query = CanonicalCurriculumQuery()
    result = query.by_id("YCCD-MATH-09-0001")
    assert result is not None
    assert result.canonical_id == "YCCD-MATH-09-0001"


def test_query_by_id_returns_none_when_missing():
    query = CanonicalCurriculumQuery()
    assert query.by_id("YCCD-MATH-09-9999") is None


def test_search_is_case_insensitive():
    query = CanonicalCurriculumQuery()
    results = query.search("phương trình", grade=9)
    assert results
    assert all("phương trình" in r.requirement_text_original.casefold() for r in results)


def test_search_can_span_all_thcs_grades():
    query = CanonicalCurriculumQuery()
    results = query.search("máy tính cầm tay")
    assert results
    assert len({r.canonical_id.split("-")[2] for r in results}) >= 2


def test_search_empty_keyword_returns_empty_list():
    query = CanonicalCurriculumQuery()
    assert query.search("   ") == []


def test_invalid_grade_is_rejected():
    query = CanonicalCurriculumQuery()
    with pytest.raises(ValueError):
        query.by_grade(10)
    with pytest.raises(ValueError):
        query.search("phương trình", grade=5)
