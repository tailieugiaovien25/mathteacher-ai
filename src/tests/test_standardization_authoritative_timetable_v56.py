from pathlib import Path

UI = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")


def source() -> str:
    return UI.read_text(encoding="utf-8-sig")


def test_v56_declares_authoritative_timetable_boundary():
    text = source()
    assert "STANDARDIZATION_AUTHORITATIVE_TIMETABLE_V56" in text
    assert "def _build_standardization_authoritative_week_view(" in text
    assert "SystemWeeklyScheduleRuntime(" in text
    assert "SystemWeeklyScheduleRuntimeRequest(" in text
    assert "ppct_scope_rules=()," in text


def test_v56_rebuilds_before_persisted_weekly_schedule_fallback():
    text = source()
    active = text.index("    view = active_view")
    injection = text.index(
        "# STANDARDIZATION_AUTHORITATIVE_TIMETABLE_V56",
        active,
    )
    fallback = text.index("    if view is None:", injection)
    repository_read = text.index(
        "SupabaseWeeklyScheduleRepository(",
        fallback,
    )
    assert active < injection < fallback < repository_read


def test_v56_does_not_persist_authoritative_standardization_view():
    text = source()
    start = text.index(
        "def _build_standardization_authoritative_week_view("
    )
    end = text.index("\ndef ", start + 10)
    helper = text[start:end]
    assert "SupabaseWeeklyScheduleRepository" not in helper
    assert ".save(" not in helper


def test_v56_keeps_existing_selector_sync_layers():
    text = source()
    assert "STANDARDIZATION_GRADE_PPCT_CONTEXT_V50B" in text
    assert "STANDARDIZATION_PPCT_REVERSE_SYNC_V51" in text
    assert "STANDARDIZATION_TIMETABLE_CONTEXT_SYNC_V52D" in text


def test_v56_runtime_output_is_presented_as_normal_week_view():
    text = source()
    start = text.index(
        "def _build_standardization_authoritative_week_view("
    )
    end = text.index("\ndef ", start + 10)
    helper = text[start:end]
    assert "WeeklyScheduleGenerationResult(" in helper
    assert "WeeklyScheduleOutputService().export_excel(" in helper
    assert "WeeklySchedulePortalPresenter().present(" in helper
