from pathlib import Path


UI_FILE = Path(
    "src/portal_v2/ui/"
    "weekly_schedule_streamlit.py"
)


def ui_source() -> str:
    return UI_FILE.read_text(
        encoding="utf-8"
    )


def test_ui_contract_has_lesson_selection():
    text = ui_source()

    assert "st.selectbox(" in text
    assert "_lesson_plan_row_label" in text
    assert "selected_index" in text
    assert "selected_row" in text


def test_ui_contract_has_drafting_date():
    text = ui_source()

    assert "st.date_input(" in text
    assert "selected_row.teaching_date" in text
    assert "drafting_date" in text


def test_ui_contract_accepts_docx_upload():
    text = ui_source()

    assert "st.file_uploader(" in text
    assert 'type=("docx",)' in text
    assert "accept_multiple_files=False" in text


def test_ui_contract_builds_upload_identity():
    text = ui_source()

    assert (
        "LessonPlanWorkflowIdentity"
        in text
    )
    assert ".from_upload(" in text
    assert "week_number=view.week_number" in text
    assert "row_index=selected_index" in text
    assert "content=uploaded_content" in text


def test_ui_contract_persists_workflow_state():
    text = ui_source()

    assert "LessonPlanWorkflowState(" in text
    assert "st.session_state[" in text
    assert "workflow_identity.state_key" in text
    assert ".with_result(" in text


def test_ui_contract_has_preview_and_teacher_review():
    text = ui_source()

    assert (
        "LessonPlanPreviewUploadService()"
        in text
    )
    assert "render_lesson_plan_preview(" in text
    assert (
        "render_lesson_plan_teacher_review("
        in text
    )


def test_ui_contract_builds_modification_plan_after_review():
    text = ui_source()

    assert (
        "LessonPlanModificationPlanner()"
        in text
    )
    assert ".build(" in text
    assert "resolution=review_resolution" in text
    assert "if review_accepted:" in text


def test_ui_contract_processes_reviewed_document():
    text = ui_source()

    assert "_process_lesson_plan_upload(" in text
    assert "row=reviewed_row" in text
    assert (
        "modification_plan=("
        in text
    )


def test_ui_contract_processing_service_receives_modification_plan():
    text = ui_source()

    assert (
        "LessonPlanDocumentProcessingService("
        in text
    )
    assert "result = service.process(" in text
    assert (
        "modification_plan=modification_plan"
        in text
    )


def test_ui_contract_preserves_original_upload():
    text = ui_source()

    assert "uploaded_content = uploaded.getvalue()" in text
    assert (
        "LessonPlanWorkflowIdentity"
        in text
    )
    assert "content=uploaded_content" in text
    assert "output_bytes" in text


def test_ui_contract_exposes_standardized_docx_download():
    text = ui_source()

    assert "st.download_button(" in text
    assert "data=output_bytes" in text
    assert "file_name=output_name" in text
    assert (
        "officedocument."
        "wordprocessingml.document"
        in text
    )
