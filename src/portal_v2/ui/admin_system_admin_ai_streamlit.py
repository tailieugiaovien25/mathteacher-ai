from __future__ import annotations

import os

from ai_platform.config import AIPlatformConfig
from ai_platform.factory import build_ai_provider
from ai_platform.system_admin.service import SystemAdminAIService


def render_admin_system_admin_ai(st, *, client=None) -> None:
    config = AIPlatformConfig.from_environment()
    st.title("AI Quản trị hệ thống")
    st.caption("Trợ lý vận hành theo nguyên tắc quan sát → phân tích → con người phê duyệt thao tác.")

    cols = st.columns(4)
    cols[0].metric("AI", "BẬT" if config.system_admin_enabled else "TẮT")
    cols[1].metric("Provider", config.provider)
    cols[2].metric("Model", config.model)
    cols[3].metric("Chế độ", "Local" if config.provider == "ollama" else "External")

    st.info("AI chỉ đọc/giải thích trạng thái trong phiên bản này. Không tự xóa, sửa hoặc triển khai dữ liệu production.")

    from portal_v2.ui.admin_ai_control_panel import render_admin_ai_control_panel
    render_admin_ai_control_panel(st)
    st.markdown("---")
    checks = (
        {"name": "Python runtime", "status": "configured" if os.sys.version_info >= (3, 11) else "warning"},
        {"name": "AI provider", "status": config.provider},
        {"name": "Supabase", "status": "configured" if os.getenv("SUPABASE_URL") else "not-configured"},
    )
    st.dataframe(checks, hide_index=True, use_container_width=True)

    if not config.system_admin_enabled:
        st.warning("SYSTEM_ADMIN_AI_ENABLED đang tắt. Bật bằng biến môi trường khi muốn dùng AI phân tích.")
        return
    provider = build_ai_provider(config)
    service = SystemAdminAIService(provider=provider, config=config)
    if st.button("Phân tích báo cáo vận hành", type="primary"):
        diagnostic = service.diagnose(checks)
        try:
            st.markdown(service.explain(diagnostic))
        except Exception as exc:
            st.error(f"AI local chưa sẵn sàng: {exc}")
