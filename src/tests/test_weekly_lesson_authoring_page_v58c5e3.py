from pathlib import Path

PAGE = Path(
    "src/portal_v2/ui/weekly_lesson_authoring_streamlit.py"
).read_text(encoding="utf-8-sig")
WEEKLY = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
).read_text(encoding="utf-8-sig")


def test_page_is_dedicated_weekly_coordination_entrypoint():
    assert '<h1 class="mt-weekly-title">Soạn bài theo tuần</h1>' in PAGE
    assert "_apply_weekly_authoring_modern_styles()" in PAGE
    assert "render_weekly_schedule_workspace" not in PAGE


def test_page_reuses_existing_canonical_week_bridge():
    assert "apply_canonical_year_week_change" in PAGE
    assert "render_weekly_schedule_workspace" not in PAGE
    assert "ContextChange(" not in PAGE
    assert "_emit_canonical_week_change" not in PAGE


def test_grouping_and_naming_foundations_still_exist():
    assert "_v58_c5b2_shadow_lesson_plan_groups" in WEEKLY
    assert "CanonicalLessonPlanNamingService" in WEEKLY


def test_weekly_page_does_not_restore_by_grade_mode():
    assert "BY_GRADE" not in PAGE
