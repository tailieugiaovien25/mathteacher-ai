from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "portal_v2" / "ui" / "assessment_exam_settings_streamlit.py"
APP = ROOT.parent / "scripts" / "teacher_portal" / "app.py"


def test_teacher_navigation_places_settings_before_blueprint() -> None:
    text = APP.read_text(encoding="utf-8-sig")
    assert "'Thi\\u1ebft \\u0111\\u1eb7t \\u0111\\u1ec1 ki\\u1ec3m tra'" in text
    assert 'selected == "Thiết đặt đề kiểm tra"' in text
    assert "render_assessment_exam_settings_page" in text
    assert text.index('selected == "Thiết đặt đề kiểm tra"') < text.index(
        'selected == "Ma trận & bản đặc tả"'
    )


def test_page_covers_teaching_scope_curriculum_and_capabilities() -> None:
    text = UI.read_text(encoding="utf-8")
    for label in (
        "SGK, PPCT và tiến độ thực dạy",
        "Yêu cầu cần đạt",
        "Phẩm chất và năng lực",
        "Chính sách tạo và xuất đề",
        "Chỉ lấy nội dung đã dạy",
        "Ngày chốt nội dung đã dạy",
        "INTERSECTION",
        "DIRECT",
        "INDIRECT",
        "CONTEXTUAL",
    ):
        assert label in text


def test_page_reads_canonical_catalogs_and_writes_only_through_rpc() -> None:
    text = UI.read_text(encoding="utf-8")
    for table in (
        "assessment_exam_setting_presets",
        "assessment_profiles",
        "textbook_catalog",
        "textbook_units",
        "assessment_learning_requirements",
    ):
        assert table in text
    for rpc in (
        "save_assessment_exam_setting_draft",
        "submit_assessment_exam_setting_for_review",
        "review_assessment_exam_setting",
    ):
        assert rpc in text
    for forbidden in (".insert(", ".update(", ".delete(", "service_role"):
        assert forbidden not in text


def test_default_values_come_from_preset_payload() -> None:
    text = UI.read_text(encoding="utf-8")
    assert "default_preset" in text
    assert "preset_values" in text
    assert "question_selection_policy" in text
    assert "competency_targets" in text
    assert "Đang dùng preset mặc định" in text
