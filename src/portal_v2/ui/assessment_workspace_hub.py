"""Teacher entry point for the existing assessment workflows.

This page only routes to legacy renderers. It does not write assessment data.
"""

from __future__ import annotations


ASSESSMENT_PRIMARY_DESTINATIONS = (
    ("Ngân hàng câu hỏi", "AI xây dựng ngân hàng câu hỏi", "Xem và quản lý câu hỏi đã lưu."),
    ("Giáo viên tạo câu hỏi", "AI xây dựng ngân hàng câu hỏi", "Soạn câu hỏi mới theo nội dung SGK; có thể dùng AI hỗ trợ."),
    ("Phạm vi & thiết đặt", "Thiết đặt đề kiểm tra", "Chọn lớp, SGK, PPCT, YCCĐ và cấu trúc bài kiểm tra."),
    ("Ma trận & bản đặc tả", "Ma trận & bản đặc tả", "Xem và hoàn thiện cấu trúc đề trước khi ráp câu."),
    ("Tạo đề theo ma trận", "Tạo đề kiểm tra", "Ráp bản nháp từ ma trận đã duyệt và câu hỏi phù hợp."),
    ("Xuất đề", "Xuất đề kiểm tra", "Xem trước và xuất đề theo trạng thái, chính sách hiện hành."),
)

ASSESSMENT_EXPERIMENTAL_DESTINATIONS = (
    ("Xưởng nháp", "Xưởng câu hỏi", "Thử nghiệm: bản nháp trong phiên, chưa ghi CSDL."),
    ("Xem trước cấu hình 6–9", "Tạo đề kiểm tra Toán 6–9", "Thử nghiệm: đọc dữ liệu và xem trước, chưa lưu CSDL."),
    ("Demo Toán 6", "Tạo đề kiểm tra Toán 6", "Demo: không dùng để phát hành đề chính thức."),
)

ASSESSMENT_LEGACY_DESTINATIONS = frozenset(
    target for _, target, _ in (*ASSESSMENT_PRIMARY_DESTINATIONS,
                                *ASSESSMENT_EXPERIMENTAL_DESTINATIONS)
)


def open_assessment_destination(st, *, label: str, target: str, navigate) -> None:
    """Open the bank in the requested mode before switching pages."""
    if target == "AI xây dựng ngân hàng câu hỏi":
        st.session_state["content_ai_workspace_view"] = (
            "Soạn câu hỏi mới" if label == "Giáo viên tạo câu hỏi" else "Xem ngân hàng"
        )
    navigate(target)
    st.rerun()


def render_assessment_workspace_hub(st, *, navigate) -> None:
    """Render one entry point while preserving the existing page dispatcher."""
    st.title("Đề kiểm tra")
    st.caption("Từ câu hỏi đến đề kiểm tra: chọn công việc bạn muốn thực hiện.")

    sections = (
        ("1 · Câu hỏi", ASSESSMENT_PRIMARY_DESTINATIONS[:2]),
        ("2 · Thiết kế đề", ASSESSMENT_PRIMARY_DESTINATIONS[2:4]),
        ("3 · Tạo và xuất đề", ASSESSMENT_PRIMARY_DESTINATIONS[4:]),
    )
    for heading, destinations in sections:
        st.subheader(heading)
        columns = st.columns(len(destinations))
        for column, (label, target, description) in zip(columns, destinations):
            with column:
                with st.container(border=True):
                    st.markdown("**" + label + "**")
                    st.caption(description)
                    if st.button("Mở " + label, key="assessment_hub_" + label,
                                 use_container_width=True):
                        open_assessment_destination(st, label=label, target=target,
                                                    navigate=navigate)

    with st.expander("Công cụ thử nghiệm và demo", expanded=False):
        for label, target, description in ASSESSMENT_EXPERIMENTAL_DESTINATIONS:
            st.caption(label + " · " + description)
            if st.button("Mở " + label, key="assessment_hub_experimental_" + target):
                navigate(target)
                st.rerun()
