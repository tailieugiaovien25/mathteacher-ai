from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "scripts/teacher_portal/app.py"
PAGE = ROOT / "src/portal_v2/ui/prompt_library_ai_streamlit.py"


def test_prompt_library_page_is_wired_once_to_teacher_portal():
    app = APP.read_text(encoding="utf-8-sig")
    label = "Thư viện Prompt & AI"
    assert app.count(label) == 2
    assert "render_prompt_library_ai_page(" in app
    assert "client=client" in app
    assert "user_id=str(user_id)" in app


def test_prompt_library_page_has_four_active_product_types():
    text = PAGE.read_text(encoding="utf-8-sig")
    for token in (
        "PromptProductType.LESSON_PLAN",
        "PromptProductType.ASSESSMENT_MATRIX",
        "PromptProductType.ASSESSMENT_SPECIFICATION",
        "PromptProductType.ASSESSMENT_EXAM",
    ):
        assert token in text
    assert "PromptLibraryService(default_math_prompts())" in text
    assert "find_active(" in text


def test_preview_is_bright_compact_and_fullscreen_capable():
    text = PAGE.read_text(encoding="utf-8-sig")
    assert "components.html(" in text
    assert "requestFullscreen()" in text
    assert "background:#fff" in text
    assert "Vừa chiều rộng" in text
    assert "Thu gọn" in text
    assert "Toàn màn hình" in text
    assert "height=590, scrolling=False" in text


def test_ai_communication_portal_is_below_preview_and_reuses_handler():
    text = PAGE.read_text(encoding="utf-8-sig")
    assert text.index("components.html(") < text.index("prompt_library_ai_chat_form_v60")
    assert "st.chat_message(" in text
    assert "st.chat_input(" not in text
    assert "st.form_submit_button(" in text
    assert "_resolve_ai_handler" in text
    assert "handler(request=" in text
    assert "document=preview" in text


def test_new_page_preserves_teacher_final_authority_and_admin_prompt_ownership():
    text = PAGE.read_text(encoding="utf-8-sig")
    assert "AI chỉ đề xuất; giáo viên duyệt kết quả cuối cùng" in text
    assert "Prompt hệ thống chỉ do ADMIN quản trị" in text
    ast.parse(text)
