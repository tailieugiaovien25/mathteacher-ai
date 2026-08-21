from datetime import date

import pytest

from lesson_planning_v2.services.lesson_schedule_aggregator import (
    LessonCurriculumPeriod,
    LessonScheduleAggregator,
    ScheduledLessonPeriod,
)


def curriculum_rows():
    return (
        LessonCurriculumPeriod(
            lesson_id="LESSON-007",
            lesson_title=(
                "Bài 7. Thứ tự thực hiện "
                "các phép tính"
            ),
            curriculum_period=10,
            period_in_lesson=1,
            total_periods=2,
        ),
        LessonCurriculumPeriod(
            lesson_id="LESSON-007",
            lesson_title=(
                "Bài 7. Thứ tự thực hiện "
                "các phép tính"
            ),
            curriculum_period=11,
            period_in_lesson=2,
            total_periods=2,
        ),
        LessonCurriculumPeriod(
            lesson_id="LESSON-008",
            lesson_title="Luyện tập chung",
            curriculum_period=12,
            period_in_lesson=1,
            total_periods=1,
        ),
    )


def test_aggregator_selects_whole_lesson():
    result = (
        LessonScheduleAggregator()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_rows=(
                curriculum_rows()
            ),
            schedule_rows=(
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=10,
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=11,
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        28,
                    ),
                ),
                ScheduledLessonPeriod(
                    lesson_id="LESSON-008",
                    curriculum_period=12,
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        30,
                    ),
                ),
            ),
        )
    )

    assert (
        result.lesson_id
        == "LESSON-007"
    )

    assert (
        result.curriculum_periods
        == (10, 11)
    )

    assert result.total_periods == 2


def test_aggregator_collects_all_classes():
    result = (
        LessonScheduleAggregator()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_rows=(
                curriculum_rows()
            ),
            schedule_rows=(
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=10,
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=10,
                    class_name="6A2",
                    teaching_date=date(
                        2026,
                        10,
                        27,
                    ),
                ),
            ),
        )
    )

    assert result.class_names == (
        "6A1",
        "6A2",
    )


def test_aggregator_keeps_next_week_class_date():
    result = (
        LessonScheduleAggregator()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_rows=(
                curriculum_rows()
            ),
            schedule_rows=(
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=10,
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        30,
                    ),
                ),
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=10,
                    class_name="6A2",
                    teaching_date=date(
                        2026,
                        11,
                        2,
                    ),
                    projected=True,
                ),
            ),
        )
    )

    assert (
        result.teaching_occurrences[0]
        .class_name
        == "6A1"
    )

    assert (
        result.teaching_occurrences[1]
        .class_name
        == "6A2"
    )

    assert (
        result.teaching_occurrences[1]
        .teaching_date
        == date(
            2026,
            11,
            2,
        )
    )

    assert result.has_projected_dates


def test_aggregator_preserves_multiple_dates_for_same_class():
    result = (
        LessonScheduleAggregator()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_rows=(
                curriculum_rows()
            ),
            schedule_rows=(
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=10,
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=11,
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        28,
                    ),
                ),
            ),
        )
    )

    assert len(
        result.teaching_occurrences
    ) == 2

    assert {
        occurrence.teaching_date
        for occurrence
        in result.teaching_occurrences
    } == {
        date(2026, 10, 26),
        date(2026, 10, 28),
    }


def test_same_class_same_date_is_not_duplicated():
    result = (
        LessonScheduleAggregator()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_rows=(
                curriculum_rows()
            ),
            schedule_rows=(
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=10,
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=11,
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
            ),
        )
    )

    assert len(
        result.teaching_occurrences
    ) == 1


def test_confirmed_duplicate_wins_over_projected():
    result = (
        LessonScheduleAggregator()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_rows=(
                curriculum_rows()
            ),
            schedule_rows=(
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=10,
                    class_name="6A2",
                    teaching_date=date(
                        2026,
                        11,
                        2,
                    ),
                    projected=True,
                ),
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=10,
                    class_name="6A2",
                    teaching_date=date(
                        2026,
                        11,
                        2,
                    ),
                    projected=False,
                ),
            ),
        )
    )

    assert (
        len(
            result.teaching_occurrences
        )
        == 1
    )

    assert (
        result.teaching_occurrences[0]
        .projected
        is False
    )

    assert (
        result.has_projected_dates
        is False
    )


def test_lesson_title_comes_from_curriculum():
    result = (
        LessonScheduleAggregator()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_rows=(
                curriculum_rows()
            ),
            schedule_rows=(
                ScheduledLessonPeriod(
                    lesson_id="LESSON-007",
                    curriculum_period=10,
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
            ),
        )
    )

    assert result.lesson_title == (
        "Bài 7. Thứ tự thực hiện "
        "các phép tính"
    )


def test_missing_lesson_in_curriculum_is_rejected():
    with pytest.raises(
        ValueError,
        match="not found",
    ):
        (
            LessonScheduleAggregator()
            .aggregate(
                lesson_id="UNKNOWN",
                curriculum_rows=(
                    curriculum_rows()
                ),
                schedule_rows=(),
            )
        )


def test_lesson_without_schedule_is_rejected():
    with pytest.raises(
        ValueError,
        match="no teaching schedule",
    ):
        (
            LessonScheduleAggregator()
            .aggregate(
                lesson_id="LESSON-007",
                curriculum_rows=(
                    curriculum_rows()
                ),
                schedule_rows=(),
            )
        )


def test_incomplete_curriculum_lesson_is_rejected():
    incomplete = (
        LessonCurriculumPeriod(
            lesson_id="LESSON-007",
            lesson_title="Bài 7",
            curriculum_period=10,
            period_in_lesson=1,
            total_periods=2,
        ),
    )

    with pytest.raises(
        ValueError,
        match="incomplete",
    ):
        (
            LessonScheduleAggregator()
            .aggregate(
                lesson_id="LESSON-007",
                curriculum_rows=(
                    incomplete
                ),
                schedule_rows=(
                    ScheduledLessonPeriod(
                        lesson_id=(
                            "LESSON-007"
                        ),
                        curriculum_period=10,
                        class_name="6A1",
                        teaching_date=date(
                            2026,
                            10,
                            26,
                        ),
                    ),
                ),
            )
        )
