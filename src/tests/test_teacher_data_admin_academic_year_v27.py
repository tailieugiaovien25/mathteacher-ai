from pathlib import Path


APP = Path("scripts/teacher_portal/app.py")


def _my_data_block() -> str:
    text = APP.read_text(encoding="utf-8-sig")
    return text.split('elif selected == "Dữ liệu của tôi":', 1)[1].split(
        'elif selected == "Thiết đặt giáo viên":', 1
    )[0]


def test_my_data_reads_current_academic_year_from_admin_repository():
    block = _my_data_block()
    assert "SupabaseAcademicYearConfigurationRepository" in block
    assert "client=client" in block
    assert ".get_current()" in block
    assert "admin_current_year.academic_year" in block


def test_my_data_year_is_read_only_and_shared_in_session():
    block = _my_data_block()
    assert '"teacher_data_academic_year"' in block
    assert 'key="teacher_data_academic_year_display"' in block
    assert "disabled=True" in block
    assert "ADMIN thi\\u1ebft l\\u1eadp" in block


def test_my_data_stops_safely_when_admin_has_no_current_year():
    block = _my_data_block()
    assert "if admin_current_year is None:" in block
    assert "st.warning(" in block
    assert "ADMIN ch\\u01b0a thi\\u1ebft l\\u1eadp" in block
    assert "return" in block
