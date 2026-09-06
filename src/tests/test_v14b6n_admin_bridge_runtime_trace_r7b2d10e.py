from pathlib import Path

APP = Path("scripts/teacher_portal/app.py")
UI = Path(
    "src/portal_v2/ui/"
    "standardized_lesson_plan_authoring_v2_streamlit.py"
)


def test_d10e_app_captures_three_sanitized_bridge_stages():
    text = APP.read_text(encoding="utf-8")

    assert "V14B6N_R7B2D10E_ADMIN_BRIDGE_TRACE_BEFORE_APPLY" in text
    assert "V14B6N_R7B2D10E_ADMIN_BRIDGE_TRACE_AFTER_APPLY" in text
    assert "V14B6N_R7B2D10E_ADMIN_BRIDGE_TRACE_AFTER_OVERLAY" in text
    assert '"admin_state_enabled"' in text
    assert '"admin_state_provider"' in text
    assert '"payload_after_apply_present"' in text
    assert '"payload_after_apply_ai_runtime_present"' in text
    assert '"overlay_written"' in text
    assert '"overlay_enabled"' in text
    assert '"overlay_provider"' in text


def test_d10e_trace_does_not_capture_credentials_or_secrets():
    text = APP.read_text(encoding="utf-8")

    start = text.index("V14B6N_R7B2D10E_ADMIN_BRIDGE_TRACE_BEFORE_APPLY")
    end = text.index(
        "V14B6N_R7B2D10E_ADMIN_BRIDGE_TRACE_AFTER_OVERLAY"
    )
    block = text[start:end + 2200]

    assert "GEMINI_API_KEY" not in block
    assert "OPENAI_API_KEY" not in block
    assert "secret_value" not in block
    assert "st.secrets" not in block


def test_d10e_ui_renders_bridge_trace_separately_from_runtime_status():
    text = UI.read_text(encoding="utf-8")

    assert "V14B6N_R7B2D10E_ADMIN_BRIDGE_TRACE_UI" in text
    assert "Dấu vết bridge ADMIN → runtime" in text
    assert "ADMIN state trước khi áp dụng cấu hình" in text
    assert "Payload sau apply_active_admin... tồn tại" in text
    assert "AI overlay đã được ghi" in text
    assert "Provider sau overlay" in text
    assert "Trạng thái AI: ĐÃ SỬ DỤNG AI" in text
    assert "Trạng thái AI: KHÔNG SỬ DỤNG AI" in text


def test_d10e_ui_does_not_render_secret_material():
    text = UI.read_text(encoding="utf-8")

    start = text.index("V14B6N_R7B2D10E_ADMIN_BRIDGE_TRACE_UI")
    block = text[start:start + 5200]

    assert "GEMINI_API_KEY" not in block
    assert "OPENAI_API_KEY" not in block
    assert "secret_value" not in block