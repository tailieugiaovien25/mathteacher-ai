from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608270002_assessment_blueprint_draft_authoring.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").lower()


def test_draft_rpc_uses_active_data_configured_profile() -> None:
    sql = _sql()

    assert "create_assessment_blueprint_draft" in sql
    assert "profile.status = 'active'" in sql
    assert "selected_profile.total_score" in sql
    assert "selected_profile.duration_minutes" in sql
    assert "selected_profile.program_code" in sql


def test_admin_activation_validates_profile_totals_and_authority() -> None:
    sql = _sql()

    assert "activate_assessment_profile" in sql
    assert "current_user_is_portal_admin" in sql
    assert "assessment_profile_section_total_mismatch" in sql
    assert "assessment_profile_level_score_mismatch" in sql
    assert "assessment_profile_level_percentage_mismatch" in sql
    assert "assessment_profile_authority_missing" in sql
    assert "status = 'active'" in sql


def test_draft_rpc_is_teacher_owned_and_idempotently_reuses_editable_version() -> None:
    sql = _sql()

    assert "current_user_id uuid := (select auth.uid())" in sql
    assert "blueprint.owner_user_id = current_user_id" in sql
    assert "assessment_blueprint_version_is_editable" not in sql
    assert "version.review_status in" in sql
    assert "editable_version.blueprint_version_id is not null" in sql
    assert "true;" in sql


def test_draft_rpc_rejects_scope_conflicts() -> None:
    sql = _sql()

    assert "grade_outside_profile_scope" in sql
    assert "blueprint_scope_conflict" in sql
    assert "editable_version_profile_conflict" in sql
    assert "blueprint_is_archived" in sql


def test_draft_rpc_is_not_available_to_anon() -> None:
    sql = _sql()

    assert "revoke all on function" in sql
    assert "from public" in sql
    assert "to authenticated" in sql
