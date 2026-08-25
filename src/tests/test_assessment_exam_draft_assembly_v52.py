from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608250016_assessment_exam_draft_assembly.sql"
)


def _text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def _function(
    text: str,
    name: str,
) -> str:
    start = text.index(
        "create or replace function\n"
        f"public.{name}("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    return text[start:end]


def test_v52_migration_is_transactional() -> None:
    text = _text()

    assert text.startswith("begin;")
    assert text.rstrip().endswith("commit;")


def test_draft_creation_is_authenticated_and_owner_scoped() -> None:
    function = _function(
        _text(),
        "create_assessment_exam_draft",
    )

    assert "current_user_id := (select auth.uid())" in function
    assert "blueprint.owner_user_id" in function
    assert (
        "blueprint_owner_user_id is distinct from current_user_id"
        in function
    )


def test_draft_requires_governed_blueprint() -> None:
    function = _function(
        _text(),
        "create_assessment_exam_draft",
    )

    assert (
        "blueprint_lifecycle_status is distinct from 'ACTIVE'"
        in function
    )
    assert (
        "blueprint_review_status is distinct from 'APPROVED'"
        in function
    )
    assert "blueprint_locked_at is null" in function


def test_draft_creation_is_idempotent() -> None:
    function = _function(
        _text(),
        "create_assessment_exam_draft",
    )

    assert "target_idempotency_key" in function
    assert "generation_idempotency_key" in function
    assert "'reused',\n            true" in function
    assert "'reused',\n        false" in function
    assert "Exam code is already used" in function


def test_draft_idempotency_is_concurrency_safe() -> None:
    function = _function(
        _text(),
        "create_assessment_exam_draft",
    )

    lock_position = function.index(
        "pg_catalog.pg_advisory_xact_lock("
    )
    lookup_position = function.index(
        "from public.assessment_exams exam"
    )

    assert "pg_catalog.hashtextextended(" in function
    assert "current_user_id::text" in function
    assert "trim(target_exam_code)" in function
    assert lock_position < lookup_position


def test_draft_inherits_blueprint_context() -> None:
    function = _function(
        _text(),
        "create_assessment_exam_draft",
    )

    required_fields = (
        "blueprint_subject_code",
        "blueprint_education_level",
        "blueprint_grade_level",
        "blueprint_total_score",
        "blueprint_duration_minutes",
        "blueprint_academic_year",
        "blueprint_semester_number",
    )

    for field in required_fields:
        assert field in function


def test_assembly_locks_target_version_for_update() -> None:
    function = _function(
        _text(),
        "assemble_assessment_exam_from_blueprint",
    )

    assert "for update of exam_version" in function
    assert "assessment_exam_version_is_editable" in function


def test_assembly_uses_only_current_governed_questions() -> None:
    function = _function(
        _text(),
        "assemble_assessment_exam_from_blueprint",
    )

    assert "question.lifecycle_status = 'ACTIVE'" in function
    assert (
        "question.current_version_number =\n"
        "                    question_version.version_number"
    ) in function
    assert "question_version.review_status = 'APPROVED'" in function
    assert "question_version.locked_at is not null" in function


def test_assembly_matches_every_blueprint_dimension() -> None:
    function = _function(
        _text(),
        "assemble_assessment_exam_from_blueprint",
    )

    required_dimensions = (
        "current_subject_code",
        "current_education_level",
        "current_grade_level",
        "blueprint_cell.question_type_code",
        "blueprint_cell.cognitive_level_code",
        "blueprint_cell.topic_code",
        "blueprint_cell.target_score",
        "blueprint_cell.question_count",
    )

    for dimension in required_dimensions:
        assert dimension in function


def test_assembly_requires_primary_requirement_topic_match() -> None:
    function = _function(
        _text(),
        "assemble_assessment_exam_from_blueprint",
    )

    assert "assessment_question_requirement_links" in function
    assert "question_requirement.link_role = 'PRIMARY'" in function
    assert (
        "requirement.topic_code =\n"
        "                            blueprint_cell.topic_code"
    ) in function


def test_assembly_is_seeded_and_deterministic() -> None:
    function = _function(
        _text(),
        "assemble_assessment_exam_from_blueprint",
    )

    assert "target_selection_seed" in function
    assert "md5(" in function
    assert "question_version.question_version_id::text" in function
    assert "blueprint_cell.blueprint_cell_id::text" in function


def test_assembly_prevents_question_reuse() -> None:
    function = _function(
        _text(),
        "assemble_assessment_exam_from_blueprint",
    )

    assert "not exists (" in function
    assert "existing_question.question_version_id" in function
    assert (
        "existing_question.exam_version_id =\n"
        "                            target_exam_version_id"
    ) in function


def test_insufficient_cell_rolls_back_function_call() -> None:
    function = _function(
        _text(),
        "assemble_assessment_exam_from_blueprint",
    )

    assert "get diagnostics inserted_count = row_count" in function
    assert (
        "inserted_count <> blueprint_cell.question_count"
        in function
    )
    assert "Insufficient approved questions" in function


def test_assembly_is_marked_only_after_all_cells() -> None:
    function = _function(
        _text(),
        "assemble_assessment_exam_from_blueprint",
    )

    insert_position = function.index(
        "insert into public.assessment_exam_questions"
    )
    mark_position = function.index(
        "perform public.mark_assessment_exam_assembled("
    )

    assert insert_position < mark_position


def test_validation_report_matches_python_contract() -> None:
    function = _function(
        _text(),
        "assessment_exam_validation_report",
    )

    assert "'is_valid'" in function
    assert "'violations'" in function
    assert "'metrics'" in function
    assert "'question_count'" in function
    assert "'expected_question_count'" in function
    assert "'assigned_score'" in function
    assert "'expected_score'" in function
    assert "'matched_cell_count'" in function
    assert "'expected_cell_count'" in function


def test_validation_report_is_visibility_scoped() -> None:
    function = _function(
        _text(),
        "assessment_exam_validation_report",
    )

    assert (
        "current_owner_user_id is distinct from current_user_id"
        in function
    )
    assert "current_user_is_portal_admin()" in function


def test_v52_rpc_permissions_are_explicit() -> None:
    text = _text()

    function_names = (
        "create_assessment_exam_draft",
        "assemble_assessment_exam_from_blueprint",
        "assessment_exam_validation_report",
    )

    for function_name in function_names:
        assert (
            "revoke all on function\n"
            f"public.{function_name}"
        ) in text
        assert (
            "grant execute on function\n"
            f"public.{function_name}"
        ) in text

    assert "to authenticated;" in text
    assert "to anon;" not in text


def test_v52_does_not_generate_variants_or_publish() -> None:
    text = _text()

    assert "generate_assessment_exam_variant" not in text
    assert "publish_assessment_exam" not in text
    assert "assessment_exam_snapshots" not in text
    assert "assessment_exam_export_packages" not in text
