from pathlib import Path

MIGRATION = Path(
    "supabase/migrations/"
    "202608300013_protect_active_lesson_plan_configuration_version_v58c6a9.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def test_followup_migration_exists():
    assert MIGRATION.exists()


def test_guard_function_exists():
    sql = _sql()
    assert "protect_active_lesson_plan_configuration_version_retirement" in sql
    assert "returns trigger" in sql.lower()


def test_guard_checks_published_to_non_published_transition():
    sql = _sql()
    assert "old.version_status = 'PUBLISHED'" in sql
    assert "new.version_status <> 'PUBLISHED'" in sql


def test_guard_checks_active_profile_current_pointer():
    sql = _sql()
    assert "lesson_plan_configuration_profiles" in sql
    assert "p.lifecycle_status = 'ACTIVE'" in sql
    assert "p.current_version_id = old.configuration_version_id" in sql


def test_guard_is_before_update_of_version_status():
    sql = _sql().lower()
    assert "before update of version_status" in sql
    assert "lesson_plan_configuration_versions" in sql


def test_guard_requires_pointer_change_before_retirement():
    sql = _sql()
    assert "Cannot retire or unpublish" in sql


def test_no_teacher_content_or_grouping_policy_mutation():
    sql = _sql().lower()
    forbidden = [
        "owner_user_id",
        "teacher_user_id",
        "lesson_plan_grouping_policy_config",
        "insert into",
        "delete from",
        "truncate ",
    ]
    for term in forbidden:
        assert term not in sql
