import pytest

from lesson_planning_v2.services.weekly_lesson_plan_display_resolver import (
    WeeklyLessonPlanDisplayResolver,
)
from lesson_planning_v2.weekly_lesson_plan_docx_presentation import (
    WeeklyLessonPlanDocxPresentationProfile,
)


def profile():
    return WeeklyLessonPlanDocxPresentationProfile(
        document_title="GI\u00c1O \u00c1N TU\u1ea6N",
        teacher_label="Gi\u00e1o vi\u00ean",
        subject_label="M\u00f4n h\u1ecdc",
        academic_year_label="N\u0103m h\u1ecdc",
        week_label="Tu\u1ea7n",
        scope_label="L\u1edbp / Kh\u1ed1i",
        curriculum_period_label="Ti\u1ebft PPCT",
        preparation_date_label="Ng\u00e0y so\u1ea1n",
        teaching_date_label="Ng\u00e0y d\u1ea1y",
        class_label="L\u1edbp",
        component_label="Ph\u00e2n m\u00f4n",
        objectives_label="I. M\u1ee5c ti\u00eau",
        materials_label=(
            "II. Thi\u1ebft b\u1ecb v\u00e0 h\u1ecdc li\u1ec7u"
        ),
        teaching_process_label=(
            "III. Ti\u1ebfn tr\u00ecnh d\u1ea1y h\u1ecdc"
        ),
        show_document_title=True,
        show_component=True,
        page_break_between_sections=False,
        approval_blank_lines=5,
    )


def test_profile_preserves_labels():
    value = profile()

    assert value.document_title == "GI\u00c1O \u00c1N TU\u1ea6N"
    assert value.teacher_label == "Gi\u00e1o vi\u00ean"
    assert value.subject_label == "M\u00f4n h\u1ecdc"
    assert value.week_label == "Tu\u1ea7n"

    assert (
        value.preparation_date_label
        == "Ng\u00e0y so\u1ea1n"
    )

    assert (
        value.teaching_date_label
        == "Ng\u00e0y d\u1ea1y"
    )


def test_profile_preserves_layout_policy():
    value = profile()

    assert value.show_document_title is True
    assert value.show_component is True
    assert value.page_break_between_sections is False
    assert value.approval_blank_lines == 5


def test_blank_required_label_is_rejected():
    with pytest.raises(
        ValueError,
        match="teacher_label",
    ):
        WeeklyLessonPlanDocxPresentationProfile(
            document_title="GI\u00c1O \u00c1N TU\u1ea6N",
            teacher_label="   ",
            subject_label="M\u00f4n h\u1ecdc",
            academic_year_label="N\u0103m h\u1ecdc",
            week_label="Tu\u1ea7n",
            scope_label="L\u1edbp / Kh\u1ed1i",
            curriculum_period_label="Ti\u1ebft PPCT",
            preparation_date_label="Ng\u00e0y so\u1ea1n",
            teaching_date_label="Ng\u00e0y d\u1ea1y",
            class_label="L\u1edbp",
            component_label="Ph\u00e2n m\u00f4n",
            objectives_label="I. M\u1ee5c ti\u00eau",
            materials_label=(
                "II. Thi\u1ebft b\u1ecb v\u00e0 h\u1ecdc li\u1ec7u"
            ),
            teaching_process_label=(
                "III. Ti\u1ebfn tr\u00ecnh d\u1ea1y h\u1ecdc"
            ),
        )


def test_negative_approval_blank_lines_are_rejected():
    with pytest.raises(
        ValueError,
        match="approval_blank_lines",
    ):
        WeeklyLessonPlanDocxPresentationProfile(
            document_title="GI\u00c1O \u00c1N TU\u1ea6N",
            teacher_label="Gi\u00e1o vi\u00ean",
            subject_label="M\u00f4n h\u1ecdc",
            academic_year_label="N\u0103m h\u1ecdc",
            week_label="Tu\u1ea7n",
            scope_label="L\u1edbp / Kh\u1ed1i",
            curriculum_period_label="Ti\u1ebft PPCT",
            preparation_date_label="Ng\u00e0y so\u1ea1n",
            teaching_date_label="Ng\u00e0y d\u1ea1y",
            class_label="L\u1edbp",
            component_label="Ph\u00e2n m\u00f4n",
            objectives_label="I. M\u1ee5c ti\u00eau",
            materials_label=(
                "II. Thi\u1ebft b\u1ecb v\u00e0 h\u1ecdc li\u1ec7u"
            ),
            teaching_process_label=(
                "III. Ti\u1ebfn tr\u00ecnh d\u1ea1y h\u1ecdc"
            ),
            approval_blank_lines=-1,
        )


def test_display_resolver_uses_external_names():
    resolver = WeeklyLessonPlanDisplayResolver()

    result = resolver.resolve(
        teacher_id="GV002",
        subject_ref="FOREIGN-LANGUAGE-1",
        class_id="CLASS-6A1",
        component_ref="COMP-A",
        teacher_name_resolver=(
            lambda _value: "Nguy\u1ec5n V\u0103n A"
        ),
        subject_name_resolver=(
            lambda _value: "Ngo\u1ea1i ng\u1eef 1"
        ),
        class_name_resolver=(
            lambda _value: "L\u1edbp 6A1"
        ),
        component_name_resolver=(
            lambda _value: "Ti\u1ebfng Anh"
        ),
    )

    assert result.teacher_name == "Nguy\u1ec5n V\u0103n A"
    assert result.subject_name == "Ngo\u1ea1i ng\u1eef 1"
    assert result.class_name == "L\u1edbp 6A1"
    assert result.component_name == "Ti\u1ebfng Anh"


def test_display_result_preserves_canonical_ids():
    resolver = WeeklyLessonPlanDisplayResolver()

    result = resolver.resolve(
        teacher_id="GV002",
        subject_ref="FOREIGN-LANGUAGE-1",
        class_id="CLASS-6A1",
        component_ref="COMP-A",
        teacher_name_resolver=lambda _value: "Teacher",
        subject_name_resolver=lambda _value: "Subject",
        class_name_resolver=lambda _value: "Class",
        component_name_resolver=lambda _value: "Component",
    )

    assert result.teacher_id == "GV002"
    assert result.subject_ref == "FOREIGN-LANGUAGE-1"
    assert result.class_id == "CLASS-6A1"
    assert result.component_ref == "COMP-A"


def test_component_can_be_absent():
    resolver = WeeklyLessonPlanDisplayResolver()

    result = resolver.resolve(
        teacher_id="GV002",
        subject_ref="SUBJECT-MATH",
        class_id="CLASS-6A1",
        component_ref=None,
        teacher_name_resolver=lambda _value: "Teacher",
        subject_name_resolver=lambda _value: "To\u00e1n",
        class_name_resolver=lambda _value: "L\u1edbp 6A1",
        component_name_resolver=lambda value: value,
    )

    assert result.component_ref is None
    assert result.component_name is None


def test_blank_resolved_teacher_name_is_rejected():
    resolver = WeeklyLessonPlanDisplayResolver()

    with pytest.raises(
        ValueError,
        match="teacher_name",
    ):
        resolver.resolve(
            teacher_id="GV002",
            subject_ref="SUBJECT-MATH",
            class_id="CLASS-6A1",
            component_ref=None,
            teacher_name_resolver=lambda _value: "   ",
            subject_name_resolver=lambda _value: "To\u00e1n",
            class_name_resolver=lambda _value: "L\u1edbp 6A1",
            component_name_resolver=lambda value: value,
        )


def test_blank_resolved_subject_name_is_rejected():
    resolver = WeeklyLessonPlanDisplayResolver()

    with pytest.raises(
        ValueError,
        match="subject_name",
    ):
        resolver.resolve(
            teacher_id="GV002",
            subject_ref="SUBJECT-MATH",
            class_id="CLASS-6A1",
            component_ref=None,
            teacher_name_resolver=lambda _value: "Teacher",
            subject_name_resolver=lambda _value: "",
            class_name_resolver=lambda _value: "L\u1edbp 6A1",
            component_name_resolver=lambda value: value,
        )


def test_resolver_does_not_infer_names_from_ids():
    resolver = WeeklyLessonPlanDisplayResolver()

    teacher_calls = []
    subject_calls = []
    class_calls = []
    component_calls = []

    result = resolver.resolve(
        teacher_id="GV002",
        subject_ref="FOREIGN-LANGUAGE-1",
        class_id="CLASS-6A1",
        component_ref="COMP-A",
        teacher_name_resolver=(
            lambda value: (
                teacher_calls.append(value)
                or "Teacher Display"
            )
        ),
        subject_name_resolver=(
            lambda value: (
                subject_calls.append(value)
                or "Subject Display"
            )
        ),
        class_name_resolver=(
            lambda value: (
                class_calls.append(value)
                or "Class Display"
            )
        ),
        component_name_resolver=(
            lambda value: (
                component_calls.append(value)
                or "Component Display"
            )
        ),
    )

    assert result.teacher_name == "Teacher Display"
    assert result.subject_name == "Subject Display"
    assert result.class_name == "Class Display"
    assert result.component_name == "Component Display"

    assert teacher_calls == ["GV002"]
    assert subject_calls == ["FOREIGN-LANGUAGE-1"]
    assert class_calls == ["CLASS-6A1"]
    assert component_calls == ["COMP-A"]
