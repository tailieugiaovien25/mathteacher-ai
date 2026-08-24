from datetime import date

import pytest

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)
from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlan,
    WeeklyLessonPlanApproval,
    WeeklyLessonPlanSession,
)
from lesson_planning_v2.weekly_lesson_plan_identity import (
    WeeklyLessonPlanIdentity,
)


def identity():
    return WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        teaching_scope=(
            LessonPlanTeachingScope.for_class(
                class_id="CLASS-6A1",
            )
        ),
    )


def session(
    *,
    period_number=1,
    curriculum_period=22,
    lesson_title="Lesson 1",
    preparation_date=date(2026, 10, 12),
    teaching_date=date(2026, 10, 13),
    class_id="CLASS-6A1",
    component_ref=None,
):
    return WeeklyLessonPlanSession(
        period_number=period_number,
        curriculum_period=curriculum_period,
        lesson_title=lesson_title,
        preparation_date=preparation_date,
        teaching_date=teaching_date,
        class_id=class_id,
        component_ref=component_ref,
    )


def test_weekly_plan_contains_identity_and_sessions():
    plan = WeeklyLessonPlan(
        identity=identity(),
        sessions=(
            session(
                period_number=1,
                curriculum_period=22,
                lesson_title="Lesson 1",
            ),
            session(
                period_number=2,
                curriculum_period=23,
                lesson_title="Lesson 2",
            ),
            session(
                period_number=3,
                curriculum_period=24,
                lesson_title="Lesson 3",
            ),
        ),
    )

    assert plan.identity.week_number == 8
    assert len(plan.sessions) == 3

    assert tuple(
        value.period_number
        for value in plan.sessions
    ) == (
        1,
        2,
        3,
    )


def test_each_session_has_its_own_dates():
    plan = WeeklyLessonPlan(
        identity=identity(),
        sessions=(
            session(
                period_number=1,
                preparation_date=date(
                    2026,
                    10,
                    12,
                ),
                teaching_date=date(
                    2026,
                    10,
                    13,
                ),
            ),
            session(
                period_number=2,
                preparation_date=date(
                    2026,
                    10,
                    14,
                ),
                teaching_date=date(
                    2026,
                    10,
                    15,
                ),
            ),
        ),
    )

    assert (
        plan.sessions[0].preparation_date
        == date(2026, 10, 12)
    )

    assert (
        plan.sessions[0].teaching_date
        == date(2026, 10, 13)
    )

    assert (
        plan.sessions[1].preparation_date
        == date(2026, 10, 14)
    )

    assert (
        plan.sessions[1].teaching_date
        == date(2026, 10, 15)
    )


def test_session_preserves_class_and_component():
    value = session(
        class_id="CLASS-6A1",
        component_ref="LISTENING",
    )

    assert value.class_id == "CLASS-6A1"
    assert value.component_ref == "LISTENING"


def test_session_preserves_curriculum_period():
    value = session(
        period_number=2,
        curriculum_period=23,
    )

    assert value.period_number == 2
    assert value.curriculum_period == 23


def test_weekly_plan_orders_sessions_by_period():
    plan = WeeklyLessonPlan(
        identity=identity(),
        sessions=(
            session(
                period_number=3,
                lesson_title="Lesson 3",
            ),
            session(
                period_number=1,
                lesson_title="Lesson 1",
            ),
            session(
                period_number=2,
                lesson_title="Lesson 2",
            ),
        ),
    )

    assert tuple(
        value.period_number
        for value in plan.sessions
    ) == (
        1,
        2,
        3,
    )


def test_approval_is_single_weekly_level_object():
    approval = WeeklyLessonPlanApproval(
        approver_role="Tổ chuyên môn",
        placement="end_of_weekly_plan",
    )

    plan = WeeklyLessonPlan(
        identity=identity(),
        sessions=(
            session(),
        ),
        approval=approval,
    )

    assert plan.approval is approval

    assert (
        plan.approval.placement
        == "end_of_weekly_plan"
    )


def test_approval_is_not_required_for_domain_creation():
    plan = WeeklyLessonPlan(
        identity=identity(),
        sessions=(
            session(),
        ),
    )

    assert plan.approval is None


def test_empty_weekly_plan_is_rejected():
    with pytest.raises(
        ValueError,
        match="sessions must not be empty",
    ):
        WeeklyLessonPlan(
            identity=identity(),
            sessions=(),
        )


@pytest.mark.parametrize(
    "period_number",
    (
        0,
        -1,
    ),
)
def test_session_period_number_must_be_positive(
    period_number,
):
    with pytest.raises(
        ValueError,
        match="period_number must be positive",
    ):
        session(
            period_number=period_number,
        )


@pytest.mark.parametrize(
    "curriculum_period",
    (
        0,
        -1,
    ),
)
def test_curriculum_period_must_be_positive(
    curriculum_period,
):
    with pytest.raises(
        ValueError,
        match="curriculum_period must be positive",
    ):
        session(
            curriculum_period=curriculum_period,
        )


def test_blank_lesson_title_is_rejected():
    with pytest.raises(
        ValueError,
        match="lesson_title must not be blank",
    ):
        session(
            lesson_title="   ",
        )


def test_blank_class_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="class_id must not be blank",
    ):
        session(
            class_id="   ",
        )
