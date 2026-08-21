from lesson_planning_v2.lesson_plan_selection_mode import (
    LessonPlanSelectionMode,
)
from lesson_planning_v2.lesson_plan_template_profile import (
    LessonPlanTemplateProfile,
)
from lesson_planning_v2.services.lesson_plan_subject_profile_resolver import (
    LessonPlanSubjectProfileResolver,
)
from lesson_planning_v2.subject_lesson_plan_profile import (
    SubjectLessonPlanProfile,
)


def _template():
    return LessonPlanTemplateProfile.default()


def _profile(
    *,
    subject_id,
    default_mode=LessonPlanSelectionMode.LESSON,
    allowed_modes=(
        LessonPlanSelectionMode.LESSON,
        LessonPlanSelectionMode.PERIOD,
        LessonPlanSelectionMode.TOPIC,
        LessonPlanSelectionMode.WEEK_SUBJECT,
    ),
):
    return SubjectLessonPlanProfile(
        teacher_id="teacher-1",
        subject_id=subject_id,
        templates=(
            _template(),
        ),
        default_selection_mode=default_mode,
        allowed_selection_modes=allowed_modes,
    )


def test_unknown_subject_uses_safe_generic_policy():
    resolver = LessonPlanSubjectProfileResolver()

    result = resolver.resolve(
        subject_id="subject-math",
        profiles={},
    )

    assert result.subject_id == "subject-math"

    assert (
        result.default_selection_mode
        == LessonPlanSelectionMode.LESSON
    )

    assert result.allowed_selection_modes == (
        LessonPlanSelectionMode.LESSON,
        LessonPlanSelectionMode.PERIOD,
        LessonPlanSelectionMode.TOPIC,
        LessonPlanSelectionMode.WEEK_SUBJECT,
    )


def test_subject_profile_controls_allowed_modes():
    resolver = LessonPlanSubjectProfileResolver()

    profile = _profile(
        subject_id="subject-art",
        default_mode=(
            LessonPlanSelectionMode.TOPIC
        ),
        allowed_modes=(
            LessonPlanSelectionMode.PERIOD,
            LessonPlanSelectionMode.TOPIC,
        ),
    )

    result = resolver.resolve(
        subject_id="subject-art",
        profiles={
            "subject-art": profile,
        },
    )

    assert result.allowed_selection_modes == (
        LessonPlanSelectionMode.PERIOD,
        LessonPlanSelectionMode.TOPIC,
    )

    assert (
        result.default_selection_mode
        == LessonPlanSelectionMode.TOPIC
    )


def test_math_can_use_lesson_as_default():
    resolver = LessonPlanSubjectProfileResolver()

    profile = _profile(
        subject_id="subject-math",
        default_mode=(
            LessonPlanSelectionMode.LESSON
        ),
        allowed_modes=(
            LessonPlanSelectionMode.LESSON,
            LessonPlanSelectionMode.PERIOD,
        ),
    )

    result = resolver.resolve(
        subject_id="subject-math",
        profiles={
            "subject-math": profile,
        },
    )

    assert (
        result.default_selection_mode
        == LessonPlanSelectionMode.LESSON
    )

    assert result.allowed_selection_modes == (
        LessonPlanSelectionMode.LESSON,
        LessonPlanSelectionMode.PERIOD,
    )


def test_single_allowed_mode_can_be_default():
    resolver = LessonPlanSubjectProfileResolver()

    profile = _profile(
        subject_id="subject-art",
        default_mode=(
            LessonPlanSelectionMode.TOPIC
        ),
        allowed_modes=(
            LessonPlanSelectionMode.TOPIC,
        ),
    )

    result = resolver.resolve(
        subject_id="subject-art",
        profiles={
            "subject-art": profile,
        },
    )

    assert result.allowed_selection_modes == (
        LessonPlanSelectionMode.TOPIC,
    )

    assert (
        result.default_selection_mode
        == LessonPlanSelectionMode.TOPIC
    )


def test_subject_id_is_normalized():
    resolver = LessonPlanSubjectProfileResolver()

    result = resolver.resolve(
        subject_id="  subject-math  ",
        profiles={},
    )

    assert result.subject_id == "subject-math"


def test_blank_subject_is_rejected():
    resolver = LessonPlanSubjectProfileResolver()

    try:
        resolver.resolve(
            subject_id="   ",
            profiles={},
        )
    except ValueError as error:
        assert (
            "subject_id must not be blank"
            in str(error)
        )
    else:
        raise AssertionError(
            "Expected ValueError"
        )



def test_week_subject_policy_is_preserved():
    resolver = LessonPlanSubjectProfileResolver()

    profile = _profile(
        subject_id="subject-language",
        default_mode=(
            LessonPlanSelectionMode.WEEK_SUBJECT
        ),
        allowed_modes=(
            LessonPlanSelectionMode.PERIOD,
            LessonPlanSelectionMode.WEEK_SUBJECT,
        ),
    )

    result = resolver.resolve(
        subject_id="subject-language",
        profiles={
            "subject-language": profile,
        },
    )

    assert result.allowed_selection_modes == (
        LessonPlanSelectionMode.PERIOD,
        LessonPlanSelectionMode.WEEK_SUBJECT,
    )

    assert (
        result.default_selection_mode
        == LessonPlanSelectionMode.WEEK_SUBJECT
    )
