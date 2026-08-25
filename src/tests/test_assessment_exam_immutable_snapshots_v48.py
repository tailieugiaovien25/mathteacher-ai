from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608250013_assessment_exam_immutable_snapshots.sql"
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


def test_snapshot_migration_exists() -> None:
    assert MIGRATION.is_file()


def test_snapshot_table_is_unique_per_publication_and_exam() -> None:
    text = _migration_text()

    assert "assessment_exam_snapshots" in text
    assert "publication_id uuid not null unique" in text
    assert "exam_version_id uuid not null unique" in text
    assert "snapshot_document jsonb not null" in text
    assert "snapshot_hash text not null" in text


def test_snapshot_contains_exam_and_blueprint_context() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "build_assessment_exam_snapshot_document",
    )

    assert "'publication'" in function
    assert "'exam'" in function
    assert "'blueprint'" in function
    assert "'questions'" in function
    assert "exam_version.total_score" in function
    assert "exam_version.duration_minutes" in function


def test_snapshot_contains_question_content() -> None:
    text = _migration_text()

    for field_name in (
        "'prompt_text'",
        "'stimulus_text'",
        "'instruction_text'",
        "'question_type_code'",
        "'cognitive_level_code'",
        "'assigned_score'",
        "'content_hash'",
    ):
        assert field_name in text


def test_snapshot_contains_options_and_statements() -> None:
    text = _migration_text()

    assert "'options'" in text
    assert "assessment_question_options" in text
    assert "'is_correct'" in text
    assert "'statements'" in text
    assert "assessment_question_statements" in text
    assert "'correct_value'" in text


def test_snapshot_contains_answers_and_solutions() -> None:
    text = _migration_text()

    assert "'answer'" in text
    assert "assessment_question_answers" in text
    assert "'accepted_answers'" in text
    assert "'solutions'" in text
    assert "assessment_question_solutions" in text
    assert "'scoring_steps'" in text
    assert "assessment_question_scoring_steps" in text
    assert "'step_score'" in text


def test_snapshot_is_captured_after_publication_insert() -> None:
    text = _migration_text()

    assert (
        "create trigger "
        "assessment_exam_publications_capture_snapshot"
    ) in text
    assert "after insert" in text
    assert "capture_assessment_exam_publication_snapshot" in text


def test_snapshot_capture_rechecks_approved_publishable_content() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "capture_assessment_exam_publication_snapshot",
    )

    assert "current_status is distinct from 'APPROVED'" in function
    assert "assessment_exam_content_is_publishable" in function
    assert "new.published_by is distinct from" in function


def test_snapshot_uses_sha256_hash() -> None:
    text = _migration_text()

    assert "extensions.digest(" in text
    assert "'sha256'" in text
    assert "encode(" in text
    assert "char_length(snapshot_hash) = 64" in text


def test_snapshot_hash_can_be_recomputed_from_stored_jsonb() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "assessment_exam_snapshot_hash_matches",
    )

    assert "snapshot.snapshot_document::text" in function
    assert "extensions.digest(" in function
    assert "'sha256'" in function
    assert "snapshot.snapshot_hash = encode(" in function
    assert "assessment_exam_version_is_visible" in function
    assert (
        "grant execute on function\n"
        "public.assessment_exam_snapshot_hash_matches(uuid)"
    ) in text


def test_snapshot_mutation_is_blocked_by_trigger() -> None:
    text = _migration_text()

    assert "prevent_assessment_exam_snapshot_mutation" in text
    assert "before update or delete" in text
    assert "snapshots are immutable" in text


def test_snapshot_has_select_only_grant() -> None:
    text = _migration_text()

    start = text.index(
        "grant select\n"
        "on table public.assessment_exam_snapshots"
    )
    end = text.index(
        "drop policy if exists",
        start,
    )
    grant_text = text[start:end]

    assert "insert" not in grant_text
    assert "update" not in grant_text
    assert "delete" not in grant_text


def test_snapshot_rls_uses_exam_visibility() -> None:
    text = _migration_text()

    assert (
        "alter table public.assessment_exam_snapshots\n"
        "    enable row level security;"
    ) in text
    assert "assessment_exam_version_is_visible" in text
    assert "from anon;" in text


def test_snapshot_functions_are_not_granted_to_authenticated() -> None:
    text = _migration_text()

    assert (
        "grant execute on function\n"
        "public.build_assessment_exam_snapshot_document"
    ) not in text
    assert (
        "grant execute on function\n"
        "public.capture_assessment_exam_publication_snapshot"
    ) not in text


def test_migration_is_transactional() -> None:
    text = _migration_text().strip().lower()

    assert text.startswith("begin;")
    assert text.endswith("commit;")

