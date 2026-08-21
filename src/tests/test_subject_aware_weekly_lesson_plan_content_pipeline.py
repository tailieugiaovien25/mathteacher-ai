from datetime import date

import pytest

from lesson_planning_v2.lesson_plan_selection_mode import (
    LessonPlanSelectionMode,
)
from lesson_planning_v2.lesson_plan_teaching_scope import (
    LessonPlanTeachingScope,
)
from lesson_planning_v2.lesson_plan_template_profile import (
    LessonPlanTemplateProfile,
)
from lesson_planning_v2.services.subject_aware_weekly_lesson_plan_content_pipeline import (
    SubjectAwareWeeklyLessonPlanContentPipeline,
)
from lesson_planning_v2.services.weekly_lesson_plan_selection_content_resolver import (
    WeeklyLessonPlanSelectionContentResolver,
)
from lesson_planning_v2.subject_lesson_plan_profile import (
    SubjectLessonPlanProfile,
)
from lesson_planning_v2.weekly_lesson_plan_assembly import (
    WeeklyLessonPlan,
    WeeklyLessonPlanSession,
)
from lesson_planning_v2.weekly_lesson_plan_identity import (
    WeeklyLessonPlanIdentity,
)


def template():
    return LessonPlanTemplateProfile.default()


def profile(
    *,
    subject_id,
    default_mode,
    allowed_modes,
):
    return SubjectLessonPlanProfile(
        teacher_id="GV002",
        subject_id=subject_id,
        templates=(
            template(),
        ),
        default_selection_mode=default_mode,
        allowed_selection_modes=allowed_modes,
    )


def weekly_plan(
    *,
    subject_ref="FOREIGN-LANGUAGE-1",
):
    return WeeklyLessonPlan(
        identity=WeeklyLessonPlanIdentity(
            teacher_id="GV002",
            academic_year="2026-2027",
            week_number=8,
            subject_ref=subject_ref,
            teaching_scope=(
                LessonPlanTeachingScope.for_class(
                    class_id="CLASS-6A1",
                )
            ),
        ),
        sessions=(
            WeeklyLessonPlanSession(
                period_number=1,
                curriculum_period=22,
                lesson_title="Lesson 1",
                preparation_date=date(
                    2026, 10, 12
                ),
                teaching_date=date(
                    2026, 10, 13
                ),
                class_id="CLASS-6A1",
                component_ref="COMP-A",
            ),
            WeeklyLessonPlanSession(
                period_number=2,
                curriculum_period=23,
                lesson_title="Lesson 2",
                preparation_date=date(
                    2026, 10, 14
                ),
                teaching_date=date(
                    2026, 10, 15
                ),
                class_id="CLASS-6A1",
                component_ref="COMP-B",
            ),
            WeeklyLessonPlanSession(
                period_number=3,
                curriculum_period=24,
                lesson_title="Lesson 3",
                preparation_date=date(
                    2026, 10, 16
                ),
                teaching_date=date(
                    2026, 10, 17
                ),
                class_id="CLASS-6A1",
                component_ref="COMP-A",
            ),
        ),
    )


def resolver():
    def lesson_provider(value):
        return {
            "title": (
                "LESSON:"
                + value.lesson_title
            ),
            "objectives": "Objectives",
            "materials": "Materials",
            "teaching_process": "Process",
        }

    def period_provider(value):
        return {
            "title": (
                "PERIOD:"
                + str(
                    value.curriculum_period
                )
            ),
            "objectives": "Objectives",
            "materials": "Materials",
            "teaching_process": "Process",
        }

    shared_topic = {
        "title": "TOPIC:A",
        "objectives": "Topic objectives",
        "materials": "Topic materials",
        "teaching_process": "Topic process",
    }

    def topic_provider(_value):
        return shared_topic

    return WeeklyLessonPlanSelectionContentResolver(
        lesson_provider=lesson_provider,
        period_provider=period_provider,
        topic_provider=topic_provider,
    )


def test_subject_default_mode_drives_weekly_content():
    pipeline = (
        SubjectAwareWeeklyLessonPlanContentPipeline()
    )

    subject_profile = profile(
        subject_id="FOREIGN-LANGUAGE-1",
        default_mode=(
            LessonPlanSelectionMode.TOPIC
        ),
        allowed_modes=(
            LessonPlanSelectionMode.LESSON,
            LessonPlanSelectionMode.PERIOD,
            LessonPlanSelectionMode.TOPIC,
        ),
    )

    result = pipeline.build(
        weekly_plan=weekly_plan(),
        subject_profiles={
            "FOREIGN-LANGUAGE-1": (
                subject_profile
            ),
        },
        content_resolver=resolver(),
    )

    assert tuple(
        value.content["title"]
        for value in result.sessions
    ) == (
        "TOPIC:A",
        "TOPIC:A",
        "TOPIC:A",
    )


def test_explicit_allowed_mode_overrides_default():
    pipeline = (
        SubjectAwareWeeklyLessonPlanContentPipeline()
    )

    subject_profile = profile(
        subject_id="FOREIGN-LANGUAGE-1",
        default_mode=(
            LessonPlanSelectionMode.TOPIC
        ),
        allowed_modes=(
            LessonPlanSelectionMode.LESSON,
            LessonPlanSelectionMode.PERIOD,
            LessonPlanSelectionMode.TOPIC,
        ),
    )

    result = pipeline.build(
        weekly_plan=weekly_plan(),
        subject_profiles={
            "FOREIGN-LANGUAGE-1": (
                subject_profile
            ),
        },
        content_resolver=resolver(),
        selection_mode=(
            LessonPlanSelectionMode.PERIOD
        ),
    )

    assert tuple(
        value.content["title"]
        for value in result.sessions
    ) == (
        "PERIOD:22",
        "PERIOD:23",
        "PERIOD:24",
    )


def test_explicit_disallowed_mode_is_rejected():
    pipeline = (
        SubjectAwareWeeklyLessonPlanContentPipeline()
    )

    subject_profile = profile(
        subject_id="FOREIGN-LANGUAGE-1",
        default_mode=(
            LessonPlanSelectionMode.TOPIC
        ),
        allowed_modes=(
            LessonPlanSelectionMode.TOPIC,
        ),
    )

    with pytest.raises(
        ValueError,
        match="allowed",
    ):
        pipeline.build(
            weekly_plan=weekly_plan(),
            subject_profiles={
                "FOREIGN-LANGUAGE-1": (
                    subject_profile
                ),
            },
            content_resolver=resolver(),
            selection_mode=(
                LessonPlanSelectionMode.PERIOD
            ),
        )


def test_week_subject_cannot_be_used_as_content_mode():
    pipeline = (
        SubjectAwareWeeklyLessonPlanContentPipeline()
    )

    subject_profile = profile(
        subject_id="FOREIGN-LANGUAGE-1",
        default_mode=(
            LessonPlanSelectionMode.TOPIC
        ),
        allowed_modes=(
            LessonPlanSelectionMode.TOPIC,
        ),
    )

    with pytest.raises(
        ValueError,
        match="content",
    ):
        pipeline.build(
            weekly_plan=weekly_plan(),
            subject_profiles={
                "FOREIGN-LANGUAGE-1": (
                    subject_profile
                ),
            },
            content_resolver=resolver(),
            selection_mode=(
                LessonPlanSelectionMode
                .WEEK_SUBJECT
            ),
        )


def test_unknown_subject_uses_generic_subject_policy():
    pipeline = (
        SubjectAwareWeeklyLessonPlanContentPipeline()
    )

    result = pipeline.build(
        weekly_plan=weekly_plan(
            subject_ref="SUBJECT-UNKNOWN",
        ),
        subject_profiles={},
        content_resolver=resolver(),
    )

    assert tuple(
        value.content["title"]
        for value in result.sessions
    ) == (
        "LESSON:Lesson 1",
        "LESSON:Lesson 2",
        "LESSON:Lesson 3",
    )


def test_component_ref_survives_complete_pipeline():
    pipeline = (
        SubjectAwareWeeklyLessonPlanContentPipeline()
    )

    subject_profile = profile(
        subject_id="FOREIGN-LANGUAGE-1",
        default_mode=(
            LessonPlanSelectionMode.TOPIC
        ),
        allowed_modes=(
            LessonPlanSelectionMode.TOPIC,
        ),
    )

    result = pipeline.build(
        weekly_plan=weekly_plan(),
        subject_profiles={
            "FOREIGN-LANGUAGE-1": (
                subject_profile
            ),
        },
        content_resolver=resolver(),
    )

    assert tuple(
        value.component_ref
        for value in result.sessions
    ) == (
        "COMP-A",
        "COMP-B",
        "COMP-A",
    )


def test_pipeline_preserves_weekly_identity():
    pipeline = (
        SubjectAwareWeeklyLessonPlanContentPipeline()
    )

    plan = weekly_plan()

    subject_profile = profile(
        subject_id="FOREIGN-LANGUAGE-1",
        default_mode=(
            LessonPlanSelectionMode.LESSON
        ),
        allowed_modes=(
            LessonPlanSelectionMode.LESSON,
        ),
    )

    result = pipeline.build(
        weekly_plan=plan,
        subject_profiles={
            "FOREIGN-LANGUAGE-1": (
                subject_profile
            ),
        },
        content_resolver=resolver(),
    )

    assert result.identity == plan.identity


def test_pipeline_preserves_session_dates():
    pipeline = (
        SubjectAwareWeeklyLessonPlanContentPipeline()
    )

    plan = weekly_plan()

    subject_profile = profile(
        subject_id="FOREIGN-LANGUAGE-1",
        default_mode=(
            LessonPlanSelectionMode.PERIOD
        ),
        allowed_modes=(
            LessonPlanSelectionMode.PERIOD,
        ),
    )

    result = pipeline.build(
        weekly_plan=plan,
        subject_profiles={
            "FOREIGN-LANGUAGE-1": (
                subject_profile
            ),
        },
        content_resolver=resolver(),
    )

    assert tuple(
        value.preparation_date
        for value in result.sessions
    ) == tuple(
        value.preparation_date
        for value in plan.sessions
    )

    assert tuple(
        value.teaching_date
        for value in result.sessions
    ) == tuple(
        value.teaching_date
        for value in plan.sessions
    )
