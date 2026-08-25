from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608250005_assessment_question_components.sql"
)


def _migration_text() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def test_question_components_migration_exists() -> None:
    assert MIGRATION.exists()


def test_question_components_define_required_tables() -> None:
    text = _migration_text()

    required_tables = (
        "assessment_question_options",
        "assessment_question_statements",
        "assessment_question_requirement_links",
        "assessment_question_competency_links",
    )

    for table_name in required_tables:
        assert (
            f"create table if not exists public.{table_name}"
            in text
        )


def test_multiple_choice_has_at_most_one_correct_option() -> None:
    text = _migration_text()

    assert (
        "assessment_question_options_one_correct_idx"
        in text
    )
    assert "where is_correct = true" in text
    assert "option_code text not null" in text
    assert "sequence_number integer not null" in text


def test_true_false_statements_store_independent_answers() -> None:
    text = _migration_text()

    assert "statement_code text not null" in text
    assert "statement_text text not null" in text
    assert "correct_value boolean not null" in text
    assert "explanation_text text not null" in text


def test_components_are_restricted_to_matching_question_types() -> None:
    text = _migration_text()

    assert (
        "validate_assessment_question_component_type"
        in text
    )
    assert "actual_question_type <> 'MULTIPLE_CHOICE'" in text
    assert "actual_question_type <> 'TRUE_FALSE'" in text
    assert (
        "assessment_question_options_validate_type"
        in text
    )
    assert (
        "assessment_question_statements_validate_type"
        in text
    )


def test_each_version_has_at_most_one_primary_requirement() -> None:
    text = _migration_text()

    assert (
        "assessment_question_requirements_one_primary_idx"
        in text
    )
    assert "where link_role = 'PRIMARY'" in text
    assert (
        "references "
        "public.assessment_learning_requirements(requirement_code)"
        in text
    )


def test_each_version_has_at_most_one_primary_competency() -> None:
    text = _migration_text()

    assert (
        "assessment_question_competencies_one_primary_idx"
        in text
    )
    assert (
        "references "
        "public.assessment_mathematical_competencies(competency_code)"
        in text
    )


def test_components_use_version_specific_links() -> None:
    text = _migration_text()

    assert text.count(
        "question_version_id uuid not null"
    ) == 4

    assert text.count(
        "references "
        "public.assessment_question_versions(question_version_id)"
    ) == 4


def test_component_rls_uses_visible_and_editable_functions() -> None:
    text = _migration_text()

    assert "assessment_question_version_is_visible" in text
    assert "assessment_question_version_is_editable" in text
    assert "current_user_is_portal_admin()" in text
    assert "enable row level security" in text
    assert "from anon" in text


def test_admin_visibility_does_not_grant_component_mutation() -> None:
    text = _migration_text()

    mutation_policy_start = text.index(
        "table_name || '_insert_editable'"
    )
    mutation_policy_text = text[mutation_policy_start:]

    assert (
        "assessment_question_version_is_editable"
        in mutation_policy_text
    )
    assert (
        "current_user_is_portal_admin()"
        not in mutation_policy_text
    )


def test_question_version_history_has_no_delete_policy() -> None:
    core_migration = Path(
        "supabase/migrations/"
        "202608250004_assessment_question_bank_core.sql"
    ).read_text(encoding="utf-8-sig")

    assert (
        "assessment_question_versions_delete"
        not in core_migration
    )
    assert (
        "grant select, insert, update, delete on table"
        not in core_migration
    )
