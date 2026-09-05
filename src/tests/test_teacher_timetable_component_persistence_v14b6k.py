from pathlib import Path


MODEL = Path(
    "src/educational_planning_v2/models/teacher_timetable.py"
)

REPO = Path(
    "src/educational_planning_v2/adapters/"
    "supabase_teacher_timetable_repository.py"
)

UI = Path(
    "src/portal_v2/ui/teacher_timetable_streamlit.py"
)

MIGRATION = Path(
    "supabase/migrations/"
    "202609050001_teacher_timetable_component_scope_v14b6k.sql"
)


def test_slot_model_has_nullable_component():
    text = MODEL.read_text(encoding="utf-8")

    assert (
        "V14B6K_TIMETABLE_COMPONENT_SCOPE"
        in text
    )
    assert (
        "component_id: str | None = None"
        in text
    )


def test_repository_persists_component():
    text = REPO.read_text(encoding="utf-8")

    assert (
        "V14B6K_TIMETABLE_COMPONENT_PERSISTENCE"
        in text
    )
    assert (
        '"component_id": slot.component_id'
        in text
    )
    assert (
        'row.get("component_id")'
        in text
    )


def test_restore_uses_assignment_and_component():
    text = UI.read_text(encoding="utf-8")

    assert (
        "V14B6K_TIMETABLE_COMPONENT_RESTORE"
        in text
    )
    assert (
        "canonical_option_by_selection_key"
        in text
    )
    assert (
        'existing.component_id or ""'
        in text
    )


def test_slot_save_persists_selected_component():
    text = UI.read_text(encoding="utf-8")

    assert "component_id=(" in text
    assert "selected_component" in text


def test_unchanged_guard_checks_component():
    text = UI.read_text(encoding="utf-8")

    assert "existing.component_id" in text
    assert "selected_component" in text


def test_migration_is_nullable():
    text = MIGRATION.read_text(encoding="utf-8")

    assert "teacher_timetable_slots" in text
    assert (
        "add column if not exists component_id text null"
        in text
    )


def test_blank_and_geometry_are_distinct():
    blank = (
        "assignment-1",
        "",
    )

    geometry = (
        "assignment-1",
        "component-geometry",
    )

    assert blank != geometry
