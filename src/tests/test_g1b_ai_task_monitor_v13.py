from pathlib import Path


UI = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py")


def test_v13b_has_inline_ai_task_monitor_and_full_width_preview():
    text = UI.read_text(encoding="utf-8")
    assert "G1B_V13B_INLINE_REAL_AI_TASK_MONITOR" in text
    assert "Tiến trình AI" in text
    assert "width:calc(300% + 2rem)" in text
    assert "height:132px" in text
    assert "G1B_V13B_INLINE_REAL_AI_TASK_MONITOR" in text
    assert "task_monitor_slot = actions[0].empty()" in text
    assert ".block-container{max-width:100%" in text
    assert "grid-template-columns:repeat(11" in text
    assert "@keyframes g1bwater" in text


def test_v13_lists_all_required_real_workflow_tasks():
    text = UI.read_text(encoding="utf-8")
    for label in (
        "Đọc và khóa cấu hình ADMIN",
        "Khổ giấy và lề trang",
        "Font, cỡ chữ và màu chữ",
        "Giãn dòng và giãn chữ",
        "Khung trang, bảng và biểu",
        "Kiểm tra tách hàng của bảng",
        "Font công thức Toán",
        "Giá trị công thức không đổi",
        "Nội dung, hình ảnh và cấu trúc",
        "Cổng tuân thủ cuối cùng",
        "Mở quyền Lưu, Tải xuống và Gộp",
    ):
        assert label in text


def test_v13_projects_compliance_evidence_instead_of_fake_completion():
    text = UI.read_text(encoding="utf-8")
    assert "_compliance_monitor_state" in text
    for code in (
        "ACTIVE_CONFIGURATION_SNAPSHOT",
        "PAGE_SIZE",
        "PAGE_MARGINS",
        "BODY_FONT",
        "FONT_COLOR",
        "CHARACTER_SPACING",
        "LINE_SPACING",
        "TABLE_ROW_SPLIT",
        "FORMULA_VALUE_INTEGRITY",
        "CONTENT_INTEGRITY",
        "MEDIA_INTEGRITY",
    ):
        assert code in text
    assert 'checks["RELEASE"] = "pass" if final_status == "PASS" else "blocked"' in text


def test_v13b_passes_real_pipeline_progress_callback_and_preview_trace():
    text = UI.read_text(encoding="utf-8")
    assert '"progress_callback" in handler_signature.parameters' in text
    assert "_apply_real_progress_event" in text
    assert 'handler_arguments["progress_callback"]' in text
    assert "Quá trình tạo bản xem:" in text
    assert "Xem nhật ký các công đoạn đã tác động đến giáo án" in text


def test_v13_preserves_v12a_save_download_merge_gate():
    text = UI.read_text(encoding="utf-8")
    assert "release_allowed = canonical_pass_100" in text
    assert "audit_blocks_save = not release_allowed" in text
    assert 'disabled=(not standardized_content or audit_blocks_save)' in text
    assert "if standardized_content:" in text
    assert "if not audit_blocks_save:" in text
