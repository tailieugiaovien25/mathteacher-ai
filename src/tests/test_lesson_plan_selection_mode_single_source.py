from lesson_planning_v2.lesson_plan_selection_mode import (
    LessonPlanSelectionMode as CanonicalMode,
)
from lesson_planning_v2.services.lesson_plan_unit_selector_service import (
    LessonPlanSelectionMode as SelectorMode,
)
from lesson_planning_v2.subject_lesson_plan_profile import (
    LessonPlanSelectionMode as SubjectMode,
    SubjectLessonPlanProfile,
)
from lesson_planning_v2.lesson_plan_template_profile import (
    LessonPlanTemplateProfile,
)


def test_selection_mode_is_one_python_type():
    assert SelectorMode is CanonicalMode
    assert SubjectMode is CanonicalMode


def test_selection_mode_storage_values_are_stable():
    assert CanonicalMode.LESSON.value == "lesson"
    assert CanonicalMode.PERIOD.value == "period"
    assert CanonicalMode.TOPIC.value == "topic"
    assert (
        CanonicalMode.WEEK_SUBJECT.value
        == "week_subject"
    )


def test_subject_profile_uses_selector_mode_directly():
    profile = SubjectLessonPlanProfile(
        teacher_id="teacher-1",
        subject_id="subject-math",
        templates=(
            LessonPlanTemplateProfile.default(),
        ),
        default_selection_mode=(
            SelectorMode.PERIOD
        ),
        allowed_selection_modes=(
            SelectorMode.LESSON,
            SelectorMode.PERIOD,
        ),
    )

    assert (
        profile.default_selection_mode
        is CanonicalMode.PERIOD
    )


def test_default_subject_modes_are_canonical():
    profile = SubjectLessonPlanProfile(
        teacher_id="teacher-1",
        subject_id="subject-math",
        templates=(
            LessonPlanTemplateProfile.default(),
        ),
    )

    assert (
        profile.default_selection_mode
        is CanonicalMode.LESSON
    )

    assert profile.allowed_selection_modes == (
        CanonicalMode.LESSON,
        CanonicalMode.PERIOD,
        CanonicalMode.TOPIC,
        CanonicalMode.WEEK_SUBJECT,
    )
