from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "src" / "portal_v2" / "ui" / "admin_lesson_plan_coordination_center_streamlit.py"


def _text():
    return TARGET.read_text(encoding="utf-8")


def test_grouping_policy_moved_to_subject_group():
    text = _text()
    group_i = text.index('st.header("I. Cấu hình toàn hệ thống về giáo án")')
    group_ii = text.index('st.header("II. Cấu hình giáo án theo môn")')
    group_iii = text.index('st.header("III. Cấu hình các công cụ")')
    grouping = text.index('st.subheader("Chính sách nhóm giáo án")')
    assert group_i < group_ii < grouping < group_iii


def test_no_grouping_renderer_remains_in_group_i():
    text = _text()
    group_i = text.index('st.header("I. Cấu hình toàn hệ thống về giáo án")')
    group_ii = text.index('st.header("II. Cấu hình giáo án theo môn")')
    assert "render_admin_lesson_plan_grouping_policy" not in text[group_i:group_ii]


def test_existing_renderer_reused_once_in_coordination_center():
    text = _text()
    assert text.count("render_admin_lesson_plan_grouping_policy(st, client=client)") == 1


def test_vietnamese_business_labels_present():
    text = _text()
    assert "Chính sách nhóm giáo án" in text
    assert "Theo tiết PPCT" in text
    assert "mỗi tiết là một giáo án" in text
    assert "Theo bài" in text
    assert "nhiều tiết cùng bài dùng chung một giáo án" in text