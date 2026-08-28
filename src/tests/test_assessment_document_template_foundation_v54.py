from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608250017_assessment_document_template_foundation.sql"
)


def _text() -> str:
    return MIGRATION.read_text(
        encoding="utf-8-sig"
    )


def test_template_foundation_has_four_tables() -> None:
    text = _text()

    assert text.count(
        "create table if not exists public.assessment_"
    ) == 4


def test_document_types_cover_complete_assessment_package() -> None:
    text = _text()

    for document_type in (
        "MATRIX",
        "SPECIFICATION",
        "STUDENT_EXAM",
        "ANSWER_KEY",
        "SCORING_GUIDE",
    ):
        assert f"'{document_type}'" in text


def test_matrix_and_specification_are_snapshot_scoped() -> None:
    text = _text()

    assert (
        "'MATRIX',\n"
        "        'Ma trận đề kiểm tra',\n"
        "        'SNAPSHOT'"
    ) in text
    assert (
        "'SPECIFICATION',\n"
        "        'Bản đặc tả đề kiểm tra',\n"
        "        'SNAPSHOT'"
    ) in text


def test_exam_outputs_are_variant_scoped() -> None:
    text = _text()

    for label in (
        "Đề dành cho học sinh",
        "Đáp án",
        "Hướng dẫn chấm",
    ):
        start = text.index(f"'{label}'")
        block = text[start:start + 150]
        assert "'VARIANT'" in block


def test_authority_scope_is_data_driven() -> None:
    text = _text()

    for scope in (
        "NATIONAL",
        "PROVINCE",
        "DISTRICT",
        "SCHOOL",
        "USER",
    ):
        assert f"'{scope}'" in text

    assert "authority_reference" in text


def test_template_versions_are_reviewed_and_versioned() -> None:
    text = _text()

    assert "version_number integer not null" in text
    assert "review_status text not null" in text
    assert "'PENDING_REVIEW'" in text
    assert "'REVISION_REQUIRED'" in text
    assert "'APPROVED'" in text
    assert "current_version_number" in text


def test_layout_style_binding_are_configuration_data() -> None:
    text = _text()

    required_schemas = (
        "global_layout_schema jsonb",
        "global_style_schema jsonb",
        "required_context_schema jsonb",
        "layout_schema jsonb",
        "style_schema jsonb",
        "binding_schema jsonb",
        "section_schema jsonb",
    )

    for schema in required_schemas:
        assert schema in text


def test_output_formats_are_not_hardcoded_to_one_renderer() -> None:
    text = _text()

    assert "supported_formats text[]" in text
    assert "'DOCX'" in text
    assert "'PDF'" in text
    assert "'JSON'" in text
    assert "renderer_code text not null" in text


def test_template_assets_are_version_integrity_protected() -> None:
    text = _text()

    assert "template_asset_path text null" in text
    assert "template_asset_hash text null" in text
    assert "char_length(template_asset_hash) = 64" in text


def test_approved_templates_are_immutable() -> None:
    text = _text()

    assert (
        "prevent_approved_assessment_template_mutation"
        in text
    )
    assert (
        "Approved assessment document templates "
        "are immutable."
    ) in text
    assert "before update or delete" in text


def test_only_approved_active_templates_are_globally_visible() -> None:
    text = _text()

    start = text.index(
        "public.assessment_document_template_set_is_visible("
    )
    end = text.index(
        "revoke all on function",
        start,
    )
    function = text[start:end]

    assert "lifecycle_status = 'ACTIVE'" in function
    assert "review_status =" in function
    assert "'APPROVED'" in function


def test_non_user_templates_are_admin_governed() -> None:
    text = _text()

    assert "authority_scope <> 'USER'" in text
    assert "current_user_is_portal_admin()" in text


def test_personal_templates_are_owner_governed() -> None:
    text = _text()

    assert "authority_scope = 'USER'" in text
    assert "owner_user_id = (select auth.uid())" in text


def test_anonymous_access_is_revoked_and_rls_enabled() -> None:
    text = _text()

    assert text.count(
        "enable row level security"
    ) == 4
    assert "from anon;" in text
    assert "to authenticated;" in text


def test_rls_references_outer_policy_rows_explicitly() -> None:
    text = _text()

    assert (
        "assessment_document_template_versions."
        "template_set_id"
    ) in text
    assert (
        "assessment_document_template_definitions."
        "template_version_id"
    ) in text

    assert (
        "template_set.template_set_id =\n"
        "                template_set_id"
    ) not in text
    assert (
        "template_version.template_version_id =\n"
        "                template_version_id"
    ) not in text


def test_template_identity_cannot_be_reassigned() -> None:
    text = _text()

    assert (
        "prevent_assessment_template_identity_reassignment"
        in text
    )

    protected_fields = (
        "new.template_code is distinct from old.template_code",
        "new.authority_scope is distinct from old.authority_scope",
        "new.owner_user_id is distinct from old.owner_user_id",
        "new.template_set_id is distinct from old.template_set_id",
        "new.version_number is distinct from old.version_number",
        "new.template_version_id is distinct from",
        "new.document_type_code is distinct from",
        "new.created_by is distinct from old.created_by",
    )

    for protected_field in protected_fields:
        assert protected_field in text

    assert text.count(
        "identity_immutable\n"
        "before update"
    ) == 3


def test_version_update_rechecks_destination_ownership() -> None:
    text = _text()

    policy_start = text.index(
        "assessment_template_versions_update_editable"
    )
    policy_end = text.index(
        "drop policy if exists\n"
        "assessment_template_definitions_select_visible",
        policy_start,
    )
    policy = text[policy_start:policy_end]

    assert "with check (" in policy
    assert (
        "assessment_document_template_versions."
        "template_set_id"
    ) in policy
    assert "owner_user_id =" in policy
    assert "current_user_is_portal_admin()" in policy


def test_templates_do_not_embed_authority_specific_columns() -> None:
    text = _text()

    forbidden_columns = (
        "dien_bien_layout",
        "district_matrix_columns",
        "ministry_fixed_header",
        "school_fixed_logo",
    )

    for forbidden_column in forbidden_columns:
        assert forbidden_column not in text
