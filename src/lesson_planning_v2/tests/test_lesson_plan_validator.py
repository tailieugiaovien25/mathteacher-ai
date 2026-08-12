from core_v2.validation.validation_result import ValidationSeverity
from lesson_planning_v2.models import LessonObjective
from lesson_planning_v2.tests._lesson_plan_factory import make_valid_plan
from lesson_planning_v2.validators import LessonPlanValidator


def test_validator_data_type_id():
    assert LessonPlanValidator().data_type_id == "LESSON_PLAN"


def test_valid_plan_returns_valid_core_result():
    result = LessonPlanValidator().validate(make_valid_plan())
    assert result.is_valid
    assert result.issues == ()


def test_invalid_plan_returns_core_validation_issue():
    result = LessonPlanValidator().validate(
        make_valid_plan(total_periods=0)
    )
    assert not result.is_valid
    assert result.has_errors
    assert result.issues[0].severity is ValidationSeverity.ERROR


def test_validator_preserves_rule_code_and_field():
    result = LessonPlanValidator().validate(
        make_valid_plan(plan_mode="UNKNOWN")
    )
    issue = next(
        i for i in result.issues
        if i.code == "LESSON_PLAN_MODE_INVALID"
    )
    assert issue.field == "plan_mode"


def test_validator_reports_requirement_scope_violation():
    objective = LessonObjective(
        objective_id="OBJ-X",
        objective_type="KNOWLEDGE",
        statement="Ngoài scope",
        source_requirement_refs=("YCCD-OUTSIDE",),
    )
    result = LessonPlanValidator().validate(
        make_valid_plan(objectives=(objective,))
    )
    assert any(
        i.code == "LESSON_OBJECTIVE_REQUIREMENT_REF_INVALID"
        for i in result.issues
    )
