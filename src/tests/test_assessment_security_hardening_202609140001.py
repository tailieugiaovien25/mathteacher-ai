from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202609140001_assessment_security_hardening.sql"
)

ANON_SIGNATURES = ['public.apply_assessment_exam_review()', 'public.assemble_assessment_exam_from_blueprint(uuid,text)', 'public.assessment_blueprint_ready_for_review(uuid)', 'public.assessment_blueprint_totals_match(uuid)', 'public.assessment_blueprint_version_is_editable(uuid)', 'public.assessment_blueprint_version_is_visible(uuid)', 'public.assessment_exam_assembly_matches_blueprint(uuid)', 'public.assessment_exam_cell_allocation_matches(uuid,uuid)', 'public.assessment_exam_content_is_publishable(uuid)', 'public.assessment_exam_current_validation_governance(uuid)', 'public.assessment_exam_ready_for_review(uuid)', 'public.assessment_exam_snapshot_hash_matches(uuid)', 'public.assessment_exam_validation_evidence_digest(uuid,integer,text,text,jsonb,jsonb,jsonb)', 'public.assessment_exam_validation_input_digest(uuid)', 'public.assessment_exam_validation_report(uuid)', 'public.assessment_exam_version_is_editable(uuid)', 'public.assessment_exam_version_is_visible(uuid)', 'public.assessment_question_scoring_total_matches(uuid)', 'public.assessment_question_version_is_editable(uuid)', 'public.assessment_question_version_is_visible(uuid)', 'public.assessment_settings_current_user_is_admin()', 'public.bind_assessment_setting_to_blueprint(uuid,uuid)', 'public.build_assessment_blueprint_snapshot_document(uuid)', 'public.build_assessment_exam_snapshot_document(uuid,uuid)', 'public.build_assessment_exam_snapshot_document_v1(uuid,uuid)', 'public.build_assessment_exam_snapshot_document_v2(uuid,uuid)', 'public.build_assessment_exam_validation_input(uuid)', 'public.capture_assessment_exam_publication_snapshot()', 'public.confirm_assessment_exam_validation_warnings(uuid,text,jsonb)', 'public.create_assessment_exam_draft(uuid,text,text,text)', 'public.current_user_is_portal_admin()', 'public.current_user_owns_assessment_question(uuid)', 'public.enforce_assessment_blueprint_cell_consistency()', 'public.enforce_assessment_exam_cell_capacity()', 'public.enforce_assessment_exam_question_alignment()', 'public.enforce_assessment_exam_version_context()', 'public.invalidate_assessment_exam_assembly()', 'public.mark_assessment_exam_assembled(uuid)', 'public.prevent_assessment_exam_governance_history_mutation()', 'public.prevent_assessment_exam_snapshot_mutation()', 'public.publish_assessment_exam(uuid,text,text)', 'public.review_assessment_exam_setting(uuid,text,text)', 'public.save_assessment_exam_setting_draft(text,text,text,text,text,integer,text,text,integer,integer,numeric,text,text,date,jsonb,jsonb,jsonb,jsonb,jsonb,jsonb,jsonb)', 'public.submit_assessment_exam_for_review(uuid)', 'public.submit_assessment_exam_setting_for_review(uuid)', 'public.validate_assessment_question_answer_mode()', 'public.validate_assessment_question_component_type()']

TRIGGER_SIGNATURES = ['public.apply_assessment_exam_review()', 'public.capture_assessment_exam_publication_snapshot()', 'public.enforce_assessment_blueprint_cell_consistency()', 'public.enforce_assessment_exam_cell_capacity()', 'public.enforce_assessment_exam_question_alignment()', 'public.enforce_assessment_exam_version_context()', 'public.invalidate_assessment_exam_assembly()', 'public.prevent_assessment_exam_governance_history_mutation()', 'public.prevent_assessment_exam_snapshot_mutation()', 'public.validate_assessment_question_answer_mode()', 'public.validate_assessment_question_component_type()']

SEVEN_INTERNAL_HELPERS = ['public.assessment_exam_validation_evidence_digest(uuid,integer,text,text,jsonb,jsonb,jsonb)', 'public.assessment_exam_validation_input_digest(uuid)', 'public.build_assessment_blueprint_snapshot_document(uuid)', 'public.build_assessment_exam_snapshot_document_v1(uuid,uuid)', 'public.build_assessment_exam_snapshot_document_v2(uuid,uuid)', 'public.build_assessment_exam_snapshot_document(uuid,uuid)', 'public.build_assessment_exam_validation_input(uuid)']

FOUR_INTERNAL_HELPERS = ['public.assessment_blueprint_totals_match(uuid)', 'public.assessment_exam_assembly_matches_blueprint(uuid)', 'public.assessment_exam_cell_allocation_matches(uuid,uuid)', 'public.mark_assessment_exam_assembled(uuid)']


def _text() -> str:
    return MIGRATION.read_text(encoding="utf-8-sig")


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", value).lower()


def test_security_hardening_is_transactional_and_fail_closed() -> None:
    assert MIGRATION.is_file()
    text = _text()
    compact = _compact(text)
    assert compact.startswith("--202609140001_assessment_security_hardening.sql")
    assert "\nbegin;" in text.lower()
    assert text.strip().lower().endswith("commit;")
    for marker in (
        "ASSESSMENT_SECURITY_PRE_CANONICAL_TABLES_REQUIRED",
        "ASSESSMENT_SECURITY_PRE_FIXED_PUBLISH_SEAM_REQUIRED",
        "ASSESSMENT_SECURITY_PRE_TARGET_SET_FAILED",
        "ASSESSMENT_SECURITY_PRE_TRIGGER_SET_FAILED",
        "ASSESSMENT_SECURITY_PRE_S1D3_RLS_REFERENCE_FOUND",
        "ASSESSMENT_SECURITY_POST_ANON_FAILED",
        "ASSESSMENT_SECURITY_POST_TRIGGER_ACL_FAILED",
        "ASSESSMENT_SECURITY_POST_INTERNAL_HELPER_ACL_FAILED",
        "ASSESSMENT_SECURITY_POST_SEARCH_PATH_FAILED",
        "ASSESSMENT_SECURITY_POST_PUBLISH_SEAM_DRIFT",
    ):
        assert marker in text


def test_exact_47_audited_functions_revoke_anon_execute() -> None:
    text = _compact(_text())
    assert len(ANON_SIGNATURES) == 47
    assert len(set(ANON_SIGNATURES)) == 47
    for signature in ANON_SIGNATURES:
        marker = _compact(
            f"revoke execute on function {signature} from anon;"
        )
        assert marker in text


def test_eleven_trigger_functions_are_not_direct_rpcs() -> None:
    text = _compact(_text())
    assert len(TRIGGER_SIGNATURES) == 11
    for signature in TRIGGER_SIGNATURES:
        for role in ("public", "anon", "authenticated"):
            marker = _compact(
                f"revoke execute on function {signature} from {role};"
            )
            assert marker in text


def test_two_updated_at_functions_get_fixed_search_path() -> None:
    text = _compact(_text())
    assert _compact(
        "alter function public.set_assessment_canonical_updated_at() "
        "set search_path = pg_catalog, public;"
    ) in text
    assert _compact(
        "alter function public.set_assessment_question_updated_at() "
        "set search_path = pg_catalog, public;"
    ) in text


def test_all_eleven_proven_internal_helpers_revoke_authenticated() -> None:
    text = _compact(_text())
    helpers = SEVEN_INTERNAL_HELPERS + FOUR_INTERNAL_HELPERS
    assert len(SEVEN_INTERNAL_HELPERS) == 7
    assert len(FOUR_INTERNAL_HELPERS) == 4
    assert len(helpers) == 11
    assert len(set(helpers)) == 11
    for signature in helpers:
        marker = _compact(
            f"revoke execute on function {signature} from authenticated;"
        )
        assert marker in text


def test_remaining_four_helpers_keep_the_rls_reference_guard() -> None:
    text = _text()
    for name in (
        "assessment_blueprint_totals_match",
        "assessment_exam_assembly_matches_blueprint",
        "assessment_exam_cell_allocation_matches",
        "mark_assessment_exam_assembled",
    ):
        assert f"('%' || t.name || '%')" not in text  # reject accidental literalized guard
        assert name in text
    assert "FROM pg_policy pol" in text
    assert "pg_get_expr(pol.polqual, pol.polrelid)" in text
    assert "pg_get_expr(pol.polwithcheck, pol.polrelid)" in text
    assert "rls_ref_count <> 0" in text


def test_publish_42702_fix_is_a_required_pre_and_post_condition() -> None:
    text = _text()
    old = "exam.current_version_number = current_version_number"
    fixed = "exam.current_version_number = current_exam_version_number"
    assert old in text
    assert fixed in text
    assert text.count("ASSESSMENT_SECURITY_PRE_FIXED_PUBLISH_SEAM_REQUIRED") == 1
    assert text.count("ASSESSMENT_SECURITY_POST_PUBLISH_SEAM_DRIFT") == 1


def test_hardening_does_not_change_business_logic_or_data() -> None:
    text = _text()
    # Strip line comments so descriptive safety comments do not look like SQL.
    executable = re.sub(r"--.*?$", "", text, flags=re.MULTILINE)
    lower = executable.lower()

    assert "create or replace function" not in lower
    assert "create table" not in lower
    assert "alter table" not in lower
    assert "create policy" not in lower
    assert "drop policy" not in lower
    assert not re.search(r"(?mi)^\s*grant\s+", executable)
    assert "service_role" not in lower

    # No application-data mutation statements.
    assert not re.search(r"(?mi)^\s*insert\s+into\s+", executable)
    assert not re.search(r"(?mi)^\s*update\s+public\.", executable)
    assert not re.search(r"(?mi)^\s*delete\s+from\s+", executable)
    assert not re.search(r"(?mi)^\s*truncate\s+", executable)


def test_postconditions_verify_effective_privileges_not_only_acl_text() -> None:
    text = _text()
    for role in ("authenticated", "anon", "public"):
        assert f"has_function_privilege('{role}', oid, 'EXECUTE')" in text
    assert "anon_effective_count <> 0" in text
    assert "helper_auth_count <> 0" in text
    assert "trigger_auth_count <> 0" in text


def test_catalog_oid_references_are_qualified_to_avoid_42702() -> None:
    text = _text()
    assert not re.search(r"\bcount\s*\(\s*oid\s*\)", text, flags=re.IGNORECASE)
    assert "count(r.oid)" in text
    assert (
        "has_function_privilege('anon', r.oid, 'EXECUTE')"
        in text
    )


def test_postcondition_resolved_cte_uses_r_alias_for_qualified_oid() -> None:
    text = _text()
    match = re.search(
        r"INTO\s+target_count,\s*resolved_count,\s*anon_effective_count"
        r"\s+FROM\s+resolved\s+(?P<alias>\w+)\s*;",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match is not None
    assert match.group("alias").lower() == "r"
    assert "count(r.oid)" in text
    assert "has_function_privilege('anon', r.oid, 'EXECUTE')" in text
