from pathlib import Path


TARGET = Path("src/portal_v2/ui/teacher_timetable_streamlit.py")


def test_teacher_timetable_has_clean_vietnamese_user_surface():
    text = TARGET.read_text(encoding="utf-8-sig")
    assert text.count('<div class="mt-timetable-hero">') == 1
    assert "Năm học đang áp dụng" in text
    assert "Cách thiết lập:" in text
    assert "Lớp → Môn → Phân môn" in text
    assert "Timetable data diagnostics" not in text
    assert "Performance audit - temporary" not in text


def test_teacher_timetable_keeps_business_and_persistence_boundaries():
    text = TARGET.read_text(encoding="utf-8-sig")
    assert "SupabaseTeacherTimetableRepository" in text
    assert "TeacherTimetableService" in text
    assert "resolve_canonical_assignment_id" in text
    assert "timetable_service.save_slot(" in text
    assert "timetable_repository.delete(" in text
    assert 'key="teacher_timetable_save"' in text
