from pathlib import Path


APP = Path("scripts/teacher_portal/app.py").read_text(encoding="utf-8")
PAGE = Path("src/portal_v2/ui/standardized_lesson_plan_authoring_v2_streamlit.py").read_text(encoding="utf-8")
WEEKLY = Path("src/portal_v2/ui/weekly_lesson_authoring_streamlit.py").read_text(encoding="utf-8")


def test_v2_route_wires_existing_docx_visual_viewer():
    route = APP[APP.index("elif selected == 'Soạn bài cùng chuẩn giáo án V2':"):]
    route = route[:route.index("elif selected == 'Soạn bài cùng chuẩn giáo án':")]
    assert "build_document_html" in route
    assert "preview_html_builder=build_document_html" in route


def test_group_header_uses_canonical_mapping_and_hides_technical_id():
    header = PAGE[PAGE.index("def _render_group_header("):PAGE.index("def _render_document(")]
    assert '("Nh\\u00f3m gi\\u00e1o \\u00e1n", group_label)' in header
    assert 'metric("Mã nhóm", _text(context.get("group_id")))' not in header
    assert 'context.get("canonical_group_name")' in header


def test_snapshot_maps_group_id_to_canonical_names():
    weekly = WEEKLY
    assert "CanonicalLessonPlanNamingService().expected_name(group).filename" in weekly
    assert '"canonical_group_name": canonical_group_name' in weekly
    assert '"canonical_file_name": canonical_file_name' in weekly


def test_upload_is_group_scoped_and_immediately_previewable():
    assert '"Tìm và tải giáo án từ máy (.docx)"' in PAGE
    assert 'key=f"g1b_v2_upload_{group_id}"' in PAGE
    assert '"group_id": group_id' in PAGE
    assert 'str(original.get("group_id", "")) != group_id' in PAGE
    assert 'content=original_content' in PAGE
    assert 'preview_html_builder=preview_html_builder' in PAGE
    assert 'context.get("canonical_file_name")' in PAGE
    assert "uploaded.name.casefold() != displayed_file_name.casefold()" in PAGE
    assert "Tên tệp chưa theo tên chuẩn của nhóm." in PAGE
    assert "Hệ thống vẫn nhận tệp đã chọn" in PAGE
