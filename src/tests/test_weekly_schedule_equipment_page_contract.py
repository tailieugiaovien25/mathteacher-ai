from pathlib import Path


PAGE = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")
RUNTIME = Path(
    "src/portal_v2/runtime/system_weekly_schedule_runtime.py"
)


def source() -> str:
    return PAGE.read_text(encoding="utf-8-sig")


def runtime_source() -> str:
    return RUNTIME.read_text(encoding="utf-8-sig")


def test_combined_page_has_two_synchronized_sections():
    text = source()

    assert "def render_weekly_schedule_and_equipment_workspace(" in text
    assert '"1. Lịch báo giảng"' in text
    assert '"2. Phiếu báo sử dụng thiết bị"' in text
    assert "view = st.session_state.get(_VIEW_STATE_KEY)" in text
    assert "_render_equipment_usage_report(" in text
    assert "client=client" in text


def test_equipment_report_is_derived_from_schedule_equipment():
    text = source()

    assert "def _equipment_usage_rows(" in text
    assert "rows = _preview_rows(" in text
    assert 'row.get("Chuẩn bị, điều chỉnh"' in text
    assert '"Thiết bị/Phương tiện"' in text
    assert '"Số lượng"' in text
    assert '"Địa điểm sử dụng"' in text
    assert '"Tải Phiếu báo sử dụng thiết bị"' in text
    assert "csv.DictWriter(" in text


def test_combined_page_defaults_to_system_weekly_generation():
    text = source()

    assert "default_system: bool = False" in text
    assert "index=1 if default_system else 0" in text
    assert "default_system=True" in text


def test_schedule_and_equipment_tables_resolve_ids_to_display_names():
    text = source()

    assert "def _resolve_lbg_display_names(" in text
    assert "class_names=class_names" in text
    assert "subject_names=subject_names" in text
    assert "component_names=component_names" in text
    assert "client=client" in text


def test_weekly_controls_use_one_compact_navy_row():
    text = source()
    for token in ("source_column,", "year_column,", "week_column,", "assignment_column,", "ppct_column,", "with source_column:", "with year_column:", "with week_column:", "with assignment_column:", "with ppct_column:"):
        assert token in text
    for token in ("background:#071a33", "font-size:15px", "min-height:76px", "padding:6px 10px", "range(1, 41)", 'f"Tu\u1ea7n {value}"', "SupabaseTeacherTimetableRepository(", "TeacherTimetableSlotStatus.ACTIVE", '"Lớp / Môn dạy"', '"Tự động · Tất cả môn"', "background:#fff", "color:#111", "font-weight:700"):
        assert token in text
    assert '"system_weekly_academic_year"' in text
    assert "get_canonical_context(" in text


def test_auto_ppct_uses_assignment_timetable_intersection():
    text = runtime_source()

    assert "TeacherTimetableSlotStatus.ACTIVE" in text
    assert "scheduled_assignment_ids" in text
    assert "slot.assignment_id" in text
    assert "if assignment.assignment_id" in text
    assert "in scheduled_assignment_ids" in text
