from pathlib import Path


WEEKLY_UI = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")
PORTAL_APP = Path("scripts/teacher_portal/app.py")
TIMETABLE_UI = Path("src/portal_v2/ui/teacher_timetable_streamlit.py")


def test_selected_unit_expands_all_rows_for_class_and_date_controls():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")
    assert "def _rows_for_selected_lesson_unit(" in text
    assert "selected_unit=selected_unit" in text
    assert "for index in tuple(getattr(selected_unit, \"row_indices\"" in text


def test_class_and_date_labels_expose_per_class_schedule_data():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")
    assert '"Lớp dạy"' in text
    assert '"Ngày dạy"' in text
    assert 'teaching_date.strftime("%d/%m/%Y")' in text
    assert "selected_class_ids = tuple(dict.fromkeys(" in text
    assert "selected_teaching_date_pairs = tuple(dict.fromkeys(" in text


def test_legacy_authoring_hub_is_hidden_without_deleting_route():
    text = PORTAL_APP.read_text(encoding="utf-8-sig")
    pages_block = text.split("PORTAL_PAGES = (", 1)[1].split(")", 1)[0]
    assert "Công cụ soạn bài" not in pages_block
    assert "render_lesson_authoring_tools_workspace" in text


def test_timetable_groups_each_day_in_a_modern_tab_card():
    text = TIMETABLE_UI.read_text(encoding="utf-8-sig")
    assert "day_tabs = st.tabs" in text
    assert "mt-timetable-hero" in text
    assert "mt-day-heading" in text
    assert "scheduled_count = sum(" in text
