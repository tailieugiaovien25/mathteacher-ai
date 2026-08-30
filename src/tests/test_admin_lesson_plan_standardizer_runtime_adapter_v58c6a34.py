from __future__ import annotations
import json
from pathlib import Path
from lesson_planning_v2.services.lesson_plan_standardizer_profile_adapter import build_runtime_standardizer_profile

def _legacy_profile(tmp_path: Path) -> Path:
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps({
        "profile_name": "legacy",
        "page": {"margin_left_cm": 3.0, "margin_right_cm": 2.0, "margin_top_cm": 2.0, "margin_bottom_cm": 2.0},
        "body": {"font": "Times New Roman", "size_pt": 14, "line_spacing": 1.15},
        "title": {"size_pt": 14},
        "table": {"size_pt": 14, "repeat_header": True, "allow_row_split": True},
        "header_footer": {"remove_existing": True, "page_number": True, "page_number_alignment": "center"},
        "equations": {"mode": "force_times", "text_font": "Times New Roman", "math_font": "Times New Roman", "preserve_omml_structure": True},
    }), encoding="utf-8")
    return path

def test_adapter_preserves_legacy_profile_without_admin_payload(tmp_path):
    path = _legacy_profile(tmp_path)
    result = build_runtime_standardizer_profile(legacy_profile_path=path, admin_template_profile=None)
    assert result == json.loads(path.read_text(encoding="utf-8"))

def test_adapter_maps_rich_admin_layout_only_to_supported_word_fields(tmp_path):
    result = build_runtime_standardizer_profile(
        legacy_profile_path=_legacy_profile(tmp_path),
        admin_template_profile={"profile_name": "ADMIN Toán", "layout": {
            "font_name": "Arial", "body_font_size_pt": 13, "line_spacing": 1.25,
            "margin_left_cm": 2.5, "margin_right_cm": 1.8, "unknown_layout_key": "ignored"}},
    )
    assert result["profile_name"] == "ADMIN Toán"
    assert result["body"]["font"] == "Arial"
    assert result["body"]["size_pt"] == 13
    assert result["body"]["line_spacing"] == 1.25
    assert result["page"]["margin_left_cm"] == 2.5
    assert result["page"]["margin_right_cm"] == 1.8
    assert result["equations"]["text_font"] == "Times New Roman"
    assert "unknown_layout_key" not in result["body"]

def test_adapter_ignores_invalid_numeric_admin_values(tmp_path):
    result = build_runtime_standardizer_profile(
        legacy_profile_path=_legacy_profile(tmp_path),
        admin_template_profile={"layout": {"body_font_size_pt": -1, "line_spacing": 0, "margin_left_cm": -2}},
    )
    assert result["body"]["size_pt"] == 14
    assert result["body"]["line_spacing"] == 1.15
    assert result["page"]["margin_left_cm"] == 3.0

def test_document_processing_service_retains_path_fallback_and_accepts_runtime_profile():
    text = Path("src/lesson_planning_v2/services/lesson_plan_document_processing_service.py").read_text(encoding="utf-8-sig")
    assert "profile: dict[str, object] | None = None" in text
    assert "LessonPlanWordStandardizer.from_json(" in text
    assert "LessonPlanWordStandardizer(" in text

def test_only_base_processor_consumes_admin_template_profile():
    text = Path("src/portal_v2/ui/weekly_schedule_streamlit.py").read_text(encoding="utf-8-sig")
    assert text.count("def _process_lesson_plan_upload(") == 4
    assert text.count('"lesson_plan_admin_template_profile"') == 1
    assert text.count("build_runtime_standardizer_profile(") == 1
