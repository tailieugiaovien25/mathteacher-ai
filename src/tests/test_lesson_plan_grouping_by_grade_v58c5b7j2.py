from types import SimpleNamespace
import pytest

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


def test_removed_by_grade_mode_is_not_available():
    assert not hasattr(LessonPlanGroupingMode, "BY_GRADE")


def test_legacy_by_grade_policy_falls_back_safely():
    with pytest.raises(ValueError, match="BY_GRADE"):
        LessonPlanGroupingPolicyResolver.from_mapping(
            {("MATH", "GEOMETRY"): "BY_GRADE"}
        )


def test_admin_ui_and_latest_migration_remove_by_grade():
    from pathlib import Path

    ui = Path(
        "src/portal_v2/ui/admin_canonical_code_catalog_streamlit.py"
    ).read_text(encoding="utf-8")
    migration = Path(
        "supabase/migrations/"
        "202608310001_lesson_plan_grouping_remove_by_grade_v58c5b7j3.sql"
    ).read_text(encoding="utf-8")
    assert "LessonPlanGroupingMode.BY_GRADE" not in ui
    assert "BY_GRADE" in migration
    assert "BY_LESSON" in migration
