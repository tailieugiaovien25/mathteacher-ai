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
        "Xác nhận thông tin kế hoạch bài dạy"
    )

    if view.requires_review:
        st.warning(
            "Có thông tin cần giáo viên kiểm tra "
            "trước khi tiếp tục."
        )
    else:
        st.info(
            "Thông tin đã phù hợp. "
            "Giáo viên có thể xác nhận hoặc chỉnh sửa."
        )

    decisions = []

    for index, item in enumerate(view.items):
        st.markdown(
            f"**{item.field_label}**"
        )

        st.write(
            "Giá trị nhận diện: "
            f"{item.detected_value}"
        )

        if item.canonical_value is not None:
            st.write(
                "Giá trị chuẩn: "
                f"{item.canonical_value}"
            )

        default_index = (
            _ACTION_OPTIONS.index(
                item.default_action
            )
        )

        action = st.radio(
            "Quyết định",
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
        )

        override_value = None

        if action is TeacherReviewAction.OVERRIDE:
            override_value = st.text_input(
                "Giá trị thay thế",
                value=(
                    item.canonical_value
                    or item.detected_value
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
