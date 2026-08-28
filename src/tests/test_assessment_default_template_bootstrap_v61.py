from pathlib import Path


MIGRATION = Path(
    "supabase/migrations/"
    "202608260001_assessment_default_template_bootstrap.sql"
)


def _text() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def test_bootstrap_migration_exists_and_is_transactional() -> None:
    text = _text()

    assert text.startswith("begin;")
    assert text.rstrip().endswith("commit;")


def test_bootstrap_is_admin_only_and_idempotent() -> None:
    text = _text()

    assert "current_user_is_portal_admin()" in text
    assert "Only a portal administrator" in text
    assert "MATHTEACHER_DEFAULT_FLEXIBLE" in text
    assert "if target_template_version_id is not null" in text
    assert "return target_template_version_id" in text


def test_bootstrap_creates_all_required_documents() -> None:
    text = _text()

    for document_type in (
        "MATRIX",
        "SPECIFICATION",
        "STUDENT_EXAM",
        "ANSWER_KEY",
        "SCORING_GUIDE",
    ):
        assert f"'{document_type}'" in text

    assert "assessment_document_template_definitions" in text
    assert "array['DOCX', 'JSON']::text[]" in text
    assert "'DOCX_JSON_V1'" in text


def test_bootstrap_remains_draft_for_human_governance() -> None:
    text = _text()

    assert "'DRAFT'" in text
    assert "HUMAN_REVIEW_REQUIRED" in text
    assert "ADMIN duyệt trước khi kích hoạt" in text
    assert "review_status,\n        compatibility_schema_version" in text
    assert "lifecycle_status,\n            current_version_number" in text

    function_body = text[
        text.index("create or replace function") :
        text.index("revoke all on function")
    ]
    assert "'APPROVED'" not in function_body
    assert "'ACTIVE'" not in function_body
    assert "review_assessment_document_template(" not in function_body
    assert "activate_assessment_document_template_version(" not in function_body


def test_bootstrap_preserves_dynamic_template_contract() -> None:
    text = _text()

    for root in (
        "matrix",
        "specification",
        "questions",
        "answer_key",
        "scoring_guide",
    ):
        assert f"'{root}'" in text

    assert "jsonb_build_object(" in text
    assert "jsonb_build_array(" in text
    assert "'REPEAT'" in text
    assert "'customizable', true" in text
    assert "replaceable_without_system_change" in text


def test_bootstrap_function_has_narrow_execute_permission() -> None:
    text = _text()

    signature = (
        "public.create_default_assessment_document_template_draft()"
    )
    assert f"revoke all on function\n{signature}\nfrom public;" in text
    assert f"grant execute on function\n{signature}\nto authenticated;" in text
