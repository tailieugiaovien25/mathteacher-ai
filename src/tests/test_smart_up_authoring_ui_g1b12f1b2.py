from pathlib import Path

UI = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")

def source():
    return UI.read_text(encoding="utf-8-sig")

def test_smart_up_button_is_present():
    text = source()
    assert '"Up giáo án"' in text
    assert "resolve_from_catalog" in text
    assert "SupabaseTeacherDocumentRepository" in text

def test_smart_up_is_user_scoped():
    assert "user_id=str(user_id)" in source()

def test_multiple_matches_are_not_silently_selected():
    text = source()
    assert 'smart_up_resolution.status == "MULTIPLE"' in text
    assert "Hệ thống chưa tự chọn để tránh tải nhầm." in text

def test_manual_noncanonical_filename_is_warning_not_rejection():
    text = source()
    assert "Tên tệp chưa theo tên chuẩn của nhóm." in text
    assert "elif expected_file_name and uploaded.name != expected_file_name:" not in text