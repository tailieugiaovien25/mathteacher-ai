from dataclasses import FrozenInstanceError

import pytest

from curriculum_v2.models.canonical_learning_requirement import (
    CanonicalLearningRequirement,
    RequirementProvenance,
    RequirementValidation,
)
from curriculum_v2.models.curriculum_node import CurriculumNode
from educational_planning_v2.models import (
    CurriculumScope,
    EducationalPlan,
    EducationalPlanItem,
)
from educational_planning_v2.services.planning_context_service import (
    PlanningContext,
)
from lesson_planning_v2.services import LessonPlanningContextService


class FakePlanningContextService:
    def __init__(self, context):
        self.context = context
        self.received_scope = None

    def build(self, scope):
        self.received_scope = scope
        return self.context


def make_requirement():
    return CanonicalLearningRequirement(
        canonical_id="YCCD-MATH-06-0001",
        curriculum_ref="CTGDPT-2018-MATH",
        curriculum_node_ref="CURR-NODE-MATH-G6-001",
        requirement_text_original="Yêu cầu cần đạt thử nghiệm.",
        provenance=RequirementProvenance(
            legal_authority="MOET",
            regulation_id="TEST-REGULATION",
            source_document_id="TEST-DOCUMENT",
        ),
        validation=RequirementValidation(
            text_integrity="VERIFIED",
            structural_integrity="VERIFIED",
            provenance_integrity="VERIFIED",
            identity_integrity="VERIFIED",
        ),
        status="ACTIVE",
    )


def make_node():
    return CurriculumNode(
        curriculum_node_id="CURR-NODE-MATH-G6-001",
        curriculum_ref="CTGDPT-2018-MATH",
        code="MATH6-001",
        name="Nút chương trình thử nghiệm",
        node_type="LESSON",
    )


def make_scope():
    return CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=6,
        curriculum_node_ids=("CURR-NODE-MATH-G6-001",),
        canonical_requirement_ids=("YCCD-MATH-06-0001",),
    )


def make_item(scope=None, item_id="ITEM-001"):
    return EducationalPlanItem(
        plan_item_id=item_id,
        title="Bài học thử nghiệm",
        curriculum_scope=scope or make_scope(),
        periods=2,
        sequence=1,
    )


def make_plan(item=None):
    item = item or make_item()
    return EducationalPlan(
        educational_plan_id="EP-001",
        academic_year="2026-2027",
        subject="Mathematics",
        grade=6,
        items=(item,),
    )


def make_service(scope=None):
    scope = scope or make_scope()
    context = PlanningContext(
        scope=scope,
        nodes=(make_node(),),
        requirements=(make_requirement(),),
    )
    fake = FakePlanningContextService(context)
    return LessonPlanningContextService(fake), fake


def test_build_preserves_educational_plan_identity():
    item = make_item()
    plan = make_plan(item)
    service, _ = make_service(item.curriculum_scope)

    context = service.build(plan, item)

    assert context.educational_plan_id == "EP-001"
    assert context.plan_item_id == "ITEM-001"


def test_build_preserves_planning_metadata():
    item = make_item()
    plan = make_plan(item)
    service, _ = make_service(item.curriculum_scope)

    context = service.build(plan, item)

    assert context.academic_year == "2026-2027"
    assert context.subject == "Mathematics"
    assert context.grade == 6
    assert context.periods == 2
    assert context.title == "Bài học thử nghiệm"


def test_build_reuses_resolved_planning_context():
    item = make_item()
    plan = make_plan(item)
    service, fake = make_service(item.curriculum_scope)

    context = service.build(plan, item)

    assert fake.received_scope is item.curriculum_scope
    assert context.curriculum_scope is fake.context.scope
    assert context.nodes is fake.context.nodes
    assert context.requirements is fake.context.requirements


def test_context_contains_canonical_node():
    item = make_item()
    plan = make_plan(item)
    service, _ = make_service(item.curriculum_scope)

    context = service.build(plan, item)

    assert context.nodes[0].curriculum_node_id == "CURR-NODE-MATH-G6-001"


def test_context_contains_canonical_requirement():
    item = make_item()
    plan = make_plan(item)
    service, _ = make_service(item.curriculum_scope)

    context = service.build(plan, item)

    assert context.requirements[0].canonical_id == "YCCD-MATH-06-0001"


def test_item_must_belong_to_plan():
    item = make_item()
    other_item = make_item(item_id="ITEM-OTHER")
    plan = make_plan(other_item)
    service, _ = make_service(item.curriculum_scope)

    with pytest.raises(ValueError, match="must belong"):
        service.build(plan, item)


def test_scope_grade_must_match_plan_grade():
    bad_scope = CurriculumScope(
        curriculum_ref="CTGDPT-2018-MATH",
        grade=7,
    )
    item = make_item(scope=bad_scope)
    plan = EducationalPlan(
        educational_plan_id="EP-001",
        academic_year="2026-2027",
        subject="Mathematics",
        grade=6,
        items=(item,),
    )
    service, _ = make_service(bad_scope)

    with pytest.raises(ValueError, match="grade must match"):
        service.build(plan, item)


def test_context_is_frozen():
    item = make_item()
    plan = make_plan(item)
    service, _ = make_service(item.curriculum_scope)
    context = service.build(plan, item)

    with pytest.raises(FrozenInstanceError):
        context.title = "Changed"


def test_service_does_not_need_direct_curriculum_facade():
    item = make_item()
    plan = make_plan(item)
    service, fake = make_service(item.curriculum_scope)

    service.build(plan, item)

    assert fake.received_scope is item.curriculum_scope
