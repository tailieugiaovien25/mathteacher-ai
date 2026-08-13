from curriculum_v2.processors.canonical_curriculum_query import (
    CanonicalCurriculumQuery,
)
from curriculum_v2.processors.curriculum_node_query import CurriculumNodeQuery
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
from lesson_planning_v2.tests.test_provider_data_independence_e2e import (
    ProviderBackedCurriculumFacade,
)


CURRICULUM_REF = "CURRICULUM-MATH-2018"
NODE_ID = "CURR-NODE-MATH-G6-004"
REQUIREMENT_ID = "YCCD-MATH-06-0001"


def make_result(query, data, source_id):
    return EducationalDataResult(
        capability=query.capability,
        data=tuple(data),
        provenance=EducationalDataProvenance(
            source_id=source_id,
            authority_type="TEST_CANONICAL",
            source_version="V1",
            status="VERIFIED",
        ),
        version=EducationalDataVersion(version_id="V1"),
    )


def make_json_provider():
    requirement_query = CanonicalCurriculumQuery()
    node_query = CurriculumNodeQuery()

    def handle(query):
        if query.capability == "curriculum_nodes":
            data = node_query.by_grade(int(query.grade_ref))
        else:
            data = requirement_query.by_grade(int(query.grade_ref))
        return make_result(query, data, "JSON-STORAGE")

    return CapabilityEducationalDataProvider(
        handlers={
            "curriculum_nodes": handle,
            "learning_requirements": handle,
        }
    )


def make_in_memory_provider(nodes, requirements):
    data_by_capability = {
        "curriculum_nodes": tuple(nodes),
        "learning_requirements": tuple(requirements),
    }

    def handle(query):
        return make_result(
            query,
            data_by_capability[query.capability],
            "IN-MEMORY-STORAGE",
        )

    return CapabilityEducationalDataProvider(
        handlers={
            "curriculum_nodes": handle,
            "learning_requirements": handle,
        }
    )


def build_lesson_plan(provider, provider_id):
    registry = EducationalDataProviderRegistry()
    registry.register(
        registration=ProviderRegistration(
            provider_id=provider_id,
            capabilities=("curriculum_nodes", "learning_requirements"),
        ),
        provider=provider,
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
        curriculum_ref=CURRICULUM_REF,
        item_drafts=(
            PlanItemDraft(
                title="Tập hợp số tự nhiên",
                periods=1,
                curriculum_node_ids=(NODE_ID,),
                canonical_requirement_ids=(REQUIREMENT_ID,),
            ),
        ),
    )
    plan_item = educational_plan.items[0]
    context = LessonPlanningContextService(
        planning_context_service
    ).build(educational_plan, plan_item)
    return LessonPlanBuilder().build(
        lesson_plan_id=f"LP-{provider_id}",
        context=context,
        draft=LessonPlanDraft(
            objectives=(
                LessonObjective(
                    objective_id=f"OBJ-{provider_id}",
                    objective_type="KNOWLEDGE",
                    statement=context.requirements[0].requirement_text_original,
                    source_requirement_refs=(REQUIREMENT_ID,),
                ),
            ),
            periods=(PeriodPlan(1),),
        ),
    )


def planning_signature(lesson_plan):
    return (
        lesson_plan.title,
        lesson_plan.grade,
        lesson_plan.total_periods,
        lesson_plan.curriculum_node_refs,
        lesson_plan.canonical_requirement_refs,
        tuple(objective.statement for objective in lesson_plan.objectives),
    )


def test_storage_changes_without_changing_the_planning_pipeline():
    json_nodes = CurriculumNodeQuery().by_grade(6)
    json_requirements = CanonicalCurriculumQuery().by_grade(6)

    json_plan = build_lesson_plan(
        make_json_provider(),
        "PROVIDER-JSON",
    )
    in_memory_plan = build_lesson_plan(
        make_in_memory_provider(json_nodes, json_requirements),
        "PROVIDER-IN-MEMORY",
    )

    assert planning_signature(json_plan) == planning_signature(in_memory_plan)
