from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.lesson_plan_preview_presenter import (
    PreviewReviewState,
)
from document_intelligence.lesson_plan_teacher_review import (
    TeacherReviewAction,
)
from document_intelligence.lesson_plan_teacher_review_presenter import (
    LessonPlanTeacherReviewViewModel,
    TeacherReviewItemView,
)
from portal_v2.ui.lesson_plan_teacher_review_streamlit import (
    render_lesson_plan_teacher_review,
)


class FakeStreamlit:
    def __init__(
        self,
        *,
        radio_values=None,
        text_values=None,
    ):
        self.radio_values = list(
            radio_values or ()
        )
        self.text_values = list(
            text_values or ()
        )
        self.subheaders = []
        self.warnings = []
        self.infos = []
        self.markdowns = []
        self.writes = []
        self.radios = []
        self.text_inputs = []

    def subheader(self, value):
        self.subheaders.append(value)

    def warning(self, value):
        self.warnings.append(value)

    def info(self, value):
        self.infos.append(value)

    def markdown(self, value):
        self.markdowns.append(value)

    def write(self, value):
        self.writes.append(value)

    def radio(
        self,
        label,
        *,
        options,
        index,
        format_func,
        key,
    ):
        self.radios.append(
            {
                "label": label,
                "options": options,
                "index": index,
                "format_func": format_func,
                "key": key,
            }
        )

        if self.radio_values:
            return self.radio_values.pop(0)

        return options[index]

    def text_input(
        self,
        label,
        *,
        value,
        key,
    ):
        self.text_inputs.append(
            {
                "label": label,
                "value": value,
                "key": key,
            }
        )

        if self.text_values:
            return self.text_values.pop(0)

        return value


def make_view(
    *,
    requires_review=True,
):
    return LessonPlanTeacherReviewViewModel(
        items=(
            TeacherReviewItemView(
                field=DocumentField.CLASS_NAME,
                field_label="Lớp",
                detected_value="8A2",
                canonical_value="8A2",
                review_state=(
                    PreviewReviewState.ACCEPTED
                ),
                requires_review=False,
                default_action=(
                    TeacherReviewAction.CONFIRM
                ),
            ),
            TeacherReviewItemView(
                field=DocumentField.LESSON_TITLE,
                field_label="Tên bài",
                detected_value="Đơn thức",
                canonical_value="Đơn thức chuẩn",
                review_state=(
                    PreviewReviewState.CONFLICT
                ),
                requires_review=True,
                default_action=(
                    TeacherReviewAction.REJECT
                ),
            ),
        ),
        requires_review=requires_review,
    )


def test_renderer_uses_safe_defaults():
    st = FakeStreamlit()

    review = render_lesson_plan_teacher_review(
        st=st,
        view=make_view(),
    )

    assert len(review.decisions) == 2

    assert (
        review.decisions[0].action
        is TeacherReviewAction.CONFIRM
    )

    assert (
        review.decisions[1].action
        is TeacherReviewAction.REJECT
    )

    assert len(st.warnings) == 1
    assert len(st.infos) == 0
    assert len(st.text_inputs) == 0


def test_renderer_returns_override():
    st = FakeStreamlit(
        radio_values=(
            TeacherReviewAction.CONFIRM,
            TeacherReviewAction.OVERRIDE,
        ),
        text_values=(
            "Đơn thức mới",
        ),
    )

    review = render_lesson_plan_teacher_review(
        st=st,
        view=make_view(),
    )

    decision = review.decisions[1]

    assert (
        decision.action
        is TeacherReviewAction.OVERRIDE
    )

    assert (
        decision.override_value
        == "Đơn thức mới"
    )

    assert len(st.text_inputs) == 1

    assert (
        st.text_inputs[0]["value"]
        == "Đơn thức chuẩn"
    )


def test_renderer_shows_info_when_review_not_required():
    st = FakeStreamlit()

    render_lesson_plan_teacher_review(
        st=st,
        view=make_view(
            requires_review=False
        ),
    )

    assert len(st.warnings) == 0
    assert len(st.infos) == 1


def test_renderer_uses_unique_widget_keys():
    st = FakeStreamlit()

    render_lesson_plan_teacher_review(
        st=st,
        view=make_view(),
        key_prefix="review_test",
    )

    keys = [
        item["key"]
        for item in st.radios
    ]

    assert len(keys) == len(set(keys))
    assert all(
        key.startswith("review_test_")
        for key in keys
    )


def test_renderer_rejects_invalid_view():
    st = FakeStreamlit()

    try:
        render_lesson_plan_teacher_review(
            st=st,
            view=object(),
        )
    except TypeError as error:
        assert (
            "view must be "
            "LessonPlanTeacherReviewViewModel"
            in str(error)
        )
    else:
        raise AssertionError(
            "TypeError was not raised"
        )
