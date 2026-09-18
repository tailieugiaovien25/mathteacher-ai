-- 202609140001_assessment_security_hardening.sql
-- Source-controlled consolidation of the Assessment SECURITY DEFINER hardening
-- proven on the isolated MathTeacherAI-B3C4B2-Test project.
--
-- SCOPE ONLY:
--   * revoke anon EXECUTE on the exact 47 audited SECURITY DEFINER functions;
--   * remove PUBLIC/anon/authenticated direct RPC execution from 11 trigger functions;
--   * fix search_path on 2 updated_at trigger functions;
--   * revoke authenticated EXECUTE from 7 proven internal digest/snapshot/input helpers;
--   * revoke authenticated EXECUTE from 4 proven internal assembly helpers.
--
-- DOES NOT:
--   * change function bodies or business logic;
--   * change RLS policies, tables, or application data;
--   * change service_role grants;
--   * grant any new privilege.
--
-- FAIL-CLOSED:
--   * canonical governance and the fixed publish seam must already exist;
--   * all exact audited function signatures must resolve as SECURITY DEFINER;
--   * the 4 assembly helpers must not be referenced by RLS policies;
--   * postconditions must prove the intended final ACL/search_path state.

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '60s';

DO $assessment_security_pre$
DECLARE
    target_count integer;
    resolved_count integer;
    secdef_count integer;
    trigger_count integer;
    trigger_secdef_count integer;
    trigger_return_count integer;
    rls_ref_count integer;
    publish_definition text;
    review_column_count integer;
BEGIN
    IF to_regclass('public.assessment_exam_validation_evidence') IS NULL
       OR to_regclass('public.assessment_exam_warning_confirmations') IS NULL THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_PRE_CANONICAL_TABLES_REQUIRED';
    END IF;

    SELECT count(*)
    INTO review_column_count
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'assessment_exam_reviews'
      AND column_name IN (
          'validation_evidence_id',
          'validation_evidence_digest',
          'warning_acknowledged'
      );

    IF review_column_count <> 3 THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_PRE_CANONICAL_REVIEW_COLUMNS_REQUIRED count=% expected=3',
          review_column_count;
    END IF;

    SELECT pg_get_functiondef(
        to_regprocedure('public.publish_assessment_exam(uuid,text,text)')
    )
    INTO publish_definition;

    IF publish_definition IS NULL
       OR position(
            'exam.current_version_number = current_version_number'
            IN publish_definition
          ) <> 0
       OR position(
            'exam.current_version_number = current_exam_version_number'
            IN publish_definition
          ) = 0 THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_PRE_FIXED_PUBLISH_SEAM_REQUIRED';
    END IF;

    WITH target(signature) AS (
        VALUES
          ('public.apply_assessment_exam_review()'),
          ('public.assemble_assessment_exam_from_blueprint(uuid,text)'),
          ('public.assessment_blueprint_ready_for_review(uuid)'),
          ('public.assessment_blueprint_totals_match(uuid)'),
          ('public.assessment_blueprint_version_is_editable(uuid)'),
          ('public.assessment_blueprint_version_is_visible(uuid)'),
          ('public.assessment_exam_assembly_matches_blueprint(uuid)'),
          ('public.assessment_exam_cell_allocation_matches(uuid,uuid)'),
          ('public.assessment_exam_content_is_publishable(uuid)'),
          ('public.assessment_exam_current_validation_governance(uuid)'),
          ('public.assessment_exam_ready_for_review(uuid)'),
          ('public.assessment_exam_snapshot_hash_matches(uuid)'),
          ('public.assessment_exam_validation_evidence_digest(uuid,integer,text,text,jsonb,jsonb,jsonb)'),
          ('public.assessment_exam_validation_input_digest(uuid)'),
          ('public.assessment_exam_validation_report(uuid)'),
          ('public.assessment_exam_version_is_editable(uuid)'),
          ('public.assessment_exam_version_is_visible(uuid)'),
          ('public.assessment_question_scoring_total_matches(uuid)'),
          ('public.assessment_question_version_is_editable(uuid)'),
          ('public.assessment_question_version_is_visible(uuid)'),
          ('public.assessment_settings_current_user_is_admin()'),
          ('public.bind_assessment_setting_to_blueprint(uuid,uuid)'),
          ('public.build_assessment_blueprint_snapshot_document(uuid)'),
          ('public.build_assessment_exam_snapshot_document(uuid,uuid)'),
          ('public.build_assessment_exam_snapshot_document_v1(uuid,uuid)'),
          ('public.build_assessment_exam_snapshot_document_v2(uuid,uuid)'),
          ('public.build_assessment_exam_validation_input(uuid)'),
          ('public.capture_assessment_exam_publication_snapshot()'),
          ('public.confirm_assessment_exam_validation_warnings(uuid,text,jsonb)'),
          ('public.create_assessment_exam_draft(uuid,text,text,text)'),
          ('public.current_user_is_portal_admin()'),
          ('public.current_user_owns_assessment_question(uuid)'),
          ('public.enforce_assessment_blueprint_cell_consistency()'),
          ('public.enforce_assessment_exam_cell_capacity()'),
          ('public.enforce_assessment_exam_question_alignment()'),
          ('public.enforce_assessment_exam_version_context()'),
          ('public.invalidate_assessment_exam_assembly()'),
          ('public.mark_assessment_exam_assembled(uuid)'),
          ('public.prevent_assessment_exam_governance_history_mutation()'),
          ('public.prevent_assessment_exam_snapshot_mutation()'),
          ('public.publish_assessment_exam(uuid,text,text)'),
          ('public.review_assessment_exam_setting(uuid,text,text)'),
          ('public.save_assessment_exam_setting_draft(text,text,text,text,text,integer,text,text,integer,integer,numeric,text,text,date,jsonb,jsonb,jsonb,jsonb,jsonb,jsonb,jsonb)'),
          ('public.submit_assessment_exam_for_review(uuid)'),
          ('public.submit_assessment_exam_setting_for_review(uuid)'),
          ('public.validate_assessment_question_answer_mode()'),
          ('public.validate_assessment_question_component_type()')
    ),
    resolved AS (
        SELECT
            signature,
            to_regprocedure(signature) AS oid
        FROM target
    )
    SELECT
        count(*),
        count(r.oid),
        count(*) FILTER (WHERE p.prosecdef)
    INTO target_count, resolved_count, secdef_count
    FROM resolved r
    LEFT JOIN pg_proc p ON p.oid = r.oid;

    IF target_count <> 47
       OR resolved_count <> 47
       OR secdef_count <> 47 THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_PRE_TARGET_SET_FAILED targets=% resolved=% secdef=% expected=47/47/47',
          target_count, resolved_count, secdef_count;
    END IF;

    WITH target(signature) AS (
        VALUES
          ('public.apply_assessment_exam_review()'),
          ('public.capture_assessment_exam_publication_snapshot()'),
          ('public.enforce_assessment_blueprint_cell_consistency()'),
          ('public.enforce_assessment_exam_cell_capacity()'),
          ('public.enforce_assessment_exam_question_alignment()'),
          ('public.enforce_assessment_exam_version_context()'),
          ('public.invalidate_assessment_exam_assembly()'),
          ('public.prevent_assessment_exam_governance_history_mutation()'),
          ('public.prevent_assessment_exam_snapshot_mutation()'),
          ('public.validate_assessment_question_answer_mode()'),
          ('public.validate_assessment_question_component_type()')
    ),
    resolved AS (
        SELECT to_regprocedure(signature) AS oid
        FROM target
    )
    SELECT
        count(*),
        count(*) FILTER (WHERE p.prosecdef),
        count(*) FILTER (WHERE p.prorettype = 'trigger'::regtype)
    INTO trigger_count, trigger_secdef_count, trigger_return_count
    FROM resolved r
    JOIN pg_proc p ON p.oid = r.oid;

    IF trigger_count <> 11
       OR trigger_secdef_count <> 11
       OR trigger_return_count <> 11 THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_PRE_TRIGGER_SET_FAILED targets=% secdef=% trigger_returns=% expected=11/11/11',
          trigger_count, trigger_secdef_count, trigger_return_count;
    END IF;

    WITH target(name) AS (
        VALUES
          ('assessment_blueprint_totals_match'),
          ('assessment_exam_assembly_matches_blueprint'),
          ('assessment_exam_cell_allocation_matches'),
          ('mark_assessment_exam_assembled')
    )
    SELECT count(*)
    INTO rls_ref_count
    FROM pg_policy pol
    JOIN pg_class cls ON cls.oid = pol.polrelid
    JOIN pg_namespace ns ON ns.oid = cls.relnamespace
    WHERE ns.nspname = 'public'
      AND EXISTS (
          SELECT 1
          FROM target t
          WHERE coalesce(pg_get_expr(pol.polqual, pol.polrelid), '')
                    ILIKE '%' || t.name || '%'
             OR coalesce(pg_get_expr(pol.polwithcheck, pol.polrelid), '')
                    ILIKE '%' || t.name || '%'
      );

    IF rls_ref_count <> 0 THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_PRE_S1D3_RLS_REFERENCE_FOUND count=%',
          rls_ref_count;
    END IF;

    IF to_regprocedure('public.set_assessment_canonical_updated_at()') IS NULL
       OR to_regprocedure('public.set_assessment_question_updated_at()') IS NULL THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_PRE_UPDATED_AT_FUNCTIONS_REQUIRED';
    END IF;
END
$assessment_security_pre$;

-- S1B equivalent: remove anon direct EXECUTE from the exact audited set.
REVOKE EXECUTE ON FUNCTION public.apply_assessment_exam_review() FROM anon;
REVOKE EXECUTE ON FUNCTION public.assemble_assessment_exam_from_blueprint(uuid,text) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_blueprint_ready_for_review(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_blueprint_totals_match(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_blueprint_version_is_editable(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_blueprint_version_is_visible(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_assembly_matches_blueprint(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_cell_allocation_matches(uuid,uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_content_is_publishable(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_current_validation_governance(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_ready_for_review(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_snapshot_hash_matches(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_validation_evidence_digest(uuid,integer,text,text,jsonb,jsonb,jsonb) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_validation_input_digest(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_validation_report(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_version_is_editable(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_version_is_visible(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_question_scoring_total_matches(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_question_version_is_editable(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_question_version_is_visible(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.assessment_settings_current_user_is_admin() FROM anon;
REVOKE EXECUTE ON FUNCTION public.bind_assessment_setting_to_blueprint(uuid,uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.build_assessment_blueprint_snapshot_document(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.build_assessment_exam_snapshot_document(uuid,uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.build_assessment_exam_snapshot_document_v1(uuid,uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.build_assessment_exam_snapshot_document_v2(uuid,uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.build_assessment_exam_validation_input(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.capture_assessment_exam_publication_snapshot() FROM anon;
REVOKE EXECUTE ON FUNCTION public.confirm_assessment_exam_validation_warnings(uuid,text,jsonb) FROM anon;
REVOKE EXECUTE ON FUNCTION public.create_assessment_exam_draft(uuid,text,text,text) FROM anon;
REVOKE EXECUTE ON FUNCTION public.current_user_is_portal_admin() FROM anon;
REVOKE EXECUTE ON FUNCTION public.current_user_owns_assessment_question(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_blueprint_cell_consistency() FROM anon;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_cell_capacity() FROM anon;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_question_alignment() FROM anon;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_version_context() FROM anon;
REVOKE EXECUTE ON FUNCTION public.invalidate_assessment_exam_assembly() FROM anon;
REVOKE EXECUTE ON FUNCTION public.mark_assessment_exam_assembled(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.prevent_assessment_exam_governance_history_mutation() FROM anon;
REVOKE EXECUTE ON FUNCTION public.prevent_assessment_exam_snapshot_mutation() FROM anon;
REVOKE EXECUTE ON FUNCTION public.publish_assessment_exam(uuid,text,text) FROM anon;
REVOKE EXECUTE ON FUNCTION public.review_assessment_exam_setting(uuid,text,text) FROM anon;
REVOKE EXECUTE ON FUNCTION public.save_assessment_exam_setting_draft(text,text,text,text,text,integer,text,text,integer,integer,numeric,text,text,date,jsonb,jsonb,jsonb,jsonb,jsonb,jsonb,jsonb) FROM anon;
REVOKE EXECUTE ON FUNCTION public.submit_assessment_exam_for_review(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.submit_assessment_exam_setting_for_review(uuid) FROM anon;
REVOKE EXECUTE ON FUNCTION public.validate_assessment_question_answer_mode() FROM anon;
REVOKE EXECUTE ON FUNCTION public.validate_assessment_question_component_type() FROM anon;

-- S1C/S1D1 equivalent: trigger functions are internal trigger entrypoints,
-- not directly callable RPCs.
REVOKE EXECUTE ON FUNCTION public.apply_assessment_exam_review() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.capture_assessment_exam_publication_snapshot() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_blueprint_cell_consistency() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_cell_capacity() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_question_alignment() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_version_context() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.invalidate_assessment_exam_assembly() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.prevent_assessment_exam_governance_history_mutation() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.prevent_assessment_exam_snapshot_mutation() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.validate_assessment_question_answer_mode() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.validate_assessment_question_component_type() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.apply_assessment_exam_review() FROM anon;
REVOKE EXECUTE ON FUNCTION public.capture_assessment_exam_publication_snapshot() FROM anon;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_blueprint_cell_consistency() FROM anon;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_cell_capacity() FROM anon;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_question_alignment() FROM anon;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_version_context() FROM anon;
REVOKE EXECUTE ON FUNCTION public.invalidate_assessment_exam_assembly() FROM anon;
REVOKE EXECUTE ON FUNCTION public.prevent_assessment_exam_governance_history_mutation() FROM anon;
REVOKE EXECUTE ON FUNCTION public.prevent_assessment_exam_snapshot_mutation() FROM anon;
REVOKE EXECUTE ON FUNCTION public.validate_assessment_question_answer_mode() FROM anon;
REVOKE EXECUTE ON FUNCTION public.validate_assessment_question_component_type() FROM anon;
REVOKE EXECUTE ON FUNCTION public.apply_assessment_exam_review() FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.capture_assessment_exam_publication_snapshot() FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_blueprint_cell_consistency() FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_cell_capacity() FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_question_alignment() FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.enforce_assessment_exam_version_context() FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.invalidate_assessment_exam_assembly() FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.prevent_assessment_exam_governance_history_mutation() FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.prevent_assessment_exam_snapshot_mutation() FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.validate_assessment_question_answer_mode() FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.validate_assessment_question_component_type() FROM authenticated;

-- S1D1 search_path hardening without changing function bodies.
ALTER FUNCTION public.set_assessment_canonical_updated_at()
    SET search_path = pg_catalog, public;

ALTER FUNCTION public.set_assessment_question_updated_at()
    SET search_path = pg_catalog, public;

-- Proven seven internal helper revokes.
REVOKE EXECUTE ON FUNCTION public.assessment_exam_validation_evidence_digest(uuid,integer,text,text,jsonb,jsonb,jsonb) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_validation_input_digest(uuid) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.build_assessment_blueprint_snapshot_document(uuid) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.build_assessment_exam_snapshot_document_v1(uuid,uuid) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.build_assessment_exam_snapshot_document_v2(uuid,uuid) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.build_assessment_exam_snapshot_document(uuid,uuid) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.build_assessment_exam_validation_input(uuid) FROM authenticated;

-- Proven four remaining internal helper revokes.
REVOKE EXECUTE ON FUNCTION public.assessment_blueprint_totals_match(uuid) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_assembly_matches_blueprint(uuid) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.assessment_exam_cell_allocation_matches(uuid,uuid) FROM authenticated;
REVOKE EXECUTE ON FUNCTION public.mark_assessment_exam_assembled(uuid) FROM authenticated;

DO $assessment_security_post$
DECLARE
    target_count integer;
    resolved_count integer;
    anon_effective_count integer;
    trigger_auth_count integer;
    trigger_anon_count integer;
    trigger_public_count integer;
    helper_auth_count integer;
    helper_anon_count integer;
    helper_public_count integer;
    path_exact_count integer;
    publish_definition text;
BEGIN
    WITH target(signature) AS (
        VALUES
          ('public.apply_assessment_exam_review()'),
          ('public.assemble_assessment_exam_from_blueprint(uuid,text)'),
          ('public.assessment_blueprint_ready_for_review(uuid)'),
          ('public.assessment_blueprint_totals_match(uuid)'),
          ('public.assessment_blueprint_version_is_editable(uuid)'),
          ('public.assessment_blueprint_version_is_visible(uuid)'),
          ('public.assessment_exam_assembly_matches_blueprint(uuid)'),
          ('public.assessment_exam_cell_allocation_matches(uuid,uuid)'),
          ('public.assessment_exam_content_is_publishable(uuid)'),
          ('public.assessment_exam_current_validation_governance(uuid)'),
          ('public.assessment_exam_ready_for_review(uuid)'),
          ('public.assessment_exam_snapshot_hash_matches(uuid)'),
          ('public.assessment_exam_validation_evidence_digest(uuid,integer,text,text,jsonb,jsonb,jsonb)'),
          ('public.assessment_exam_validation_input_digest(uuid)'),
          ('public.assessment_exam_validation_report(uuid)'),
          ('public.assessment_exam_version_is_editable(uuid)'),
          ('public.assessment_exam_version_is_visible(uuid)'),
          ('public.assessment_question_scoring_total_matches(uuid)'),
          ('public.assessment_question_version_is_editable(uuid)'),
          ('public.assessment_question_version_is_visible(uuid)'),
          ('public.assessment_settings_current_user_is_admin()'),
          ('public.bind_assessment_setting_to_blueprint(uuid,uuid)'),
          ('public.build_assessment_blueprint_snapshot_document(uuid)'),
          ('public.build_assessment_exam_snapshot_document(uuid,uuid)'),
          ('public.build_assessment_exam_snapshot_document_v1(uuid,uuid)'),
          ('public.build_assessment_exam_snapshot_document_v2(uuid,uuid)'),
          ('public.build_assessment_exam_validation_input(uuid)'),
          ('public.capture_assessment_exam_publication_snapshot()'),
          ('public.confirm_assessment_exam_validation_warnings(uuid,text,jsonb)'),
          ('public.create_assessment_exam_draft(uuid,text,text,text)'),
          ('public.current_user_is_portal_admin()'),
          ('public.current_user_owns_assessment_question(uuid)'),
          ('public.enforce_assessment_blueprint_cell_consistency()'),
          ('public.enforce_assessment_exam_cell_capacity()'),
          ('public.enforce_assessment_exam_question_alignment()'),
          ('public.enforce_assessment_exam_version_context()'),
          ('public.invalidate_assessment_exam_assembly()'),
          ('public.mark_assessment_exam_assembled(uuid)'),
          ('public.prevent_assessment_exam_governance_history_mutation()'),
          ('public.prevent_assessment_exam_snapshot_mutation()'),
          ('public.publish_assessment_exam(uuid,text,text)'),
          ('public.review_assessment_exam_setting(uuid,text,text)'),
          ('public.save_assessment_exam_setting_draft(text,text,text,text,text,integer,text,text,integer,integer,numeric,text,text,date,jsonb,jsonb,jsonb,jsonb,jsonb,jsonb,jsonb)'),
          ('public.submit_assessment_exam_for_review(uuid)'),
          ('public.submit_assessment_exam_setting_for_review(uuid)'),
          ('public.validate_assessment_question_answer_mode()'),
          ('public.validate_assessment_question_component_type()')
    ),
    resolved AS (
        SELECT
            signature,
            to_regprocedure(signature) AS oid
        FROM target
    )
    SELECT
        count(*),
        count(r.oid),
        count(*) FILTER (
            WHERE has_function_privilege('anon', r.oid, 'EXECUTE')
        )
    INTO target_count, resolved_count, anon_effective_count
    FROM resolved r;

    IF target_count <> 47
       OR resolved_count <> 47
       OR anon_effective_count <> 0 THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_POST_ANON_FAILED targets=% resolved=% anon=% expected=47/47/0',
          target_count, resolved_count, anon_effective_count;
    END IF;

    WITH target(signature) AS (
        VALUES
          ('public.apply_assessment_exam_review()'),
          ('public.capture_assessment_exam_publication_snapshot()'),
          ('public.enforce_assessment_blueprint_cell_consistency()'),
          ('public.enforce_assessment_exam_cell_capacity()'),
          ('public.enforce_assessment_exam_question_alignment()'),
          ('public.enforce_assessment_exam_version_context()'),
          ('public.invalidate_assessment_exam_assembly()'),
          ('public.prevent_assessment_exam_governance_history_mutation()'),
          ('public.prevent_assessment_exam_snapshot_mutation()'),
          ('public.validate_assessment_question_answer_mode()'),
          ('public.validate_assessment_question_component_type()')
    ),
    resolved AS (
        SELECT to_regprocedure(signature) AS oid
        FROM target
    )
    SELECT
        count(*) FILTER (
            WHERE has_function_privilege('authenticated', oid, 'EXECUTE')
        ),
        count(*) FILTER (
            WHERE has_function_privilege('anon', oid, 'EXECUTE')
        ),
        count(*) FILTER (
            WHERE has_function_privilege('public', oid, 'EXECUTE')
        )
    INTO trigger_auth_count, trigger_anon_count, trigger_public_count
    FROM resolved;

    IF trigger_auth_count <> 0
       OR trigger_anon_count <> 0
       OR trigger_public_count <> 0 THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_POST_TRIGGER_ACL_FAILED auth=% anon=% public=% expected=0/0/0',
          trigger_auth_count, trigger_anon_count, trigger_public_count;
    END IF;

    WITH target(signature) AS (
        VALUES
          ('public.assessment_exam_validation_evidence_digest(uuid,integer,text,text,jsonb,jsonb,jsonb)'),
          ('public.assessment_exam_validation_input_digest(uuid)'),
          ('public.build_assessment_blueprint_snapshot_document(uuid)'),
          ('public.build_assessment_exam_snapshot_document_v1(uuid,uuid)'),
          ('public.build_assessment_exam_snapshot_document_v2(uuid,uuid)'),
          ('public.build_assessment_exam_snapshot_document(uuid,uuid)'),
          ('public.build_assessment_exam_validation_input(uuid)'),
          ('public.assessment_blueprint_totals_match(uuid)'),
          ('public.assessment_exam_assembly_matches_blueprint(uuid)'),
          ('public.assessment_exam_cell_allocation_matches(uuid,uuid)'),
          ('public.mark_assessment_exam_assembled(uuid)')
    ),
    resolved AS (
        SELECT to_regprocedure(signature) AS oid
        FROM target
    )
    SELECT
        count(*) FILTER (
            WHERE has_function_privilege('authenticated', oid, 'EXECUTE')
        ),
        count(*) FILTER (
            WHERE has_function_privilege('anon', oid, 'EXECUTE')
        ),
        count(*) FILTER (
            WHERE has_function_privilege('public', oid, 'EXECUTE')
        )
    INTO helper_auth_count, helper_anon_count, helper_public_count
    FROM resolved;

    IF helper_auth_count <> 0
       OR helper_anon_count <> 0
       OR helper_public_count <> 0 THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_POST_INTERNAL_HELPER_ACL_FAILED auth=% anon=% public=% expected=0/0/0',
          helper_auth_count, helper_anon_count, helper_public_count;
    END IF;

    SELECT count(*)
    INTO path_exact_count
    FROM pg_proc p
    JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.proname IN (
          'set_assessment_canonical_updated_at',
          'set_assessment_question_updated_at'
      )
      AND p.prorettype = 'trigger'::regtype
      AND EXISTS (
          SELECT 1
          FROM unnest(coalesce(p.proconfig, ARRAY[]::text[])) cfg
          WHERE replace(cfg, ' ', '') =
                'search_path=pg_catalog,public'
      );

    IF path_exact_count <> 2 THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_POST_SEARCH_PATH_FAILED count=% expected=2',
          path_exact_count;
    END IF;

    SELECT pg_get_functiondef(
        to_regprocedure('public.publish_assessment_exam(uuid,text,text)')
    )
    INTO publish_definition;

    IF position(
           'exam.current_version_number = current_version_number'
           IN publish_definition
       ) <> 0
       OR position(
           'exam.current_version_number = current_exam_version_number'
           IN publish_definition
       ) = 0 THEN
        RAISE EXCEPTION
          'ASSESSMENT_SECURITY_POST_PUBLISH_SEAM_DRIFT';
    END IF;
END
$assessment_security_post$;

COMMIT;
