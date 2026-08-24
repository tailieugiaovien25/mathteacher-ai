from datetime import date
from types import SimpleNamespace

from lesson_planning_v2.services.lesson_plan_unit_selector_service import (
    LessonPlanSelectionMode,
    LessonPlanUnitSelectorService,
)


def row(
    *,
    period,
    title,
    class_id,
    teaching_date,
    lesson_id="",
    topic_id="",
    topic_title="",
    subject_ref="SUBJECT-MATH-6",
    component_ref=None,
):
    return SimpleNamespace(
        curriculum_period=period,
        lesson_title=title,
        class_id=class_id,
        teaching_date=teaching_date,
        lesson_id=lesson_id,
        topic_id=topic_id,
        topic_title=topic_title,
        subject_ref=subject_ref,
        component_ref=component_ref,
    )


def rows():
    return (
        row(
            period=10,
            title="Bài 7",
            class_id="6A1",
            teaching_date=date(
                2026,
                9,
                10,
            ),
            lesson_id="LESSON-007",
            topic_id="TOPIC-01",
            topic_title="Số tự nhiên",
        ),
        row(
            period=11,
            title="Bài 7",
            class_id="6A1",
            teaching_date=date(
                2026,
                9,
                12,
            ),
            lesson_id="LESSON-007",
            topic_id="TOPIC-01",
            topic_title="Số tự nhiên",
        ),
        row(
            period=12,
            title="Luyện tập chung",
            class_id="6A1",
            teaching_date=date(
                2026,
                9,
                14,
            ),
            lesson_id="LESSON-008",
            topic_id="TOPIC-01",
            topic_title="Số tự nhiên",
        ),
    )


def test_lesson_mode_groups_periods():
    units = (
        LessonPlanUnitSelectorService()
        .build_units(
            rows=rows(),
            mode=(
                LessonPlanSelectionMode
                .LESSON
            ),
        )
    )

    assert len(units) == 2

    assert (
        units[0].curriculum_periods
        == (10, 11)
    )


def test_period_mode_keeps_each_period_separate():
    units = (
        LessonPlanUnitSelectorService()
        .build_units(
            rows=rows(),
            mode=(
                LessonPlanSelectionMode
                .PERIOD
            ),
        )
    )

    assert len(units) == 3

    assert (
        units[0].curriculum_periods
        == (10,)
    )

    assert (
        units[1].curriculum_periods
        == (11,)
    )


def test_topic_mode_groups_multiple_lessons():
    units = (
        LessonPlanUnitSelectorService()
        .build_units(
            rows=rows(),
            mode=(
                LessonPlanSelectionMode
                .TOPIC
            ),
        )
    )

    assert len(units) == 1

    assert (
        units[0].title
        == "Số tự nhiên"
    )

    assert (
        units[0].curriculum_periods
        == (10, 11, 12)
    )


def test_topic_mode_only_available_when_topic_data_exists():
    service = (
        LessonPlanUnitSelectorService()
    )

    modes = service.available_modes(
        rows=rows()
    )

    assert (
        LessonPlanSelectionMode.TOPIC
        in modes
    )


def test_topic_mode_hidden_without_topic_data():
    plain = (
        row(
            period=10,
            title="Bài 7",
            class_id="6A1",
            teaching_date=date(
                2026,
                9,
                10,
            ),
        ),
    )

    modes = (
        LessonPlanUnitSelectorService()
        .available_modes(
            rows=plain
        )
    )

    assert modes == (
        LessonPlanSelectionMode.LESSON,
        LessonPlanSelectionMode.PERIOD,
        LessonPlanSelectionMode.WEEK_SUBJECT,
    )

    assert (
        LessonPlanSelectionMode.TOPIC
        not in modes
    )



def test_week_subject_mode_groups_same_subject():
    source = (
        row(
            period=10,
            title="Lesson 1",
            class_id="6A1",
            teaching_date=date(2026, 9, 8),
            lesson_id="LESSON-001",
            subject_ref="ENGLISH-6",
        ),
        row(
            period=11,
            title="Lesson 2",
            class_id="6A1",
            teaching_date=date(2026, 9, 10),
            lesson_id="LESSON-002",
            subject_ref="ENGLISH-6",
        ),
        row(
            period=12,
            title="Lesson 3",
            class_id="6A1",
            teaching_date=date(2026, 9, 12),
            lesson_id="LESSON-003",
            subject_ref="ENGLISH-6",
        ),
    )

    units = (
        LessonPlanUnitSelectorService()
        .build_units(
            rows=source,
            mode=(
                LessonPlanSelectionMode
                .WEEK_SUBJECT
            ),
        )
    )

    assert len(units) == 1

    unit = units[0]

    assert unit.unit_id == (
        "week_subject:ENGLISH-6"
    )

    assert unit.curriculum_periods == (
        10,
        11,
        12,
    )

    assert unit.row_indices == (
        0,
        1,
        2,
    )

    assert len(unit.teaching_dates) == 3


def test_week_subject_mode_separates_subjects():
    source = (
        row(
            period=10,
            title="To?n",
            class_id="6A1",
            teaching_date=date(2026, 9, 8),
            subject_ref="MATH-6",
        ),
        row(
            period=20,
            title="English",
            class_id="6A1",
            teaching_date=date(2026, 9, 9),
            subject_ref="ENGLISH-6",
        ),
    )

    units = (
        LessonPlanUnitSelectorService()
        .build_units(
            rows=source,
            mode=(
                LessonPlanSelectionMode
                .WEEK_SUBJECT
            ),
        )
    )

    assert len(units) == 2

    assert {
        unit.unit_id
        for unit in units
    } == {
        "week_subject:MATH-6",
        "week_subject:ENGLISH-6",
    }


def test_week_subject_does_not_split_components():
    source = (
        row(
            period=10,
            title="??i s?",
            class_id="6A1",
            teaching_date=date(2026, 9, 8),
            subject_ref="MATH-6",
            component_ref="ALGEBRA",
        ),
        row(
            period=11,
            title="H?nh h?c",
            class_id="6A1",
            teaching_date=date(2026, 9, 10),
            subject_ref="MATH-6",
            component_ref="GEOMETRY",
        ),
    )

    units = (
        LessonPlanUnitSelectorService()
        .build_units(
            rows=source,
            mode=(
                LessonPlanSelectionMode
                .WEEK_SUBJECT
            ),
        )
    )

    assert len(units) == 1
    assert (
        units[0].curriculum_periods
        == (10, 11)
    )


def test_week_subject_skips_blank_subject_ref():
    source = (
        row(
            period=10,
            title="Unknown",
            class_id="6A1",
            teaching_date=date(2026, 9, 8),
            subject_ref="",
        ),
    )

    units = (
        LessonPlanUnitSelectorService()
        .build_units(
            rows=source,
            mode=(
                LessonPlanSelectionMode
                .WEEK_SUBJECT
            ),
        )
    )

    assert units == ()


def test_week_subject_is_available_for_subject_rows():
    source = (
        row(
            period=10,
            title="Lesson",
            class_id="6A1",
            teaching_date=date(2026, 9, 8),
            subject_ref="ENGLISH-6",
        ),
    )

    modes = (
        LessonPlanUnitSelectorService()
        .available_modes(
            rows=source
        )
    )

    assert (
        LessonPlanSelectionMode
        .WEEK_SUBJECT
        in modes
    )
