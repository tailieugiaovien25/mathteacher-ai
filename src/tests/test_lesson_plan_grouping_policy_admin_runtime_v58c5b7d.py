from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_admin_policy_attached_to_existing_canonical_page():
    text = (
        ROOT / "src/portal_v2/ui/admin_canonical_code_catalog_streamlit.py"
    ).read_text(encoding="utf-8-sig")
    assert "V58_C5B7D_GROUPING_POLICY_ADMIN" in text
    assert "def _render_admin_lesson_plan_grouping_policy" in text
    assert "LessonPlanGroupingMode.BY_WEEK" in text
    assert "policy_repo.upsert_config" in text
    assert "Ch?nh s?ch nh?m gi?o ?n" not in text
    assert "SupabaseLessonPlanGroupingPolicyRepository" in text


def test_runtime_policy_injection_remains_shadow():
    text = (
        ROOT / "src/portal_v2/ui/weekly_schedule_streamlit.py"
    ).read_text(encoding="utf-8-sig")
    assert "V58_C5B7D_RUNTIME_POLICY_INJECTION" in text
    assert "SupabaseLessonPlanGroupingPolicyRepository(client)" in text
    assert "_v58_c5b2_shadow_lesson_plan_groups" in text
    assert "_v58_c5b7d_policy_load_error" in text


def test_migration_contract():
    base_text = (
        ROOT / "supabase/migrations/202608300010_lesson_plan_grouping_policy_config_v58c5b7d.sql"
    ).read_text(encoding="utf-8")
    extension_text = (
        ROOT / "supabase/migrations/202608300011_lesson_plan_grouping_by_grade_v58c5b7j2.sql"
    ).read_text(encoding="utf-8")

    for token in ("BY_PERIOD", "BY_LESSON", "BY_WEEK"):
        assert token in base_text
    assert "BY_GRADE" not in base_text
    assert "BY_GRADE" in extension_text
    assert "drop table" not in extension_text.lower()

    text = base_text
    assert "portal_roles" in text
    assert "pr.role = 'admin'" in text
    assert "for select" in text.lower()
    assert "for insert" in text.lower()
    assert "for update" in text.lower()


def test_year_week_bridge_preserved():
    text = (
        ROOT / "src/portal_v2/ui/weekly_schedule_streamlit.py"
    ).read_text(encoding="utf-8-sig")
    assert "def _sync_standardization_week_to_lbg" in text
    assert "def _emit_canonical_week_change" in text
