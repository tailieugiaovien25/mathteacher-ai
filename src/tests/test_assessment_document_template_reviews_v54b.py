from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608250018_assessment_document_template_reviews.sql"
)


def _text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def test_review_history_table_exists() -> None:
    text = _text()

    assert (
        "create table if not exists "
        "public.assessment_document_template_reviews"
    ) in text
    assert "reviewer_user_id uuid not null" in text
    assert "reviewed_at timestamptz not null" in text


def test_review_decisions_are_explicit() -> None:
    text = _text()

    for decision in (
        "APPROVED",
        "REVISION_REQUIRED",
        "REJECTED",
    ):
        assert f"'{decision}'" in text


def test_readiness_requires_every_active_document_type() -> None:
    text = _text()

    start = text.index(
        "public.assessment_document_template_ready_for_review("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    function = text[start:end]

    assert "select count(*)" in function
    assert "document_type.is_active" in function
    assert "required_document_type.is_active" in function
    assert "not exists (" in function


def test_readiness_checks_dynamic_schemas_and_assets() -> None:
    text = _text()

    for field in (
        "supported_formats",
        "layout_schema",
        "style_schema",
        "binding_schema",
        "section_schema",
        "template_asset_path",
        "template_asset_hash",
    ):
        assert field in text


def test_readiness_supports_approved_activation() -> None:
    text = _text()

    start = text.index(
        "public.assessment_document_template_ready_for_review("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    readiness = text[start:end]

    assert "'DRAFT'" in readiness
    assert "'PENDING_REVIEW'" in readiness
    assert "'REVISION_REQUIRED'" in readiness
    assert "'APPROVED'" in readiness


def test_owner_or_authority_admin_submits_template() -> None:
    text = _text()

    start = text.index(
        "public.submit_assessment_document_template_for_review("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    function = text[start:end]

    assert "current_owner_user_id" in function
    assert "current_authority_scope" in function
    assert "current_user_is_portal_admin()" in function
    assert "'PENDING_REVIEW'" in function


def test_only_admin_reviews_templates() -> None:
    text = _text()

    start = text.index(
        "public.review_assessment_document_template("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    function = text[start:end]

    assert "current_user_is_portal_admin()" in function
    assert "Only a portal administrator" in function
    assert "'PENDING_REVIEW'" in function


def test_approval_rechecks_readiness() -> None:
    text = _text()

    start = text.index(
        "public.review_assessment_document_template("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    function = text[start:end]

    assert "target_decision = 'APPROVED'" in function
    assert (
        "assessment_document_template_ready_for_review("
        in function
    )


def test_activation_requires_approved_complete_version() -> None:
    text = _text()

    start = text.index(
        "public.activate_assessment_document_template_version("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    function = text[start:end]

    assert "current_review_status" in function
    assert "'APPROVED'" in function
    assert (
        "assessment_document_template_ready_for_review("
        in function
    )
    assert "approved_version_number" in function
    assert (
        "current_version_number =\n"
        "            approved_version_number"
    ) in function
    assert (
        "current_version_number =\n"
        "            current_version_number"
    ) not in function
    assert "lifecycle_status = 'ACTIVE'" in function


def test_user_activates_personal_template_only() -> None:
    text = _text()

    start = text.index(
        "public.activate_assessment_document_template_version("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    function = text[start:end]

    assert "current_authority_scope = 'USER'" in function
    assert "current_owner_user_id =" in function
    assert "current_user_is_portal_admin()" in function


def test_review_history_is_immutable() -> None:
    text = _text()

    assert (
        "prevent_assessment_template_review_mutation"
        in text
    )
    assert "before update or delete" in text
    assert (
        "Assessment document template reviews "
        "are immutable."
    ) in text


def test_review_history_has_no_direct_write_grant() -> None:
    text = _text()

    grant_start = text.index(
        "grant select\n"
        "on table public.assessment_document_template_reviews"
    )
    grant_end = text.index(
        "drop policy if exists",
        grant_start,
    )
    grant = text[grant_start:grant_end]

    assert "insert" not in grant
    assert "update" not in grant
    assert "delete" not in grant


def test_anonymous_access_is_revoked_and_rls_enabled() -> None:
    text = _text()

    assert "enable row level security" in text
    assert "from anon;" in text
    assert "to authenticated;" in text


def test_workflow_does_not_hardcode_authority_templates() -> None:
    text = _text()

    forbidden = (
        "DIEN_BIEN",
        "PHONG_GD",
        "SO_GD",
        "BO_GDDT",
    )

    for value in forbidden:
        assert value not in text
