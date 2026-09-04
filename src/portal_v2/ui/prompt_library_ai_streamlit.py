from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from prompt_library_v2 import PromptLibraryService, PromptProductType, PromptRenderError
from prompt_library_v2.defaults import default_math_prompts


PAGE_LABEL = "Thư viện Prompt & Trợ lý AI"
_PREVIEW_KEY = "prompt_library_ai_preview_v60"
_MESSAGES_KEY = "prompt_library_ai_messages_v60"
_RENDERED_PROMPT_KEY = "prompt_library_rendered_prompt_v60"

_PRODUCT_LABELS = {
    PromptProductType.LESSON_PLAN: "Tạo giáo án với Prompt",
    PromptProductType.ASSESSMENT_MATRIX: "Táº¡o ma tráº­n ÄKT vá»›i Prompt",
    PromptProductType.ASSESSMENT_SPECIFICATION: "Táº¡o báº£n Ä‘áº·c táº£ ÄKT vá»›i Prompt",
    PromptProductType.ASSESSMENT_EXAM: "Táº¡o ÄKT vá»›i Prompt",
}

_COMPONENTS = (
    "Sá»‘ vÃ  Äáº¡i sá»‘",
    "HÃ¬nh há»c vÃ  Äo lÆ°á»ng",
    "Thống kê và Xác suất",
)

_PAGE_CSS = """
<style>
.mt-prompt-page-anchor { display:none; }
.mt-prompt-hero {
  padding:1.15rem 1.25rem; margin:0 0 1rem; border:1px solid #dfe6f2;
  border-radius:18px; background:linear-gradient(135deg,#ffffff,#f3f7ff);
  box-shadow:0 10px 28px rgba(31,50,100,.07);
}
.mt-prompt-eyebrow {font-size:.76rem;font-weight:750;letter-spacing:.08em;color:#4c68c5;text-transform:uppercase}
.mt-prompt-title {margin:.25rem 0;font-size:clamp(1.7rem,2.2vw,2.25rem);font-weight:780;color:#17213a}
.mt-prompt-subtitle {max-width:920px;color:#667085;line-height:1.55}
.mt-prompt-section {margin:.9rem 0 .45rem;font-size:.78rem;font-weight:750;letter-spacing:.07em;color:#5068b6;text-transform:uppercase}
.mt-chat-intro {padding:.85rem 1rem;border:1px solid #dfe6f2;border-radius:14px;background:#f8faff;color:#526079}
section[data-testid="stMain"]:has(.mt-prompt-page-anchor) [data-testid="stMainBlockContainer"] {max-width:1500px;padding-top:1rem}
section[data-testid="stMain"]:has(.mt-prompt-page-anchor) [data-testid="stForm"] {border-radius:16px;background:#fff}
section[data-testid="stMain"]:has(.mt-prompt-page-anchor) [data-testid="stChatMessage"] {border:1px solid #e3e8f0;border-radius:14px;background:#fff}
section[data-testid="stMain"]:has(.mt-prompt-page-anchor) [data-testid="stChatInput"] {border-radius:14px}

section[data-testid="stMain"]:has(.mt-prompt-page-anchor)
[data-testid="stForm"]:has(textarea[aria-label="Y??u c???u d??nh cho AI"]) {
  margin-top:.65rem;padding:1rem 1.05rem;border:1px solid #dbe3ef;
  border-radius:16px;background:linear-gradient(135deg,#fff,#f7f9ff);
  box-shadow:0 8px 22px rgba(30,49,95,.07)
}
section[data-testid="stMain"]:has(.mt-prompt-page-anchor)
textarea[aria-label="Y??u c???u d??nh cho AI"] {
  border-radius:12px;background:#fff;font-size:.95rem;line-height:1.5
}
@media(max-width:700px){.mt-prompt-hero{padding:1rem}.mt-prompt-title{font-size:1.55rem}}
</style>
"""


def _resolve_ai_handler():
    # Reuse the canonical handler and provider resolution already used by the
    # lesson-authoring page. No second Gemini client is created here.
    from portal_v2.ui.lesson_authoring_ai_streamlit import _resolve_ai_handler as resolve
    return resolve()


def _preview_html(content: str, title: str) -> str:
    empty_message = (
        "Chưa có nội dung. Hãy tạo bản đầu tiên "
        "hoặc gửi yêu cầu cho AI."
    )
    safe_content = escape(content or empty_message)
    safe_title = escape(title)
    fit_label = "Vừa chiều rộng"
    compact_label = "Thu gọn"
    fullscreen_label = "Toàn màn hình"
    return f"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><style>
*{{box-sizing:border-box}}
body{{margin:0;background:#edf1f7;font-family:Inter,Segoe UI,Arial,sans-serif;color:#20293b}}
.shell{{min-height:560px;padding:14px}}
.toolbar{{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 14px;background:#fff;border:1px solid #dfe5ef;border-radius:14px 14px 0 0;box-shadow:0 4px 14px rgba(30,45,80,.05)}}
.title{{font-size:14px;font-weight:700;color:#33415f;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.tools{{display:flex;gap:7px;flex-wrap:wrap}}
button{{border:1px solid #cfd8e7;border-radius:9px;background:#fff;padding:7px 11px;color:#3655a8;font-weight:650;cursor:pointer}}
button:hover{{border-color:#5977d2;background:#eef3ff}}
.viewport{{height:490px;overflow:auto;padding:26px;background:#dfe5ed;border:1px solid #dfe5ef;border-top:0;border-radius:0 0 14px 14px}}
.paper{{width:min(100%,920px);min-height:760px;margin:0 auto;padding:54px 62px;background:#fff;box-shadow:0 14px 38px rgba(25,40,70,.14);font-family:'Times New Roman',serif;font-size:17px;line-height:1.65;white-space:pre-wrap}}
.fit .paper{{width:100%;max-width:none}}
.compact .paper{{font-size:15px;padding:36px 42px}}
:fullscreen .shell{{height:100vh;padding:12px;background:#e8edf4}}
:fullscreen .viewport{{height:calc(100vh - 58px)}}
@media(max-width:700px){{.viewport{{padding:10px}}.paper{{padding:28px 22px;font-size:15px}}.title{{display:none}}}}
</style></head><body>
<div class="shell" id="previewShell">
  <div class="toolbar"><div class="title">{safe_title}</div>
    <div class="tools">
      <button type="button" onclick="toggleFit()">{fit_label}</button>
      <button type="button" onclick="toggleCompact()">{compact_label}</button>
      <button type="button" onclick="full()">{fullscreen_label}</button>
    </div>
  </div>
  <div class="viewport" id="viewport"><article class="paper">{safe_content}</article></div>
</div>
<script>
function toggleFit(){{document.getElementById('viewport').classList.toggle('fit')}}
function toggleCompact(){{document.getElementById('viewport').classList.toggle('compact')}}
function full(){{const el=document.getElementById('previewShell');if(!document.fullscreenElement){{el.requestFullscreen()}}else{{document.exitFullscreen()}}}}
</script></body></html>"""


def _context(product_type: PromptProductType, grade: str, component: str, topic: str) -> dict[str, Any]:
    return {
        "subject_ref": "MATH",
        "subject_name": "Toán",
        "component_ref": component,
        "component_name": component,
        "grade_level": grade,
        "lesson_title": topic,
        "prompt_product_type": product_type.value,
    }


def render_prompt_library_ai_page(*, client=None, user_id: str = "") -> None:
    del client
    st.markdown(_PAGE_CSS, unsafe_allow_html=True)
    st.markdown('<span class="mt-prompt-page-anchor" aria-hidden="true"></span>', unsafe_allow_html=True)
    st.markdown(
        '<section class="mt-prompt-hero"><div class="mt-prompt-eyebrow">MathTeacher-AI · Không gian sáng tạo</div>'
        '<div class="mt-prompt-title">Thư viện Prompt &amp; Trợ lý AI</div>'
        '<div class="mt-prompt-subtitle">Chọn Prompt chuẩn, cung cấp dữ liệu chuyên môn, xem trước toàn màn hình và tiếp tục trao đổi với AI ngay bên dưới. AI chỉ đề xuất; giáo viên duyệt kết quả cuối cùng.</div></section>',
        unsafe_allow_html=True,
    )

    service = PromptLibraryService(default_math_prompts())
    product_options = tuple(_PRODUCT_LABELS)

    with st.form("prompt_library_input_form_v60"):
        st.markdown('<div class="mt-prompt-section">1 Â· Chá»n Prompt vÃ  dá»¯ liá»‡u Ä‘áº§u vÃ o</div>', unsafe_allow_html=True)
        first, second, third = st.columns([1.1, 1.2, .8])
        with first:
            product_type = st.selectbox("Loại sản phẩm", product_options, format_func=lambda item: _PRODUCT_LABELS[item])
        with second:
            component = st.selectbox("Mạch nội dung/phân môn", _COMPONENTS)
        with third:
            grade = st.selectbox("Khối lớp", ("6", "7", "8", "9"))
        topic = st.text_input("BÃ i há»c/chá»§ Ä‘á»", placeholder='Ví dụ: Phân số với tử và mẫu là số nguyên')
        requirements = st.text_area('Yêu cầu cần đạt', height=110, placeholder="Nháº­p hoáº·c dÃ¡n cÃ¡c yÃªu cáº§u cáº§n Ä‘áº¡t Ä‘Ã£ chá»n tá»« dá»¯ liá»‡u chuáº©n...")
        additional = st.text_area('Yêu cầu bổ sung', height=82, placeholder="Sá»‘ tiáº¿t, cáº¥u trÃºc Ä‘á», phÆ°Æ¡ng phÃ¡p, má»©c Ä‘á»™ phÃ¢n hÃ³a...")
        prepare = st.form_submit_button("Chuẩn bị Prompt", type="primary", use_container_width=True)

    prompt = service.find_active(subject_ref="MATH", product_type=product_type)[0]
    if prepare:
        try:
            rendered = service.render(prompt, {
                "grade_level": grade,
                "subject_component": component,
                "lesson_or_topic": topic,
                "learning_requirements": requirements,
                "additional_requirements": additional,
            })
            st.session_state[_RENDERED_PROMPT_KEY] = rendered.content
            st.session_state[_PREVIEW_KEY] = ""
            st.session_state[_MESSAGES_KEY] = []
            st.success("ÄÃ£ chuáº©n bá»‹ Prompt ACTIVE phiÃªn báº£n 1. CÃ³ thá»ƒ táº¡o báº£n Ä‘áº§u tiÃªn.")
        except PromptRenderError as error:
            st.error(str(error))

    rendered_prompt = str(st.session_state.get(_RENDERED_PROMPT_KEY, "") or "")
    preview = str(st.session_state.get(_PREVIEW_KEY, "") or "")
    title = _PRODUCT_LABELS[product_type] + " · Toán " + grade

    st.markdown('<div class="mt-prompt-section">2 · Xem trước sản phẩm</div>', unsafe_allow_html=True)
    components.html(_preview_html(preview, title), height=590, scrolling=False)

    action_left, action_middle, action_right = st.columns([1, 1, 1])
    handler, ai_status = _resolve_ai_handler()
    if action_left.button("Tạo bản đầu tiên", type="primary", use_container_width=True, disabled=not rendered_prompt):
        if not callable(handler):
            st.warning(ai_status)
        else:
            try:
                with st.spinner("AI đang tạo sản phẩm từ Prompt ACTIVE..."):
                    result = handler(request=rendered_prompt, document="", context=_context(product_type, grade, component, topic))
                if str(result or "").strip():
                    st.session_state[_PREVIEW_KEY] = str(result)
                    st.session_state[_MESSAGES_KEY] = [
                        {"role": "assistant", "content": "ÄÃ£ táº¡o báº£n Ä‘áº§u tiÃªn. Báº¡n cÃ³ thá»ƒ yÃªu cáº§u chá»‰nh sá»­a á»Ÿ cá»•ng AI bÃªn dÆ°á»›i."}
                    ]
                    st.rerun()
            except Exception as error:
                st.error("AI chưa tạo được sản phẩm: " + str(error))
    action_middle.download_button(
        "Tải bản nháp TXT", data=preview.encode("utf-8"), file_name="mathteacher-ai-draft.txt",
        mime="text/plain", use_container_width=True, disabled=not preview.strip(),
    )
    if action_right.button("Xóa bản xem trước", use_container_width=True, disabled=not preview.strip()):
        st.session_state[_PREVIEW_KEY] = ""
        st.session_state[_MESSAGES_KEY] = []
        st.rerun()

    st.markdown('<div class="mt-prompt-section">3 · Cổng giao tiếp với AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="mt-chat-intro">YÃªu cáº§u AI bá»• sung, viáº¿t láº¡i, rÃºt gá»n, kiá»ƒm tra lá»—i hoáº·c Ä‘iá»u chá»‰nh má»©c Ä‘á»™. Má»—i pháº£n há»“i táº¡o má»™t phiÃªn báº£n xem trÆ°á»›c má»›i; Prompt chuáº©n khÃ´ng bá»‹ thay Ä‘á»•i.</div>', unsafe_allow_html=True)
    if callable(handler):
        st.caption("Trạng thái AI: " + ai_status)
    else:
        st.warning(ai_status)

    messages = list(st.session_state.get(_MESSAGES_KEY, []))
    for message in messages:
        with st.chat_message(str(message.get("role", "assistant"))):
            st.markdown(str(message.get("content", "")))

    with st.form("prompt_library_ai_chat_form_v60", clear_on_submit=True):
        request = st.text_area(
            "Yêu cầu dành cho AI",
            height=105,
            placeholder=(
                "Ví dụ: Viết lại hoạt động luyện tập theo hướng phân hóa; "
                "kiểm tra lỗi và bổ sung tiêu chí đánh giá..."
            ),
            key="prompt_library_ai_request_v60",
        )
        send_request = st.form_submit_button(
            "Gửi yêu cầu cho AI",
            type="primary",
            use_container_width=True,
            disabled=not request.strip(),
        )

    if send_request:
        messages.append({"role": "user", "content": request})
        st.session_state[_MESSAGES_KEY] = messages
        if not callable(handler):
            messages.append({
                "role": "assistant",
                "content": (
                    "Dịch vụ AI chưa được cấu hình. Yêu cầu của bạn "
                    "đã được giữ trong phiên làm việc."
                ),
            })
            st.session_state[_MESSAGES_KEY] = messages
            st.rerun()
        try:
            with st.spinner("AI đang cập nhật phiên bản xem trước..."):
                revised = handler(
                    request=(
                        rendered_prompt
                        + "\n\nYÊU CẦU CHỈNH SỬA CỦA GIÁO VIÊN:\n"
                        + request
                    ),
                    document=preview,
                    context=_context(
                        product_type,
                        grade,
                        component,
                        topic,
                    ),
                )
            if str(revised or "").strip():
                st.session_state[_PREVIEW_KEY] = str(revised)
                messages.append({
                    "role": "assistant",
                    "content": (
                        "Đã cập nhật bản xem trước theo yêu cầu. "
                        "Vui lòng kiểm tra nội dung phía trên."
                    ),
                })
                st.session_state[_MESSAGES_KEY] = messages[-30:]
                st.rerun()
        except Exception as error:
            messages.append({
                "role": "assistant",
                "content": "AI chưa xử lý được yêu cầu: " + str(error),
            })
            st.session_state[_MESSAGES_KEY] = messages[-30:]
            st.rerun()

    st.caption("Phiên làm việc của USER: " + (str(user_id)[:8] or "-") + " · Prompt hệ thống chỉ do ADMIN quản trị.")
