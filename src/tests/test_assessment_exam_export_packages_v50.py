from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608250015_assessment_exam_export_packages.sql"
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


def test_export_migration_exists() -> None:
    assert MIGRATION.is_file()


def test_export_package_table_supports_three_audiences() -> None:
    text = _migration_text()

    assert "assessment_exam_export_packages" in text
    assert "'STUDENT_EXAM'" in text
    assert "'ANSWER_KEY'" in text
    assert "'SCORING_GUIDE'" in text
    assert "'DOCX'" in text
    assert "'PDF'" in text
    assert "'JSON'" in text


def test_export_records_template_identity_and_checksum() -> None:
    text = _migration_text()

    assert "template_code text not null" in text
    assert "template_version text not null" in text
    assert "package_payload jsonb not null" in text
    assert "char_length(package_hash) = 64" in text
    assert "package_status text not null default 'LOCKED'" in text


def test_student_payload_is_built_by_explicit_allowlist() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "build_assessment_student_exam_payload",
    )

    assert "'prompt_text'" in function
    assert "'stimulus_text'" in function
    assert "'instruction_text'" in function
    assert "'options'" in function
    assert "'statements'" in function
    assert "'answer'" not in function
    assert "'solutions'" not in function
    assert "'scoring_steps'" not in function
    assert "'is_correct'" not in function
    assert "'correct_value'" not in function
    assert "'feedback_text'" not in function


def test_student_payload_has_recursive_forbidden_key_guard() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "assessment_student_payload_has_forbidden_keys",
    )

    forbidden_keys = (
        "answer",
        "solutions",
        "scoring_steps",
        "is_correct",
        "correct_value",
        "feedback_text",
        "answer_explanation",
        "acceptance_note",
    )

    for forbidden_key in forbidden_keys:
        assert f"'$.**.{forbidden_key}'" in function

    creation = _function_text(
        text,
        "create_assessment_exam_export_package",
    )

    assert "target_package_type = 'STUDENT_EXAM'" in creation
    assert "assessment_student_payload_has_forbidden_keys" in creation
    assert "Student exam payload contains forbidden" in creation

    assert (
        "grant execute on function\n"
        "public.assessment_student_payload_has_forbidden_keys"
    ) not in text


def test_student_options_use_variant_codes_and_order() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "build_assessment_student_exam_payload",
    )

    assert "option_mapping.variant_option_code" in function
    assert "option_mapping.variant_sequence_number" in function
    assert "option_mapping.option_payload" in function
    assert "option_mapping.is_correct" not in function


def test_answer_key_uses_variant_correct_options() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "build_assessment_answer_key_payload",
    )

    assert "'correct_options'" in function
    assert "option_mapping.variant_option_code" in function
    assert "option_mapping.is_correct" in function
    assert "'statement_answers'" in function
    assert "'correct_value'" in function


def test_scoring_guide_contains_answer_solutions_and_steps() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "build_assessment_scoring_guide_payload",
    )

    assert "'answer'" in function
    assert "'solutions'" in function
    assert "'statements'" in function
    assert "'correct_options'" in function


def test_only_owner_exports_locked_variant() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "create_assessment_exam_export_package",
    )

    assert "source_owner_user_id is distinct from" in function
    assert "source_variant_status is distinct from 'LOCKED'" in function
    assert "assessment_exam_snapshot_hash_matches" in function


def test_export_package_hash_covers_payload_and_template() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "create_assessment_exam_export_package",
    )

    assert "'target_format'" in function
    assert "'template_code'" in function
    assert "'template_version'" in function
    assert "package_payload_value::text" in function
    assert "'sha256'" in function


def test_export_hash_can_be_verified() -> None:
    text = _migration_text()
    function = _function_text(
        text,
        "assessment_exam_export_package_hash_matches",
    )

    assert "export_package.package_payload::text" in function
    assert "export_package.package_hash = encode(" in function
    assert "assessment_exam_version_is_visible" in function


def test_export_packages_are_immutable() -> None:
    text = _migration_text()

    assert "prevent_assessment_exam_export_package_mutation" in text
    assert "before update or delete" in text
    assert "export packages are immutable" in text


def test_export_table_has_select_only_grant() -> None:
    text = _migration_text()

    start = text.index(
        "grant select\n"
        "on table public.assessment_exam_export_packages"
    )
    end = text.index(
        "create policy",
        start,
    )
    grant_text = text[start:end]

    assert "insert" not in grant_text
    assert "update" not in grant_text
    assert "delete" not in grant_text


def test_export_rls_uses_exam_visibility() -> None:
    text = _migration_text()

    assert (
        "alter table public.assessment_exam_export_packages\n"
        "    enable row level security;"
    ) in text
    assert "assessment_exam_version_is_visible" in text
    assert "from anon;" in text


def test_only_creation_and_hash_verification_are_callable() -> None:
    text = _migration_text()

    assert (
        "grant execute on function\n"
        "public.create_assessment_exam_export_package("
    ) in text
    assert (
        "grant execute on function\n"
        "public.assessment_exam_export_package_hash_matches(uuid)"
    ) in text
    assert (
        "grant execute on function\n"
        "public.build_assessment_student_exam_payload(uuid)"
    ) not in text


def test_migration_is_transactional() -> None:
    text = _migration_text().strip().lower()

    assert text.startswith("begin;")
    assert text.endswith("commit;")

