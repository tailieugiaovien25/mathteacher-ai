from types import SimpleNamespace

from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode
from lesson_planning_v2.services.lesson_plan_grouping_service import (
    LessonPlanGroupingPolicyResolver,
    LessonPlanGroupingService,
)


def _row(*, grade, lesson_id, period, class_id):
    return SimpleNamespace(
        subject_ref="MATH",
        component_ref="GEOMETRY",
        grade=grade,
        lesson_id=lesson_id,
        lesson_title=f"Lesson {lesson_id}",
        curriculum_period=period,
        class_id=class_id,
        teaching_date=None,
        timetable_period=None,
        timetable_slot_id=None,
    )


def test_by_grade_groups_different_lessons_and_periods_in_same_grade():
    resolver = LessonPlanGroupingPolicyResolver.from_mapping(
        {("MATH", "GEOMETRY"): LessonPlanGroupingMode.BY_GRADE}
    )
    groups = LessonPlanGroupingService().group(
        (
            _row(grade=6, lesson_id="L1", period=1, class_id="6A1"),
            _row(grade=6, lesson_id="L2", period=2, class_id="6A2"),
        ),
        policy_resolver=resolver,
    )
    assert len(groups) == 1
    assert groups[0].grouping_mode is LessonPlanGroupingMode.BY_GRADE
    assert groups[0].grade == 6
    assert groups[0].class_ids == ("6A1", "6A2")
    assert groups[0].curriculum_periods == (1, 2)


def test_by_grade_never_crosses_canonical_grade():
    resolver = LessonPlanGroupingPolicyResolver.from_mapping(
        {("MATH", "GEOMETRY"): LessonPlanGroupingMode.BY_GRADE}
    )
    groups = LessonPlanGroupingService().group(
        (
            _row(grade=6, lesson_id="L1", period=1, class_id="6A1"),
            _row(grade=7, lesson_id="L1", period=1, class_id="7A1"),
        ),
        policy_resolver=resolver,
    )
    assert len(groups) == 2
    assert {group.grade for group in groups} == {6, 7}


def test_admin_ui_and_new_migration_expose_by_grade():
    from pathlib import Path

    ui = Path(
        "src/portal_v2/ui/admin_canonical_code_catalog_streamlit.py"
    ).read_text(encoding="utf-8")
    migration = Path(
        "supabase/migrations/"
        "202608300011_lesson_plan_grouping_by_grade_v58c5b7j2.sql"
    ).read_text(encoding="utf-8")
    assert "LessonPlanGroupingMode.BY_GRADE" in ui
    assert "BY_GRADE" in migration
    assert "drop table" not in migration.lower()
