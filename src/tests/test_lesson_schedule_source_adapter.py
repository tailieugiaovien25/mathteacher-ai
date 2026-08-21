from datetime import date
from types import SimpleNamespace

from lesson_planning_v2.services.lesson_schedule_source_adapter import (
    LessonScheduleSourceAdapter,
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
        period_in_lesson=(
            period_in_lesson
        ),
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


def test_adapter_joins_schedule_to_ppct_by_class_and_period():
    source = (
        LessonScheduleSourceAdapter()
        .adapt(
            curriculum_periods=(
                curriculum(
                    class_id="6A1",
                    period=10,
                    lesson_id="LESSON-007",
                    title="Bài 7",
                    period_in_lesson=1,
                ),
                curriculum(
                    class_id="6A1",
                    period=11,
                    lesson_id="LESSON-007",
                    title="Bài 7",
                    period_in_lesson=2,
                ),
            ),
            schedules=(
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
                ),
            ),
        )
    )

    assert len(
        source.curriculum_rows
    ) == 2

    assert len(
        source.schedule_rows
    ) == 2

    assert {
        row.lesson_id
        for row in source.schedule_rows
    } == {
        "LESSON-007"
    }


def test_adapter_uses_ppct_lesson_id_not_schedule_text():
    result = (
        LessonScheduleSourceAdapter()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_periods=(
                curriculum(
                    class_id="6A1",
                    period=10,
                    lesson_id="LESSON-007",
                    title=(
                        "Bài 7. Thứ tự "
                        "thực hiện phép tính"
                    ),
                    period_in_lesson=1,
                ),
            ),
            schedules=(
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
                ),
            ),
        )
    )

    assert (
        result.lesson_id
        == "LESSON-007"
    )

    assert (
        result.lesson_title
        == "Bài 7. Thứ tự "
           "thực hiện phép tính"
    )


def test_adapter_collects_same_lesson_from_multiple_classes():
    result = (
        LessonScheduleSourceAdapter()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_periods=(
                curriculum(
                    class_id="6A1",
                    period=10,
                    lesson_id="LESSON-007",
                    title="Bài 7",
                    period_in_lesson=1,
                ),
                curriculum(
                    class_id="6A2",
                    period=10,
                    lesson_id="LESSON-007",
                    title="Bài 7",
                    period_in_lesson=1,
                ),
            ),
            schedules=(
                schedule(
                    "W05",
                    entry(
                        class_id="6A1",
                        period=10,
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
                ),
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

    assert result.class_names == (
        "6A1",
        "6A2",
    )

    assert len(
        result.teaching_occurrences
    ) == 2

    assert (
        result.teaching_occurrences[1]
        .projected
        is True
    )


def test_adapter_groups_two_period_lesson():
    result = (
        LessonScheduleSourceAdapter()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_periods=(
                curriculum(
                    class_id="6A1",
                    period=10,
                    lesson_id="LESSON-007",
                    title="Bài 7",
                    period_in_lesson=1,
                ),
                curriculum(
                    class_id="6A1",
                    period=11,
                    lesson_id="LESSON-007",
                    title="Bài 7",
                    period_in_lesson=2,
                ),
            ),
            schedules=(
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
                ),
            ),
        )
    )

    assert (
        result.curriculum_periods
        == (10, 11)
    )

    assert result.total_periods == 2


def test_schedule_row_without_matching_ppct_is_ignored():
    result = (
        LessonScheduleSourceAdapter()
        .aggregate(
            lesson_id="LESSON-007",
            curriculum_periods=(
                curriculum(
                    class_id="6A1",
                    period=10,
                    lesson_id="LESSON-007",
                    title="Bài 7",
                    period_in_lesson=1,
                ),
            ),
            schedules=(
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
                        class_id="OTHER",
                        period=99,
                        teaching_date=date(
                            2026,
                            10,
                            27,
                        ),
                    ),
                ),
            ),
        )
    )

    assert result.class_names == (
        "6A1",
    )
