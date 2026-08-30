from portal_v2.ui.admin_context_control_center_streamlit import _FIELD_LABELS,_KIND_LABELS,_AUTHORITY_LABELS,_STATUS_LABELS,_to_vietnamese_row

def test_vi_labels():
    assert _FIELD_LABELS["week_number"] == "Tuần học"
    assert _FIELD_LABELS["curriculum_period"] == "Tiết PPCT"
    assert _KIND_LABELS["GLOBAL"] == "Toàn hệ thống"
    assert _AUTHORITY_LABELS["ACTIVE_TEACHER_TIMETABLE"] == "Thời khóa biểu đang hiệu lực"
    assert _STATUS_LABELS["CONFLICT"] == "Xung đột"

def test_presentation_only():
    row={"canonical_field":"week_number","current_value":"2","kind":"GLOBAL","authority":"ACADEMIC_CALENDAR","state_keys":"global_weekly_active_week_number","observed_keys":"global_weekly_active_week_number","depends_on":"academic_year","invalidates":"subject_ref, grade","status":"OK"}
    vi=_to_vietnamese_row(row)
    assert vi["Trường ngữ cảnh"] == "Tuần học"
    assert vi["Nguồn dữ liệu chuẩn"] == "Lịch năm học"
    assert vi["Phụ thuộc vào"] == "Năm học"
    assert vi["Trạng thái đồng bộ"] == "Đồng bộ"
    assert row["canonical_field"] == "week_number"
