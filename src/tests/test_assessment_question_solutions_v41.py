from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608250006_assessment_question_solutions.sql"
)


def _migration_text() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def test_question_solutions_migration_exists() -> None:
    assert MIGRATION.exists()


def test_question_solutions_define_three_tables() -> None:
    text = _migration_text()

    required_tables = (
        "assessment_question_answers",
        "assessment_question_solutions",
        "assessment_question_scoring_steps",
    )

    for table_name in required_tables:
        assert (
            f"create table if not exists public.{table_name}"
            in text
        )


def test_each_version_has_one_canonical_answer() -> None:
    text = _migration_text()

    assert "question_version_id uuid not null unique" in text
    assert "answer_mode text not null" in text
    assert "exact_answer_text text null" in text


def test_short_response_supports_equivalent_answers() -> None:
    text = _migration_text()

    assert "accepted_answers jsonb not null" in text
    assert "jsonb_typeof(accepted_answers) = 'array'" in text
    assert "numeric_answer numeric null" in text
    assert "tolerance numeric null" in text
    assert "unit_text text null" in text
    assert "rounding_rule text null" in text


def test_numeric_tolerance_requires_numeric_answer() -> None:
    text = _migration_text()

    assert (
        "numeric_answer is not null\n"
        "        or tolerance is null"
    ) in text
    assert "tolerance >= 0" in text


def test_answer_mode_must_match_question_type() -> None:
    text = _migration_text()

    assert "validate_assessment_question_answer_mode" in text
    assert "question_type.answer_mode" in text
    assert "new.answer_mode <> expected_answer_mode" in text
    assert "assessment_question_answers_validate_mode" in text


def test_each_version_has_at_most_one_primary_solution() -> None:
    text = _migration_text()

    assert (
        "assessment_question_solutions_one_primary_idx"
        in text
    )
    assert "where is_primary = true" in text


def test_scoring_steps_support_equivalent_methods() -> None:
    text = _migration_text()

    assert "step_score numeric(6,2) not null" in text
    assert "acceptance_note text not null" in text
    assert "allows_equivalent_method boolean not null" in text
    assert "step_score > 0" in text


def test_scoring_steps_belong_to_same_solution_version() -> None:
    text = _migration_text()

    assert (
        "foreign key (\n"
        "        solution_id,\n"
        "        question_version_id"
    ) in text
    assert (
        "references public.assessment_question_solutions"
        in text
    )


def test_scoring_total_validation_is_available() -> None:
    text = _migration_text()

    assert "assessment_question_scoring_total_matches" in text
    assert "sum(scoring_step.step_score)" in text
    assert "question_version.default_score" in text
    assert "solution.solution_id" in text
    assert "group by" in text
    assert "> 0.0001" in text


def test_solution_tables_use_version_visibility_and_editability() -> None:
    text = _migration_text()

    assert "assessment_question_version_is_visible" in text
    assert "assessment_question_version_is_editable" in text
    assert "enable row level security" in text
    assert "from anon" in text


def test_admin_cannot_mutate_teacher_solution_content() -> None:
    text = _migration_text()

    mutation_start = text.index(
        "table_name || '_insert_editable'"
    )
    mutation_text = text[mutation_start:]

    assert "assessment_question_version_is_editable" in mutation_text
    assert "current_user_is_portal_admin()" not in mutation_text

