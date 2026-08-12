import pytest

from curriculum_v2.processors.canonical_curriculum_context import (
    CanonicalCurriculumContext,
    CanonicalCurriculumContextService,
)


def test_build_returns_context_for_canonical_node():
    service = CanonicalCurriculumContextService()

    context = service.build(6, "CURR-NODE-MATH-G6-001")

    assert isinstance(context, CanonicalCurriculumContext)
    assert context.grade == 6
    assert context.selected_node.curriculum_node_id == (
        "CURR-NODE-MATH-G6-001"
    )


def test_context_includes_ancestors_for_nested_node():
    service = CanonicalCurriculumContextService()
    node = service.node_query.by_grade(9)[-1]

    context = service.build(9, node.curriculum_node_id)

    if node.parent_id is not None:
        assert context.ancestors
        assert context.ancestors[-1].curriculum_node_id == node.parent_id


def test_context_includes_descendants_by_default():
    service = CanonicalCurriculumContextService()
    root = service.node_query.roots(6)[0]

    context = service.build(6, root.curriculum_node_id)

    assert context.descendants
    assert all(
        node.curriculum_node_id != root.curriculum_node_id
        for node in context.descendants
    )


def test_context_can_exclude_descendants():
    service = CanonicalCurriculumContextService()
    root = service.node_query.roots(6)[0]

    context = service.build(
        6,
        root.curriculum_node_id,
        include_descendants=False,
    )

    assert context.descendants == ()
    assert all(
        requirement.curriculum_node_ref == root.curriculum_node_id
        for requirement in context.requirements
    )


def test_context_requirements_are_scoped_to_selected_subtree():
    service = CanonicalCurriculumContextService()
    root = service.node_query.roots(9)[0]

    context = service.build(9, root.curriculum_node_id)

    allowed = {root.curriculum_node_id}
    allowed.update(node.curriculum_node_id for node in context.descendants)

    assert context.requirements
    assert all(
        requirement.curriculum_node_ref in allowed
        for requirement in context.requirements
    )


def test_leaf_context_contains_direct_requirements_only():
    service = CanonicalCurriculumContextService()
    nodes = service.node_query.by_grade(8)
    leaf = next(
        node
        for node in nodes
        if not service.node_query.children(8, node.curriculum_node_id)
        and service.requirement_query.by_node(8, node.curriculum_node_id)
    )

    context = service.build(8, leaf.curriculum_node_id)

    expected = service.requirement_query.by_node(
        8,
        leaf.curriculum_node_id,
    )

    assert context.descendants == ()
    assert [r.canonical_id for r in context.requirements] == [
        r.canonical_id for r in expected
    ]


def test_context_preserves_canonical_requirement_objects():
    service = CanonicalCurriculumContextService()
    node = next(
        node
        for node in service.node_query.by_grade(7)
        if service.requirement_query.by_node(
            7,
            node.curriculum_node_id,
        )
    )

    context = service.build(7, node.curriculum_node_id)

    assert context.requirements
    assert all(r.canonical_id for r in context.requirements)
    assert all(r.provenance for r in context.requirements)
    assert all(r.validation for r in context.requirements)


def test_wrong_grade_node_combination_is_rejected():
    service = CanonicalCurriculumContextService()

    with pytest.raises(ValueError):
        service.build(7, "CURR-NODE-MATH-G8-001")


def test_missing_canonical_node_is_rejected():
    service = CanonicalCurriculumContextService()

    with pytest.raises(LookupError):
        service.build(9, "CURR-NODE-MATH-G9-999")


def test_invalid_grade_is_rejected():
    service = CanonicalCurriculumContextService()

    with pytest.raises(ValueError):
        service.build(10, "CURR-NODE-MATH-G10-001")
