import pytest

from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode
from lesson_planning_v2.models.lesson_plan_grouping_policy_config import (
    LessonPlanGroupingPolicyConfig,
)
from lesson_planning_v2.services.lesson_plan_grouping_policy_config_service import (
    LessonPlanGroupingPolicyConfigService,
)


def test_admin_config_can_set_subject_default_by_week():
    source = LessonPlanGroupingPolicyConfigService().build_policy_source(
        [
            LessonPlanGroupingPolicyConfig(
                subject_ref="ENG",
                component_ref="",
                mode=LessonPlanGroupingMode.BY_WEEK,
            )
        ]
    )
    assert source.resolve(subject_ref="ENG", component_ref="READING").mode is LessonPlanGroupingMode.BY_WEEK


def test_component_policy_overrides_subject_default():
    source = LessonPlanGroupingPolicyConfigService().build_policy_source(
        [
            LessonPlanGroupingPolicyConfig("ENG", "", LessonPlanGroupingMode.BY_WEEK),
            LessonPlanGroupingPolicyConfig("ENG", "READING", LessonPlanGroupingMode.BY_LESSON),
        ]
    )
    assert source.resolve(subject_ref="ENG", component_ref="READING").mode is LessonPlanGroupingMode.BY_LESSON
    assert source.resolve(subject_ref="ENG", component_ref="LISTENING").mode is LessonPlanGroupingMode.BY_WEEK


def test_inactive_config_does_not_apply():
    source = LessonPlanGroupingPolicyConfigService().build_policy_source(
        [
            LessonPlanGroupingPolicyConfig(
                "MATH", "", LessonPlanGroupingMode.BY_LESSON, active=False
            )
        ]
    )
    assert source.resolve(subject_ref="MATH", component_ref="").mode is LessonPlanGroupingMode.BY_PERIOD


def test_grouping_modes_exclude_grade_partition():
    assert {m.value for m in LessonPlanGroupingMode} == {
        "BY_PERIOD", "BY_LESSON", "BY_WEEK"
    }


def test_subject_required():
    with pytest.raises(ValueError, match="SUBJECT_REF_REQUIRED"):
        LessonPlanGroupingPolicyConfig("", "", LessonPlanGroupingMode.BY_PERIOD)


def test_version_positive():
    with pytest.raises(ValueError, match="POLICY_VERSION_MUST_BE_POSITIVE"):
        LessonPlanGroupingPolicyConfig(
            "ENG", "", LessonPlanGroupingMode.BY_WEEK, version=0
        )
