from __future__ import annotations

from document_intelligence.lesson_plan_teacher_review import (
    LessonPlanTeacherReview,
    TeacherFieldDecision,
    TeacherReviewAction,
)
from document_intelligence.lesson_plan_teacher_review_presenter import (
    LessonPlanTeacherReviewViewModel,
)


_ACTION_OPTIONS = (
    TeacherReviewAction.CONFIRM,
    TeacherReviewAction.OVERRIDE,
    TeacherReviewAction.REJECT,
)

_ACTION_LABELS = {
    TeacherReviewAction.CONFIRM: (
        "Xác nhận"
    ),
    TeacherReviewAction.OVERRIDE: (
        "Thay đổi"
    ),
    TeacherReviewAction.REJECT: (
        "Chưa chấp nhận"
    ),
}


def render_lesson_plan_teacher_review(
    *,
    st,
    view: LessonPlanTeacherReviewViewModel,
    key_prefix: str = "lesson_plan_teacher_review",
) -> LessonPlanTeacherReview:
    if not isinstance(
        view,
        LessonPlanTeacherReviewViewModel,
    ):
        raise TypeError(
            "view must be LessonPlanTeacherReviewViewModel"
        )

    st.subheader(
        "Thông tin đối chiếu"
    )

    if view.requires_review:
        st.info(
            "Hệ thống đã đối chiếu thông tin trong giáo án "
            "với dữ liệu bài dạy hiện tại. "
            "Kiểm tra các mục cần thiết trước khi tiếp tục."
        )
    else:
        st.success(
            "Thông tin giáo án phù hợp với dữ liệu bài dạy."
        )

    decisions = []

    for index, item in enumerate(
        view.items
    ):
        detected_value = (
            item.detected_value
            if item.detected_value is not None
            else ""
        )

        canonical_value = (
            item.canonical_value
            if item.canonical_value is not None
            else ""
        )

        default_index = (
            _ACTION_OPTIONS.index(
                item.default_action
            )
        )

        columns = st.columns(
            [1.2, 2.0, 2.0, 1.8],
            gap="small",
        )

        with columns[0]:
            st.markdown(
                f"**{item.field_label}**"
            )

        with columns[1]:
            st.write(
                detected_value
                or "—"
            )

        with columns[2]:
            st.write(
                canonical_value
                or "—"
            )

        with columns[3]:
            action = st.selectbox(
                "Xử lý",
                options=_ACTION_OPTIONS,
                index=default_index,
                format_func=lambda value: (
                    _ACTION_LABELS[value]
                ),
                key=(
                    f"{key_prefix}_"
                    f"{index}_"
                    f"{item.field.value}_action"
                ),
                label_visibility="collapsed",
            )

        override_value = None

        if (
            action
            is TeacherReviewAction.OVERRIDE
        ):
            override_value = st.text_input(
                (
                    "Giá trị thay thế · "
                    + item.field_label
                ),
                value=(
                    canonical_value
                    or detected_value
                ),
                key=(
                    f"{key_prefix}_"
                    f"{index}_"
                    f"{item.field.value}_override"
                ),
            )

        decisions.append(
            TeacherFieldDecision(
                field=item.field,
                action=action,
                detected_value=(
                    item.detected_value
                ),
                canonical_value=(
                    item.canonical_value
                ),
                override_value=(
                    override_value
                ),
            )
        )

    return LessonPlanTeacherReview(
        decisions=tuple(decisions)
    )
