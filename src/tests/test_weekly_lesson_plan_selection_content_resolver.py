from datetime import date

import pytest

from lesson_planning_v2.lesson_plan_selection_mode import (
    LessonPlanSelectionMode,
)
from lesson_planning_v2.services.weekly_lesson_plan_selection_content_resolver import (
    WeeklyLessonPlanSelectionContentResolver,
)
from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlanSession,
)


def session(
    *,
    period_number=1,
    curriculum_period=22,
    lesson_title="Lesson 1",
    component_ref=None,
):
    return WeeklyLessonPlanSession(
        period_number=period_number,
        curriculum_period=curriculum_period,
        lesson_title=lesson_title,
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
        class_id="CLASS-6A1",
        component_ref=component_ref,
    )


def test_lesson_mode_can_resolve_by_lesson_unit():
    calls = []

    def lesson_provider(value):
        calls.append(
            value.lesson_title
        )

        return {
            "title": "Lesson unit",
            "objectives": "Objectives",
            "materials": "Materials",
            "teaching_process": "Process",
        }

    resolver = (
        WeeklyLessonPlanSelectionContentResolver(
            lesson_provider=lesson_provider,
            period_provider=None,
            topic_provider=None,
        )
    )

    result = resolver.resolve(
        session=session(
            lesson_title="Lesson 1",
        ),
        mode=(
            LessonPlanSelectionMode.LESSON
        ),
    )

    assert result["title"] == "Lesson unit"

    assert calls == [
        "Lesson 1",
    ]


def test_period_mode_can_resolve_by_period():
    calls = []

    def period_provider(value):
        calls.append(
            value.curriculum_period
        )

        return {
            "title": (
                f"Period "
                f"{value.curriculum_period}"
            ),
            "objectives": "Objectives",
            "materials": "Materials",
            "teaching_process": "Process",
        }

    resolver = (
        WeeklyLessonPlanSelectionContentResolver(
            lesson_provider=None,
            period_provider=period_provider,
            topic_provider=None,
        )
    )

    result = resolver.resolve(
        session=session(
            curriculum_period=23,
        ),
        mode=(
            LessonPlanSelectionMode.PERIOD
        ),
    )

    assert result["title"] == "Period 23"

    assert calls == [
        23,
    ]


def test_topic_mode_can_reuse_same_topic_content():
    shared_topic = {
        "title": "Topic A",
        "objectives": "Topic objectives",
        "materials": "Topic materials",
        "teaching_process": (
            "Topic teaching process"
        ),
    }

    def topic_provider(_value):
        return shared_topic

    resolver = (
        WeeklyLessonPlanSelectionContentResolver(
            lesson_provider=None,
            period_provider=None,
            topic_provider=topic_provider,
        )
    )

    first = resolver.resolve(
        session=session(
            period_number=1,
        ),
        mode=(
            LessonPlanSelectionMode.TOPIC
        ),
    )

    second = resolver.resolve(
        session=session(
            period_number=2,
            curriculum_period=23,
            lesson_title="Lesson 2",
        ),
        mode=(
            LessonPlanSelectionMode.TOPIC
        ),
    )

    assert first == shared_topic
    assert second == shared_topic


def test_lesson_mode_does_not_require_one_period_per_lesson():
    shared_lesson = {
        "title": "Multi-period lesson",
        "objectives": "Objectives",
        "materials": "Materials",
        "teaching_process": "Process",
    }

    def lesson_provider(_value):
        return shared_lesson

    resolver = (
        WeeklyLessonPlanSelectionContentResolver(
            lesson_provider=lesson_provider,
            period_provider=None,
            topic_provider=None,
        )
    )

    first = resolver.resolve(
        session=session(
            period_number=1,
            curriculum_period=22,
        ),
        mode=(
            LessonPlanSelectionMode.LESSON
        ),
    )

    second = resolver.resolve(
        session=session(
            period_number=2,
            curriculum_period=23,
        ),
        mode=(
            LessonPlanSelectionMode.LESSON
        ),
    )

    assert first == shared_lesson
    assert second == shared_lesson


def test_component_ref_is_available_to_provider():
    calls = []

    def period_provider(value):
        calls.append(
            value.component_ref
        )

        return {
            "title": "Component-aware period",
            "objectives": "Objectives",
            "materials": "Materials",
            "teaching_process": "Process",
        }

    resolver = (
        WeeklyLessonPlanSelectionContentResolver(
            lesson_provider=None,
            period_provider=period_provider,
            topic_provider=None,
        )
    )

    resolver.resolve(
        session=session(
            component_ref="COMP-A",
        ),
        mode=(
            LessonPlanSelectionMode.PERIOD
        ),
    )

    assert calls == [
        "COMP-A",
    ]


@pytest.mark.parametrize(
    (
        "mode",
        "provider_name",
    ),
    (
        (
            LessonPlanSelectionMode.LESSON,
            "lesson_provider",
        ),
        (
            LessonPlanSelectionMode.PERIOD,
            "period_provider",
        ),
        (
            LessonPlanSelectionMode.TOPIC,
            "topic_provider",
        ),
    ),
)
def test_missing_provider_is_rejected(
    mode,
    provider_name,
):
    resolver = (
        WeeklyLessonPlanSelectionContentResolver(
            lesson_provider=None,
            period_provider=None,
            topic_provider=None,
        )
    )

    with pytest.raises(
        ValueError,
        match=provider_name,
    ):
        resolver.resolve(
            session=session(),
            mode=mode,
        )


def test_provider_must_return_non_empty_mapping():
    def invalid_provider(_value):
        return {}

    resolver = (
        WeeklyLessonPlanSelectionContentResolver(
            lesson_provider=invalid_provider,
            period_provider=None,
            topic_provider=None,
        )
    )

    with pytest.raises(
        ValueError,
        match="content",
    ):
        resolver.resolve(
            session=session(),
            mode=(
                LessonPlanSelectionMode.LESSON
            ),
        )


def test_provider_returning_none_is_rejected():
    def invalid_provider(_value):
        return None

    resolver = (
        WeeklyLessonPlanSelectionContentResolver(
            lesson_provider=None,
            period_provider=invalid_provider,
            topic_provider=None,
        )
    )

    with pytest.raises(
        ValueError,
        match="content",
    ):
        resolver.resolve(
            session=session(),
            mode=(
                LessonPlanSelectionMode.PERIOD
            ),
        )


def test_week_subject_is_not_a_content_resolution_mode():
    resolver = (
        WeeklyLessonPlanSelectionContentResolver(
            lesson_provider=None,
            period_provider=None,
            topic_provider=None,
        )
    )

    with pytest.raises(
        ValueError,
        match="content selection mode",
    ):
        resolver.resolve(
            session=session(),
            mode=(
                LessonPlanSelectionMode
                .WEEK_SUBJECT
            ),
        )
