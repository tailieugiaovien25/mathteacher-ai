from contextlib import nullcontext

import pytest

from document_intelligence.contracts import (
    AnalysisSource,
    DocumentField,
)
from document_intelligence.lesson_plan_preview_presenter import (
    LessonPlanPreviewItemView,
    LessonPlanPreviewViewModel,
    PreviewReviewState,
)
from document_intelligence.validation import (
    ValidationStatus,
)
from portal_v2.ui.lesson_plan_preview_streamlit import (
    render_lesson_plan_preview,
)


class FakeStreamlit:
    def __init__(self):
        self.calls = []

    def _record(
        self,
        name,
        value=None,
        **kwargs,
    ):
        self.calls.append(
            (name, value, kwargs)
        )

    def subheader(
        self,
        value,
    ):
        self._record(
            "subheader",
            value,
        )

    def warning(
        self,
        value,
    ):
        self._record(
            "warning",
            value,
        )

    def info(
        self,
        value,
    ):
        self._record(
            "info",
            value,
        )

    def success(
        self,
        value,
    ):
        self._record(
            "success",
            value,
        )

    def error(
        self,
        value,
    ):
        self._record(
            "error",
            value,
        )

    def markdown(
        self,
        value,
    ):
        self._record(
            "markdown",
            value,
        )

    def write(
        self,
        value,
    ):
        self._record(
            "write",
            value,
        )

    def caption(
        self,
        value,
    ):
        self._record(
            "caption",
            value,
        )

    def container(
        self,
        **kwargs,
    ):
        self._record(
            "container",
            None,
            **kwargs,
        )
        return nullcontext()


def make_item(
    *,
    field=DocumentField.CLASS_NAME,
    field_label="Lớp",
    value="6A1",
    confidence=0.99,
    confidence_percent=99,
    source=AnalysisSource.DETERMINISTIC,
    source_label="Quy tắc",
    evidence="Lớp: 6A1",
    validation_status=ValidationStatus.ACCEPTED,
    review_state=PreviewReviewState.ACCEPTED,
    requires_review=False,
):
    return LessonPlanPreviewItemView(
        field=field,
        field_label=field_label,
        value=value,
        confidence=confidence,
        confidence_percent=confidence_percent,
        source=source,
        source_label=source_label,
        evidence=evidence,
        validation_status=validation_status,
        review_state=review_state,
        requires_review=requires_review,
    )


def values_for(
    st,
    call_name,
):
    return [
        value
        for name, value, _ in st.calls
        if name == call_name
    ]


def test_renderer_rejects_invalid_view():
    with pytest.raises(
        TypeError,
        match="view must be LessonPlanPreviewViewModel",
    ):
        render_lesson_plan_preview(
            st=FakeStreamlit(),
            view=object(),
        )


def test_renderer_shows_accepted_item():
    st = FakeStreamlit()

    view = LessonPlanPreviewViewModel(
        items=(
            make_item(),
        ),
        ai_used=False,
        ai_failed=False,
        requires_review=False,
        conflict_count=0,
    )

    render_lesson_plan_preview(
        st=st,
        view=view,
    )

    assert (
        "Xem trước thông tin kế hoạch bài dạy"
        in values_for(st, "subheader")
    )
    assert "6A1" in values_for(
        st,
        "write",
    )
    assert "Phù hợp" in values_for(
        st,
        "success",
    )

    captions = values_for(
        st,
        "caption",
    )

    assert any(
        "Quy tắc" in value
        and "99%" in value
        for value in captions
    )

    assert any(
        "Lớp: 6A1" in value
        for value in captions
    )


def test_renderer_shows_conflict_and_ai_state():
    st = FakeStreamlit()

    item = make_item(
        value="6A2",
        confidence=0.95,
        confidence_percent=95,
        source=AnalysisSource.AI,
        source_label="AI",
        validation_status=ValidationStatus.CONFLICT,
        review_state=PreviewReviewState.CONFLICT,
        requires_review=True,
    )

    view = LessonPlanPreviewViewModel(
        items=(item,),
        ai_used=True,
        ai_failed=False,
        requires_review=True,
        conflict_count=1,
    )

    render_lesson_plan_preview(
        st=st,
        view=view,
    )

    assert (
        "Kết quả có sử dụng hỗ trợ AI."
        in values_for(st, "info")
    )

    assert any(
        "1 mục" in value
        and "xung đột" in value
        for value in values_for(
            st,
            "warning",
        )
    )

    assert (
        "Xung đột — cần kiểm tra"
        in values_for(st, "error")
    )


def test_renderer_shows_unverified_review():
    st = FakeStreamlit()

    item = make_item(
        field=DocumentField.LESSON_TITLE,
        field_label="Tên bài",
        value="Đơn thức",
        confidence=0.88,
        confidence_percent=88,
        source=AnalysisSource.AI,
        source_label="AI",
        evidence="",
        validation_status=ValidationStatus.UNVERIFIED,
        review_state=PreviewReviewState.REVIEW,
        requires_review=True,
    )

    view = LessonPlanPreviewViewModel(
        items=(item,),
        ai_used=True,
        ai_failed=False,
        requires_review=True,
        conflict_count=0,
    )

    render_lesson_plan_preview(
        st=st,
        view=view,
    )

    assert (
        "Chưa xác minh — cần kiểm tra"
        in values_for(
            st,
            "warning",
        )
    )


def test_renderer_shows_ai_failure_and_empty_state():
    st = FakeStreamlit()

    view = LessonPlanPreviewViewModel(
        items=(),
        ai_used=True,
        ai_failed=True,
        requires_review=False,
        conflict_count=0,
    )

    render_lesson_plan_preview(
        st=st,
        view=view,
    )

    assert any(
        "AI không hoàn thành phân tích" in value
        for value in values_for(
            st,
            "warning",
        )
    )

    assert (
        "Chưa nhận diện được thông tin để hiển thị."
        in values_for(st, "info")
    )


def test_renderer_uses_bordered_container():
    st = FakeStreamlit()

    view = LessonPlanPreviewViewModel(
        items=(
            make_item(),
        ),
        ai_used=False,
        ai_failed=False,
        requires_review=False,
        conflict_count=0,
    )

    render_lesson_plan_preview(
        st=st,
        view=view,
    )

    container_calls = [
        kwargs
        for name, _, kwargs in st.calls
        if name == "container"
    ]

    assert container_calls == [
        {"border": True}
    ]
