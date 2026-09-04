from pathlib import Path


SOURCE = Path("src/portal_v2/ui/weekly_schedule_streamlit.py")
SERVICE = Path(
    "src/lesson_planning_v2/services/scheduled_lesson_context_service.py"
)


def test_v2_adapter_supplies_every_required_schedule_row_attribute():
    source = SOURCE.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    adapter = source[source.index("# G1B_13H1_V2_STANDARDIZE_ADAPTER"):]
    required = (
        "teaching_date",
        "class_id",
        "subject_ref",
        "component_ref",
        "curriculum_period",
        "lesson_id",
        "lesson_title",
        "session",
        "timetable_period",
        "period_in_lesson",
    )
    for name in required:
        assert f'"{name}"' in service
        assert f"{name}=" in adapter


def test_v2_adapter_uses_group_occurrence_as_representative_row_source():
    source = SOURCE.read_text(encoding="utf-8")
    adapter = source[source.index("# G1B_13H1_V2_STANDARDIZE_ADAPTER"):]
    assert 'context.get("occurrences", ())' in adapter
    assert "for source in (context, occurrence)" in adapter
    assert 'first("class_id", default="")' in adapter
    assert 'first("teaching_date", "date", "lesson_date")' in adapter


def test_previous_options_compatibility_fix_remains_present():
    source = SOURCE.read_text(encoding="utf-8")
    assert "supported_kwargs = {" in source
    assert "**supported_kwargs," in source
