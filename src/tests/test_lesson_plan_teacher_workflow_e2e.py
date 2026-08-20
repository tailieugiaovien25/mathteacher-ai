from contextlib import nullcontext
from datetime import date
from types import SimpleNamespace

import portal_v2.ui.weekly_schedule_streamlit as module

from document_intelligence.lesson_plan_workflow_state import (
    LessonPlanWorkflowState,
)
from educational_planning_v2.models.weekly_teaching_schedule import (
    TeachingSession,
)
from portal_v2.ui.weekly_schedule_portal import (
    WeeklySchedulePortalPreviewRow,
)


class FakeUpload:
    def __init__(
        self,
        *,
        name: str,
        content: bytes,
    ):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content


class FakeStreamlit:
    def __init__(
        self,
        *,
        uploaded,
        process_clicked=True,
    ):
        self.uploaded = uploaded
        self.process_clicked = process_clicked
        self.session_state = {}

        self.successes = []
        self.warnings = []
        self.errors = []
        self.downloads = []

    def divider(self):
        pass

    def subheader(self, value):
        pass

    def caption(self, value):
        pass

    def selectbox(
        self,
        label,
        *,
        options,
        format_func,
        key,
    ):
        return options[0]

    def info(self, value):
        pass

    def date_input(
        self,
        label,
        *,
        value,
        max_value,
        key,
    ):
        return value

    def file_uploader(
        self,
        label,
        *,
        type,
        accept_multiple_files,
        key,
    ):
        return self.uploaded

    def success(self, value):
        self.successes.append(value)

    def warning(self, value):
        self.warnings.append(value)

    def error(self, value):
        self.errors.append(value)

    def button(
        self,
        label,
        *,
        type,
        width,
        key,
    ):
        return self.process_clicked

    def spinner(self, value):
        return nullcontext()

    def download_button(
        self,
        label,
        *,
        data,
        file_name,
        mime,
        width,
        key,
    ):
        self.downloads.append(
            {
                "label": label,
                "data": data,
                "file_name": file_name,
                "mime": mime,
                "key": key,
            }
        )


def make_row():
    return WeeklySchedulePortalPreviewRow(
        teaching_date=date(
            2026,
            9,
            28,
        ),
        weekday=1,
        timetable_period=2,
        session=TeachingSession.MORNING,
        class_id="8A1",
        subject_ref="TOAN",
        component_ref=None,
        curriculum_period=9,
        lesson_id="TOAN8-009",
        lesson_title="Đơn thức",
        period_in_lesson=1,
        teaching_equipment=(),
    )


def make_view():
    return SimpleNamespace(
        week_number=5,
        rows=(
            make_row(),
        ),
    )


def test_teacher_workflow_happy_path_reaches_download(
    monkeypatch,
):
    uploaded = FakeUpload(
        name="lesson.docx",
        content=b"lesson-plan-content",
    )

    st = FakeStreamlit(
        uploaded=uploaded,
        process_clicked=True,
    )

    preview = object()
    review = object()

    resolution = SimpleNamespace(
        accepted=True,
        metadata=SimpleNamespace(
            values=(
                (
                    module.DocumentField.CLASS_NAME,
                    "8A1",
                ),
                (
                    module.DocumentField.CURRICULUM_PERIOD,
                    "9",
                ),
                (
                    module.DocumentField.LESSON_TITLE,
                    "Đơn thức",
                ),
                (
                    module.DocumentField.DRAFTING_DATE,
                    "28/09/2026",
                ),
                (
                    module.DocumentField.TEACHING_DATE,
                    "28/09/2026",
                ),
            )
        ),
    )

    class FakePreviewService:
        def prepare(
            self,
            *,
            content,
            canonical,
        ):
            assert content == b"lesson-plan-content"
            assert canonical.class_name == "8A1"
            assert canonical.curriculum_period == 9
            assert canonical.lesson_title == "Đơn thức"
            return preview

    class FakePresenter:
        def present(
            self,
            *,
            preview,
            canonical_values,
        ):
            return object()

    class FakeResolver:
        def resolve(
            self,
            *,
            preview,
            review,
        ):
            return resolution

    processed = []

    def fake_process(
        *,
        row,
        drafting_date,
        content,
        original_name,
        modification_plan=None,
    ):
        processed.append(
            {
                "row": row,
                "drafting_date": drafting_date,
                "content": content,
                "original_name": original_name,
            }
        )

        return (
            "lesson-standardized.docx",
            b"standardized-docx",
            (),
        )

    monkeypatch.setattr(
        module,
        "st",
        st,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanPreviewUploadService",
        FakePreviewService,
    )

    monkeypatch.setattr(
        module,
        "render_lesson_plan_preview",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanTeacherReviewPresenter",
        FakePresenter,
    )

    monkeypatch.setattr(
        module,
        "render_lesson_plan_teacher_review",
        lambda **kwargs: review,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanTeacherReviewResolver",
        FakeResolver,
    )

    class FakeModificationPlanner:
        def build(
            self,
            *,
            resolution,
        ):
            return object()

    monkeypatch.setattr(
        module,
        "LessonPlanModificationPlanner",
        FakeModificationPlanner,
    )

    monkeypatch.setattr(
        module,
        "_process_lesson_plan_upload",
        fake_process,
    )

    module._render_lesson_plan_standardization_workspace(
        make_view()
    )

    assert st.errors == []

    assert len(processed) == 1

    assert (
        processed[0]["content"]
        == b"lesson-plan-content"
    )

    assert (
        processed[0]["original_name"]
        == "lesson.docx"
    )

    assert (
        processed[0]["row"].class_id
        == "8A1"
    )

    assert (
        processed[0]["row"].lesson_title
        == "Đơn thức"
    )

    assert len(st.downloads) == 1

    assert (
        st.downloads[0]["file_name"]
        == "lesson-standardized.docx"
    )

    assert (
        st.downloads[0]["data"]
        == b"standardized-docx"
    )

    workflow_states = [
        value
        for value
        in st.session_state.values()
        if isinstance(
            value,
            LessonPlanWorkflowState,
        )
    ]

    assert len(workflow_states) == 1

    state = workflow_states[0]

    assert state.preview is preview
    assert state.review is review
    assert state.resolution is resolution

    assert state.result == (
        "lesson-standardized.docx",
        b"standardized-docx",
        (),
    )


def test_teacher_override_reaches_processing_row(
    monkeypatch,
):
    uploaded = FakeUpload(
        name="lesson.docx",
        content=b"lesson-plan-override",
    )

    st = FakeStreamlit(
        uploaded=uploaded,
        process_clicked=True,
    )

    preview = object()
    review = object()

    override_title = (
        "\u0110\u01a1n th\u1ee9c m\u1edbi"
    )

    resolution = SimpleNamespace(
        accepted=True,
        metadata=SimpleNamespace(
            values=(
                (
                    module.DocumentField.CLASS_NAME,
                    "8A1",
                ),
                (
                    module.DocumentField.CURRICULUM_PERIOD,
                    "9",
                ),
                (
                    module.DocumentField.LESSON_TITLE,
                    override_title,
                ),
                (
                    module.DocumentField.DRAFTING_DATE,
                    "28/09/2026",
                ),
                (
                    module.DocumentField.TEACHING_DATE,
                    "28/09/2026",
                ),
            )
        ),
    )

    class FakePreviewService:
        def prepare(
            self,
            *,
            content,
            canonical,
        ):
            assert (
                canonical.lesson_title
                == "\u0110\u01a1n th\u1ee9c"
            )

            return preview

    class FakePresenter:
        def present(
            self,
            *,
            preview,
            canonical_values,
        ):
            assert (
                canonical_values[
                    module.DocumentField.LESSON_TITLE
                ]
                == "\u0110\u01a1n th\u1ee9c"
            )

            return object()

    class FakeResolver:
        def resolve(
            self,
            *,
            preview,
            review,
        ):
            return resolution

    processed = []

    def fake_process(
        *,
        row,
        drafting_date,
        content,
        original_name,
        modification_plan=None,
    ):
        processed.append(row)

        return (
            "lesson-override-standardized.docx",
            b"override-standardized-docx",
            (),
        )

    monkeypatch.setattr(
        module,
        "st",
        st,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanPreviewUploadService",
        FakePreviewService,
    )

    monkeypatch.setattr(
        module,
        "render_lesson_plan_preview",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanTeacherReviewPresenter",
        FakePresenter,
    )

    monkeypatch.setattr(
        module,
        "render_lesson_plan_teacher_review",
        lambda **kwargs: review,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanTeacherReviewResolver",
        FakeResolver,
    )

    class FakeModificationPlanner:
        def build(
            self,
            *,
            resolution,
        ):
            return object()

    monkeypatch.setattr(
        module,
        "LessonPlanModificationPlanner",
        FakeModificationPlanner,
    )

    monkeypatch.setattr(
        module,
        "_process_lesson_plan_upload",
        fake_process,
    )

    module._render_lesson_plan_standardization_workspace(
        make_view()
    )

    assert st.errors == []

    assert len(processed) == 1

    reviewed_row = processed[0]

    assert (
        reviewed_row.lesson_title
        == override_title
    )

    assert (
        reviewed_row.lesson_title
        != "\u0110\u01a1n th\u1ee9c"
    )

    assert reviewed_row.class_id == "8A1"

    assert (
        reviewed_row.curriculum_period
        == 9
    )

    assert len(st.downloads) == 1

    assert (
        st.downloads[0]["file_name"]
        == "lesson-override-standardized.docx"
    )

    assert (
        st.downloads[0]["data"]
        == b"override-standardized-docx"
    )


def test_rejected_review_blocks_processing_and_download(
    monkeypatch,
):
    uploaded = FakeUpload(
        name="lesson.docx",
        content=b"lesson-plan-rejected",
    )

    st = FakeStreamlit(
        uploaded=uploaded,
        process_clicked=True,
    )

    preview = object()
    review = object()

    resolution = SimpleNamespace(
        accepted=False,
        metadata=SimpleNamespace(
            values=()
        ),
    )

    class FakePreviewService:
        def prepare(
            self,
            *,
            content,
            canonical,
        ):
            return preview

    class FakePresenter:
        def present(
            self,
            *,
            preview,
            canonical_values,
        ):
            return object()

    class FakeResolver:
        def resolve(
            self,
            *,
            preview,
            review,
        ):
            return resolution

    process_calls = []

    def fake_process(
        *,
        row,
        drafting_date,
        content,
        original_name,
        modification_plan=None,
    ):
        process_calls.append(
            {
                "row": row,
                "drafting_date": drafting_date,
                "content": content,
                "original_name": original_name,
            }
        )

        raise AssertionError(
            "processing must not run "
            "for rejected review"
        )

    monkeypatch.setattr(
        module,
        "st",
        st,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanPreviewUploadService",
        FakePreviewService,
    )

    monkeypatch.setattr(
        module,
        "render_lesson_plan_preview",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanTeacherReviewPresenter",
        FakePresenter,
    )

    monkeypatch.setattr(
        module,
        "render_lesson_plan_teacher_review",
        lambda **kwargs: review,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanTeacherReviewResolver",
        FakeResolver,
    )

    class FakeModificationPlanner:
        def build(
            self,
            *,
            resolution,
        ):
            return object()

    monkeypatch.setattr(
        module,
        "LessonPlanModificationPlanner",
        FakeModificationPlanner,
    )

    monkeypatch.setattr(
        module,
        "_process_lesson_plan_upload",
        fake_process,
    )

    module._render_lesson_plan_standardization_workspace(
        make_view()
    )

    assert process_calls == []

    assert st.downloads == []

    assert st.errors == []

    assert len(st.warnings) >= 1

    workflow_states = [
        value
        for value
        in st.session_state.values()
        if isinstance(
            value,
            LessonPlanWorkflowState,
        )
    ]

    assert len(workflow_states) == 1

    state = workflow_states[0]

    assert state.preview is preview
    assert state.review is review
    assert state.resolution is resolution
    assert state.result is None


def test_rerun_preserves_result_without_reprocessing(
    monkeypatch,
):
    uploaded = FakeUpload(
        name="lesson.docx",
        content=b"lesson-plan-rerun",
    )

    st = FakeStreamlit(
        uploaded=uploaded,
        process_clicked=True,
    )

    preview = object()
    review = object()

    resolution = SimpleNamespace(
        accepted=True,
        metadata=SimpleNamespace(
            values=(
                (
                    module.DocumentField.CLASS_NAME,
                    "8A1",
                ),
                (
                    module.DocumentField.CURRICULUM_PERIOD,
                    "9",
                ),
                (
                    module.DocumentField.LESSON_TITLE,
                    "\u0110\u01a1n th\u1ee9c",
                ),
                (
                    module.DocumentField.DRAFTING_DATE,
                    "28/09/2026",
                ),
                (
                    module.DocumentField.TEACHING_DATE,
                    "28/09/2026",
                ),
            )
        ),
    )

    preview_calls = []
    process_calls = []

    class FakePreviewService:
        def prepare(
            self,
            *,
            content,
            canonical,
        ):
            preview_calls.append(content)
            return preview

    class FakePresenter:
        def present(
            self,
            *,
            preview,
            canonical_values,
        ):
            return object()

    class FakeResolver:
        def resolve(
            self,
            *,
            preview,
            review,
        ):
            return resolution

    def fake_process(
        *,
        row,
        drafting_date,
        content,
        original_name,
        modification_plan=None,
    ):
        process_calls.append(
            {
                "row": row,
                "content": content,
                "original_name": original_name,
            }
        )

        return (
            "lesson-rerun-standardized.docx",
            b"rerun-standardized-docx",
            (),
        )

    monkeypatch.setattr(
        module,
        "st",
        st,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanPreviewUploadService",
        FakePreviewService,
    )

    monkeypatch.setattr(
        module,
        "render_lesson_plan_preview",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanTeacherReviewPresenter",
        FakePresenter,
    )

    monkeypatch.setattr(
        module,
        "render_lesson_plan_teacher_review",
        lambda **kwargs: review,
    )

    monkeypatch.setattr(
        module,
        "LessonPlanTeacherReviewResolver",
        FakeResolver,
    )

    class FakeModificationPlanner:
        def build(
            self,
            *,
            resolution,
        ):
            return object()

    monkeypatch.setattr(
        module,
        "LessonPlanModificationPlanner",
        FakeModificationPlanner,
    )

    monkeypatch.setattr(
        module,
        "_process_lesson_plan_upload",
        fake_process,
    )

    # First render: process and store result.
    module._render_lesson_plan_standardization_workspace(
        make_view()
    )

    assert len(preview_calls) == 1
    assert len(process_calls) == 1
    assert len(st.downloads) == 1

    first_state_values = [
        value
        for value
        in st.session_state.values()
        if isinstance(
            value,
            LessonPlanWorkflowState,
        )
    ]

    assert len(first_state_values) == 1

    first_state = first_state_values[0]

    assert first_state.result == (
        "lesson-rerun-standardized.docx",
        b"rerun-standardized-docx",
        (),
    )

    # Simulate Streamlit rerun without clicking process again.
    st.process_clicked = False
    st.downloads.clear()

    module._render_lesson_plan_standardization_workspace(
        make_view()
    )

    # Preview comes from cached workflow state.
    assert len(preview_calls) == 1

    # Document processing must not run again.
    assert len(process_calls) == 1

    # Existing result remains downloadable.
    assert len(st.downloads) == 1

    assert (
        st.downloads[0]["file_name"]
        == "lesson-rerun-standardized.docx"
    )

    assert (
        st.downloads[0]["data"]
        == b"rerun-standardized-docx"
    )

    second_state_values = [
        value
        for value
        in st.session_state.values()
        if isinstance(
            value,
            LessonPlanWorkflowState,
        )
    ]

    assert len(second_state_values) == 1

    second_state = second_state_values[0]

    assert (
        second_state.result
        == first_state.result
    )
