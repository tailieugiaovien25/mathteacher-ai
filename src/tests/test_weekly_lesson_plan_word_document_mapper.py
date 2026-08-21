from datetime import date

import pytest

from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)
from lesson_planning_v2.services.weekly_lesson_plan_word_document_mapper import (
    WeeklyLessonPlanWordDocumentMapper,
)
from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlanApproval,
)
from lesson_planning_v2.weekly_lesson_plan_content import (
    WeeklyLessonPlanContent,
    WeeklyLessonPlanContentSession,
)
from lesson_planning_v2.weekly_lesson_plan_identity import (
    WeeklyLessonPlanIdentity,
)
from lesson_planning_v2.weekly_lesson_plan_word_document import (
    WeeklyLessonPlanWordDocument,
)


def identity(
    *,
    scope=None,
):
    return WeeklyLessonPlanIdentity(
        teacher_id="GV002",
        academic_year="2026-2027",
        week_number=8,
        subject_ref="FOREIGN-LANGUAGE-1",
        teaching_scope=(
            scope
            or LessonPlanTeachingScope.for_class(
                class_id="CLASS-6A1",
            )
        ),
    )


def content_session(
    *,
    period_number=1,
    curriculum_period=22,
    title="Lesson 1",
    preparation_date=date(2026, 10, 12),
    teaching_date=date(2026, 10, 13),
    class_id="CLASS-6A1",
    component_ref=None,
):
    return WeeklyLessonPlanContentSession(
        period_number=period_number,
        curriculum_period=curriculum_period,
        lesson_title=title,
        preparation_date=preparation_date,
        teaching_date=teaching_date,
        class_id=class_id,
        component_ref=component_ref,
        content={
            "title": title,
            "objectives": (
                f"Objectives for {title}"
            ),
            "materials": (
                f"Materials for {title}"
            ),
            "teaching_process": (
                f"Process for {title}"
            ),
        },
    )


def content_plan(
    *,
    plan_identity=None,
    approval=None,
):
    return WeeklyLessonPlanContent(
        identity=(
            plan_identity
            or identity()
        ),
        sessions=(
            content_session(
                period_number=1,
                curriculum_period=22,
                title="Lesson 1",
                component_ref="COMP-A",
            ),
            content_session(
                period_number=2,
                curriculum_period=23,
                title="Lesson 2",
                preparation_date=date(
                    2026, 10, 14
                ),
                teaching_date=date(
                    2026, 10, 15
                ),
                component_ref="COMP-B",
            ),
            content_session(
                period_number=3,
                curriculum_period=24,
                title="Lesson 3",
                preparation_date=date(
                    2026, 10, 16
                ),
                teaching_date=date(
                    2026, 10, 17
                ),
                component_ref="COMP-A",
            ),
        ),
        approval=approval,
    )


def class_scope_label_resolver(scope):
    assert scope.class_id == "CLASS-6A1"
    return "Lớp 6A1"


def test_mapper_builds_word_document():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    result = mapper.map(
        weekly_content=content_plan(),
        scope_label_resolver=(
            class_scope_label_resolver
        ),
    )

    assert isinstance(
        result,
        WeeklyLessonPlanWordDocument,
    )

    assert result.identity == identity()
    assert len(result.sections) == 3


def test_mapper_builds_header_from_identity():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    result = mapper.map(
        weekly_content=content_plan(),
        scope_label_resolver=(
            class_scope_label_resolver
        ),
    )

    assert result.header.teacher_id == "GV002"

    assert (
        result.header.academic_year
        == "2026-2027"
    )

    assert result.header.week_number == 8

    assert (
        result.header.subject_ref
        == "FOREIGN-LANGUAGE-1"
    )

    assert (
        result.header.scope_label
        == "Lớp 6A1"
    )


def test_mapper_maps_sessions_to_sections():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    result = mapper.map(
        weekly_content=content_plan(),
        scope_label_resolver=(
            class_scope_label_resolver
        ),
    )

    assert tuple(
        value.period_number
        for value in result.sections
    ) == (
        1,
        2,
        3,
    )

    assert tuple(
        value.curriculum_period
        for value in result.sections
    ) == (
        22,
        23,
        24,
    )

    assert tuple(
        value.title
        for value in result.sections
    ) == (
        "Lesson 1",
        "Lesson 2",
        "Lesson 3",
    )


def test_mapper_preserves_dates():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    result = mapper.map(
        weekly_content=content_plan(),
        scope_label_resolver=(
            class_scope_label_resolver
        ),
    )

    assert tuple(
        value.preparation_date
        for value in result.sections
    ) == (
        date(2026, 10, 12),
        date(2026, 10, 14),
        date(2026, 10, 16),
    )

    assert tuple(
        value.teaching_date
        for value in result.sections
    ) == (
        date(2026, 10, 13),
        date(2026, 10, 15),
        date(2026, 10, 17),
    )


def test_mapper_preserves_component_ref():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    result = mapper.map(
        weekly_content=content_plan(),
        scope_label_resolver=(
            class_scope_label_resolver
        ),
    )

    assert tuple(
        value.component_ref
        for value in result.sections
    ) == (
        "COMP-A",
        "COMP-B",
        "COMP-A",
    )


def test_mapper_preserves_content():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    result = mapper.map(
        weekly_content=content_plan(),
        scope_label_resolver=(
            class_scope_label_resolver
        ),
    )

    assert (
        result.sections[0]
        .content["objectives"]
        == "Objectives for Lesson 1"
    )

    assert (
        result.sections[1]
        .content["materials"]
        == "Materials for Lesson 2"
    )

    assert (
        result.sections[2]
        .content["teaching_process"]
        == "Process for Lesson 3"
    )


def test_mapper_maps_weekly_approval_to_document_level():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    result = mapper.map(
        weekly_content=content_plan(
            approval=WeeklyLessonPlanApproval(
                approver_role=(
                    "Tổ chuyên môn"
                ),
            )
        ),
        scope_label_resolver=(
            class_scope_label_resolver
        ),
    )

    assert result.approval is not None

    assert (
        result.approval.approver_role
        == "Tổ chuyên môn"
    )

    assert (
        result.approval.placement
        == "end_of_document"
    )


def test_mapper_does_not_create_approval_implicitly():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    result = mapper.map(
        weekly_content=content_plan(),
        scope_label_resolver=(
            class_scope_label_resolver
        ),
    )

    assert result.approval is None


def test_grade_scope_uses_external_scope_label_resolver():
    grade_identity = identity(
        scope=(
            LessonPlanTeachingScope.for_grade(
                grade_key="GRADE-6",
            )
        ),
    )

    calls = []

    def resolver(scope):
        calls.append(
            scope.identity_key
        )

        return "Khối 6"

    mapper = WeeklyLessonPlanWordDocumentMapper()

    result = mapper.map(
        weekly_content=content_plan(
            plan_identity=grade_identity,
        ),
        scope_label_resolver=resolver,
    )

    assert result.header.scope_label == "Khối 6"

    assert calls == [
        (
            "grade",
            "GRADE-6",
        ),
    ]


def test_mapper_does_not_infer_scope_label_from_scope_ref():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    def resolver(_scope):
        return "Tên hiển thị tùy cấu hình"

    result = mapper.map(
        weekly_content=content_plan(),
        scope_label_resolver=resolver,
    )

    assert (
        result.header.scope_label
        == "Tên hiển thị tùy cấu hình"
    )


def test_blank_resolved_scope_label_is_rejected():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    def invalid_resolver(_scope):
        return "   "

    with pytest.raises(
        ValueError,
        match="scope_label",
    ):
        mapper.map(
            weekly_content=content_plan(),
            scope_label_resolver=(
                invalid_resolver
            ),
        )


def test_mapper_does_not_mutate_source_content():
    mapper = WeeklyLessonPlanWordDocumentMapper()

    source = content_plan()

    original_sessions = source.sessions

    mapper.map(
        weekly_content=source,
        scope_label_resolver=(
            class_scope_label_resolver
        ),
    )

    assert source.sessions is original_sessions
