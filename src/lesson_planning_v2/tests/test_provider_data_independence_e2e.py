import pytest

from curriculum_v2.models import CanonicalLearningRequirement
from curriculum_v2.models.canonical_learning_requirement import (
    RequirementProvenance,
    RequirementValidation,
)
from curriculum_v2.models.curriculum_node import CurriculumNode
from curriculum_v2.providers import (
    CapabilityEducationalDataProvider,
    EducationalDataProviderRegistry,
)
from curriculum_v2.providers.contracts import (
    EducationalDataProvenance,
    EducationalDataQuery,
    EducationalDataResult,
    EducationalDataVersion,
    ProviderRegistration,
)
from educational_planning_v2.builders import (
    EducationalPlanBuilder,
    PlanItemDraft,
)
from educational_planning_v2.services import PlanningContextService
from educational_planning_v2.validators import EducationalPlanValidator
from lesson_planning_v2.builders import LessonPlanBuilder, LessonPlanDraft
from lesson_planning_v2.models import LessonObjective, PeriodPlan
from lesson_planning_v2.services import LessonPlanningContextService


class ProviderBackedCurriculumFacade:
    """Test adapter from the provider boundary to the canonical facade API."""

    def __init__(self, provider, *, grade):
        self._provider = provider
        self._grade = grade

    def node_by_id(self, node_id):
        return self._find("curriculum_nodes", "curriculum_node_id", node_id)

    def requirement_by_id(self, requirement_id):
        return self._find(
            "learning_requirements",
            "canonical_id",
            requirement_id,
        )

    def _find(self, capability, identity_field, identity):
        result = self._provider.query(
            EducationalDataQuery(
                capability=capability,
                curriculum_ref="CURRICULUM-MATH-2018",
                subject_ref="MATHEMATICS",
                grade_ref=str(self._grade),
            )
        )
        return next(
            (
                item
                for item in result.data
                if getattr(item, identity_field) == identity
            ),
            None,
        )


def make_provider(provider_id, node, requirement):
    data_by_capability = {
        "curriculum_nodes": (node,),
        "learning_requirements": (requirement,),
    }

    def handle(query):
        return EducationalDataResult(
            capability=query.capability,
            data=data_by_capability[query.capability],
            provenance=EducationalDataProvenance(
                source_id=provider_id,
                authority_type="TEST_CANONICAL",
                source_version="V1",
                status="VERIFIED",
            ),
            version=EducationalDataVersion(version_id="V1"),
        )

    return CapabilityEducationalDataProvider(
        handlers={
            "curriculum_nodes": handle,
            "learning_requirements": handle,
        }
    )


def make_dataset(*, node_id, requirement_id, title, requirement_text):
    node = CurriculumNode(
        curriculum_node_id=node_id,
        curriculum_ref="CURRICULUM-MATH-2018",
        code=node_id,
        name=title,
        node_type="LESSON",
    )
    requirement = CanonicalLearningRequirement(
        canonical_id=requirement_id,
        curriculum_ref="CURRICULUM-MATH-2018",
        curriculum_node_ref=node_id,
        requirement_text_original=requirement_text,
        provenance=RequirementProvenance(
            legal_authority="TEST AUTHORITY",
            regulation_id="TEST REGULATION",
            source_document_id="TEST DOCUMENT",
        ),
        validation=RequirementValidation(
            text_integrity="VERIFIED",
            structural_integrity="VERIFIED",
            provenance_integrity="VERIFIED",
            identity_integrity="VERIFIED",
        ),
        status="ACTIVE",
    )
    return node, requirement


@pytest.mark.parametrize(
    ("provider_id", "node_id", "requirement_id", "title", "requirement_text"),
    (
        (
            "PROVIDER-SOURCE-A",
            "CURR-NODE-MATH-G6-901",
            "YCCD-MATH-06-0901",
            "Dữ liệu nguồn A",
            "Yêu cầu cần đạt từ nguồn A.",
        ),
        (
            "PROVIDER-SOURCE-B",
            "CURR-NODE-MATH-G6-902",
            "YCCD-MATH-06-0902",
            "Dữ liệu nguồn B",
            "Yêu cầu cần đạt từ nguồn B.",
        ),
    ),
)
def test_provider_changes_without_changing_the_planning_pipeline(
    provider_id,
    node_id,
    requirement_id,
    title,
    requirement_text,
):
    node, requirement = make_dataset(
        node_id=node_id,
        requirement_id=requirement_id,
        title=title,
        requirement_text=requirement_text,
    )
    registry = EducationalDataProviderRegistry()
    registry.register(
        registration=ProviderRegistration(
            provider_id=provider_id,
            capabilities=("curriculum_nodes", "learning_requirements"),
        ),
        provider=make_provider(provider_id, node, requirement),
    )
    selected_provider = registry.resolve(
        capability="learning_requirements"
    ).provider
    planning_context_service = PlanningContextService(
        curriculum=ProviderBackedCurriculumFacade(
            selected_provider,
            grade=6,
        )
    )

    educational_plan = EducationalPlanBuilder(
        validator=EducationalPlanValidator(
            context_service=planning_context_service
        )
    ).build(
        educational_plan_id=f"EP-{provider_id}",
        academic_year="2026-2027",
        subject="Mathematics",
        grade=6,
        curriculum_ref="CURRICULUM-MATH-2018",
        item_drafts=(
            PlanItemDraft(
                title=title,
                periods=1,
                curriculum_node_ids=(node_id,),
                canonical_requirement_ids=(requirement_id,),
            ),
        ),
    )
    plan_item = educational_plan.items[0]
    context = LessonPlanningContextService(
        planning_context_service
    ).build(educational_plan, plan_item)
    lesson_plan = LessonPlanBuilder().build(
        lesson_plan_id=f"LP-{provider_id}",
        context=context,
        draft=LessonPlanDraft(
            objectives=(
                LessonObjective(
                    objective_id=f"OBJ-{provider_id}",
                    objective_type="KNOWLEDGE",
                    statement=context.requirements[0].requirement_text_original,
                    source_requirement_refs=(requirement_id,),
                ),
            ),
            periods=(PeriodPlan(1),),
        ),
    )

    assert lesson_plan.title == title
    assert lesson_plan.curriculum_node_refs == (node_id,)
    assert lesson_plan.canonical_requirement_refs == (requirement_id,)
    assert lesson_plan.objectives[0].statement == requirement_text
