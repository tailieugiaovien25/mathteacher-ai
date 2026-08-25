from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608250007_assessment_question_reviews.sql"
)


def _migration_text() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def test_question_reviews_migration_exists() -> None:
    assert MIGRATION.exists()


def test_question_reviews_define_immutable_history() -> None:
    text = _migration_text()

    assert (
        "create table if not exists "
        "public.assessment_question_reviews"
    ) in text
    assert "reviewer_user_id uuid not null" in text
    assert "'APPROVED'" in text
    assert "'REVISION_REQUIRED'" in text
    assert "'REJECTED'" in text
    assert "grant select, insert on table" in text
    assert "grant select, insert, update" not in text
    assert "grant select, insert, delete" not in text


def test_readiness_requires_canonical_answer() -> None:
    text = _migration_text()

    assert "assessment_question_ready_for_review" in text
    assert "assessment_question_answers answer" in text
    assert "answer.answer_mode" in text


def test_readiness_requires_primary_requirement_and_competency() -> None:
    text = _migration_text()

    assert "assessment_question_requirement_links link" in text
    assert "assessment_question_competency_links link" in text
    assert text.count("link.link_role = 'PRIMARY'") == 2


def test_multiple_choice_requires_four_options_and_one_correct() -> None:
    text = _migration_text()

    assert "option_count <> 4" in text
    assert "correct_option_count <> 1" in text
    assert "where option.is_correct = true" in text


def test_true_false_requires_four_statements() -> None:
    text = _migration_text()

    assert "question_type_code_value = 'TRUE_FALSE'" in text
    assert "statement_count <> 4" in text


def test_essay_requires_scoring_steps_and_matching_total() -> None:
    text = _migration_text()

    assert "question_type_code_value = 'ESSAY'" in text
    assert "assessment_question_scoring_steps scoring_step" in text
    assert "assessment_question_scoring_total_matches" in text


def test_owner_submission_requires_editable_complete_version() -> None:
    text = _migration_text()

    readiness_start = text.index(
        "public.assessment_question_ready_for_review("
    )
    readiness_end = text.index(
        "revoke all on function",
        readiness_start,
    )
    readiness_text = text[readiness_start:readiness_end]

    assert "'PENDING_REVIEW'" in readiness_text
    assert "submit_assessment_question_for_review" in text
    assert "assessment_question_version_is_editable" in text
    assert "review_status = 'PENDING_REVIEW'" in text

    approval_start = text.index(
        "if new.decision = 'APPROVED'"
    )
    approval_text = text[approval_start:]

    assert (
        "assessment_question_ready_for_review("
        in approval_text
    )


def test_only_admin_can_insert_review_decision() -> None:
    text = _migration_text()

    assert "assessment_question_reviews_insert_admin" in text
    assert "current_user_is_portal_admin()" in text
    assert "reviewer_user_id = (select auth.uid())" in text


def test_approval_locks_version_and_activates_question() -> None:
    text = _migration_text()

    assert "review_status = 'APPROVED'" in text
    assert "locked_at = now()" in text
    assert "current_version_number =" in text
    assert "lifecycle_status = 'ACTIVE'" in text


def test_revision_reopens_version() -> None:
    text = _migration_text()

    assert "review_status = 'REVISION_REQUIRED'" in text
    assert "locked_at = null" in text


def test_rejection_locks_rejected_version() -> None:
    text = _migration_text()

    assert "review_status = 'REJECTED'" in text
    assert "locked_at = now()" in text


def test_owner_and_ai_cannot_self_approve() -> None:
    core_text = Path(
        "supabase/migrations/"
        "202608250004_assessment_question_bank_core.sql"
    ).read_text(encoding="utf-8-sig")

    assert "'APPROVED'" not in core_text[
        core_text.index(
            "assessment_question_versions_insert_own"
        ):
        core_text.index(
            "assessment_question_versions_update_editable"
        )
    ]

    assert "assessment_question_reviews_insert_admin" in _migration_text()

