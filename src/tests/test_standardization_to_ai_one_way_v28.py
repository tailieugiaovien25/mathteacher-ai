from pathlib import Path


WEEKLY_UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)
AI_UI = Path(
    "src/portal_v2/ui/lesson_authoring_ai_streamlit.py"
)


def _function_source(text: str, name: str) -> str:
    start = text.index(f"def {name}(")
    end = text.find("\ndef ", start + 10)
    return text[start:] if end == -1 else text[start:end]


def test_standardization_sends_complete_selected_context_to_ai():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")
    workspace = _function_source(
        text,
        "_render_lesson_plan_standardization_workspace",
    )

    for field in (
        "academic_year",
        "week_number",
        "subject_ref",
        "component_ref",
        "subject_name",
        "component_name",
        "class_id",
        "class_name",
        "classes",
        "curriculum_period",
        "periods",
        "timetable_period",
        "timetable_periods_by_class",
        "teaching_date",
        "teaching_dates_by_class",
        "teaching_equipment",
        "lesson_title",
    ):
        assert f'"{field}"' in workspace

    assert "on_click=_open_ai_authoring_page" in workspace
    assert "args=(dict(selected_lesson),)" in workspace


def test_open_ai_marks_context_as_read_only_standardization_data():
    text = WEEKLY_UI.read_text(encoding="utf-8-sig")
    function = _function_source(text, "_open_ai_authoring_page")

    assert 'context_origin="STANDARDIZATION"' in function
    assert "context_read_only=True" in function
    assert '"lesson_authoring_ai_context"' in function
    assert '"portal_page"' in function


def test_ai_consumes_standardization_context_without_reselecting_it():
    text = AI_UI.read_text(encoding="utf-8-sig")
    function = _function_source(text, "_schedule_context_selector")

    authority = function.index(
        'context.get("context_origin") == "STANDARDIZATION"'
    )
    early_return = function.index(
        "return received, True",
        authority,
    )
    schedule_view = function.index(
        'st.session_state.get("weekly_schedule_portal_view")'
    )
    assert authority < early_return < schedule_view


def test_ai_exposes_separate_locked_destination_fields():
    text = AI_UI.read_text(encoding="utf-8-sig")
    function = _function_source(text, "_context_editor")

    for label in (
        '"Năm học"',
        '"Tuần học"',
        '"Môn"',
        '"Phân môn"',
        '"Lớp"',
        '"Tên bài dạy"',
        '"Tiết PPCT"',
        '"Tiết TKB"',
        '"Ngày dạy"',
        '"Thiết bị dạy học"',
    ):
        assert label in function

    assert "if not linked:" in function
    assert "không ghi ngược dữ liệu nguồn" in function


def test_ai_return_transfer_contains_document_but_no_schedule_metadata():
    text = AI_UI.read_text(encoding="utf-8-sig")
    function = _function_source(
        text,
        "_publish_standardization_transfer",
    )

    assert '"docx_bytes": item.get("docx_bytes")' in function
    assert '"full_document_text":' in function
    for field in (
        "academic_year",
        "week_number",
        "subject_ref",
        "component_ref",
        "class_ref",
        "curriculum_period",
        "timetable_period",
        "teaching_date",
    ):
        assert f'"{field}":' not in function

