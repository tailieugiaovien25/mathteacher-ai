from datetime import date

import pytest

from lesson_planning_v2.lesson_plan_template_profile import (
    DraftingWeekday,
    LessonPlanAlignment,
    LessonPlanSchedulingPolicy,
    LessonPlanTemplateProfile,
)

from lesson_planning_v2.services.lesson_plan_template_application_service import (
    LessonPlanTemplateApplicationService,
    LessonTeachingOccurrence,
)


def make_profile(
    *,
    drafting_weekday=DraftingWeekday.SATURDAY,
    approval_offset_days=2,
):
    base = (
        LessonPlanTemplateProfile
        .default()
    )

    return LessonPlanTemplateProfile(
        profile_name=base.profile_name,
        structure=base.structure,
        header=base.header,
        layout=base.layout,
        scheduling=(
            LessonPlanSchedulingPolicy(
                drafting_weekday=(
                    drafting_weekday
                ),
                approval_offset_days=(
                    approval_offset_days
                ),
                allow_projected_teaching_dates=True,
                projected_schedule_horizon_weeks=2,
            )
        ),
        approval=base.approval,
        is_default=True,
    )


def test_application_resolves_shared_drafting_date():
    result = (
        LessonPlanTemplateApplicationService()
        .apply(
            profile=make_profile(),
            week_start_date=date(
                2026,
                10,
                26,
            ),
            curriculum_periods=(
                10,
                11,
            ),
            lesson_title=(
                "Bài 7. Thứ tự thực hiện "
                "các phép tính"
            ),
            teaching_occurrences=(
                LessonTeachingOccurrence(
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
                LessonTeachingOccurrence(
                    class_name="6A2",
                    teaching_date=date(
                        2026,
                        10,
                        27,
                    ),
                ),
            ),
        )
    )

    assert result.drafting_date == date(
        2026,
        10,
        24,
    )


def test_application_resolves_approval_date():
    result = (
        LessonPlanTemplateApplicationService()
        .apply(
            profile=make_profile(
                approval_offset_days=2
            ),
            week_start_date=date(
                2026,
                10,
                26,
            ),
            curriculum_periods=(10,),
            lesson_title="Bài 7",
            teaching_occurrences=(
                LessonTeachingOccurrence(
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
            ),
        )
    )

    assert result.drafting_date == date(
        2026,
        10,
        24,
    )

    assert result.approval_date == date(
        2026,
        10,
        26,
    )


def test_application_keeps_class_date_in_following_week():
    result = (
        LessonPlanTemplateApplicationService()
        .apply(
            profile=make_profile(),
            week_start_date=date(
                2026,
                10,
                26,
            ),
            curriculum_periods=(
                10,
                11,
            ),
            lesson_title="Bài 7",
            teaching_occurrences=(
                LessonTeachingOccurrence(
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        30,
                    ),
                ),
                LessonTeachingOccurrence(
                    class_name="6A2",
                    teaching_date=date(
                        2026,
                        11,
                        2,
                    ),
                    projected=True,
                ),
            ),
        )
    )

    assert len(
        result.teaching_occurrences
    ) == 2

    assert (
        result.teaching_occurrences[1]
        .class_name
        == "6A2"
    )

    assert (
        result.teaching_occurrences[1]
        .teaching_date
        == date(
            2026,
            11,
            2,
        )
    )

    assert (
        result.teaching_occurrences[1]
        .projected
        is True
    )


def test_application_builds_multi_period_heading():
    result = (
        LessonPlanTemplateApplicationService()
        .apply(
            profile=make_profile(),
            week_start_date=date(
                2026,
                10,
                26,
            ),
            curriculum_periods=(
                11,
                10,
                10,
            ),
            lesson_title="Bài 7",
            teaching_occurrences=(
                LessonTeachingOccurrence(
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
            ),
        )
    )

    assert (
        result.curriculum_periods
        == (10, 11)
    )

    assert (
        result.period_heading
        == "\u0054\u0049\u1ebe\u0054 10 + 11"
    )


def test_application_uppercases_lesson_title():
    result = (
        LessonPlanTemplateApplicationService()
        .apply(
            profile=make_profile(),
            week_start_date=date(
                2026,
                10,
                26,
            ),
            curriculum_periods=(10,),
            lesson_title=(
                "Bài 7. Thứ tự thực hiện "
                "các phép tính"
            ),
            teaching_occurrences=(
                LessonTeachingOccurrence(
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
            ),
        )
    )

    assert result.lesson_title == (
        "BÀI 7. THỨ TỰ THỰC HIỆN "
        "CÁC PHÉP TÍNH"
    )


def test_application_carries_layout_rules():
    result = (
        LessonPlanTemplateApplicationService()
        .apply(
            profile=make_profile(),
            week_start_date=date(
                2026,
                10,
                26,
            ),
            curriculum_periods=(10,),
            lesson_title="Bài 7",
            teaching_occurrences=(
                LessonTeachingOccurrence(
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
            ),
        )
    )

    assert (
        result.metadata_alignment
        is LessonPlanAlignment.LEFT
    )

    assert (
        result.period_alignment
        is LessonPlanAlignment.CENTER
    )

    assert result.period_bold is True

    assert (
        result.lesson_title_alignment
        is LessonPlanAlignment.CENTER
    )

    assert result.lesson_title_bold is True

    assert (
        result.approval_alignment
        is LessonPlanAlignment.RIGHT
    )

    assert (
        result.approval_signature_blank_lines
        == 5
    )


def test_application_supports_friday_previous_week():
    result = (
        LessonPlanTemplateApplicationService()
        .apply(
            profile=make_profile(
                drafting_weekday=(
                    DraftingWeekday.FRIDAY
                )
            ),
            week_start_date=date(
                2026,
                10,
                26,
            ),
            curriculum_periods=(10,),
            lesson_title="Bài 7",
            teaching_occurrences=(
                LessonTeachingOccurrence(
                    class_name="6A1",
                    teaching_date=date(
                        2026,
                        10,
                        26,
                    ),
                ),
            ),
        )
    )

    assert result.drafting_date == date(
        2026,
        10,
        23,
    )


def test_application_requires_monday_week_start():
    with pytest.raises(
        ValueError,
        match="Monday",
    ):
        (
            LessonPlanTemplateApplicationService()
            .apply(
                profile=make_profile(),
                week_start_date=date(
                    2026,
                    10,
                    27,
                ),
                curriculum_periods=(10,),
                lesson_title="Bài 7",
                teaching_occurrences=(
                    LessonTeachingOccurrence(
                        class_name="6A1",
                        teaching_date=date(
                            2026,
                            10,
                            27,
                        ),
                    ),
                ),
            )
        )


def test_application_rejects_blank_class_name():
    with pytest.raises(
        ValueError,
        match="class_name",
    ):
        LessonTeachingOccurrence(
            class_name=" ",
            teaching_date=date(
                2026,
                10,
                26,
            ),
        )
