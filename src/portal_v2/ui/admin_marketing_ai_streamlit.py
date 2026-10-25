from __future__ import annotations

from ai_platform.config import AIPlatformConfig
from ai_platform.factory import build_ai_provider
from ai_platform.marketing.service import MarketingAIService


def render_admin_marketing_ai(st, *, client=None) -> None:
    config = AIPlatformConfig.from_environment()
    st.title("AI Marketing")
    st.caption("Nhóm AI dành cho giai đoạn thương mại; mặc định TẮT trong bản giáo viên hiện tại.")

    if not config.commercial_mode:
        st.warning("Chế độ thương mại chưa bật. AI Marketing được khóa để tránh kích hoạt sớm.")
        st.checkbox("Cho phép AI Marketing", value=False, disabled=True)
        return
    if not config.marketing_enabled:
        st.warning("AI Marketing vẫn đang TẮT. Cần bật MARKETING_AI_ENABLED sau khi đã chuyển sang thương mại.")
        return

    provider = build_ai_provider(config)
    service = MarketingAIService(provider=provider, config=config)
    objective = st.text_area("Mục tiêu chiến dịch", placeholder="Ví dụ: giới thiệu tính năng mới...")
    audience = st.text_input("Đối tượng", value="Giáo viên")
    channel = st.selectbox("Kênh", ("Website", "Facebook", "Email", "Zalo"))
    st.caption("Nội dung chỉ là bản nháp. Không có chức năng tự gửi chiến dịch trong phiên bản này.")
    if st.button("Tạo bản nháp", type="primary"):
        if not objective.strip():
            st.error("Hãy nhập mục tiêu chiến dịch.")
            return
        try:
            st.markdown(service.draft(objective=objective, audience=audience, channel=channel))
        except Exception as exc:
            st.error(str(exc))
