from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608250008_assessment_blueprint_foundation.sql"
)


def _migration_text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def test_blueprint_migration_exists() -> None:
    assert MIGRATION.is_file()


def test_four_blueprint_tables_are_created() -> None:
    text = _migration_text()

    tables = re.findall(
        r"create table if not exists\s+"
        r"public\.(assessment_[a-z0-9_]+)",
        text,
        flags=re.IGNORECASE,
    )

    assert tables == [
        "assessment_blueprints",
        "assessment_blueprint_versions",
        "assessment_blueprint_cells",
        "assessment_blueprint_requirement_links",
    ]


def test_blueprint_identity_is_teacher_owned() -> None:
    text = _migration_text()

    assert "owner_user_id uuid not null" in text
    assert "unique (\n        owner_user_id,\n        blueprint_code\n    )" in text
    assert "owner_user_id = (select auth.uid())" in text


def test_blueprint_versions_are_versioned_and_lockable() -> None:
    text = _migration_text()

    assert "version_number integer not null" in text
    assert "unique (\n        blueprint_id,\n        version_number\n    )" in text
    assert "locked_at timestamptz null" in text
    assert "'APPROVED'" in text
    assert "'REVISION_REQUIRED'" in text
    assert "'RETIRED'" in text


def test_ai_origin_is_auditable_but_not_self_approved() -> None:
    text = _migration_text()

    assert "origin_type text not null default 'HUMAN'" in text
    assert "ai_generation_reference text null" in text
    assert "created_by uuid not null" in text
    assert "review_status in (\n        'DRAFT',\n        'AI_PROPOSED'" in text


def test_cells_reference_profile_sections_and_curriculum() -> None:
    text = _migration_text()

    assert "assessment_profile_sections" in text
    assert "assessment_curriculum_topics" in text
    assert "assessment_cognitive_levels" in text
    assert "assessment_question_types" in text
    assert "response_count >= question_count" in text


def test_requirement_scope_is_explicit() -> None:
    text = _migration_text()

    assert "assessment_blueprint_requirement_links" in text
    assert "assessment_learning_requirements" in text
    assert "coverage_role in (" in text
    assert "'PRIMARY'" in text
    assert "'SUPPORTING'" in text


def test_cell_consistency_is_enforced() -> None:
    text = _migration_text()

    assert "enforce_assessment_blueprint_cell_consistency" in text
    assert "new.profile_code is distinct from expected_profile_code" in text
    assert "expected_question_type_code" in text
    assert (
        "new.question_type_code\n"
        "        is distinct from expected_question_type_code"
    ) in text
    assert "actual_topic_grade is distinct from expected_grade_level" in text
    assert "before insert or update" in text


def test_total_score_readiness_is_database_validated() -> None:
    text = _migration_text()

    assert "assessment_blueprint_totals_match" in text
    assert "sum(blueprint_cell.target_score)" in text
    assert "<= 0.0001" in text
    assert "assessment_blueprint_ready_for_review" in text
    assert "coverage_role = 'PRIMARY'" in text


def test_pending_state_is_supported_for_future_approval_recheck() -> None:
    text = _migration_text()

    start = text.index(
        "public.assessment_blueprint_ready_for_review("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    readiness_text = text[start:end]

    assert "'PENDING_REVIEW'" in readiness_text


def test_admin_cannot_overwrite_teacher_blueprint_content() -> None:
    text = _migration_text()

    start = text.index(
        "create policy assessment_blueprints_update_owned"
    )
    end = text.index(
        "drop policy if exists",
        start,
    )
    identity_update_policy = text[start:end]

    start = text.index(
        "create policy assessment_blueprint_versions_update_owned"
    )
    end = text.index(
        "drop policy if exists",
        start,
    )
    version_update_policy = text[start:end]

    assert "owner_user_id = (select auth.uid())" in identity_update_policy
    assert "current_user_is_portal_admin()" not in identity_update_policy
    assert "assessment_blueprint_version_is_editable" in version_update_policy
    assert "created_by = (select auth.uid())" in version_update_policy
    assert "owner_user_id =" in version_update_policy
    assert "current_user_is_portal_admin()" not in version_update_policy


def test_rls_and_anonymous_denial_cover_all_tables() -> None:
    text = _migration_text()

    for table_name in (
        "assessment_blueprints",
        "assessment_blueprint_versions",
        "assessment_blueprint_cells",
        "assessment_blueprint_requirement_links",
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

