from core_v2.validation.validation_result import ValidationResult
from lesson_planning_v2.lesson_planning import (
    LessonPlanningFacade,
    get_lesson_planning,
)


class FakeContextService:
    def __init__(self):
        self.calls = []

    def build(self, plan, item):
        self.calls.append((plan, item))
        return "CONTEXT"


class FakeBuilder:
    def __init__(self):
        self.calls = []

    def build(self, **kwargs):
        self.calls.append(kwargs)
        return "LESSON_PLAN"


class FakeValidator:
    def __init__(self):
        self.calls = []

    def validate(self, plan):
        self.calls.append(plan)
        return ValidationResult.pass_result()


def make_facade():
    context_service = FakeContextService()
    builder = FakeBuilder()
    validator = FakeValidator()
    facade = LessonPlanningFacade(
        context_service=context_service,
        builder=builder,
        validator=validator,
    )
    return facade, context_service, builder, validator


def test_build_context_delegates_to_context_service():
    facade, context_service, _, _ = make_facade()

    result = facade.build_context("PLAN", "ITEM")

    assert result == "CONTEXT"
    assert context_service.calls == [("PLAN", "ITEM")]


def test_build_plan_delegates_to_builder():
    facade, _, builder, _ = make_facade()

    result = facade.build_plan(
        lesson_plan_id="LP-001",
        context="CONTEXT",
        draft="DRAFT",
    )

    assert result == "LESSON_PLAN"
    assert builder.calls == [{
        "lesson_plan_id": "LP-001",
        "context": "CONTEXT",
        "draft": "DRAFT",
    }]


def test_validate_plan_delegates_to_validator():
    facade, _, _, validator = make_facade()

    result = facade.validate_plan("PLAN")

    assert result.is_valid
    assert validator.calls == ["PLAN"]


def test_facade_keeps_application_operations_separate():
    facade, context_service, builder, validator = make_facade()

    facade.build_context("PLAN", "ITEM")
    facade.build_plan(
        lesson_plan_id="LP-001",
        context="CONTEXT",
        draft="DRAFT",
    )
    facade.validate_plan("LESSON_PLAN")

    assert len(context_service.calls) == 1
    assert len(builder.calls) == 1
    assert len(validator.calls) == 1


def test_get_lesson_planning_returns_shared_facade():
    first = get_lesson_planning()
    second = get_lesson_planning()

    assert first is second
    assert isinstance(first, LessonPlanningFacade)


def test_default_facade_can_be_constructed():
    facade = LessonPlanningFacade()

    assert facade is not None


def test_injected_context_service_does_not_require_curriculum_access():
    facade, context_service, _, _ = make_facade()

    facade.build_context("PLAN", "ITEM")

    assert context_service.calls == [("PLAN", "ITEM")]
