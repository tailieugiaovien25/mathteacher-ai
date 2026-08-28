from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608250011_assessment_exam_assembly_validation.sql"
)


def _migration_text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def _function_text(
    text: str,
    function_name: str,
) -> str:
    start = text.index(
        f"public.{function_name}("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    return text[start:end]


def test_exam_validation_migration_exists() -> None:
    assert MIGRATION.is_file()


def test_cell_capacity_prevents_question_overflow() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "enforce_assessment_exam_cell_capacity",
    )

    assert "maximum_question_count" in function
    assert "existing_question_count + 1" in function
    assert "exceeds blueprint cell capacity" in function


def test_cell_capacity_prevents_score_overflow() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "enforce_assessment_exam_cell_capacity",
    )

    assert "existing_assigned_score + new.assigned_score" in function
    assert "maximum_target_score + 0.0001" in function
    assert "exceeds blueprint cell target" in function


def test_update_excludes_current_assignment_from_capacity() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "enforce_assessment_exam_cell_capacity",
    )

    assert "tg_op = 'INSERT'" in function
    assert (
        "exam_question.exam_question_id\n"
        "                is distinct from new.exam_question_id"
    ) in function


def test_content_change_invalidates_assembled_state() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "invalidate_assessment_exam_assembly",
    )

    assert "'ASSEMBLED'" in function
    assert "'REVISION_REQUIRED'" in function
    assert "'AI_PROPOSED'" in function
    assert "'DRAFT'" in function
    assert "if tg_op = 'DELETE' then" in function
    assert "old.exam_version_id" in function
    assert "return old;" in function
    assert "return new;" in function
    assert "coalesce(new, old)" not in function
    assert "coalesce(\n        new.exam_version_id" not in function
    assert "after insert or update or delete" in text


def test_moving_question_invalidates_old_and_new_exam() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "invalidate_assessment_exam_assembly",
    )

    assert "old.exam_version_id" in function
    assert (
        "is distinct from new.exam_version_id"
    ) in function


def test_cell_match_checks_exact_count_and_score() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "assessment_exam_cell_allocation_matches",
    )

    assert "= blueprint_cell.question_count" in function
    assert "blueprint_cell.target_score" in function
    assert "<= 0.0001" in function


def test_complete_assembly_checks_every_blueprint_cell() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "assessment_exam_assembly_matches_blueprint",
    )

    assert "and not exists (" in function
    assert "assessment_exam_cell_allocation_matches" in function
    assert "blueprint_cell.blueprint_version_id" in function


def test_complete_assembly_checks_total_score() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "assessment_exam_assembly_matches_blueprint",
    )

    assert "sum(exam_question.assigned_score)" in function
    assert "exam_version.total_score" in function
    assert "<= 0.0001" in function


def test_question_numbering_must_be_continuous() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "assessment_exam_assembly_matches_blueprint",
    )

    assert "min(exam_question.display_number)" in function
    assert "= 1" in function
    assert "max(exam_question.display_number)" in function
    assert "count(*)::integer" in function


def test_mark_assembled_requires_owner_editability_and_match() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "mark_assessment_exam_assembled",
    )

    assert "assessment_exam_version_is_editable" in function
    assert "assessment_exam_assembly_matches_blueprint" in function
    assert "assembly_status = 'ASSEMBLED'" in function


def test_review_readiness_rechecks_assembly_and_blueprint() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "assessment_exam_ready_for_review",
    )

    assert "'ASSEMBLED'" in function
    assert "'PENDING_REVIEW'" in function
    assert "blueprint_version.review_status = 'APPROVED'" in function
    assert "blueprint_version.locked_at is not null" in function
    assert "assessment_exam_assembly_matches_blueprint" in function


def test_validation_functions_are_callable_by_authenticated_users() -> None:
    text = _migration_text()

    assert (
        "grant execute on function\n"
        "public.assessment_exam_cell_allocation_matches(uuid, uuid)"
    ) in text
    assert (
        "grant execute on function\n"
        "public.assessment_exam_assembly_matches_blueprint(uuid)"
    ) in text
    assert (
        "grant execute on function\n"
        "public.mark_assessment_exam_assembled(uuid)"
    ) in text


def test_migration_is_transactional() -> None:
    text = _migration_text().strip().lower()

    assert text.startswith("begin;")
    assert text.endswith("commit;")

