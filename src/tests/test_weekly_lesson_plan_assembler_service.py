from dataclasses import dataclass
from datetime import date

import pytest

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)
from lesson_planning_v2.services.weekly_lesson_plan_assembler_service import (
    WeeklyLessonPlanAssemblerService,
)
from lesson_planning_v2.services.weekly_lesson_plan_grouping_service import (
    WeeklyLessonPlanGroup,
)
from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlanApproval,
)
from lesson_planning_v2.weekly_lesson_plan_identity import (
    WeeklyLessonPlanIdentity,
)


@dataclass(frozen=True)
class ScheduleItem:
    teacher_id: str
    academic_year: str
    week_number: int
    subject_ref: str
    class_id: str
    period_number: int
    curriculum_period: int
    lesson_title: str
    teaching_date: date
    component_ref: str | None = None


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


def item(
    *,
    period_number,
    curriculum_period,
    lesson_title,
    teaching_date,
    class_id="CLASS-6A1",
    component_ref=None,
):
    return ScheduleItem(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        class_id=class_id,
        period_number=period_number,
        curriculum_period=curriculum_period,
        lesson_title=lesson_title,
        teaching_date=teaching_date,
        component_ref=component_ref,
    )


def group():
    return WeeklyLessonPlanGroup(
        identity=identity(),
        items=(
            item(
                period_number=1,
                curriculum_period=22,
                lesson_title="Lesson 1",
                teaching_date=date(2026, 10, 13),
                component_ref="COMP-A",
            ),
            item(
                period_number=2,
                curriculum_period=23,
                lesson_title="Lesson 2",
                teaching_date=date(2026, 10, 15),
                component_ref="COMP-B",
            ),
            item(
                period_number=3,
                curriculum_period=24,
                lesson_title="Lesson 3",
                teaching_date=date(2026, 10, 17),
                component_ref="COMP-A",
            ),
        ),
    )


def preparation_date_resolver(schedule_item):
    return date(
        2026,
        10,
        12 + (
            schedule_item.period_number - 1
        ) * 2,
    )


def test_assembler_builds_weekly_plan_from_group():
    service = WeeklyLessonPlanAssemblerService()

    plan = service.assemble(
        group=group(),
        preparation_date_resolver=(
            preparation_date_resolver
        ),
    )

    assert plan.identity == identity()
    assert len(plan.sessions) == 3


def test_assembler_maps_schedule_fields_to_sessions():
    service = WeeklyLessonPlanAssemblerService()

    plan = service.assemble(
        group=group(),
        preparation_date_resolver=(
            preparation_date_resolver
        ),
    )

    assert tuple(
        value.curriculum_period
        for value in plan.sessions
    ) == (
        22,
        23,
        24,
    )

    assert tuple(
        value.lesson_title
        for value in plan.sessions
    ) == (
        "Lesson 1",
        "Lesson 2",
        "Lesson 3",
    )

    assert tuple(
        value.class_id
        for value in plan.sessions
    ) == (
        "CLASS-6A1",
        "CLASS-6A1",
        "CLASS-6A1",
    )


def test_assembler_uses_each_teaching_date():
    service = WeeklyLessonPlanAssemblerService()

    plan = service.assemble(
        group=group(),
        preparation_date_resolver=(
            preparation_date_resolver
        ),
    )

    assert tuple(
        value.teaching_date
        for value in plan.sessions
    ) == (
        date(2026, 10, 13),
        date(2026, 10, 15),
        date(2026, 10, 17),
    )


def test_assembler_uses_preparation_date_resolver():
    service = WeeklyLessonPlanAssemblerService()

    plan = service.assemble(
        group=group(),
        preparation_date_resolver=(
            preparation_date_resolver
        ),
    )

    assert tuple(
        value.preparation_date
        for value in plan.sessions
    ) == (
        date(2026, 10, 12),
        date(2026, 10, 14),
        date(2026, 10, 16),
    )


def test_assembler_preserves_component_ref():
    service = WeeklyLessonPlanAssemblerService()

    plan = service.assemble(
        group=group(),
        preparation_date_resolver=(
            preparation_date_resolver
        ),
    )

    assert tuple(
        value.component_ref
        for value in plan.sessions
    ) == (
        "COMP-A",
        "COMP-B",
        "COMP-A",
    )


def test_assembler_can_attach_weekly_approval():
    service = WeeklyLessonPlanAssemblerService()

    approval = WeeklyLessonPlanApproval(
        approver_role="TO-CHUYEN-MON",
    )

    plan = service.assemble(
        group=group(),
        preparation_date_resolver=(
            preparation_date_resolver
        ),
        approval=approval,
    )

    assert plan.approval is approval


def test_assembler_does_not_create_approval_implicitly():
    service = WeeklyLessonPlanAssemblerService()

    plan = service.assemble(
        group=group(),
        preparation_date_resolver=(
            preparation_date_resolver
        ),
    )

    assert plan.approval is None


def test_missing_curriculum_period_is_rejected():
    service = WeeklyLessonPlanAssemblerService()

    broken = item(
        period_number=1,
        curriculum_period=22,
        lesson_title="Lesson 1",
        teaching_date=date(2026, 10, 13),
    )

    object.__setattr__(
        broken,
        "curriculum_period",
        None,
    )

    invalid_group = WeeklyLessonPlanGroup(
        identity=identity(),
        items=(broken,),
    )

    with pytest.raises(
        ValueError,
        match="curriculum_period",
    ):
        service.assemble(
            group=invalid_group,
            preparation_date_resolver=(
                preparation_date_resolver
            ),
        )


def test_invalid_preparation_date_is_rejected():
    service = WeeklyLessonPlanAssemblerService()

    def invalid_resolver(_item):
        return None

    with pytest.raises(
        ValueError,
        match="preparation_date",
    ):
        service.assemble(
            group=group(),
            preparation_date_resolver=(
                invalid_resolver
            ),
        )


def test_empty_group_is_rejected():
    service = WeeklyLessonPlanAssemblerService()

    empty_group = WeeklyLessonPlanGroup(
        identity=identity(),
        items=(),
    )

    with pytest.raises(
        ValueError,
        match="group items must not be empty",
    ):
        service.assemble(
            group=empty_group,
            preparation_date_resolver=(
                preparation_date_resolver
            ),
        )
