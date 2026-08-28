from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608250009_assessment_blueprint_reviews.sql"
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


def test_blueprint_review_migration_exists() -> None:
    assert MIGRATION.is_file()


def test_review_history_table_is_created() -> None:
    text = _migration_text()

    tables = re.findall(
        r"create table if not exists\s+"
        r"public\.(assessment_[a-z0-9_]+)",
        text,
        flags=re.IGNORECASE,
    )

    assert tables == [
        "assessment_blueprint_reviews",
    ]
    assert "blueprint_version_id uuid not null" in text
    assert "reviewer_user_id uuid not null" in text


def test_review_decisions_are_explicit() -> None:
    text = _migration_text()

    assert "decision in (" in text
    assert "'APPROVED'" in text
    assert "'REVISION_REQUIRED'" in text
    assert "'REJECTED'" in text


def test_owner_submission_requires_editable_complete_blueprint() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "submit_assessment_blueprint_for_review",
    )

    assert "owner_user_id" in function
    assert "auth.uid()" in function
    assert "assessment_blueprint_version_is_editable" in function
    assert "assessment_blueprint_ready_for_review" in function
    assert "review_status = 'PENDING_REVIEW'" in function


def test_only_admin_can_apply_review() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "apply_assessment_blueprint_review",
    )

    assert "current_user_is_portal_admin()" in function
    assert (
        "new.reviewer_user_id is distinct from "
        "(select auth.uid())"
    ) in function


def test_reviewer_cannot_review_own_blueprint() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "apply_assessment_blueprint_review",
    )

    assert "current_owner_user_id = (select auth.uid())" in function
    assert "may not review their own blueprint" in function


def test_only_pending_version_can_be_reviewed() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "apply_assessment_blueprint_review",
    )

    assert (
        "current_status is distinct from 'PENDING_REVIEW'"
        in function
    )


def test_approval_rechecks_readiness_and_locks_version() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "apply_assessment_blueprint_review",
    )

    approval_start = function.index(
        "if new.decision = 'APPROVED'"
    )
    approval_end = function.index(
        "elsif new.decision = 'REVISION_REQUIRED'"
    )
    approval = function[approval_start:approval_end]

    assert "assessment_blueprint_ready_for_review" in approval
    assert "review_status = 'APPROVED'" in approval
    assert "locked_at = now()" in approval
    assert "lifecycle_status = 'ACTIVE'" in approval
    assert "approved_version_number" in approval
    assert (
        "current_version_number =\n"
        "                approved_version_number"
    ) in approval
    assert (
        "current_version_number =\n"
        "                current_version_number"
    ) not in approval


def test_revision_required_unlocks_for_teacher_editing() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "apply_assessment_blueprint_review",
    )

    assert "review_status = 'REVISION_REQUIRED'" in function
    assert "locked_at = null" in function


def test_rejection_locks_version() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "apply_assessment_blueprint_review",
    )

    rejection_start = function.index(
        "elsif new.decision = 'REJECTED'"
    )
    rejection = function[rejection_start:]

    assert "review_status = 'REJECTED'" in rejection
    assert "locked_at = now()" in rejection


def test_review_trigger_runs_before_insert() -> None:
    text = _migration_text()

    assert "create trigger assessment_blueprint_reviews_apply" in text
    assert "before insert" in text
    assert (
        "execute function\n"
        "public.apply_assessment_blueprint_review();"
    ) in text


def test_review_history_is_immutable() -> None:
    text = _migration_text()

    grant_start = text.index(
        "grant select, insert"
    )
    policy_start = text.index(
        "drop policy if exists",
        grant_start,
    )
    grants = text[grant_start:policy_start]

    assert "update" not in grants
    assert "delete" not in grants
    assert (
        "create policy "
        "assessment_blueprint_reviews_insert_admin"
    ) in text


def test_rls_and_anonymous_denial_are_enabled() -> None:
    text = _migration_text()

    assert (
        "alter table public.assessment_blueprint_reviews\n"
        "    enable row level security;"
    ) in text
    assert "from anon;" in text
    assert "reviewer_user_id = (select auth.uid())" in text


def test_migration_is_transactional() -> None:
    text = _migration_text().strip().lower()

    assert text.startswith("begin;")
    assert text.endswith("commit;")

