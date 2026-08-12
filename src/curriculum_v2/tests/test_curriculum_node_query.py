import pytest

from curriculum_v2.processors.curriculum_node_query import CurriculumNodeQuery


def test_node_query_uses_locked_baseline_counts():
    query = CurriculumNodeQuery()

    assert len(query.by_grade(6)) == 43
    assert len(query.by_grade(7)) == 41
    assert len(query.by_grade(8)) == 40
    assert len(query.by_grade(9)) == 41


def test_node_query_returns_curriculum_node_model():
    query = CurriculumNodeQuery()

    node = query.by_id("CURR-NODE-MATH-G6-001")

    assert node is not None
    assert node.curriculum_node_id == "CURR-NODE-MATH-G6-001"
    assert node.name
    assert node.node_type


def test_roots_have_no_parent():
    query = CurriculumNodeQuery()

    roots = query.roots(9)

    assert roots
    assert all(node.parent_id is None for node in roots)


def test_children_are_direct_children_only_and_ordered():
    query = CurriculumNodeQuery()
    parent_id = "CURR-NODE-MATH-G6-001"

    children = query.children(6, parent_id)

    assert children
    assert all(node.parent_id == parent_id for node in children)
    assert [node.sequence for node in children] == sorted(
        node.sequence for node in children
    )


def test_descendants_are_recursive():
    query = CurriculumNodeQuery()
    root = query.roots(6)[0]

    descendants = query.descendants(6, root.curriculum_node_id)

    assert descendants
    descendant_ids = {node.curriculum_node_id for node in descendants}
    direct_children = query.children(6, root.curriculum_node_id)
    assert all(
        child.curriculum_node_id in descendant_ids
        for child in direct_children
    )


def test_ancestors_form_path_from_root_to_parent():
    query = CurriculumNodeQuery()
    node = query.by_grade(9)[-1]

    ancestors = query.ancestors(9, node.curriculum_node_id)

    if node.parent_id is not None:
        assert ancestors
        assert ancestors[-1].curriculum_node_id == node.parent_id
        assert ancestors[0].parent_id is None


def test_search_finds_nodes_by_name_case_insensitively():
    query = CurriculumNodeQuery()

    results = query.search("hình học", grade=6)

    assert results
    assert any("hình học" in node.name.casefold() for node in results)


def test_search_empty_keyword_returns_empty_list():
    query = CurriculumNodeQuery()

    assert query.search("   ") == []


def test_missing_node_returns_none_or_empty_hierarchy():
    query = CurriculumNodeQuery()

    assert query.by_id("CURR-NODE-MATH-G9-999") is None
    assert query.ancestors(9, "CURR-NODE-MATH-G9-999") == []
    assert query.descendants(9, "CURR-NODE-MATH-G9-999") == []


def test_invalid_grade_is_rejected():
    query = CurriculumNodeQuery()

    with pytest.raises(ValueError):
        query.by_grade(10)

    with pytest.raises(ValueError):
        query.search("đại số", grade=5)
