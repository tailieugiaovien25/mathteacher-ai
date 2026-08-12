import pytest

from educational_planning_v2.models import CurriculumScope
from educational_planning_v2.services import (
    PlanningContext,
    PlanningContextService,
)


def test_build_empty_scope_returns_empty_context():
    service = PlanningContextService()
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=6,
    )

    context = service.build(scope)

    assert isinstance(context, PlanningContext)
    assert context.scope is scope
    assert context.nodes == ()
    assert context.requirements == ()


def test_build_resolves_canonical_node():
    service = PlanningContextService()
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=6,
        curriculum_node_ids=("CURR-NODE-MATH-G6-001",),
    )

    context = service.build(scope)

    assert len(context.nodes) == 1
    assert context.nodes[0].curriculum_node_id == "CURR-NODE-MATH-G6-001"


def test_build_resolves_canonical_requirement():
    service = PlanningContextService()
    requirement = service._curriculum.requirement_by_id(
        "YCCD-MATH-07-0001"
    )
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=7,
        curriculum_node_ids=(requirement.curriculum_node_ref,),
        canonical_requirement_ids=("YCCD-MATH-07-0001",),
    )

    context = service.build(scope)

    assert len(context.requirements) == 1
    assert context.requirements[0].canonical_id == "YCCD-MATH-07-0001"


def test_build_preserves_canonical_objects():
    service = PlanningContextService()
    requirement = service._curriculum.requirement_by_id(
        "YCCD-MATH-08-0001"
    )
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=8,
        curriculum_node_ids=(requirement.curriculum_node_ref,),
        canonical_requirement_ids=("YCCD-MATH-08-0001",),
    )

    context = service.build(scope)

    assert context.requirements[0].provenance
    assert context.requirements[0].validation
    assert context.nodes[0].name


def test_wrong_grade_node_is_rejected():
    service = PlanningContextService()
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=7,
        curriculum_node_ids=("CURR-NODE-MATH-G8-001",),
    )

    with pytest.raises(ValueError):
        service.build(scope)


def test_wrong_grade_requirement_is_rejected():
    service = PlanningContextService()
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=8,
        canonical_requirement_ids=("YCCD-MATH-09-0001",),
    )

    with pytest.raises(ValueError):
        service.build(scope)


def test_missing_canonical_reference_is_rejected():
    service = PlanningContextService()
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=9,
        curriculum_node_ids=("CURR-NODE-MATH-G9-999",),
    )

    with pytest.raises(LookupError):
        service.build(scope)


def test_requirement_outside_selected_nodes_is_rejected():
    service = PlanningContextService()
    requirement = service._curriculum.requirement_by_id(
        "YCCD-MATH-06-0001"
    )
    other_node = next(
        node
        for node in service._curriculum.nodes_for_grade(6)
        if node.curriculum_node_id != requirement.curriculum_node_ref
    )
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=6,
        curriculum_node_ids=(other_node.curriculum_node_id,),
        canonical_requirement_ids=("YCCD-MATH-06-0001",),
    )

    with pytest.raises(ValueError):
        service.build(scope)


def test_invalid_grade_is_rejected():
    service = PlanningContextService()
    scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=10,
    )

    with pytest.raises(ValueError):
        service.build(scope)
