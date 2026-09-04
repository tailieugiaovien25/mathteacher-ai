from pathlib import Path


PAGE = Path(
    "src/portal_v2/ui/weekly_lesson_authoring_streamlit.py"
).read_text(encoding="utf-8-sig")


def test_weekly_page_has_only_required_workflow_controls():
    assert "Soạn bài theo tuần" in PAGE
    assert "Chọn tuần soạn" in PAGE
    assert "Soạn bài cùng chuẩn giáo án" in PAGE
    assert "Soạn bài cùng AI" in PAGE

    assert "render_weekly_schedule_workspace" not in PAGE
    assert "_sync_standardization_week_to_lbg" not in PAGE
    assert "_v58_c5b2_shadow_lesson_plan_groups" not in PAGE


def test_group_card_contains_required_business_information():
    for term in (
        "Môn:",
        "Khối:",
        "Tiết PPCT:",
        "Bài:",
        "Lớp ",
        "Ngày dạy:",
    ):
        assert term in PAGE


def test_weekly_page_reads_authoritative_current_lbg_provider():
    assert "WeeklyLessonPlanGroupProvider" in PAGE
    assert "SystemWeeklyScheduleRuntime" not in PAGE
    assert "_v58_c5b2_shadow_lesson_plan_groups" not in PAGE


def test_week_selector_emits_canonical_context_change_only():
    assert "apply_canonical_year_week_change" in PAGE
    assert "from portal_v2.context.session_scoped_context_holder import apply_canonical_year_week_change" in PAGE
    assert 'field="week_number"' in PAGE
    assert 'source_page="weekly_lesson_authoring"' in PAGE
    assert "_autosave_standardization_change" not in PAGE
