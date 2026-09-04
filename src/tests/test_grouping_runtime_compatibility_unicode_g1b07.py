from lesson_planning_v2.adapters.supabase_lesson_plan_grouping_policy_repository import (
    SupabaseLessonPlanGroupingPolicyRepository,
)
from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroupingMode
from pathlib import Path


def test_legacy_by_grade_row_is_runtime_compatible():
    config = SupabaseLessonPlanGroupingPolicyRepository._from_row({
        "subject_ref": "subject-math",
        "component_ref": "",
        "grouping_mode": "BY_GRADE",
        "status": "ACTIVE",
        "rule_version": 1,
    })
    assert config.mode is LessonPlanGroupingMode.BY_WEEK


def test_weekly_authoring_diagnostic_labels_are_utf8():
    text = Path("src/portal_v2/ui/weekly_lesson_authoring_streamlit.py").read_text(encoding="utf-8")
    assert "Chi ti\u1ebft ch\u1ea9n \u0111o\u00e1n c\u1ea5u h\u00ecnh nh\u00f3m gi\u00e1o \u00e1n" in text
    assert "Ch\u1ea9n \u0111o\u00e1n ch\u1ec9 \u0111\u1ecdc" in text
    assert "Chi ti?t ch?n ?o?n" not in text


def test_provider_tokens_are_not_joined():
    text = Path("src/lesson_planning_v2/services/weekly_lesson_plan_group_provider.py").read_text(encoding="utf-8")
    assert "p.mode for p in policies" in text
    assert '") from exc' in text
    assert "p.modefor" not in text
