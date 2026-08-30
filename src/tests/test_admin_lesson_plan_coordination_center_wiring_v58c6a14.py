from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_navigation_has_coordination_center_constant_and_real_unicode_page():
    text = _text("src/portal_v2/ui/admin_navigation.py")
    assert (
        'ADMIN_PAGE_LESSON_PLAN_COORDINATION_CENTER = '
        '"lesson_plan_coordination_center"'
    ) in text
    assert "Trung t\u00e2m \u0111i\u1ec1u ph\u1ed1i gi\u00e1o \u00e1n" in text
    assert "\\u00e2m" not in text
    assert text.count("ADMIN_PAGE_LESSON_PLAN_COORDINATION_CENTER") == 2


def test_admin_shell_imports_and_routes_coordination_center():
    text = _text("src/portal_v2/ui/admin_shell.py")
    assert "ADMIN_PAGE_LESSON_PLAN_COORDINATION_CENTER" in text
    assert "render_admin_lesson_plan_coordination_center" in text
    assert (
        "page.page_id == ADMIN_PAGE_LESSON_PLAN_COORDINATION_CENTER"
        in text
    )


def test_coordination_center_reuses_existing_grouping_ui():
    center = _text(
        "src/portal_v2/ui/"
        "admin_lesson_plan_coordination_center_streamlit.py"
    )
    canonical = _text(
        "src/portal_v2/ui/admin_canonical_code_catalog_streamlit.py"
    )
    assert "render_admin_lesson_plan_grouping_policy" in center
    assert "def render_admin_lesson_plan_grouping_policy" in canonical
    assert (
        "_render_admin_lesson_plan_grouping_policy(st, client=client)"
        in canonical
    )


def test_no_duplicate_grouping_persistence_in_center():
    center = _text(
        "src/portal_v2/ui/"
        "admin_lesson_plan_coordination_center_streamlit.py"
    ).lower()
    assert "lesson_plan_grouping_policy_config" not in center
    assert ".upsert(" not in center
    assert ".insert(" not in center



def test_teacher_operational_runtime_preserved_while_global_settings_move_to_admin():
    teacher = _text("scripts/teacher_portal/app.py")
    weekly = _text("src/portal_v2/ui/weekly_schedule_streamlit.py")
    assert "render_lesson_plan_template_setup(" not in teacher
    assert "lesson_plan_tab" not in teacher
    assert "standardization_subject_filter" in weekly
    assert "standardization_component_filter" in weekly



def test_center_keeps_admin_config_boundary():
    center = _text(
        "src/portal_v2/ui/"
        "admin_lesson_plan_coordination_center_streamlit.py"
    )
    assert "SupabaseLessonPlanConfigurationRepository" in center
    assert "LessonPlanConfigurationService" in center
    assert "Ph\u1ea1m vi chuy\u1ec3n giao t\u1eeb USER" in center
