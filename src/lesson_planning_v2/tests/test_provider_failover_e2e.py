import pytest

from curriculum_v2.providers import (
    CapabilityEducationalDataProvider,
    EducationalDataProviderFailoverService,
    EducationalDataProviderRegistry,
    EducationalDataProviderUnavailableError,
)
from curriculum_v2.providers.contracts import (
    EducationalDataQuery,
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
from lesson_planning_v2.tests.test_storage_independence_e2e import (
    make_json_provider,
)


CAPABILITIES = ("curriculum_nodes", "learning_requirements")


def unavailable_provider():
    def handle(_query):
        raise EducationalDataProviderUnavailableError(
            "primary source is unavailable"
        )

    return CapabilityEducationalDataProvider(
        handlers={capability: handle for capability in CAPABILITIES}
    )


def registry_with(primary, fallback):
    registry = EducationalDataProviderRegistry()
    registry.register(
        registration=ProviderRegistration(
            provider_id="PROVIDER-PRIMARY",
            capabilities=CAPABILITIES,
            priority=10,
        ),
        provider=primary,
    )
    registry.register(
        registration=ProviderRegistration(
            provider_id="PROVIDER-FALLBACK",
            capabilities=CAPABILITIES,
            priority=20,
        ),
        provider=fallback,
    )
    return registry


def test_unavailable_primary_fails_over_through_the_planning_pipeline():
    failover = EducationalDataProviderFailoverService(
        registry_with(unavailable_provider(), make_json_provider())
    )
    planning_context_service = PlanningContextService(
        curriculum=ProviderBackedCurriculumFacade(failover, grade=6)
    )
    educational_plan = EducationalPlanBuilder(
        validator=EducationalPlanValidator(
            context_service=planning_context_service
        )
    ).build(
        educational_plan_id="EP-FAILOVER",
        academic_year="2026-2027",
        subject="Mathematics",
        grade=6,
        curriculum_ref="CURRICULUM-MATH-2018",
        item_drafts=(
            PlanItemDraft(
                title="Tập hợp số tự nhiên",
                periods=1,
                curriculum_node_ids=("CURR-NODE-MATH-G6-004",),
                canonical_requirement_ids=("YCCD-MATH-06-0001",),
            ),
        ),
    )
    item = educational_plan.items[0]
    context = LessonPlanningContextService(
        planning_context_service
    ).build(educational_plan, item)
    lesson_plan = LessonPlanBuilder().build(
        lesson_plan_id="LP-FAILOVER",
        context=context,
        draft=LessonPlanDraft(
            objectives=(
                LessonObjective(
                    objective_id="OBJ-FAILOVER",
                    objective_type="KNOWLEDGE",
                    statement=context.requirements[0].requirement_text_original,
                    source_requirement_refs=("YCCD-MATH-06-0001",),
                ),
            ),
            periods=(PeriodPlan(1),),
        ),
    )

    assert lesson_plan.curriculum_node_refs == (
        "CURR-NODE-MATH-G6-004",
    )
    assert lesson_plan.canonical_requirement_refs == (
        "YCCD-MATH-06-0001",
    )


def test_failover_does_not_hide_non_availability_errors():
    def invalid_data(_query):
        raise ValueError("invalid canonical data")

    invalid_provider = CapabilityEducationalDataProvider(
        handlers={capability: invalid_data for capability in CAPABILITIES}
    )
    failover = EducationalDataProviderFailoverService(
        registry_with(invalid_provider, make_json_provider())
    )

    with pytest.raises(ValueError, match="invalid canonical data"):
        failover.query(
            EducationalDataQuery(capability="learning_requirements")
        )


def test_failover_reports_when_all_candidates_are_unavailable():
    failover = EducationalDataProviderFailoverService(
        registry_with(unavailable_provider(), unavailable_provider())
    )

    with pytest.raises(
        EducationalDataProviderUnavailableError,
        match="PROVIDER-PRIMARY, PROVIDER-FALLBACK",
    ):
        failover.query(
            EducationalDataQuery(capability="learning_requirements")
        )
