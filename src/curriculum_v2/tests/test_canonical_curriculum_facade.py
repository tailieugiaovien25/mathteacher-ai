import pytest

from curriculum_v2.canonical_curriculum import (
    CanonicalCurriculumFacade,
    get_canonical_curriculum,
)


def test_public_facade_exposes_locked_requirement_counts():
    facade = CanonicalCurriculumFacade()

    assert len(facade.requirements_for_grade(6)) == 80
    assert len(facade.requirements_for_grade(7)) == 68
    assert len(facade.requirements_for_grade(8)) == 68
    assert len(facade.requirements_for_grade(9)) == 74


def test_public_facade_exposes_locked_node_counts():
    facade = CanonicalCurriculumFacade()

    assert len(facade.nodes_for_grade(6)) == 43
    assert len(facade.nodes_for_grade(7)) == 41
    assert len(facade.nodes_for_grade(8)) == 40
    assert len(facade.nodes_for_grade(9)) == 41


def test_public_facade_finds_requirement_by_id():
    facade = CanonicalCurriculumFacade()

    requirement = facade.requirement_by_id("YCCD-MATH-09-0001")

    assert requirement is not None
    assert requirement.canonical_id == "YCCD-MATH-09-0001"


def test_public_facade_finds_node_by_id():
    facade = CanonicalCurriculumFacade()

    node = facade.node_by_id("CURR-NODE-MATH-G8-001")

    assert node is not None
    assert node.curriculum_node_id == "CURR-NODE-MATH-G8-001"


def test_public_facade_searches_requirements():
    facade = CanonicalCurriculumFacade()

    results = facade.search_requirements("phương trình", grade=9)

    assert results
    assert all(
        "phương trình" in item.requirement_text_original.casefold()
        for item in results
    )


def test_public_facade_exposes_hierarchy_navigation():
    facade = CanonicalCurriculumFacade()
    roots = facade.root_nodes(6)

    assert roots
    children = facade.child_nodes(6, roots[0].curriculum_node_id)
    assert children
    assert all(
        child.parent_id == roots[0].curriculum_node_id
        for child in children
    )


def test_public_facade_builds_curriculum_context():
    facade = CanonicalCurriculumFacade()
    root = facade.root_nodes(9)[0]

    context = facade.curriculum_context(
        9,
        root.curriculum_node_id,
    )

    assert context.grade == 9
    assert context.selected_node.curriculum_node_id == root.curriculum_node_id
    assert context.descendants
    assert context.requirements


def test_public_facade_can_build_direct_node_context():
    facade = CanonicalCurriculumFacade()
    node = next(
        node
        for node in facade.nodes_for_grade(7)
        if facade.requirement_by_id("YCCD-MATH-07-0001") is not None
        and node.curriculum_node_id
        == facade.requirement_by_id(
            "YCCD-MATH-07-0001"
        ).curriculum_node_ref
    )

    context = facade.curriculum_context(
        7,
        node.curriculum_node_id,
        include_descendants=False,
    )

    assert context.descendants == ()
    assert all(
        requirement.curriculum_node_ref == node.curriculum_node_id
        for requirement in context.requirements
    )


def test_public_facade_rejects_invalid_grade():
    facade = CanonicalCurriculumFacade()

    with pytest.raises(ValueError):
        facade.requirements_for_grade(10)

    with pytest.raises(ValueError):
        facade.nodes_for_grade(5)


def test_default_facade_is_shared():
    first = get_canonical_curriculum()
    second = get_canonical_curriculum()

    assert first is second
