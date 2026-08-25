from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608250004_assessment_question_bank_core.sql"
)


def _migration_text() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def test_question_bank_core_migration_exists() -> None:
    assert MIGRATION.exists()


def test_question_bank_core_defines_identity_and_versions() -> None:
    text = _migration_text()

    assert (
        "create table if not exists "
        "public.assessment_question_items"
    ) in text

    assert (
        "create table if not exists "
        "public.assessment_question_versions"
    ) in text


def test_question_identity_is_teacher_owned() -> None:
    text = _migration_text()

    assert "owner_user_id uuid not null" in text
    assert "references auth.users(id)" in text
    assert "owner_user_id = (select auth.uid())" in text
    assert "unique (\n        owner_user_id,\n        question_code" in text


def test_question_content_is_versioned_and_not_overwritten() -> None:
    text = _migration_text()

    assert "version_number integer not null" in text
    assert "unique (\n        question_id,\n        version_number" in text
    assert "locked_at timestamptz null" in text
    assert "grant select, insert, update on table" in text
    assert "grant select, insert, update, delete" not in text


def test_question_version_tracks_ai_provenance() -> None:
    text = _migration_text()

    assert "'HUMAN'" in text
    assert "'AI'" in text
    assert "'IMPORTED'" in text
    assert "ai_generation_reference text null" in text
    assert "'AI_PROPOSED'" in text


def test_ai_question_cannot_be_inserted_as_approved() -> None:
    text = _migration_text()

    insert_policy_start = text.index(
        "assessment_question_versions_insert_own"
    )
    update_policy_start = text.index(
        "assessment_question_versions_update_editable"
    )

    insert_policy = text[
        insert_policy_start:update_policy_start
    ]

    assert "'AI_PROPOSED'" in insert_policy
    assert "'APPROVED'" not in insert_policy
    assert "locked_at is null" in insert_policy


def test_locked_or_reviewed_version_is_not_editable() -> None:
    text = _migration_text()

    assert "assessment_question_version_is_editable" in text
    assert "question_version.locked_at is null" in text
    assert "question_version.review_status in (" in text
    assert "'APPROVED'" not in text[
        text.index(
            "question_version.review_status in ("
        ):
        text.index(
            "revoke all on function",
            text.index(
                "question_version.review_status in ("
            ),
        )
    ]


def test_question_bank_core_enables_rls() -> None:
    text = _migration_text()

    assert (
        "alter table public.assessment_question_items\n"
        "    enable row level security;"
    ) in text

    assert (
        "alter table public.assessment_question_versions\n"
        "    enable row level security;"
    ) in text

    assert "current_user_is_portal_admin()" in text
    assert "from anon" in text
    assert "to authenticated" in text


def test_admin_can_read_but_not_overwrite_teacher_question() -> None:
    text = _migration_text()

    select_policy_start = text.index(
        "assessment_question_items_select_authorized"
    )
    insert_policy_start = text.index(
        "assessment_question_items_insert_own"
    )

    select_policy = text[
        select_policy_start:insert_policy_start
    ]

    assert "current_user_is_portal_admin()" in select_policy

    update_policy_start = text.index(
        "assessment_question_items_update_own"
    )
    version_select_start = text.index(
        "assessment_question_versions_select_authorized"
    )

    update_policy = text[
        update_policy_start:version_select_start
    ]

    assert "current_user_is_portal_admin()" not in update_policy
    assert "owner_user_id = (select auth.uid())" in update_policy
    assert "current_user_is_portal_admin()" not in update_policy

