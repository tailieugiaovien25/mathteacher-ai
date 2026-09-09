from pathlib import Path


TARGET = Path("src/portal_v2/ui/teacher_timetable_streamlit.py")


def _source() -> str:
    return TARGET.read_text(encoding="utf-8-sig")


def test_header_is_one_compact_dark_three_dimensional_control_panel():
    text = _source()
    assert text.count('<div class="mt-timetable-hero">') == 1
    assert "linear-gradient(145deg,#102d4d 0%,#06182d 58%,#020914 100%)" in text
    assert "Năm học đang áp dụng:" in text
    assert "mt-timetable-guide" in text
    assert "box-shadow:5px 6px 0 #163454" in text
    assert "mt-timetable-context" not in text


def test_morning_and_afternoon_are_rendered_in_the_same_row():
    text = _source()
    assert "morning_column, afternoon_column = st.columns(" in text
    assert "with morning_column:" in text
    assert "with afternoon_column:" in text
    assert 'title="☀ Buổi sáng"' in text
    assert 'title="☾ Buổi chiều"' in text


def test_data_fields_keep_white_surface_and_dark_contrast_borders():
    text = _source()
    assert "border: 1.5px solid #173f67 !important" in text
    assert "background:#fff!important" in text
    assert "mt-session-title" in text
    assert "background:linear-gradient(145deg,#123a61,#06182d)" in text
    assert "color:#fff" in text


def test_business_persistence_boundaries_remain_present():
    text = _source()
    assert "TeacherTimetableService(" in text
    assert "timetable_repository.delete(" in text
    assert "timetable_service.save_slot(" in text
    assert 'key="teacher_timetable_save"' in text
