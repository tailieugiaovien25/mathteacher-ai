from pathlib import Path


PORTAL_APP = Path("scripts/teacher_portal/app.py")
TIMETABLE_UI = Path("src/portal_v2/ui/teacher_timetable_streamlit.py")


def test_teacher_workspace_labels_keep_correct_vietnamese_unicode():
    text = PORTAL_APP.read_text(encoding="utf-8-sig")
    assert 'workspace = "Giáo viên"' in text
    assert '"Khu vực"' in text
    assert '("Giáo viên", "ADMIN")' in text
    assert "Gi?o vi?n" not in text
    assert "Khu v?c" not in text


def test_morning_and_afternoon_share_one_day_row():
    text = TIMETABLE_UI.read_text(encoding="utf-8-sig")
    assert "morning_column, afternoon_column = st.columns(" in text
    assert "with morning_column:" in text
    assert "with afternoon_column:" in text
    assert "st.divider()" not in text.split(
        "def render_day_card(", 1
    )[1].split("st.markdown(", 1)[0]


def test_session_widget_data_contract_is_unchanged():
    text = TIMETABLE_UI.read_text(encoding="utf-8-sig")
    assert 'f"{session.value}_"' in text
    assert "TeachingSession.MORNING" in text
    assert "TeachingSession.AFTERNOON" in text
    assert "selections[position]" in text
