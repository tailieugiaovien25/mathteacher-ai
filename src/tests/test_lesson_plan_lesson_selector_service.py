from datetime import date
from types import SimpleNamespace

import pytest

from lesson_planning_v2.services.lesson_plan_lesson_selector_service import (
    LessonPlanLessonSelectorService,
)


def curriculum(
    *,
    class_id,
    period,
    lesson_id,
    title,
    period_in_lesson,
):
    return SimpleNamespace(
        class_id=class_id,
        period_number=period,
        lesson_id=lesson_id,
        lesson_title=title,
        period_in_lesson=period_in_lesson,
    )


def entry(
    *,
    class_id,
    period,
    teaching_date,
):
    return SimpleNamespace(
        class_id=class_id,
        curriculum_period=period,
        teaching_date=teaching_date,
    )


def schedule(
    schedule_id,
    *entries,
):
    return SimpleNamespace(
        schedule_id=schedule_id,
        entries=entries,
    )


def source_curriculum():
    return (
        curriculum(
            class_id="6A1",
            period=10,
            lesson_id="LESSON-007",
            title=(
                "Bài 7. Thứ tự thực hiện "
                "các phép tính"
            ),
            period_in_lesson=1,
        ),
        curriculum(
            class_id="6A1",
            period=11,
            lesson_id="LESSON-007",
            title=(
                "Bài 7. Thứ tự thực hiện "
                "các phép tính"
            ),
            period_in_lesson=2,
        ),
        curriculum(
            class_id="6A2",
            period=10,
            lesson_id="LESSON-007",
            title=(
                "Bài 7. Thứ tự thực hiện "
                "các phép tính"
            ),
            period_in_lesson=1,
        ),
        curriculum(
            class_id="6A2",
            period=11,
            lesson_id="LESSON-007",
            title=(
                "Bài 7. Thứ tự thực hiện "
                "các phép tính"
            ),
            period_in_lesson=2,
        ),
        curriculum(
            class_id="6A1",
            period=12,
            lesson_id="LESSON-008",
            title="Luyện tập chung",
            period_in_lesson=1,
        ),
    )


def source_schedules():
    return (
        schedule(
            "W05",
            entry(
                class_id="6A1",
                period=10,
                teaching_date=date(
                    2026,
                    10,
                    26,
                ),
            ),
            entry(
                class_id="6A1",
                period=11,
                teaching_date=date(
                    2026,
                    10,
                    28,
                ),
            ),
            entry(
                class_id="6A1",
                period=12,
                teaching_date=date(
                    2026,
                    10,
                    30,
                ),
            ),
        ),
        schedule(
            "W06-PROJECTED",
            entry(
                class_id="6A2",
                period=10,
                teaching_date=date(
                    2026,
                    11,
                    2,
                ),
            ),
            entry(
                class_id="6A2",
                period=11,
                teaching_date=date(
                    2026,
                    11,
                    4,
                ),
            ),
        ),
    )


def test_selector_builds_lesson_level_options():
    options = (
        LessonPlanLessonSelectorService()
        .build_options(
            curriculum_periods=(
                source_curriculum()
            ),
            schedules=(
                source_schedules()
            ),
            projected_schedule_ids=(
                frozenset(
                    {
                        "W06-PROJECTED"
                    }
                )
            ),
        )
    )

    assert len(options) == 2

    assert (
        options[0].lesson_id
        == "LESSON-007"
    )

    assert (
        options[1].lesson_id
        == "LESSON-008"
    )


def test_selector_groups_multi_period_lesson():
    option = (
        LessonPlanLessonSelectorService()
        .get_option(
            lesson_id="LESSON-007",
            curriculum_periods=(
                source_curriculum()
            ),
            schedules=(
                source_schedules()
            ),
            projected_schedule_ids=(
                frozenset(
                    {
                        "W06-PROJECTED"
                    }
                )
            ),
        )
    )

    assert (
        option.curriculum_periods
        == (10, 11)
    )

    assert option.total_periods == 2

    assert (
        option.period_heading
        == "10 + 11"
    )


def test_selector_collects_all_classes():
    option = (
        LessonPlanLessonSelectorService()
        .get_option(
            lesson_id="LESSON-007",
            curriculum_periods=(
                source_curriculum()
            ),
            schedules=(
                source_schedules()
            ),
            projected_schedule_ids=(
                frozenset(
                    {
                        "W06-PROJECTED"
                    }
                )
            ),
        )
    )

    assert option.class_names == (
        "6A1",
        "6A2",
    )


def test_selector_preserves_all_teaching_dates():
    option = (
        LessonPlanLessonSelectorService()
        .get_option(
            lesson_id="LESSON-007",
            curriculum_periods=(
                source_curriculum()
            ),
            schedules=(
                source_schedules()
            ),
            projected_schedule_ids=(
                frozenset(
                    {
                        "W06-PROJECTED"
                    }
                )
            ),
        )
    )

    assert len(
        option.teaching_dates
    ) == 4

    assert {
        (
            item.class_name,
            item.teaching_date,
        )
        for item
        in option.teaching_dates
    } == {
        (
            "6A1",
            date(2026, 10, 26),
        ),
        (
            "6A1",
            date(2026, 10, 28),
        ),
        (
            "6A2",
            date(2026, 11, 2),
        ),
        (
            "6A2",
            date(2026, 11, 4),
        ),
    }


def test_selector_marks_projected_future_schedule():
    option = (
        LessonPlanLessonSelectorService()
        .get_option(
            lesson_id="LESSON-007",
            curriculum_periods=(
                source_curriculum()
            ),
            schedules=(
                source_schedules()
            ),
            projected_schedule_ids=(
                frozenset(
                    {
                        "W06-PROJECTED"
                    }
                )
            ),
        )
    )

    assert option.has_projected_dates

    projected = tuple(
        item
        for item
        in option.teaching_dates
        if item.projected
    )

    assert len(projected) == 2


def test_selector_label_is_teacher_friendly():
    option = (
        LessonPlanLessonSelectorService()
        .get_option(
            lesson_id="LESSON-007",
            curriculum_periods=(
                source_curriculum()
            ),
            schedules=(
                source_schedules()
            ),
            projected_schedule_ids=(
                frozenset(
                    {
                        "W06-PROJECTED"
                    }
                )
            ),
        )
    )

    assert option.selection_label == (
        "Bài 7. Thứ tự thực hiện "
        "các phép tính "
        "(Tiết 10 + 11)"
    )


def test_selector_skips_lesson_without_schedule():
    curriculum_rows = (
        *source_curriculum(),
        curriculum(
            class_id="6A1",
            period=13,
            lesson_id="LESSON-009",
            title="Bài chưa dạy",
            period_in_lesson=1,
        ),
    )

    options = (
        LessonPlanLessonSelectorService()
        .build_options(
            curriculum_periods=(
                curriculum_rows
            ),
            schedules=(
                source_schedules()
            ),
            projected_schedule_ids=(
                frozenset(
                    {
                        "W06-PROJECTED"
                    }
                )
            ),
        )
    )

    assert {
        item.lesson_id
        for item in options
    } == {
        "LESSON-007",
        "LESSON-008",
    }


def test_selector_rejects_unknown_lesson():
    with pytest.raises(
        ValueError,
        match="not found",
    ):
        (
            LessonPlanLessonSelectorService()
            .get_option(
                lesson_id="UNKNOWN",
                curriculum_periods=(
                    source_curriculum()
                ),
                schedules=(
                    source_schedules()
                ),
            )
        )
