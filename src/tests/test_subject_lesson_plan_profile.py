import pytest

from lesson_planning_v2.lesson_plan_template_profile import (
    LessonPlanTemplateProfile,
)
from lesson_planning_v2.subject_lesson_plan_profile import (
    LessonPlanSelectionMode,
    SubjectLessonPlanProfile,
)


def template(
    name: str,
    *,
    is_default: bool = False,
):
    base = LessonPlanTemplateProfile.default()

    return LessonPlanTemplateProfile(
        profile_name=name,
        structure=base.structure,
        header=base.header,
        layout=base.layout,
        scheduling=base.scheduling,
        approval=base.approval,
        is_default=is_default,
    )


def test_subject_profile_supports_multiple_templates():
    profile = SubjectLessonPlanProfile(
        teacher_id="teacher-1",
        subject_id="subject-math",
        templates=(
            template(
                "Mẫu Toán mặc định",
                is_default=True,
            ),
            template(
                "Mẫu chuyên đề Toán",
            ),
        ),
    )

    assert len(profile.templates) == 2

    assert (
        profile.default_template.profile_name
        == "Mẫu Toán mặc định"
    )


def test_teacher_can_have_independent_subject_profiles():
    math_profile = SubjectLessonPlanProfile(
        teacher_id="teacher-1",
        subject_id="subject-math",
        templates=(
            template("Mẫu Toán"),
        ),
        default_selection_mode=(
            LessonPlanSelectionMode.LESSON
        ),
    )

    ict_profile = SubjectLessonPlanProfile(
        teacher_id="teacher-1",
        subject_id="subject-ict",
        templates=(
            template("Mẫu Tin học"),
        ),
        default_selection_mode=(
            LessonPlanSelectionMode.TOPIC
        ),
    )

    assert (
        math_profile.teacher_id
        == ict_profile.teacher_id
    )

    assert (
        math_profile.subject_id
        != ict_profile.subject_id
    )

    assert (
        math_profile.default_selection_mode
        == LessonPlanSelectionMode.LESSON
    )

    assert (
        ict_profile.default_selection_mode
        == LessonPlanSelectionMode.TOPIC
    )


def test_subject_profile_can_restrict_selection_modes():
    profile = SubjectLessonPlanProfile(
        teacher_id="teacher-1",
        subject_id="subject-x",
        templates=(
            template("Mẫu môn X"),
        ),
        default_selection_mode=(
            LessonPlanSelectionMode.PERIOD
        ),
        allowed_selection_modes=(
            LessonPlanSelectionMode.PERIOD,
            LessonPlanSelectionMode.TOPIC,
        ),
    )

    assert profile.supports(
        LessonPlanSelectionMode.PERIOD
    )

    assert profile.supports(
        LessonPlanSelectionMode.TOPIC
    )

    assert not profile.supports(
        LessonPlanSelectionMode.LESSON
    )


def test_default_mode_must_be_allowed():
    with pytest.raises(
        ValueError,
        match="default selection mode",
    ):
        SubjectLessonPlanProfile(
            teacher_id="teacher-1",
            subject_id="subject-x",
            templates=(
                template("Mẫu môn X"),
            ),
            default_selection_mode=(
                LessonPlanSelectionMode.LESSON
            ),
            allowed_selection_modes=(
                LessonPlanSelectionMode.PERIOD,
            ),
        )


def test_subject_profile_requires_subject_id():
    with pytest.raises(
        ValueError,
        match="subject_id",
    ):
        SubjectLessonPlanProfile(
            teacher_id="teacher-1",
            subject_id=" ",
            templates=(
                template("Mẫu"),
            ),
        )


def test_subject_profile_requires_teacher_id():
    with pytest.raises(
        ValueError,
        match="teacher_id",
    ):
        SubjectLessonPlanProfile(
            teacher_id=" ",
            subject_id="subject-1",
            templates=(
                template("Mẫu"),
            ),
        )


def test_subject_profile_rejects_duplicate_template_names():
    with pytest.raises(
        ValueError,
        match="duplicate template",
    ):
        SubjectLessonPlanProfile(
            teacher_id="teacher-1",
            subject_id="subject-1",
            templates=(
                template("Mẫu A"),
                template("Mẫu A"),
            ),
        )


def test_subject_profile_rejects_multiple_defaults():
    with pytest.raises(
        ValueError,
        match="only one template",
    ):
        SubjectLessonPlanProfile(
            teacher_id="teacher-1",
            subject_id="subject-1",
            templates=(
                template(
                    "Mẫu A",
                    is_default=True,
                ),
                template(
                    "Mẫu B",
                    is_default=True,
                ),
            ),
        )


def test_first_template_is_effective_default_when_none_marked():
    profile = SubjectLessonPlanProfile(
        teacher_id="teacher-1",
        subject_id="subject-1",
        templates=(
            template("Mẫu A"),
            template("Mẫu B"),
        ),
    )

    assert (
        profile.default_template.profile_name
        == "Mẫu A"
    )



def test_week_subject_can_be_configured_as_default():
    profile = SubjectLessonPlanProfile(
        teacher_id="teacher-1",
        subject_id="subject-language",
        templates=(
            template("M?u Ngo?i ng?"),
        ),
        default_selection_mode=(
            LessonPlanSelectionMode.WEEK_SUBJECT
        ),
        allowed_selection_modes=(
            LessonPlanSelectionMode.PERIOD,
            LessonPlanSelectionMode.WEEK_SUBJECT,
        ),
    )

    assert (
        profile.default_selection_mode
        == LessonPlanSelectionMode.WEEK_SUBJECT
    )

    assert profile.supports(
        LessonPlanSelectionMode.WEEK_SUBJECT
    )
