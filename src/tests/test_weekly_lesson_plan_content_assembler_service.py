from datetime import date

import pytest

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)
from lesson_planning_v2.services.weekly_lesson_plan_content_assembler_service import (
    WeeklyLessonPlanContentAssemblerService,
)
from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlan,
    WeeklyLessonPlanApproval,
    WeeklyLessonPlanSession,
)
from lesson_planning_v2.weekly_lesson_plan_content import (
    WeeklyLessonPlanContent,
    WeeklyLessonPlanContentSession,
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
    period_number,
    curriculum_period,
    lesson_title,
    preparation_date,
    teaching_date,
    component_ref=None,
):
    return WeeklyLessonPlanSession(
        period_number=period_number,
        curriculum_period=curriculum_period,
        lesson_title=lesson_title,
        preparation_date=preparation_date,
        teaching_date=teaching_date,
        class_id="CLASS-6A1",
        component_ref=component_ref,
    )


def weekly_plan():
    return WeeklyLessonPlan(
        identity=identity(),
        sessions=(
            session(
                period_number=1,
                curriculum_period=22,
                lesson_title="Lesson 1",
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
                component_ref="COMP-A",
            ),
            session(
                period_number=2,
                curriculum_period=23,
                lesson_title="Lesson 2",
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
                component_ref="COMP-B",
            ),
            session(
                period_number=3,
                curriculum_period=24,
                lesson_title="Lesson 3",
                preparation_date=date(
                    2026,
                    10,
                    16,
                ),
                teaching_date=date(
                    2026,
                    10,
                    17,
                ),
                component_ref="COMP-A",
            ),
        ),
        approval=WeeklyLessonPlanApproval(
            approver_role="TO-CHUYEN-MON",
        ),
    )


def content_resolver(session):
    return {
        "title": session.lesson_title,
        "objectives": (
            f"Objectives for "
            f"{session.lesson_title}"
        ),
        "materials": (
            f"Materials for "
            f"{session.lesson_title}"
        ),
        "teaching_process": (
            f"Teaching process for "
            f"{session.lesson_title}"
        ),
    }


def test_assembler_builds_content_plan():
    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    result = service.assemble(
        weekly_plan=weekly_plan(),
        content_resolver=content_resolver,
    )

    assert isinstance(
        result,
        WeeklyLessonPlanContent,
    )

    assert result.identity == identity()
    assert len(result.sessions) == 3


def test_content_plan_preserves_weekly_approval():
    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    source = weekly_plan()

    result = service.assemble(
        weekly_plan=source,
        content_resolver=content_resolver,
    )

    assert result.approval is source.approval


def test_each_content_session_preserves_metadata():
    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    result = service.assemble(
        weekly_plan=weekly_plan(),
        content_resolver=content_resolver,
    )

    first = result.sessions[0]

    assert isinstance(
        first,
        WeeklyLessonPlanContentSession,
    )

    assert first.period_number == 1
    assert first.curriculum_period == 22

    assert (
        first.preparation_date
        == date(2026, 10, 12)
    )

    assert (
        first.teaching_date
        == date(2026, 10, 13)
    )

    assert first.class_id == "CLASS-6A1"
    assert first.component_ref == "COMP-A"


def test_content_resolver_is_called_for_every_session():
    calls = []

    def resolver(value):
        calls.append(
            value.period_number
        )

        return content_resolver(
            value
        )

    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    result = service.assemble(
        weekly_plan=weekly_plan(),
        content_resolver=resolver,
    )

    assert len(result.sessions) == 3

    assert calls == [
        1,
        2,
        3,
    ]


def test_content_is_preserved_without_word_dependency():
    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    result = service.assemble(
        weekly_plan=weekly_plan(),
        content_resolver=content_resolver,
    )

    first = result.sessions[0]

    assert (
        first.content["objectives"]
        == "Objectives for Lesson 1"
    )

    assert (
        first.content["materials"]
        == "Materials for Lesson 1"
    )

    assert (
        first.content[
            "teaching_process"
        ]
        == "Teaching process for Lesson 1"
    )


def test_resolver_can_reuse_one_content_unit():
    shared_content = {
        "title": "Shared topic",
        "objectives": "Shared objectives",
        "materials": "Shared materials",
        "teaching_process": (
            "Shared teaching process"
        ),
    }

    def resolver(_session):
        return shared_content

    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    result = service.assemble(
        weekly_plan=weekly_plan(),
        content_resolver=resolver,
    )

    assert (
        result.sessions[0].content
        == shared_content
    )

    assert (
        result.sessions[1].content
        == shared_content
    )

    assert (
        result.sessions[2].content
        == shared_content
    )


def test_content_assembler_does_not_require_one_lesson_per_period():
    shared_topic = {
        "title": "Topic A",
        "objectives": "Topic objectives",
        "materials": "Topic materials",
        "teaching_process": (
            "Topic teaching process"
        ),
    }

    def topic_resolver(_session):
        return shared_topic

    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    result = service.assemble(
        weekly_plan=weekly_plan(),
        content_resolver=topic_resolver,
    )

    assert len(result.sessions) == 3

    assert all(
        value.content["title"]
        == "Topic A"
        for value in result.sessions
    )


def test_invalid_content_is_rejected():
    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    def invalid_resolver(_session):
        return None

    with pytest.raises(
        ValueError,
        match="content",
    ):
        service.assemble(
            weekly_plan=weekly_plan(),
            content_resolver=(
                invalid_resolver
            ),
        )


def test_empty_content_mapping_is_rejected():
    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    def empty_resolver(_session):
        return {}

    with pytest.raises(
        ValueError,
        match="content",
    ):
        service.assemble(
            weekly_plan=weekly_plan(),
            content_resolver=(
                empty_resolver
            ),
        )


def test_source_weekly_plan_is_not_mutated():
    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    source = weekly_plan()

    original_sessions = source.sessions

    service.assemble(
        weekly_plan=source,
        content_resolver=content_resolver,
    )

    assert source.sessions is original_sessions


def test_content_plan_orders_sessions_by_period():
    source = WeeklyLessonPlan(
        identity=identity(),
        sessions=(
            session(
                period_number=3,
                curriculum_period=24,
                lesson_title="Lesson 3",
                preparation_date=date(
                    2026,
                    10,
                    16,
                ),
                teaching_date=date(
                    2026,
                    10,
                    17,
                ),
            ),
            session(
                period_number=1,
                curriculum_period=22,
                lesson_title="Lesson 1",
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
                curriculum_period=23,
                lesson_title="Lesson 2",
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

    service = (
        WeeklyLessonPlanContentAssemblerService()
    )

    result = service.assemble(
        weekly_plan=source,
        content_resolver=content_resolver,
    )

    assert tuple(
        value.period_number
        for value in result.sessions
    ) == (
        1,
        2,
        3,
    )
