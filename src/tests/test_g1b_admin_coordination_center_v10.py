from pathlib import Path


UI = Path("src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py")


def test_coordination_center_has_three_non_overlapping_groups_and_save_actions():
    text = UI.read_text(encoding="utf-8")
    assert '"I. Cấu hình toàn hệ thống về giáo án"' in text
    assert '"II. Cấu hình giáo án theo môn"' in text
    assert '"III. Cấu hình các công cụ"' in text
    assert '"1. Công cụ chuẩn giáo án – Điều khiển AI"' in text
    assert text.count("group_key=") == 3
    assert text.count("render_admin_subject_coordination_workspace(client=client)") == 1
    assert text.count("_render_admin_configuration_write_workspace(st, client=client)") == 1
    assert text.count("render_admin_lesson_authoring_ai_settings(st, client=client)") == 1


def test_coordination_center_uses_consistent_modern_3d_visual_system():
    text = UI.read_text(encoding="utf-8")
    assert "_render_coordination_center_visual_system(st)" in text
    assert "linear-gradient(145deg" in text
    assert "box-shadow:" in text
    assert 'with st.container(border=True):' in text
    assert 'type="primary"' in text
