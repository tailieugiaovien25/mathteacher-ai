from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608260006_blueprint_requirement_link_rpc.sql"
)


def migration_text():
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def test_rpc_name_is_exact():
    text = migration_text()

    assert (
        "replace_assessment_blueprint_requirement_links"
        in text
    )


def test_function_only_migration_has_no_table_creation():
    text = migration_text().lower()

    assert "create table" not in text
    assert "alter table" not in text
    assert "drop table" not in text


def test_function_is_security_definer():
    text = migration_text().lower()

    assert "security definer" in text
    assert "set search_path = pg_catalog, public" in text


def test_rpc_validates_editability():
    text = migration_text()

    assert (
        "assessment_blueprint_version_is_editable"
        in text
    )

    assert "BLUEPRINT_VERSION_NOT_EDITABLE" in text


def test_payload_validation_occurs_before_delete():
    text = migration_text()

    delete_pos = text.index(
        "delete from public."
        "assessment_blueprint_requirement_links"
    )

    markers = (
        "ASSIGNMENTS_NOT_ARRAY",
        "EMPTY_ASSIGNMENT_SET",
        "ASSIGNMENT_NOT_OBJECT",
        "ASSIGNMENT_UNKNOWN_FIELD",
        "ASSIGNMENT_REQUIRED_FIELD_MISSING",
        "DUPLICATE_REQUIREMENT_CODE",
        "REQUIREMENT_NOT_FOUND",
        "REQUIREMENT_NOT_ACTIVE",
        "REQUIREMENT_NOT_VERIFIED",
        "INVALID_COVERAGE_ROLE",
        "INVALID_TARGET_QUESTION_COUNT",
        "INVALID_TARGET_SCORE",
        "INVALID_SEQUENCE_NUMBER",
    )

    for marker in markers:
        assert text.index(marker) < delete_pos


def test_duplicate_requirement_guard_exists():
    text = migration_text()

    assert "DUPLICATE_REQUIREMENT_CODE" in text
    assert "count(distinct requirement_code)" in text


def test_canonical_requirement_guards_exist():
    text = migration_text()

    assert "REQUIREMENT_NOT_FOUND" in text
    assert "REQUIREMENT_NOT_ACTIVE" in text
    assert "REQUIREMENT_NOT_VERIFIED" in text

    assert "assessment_learning_requirements" in text
    assert "r.status = 'ACTIVE'" in text
    assert "canonical_status" in text
    assert "'VERIFIED'" in text


def test_allocation_value_guards_exist():
    text = migration_text()

    assert "INVALID_COVERAGE_ROLE" in text
    assert "INVALID_TARGET_QUESTION_COUNT" in text
    assert "INVALID_TARGET_SCORE" in text
    assert "INVALID_SEQUENCE_NUMBER" in text


def test_delete_and_insert_same_function():
    text = migration_text().lower()

    assert (
        "delete from public."
        "assessment_blueprint_requirement_links"
        in text
    )

    assert (
        "insert into public."
        "assessment_blueprint_requirement_links"
        in text
    )


def test_insert_occurs_after_delete():
    text = migration_text().lower()

    delete_pos = text.index(
        "delete from public."
        "assessment_blueprint_requirement_links"
    )

    insert_pos = text.index(
        "insert into public."
        "assessment_blueprint_requirement_links"
    )

    assert delete_pos < insert_pos


def test_return_order_is_deterministic():
    text = migration_text()

    assert (
        "order by\n"
        "        l.sequence_number,\n"
        "        l.requirement_code"
        in text
    )


def test_authenticated_execute_granted():
    text = migration_text().lower()

    assert (
        "grant execute on function "
        "public.replace_assessment_blueprint_requirement_links"
        in text
    )

    assert "to authenticated;" in text


def test_public_and_anon_execute_revoked():
    text = migration_text().lower()

    assert (
        "from public;"
        in text
    )

    assert (
        "from anon;"
        in text
    )


def test_no_existing_data_backfill():
    text = migration_text().lower()

    function_pos = text.index(
        "create or replace function"
    )

    prefix = text[:function_pos]

    assert "insert into" not in prefix
    assert "update " not in prefix
    assert "delete from" not in prefix


def test_migration_only_mutates_links_when_rpc_invoked():
    text = migration_text().lower()

    assert text.count(
        "delete from public."
        "assessment_blueprint_requirement_links"
    ) == 1

    assert text.count(
        "insert into public."
        "assessment_blueprint_requirement_links"
    ) == 1


def test_rpc_contract_has_expected_error_codes():
    text = migration_text()

    expected = (
        "BLUEPRINT_VERSION_NOT_FOUND",
        "BLUEPRINT_VERSION_NOT_EDITABLE",
        "ASSIGNMENTS_NOT_ARRAY",
        "EMPTY_ASSIGNMENT_SET",
        "ASSIGNMENT_NOT_OBJECT",
        "ASSIGNMENT_UNKNOWN_FIELD",
        "ASSIGNMENT_REQUIRED_FIELD_MISSING",
        "DUPLICATE_REQUIREMENT_CODE",
        "REQUIREMENT_NOT_FOUND",
        "REQUIREMENT_NOT_ACTIVE",
        "REQUIREMENT_NOT_VERIFIED",
        "INVALID_COVERAGE_ROLE",
        "INVALID_TARGET_QUESTION_COUNT",
        "INVALID_TARGET_SCORE",
        "INVALID_SEQUENCE_NUMBER",
    )

    for marker in expected:
        assert marker in text
