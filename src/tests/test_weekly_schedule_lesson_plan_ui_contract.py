from pathlib import Path


UI_FILE = Path(
    "src/portal_v2/ui/"
    "weekly_schedule_streamlit.py"
)


def ui_source() -> str:
    return UI_FILE.read_text(
        encoding="utf-8"
    )


def test_ui_contract_has_compact_action_hub_without_cards():
    text = ui_source()

    assert "_render_lesson_authoring_tool_hub" in text

    # Hai th? gi?i thi?u l?n ?? ???c lo?i b?.
    assert 'class="mt-tool-grid"' not in text
    assert "mt-tool-card-ai" not in text
    assert "mt-tool-card-standard" not in text

    # Hai ?i?u khi?n ch?c n?ng th?t v?n ph?i ???c gi?.
    assert "open_ai_workspace = st.button(" in text
    assert "open_standardization_workspace = st.button(" in text
    assert "lesson_authoring_open_ai" in text
    assert "lesson_authoring_open_standardization" in text
    assert "st.columns(" in text


def test_ui_contract_renders_tool_hub_before_page_data():
    text = ui_source()

    workspace_start = text.index(
        "def render_weekly_schedule_workspace("
    )
    hub_call = text.index(
        "_render_lesson_authoring_tool_hub(",
        workspace_start,
    )
    repository_call = text.index(
        "SupabaseAcademicYearConfigurationRepository(",
        text.index("def render_weekly_schedule_workspace("),
    )

    assert hub_call < repository_call


def test_ui_contract_connects_tool_hub_to_real_actions():
    text = ui_source()

    assert '"✨ Bắt đầu soạn bài"' in text
    assert '"📁 Chọn tệp giáo án"' in text
    assert 'key="lesson_authoring_open_ai"' in text
    assert (
        'key="lesson_authoring_open_standardization"'
        in text
    )
    assert "_LESSON_AUTHORING_FOCUS_KEY" in text
    assert 'workspace_focus == "AI"' in text
    assert 'workspace_focus="AI"' in text


def test_ui_contract_keeps_the_page_compact():
    text = ui_source()

    assert '"Xem L\\u1ecbch b\\u00e1o gi\\u1ea3ng "' in text
    assert '"Ki\\u1ec3m tra th\\u00f4ng tin b\\u00e0i so\\u1ea1n"' in text
    assert '"Xem quy tr\\u00ecnh chu\\u1ea9n h\\u00f3a"' in text
    assert "MATHTEACHER AI &middot;" not in text
    assert "_render_selected_lesson_summary(" not in text[
        text.index(
            "def _render_lesson_plan_standardization_workspace("
        ):
    ]


def test_ui_contract_has_powerful_ai_drafting_workspace():
    text = ui_source()

    assert "_build_lesson_plan_starter" in text
    assert "_lesson_plan_quality_checks" in text
    assert '"Tạo khung giáo án từ bài đang chọn"' in text
    assert 'st.tabs(' in text
    assert '"Tải bản nháp Word"' in text
    assert 'key=prefix + "_download_draft"' in text
    assert 'disabled=True' in text
    assert "Dịch vụ AI chưa được kết nối" in text


def test_ui_contract_syncs_weekly_schedule_into_drafting():
    text = ui_source()

    assert "_subject_display_name" in text
    assert '"subject_ref": str(' in text
    assert '"component_ref": str(' in text
    assert "context_class = _class_display_names(" in text
    assert '"class_name": context_class' in text
    assert '"timetable_period": getattr(' in text
    assert '"teaching_equipment": tuple(' in text
    assert 'class="mt-synced-lesson-title"' in text
    assert "subject_name=str(" in text
    assert "teaching_equipment=selected.get(" in text


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


def test_ui_contract_has_modern_visual_preview():
    text = ui_source()

    assert (
        "LessonPlanPreviewUploadService()"
        in text
    )
    assert ".prepare(" in text
    assert "build_document_html(" in text


def test_ui_contract_builds_modification_plan_from_canonical_values():
    text = ui_source()

    assert (
        "LessonPlanModificationPlanner()"
        in text
    )
    assert ".build_from_values(" in text
    assert "values=canonical_values" in text
    assert "processing_ready = (" in text




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

    assert "uploaded_content = (" in text
    assert "uploaded.getvalue()" in text
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
