from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608250010_assessment_exam_assembly_foundation.sql"
)


def _migration_text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def test_exam_assembly_migration_exists() -> None:
    assert MIGRATION.is_file()


def test_three_exam_tables_are_created() -> None:
    text = _migration_text()

    tables = re.findall(
        r"create table if not exists\s+"
        r"public\.(assessment_[a-z0-9_]+)",
        text,
        flags=re.IGNORECASE,
    )

    assert tables == [
        "assessment_exams",
        "assessment_exam_versions",
        "assessment_exam_questions",
    ]


def test_exam_identity_is_teacher_owned_and_versioned() -> None:
    text = _migration_text()

    assert "owner_user_id uuid not null" in text
    assert "current_version_number integer not null" in text
    assert "unique (\n        owner_user_id,\n        exam_code\n    )" in text
    assert "unique (\n        exam_id,\n        version_number\n    )" in text


def test_exam_requires_an_approved_locked_blueprint() -> None:
    text = _migration_text()

    assert "enforce_assessment_exam_version_context" in text
    assert "blueprint_status is distinct from 'APPROVED'" in text
    assert "blueprint_locked_at is null" in text
    assert "Only an approved locked blueprint" in text


def test_exam_context_and_totals_match_blueprint() -> None:
    text = _migration_text()

    assert "exam_subject_code is distinct from blueprint_subject_code" in text
    assert (
        "exam_education_level\n"
        "            is distinct from blueprint_education_level"
    ) in text
    assert "exam_grade_level is distinct from blueprint_grade_level" in text
    assert "new.total_score is distinct from blueprint_total_score" in text
    assert "new.duration_minutes" in text
    assert (
        "before insert or update of\n"
        "    exam_id,\n"
        "    blueprint_version_id,\n"
        "    total_score,\n"
        "    duration_minutes"
    ) in text
    assert (
        "before insert or update\n"
        "on public.assessment_exam_versions"
    ) not in text


def test_question_assignment_is_unique_and_ordered() -> None:
    text = _migration_text()

    assert (
        "unique (\n"
        "        exam_version_id,\n"
        "        question_version_id\n"
        "    )"
    ) in text
    assert (
        "unique (\n"
        "        exam_version_id,\n"
        "        display_number\n"
        "    )"
    ) in text


def test_only_approved_locked_questions_can_be_used() -> None:
    text = _migration_text()

    assert "actual_review_status is distinct from 'APPROVED'" in text
    assert "actual_locked_at is null" in text
    assert "actual_lifecycle_status is distinct from 'ACTIVE'" in text
    assert (
        "Only an active approved locked question may be used."
        in text
    )


def test_question_matches_exam_and_matrix_cell() -> None:
    text = _migration_text()

    assert "Blueprint cell does not belong to the exam blueprint." in text
    assert "actual_subject_code is distinct from exam_subject_code" in text
    assert (
        "actual_question_type_code\n"
        "            is distinct from expected_question_type_code"
    ) in text
    assert (
        "actual_cognitive_level_code\n"
        "            is distinct from expected_cognitive_level_code"
    ) in text


def test_question_primary_requirement_matches_topic() -> None:
    text = _migration_text()

    assert "assessment_question_requirement_links" in text
    assert "assessment_learning_requirements" in text
    assert "question_requirement.link_role = 'PRIMARY'" in text
    assert "requirement.topic_code = expected_topic_code" in text


def test_assigned_score_matches_approved_question_score() -> None:
    text = _migration_text()

    assert "new.assigned_score is distinct from actual_default_score" in text
    assert "Assigned score must match the approved question score." in text


def test_ai_question_selection_is_auditable() -> None:
    text = _migration_text()

    assert "selection_origin text not null default 'TEACHER'" in text
    assert "'AI_SUGGESTED'" in text
    assert "ai_selection_reference text null" in text


def test_admin_can_view_but_cannot_overwrite_exam() -> None:
    text = _migration_text()

    start = text.index(
        "create policy assessment_exams_update_owned"
    )
    end = text.index(
        "drop policy if exists",
        start,
    )
    update_policy = text[start:end]

    assert "owner_user_id = (select auth.uid())" in update_policy
    assert "current_user_is_portal_admin()" not in update_policy


def test_exam_content_is_editable_only_in_working_states() -> None:
    text = _migration_text()

    start = text.index(
        "public.assessment_exam_version_is_editable("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    function = text[start:end]

    assert "'DRAFT'" in function
    assert "'AI_PROPOSED'" in function
    assert "'ASSEMBLED'" in function
    assert "'REVISION_REQUIRED'" in function
    assert "'APPROVED'" not in function
    assert "'PUBLISHED'" not in function


def test_rls_and_anonymous_denial_cover_all_exam_tables() -> None:
    text = _migration_text()

    for table_name in (
        "assessment_exams",
        "assessment_exam_versions",
        "assessment_exam_questions",
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

