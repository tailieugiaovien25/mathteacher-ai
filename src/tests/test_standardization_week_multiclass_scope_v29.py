from pathlib import Path


UI = Path(
    "src/portal_v2/ui/weekly_schedule_streamlit.py"
)


def source() -> str:
    return UI.read_text(encoding="utf-8-sig")


def _function_source(text: str, name: str) -> str:
    start = text.index(f"def {name}(")
    end = text.find("\ndef ", start + 10)
    return text[start:] if end == -1 else text[start:end]


def test_large_authoring_week_menu_is_present():
    text = source()
    workspace = _function_source(
        text,
        "render_weekly_schedule_workspace",
    )

    assert "mt-standardization-week-menu" in workspace
    assert "📅 TUẦN SOẠN GIÁO ÁN" in workspace
    assert '"Chọn tuần soạn"' in workspace
    assert "_STANDARDIZATION_WEEK_KEY" in workspace


def test_authoring_week_is_the_only_explicit_two_way_lbg_field():
    text = source()
    callback = _function_source(
        text,
        "_sync_standardization_week_to_lbg",
    )

    assert '"system_weekly_week_number"' in callback
    assert '"lbg_user_week_number"' in callback
    assert "_ACTIVE_VIEW_KEY" not in callback
    assert "_VIEW_STATE_KEY" not in callback
    for field in (
        "subject_ref",
        "component_ref",
        "class_id",
        "teaching_date",
        "curriculum_period",
        "timetable_period",
    ):
        assert field not in callback


def test_lbg_week_initializes_standardization_week():
    text = source()
    workspace = _function_source(
        text,
        "render_weekly_schedule_workspace",
    )

    lbg_read = workspace.index(
        'st.session_state.get(\n        "system_weekly_week_number"'
    )
    standardization_write = workspace.index(
        "_STANDARDIZATION_WEEK_KEY",
        lbg_read,
    )
    week_widget = workspace.index(
        '"Chọn tuần soạn"',
        standardization_write,
    )
    assert lbg_read < standardization_write < week_widget


def test_class_field_aggregates_every_timetable_class_for_selected_unit():
    text = source()
    workspace = _function_source(
        text,
        "_render_lesson_plan_standardization_workspace",
    )

    assert "selected_timetable_rows = _rows_for_selected_lesson_unit(" in workspace
    assert "selected_class_ids = tuple(dict.fromkeys(" in workspace
    assert "class_display_value = _class_display_names(" in workspace
    assert 'text_input(\n        "Lớp dạy"' in workspace
    assert "disabled=True" in workspace
    assert 'selectbox(\n        "Lớp dạy"' not in workspace


def test_teaching_date_field_keeps_unique_class_date_pairs():
    text = source()
    workspace = _function_source(
        text,
        "_render_lesson_plan_standardization_workspace",
    )

    assert "selected_teaching_date_pairs = tuple(dict.fromkeys(" in workspace
    assert "for class_id, teaching_date" in workspace
    assert 'text_input(\n        "Ngày dạy"' in workspace
    assert 'selected_lesson["teaching_dates_by_class"]' in workspace
    assert 'selectbox(\n            "Ngày dạy"' not in workspace


def test_ppct_choices_are_built_only_from_current_week_view_rows():
    text = source()
    workspace = _function_source(
        text,
        "_render_lesson_plan_standardization_workspace",
    )

    assert "WEEK_SCOPED_PPCT_OPTIONS_V1" in workspace
    assert "rows=filtered_schedule_rows" in workspace
    assert "schedule_rows = tuple(\n        view.rows" in workspace
    assert "all_week" not in workspace.casefold()
