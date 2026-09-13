from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202609130001_assessment_exam_canonical_validation_governance.sql"
)


def _text() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def _function(text: str, name: str) -> str:
    match = re.search(
        rf"create or replace function\s+public\.{name}\s*\(",
        text,
        flags=re.IGNORECASE,
    )
    assert match is not None, f"missing function {name}"
    end = text.index("revoke all on function", match.start())
    return text[match.start():end]


def _table(text: str, name: str) -> str:
    match = re.search(
        rf"create table public\.{name}\s*\(",
        text,
        flags=re.IGNORECASE,
    )
    assert match is not None, f"missing table {name}"
    end = text.index(";", match.start())
    return text[match.start():end]


def test_migration_is_one_transactional_forward_file() -> None:
    assert MIGRATION.is_file()
    text = _text().strip().lower()
    assert text.startswith("begin;")
    assert text.endswith("commit;")
    assert "create table public.assessment_exam_validation_evidence" in text
    assert "create table public.assessment_exam_warning_confirmations" in text


def test_validation_evidence_contract_and_status_invariants() -> None:
    table = _table(_text(), "assessment_exam_validation_evidence")
    required = (
        "validation_evidence_id uuid primary key",
        "exam_version_id uuid not null",
        "validation_revision bigint not null",
        "validation_status text not null",
        "errors jsonb not null",
        "warnings jsonb not null",
        "metrics jsonb not null",
        "validation_input_digest text not null",
        "evidence_digest text not null",
        "validated_at timestamptz not null",
        "validation_schema_version integer not null",
        "unique (exam_version_id, validation_revision)",
        "validation_revision > 0",
        "validation_schema_version > 0",
        "validation_status in ('PASS', 'WARNING', 'FAIL')",
        "jsonb_typeof(errors) = 'array'",
        "jsonb_typeof(warnings) = 'array'",
        "jsonb_typeof(metrics) = 'object'",
    )
    for marker in required:
        assert marker in table

    assert table.count("~ '^[0-9a-f]{64}$'") == 2
    assert re.search(
        r"validation_status = 'PASS'.*?errors = '\[\]'::jsonb"
        r".*?warnings = '\[\]'::jsonb",
        table,
        flags=re.DOTALL,
    )
    assert re.search(
        r"validation_status = 'WARNING'.*?errors = '\[\]'::jsonb"
        r".*?jsonb_array_length\(warnings\) > 0",
        table,
        flags=re.DOTALL,
    )
    assert re.search(
        r"validation_status = 'FAIL'.*?"
        r"jsonb_array_length\(errors\) > 0",
        table,
        flags=re.DOTALL,
    )


def test_warning_confirmation_and_review_binding_columns_exist() -> None:
    text = _text()
    table = _table(text, "assessment_exam_warning_confirmations")
    for marker in (
        "warning_confirmation_id uuid primary key",
        "exam_version_id uuid not null",
        "validation_evidence_id uuid not null",
        "owner_user_id uuid not null",
        "validation_evidence_digest text not null",
        "confirmed_warnings jsonb not null",
        "confirmed_at timestamptz not null",
        "unique (validation_evidence_id, owner_user_id)",
        "jsonb_typeof(confirmed_warnings) = 'array'",
    ):
        assert marker in table

    review_alter = re.search(
        r"alter table public\.assessment_exam_reviews\s+"
        r"add column validation_evidence_id.*?"
        r"add column warning_acknowledged boolean null;",
        text,
        flags=re.DOTALL,
    )
    assert review_alter is not None
    assert "add column validation_evidence_digest text null" in (
        review_alter.group(0)
    )


def test_history_is_append_only_with_explicit_triggers() -> None:
    text = _text()
    for trigger in (
        "assessment_exam_validation_evidence_append_only",
        "assessment_exam_warning_confirmations_append_only",
        "assessment_exam_reviews_append_only",
    ):
        trigger_match = re.search(
            rf"create trigger {trigger}\s+before update or delete",
            text,
            flags=re.IGNORECASE,
        )
        assert trigger_match is not None
    assert "Assessment exam governance history is append-only." in text


def test_digest_inputs_are_deterministic_and_evidence_is_canonical() -> None:
    text = _text()
    input_builder = _function(
        text,
        "build_assessment_exam_validation_input",
    )
    for marker in (
        "'exam_version_id'",
        "'setting_version_id'",
        "'setting_snapshot'",
        "'blueprint_version_id'",
        "'blueprint_cells'",
        "'question_count'",
        "'target_score'",
        "'exam_questions'",
        "'question_version_id'",
        "'assigned_score'",
        "'display_number'",
        "order by",
    ):
        assert marker in input_builder
    assert "created_at" not in input_builder
    assert "updated_at" not in input_builder

    input_digest = _function(
        text,
        "assessment_exam_validation_input_digest",
    )
    evidence_digest = _function(
        text,
        "assessment_exam_validation_evidence_digest",
    )
    for function in (input_digest, evidence_digest):
        assert "extensions.digest(" in function
        assert "::text" in function
        assert "'sha256'" in function
        assert "'hex'" in function

    for marker in (
        "'exam_version_id'",
        "'validation_schema_version'",
        "'validation_input_digest'",
        "'validation_status'",
        "'errors'",
        "'warnings'",
        "'metrics'",
    ):
        assert marker in evidence_digest
    for forbidden in (
        "validation_evidence_id",
        "validated_at",
        "validation_revision",
    ):
        assert forbidden not in evidence_digest


def test_validator_persists_and_reuses_only_identical_current_evidence() -> None:
    function = _function(_text(), "assessment_exam_validation_report")
    for marker in (
        "for update of exam_version",
        "assessment_exam_validation_input_digest",
        "assessment_exam_assembly_matches_blueprint",
        "assessment_exam_validation_evidence_digest",
        "validation_revision desc",
        "validation_input_digest",
        "validation_status",
        "errors is distinct from",
        "warnings is distinct from",
        "metrics is distinct from",
        "evidence_digest",
        "insert into public.assessment_exam_validation_evidence",
        "coalesce(evidence_row.validation_revision, 0) + 1",
        "'validation_evidence_id'",
        "'validated_at'",
    ):
        assert marker in function


def test_production_validator_has_no_warning_business_rule() -> None:
    function = _function(_text(), "assessment_exam_validation_report")
    producer = function[
        function.index("status_value := case"):
        function.index("metrics_value :=")
    ]
    assert "then 'PASS'" in producer
    assert "else 'FAIL'" in producer
    assert "'WARNING'" not in producer
    assert "warnings_value jsonb := '[]'::jsonb" in function
    assert "WARNING_EXTENSION_SEAM" in function


def test_confirmation_rpc_enforces_exact_current_warning() -> None:
    function = _function(
        _text(),
        "confirm_assessment_exam_validation_warnings",
    )
    for marker in (
        "AUTHENTICATION_REQUIRED",
        "ASSESSMENT_EXAM_OWNER_REQUIRED",
        "for update of exam_version",
        "validation_revision desc",
        "STALE_CANONICAL_VALIDATION_EVIDENCE",
        "PASS_HAS_NO_WARNINGS_TO_CONFIRM",
        "FAIL_VALIDATION_CANNOT_BE_OVERRIDDEN",
        "validation_status is distinct from 'WARNING'",
        "VALIDATION_EVIDENCE_DIGEST_MISMATCH",
        "target_confirmed_warnings is distinct from evidence_row.warnings",
        "insert into public.assessment_exam_warning_confirmations",
        "warning_confirmation_id",
    ):
        assert marker in function


def test_submit_review_and_publication_use_canonical_gates() -> None:
    text = _text()
    helper = _function(
        text,
        "assessment_exam_current_validation_governance",
    )
    for marker in (
        "CANONICAL_VALIDATION_EVIDENCE_REQUIRED",
        "STALE_CANONICAL_VALIDATION_EVIDENCE",
        "FAIL_VALIDATION_CANNOT_BE_OVERRIDDEN",
        "validation_status is distinct from 'WARNING'",
        "CURRENT_WARNING_CONFIRMATION_REQUIRED",
        "confirmed_warnings = evidence_row.warnings",
    ):
        assert marker in helper

    submit = _function(text, "submit_assessment_exam_for_review")
    review = _function(text, "apply_assessment_exam_review")
    publish = _function(text, "publish_assessment_exam")
    assert "CANONICAL_EVIDENCE_GATE_SUBMIT" in submit
    assert "assessment_exam_ready_for_review" in submit
    assert "assessment_exam_content_is_publishable" in submit
    assert "current_status = 'PENDING_REVIEW'" in submit
    assert "CANONICAL_EVIDENCE_GATE_REVIEW" in review
    assert "REVIEW_VALIDATION_EVIDENCE_MISMATCH" in review
    assert "WARNING_REVIEW_ACKNOWLEDGEMENT_REQUIRED" in review
    assert "new.warning_acknowledged is distinct from true" in review
    assert "FAIL_VALIDATION_CANNOT_BE_OVERRIDDEN" in review
    assert "CANONICAL_EVIDENCE_GATE_PUBLICATION" in publish
    assert "CURRENT_GOVERNED_APPROVED_REVIEW_REQUIRED" in publish
    assert "review.warning_acknowledged = true" in publish
    assert "governance_row.warning_confirmation_id is not null" in publish


def test_schema_three_snapshot_contains_governance_and_publisher() -> None:
    text = _text()
    builder = _function(
        text,
        "build_assessment_exam_snapshot_document",
    )
    assert (
        "rename to build_assessment_exam_snapshot_document_v2"
        in text
    )
    assert "build_assessment_exam_snapshot_document_v2(" in builder
    assert "'{snapshot_schema_version}'" in builder
    assert "'3'::jsonb" in builder
    assert "'published_by'" in builder
    assert "'{governance}'" in builder
    assert "'validation'" in builder
    assert "'teacher_confirmation'" in builder
    assert "when validation_status = 'PASS' then 'null'::jsonb" in builder
    assert "'review'" in builder
    for marker in (
        "'validation_status'",
        "'errors'",
        "'warnings'",
        "'metrics'",
        "'validation_evidence_id'",
        "'validation_input_digest'",
        "'evidence_digest'",
        "'validated_at'",
        "'validation_schema_version'",
        "'reviewer_user_id'",
        "'warning_acknowledged'",
        "'reviewed_at'",
    ):
        assert marker in builder


def test_snapshot_hash_stays_sha256_of_jsonb_text_without_rewrite() -> None:
    text = _text()
    capture = _function(
        text,
        "capture_assessment_exam_publication_snapshot",
    )
    assert "extensions.digest(snapshot_document_value::text, 'sha256')" in (
        capture
    )
    assert re.search(
        r"snapshot_schema_version,.*?\) values \(.*?\b3,",
        capture,
        flags=re.DOTALL,
    )
    assert not re.search(
        r"\b(update|delete from)\s+public\.assessment_exam_snapshots\b",
        text,
        flags=re.IGNORECASE,
    )
    assert "build_assessment_exam_snapshot_document_v2" in text


def test_rls_select_only_grants_and_no_direct_writes() -> None:
    text = _text()
    for table in (
        "assessment_exam_validation_evidence",
        "assessment_exam_warning_confirmations",
    ):
        assert re.search(
            rf"alter table public\.{table}\s+enable row level security;",
            text,
            flags=re.IGNORECASE,
        )
        assert (
            f"create policy {table}_select_visible"
            in text
        )

    grant = re.search(
        r"grant\s+(select)\s+on table\s+"
        r"public\.assessment_exam_validation_evidence,\s+"
        r"public\.assessment_exam_warning_confirmations\s+"
        r"to authenticated;",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert grant is not None
    assert grant.group(1).lower() == "select"
    assert not re.search(
        r"grant\s+(insert|update|delete).*?on table\s+.*?"
        r"assessment_exam_(validation_evidence|warning_confirmations)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert "from public, anon, authenticated;" in text
    assert "set search_path = ''" in text


def test_migration_does_not_modify_legacy_migration_files() -> None:
    text = _text()
    assert "202608250012_assessment_exam_review_publication.sql" not in text
    assert "202608250013_assessment_exam_immutable_snapshots.sql" not in text
    assert "202608250019_assessment_snapshot_schema_v2.sql" not in text
    assert "update public.assessment_exam_snapshots" not in text.lower()
