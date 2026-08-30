from lesson_planning_v2.models.lesson_plan_grouping import (
    LessonPlanGroupingMode,
)
from lesson_planning_v2.services.lesson_plan_grouping_policy_source import (
    LessonPlanGroupingPolicySource,
)


def test_safe_default_is_by_period():
    source = LessonPlanGroupingPolicySource.safe_default()
    policy = source.resolve(subject_ref="MATH", component_ref="")
    assert policy.mode is LessonPlanGroupingMode.BY_PERIOD


def test_exact_subject_component_policy_wins():
    source = LessonPlanGroupingPolicySource(
        exact={
            ("ENG", "LISTENING"): LessonPlanGroupingMode.BY_WEEK,
        },
        subject_defaults={
            "ENG": LessonPlanGroupingMode.BY_LESSON,
        },
    )
    policy = source.resolve(
        subject_ref="ENG",
        component_ref="LISTENING",
    )
    assert policy.mode is LessonPlanGroupingMode.BY_WEEK


def test_subject_default_applies_when_exact_missing():
    source = LessonPlanGroupingPolicySource(
        exact={},
        subject_defaults={
            "ENG": LessonPlanGroupingMode.BY_WEEK,
        },
    )
    policy = source.resolve(subject_ref="ENG", component_ref="READING")
    assert policy.mode is LessonPlanGroupingMode.BY_WEEK


def test_fallback_can_be_explicit():
    source = LessonPlanGroupingPolicySource(
        exact={},
        subject_defaults={},
        fallback=LessonPlanGroupingMode.BY_LESSON,
    )
    policy = source.resolve(subject_ref="MUSIC", component_ref="")
    assert policy.mode is LessonPlanGroupingMode.BY_LESSON
