from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/202608270004_assessment_exam_settings.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").lower()


def test_settings_schema_is_versioned_and_reviewed() -> None:
    sql = _sql()
    for table in (
        "assessment_exam_setting_presets",
        "assessment_exam_setting_sets",
        "assessment_exam_setting_versions",
        "assessment_exam_setting_reviews",
    ):
        assert f"public.{table}" in sql
    assert "current_version_number" in sql
    assert "pending_review" in sql
    assert "revision_required" in sql
    assert "locked_at" in sql


def test_setting_scope_reuses_textbook_profile_and_requirement_catalogs() -> None:
    sql = _sql()
    for source in (
        "public.assessment_profiles",
        "public.textbook_catalog",
        "public.textbook_units",
        "public.assessment_learning_requirements",
        "public.assessment_curriculum_programs",
    ):
        assert source in sql
    assert "textbook_unit_scope_invalid" in sql
    assert "learning_requirement_scope_invalid" in sql


def test_default_preset_is_data_not_ui_code() -> None:
    sql = _sql()
    assert "math-thcs-periodic-default-v1" in sql
    assert "math-thcs-default-3223-v1" in sql
    assert "only_taught_content" in sql
    assert "intersection" in sql
    assert "textbook_is_context_not_authority" in sql
    assert "approved_and_locked_only" in sql
    assert "no_trait_conclusion_from_score_only" in sql


def test_governed_rpcs_enforce_owner_admin_and_no_self_review() -> None:
    sql = _sql()
    for function_name in (
        "save_assessment_exam_setting_draft",
        "submit_assessment_exam_setting_for_review",
        "review_assessment_exam_setting",
        "assessment_settings_current_user_is_admin",
    ):
        assert function_name in sql
    assert "shared_assessment_setting_requires_admin" in sql
    assert "assessment_setting_owner_required" in sql
    assert "assessment_setting_self_review_forbidden" in sql
    assert "current_user_is_portal_admin" in sql
    assert "to anon" not in sql
