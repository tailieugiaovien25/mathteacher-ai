from pathlib import Path


UI = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")


def source():
    return UI.read_text(encoding="utf-8")


def test_selector_has_six_controls_in_required_order():
    text = source()
    start = text.index("selector_columns = st.columns(")
    end = text.index("selected_timetable_rows =", start)
    segment = text[start:end]

    labels = (
        '"Môn"',
        '"Phân môn"',
        '"Cách thực hiện"',
        '"Lớp dạy"',
        '"Ngày dạy"',
        '"Tiết (theo PPCT)"',
    )

    # Class/date are rendered immediately after timetable rows are resolved,
    # but their fixed column indices preserve the required visual order.
    assert "selector_columns[0].selectbox" not in segment
    assert "with selector_columns[0]" in segment
    assert "with selector_columns[1]" in segment
    assert "selector_columns[2].selectbox" in segment
    assert "selector_columns[5].selectbox" in segment
    full_workspace = text[start:text.index("# Lesson authoring visual context", start)]
    for label in labels:
        assert label in full_workspace
    assert "selector_columns[3].text_input" in full_workspace
    assert "selector_columns[4].text_input" in full_workspace
    assert 'selectbox(\n        "Lớp dạy"' not in full_workspace
    assert 'selectbox(\n            "Ngày dạy"' not in full_workspace


def test_subject_and_component_filter_real_schedule_rows():
    text = source()

    assert "filtered_schedule_rows = tuple(" in text
    assert "rows=filtered_schedule_rows" in text
    assert 'getattr(row, "subject_ref"' in text
    assert 'getattr(row, "component_ref"' in text


def test_selection_modes_are_period_lesson_topic_in_order():
    text = source()
    start = text.index("available_modes = tuple(")
    segment = text[start:start + 500]

    period = segment.index("LessonPlanSelectionMode.PERIOD")
    lesson = segment.index("LessonPlanSelectionMode.LESSON")
    topic = segment.index("LessonPlanSelectionMode.TOPIC")
    assert period < lesson < topic


def test_standardization_page_hides_legacy_shell_only():
    text = source()

    assert "omit the legacy entry hub and" in text
    assert "hide_standardization_context_ui = (" in text
    assert "_render_lesson_plan_standardization_workspace(" in text
    assert "_render_lbg_table(" in text


def test_selector_uses_modern_3d_visual_tokens():
    text = source()

    assert "mt-standard-selector-shell" in text
    assert "linear-gradient(145deg" in text
    assert "box-shadow:0 12px 28px" in text
    assert "font-family:Inter,Arial,sans-serif" in text
