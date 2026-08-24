from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UI_FILE = (
    ROOT
    / "src"
    / "portal_v2"
    / "ui"
    / "weekly_schedule_streamlit.py"
)


def source() -> str:
    return UI_FILE.read_text(encoding="utf-8")


def test_standardization_page_hides_entry_actions():
    text = source()

    assert "show_entry_actions: bool = True" in text
    assert 'if page_title == "Chuẩn hóa giáo án":' in text
    assert "omit the legacy entry hub" in text
    assert "if not show_entry_actions:" in text
    assert "return active_focus" in text


def test_entry_actions_remain_available_for_other_workspaces():
    text = source()

    assert '"✨ Bắt đầu soạn bài"' in text
    assert '"📁 Chọn tệp giáo án"' in text
    assert 'key="lesson_authoring_open_ai"' in text
    assert 'key="lesson_authoring_open_standardization"' in text
