from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase/migrations/"
    "202608300012_admin_lesson_plan_configuration_foundation_v58c6a4.sql"
)


def migration_text() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def test_migration_1_creates_versioned_admin_lesson_plan_configuration():
    text = migration_text()

    assert "create table if not exists public.lesson_plan_configuration_profiles" in text
    assert "create table if not exists public.lesson_plan_configuration_versions" in text
    assert "configuration_payload jsonb not null" in text
    assert "current_version_id uuid null" in text
    assert "unique (profile_id, version_number)" in text


def test_active_scope_is_unique_and_requires_published_current_version():
    text = migration_text()

    assert "lesson_plan_configuration_profiles_one_active_scope" in text
    assert "where lifecycle_status = 'ACTIVE'" in text
    assert "ACTIVE lesson-plan configuration requires current_version_id." in text
    assert "ACTIVE lesson-plan configuration must point to a PUBLISHED version." in text
    assert "selected_version.profile_id <> new.profile_id" in text


def test_runtime_read_is_active_only_while_admin_can_manage_all():
    text = migration_text()

    assert "lesson_plan_configuration_profiles_runtime_read" in text
    assert "lifecycle_status = 'ACTIVE'" in text
    assert "or (select public.current_user_is_portal_admin())" in text

    assert "lesson_plan_configuration_versions_runtime_read" in text
    assert "version_status = 'PUBLISHED'" in text
    assert "profile.current_version_id =" in text

    for suffix in ("insert", "update", "delete"):
        assert f"lesson_plan_configuration_profiles_admin_{suffix}" in text
        assert f"lesson_plan_configuration_versions_admin_{suffix}" in text


def test_canonical_configuration_has_no_teacher_owner_boundary():
    text = migration_text().lower()

    assert "owner_user_id" not in text
    assert "teacher_user_id" not in text
    assert "lesson_plan_workspace_drafts" not in text
    assert "teacher_documents" not in text


def test_grouping_policy_is_reused_not_duplicated():
    text = migration_text()

    assert "create table if not exists public.lesson_plan_grouping_policy_config" not in text
    assert "Existing lesson_plan_grouping_policy_config is reused" in text


def test_published_payload_is_protected_by_new_version_rule():
    text = migration_text()

    assert "protect_published_lesson_plan_configuration_version" in text
    assert "old.version_status = 'PUBLISHED'" in text
    assert "new.configuration_payload is distinct from old.configuration_payload" in text
    assert "create a new version" in text


def test_migration_does_not_seed_or_migrate_user_session_configuration():
    text = migration_text().lower()

    # Migration 1 establishes canonical authority only.
    # It deliberately does not promote per-session teacher choices.
    assert "insert into public.lesson_plan_configuration_profiles" not in text
    assert "insert into public.lesson_plan_configuration_versions" not in text
    assert "st.session_state" not in text
