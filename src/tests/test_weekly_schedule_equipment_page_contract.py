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

    assert "source_column," in text
    assert "year_column," in text
    assert "week_column," in text
    assert "assignment_column," in text
    assert "ppct_column," in text
    assert "with source_column:" in text
    assert "with year_column:" in text
    assert "with week_column:" in text
    assert "with assignment_column:" in text
    assert "with ppct_column:" in text
    assert "background:#071a33" in text
    assert "font-size:15px" in text
    assert "min-height:76px" in text
    assert "padding:6px 10px" in text
    assert '"portal_academic_year",\n                    "2026-2027",' in text
    assert "range(1, 41)" in text
    assert "index=0" in text
    assert 'f"Tu\\u1ea7n {value}"' in text
    assert "SupabaseTeacherTimetableRepository(" in text
    assert "TeacherTimetableSlotStatus.ACTIVE" in text
    assert '"Lớp / Môn dạy"' in text
    assert '"Tự động · Tất cả môn"' in text
    assert "background:#fff" in text
    assert "color:#111" in text
    assert "font-weight:700" in text


def test_auto_ppct_uses_assignment_timetable_intersection():
    text = runtime_source()

    assert "TeacherTimetableSlotStatus.ACTIVE" in text
    assert "scheduled_assignment_ids" in text
    assert "slot.assignment_id" in text
    assert "if assignment.assignment_id" in text
    assert "in scheduled_assignment_ids" in text
