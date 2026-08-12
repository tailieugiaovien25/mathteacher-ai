from lesson_planning_v2.models import (
    LearningActivity,
    LessonObjective,
    PeriodPlan,
    TeachingResource,
)
from lesson_planning_v2.rules import validate_lesson_plan_structure
from lesson_planning_v2.tests._lesson_plan_factory import make_valid_plan


def codes(plan):
    return {v.code for v in validate_lesson_plan_structure(plan)}


def test_valid_plan_has_no_violations():
    assert validate_lesson_plan_structure(make_valid_plan()) == ()


def test_invalid_mode():
    assert "LESSON_PLAN_MODE_INVALID" in codes(
        make_valid_plan(plan_mode="UNKNOWN")
    )


def test_total_periods_must_be_positive():
    assert "LESSON_PLAN_TOTAL_PERIODS_INVALID" in codes(
        make_valid_plan(total_periods=0)
    )


def test_full_lesson_must_not_select_period():
    assert "LESSON_PLAN_PERIOD_INVALID" in codes(
        make_valid_plan(period_in_lesson=1)
    )


def test_single_period_requires_valid_selected_period():
    assert "LESSON_PLAN_PERIOD_INVALID" in codes(
        make_valid_plan(
            plan_mode="SINGLE_PERIOD",
            total_periods=2,
            period_in_lesson=3,
        )
    )


def test_period_numbers_must_be_unique():
    p = PeriodPlan(1)
    assert "LESSON_PERIOD_DUPLICATE" in codes(
        make_valid_plan(periods=(p, p))
    )


def test_objective_ids_must_be_unique():
    o = make_valid_plan().objectives[0]
    assert "LESSON_OBJECTIVE_ID_DUPLICATE" in codes(
        make_valid_plan(objectives=(o, o))
    )


def test_resource_ids_must_be_unique():
    r = make_valid_plan().resources[0]
    assert "LESSON_RESOURCE_ID_DUPLICATE" in codes(
        make_valid_plan(resources=(r, r))
    )


def test_activity_ids_must_be_unique_across_plan():
    a = make_valid_plan().periods[0].activities[0]
    assert "LESSON_ACTIVITY_ID_DUPLICATE" in codes(
        make_valid_plan(
            total_periods=2,
            periods=(PeriodPlan(1, (a,)), PeriodPlan(2, (a,))),
        )
    )


def test_activity_order_must_be_unique_within_period():
    a1 = make_valid_plan().periods[0].activities[0]
    a2 = LearningActivity(
        activity_id="ACT-002",
        title="Luyện tập",
        activity_type="LEARNING",
        order=1,
    )
    assert "LESSON_ACTIVITY_ORDER_DUPLICATE" in codes(
        make_valid_plan(periods=(PeriodPlan(1, (a1, a2)),))
    )


def test_activity_objective_ref_must_exist():
    a = LearningActivity(
        activity_id="ACT-002",
        title="Sai tham chiếu",
        activity_type="LEARNING",
        order=1,
        objective_refs=("OBJ-NOT-FOUND",),
    )
    assert "LESSON_ACTIVITY_OBJECTIVE_REF_INVALID" in codes(
        make_valid_plan(periods=(PeriodPlan(1, (a,)),))
    )


def test_activity_resource_ref_must_exist():
    a = LearningActivity(
        activity_id="ACT-002",
        title="Sai tham chiếu",
        activity_type="LEARNING",
        order=1,
        resource_refs=("RES-NOT-FOUND",),
    )
    assert "LESSON_ACTIVITY_RESOURCE_REF_INVALID" in codes(
        make_valid_plan(periods=(PeriodPlan(1, (a,)),))
    )


def test_objective_requirement_ref_must_be_in_plan_scope():
    o = LessonObjective(
        objective_id="OBJ-002",
        objective_type="KNOWLEDGE",
        statement="Mục tiêu ngoài scope",
        source_requirement_refs=("YCCD-OUTSIDE",),
    )
    assert "LESSON_OBJECTIVE_REQUIREMENT_REF_INVALID" in codes(
        make_valid_plan(objectives=(o,))
    )
