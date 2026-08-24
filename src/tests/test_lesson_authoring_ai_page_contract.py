from pathlib import Path


APP = Path("scripts/teacher_portal/app.py")
PAGE = Path(
    "src/portal_v2/ui/lesson_authoring_ai_streamlit.py"
)
WEEKLY = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def test_teacher_portal_exposes_standalone_ai_authoring_page():
    text = APP.read_text(encoding="utf-8-sig")

    assert "So\\u1ea1n b\\xe0i c\\xf9ng AI" in text
    assert "render_lesson_authoring_ai_page" in text


def test_ai_page_is_full_width_and_has_three_working_panes():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert "max-width: none !important" in text
    assert "st.columns([2.2, 7.2, 2.6]" in text
    assert "NGUỒN GIÁO ÁN" in text
    assert "CỬA SỔ CHỈNH SỬA TOÀN VĂN" in text
    assert "TRỢ LÝ SOẠN BÀI" in text


def test_docx_upload_is_automatically_imported_into_editor():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert "LessonPlanDocxWholeDocumentImporter" in text
    assert ".import_bytes(payload)" in text
    assert "_set_document(imported)" in text
    assert "SOURCE_BYTES_KEY" in text


def test_page_supports_edit_save_undo_quality_and_word_export():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert "key=DOCUMENT_KEY" in text
    assert "Lưu bản nháp" in text
    assert "Hoàn tác" in text
    assert "Mức độ đầy đủ" in text
    assert "LessonPlanFullDocumentDocxAdapter" in text
    assert "download_button(" in text


def test_weekly_schedule_can_open_selected_lesson_in_ai_page():
    text = WEEKLY.read_text(encoding="utf-8-sig")

    assert "Mở trong trang Soạn bài cùng AI" in text
    assert "on_click=_open_ai_authoring_page" in text
    assert '"lesson_authoring_ai_context"' in text
    assert "transferred_context = dict(selected_lesson)" in text
    assert 'context_origin="STANDARDIZATION"' in text
    assert "context_read_only=True" in text
    assert '] = "Soạn bài cùng AI"' in text


def test_ai_backend_is_connected_through_a_safe_handler_contract():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert 'st.session_state.get("lesson_authoring_ai_handler")' in text
    assert "if callable(handler):" in text
    assert "request=request" in text
    assert "document=st.session_state.get(DOCUMENT_KEY" in text
    assert "context=context" in text


def test_navigation_changes_run_in_streamlit_callbacks():
    page = PAGE.read_text(encoding="utf-8-sig")
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    assert "def _open_standardization(" in page
    assert "on_click=_open_standardization" in page
    assert "def _open_ai_authoring_page(" in weekly
    assert "on_click=_open_ai_authoring_page" in weekly


def test_transfer_to_standardization_upserts_management_catalogue():
    page = PAGE.read_text(encoding="utf-8-sig")

    assert 'MANAGEMENT_CATALOG_KEY = "lesson_plan_management_catalog"' in page
    assert "def _save_to_management_catalog(" in page
    assert "def _catalog_identity(" in page
    assert '"lesson_plan_management_selected_id"' in page
    assert "catalogue.append(item)" in page
    assert "catalogue[-100:]" in page
    assert "_save_to_management_catalog(" in page
    assert "args=(document, context, user_id)" in page


def test_management_page_lists_and_reopens_catalogued_lessons():
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    assert 'st.subheader("Danh mục giáo án")' in weekly
    assert '"lesson_plan_management_catalog"' in weekly
    assert "def _open_management_catalogue_item(" in weekly
    assert '"Chuyển vào Chuẩn hóa giáo án"' in weekly
    assert '"lesson_authoring_standardization_document"' in weekly
    assert '"lesson_authoring_ai_source_bytes"' in weekly
    assert 'st.session_state["portal_page"] = "Chuẩn hóa giáo án"' in weekly


def test_each_catalogue_item_has_safe_transfer_and_delete_actions():
    page = PAGE.read_text(encoding="utf-8-sig")
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    assert '] = "Chuẩn hóa giáo án"' in page
    assert '"Chuyển vào Chuẩn hóa giáo án"' in weekly
    assert '"Xóa"' in weekly
    assert "def _request_catalogue_item_delete(" in weekly
    assert '"Xác nhận xóa"' in weekly
    assert '"Hủy"' in weekly
    assert "def _delete_management_catalogue_item(" in weekly
    assert 'str(item.get("user_id", "")) == str(user_id)' in weekly


def test_ai_transfer_uses_payload_contract_consumed_by_standardizer():
    page = PAGE.read_text(encoding="utf-8-sig")
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    assert "def _publish_standardization_transfer(" in page
    assert '"_standardization_transfer"' in page
    assert '"source": "AI_DRAFT"' in page
    assert '"docx_bytes": item.get("docx_bytes")' in page
    assert "LessonPlanFullDocumentDocxAdapter" in page
    assert ").build_bytes(document)" in page
    assert 'str(key).endswith(' in weekly
    assert '"_standardization_transfer"' in weekly
    assert 'value.get("source")' in weekly
    assert '!= "AI_DRAFT"' in weekly


def test_management_reopen_republishes_and_delete_removes_transfer():
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    open_start = weekly.index("def _open_management_catalogue_item(")
    delete_start = weekly.index("def _delete_management_catalogue_item(")
    open_text = weekly[open_start:delete_start]
    delete_text = weekly[delete_start:]
    assert '"source": "AI_DRAFT"' in open_text
    assert '"docx_bytes": selected.get("docx_bytes")' in open_text
    assert 'st.session_state.pop(transfer_key, None)' in open_text
    assert 'st.session_state.pop(transfer_key, None)' in delete_text


def test_standardization_preselects_canonical_schedule_context():
    page = PAGE.read_text(encoding="utf-8-sig")
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    open_start = page.index("def _open_standardization(")
    open_end = page.index(
        "\ndef _schedule_context_selector(",
        open_start,
    )
    open_text = page[open_start:open_end]
    assert 'st.session_state["lbg_user_week_number"]' not in open_text
    assert "def _latest_ai_standardization_transfer(" in weekly
    assert "def _match_transfer_schedule_row(" in weekly
    assert '"subject_ref", "subject_ref"' in weekly
    assert '"class_ref", "class_id"' in weekly
    assert '"curriculum_period", "curriculum_period"' in weekly
    assert '"timetable_period", "timetable_period"' in weekly
    assert '"teaching_date", "teaching_date"' in weekly
    assert "LessonPlanSelectionMode.LESSON" in weekly
    assert "unit.representative_index" in weekly
    assert '"lesson_plan_standardization_applied_transfer_id"' in weekly


def test_ai_document_can_return_without_schedule_metadata_writeback():
    page = PAGE.read_text(encoding="utf-8-sig")
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    assert '"drafting_date": _value(' in page
    publish_start = page.index("def _publish_standardization_transfer(")
    publish_end = page.index("\ndef _open_standardization(", publish_start)
    publish_text = page[publish_start:publish_end]
    assert '"docx_bytes": item.get("docx_bytes")' in publish_text
    assert '"academic_year":' not in publish_text
    assert '"week_number":' not in publish_text
    assert '"teaching_date":' not in publish_text

    reopen_start = weekly.index("def _open_management_catalogue_item(")
    reopen_end = weekly.index("\ndef _request_catalogue_item_delete(", reopen_start)
    reopen_text = weekly[reopen_start:reopen_end]
    assert '"docx_bytes": selected.get("docx_bytes")' in reopen_text
    assert '"academic_year":' not in reopen_text
    assert '"week_number":' not in reopen_text
    assert '"teaching_date":' not in reopen_text


def test_transferred_lesson_keeps_full_v25_context_ui_and_sync():
    weekly = WEEKLY.read_text(encoding="utf-8-sig")

    assert "hide_synced_context = False" in weekly
    assert 'page_title == "Chuẩn hóa giáo án"' in weekly
    assert "def _render_synced_context_markdown(" in weekly
    assert "if hide_synced_context:" in weekly
    assert "selection_mode = LessonPlanSelectionMode.LESSON" in weekly
    assert "if not hide_synced_context:" in weekly
    assert '"drafting_date": drafting_date' in weekly
    assert '"teaching_date": selected_row.teaching_date' in weekly
    assert "if not hide_standardization_context_ui:" in weekly
    assert 'st.subheader(\n        "\\U0001f4dd CHU\\u1ea8N H\\u00d3A GI\\u00c1O \\u00c1N"' in weekly


def test_six_authoring_fields_are_linked_from_one_schedule_row():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert "def _schedule_context_selector(" in text
    assert 'st.session_state.get("weekly_schedule_portal_view")' in text
    assert "Chọn bài từ Lịch báo giảng" in text
    assert 'subject_name=subject_name' in text
    assert 'class_name=class_name' in text
    assert 'lesson_title=str(getattr(row, "lesson_title"' in text
    assert 'curriculum_period=getattr(row, "curriculum_period"' in text
    assert 'timetable_period=getattr(row, "timetable_period"' in text
    assert 'teaching_date=getattr(row, "teaching_date"' in text
    assert "disabled=linked" in text


def test_ai_page_uses_navy_3d_frames_and_unfilled_inputs():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert "border:2px solid #12345b" in text
    assert "box-shadow:4px 5px 0 #0a2342" in text
    assert 'div[data-testid="column"]:has(.mt-pane-label)' in text
    assert "background:transparent !important" in text
    assert ".stTextArea textarea" in text
    assert ".stTextInput input" in text
    assert '[data-baseweb="select"] > div' in text


def test_full_document_editor_uses_translucent_white_surface():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert ".mt-ai-document-pane-marker" in text
    assert 'div[data-testid="column"]:has(.mt-ai-document-pane-marker)' in text
    assert "background:rgba(255,255,255,.94) !important" in text
    assert "backdrop-filter:blur(10px)" in text


def test_full_document_editor_uses_navy_frame_and_18px_type():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert "background:#071a33 !important" in text
    assert "box-shadow:5px 6px 0 #03101f" in text
    assert "font-size:18px !important" in text
    assert "line-height:1.5 !important" in text


def test_ai_page_uses_navy_surfaces_white_labels_and_uniform_readability():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert ".mt-ai-page-header" in text
    assert "background:#071a33" in text
    assert "color:#ffffff" in text
    assert '[data-testid="stExpander"]' in text
    assert ".stApp, .stApp button, .stApp input, .stApp textarea" in text
    assert "font-size:18px" in text
    assert "line-height:1.5" in text


def test_ai_page_connects_gemini_without_exposing_the_key():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert '_secret("GEMINI_API_KEY")' in text
    assert 'GeminiLessonPlanService(' in text
    assert 'model=_secret("GEMINI_MODEL", "gemini-3.5-flash-lite")' in text
    assert "Gemini Free Tier đã kết nối" in text
    assert "with st.spinner(" in text


def test_ai_results_are_applied_before_document_widget_is_instantiated():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert 'PENDING_DOCUMENT_KEY = "lesson_authoring_ai_pending_document"' in text
    assert "def _queue_document(text: str)" in text
    assert "pending_document = st.session_state.pop(PENDING_DOCUMENT_KEY, None)" in text
    assert "_queue_document(str(revised))" in text
    assert "_queue_document(str(st.session_state.get(DOCUMENT_KEY" in text


def test_subject_menu_uses_active_teacher_assignments_and_filters_rows():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert "SupabaseTeachingAssignmentRepository" in text
    assert "TeachingAssignmentRole.TEACHING" in text
    assert "TeachingAssignmentStatus.ACTIVE" in text
    assert '"Môn/phân môn"' in text
    assert 'key="lesson_authoring_ai_assignment_subject"' in text
    assert "assignment_classes" in text
    assert "filtered_rows" in text
    assert "row = filtered_rows[int(selected_index)]" in text


def test_dependent_context_fields_come_from_one_filtered_schedule_row():
    text = PAGE.read_text(encoding="utf-8-sig")

    for field in (
        "class_id",
        "lesson_title",
        "curriculum_period",
        "timetable_period",
        "teaching_date",
    ):
        assert f'getattr(row, "{field}"' in text


def test_assignment_menu_resolves_year_without_opening_schedule_first():
    text = PAGE.read_text(encoding="utf-8-sig")

    assert '"lbg_user_academic_year"' in text
    assert '"portal_academic_year"' in text
    assert "SupabaseAcademicYearConfigurationRepository" in text
    assert ").get_current()" in text
    assert 'context["academic_year"] = academic_year' in text
