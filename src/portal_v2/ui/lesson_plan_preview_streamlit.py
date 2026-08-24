from __future__ import annotations

from document_intelligence.lesson_plan_preview_presenter import (
    LessonPlanPreviewViewModel,
    PreviewReviewState,
)


def render_lesson_plan_preview(
    *,
    st,
    view: LessonPlanPreviewViewModel,
) -> None:
    """
    Render a read-only lesson-plan intelligence preview.

    The renderer consumes an already prepared view model.
    It does not analyze documents, run AI, validate proposals,
    mutate Word files, persist data, or construct presenters.
    """

    if not isinstance(
        view,
        LessonPlanPreviewViewModel,
    ):
        raise TypeError(
            "view must be LessonPlanPreviewViewModel"
        )

    st.subheader(
        "Xem trước thông tin kế hoạch bài dạy"
    )

    if view.ai_failed:
        st.warning(
            "AI không hoàn thành phân tích. "
            "Kết quả hiện có vẫn được giữ để xem xét."
        )
    elif view.ai_used:
        st.info(
            "Kết quả có sử dụng hỗ trợ AI."
        )

    if not view.items:
        st.info(
            "Chưa nhận diện được thông tin để hiển thị."
        )
        return

    if view.requires_review:
        if view.conflict_count:
            st.warning(
                "Có thông tin cần giáo viên kiểm tra, "
                f"trong đó {view.conflict_count} mục "
                "xung đột với dữ liệu chuẩn."
            )
        else:
            st.warning(
                "Có thông tin cần giáo viên kiểm tra "
                "trước khi sử dụng."
            )
    else:
        st.success(
            "Các thông tin nhận diện hiện tại "
            "phù hợp với dữ liệu chuẩn."
        )

    for item in view.items:
        with st.container(
            border=True
        ):
            st.markdown(
                f"**{item.field_label}**"
            )

            st.write(
                item.value
            )

            st.caption(
                f"Nguồn: {item.source_label} · "
                f"Độ tin cậy: "
                f"{item.confidence_percent}%"
            )

            if item.evidence:
                st.caption(
                    f"Bằng chứng: {item.evidence}"
                )

            if (
                item.review_state
                is PreviewReviewState.ACCEPTED
            ):
                st.success(
                    "Phù hợp"
                )
            elif (
                item.review_state
                is PreviewReviewState.CONFLICT
            ):
                st.error(
                    "Xung đột — cần kiểm tra"
                )
            else:
                st.warning(
                    "Chưa xác minh — cần kiểm tra"
                )
