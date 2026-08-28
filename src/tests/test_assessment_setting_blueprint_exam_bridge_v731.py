from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "supabase/migrations/202608270005_assessment_setting_blueprint_exam_bridge.sql"
BLUEPRINT_UI = ROOT / "src/portal_v2/ui/assessment_blueprint_authoring_streamlit.py"
GENERATION_UI = ROOT / "src/portal_v2/ui/assessment_exam_generation_streamlit.py"


def test_bridge_migration_requires_governed_setting_and_snapshot() -> None:
    text = MIGRATION.read_text(encoding="utf-8")
    for term in (
        "setting_version_id uuid",
        "setting_snapshot jsonb",
        "bind_assessment_setting_to_blueprint",
        "APPROVED_ACTIVE_SETTING_REQUIRED",
        "capture_exam_setting_snapshot",
        "BLUEPRINT_SETTING_REQUIRED_FOR_EXAM",
        "BLUEPRINT_REQUIREMENT_OUTSIDE_SETTING_SCOPE",
        "EXAM_SETTING_SNAPSHOT_IS_IMMUTABLE",
    ):
        assert term in text


def test_teacher_blueprint_page_binds_an_approved_setting() -> None:
    text = BLUEPRINT_UI.read_text(encoding="utf-8")
    assert "list_approved_settings" in text
    assert "bind_setting" in text
    assert "bind_assessment_setting_to_blueprint" in text
    assert "Thiết đặt đề kiểm tra đã duyệt" in text


def test_generation_catalog_requires_linked_setting() -> None:
    text = GENERATION_UI.read_text(encoding="utf-8")
    assert "setting_version_id" in text
    assert '("not_is", "setting_version_id", "null")' not in text
    assert '.not_.is_("setting_version_id", "null")' in text


def test_ui_does_not_write_bridge_tables_directly() -> None:
    for path in (BLUEPRINT_UI, GENERATION_UI):
        text = path.read_text(encoding="utf-8")
        assert '.insert(' not in text
        assert '.update(' not in text
        assert '.delete(' not in text
