from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_domain_snapshot_exists():
    text = _text(
        "src/lesson_planning_v2/models/lesson_plan_configuration.py"
    )
    assert "class LessonPlanConfigurationSnapshot" in text
    assert "configuration_payload" in text


def test_repository_uses_applied_configuration_tables_read_only():
    text = _text(
        "src/lesson_planning_v2/adapters/"
        "supabase_lesson_plan_configuration_repository.py"
    )
    assert 'PROFILE_TABLE = "lesson_plan_configuration_profiles"' in text
    assert 'VERSION_TABLE = "lesson_plan_configuration_versions"' in text
    assert 'eq("lifecycle_status", "ACTIVE")' in text
    assert 'eq("version_status", "PUBLISHED")' in text
    lowered = text.lower()
    for forbidden in (".insert(", ".update(", ".upsert(", ".delete("):
        assert forbidden not in lowered


def test_repository_scope_precedence_is_explicit():
    text = _text(
        "src/lesson_planning_v2/adapters/"
        "supabase_lesson_plan_configuration_repository.py"
    )
    assert "row_subject == subject and row_component == component" in text
    assert "row_subject == subject and not row_component" in text
    assert "not row_subject and not row_component" in text


def test_service_has_admin_first_and_current_default_fallback():
    text = _text(
        "src/lesson_planning_v2/services/"
        "lesson_plan_configuration_service.py"
    )
    assert 'SOURCE_ADMIN = "ADMIN_ACTIVE"' in text
    assert 'SOURCE_CURRENT_DEFAULT = "CURRENT_CODE_DEFAULT"' in text
    assert "fallback_payload" in text


def test_admin_center_is_isolated_and_read_only():
    text = _text(
        "src/portal_v2/ui/"
        "admin_lesson_plan_coordination_center_streamlit.py"
    )
    assert "Trung tâm điều phối giáo án" in text
    assert "SupabaseLessonPlanConfigurationRepository" in text
    assert "LessonPlanConfigurationService" in text
    assert "Giai đoạn này chỉ đọc" in text



def test_patch_preserves_sensitive_runtime_while_user_global_menu_moves_to_admin():
    weekly = _text("src/portal_v2/ui/weekly_schedule_streamlit.py")
    teacher = _text("scripts/teacher_portal/app.py")
    assert "def render_weekly_schedule_workspace" in weekly
    assert "render_lesson_plan_template_setup(" not in teacher
    assert "lesson_plan_tab" not in teacher



def test_no_teacher_content_ownership_or_grouping_persistence_duplication():
    combined = "\n".join(
        _text(path)
        for path in (
            "src/lesson_planning_v2/models/lesson_plan_configuration.py",
            "src/lesson_planning_v2/adapters/"
            "supabase_lesson_plan_configuration_repository.py",
            "src/lesson_planning_v2/services/"
            "lesson_plan_configuration_service.py",
            "src/portal_v2/ui/"
            "admin_lesson_plan_coordination_center_streamlit.py",
        )
    ).lower()
    assert "owner_user_id" not in combined
    assert "teacher_user_id" not in combined
    assert "lesson_plan_grouping_policy_config" not in combined
