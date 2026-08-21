from datetime import date

import pytest

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)
from lesson_planning_v2.weekly_lesson_plan_identity import (
    WeeklyLessonPlanIdentity,
)
from lesson_planning_v2.weekly_lesson_plan_word_document import (
    WeeklyLessonPlanWordDocument,
    WeeklyLessonPlanWordHeader,
    WeeklyLessonPlanWordSection,
    WeeklyLessonPlanWordApproval,
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


def header():
    return WeeklyLessonPlanWordHeader(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        scope_label="Lớp 6A1",
    )


def section(
    *,
    period_number=1,
    curriculum_period=22,
    preparation_date=date(2026, 10, 12),
    teaching_date=date(2026, 10, 13),
    title="Lesson 1",
    class_id="CLASS-6A1",
    component_ref=None,
    content=None,
):
    return WeeklyLessonPlanWordSection(
        period_number=period_number,
        curriculum_period=curriculum_period,
        preparation_date=preparation_date,
        teaching_date=teaching_date,
        title=title,
        class_id=class_id,
        component_ref=component_ref,
        content=(
            {
                "objectives": "Objectives",
                "materials": "Materials",
                "teaching_process": "Process",
            }
            if content is None
            else content
        ),
    )


def test_document_contains_header_identity_and_sections():
    document = WeeklyLessonPlanWordDocument(
        identity=identity(),
        header=header(),
        sections=(
            section(
                period_number=1,
                curriculum_period=22,
                title="Lesson 1",
            ),
            section(
                period_number=2,
                curriculum_period=23,
                title="Lesson 2",
            ),
            section(
                period_number=3,
                curriculum_period=24,
                title="Lesson 3",
            ),
        ),
    )

    assert document.identity == identity()
    assert document.header.week_number == 8
    assert len(document.sections) == 3


def test_header_preserves_weekly_document_metadata():
    value = header()

    assert value.teacher_id == "GV002"
    assert value.academic_year == "2026-2027"
    assert value.week_number == 8

    assert (
        value.subject_ref
        == "FOREIGN-LANGUAGE-1"
    )

    assert value.scope_label == "Lớp 6A1"


def test_section_preserves_session_metadata():
    value = section(
        period_number=2,
        curriculum_period=23,
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
        title="Lesson 2",
        component_ref="COMP-B",
    )

    assert value.period_number == 2
    assert value.curriculum_period == 23

    assert (
        value.preparation_date
        == date(2026, 10, 14)
    )

    assert (
        value.teaching_date
        == date(2026, 10, 15)
    )

    assert value.title == "Lesson 2"
    assert value.class_id == "CLASS-6A1"
    assert value.component_ref == "COMP-B"


def test_section_preserves_content():
    value = section(
        content={
            "objectives": "A",
            "materials": "B",
            "teaching_process": "C",
        }
    )

    assert value.content["objectives"] == "A"
    assert value.content["materials"] == "B"

    assert (
        value.content["teaching_process"]
        == "C"
    )


def test_document_orders_sections_by_period():
    document = WeeklyLessonPlanWordDocument(
        identity=identity(),
        header=header(),
        sections=(
            section(
                period_number=3,
                curriculum_period=24,
                title="Lesson 3",
            ),
            section(
                period_number=1,
                curriculum_period=22,
                title="Lesson 1",
            ),
            section(
                period_number=2,
                curriculum_period=23,
                title="Lesson 2",
            ),
        ),
    )

    assert tuple(
        value.period_number
        for value in document.sections
    ) == (
        1,
        2,
        3,
    )


def test_approval_is_single_document_level_block():
    approval = WeeklyLessonPlanWordApproval(
        approver_role="Tổ chuyên môn",
        placement="end_of_document",
    )

    document = WeeklyLessonPlanWordDocument(
        identity=identity(),
        header=header(),
        sections=(
            section(),
        ),
        approval=approval,
    )

    assert document.approval is approval

    assert (
        document.approval.placement
        == "end_of_document"
    )


def test_document_can_exist_without_approval():
    document = WeeklyLessonPlanWordDocument(
        identity=identity(),
        header=header(),
        sections=(
            section(),
        ),
    )

    assert document.approval is None


def test_empty_sections_are_rejected():
    with pytest.raises(
        ValueError,
        match="sections must not be empty",
    ):
        WeeklyLessonPlanWordDocument(
            identity=identity(),
            header=header(),
            sections=(),
        )


@pytest.mark.parametrize(
    "period_number",
    (
        0,
        -1,
    ),
)
def test_section_period_number_must_be_positive(
    period_number,
):
    with pytest.raises(
        ValueError,
        match="period_number must be positive",
    ):
        section(
            period_number=period_number,
        )


@pytest.mark.parametrize(
    "curriculum_period",
    (
        0,
        -1,
    ),
)
def test_section_curriculum_period_must_be_positive(
    curriculum_period,
):
    with pytest.raises(
        ValueError,
        match="curriculum_period must be positive",
    ):
        section(
            curriculum_period=curriculum_period,
        )


def test_blank_header_scope_label_is_rejected():
    with pytest.raises(
        ValueError,
        match="scope_label must not be blank",
    ):
        WeeklyLessonPlanWordHeader(
            teacher_id="GV002",
            academic_year="2026-2027",
            week_number=8,
            subject_ref="FOREIGN-LANGUAGE-1",
            scope_label="   ",
        )


def test_blank_section_title_is_rejected():
    with pytest.raises(
        ValueError,
        match="title must not be blank",
    ):
        section(
            title="   ",
        )


def test_empty_section_content_is_rejected():
    with pytest.raises(
        ValueError,
        match="content",
    ):
        section(
            content={},
        )
