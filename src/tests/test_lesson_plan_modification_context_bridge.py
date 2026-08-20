from dataclasses import replace
from datetime import date

import pytest

from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_modification_plan import (
    LessonPlanFieldModification,
    LessonPlanModificationPlan,
)
from educational_planning_v2.models import (
    TeachingSession,
)
from lesson_planning_v2.contexts import (
    ScheduledLessonContext,
)
from lesson_planning_v2.services.lesson_plan_document_processing_service import (
    LessonPlanDocumentProcessingService,
)


def make_context():
    return ScheduledLessonContext(
        teaching_date=date(2026, 9, 8),
        drafting_date=date(2026, 9, 7),
        class_id="8A1",
        subject_ref="MATHEMATICS",
        component_ref="ALGEBRA",
        curriculum_period=1,
        lesson_id="LESSON-001",
        lesson_title="Bài cũ",
        session=TeachingSession.MORNING,
        timetable_period=1,
        period_in_lesson=1,
    )


def make_plan(*modifications):
    return LessonPlanModificationPlan(
        modifications=tuple(
            LessonPlanFieldModification(
                field=field,
                value=value,
            )
            for field, value in modifications
        )
    )


def apply(context, plan):
    return (
        LessonPlanDocumentProcessingService
        .apply_modification_plan(
            context=context,
            modification_plan=plan,
        )
    )


def test_empty_plan_keeps_context_unchanged():
    context = make_context()

    result = apply(
        context,
        LessonPlanModificationPlan(),
    )

    assert result == context


def test_plan_overrides_class_period_and_title():
    context = make_context()

    result = apply(
        context,
        make_plan(
            (
                DocumentField.CLASS_NAME,
                "8A2",
            ),
            (
                DocumentField.CURRICULUM_PERIOD,
                "9",
            ),
            (
                DocumentField.LESSON_TITLE,
                "Đơn thức",
            ),
        ),
    )

    assert result.class_id == "8A2"
    assert result.curriculum_period == 9
    assert result.lesson_title == "Đơn thức"

    assert result.teaching_date == context.teaching_date
    assert result.drafting_date == context.drafting_date
    assert result.subject_ref == context.subject_ref
    assert result.component_ref == context.component_ref
    assert result.lesson_id == context.lesson_id
    assert result.session == context.session
    assert result.timetable_period == context.timetable_period
    assert result.period_in_lesson == context.period_in_lesson


def test_plan_can_override_drafting_date():
    context = make_context()

    result = apply(
        context,
        make_plan(
            (
                DocumentField.DRAFTING_DATE,
                "06/09/2026",
            ),
        ),
    )

    assert result.drafting_date == date(
        2026,
        9,
        6,
    )


def test_plan_can_override_teaching_date():
    context = make_context()

    result = apply(
        context,
        make_plan(
            (
                DocumentField.TEACHING_DATE,
                "09/09/2026",
            ),
        ),
    )

    assert result.teaching_date == date(
        2026,
        9,
        9,
    )


def test_invalid_curriculum_period_is_rejected():
    with pytest.raises(
        ValueError,
        match="curriculum",
    ):
        apply(
            make_context(),
            make_plan(
                (
                    DocumentField.CURRICULUM_PERIOD,
                    "không hợp lệ",
                ),
            ),
        )


def test_invalid_date_is_rejected():
    with pytest.raises(
        ValueError,
        match="date",
    ):
        apply(
            make_context(),
            make_plan(
                (
                    DocumentField.TEACHING_DATE,
                    "không phải ngày",
                ),
            ),
        )


def test_wrong_context_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="ScheduledLessonContext",
    ):
        apply(
            object(),
            LessonPlanModificationPlan(),
        )


def test_wrong_plan_type_is_rejected():
    with pytest.raises(
        TypeError,
        match="LessonPlanModificationPlan",
    ):
        apply(
            make_context(),
            object(),
        )
