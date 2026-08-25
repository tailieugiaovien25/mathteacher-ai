from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608250012_assessment_exam_review_publication.sql"
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


def test_exam_review_publication_migration_exists() -> None:
    assert MIGRATION.is_file()


def test_review_and_publication_tables_are_created() -> None:
    text = _migration_text()

    tables = re.findall(
        r"create table if not exists\s+"
        r"public\.(assessment_[a-z0-9_]+)",
        text,
        flags=re.IGNORECASE,
    )

    assert tables == [
        "assessment_exam_reviews",
        "assessment_exam_publications",
    ]


def test_publication_is_unique_per_exam_version() -> None:
    text = _migration_text()

    assert "exam_version_id uuid not null unique" in text
    assert "published_by uuid not null" in text
    assert "published_at timestamptz not null default now()" in text


def test_publishability_rechecks_blueprint_and_questions() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "assessment_exam_content_is_publishable",
    )

    assert "blueprint_version.review_status = 'APPROVED'" in function
    assert "blueprint_version.locked_at is not null" in function
    assert "assessment_exam_assembly_matches_blueprint" in function
    assert "question_version.review_status" in function
    assert "question_version.locked_at is null" in function
    assert "question.lifecycle_status" in function
    assert "'ACTIVE'" in function


def test_owner_submits_only_assembled_complete_exam() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "submit_assessment_exam_for_review",
    )

    assert "owner_user_id" in function
    assert "current_status is distinct from 'ASSEMBLED'" in function
    assert "assessment_exam_ready_for_review" in function
    assert "assessment_exam_content_is_publishable" in function
    assert "assembly_status = 'PENDING_REVIEW'" in function


def test_only_admin_can_review() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "apply_assessment_exam_review",
    )

    assert "current_user_is_portal_admin()" in function
    assert "new.reviewer_user_id is distinct from" in function


def test_reviewer_cannot_review_own_exam() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "apply_assessment_exam_review",
    )

    assert "current_owner_user_id = (select auth.uid())" in function
    assert "may not review their own exam" in function


def test_approval_rechecks_and_locks_exam() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "apply_assessment_exam_review",
    )

    approval_start = function.index(
        "if new.decision = 'APPROVED'"
    )
    approval_end = function.index(
        "elsif new.decision = 'REVISION_REQUIRED'"
    )
    approval = function[approval_start:approval_end]

    assert "assessment_exam_ready_for_review" in approval
    assert "assessment_exam_content_is_publishable" in approval
    assert "assembly_status = 'APPROVED'" in approval
    assert "locked_at = now()" in approval
    assert "approved_version_number" in approval
    assert "lifecycle_status = 'ACTIVE'" in approval


def test_revision_unlocks_and_rejection_locks() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "apply_assessment_exam_review",
    )

    assert "assembly_status = 'REVISION_REQUIRED'" in function
    assert "locked_at = null" in function
    assert "assembly_status = 'REJECTED'" in function
    assert "locked_at = now()" in function


def test_review_history_is_immutable() -> None:
    text = _migration_text()

    start = text.index(
        "grant select, insert\n"
        "on table public.assessment_exam_reviews"
    )
    end = text.index(
        "grant select\n"
        "on table public.assessment_exam_publications",
        start,
    )
    review_grant = text[start:end]

    assert "grant select, insert" in review_grant
    assert "update" not in review_grant
    assert "delete" not in review_grant
    assert "assessment_exam_reviews_insert_admin" in text


def test_only_owner_publishes_current_approved_version() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "publish_assessment_exam",
    )

    assert "current_owner_user_id is distinct from" in function
    assert "current_status is distinct from 'APPROVED'" in function
    assert "exam.current_version_number" in function
    assert "current_version_number" in function


def test_publication_rechecks_content_and_sets_published() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "publish_assessment_exam",
    )

    assert "assessment_exam_content_is_publishable" in function
    assert "assessment_exam_publications" in function
    assert "assembly_status = 'PUBLISHED'" in function
    assert "return new_publication_id" in function


def test_exam_identity_sensitive_columns_have_no_direct_update_grant() -> None:
    text = _migration_text()

    assert (
        "revoke update\n"
        "on table public.assessment_exams\n"
        "from authenticated;"
    ) in text

    start = text.index(
        "grant update (\n"
        "    exam_code,"
    )
    end = text.index(
        "drop policy if exists",
        start,
    )
    restricted_grant = text[start:end]

    assert "exam_code" in restricted_grant
    assert "metadata" in restricted_grant
    assert "updated_at" in restricted_grant
    assert "current_version_number" not in restricted_grant
    assert "owner_user_id" not in restricted_grant
    assert "subject_code" not in restricted_grant
    assert "education_level" not in restricted_grant
    assert "grade_level" not in restricted_grant
    assert "lifecycle_status" not in restricted_grant


def test_publication_history_has_no_direct_insert_grant() -> None:
    text = _migration_text()

    start = text.index(
        "grant select\n"
        "on table public.assessment_exam_publications"
    )
    end = text.index(
        "revoke update\n"
        "on table public.assessment_exams",
        start,
    )
    publication_grant = text[start:end]

    assert "insert" not in publication_grant
    assert "update" not in publication_grant
    assert "delete" not in publication_grant


def test_rls_and_anonymous_denial_cover_review_tables() -> None:
    text = _migration_text()

    for table_name in (
        "assessment_exam_reviews",
        "assessment_exam_publications",
    ):
        assert (
            f"alter table public.{table_name}\n"
            "    enable row level security;"
        ) in text

    assert "from anon;" in text


def test_migration_is_transactional() -> None:
    text = _migration_text().strip().lower()

    assert text.startswith("begin;")
    assert text.endswith("commit;")


