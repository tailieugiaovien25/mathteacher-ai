"""ADMIN read-only diagnostics for assessment export readiness."""

from __future__ import annotations

from typing import Any

from assessment_generation_v2.services import (
    SupabaseAssessmentRuntimeReadinessService,
)


STATUS_LABELS = {
    "PASS": "Sẵn sàng",
    "WARNING": "Thiếu dữ liệu",
    "BLOCKED": "Bị chặn",
}


def render_admin_assessment_runtime_readiness(
    st: Any,
    *,
    client: Any,
    service: Any | None = None,
) -> None:
    st.title("System Health")
    st.subheader("Mức độ sẵn sàng của module xuất đề")
    st.caption(
        "Kiểm tra chỉ đọc đối với schema, RPC, Storage và dữ liệu "
        "cần thiết để xuất bộ tài liệu."
    )

    if client is None and service is None:
        st.warning("Chưa có kết nối Supabase để thực hiện chẩn đoán.")
        return

    try:
        runtime_service = service or (
            SupabaseAssessmentRuntimeReadinessService(client=client)
        )
        report = runtime_service.inspect()
    except Exception as error:
        st.error(f"Không thể chạy chẩn đoán module xuất đề: {error}")
        return

    metrics = st.columns(3)
    metrics[0].metric("Sẵn sàng", report.passed_count)
    metrics[1].metric("Thiếu dữ liệu", report.warning_count)
    metrics[2].metric("Bị chặn", report.blocked_count)

    if report.blocked_count:
        st.error(
            "Module chưa thể vận hành. Hãy áp dụng các migration còn "
            "thiếu hoặc sửa quyền truy cập được chỉ ra bên dưới."
        )
    elif report.warning_count:
        st.warning(
            "Hạ tầng đã sẵn sàng nhưng còn thiếu dữ liệu nghiệp vụ. "
            "Hãy xuất bản đề, tạo mã đề hoặc kích hoạt bộ mẫu."
        )
    else:
        st.success("Module xuất đề đã sẵn sàng vận hành.")

    st.dataframe(
        [
            {
                "Trạng thái": STATUS_LABELS[item.status],
                "Hạng mục": item.label,
                "Chi tiết": item.detail,
                "Mã kiểm tra": item.check_code,
            }
            for item in report.checks
        ],
        hide_index=True,
        use_container_width=True,
    )

    st.info(
        "Trang này không tự áp dụng migration, không tạo dữ liệu và "
        "không thay đổi quyền truy cập."
    )
