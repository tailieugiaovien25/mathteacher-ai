import json
from pathlib import Path

from lesson_planning_v2.services.lesson_plan_standardizer_profile_adapter import (
    build_runtime_standardizer_profile,
)


def test_admin_format_panel_exposes_locked_group_one_controls():
    text = Path("src/portal_v2/ui/admin_lesson_plan_coordination_center_streamlit.py").read_text(encoding="utf-8")
    for marker in (
        '"Khổ giấy"', '"Times New Roman"', '"Arial"', '"Calibri"',
        '"Màu chữ"', '"Độ giãn chữ (pt)"', '"Bật khung trang"',
        '"Lặp hàng tiêu đề bảng"', '"Chiều rộng tối đa hình/biểu đồ (%)"',
        '"preserve_value": True', '"rollback_on_integrity_failure": True',
    ):
        assert marker in text


def test_active_admin_profile_maps_to_runtime_and_formula_policy_is_locked(tmp_path):
    legacy = {
        "profile_name": "legacy",
        "page": {"margin_left_cm": 2, "margin_right_cm": 2, "margin_top_cm": 2, "margin_bottom_cm": 2},
        "body": {"font": "Arial", "size_pt": 12, "line_spacing": 1.0},
        "title": {"size_pt": 14},
        "table": {"size_pt": 11, "repeat_header": True, "allow_row_split": False},
        "header_footer": {},
        "equations": {"mode": "safe", "text_font": "Cambria Math"},
    }
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(legacy), encoding="utf-8")
    profile = build_runtime_standardizer_profile(
        legacy_profile_path=path,
        admin_template_profile={"layout": {
            "paper_size": "A5", "font_name": "Calibri", "font_color": "red",
            "body_font_size_pt": 15, "line_spacing": 1.3, "character_spacing_pt": 0.4,
            "margin_left_cm": 3, "margin_right_cm": 2, "margin_top_cm": 1.5, "margin_bottom_cm": 1,
            "page_border_enabled": True, "page_border_style": "double", "page_border_width_pt": 1,
            "table_border_style": "dashed", "table_border_width_pt": 0.75,
            "table_repeat_header": False, "table_allow_row_split": True,
        }},
    )
    assert profile["page"]["paper_size"] == "A5"
    assert profile["page"]["border_enabled"] is True
    assert profile["body"]["color_rgb"] == "FF0000"
    assert profile["body"]["character_spacing_pt"] == 0.4
    assert profile["table"]["repeat_header"] is False
    assert profile["equations"] == {
        "mode": "force_times", "text_font": "Times New Roman",
        "math_font": "Times New Roman", "preserve_omml_structure": True,
        "preserve_value": True, "rollback_on_integrity_failure": True,
    }
