"""Teacher-facing OpenClaw chat workspace."""

from __future__ import annotations

import re
from typing import Any

import streamlit as st

from portal_v2.integrations import OpenClawCLI, OpenClawError


PAGE_LABEL = "Trợ lý OpenClaw"
_MESSAGES_KEY = "openclaw_chat_messages_v1"
_AGENT_KEY = "openclaw_chat_agent_v1"
_STATUS_KEY = "openclaw_gateway_status_v1"

_PAGE_CSS = """
<style>
.mt-openclaw-anchor{display:none}
.mt-openclaw-hero{padding:1.15rem 1.25rem;margin:0 0 1rem;border:1px solid #263756;
 border-radius:18px;background:linear-gradient(135deg,#091321,#142845);color:#fff;
 box-shadow:0 12px 30px rgba(7,18,35,.22)}
.mt-openclaw-title{font-size:clamp(1.65rem,2vw,2.15rem);font-weight:780}
.mt-openclaw-subtitle{margin-top:.35rem;color:#cad6e8;line-height:1.5;max-width:980px}
.mt-openclaw-note{padding:.8rem 1rem;border:1px solid #d9e2ef;border-radius:13px;
 background:#f7f9fc;color:#46566f}
section[data-testid="stMain"]:has(.mt-openclaw-anchor) [data-testid="stMainBlockContainer"]{max-width:1500px;padding-top:1rem}
section[data-testid="stMain"]:has(.mt-openclaw-anchor) [data-testid="stChatMessage"]{border:1px solid #e0e7f0;border-radius:15px;background:#fff}
</style>
"""


def _safe_session_key(user_id: str, agent_id: str) -> str:
    user = re.sub(r"[^a-zA-Z0-9_-]", "-", user_id.strip())[:32] or "local-user"
    agent = re.sub(r"[^a-zA-Z0-9_-]", "-", agent_id.strip())[:32]
    return f"mathteacher-ui-{agent}-{user}"


def render_openclaw_chat_page(
    *,
    client: Any = None,
    user_id: str = "",
    openclaw: OpenClawCLI | None = None,
    authorized: bool = False,
) -> None:
    del client
    runtime = openclaw or OpenClawCLI()
    st.markdown(_PAGE_CSS, unsafe_allow_html=True)
    st.markdown('<span class="mt-openclaw-anchor" aria-hidden="true"></span>', unsafe_allow_html=True)
    st.markdown(
        '<section class="mt-openclaw-hero"><div class="mt-openclaw-title">Trợ lý OpenClaw</div>'
        '<div class="mt-openclaw-subtitle">Giao việc cho agent OpenClaw ngay trong MathTeacher-AI. '
        'Gateway và quyền thực thi vẫn do OpenClaw kiểm soát; ứng dụng không lưu token truy cập.</div></section>',
        unsafe_allow_html=True,
    )

    if not authorized:
        st.error(
            "Chức năng này chỉ dành cho ADMIN vì OpenClaw có thể sử dụng "
            "công cụ và thao tác mã nguồn trên máy chủ."
        )
        return

    left, right = st.columns([1.35, 1])
    with left:
        agent_id = st.selectbox(
            "Agent làm việc",
            ("mathteacher-engineer", "main"),
            key=_AGENT_KEY,
            help="mathteacher-engineer là agent chuyên trách dự án MathTeacher-AI.",
        )
    with right:
        if st.button("Kiểm tra Gateway", use_container_width=True):
            status = runtime.gateway_status()
            st.session_state[_STATUS_KEY] = {
                "available": status.available,
                "message": status.message,
            }

    saved_status = st.session_state.get(_STATUS_KEY)
    if isinstance(saved_status, dict):
        if saved_status.get("available"):
            st.success(str(saved_status.get("message", "Gateway sẵn sàng.")))
        else:
            st.warning(str(saved_status.get("message", "Gateway chưa sẵn sàng.")))
    elif not runtime.installed:
        st.warning("Chưa tìm thấy OpenClaw trên máy đang chạy MathTeacher-AI.")

    st.markdown(
        '<div class="mt-openclaw-note">Chỉ gửi một lần cho mỗi nhiệm vụ. Nếu mất kết nối sau khi Gateway đã nhận lệnh, '
        'hãy kiểm tra phiên OpenClaw trước khi gửi lại để tránh thực hiện trùng.</div>',
        unsafe_allow_html=True,
    )

    messages = list(st.session_state.get(_MESSAGES_KEY, []))
    for message in messages:
        with st.chat_message(str(message.get("role", "assistant"))):
            st.markdown(str(message.get("content", "")))

    with st.form("openclaw_chat_form_v1", clear_on_submit=True):
        request = st.text_area(
            "Nội dung giao cho OpenClaw",
            height=120,
            placeholder="Ví dụ: Chỉ đọc mã nguồn và kiểm tra nguyên nhân lỗi của trang Lịch báo giảng. Không sửa file.",
        )
        send = st.form_submit_button(
            "Gửi nhiệm vụ",
            type="primary",
            use_container_width=True,
        )

    controls, _ = st.columns([1, 3])
    if controls.button("Xóa nội dung chat", use_container_width=True, disabled=not messages):
        st.session_state[_MESSAGES_KEY] = []
        st.rerun()

    if not send:
        return

    messages.append({"role": "user", "content": request})
    st.session_state[_MESSAGES_KEY] = messages[-40:]
    try:
        with st.spinner(f"Agent {agent_id} đang xử lý nhiệm vụ..."):
            result = runtime.send_turn(
                message=request,
                agent_id=agent_id,
                session_key=_safe_session_key(user_id, agent_id),
            )
        messages.append({"role": "assistant", "content": result.text})
    except (OpenClawError, ValueError) as error:
        messages.append({
            "role": "assistant",
            "content": "OpenClaw chưa xử lý được yêu cầu: " + str(error),
        })
    st.session_state[_MESSAGES_KEY] = messages[-40:]
    st.rerun()
