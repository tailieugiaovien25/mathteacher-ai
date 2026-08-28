from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608270001_blueprint_requirement_scope_guard.sql"
)


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8").lower()


def test_hotfix_uses_real_blueprint_version_primary_key() -> None:
    sql = _sql()

    assert "version.blueprint_version_id" in sql
    assert "version.id = target_blueprint_version_id" not in sql


def test_guard_enforces_subject_grade_program_topic_and_verified_scope() -> None:
    sql = _sql()

    required_contracts = (
        "blueprint.subject_code = program.subject_code",
        "blueprint.grade_level = requirement.grade_level",
        "topic.program_code = requirement.program_code",
        "topic.grade_level = requirement.grade_level",
        "requirement.status = 'active'",
        "topic.status = 'active'",
        "program.status = 'active'",
        "requirement.metadata ->> 'canonical_status'",
        "= 'verified'",
    )
    for contract in required_contracts:
        assert contract in sql


def test_guard_covers_rpc_and_direct_table_writes() -> None:
    sql = _sql()

    assert "create trigger assessment_blueprint_requirement_scope_guard" in sql
    assert "before insert or update" in sql
    assert "replace_assessment_blueprint_requirement_links" in sql
    assert "assessment_blueprint_version_is_editable" in sql
    assert "requirement_outside_blueprint_canonical_scope" in sql
