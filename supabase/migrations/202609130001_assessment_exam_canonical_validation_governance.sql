begin;

create table public.assessment_exam_validation_evidence (
    validation_evidence_id uuid primary key default gen_random_uuid(),
    exam_version_id uuid not null
        references public.assessment_exam_versions(exam_version_id)
        on delete restrict,
    validation_revision bigint not null,
    validation_status text not null,
    errors jsonb not null,
    warnings jsonb not null,
    metrics jsonb not null,
    validation_input_digest text not null,
    evidence_digest text not null,
    validated_at timestamptz not null default now(),
    validation_schema_version integer not null,

    unique (exam_version_id, validation_revision),
    check (validation_revision > 0),
    check (validation_schema_version > 0),
    check (validation_status in ('PASS', 'WARNING', 'FAIL')),
    check (jsonb_typeof(errors) = 'array'),
    check (jsonb_typeof(warnings) = 'array'),
    check (jsonb_typeof(metrics) = 'object'),
    check (validation_input_digest ~ '^[0-9a-f]{64}$'),
    check (evidence_digest ~ '^[0-9a-f]{64}$'),
    check (
        (validation_status = 'PASS'
            and errors = '[]'::jsonb
            and warnings = '[]'::jsonb)
        or (validation_status = 'WARNING'
            and errors = '[]'::jsonb
            and jsonb_array_length(warnings) > 0)
        or (validation_status = 'FAIL'
            and jsonb_array_length(errors) > 0)
    )
);

create index assessment_exam_validation_evidence_latest_idx
on public.assessment_exam_validation_evidence (
    exam_version_id,
    validation_revision desc
);

create table public.assessment_exam_warning_confirmations (
    warning_confirmation_id uuid primary key default gen_random_uuid(),
    exam_version_id uuid not null
        references public.assessment_exam_versions(exam_version_id)
        on delete restrict,
    validation_evidence_id uuid not null
        references public.assessment_exam_validation_evidence(
            validation_evidence_id
        )
        on delete restrict,
    owner_user_id uuid not null
        references auth.users(id)
        on delete restrict,
    validation_evidence_digest text not null,
    confirmed_warnings jsonb not null,
    confirmed_at timestamptz not null default now(),

    unique (validation_evidence_id, owner_user_id),
    check (validation_evidence_digest ~ '^[0-9a-f]{64}$'),
    check (jsonb_typeof(confirmed_warnings) = 'array')
);

alter table public.assessment_exam_reviews
    add column validation_evidence_id uuid null
        references public.assessment_exam_validation_evidence(
            validation_evidence_id
        )
        on delete restrict,
    add column validation_evidence_digest text null
        check (
            validation_evidence_digest is null
            or validation_evidence_digest ~ '^[0-9a-f]{64}$'
        ),
    add column warning_acknowledged boolean null;

create or replace function
public.prevent_assessment_exam_governance_history_mutation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    raise exception
        'Assessment exam governance history is append-only.';
end;
$$;

revoke all on function
public.prevent_assessment_exam_governance_history_mutation()
from public;

create trigger assessment_exam_validation_evidence_append_only
before update or delete
on public.assessment_exam_validation_evidence
for each row
execute function
public.prevent_assessment_exam_governance_history_mutation();

create trigger assessment_exam_warning_confirmations_append_only
before update or delete
on public.assessment_exam_warning_confirmations
for each row
execute function
public.prevent_assessment_exam_governance_history_mutation();

create trigger assessment_exam_reviews_append_only
before update or delete
on public.assessment_exam_reviews
for each row
execute function
public.prevent_assessment_exam_governance_history_mutation();

create or replace function
public.build_assessment_exam_validation_input(
    target_exam_version_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
    select jsonb_build_object(
        'exam_version_id', exam_version.exam_version_id,
        'total_score', exam_version.total_score,
        'setting_version_id', exam_version.setting_version_id,
        'setting_snapshot', exam_version.setting_snapshot,
        'blueprint_version_id', exam_version.blueprint_version_id,
        'blueprint_cells', coalesce(
            (
                select jsonb_agg(
                    jsonb_build_object(
                        'blueprint_cell_id', cell.blueprint_cell_id,
                        'question_count', cell.question_count,
                        'target_score', cell.target_score
                    )
                    order by
                        cell.sequence_number,
                        cell.blueprint_cell_id
                )
                from public.assessment_blueprint_cells cell
                where cell.blueprint_version_id =
                    exam_version.blueprint_version_id
            ),
            '[]'::jsonb
        ),
        'exam_questions', coalesce(
            (
                select jsonb_agg(
                    jsonb_build_object(
                        'exam_question_id', assignment.exam_question_id,
                        'blueprint_cell_id', assignment.blueprint_cell_id,
                        'question_version_id', assignment.question_version_id,
                        'assigned_score', assignment.assigned_score,
                        'display_number', assignment.display_number
                    )
                    order by
                        assignment.display_number,
                        assignment.exam_question_id
                )
                from public.assessment_exam_questions assignment
                where assignment.exam_version_id =
                    exam_version.exam_version_id
            ),
            '[]'::jsonb
        )
    )
    from public.assessment_exam_versions exam_version
    where exam_version.exam_version_id = target_exam_version_id;
$$;

revoke all on function
public.build_assessment_exam_validation_input(uuid)
from public;

create or replace function
public.assessment_exam_validation_input_digest(
    target_exam_version_id uuid
)
returns text
language sql
stable
security definer
set search_path = ''
as $$
    select encode(
        extensions.digest(
            public.build_assessment_exam_validation_input(
                target_exam_version_id
            )::text,
            'sha256'
        ),
        'hex'
    );
$$;

revoke all on function
public.assessment_exam_validation_input_digest(uuid)
from public;

create or replace function
public.assessment_exam_validation_evidence_digest(
    target_exam_version_id uuid,
    target_validation_schema_version integer,
    target_validation_input_digest text,
    target_validation_status text,
    target_errors jsonb,
    target_warnings jsonb,
    target_metrics jsonb
)
returns text
language sql
immutable
security definer
set search_path = ''
as $$
    select encode(
        extensions.digest(
            jsonb_build_object(
                'exam_version_id', target_exam_version_id,
                'validation_schema_version',
                    target_validation_schema_version,
                'validation_input_digest',
                    target_validation_input_digest,
                'validation_status', target_validation_status,
                'errors', target_errors,
                'warnings', target_warnings,
                'metrics', target_metrics
            )::text,
            'sha256'
        ),
        'hex'
    );
$$;

revoke all on function
public.assessment_exam_validation_evidence_digest(
    uuid,
    integer,
    text,
    text,
    jsonb,
    jsonb,
    jsonb
)
from public;

create or replace function
public.assessment_exam_validation_report(
    target_exam_version_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_user_id uuid := (select auth.uid());
    current_owner_user_id uuid;
    current_blueprint_version_id uuid;
    question_count_value integer;
    expected_question_count integer;
    assigned_score_value numeric(10,4);
    expected_score_value numeric(10,4);
    matched_cell_count integer;
    expected_cell_count integer;
    assembly_matches boolean;
    errors_value jsonb;
    warnings_value jsonb := '[]'::jsonb;
    metrics_value jsonb;
    status_value text;
    input_digest_value text;
    evidence_digest_value text;
    schema_version_value integer := 1;
    evidence_row public.assessment_exam_validation_evidence%rowtype;
begin
    select
        exam.owner_user_id,
        exam_version.blueprint_version_id,
        exam_version.total_score
    into
        current_owner_user_id,
        current_blueprint_version_id,
        expected_score_value
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where exam_version.exam_version_id = target_exam_version_id
    for update of exam_version;

    if current_owner_user_id is null then
        raise exception 'Assessment exam version does not exist.';
    end if;

    if (
        current_owner_user_id is distinct from current_user_id
        and not public.current_user_is_portal_admin()
    ) then
        raise exception
            'Assessment exam validation report is not visible.';
    end if;

    perform 1
    from public.assessment_exam_questions assignment
    where assignment.exam_version_id = target_exam_version_id
    order by assignment.display_number
    for update;

    input_digest_value :=
        public.assessment_exam_validation_input_digest(
            target_exam_version_id
        );

    select
        count(*)::integer,
        coalesce(sum(cell.question_count), 0)::integer
    into expected_cell_count, expected_question_count
    from public.assessment_blueprint_cells cell
    where cell.blueprint_version_id = current_blueprint_version_id;

    select
        count(*)::integer,
        coalesce(sum(exam_question.assigned_score), 0)
    into question_count_value, assigned_score_value
    from public.assessment_exam_questions exam_question
    where exam_question.exam_version_id = target_exam_version_id;

    select count(*)::integer
    into matched_cell_count
    from public.assessment_blueprint_cells cell
    where
        cell.blueprint_version_id = current_blueprint_version_id
        and public.assessment_exam_cell_allocation_matches(
            target_exam_version_id,
            cell.blueprint_cell_id
        );

    assembly_matches :=
        public.assessment_exam_assembly_matches_blueprint(
            target_exam_version_id
        );

    errors_value := case
        when assembly_matches then '[]'::jsonb
        else jsonb_build_array(
            'Assessment exam does not completely match its blueprint.'
        )
    end;

    -- WARNING_EXTENSION_SEAM: no authoritative production warning rule
    -- exists. This producer intentionally emits PASS or FAIL only.
    status_value := case
        when assembly_matches then 'PASS'
        else 'FAIL'
    end;

    metrics_value := jsonb_build_object(
        'question_count', question_count_value,
        'expected_question_count', expected_question_count,
        'assigned_score', assigned_score_value,
        'expected_score', expected_score_value,
        'matched_cell_count', matched_cell_count,
        'expected_cell_count', expected_cell_count
    );

    evidence_digest_value :=
        public.assessment_exam_validation_evidence_digest(
            target_exam_version_id,
            schema_version_value,
            input_digest_value,
            status_value,
            errors_value,
            warnings_value,
            metrics_value
        );

    select evidence.*
    into evidence_row
    from public.assessment_exam_validation_evidence evidence
    where evidence.exam_version_id = target_exam_version_id
    order by evidence.validation_revision desc
    limit 1;

    if evidence_row.validation_evidence_id is null
       or evidence_row.validation_input_digest
            is distinct from input_digest_value
       or evidence_row.validation_status is distinct from status_value
       or evidence_row.errors is distinct from errors_value
       or evidence_row.warnings is distinct from warnings_value
       or evidence_row.metrics is distinct from metrics_value
       or evidence_row.evidence_digest
            is distinct from evidence_digest_value then
        insert into public.assessment_exam_validation_evidence (
            exam_version_id,
            validation_revision,
            validation_status,
            errors,
            warnings,
            metrics,
            validation_input_digest,
            evidence_digest,
            validation_schema_version
        ) values (
            target_exam_version_id,
            coalesce(evidence_row.validation_revision, 0) + 1,
            status_value,
            errors_value,
            warnings_value,
            metrics_value,
            input_digest_value,
            evidence_digest_value,
            schema_version_value
        )
        returning * into evidence_row;
    end if;

    return jsonb_build_object(
        'is_valid', evidence_row.validation_status = 'PASS',
        'violations', evidence_row.errors,
        'status', evidence_row.validation_status,
        'errors', evidence_row.errors,
        'warnings', evidence_row.warnings,
        'metrics', evidence_row.metrics,
        'validation_evidence_id', evidence_row.validation_evidence_id,
        'validation_revision', evidence_row.validation_revision,
        'validation_input_digest',
            evidence_row.validation_input_digest,
        'evidence_digest', evidence_row.evidence_digest,
        'validation_schema_version',
            evidence_row.validation_schema_version,
        'validated_at', evidence_row.validated_at
    );
end;
$$;

revoke all on function
public.assessment_exam_validation_report(uuid)
from public;

grant execute on function
public.assessment_exam_validation_report(uuid)
to authenticated;

create or replace function
public.confirm_assessment_exam_validation_warnings(
    target_exam_version_id uuid,
    target_validation_evidence_digest text,
    target_confirmed_warnings jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_user_id uuid := (select auth.uid());
    current_owner_user_id uuid;
    current_input_digest text;
    evidence_row public.assessment_exam_validation_evidence%rowtype;
    confirmation_row
        public.assessment_exam_warning_confirmations%rowtype;
begin
    if current_user_id is null then
        raise exception 'AUTHENTICATION_REQUIRED';
    end if;

    select exam.owner_user_id
    into current_owner_user_id
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where exam_version.exam_version_id = target_exam_version_id
    for update of exam_version;

    if current_owner_user_id is null then
        raise exception 'ASSESSMENT_EXAM_VERSION_NOT_FOUND';
    end if;
    if current_owner_user_id is distinct from current_user_id then
        raise exception 'ASSESSMENT_EXAM_OWNER_REQUIRED';
    end if;

    perform 1
    from public.assessment_exam_questions assignment
    where assignment.exam_version_id = target_exam_version_id
    order by assignment.display_number
    for update;

    current_input_digest :=
        public.assessment_exam_validation_input_digest(
            target_exam_version_id
        );

    select evidence.*
    into evidence_row
    from public.assessment_exam_validation_evidence evidence
    where evidence.exam_version_id = target_exam_version_id
    order by evidence.validation_revision desc
    limit 1;

    if evidence_row.validation_evidence_id is null then
        raise exception 'CANONICAL_VALIDATION_EVIDENCE_REQUIRED';
    end if;
    if evidence_row.validation_input_digest
        is distinct from current_input_digest then
        raise exception 'STALE_CANONICAL_VALIDATION_EVIDENCE';
    end if;
    if evidence_row.validation_status = 'PASS' then
        raise exception 'PASS_HAS_NO_WARNINGS_TO_CONFIRM';
    end if;
    if evidence_row.validation_status = 'FAIL' then
        raise exception 'FAIL_VALIDATION_CANNOT_BE_OVERRIDDEN';
    end if;
    if evidence_row.validation_status is distinct from 'WARNING' then
        raise exception 'UNSUPPORTED_VALIDATION_STATUS';
    end if;
    if evidence_row.evidence_digest
        is distinct from target_validation_evidence_digest then
        raise exception 'VALIDATION_EVIDENCE_DIGEST_MISMATCH';
    end if;
    if jsonb_typeof(target_confirmed_warnings) is distinct from 'array'
       or target_confirmed_warnings is distinct from evidence_row.warnings
    then
        raise exception 'CONFIRMED_WARNINGS_MUST_MATCH_CANONICAL_ORDER';
    end if;

    select confirmation.*
    into confirmation_row
    from public.assessment_exam_warning_confirmations confirmation
    where
        confirmation.validation_evidence_id =
            evidence_row.validation_evidence_id
        and confirmation.owner_user_id = current_user_id;

    if confirmation_row.warning_confirmation_id is null then
        insert into public.assessment_exam_warning_confirmations (
            exam_version_id,
            validation_evidence_id,
            owner_user_id,
            validation_evidence_digest,
            confirmed_warnings
        ) values (
            target_exam_version_id,
            evidence_row.validation_evidence_id,
            current_user_id,
            evidence_row.evidence_digest,
            evidence_row.warnings
        )
        returning * into confirmation_row;
    elsif confirmation_row.exam_version_id
            is distinct from target_exam_version_id
       or confirmation_row.validation_evidence_digest
            is distinct from evidence_row.evidence_digest
       or confirmation_row.confirmed_warnings
            is distinct from evidence_row.warnings then
        raise exception 'WARNING_CONFIRMATION_CONFLICT';
    end if;

    return jsonb_build_object(
        'warning_confirmation_id',
            confirmation_row.warning_confirmation_id,
        'exam_version_id', confirmation_row.exam_version_id,
        'validation_evidence_id',
            confirmation_row.validation_evidence_id,
        'owner_user_id', confirmation_row.owner_user_id,
        'validation_evidence_digest',
            confirmation_row.validation_evidence_digest,
        'confirmed_warnings', confirmation_row.confirmed_warnings,
        'confirmed_at', confirmation_row.confirmed_at,
        'validation_status', evidence_row.validation_status
    );
end;
$$;

revoke all on function
public.confirm_assessment_exam_validation_warnings(uuid, text, jsonb)
from public;

grant execute on function
public.confirm_assessment_exam_validation_warnings(uuid, text, jsonb)
to authenticated;

create or replace function
public.assessment_exam_current_validation_governance(
    target_exam_version_id uuid
)
returns table (
    validation_evidence_id uuid,
    validation_status text,
    validation_evidence_digest text,
    warning_confirmation_id uuid
)
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
    current_owner_user_id uuid;
    current_input_digest text;
    evidence_row public.assessment_exam_validation_evidence%rowtype;
begin
    select exam.owner_user_id
    into current_owner_user_id
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where exam_version.exam_version_id = target_exam_version_id;

    if current_owner_user_id is null then
        raise exception 'ASSESSMENT_EXAM_VERSION_NOT_FOUND';
    end if;

    current_input_digest :=
        public.assessment_exam_validation_input_digest(
            target_exam_version_id
        );

    select evidence.*
    into evidence_row
    from public.assessment_exam_validation_evidence evidence
    where evidence.exam_version_id = target_exam_version_id
    order by evidence.validation_revision desc
    limit 1;

    if evidence_row.validation_evidence_id is null then
        raise exception 'CANONICAL_VALIDATION_EVIDENCE_REQUIRED';
    end if;
    if evidence_row.validation_input_digest
        is distinct from current_input_digest then
        raise exception 'STALE_CANONICAL_VALIDATION_EVIDENCE';
    end if;
    if evidence_row.validation_status = 'FAIL' then
        raise exception 'FAIL_VALIDATION_CANNOT_BE_OVERRIDDEN';
    end if;
    if evidence_row.validation_status = 'PASS' then
        return query select
            evidence_row.validation_evidence_id,
            evidence_row.validation_status,
            evidence_row.evidence_digest,
            null::uuid;
        return;
    end if;
    if evidence_row.validation_status is distinct from 'WARNING' then
        raise exception 'UNSUPPORTED_VALIDATION_STATUS';
    end if;

    return query
    select
        evidence_row.validation_evidence_id,
        evidence_row.validation_status,
        evidence_row.evidence_digest,
        confirmation.warning_confirmation_id
    from public.assessment_exam_warning_confirmations confirmation
    where
        confirmation.exam_version_id = target_exam_version_id
        and confirmation.validation_evidence_id =
            evidence_row.validation_evidence_id
        and confirmation.owner_user_id = current_owner_user_id
        and confirmation.validation_evidence_digest =
            evidence_row.evidence_digest
        and confirmation.confirmed_warnings = evidence_row.warnings;

    if not found then
        raise exception 'CURRENT_WARNING_CONFIRMATION_REQUIRED';
    end if;
end;
$$;

revoke all on function
public.assessment_exam_current_validation_governance(uuid)
from public;

create or replace function
public.submit_assessment_exam_for_review(
    target_exam_version_id uuid
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_owner_user_id uuid;
    current_status text;
    governance_row record;
begin
    select
        exam.owner_user_id,
        exam_version.assembly_status
    into current_owner_user_id, current_status
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where exam_version.exam_version_id = target_exam_version_id
    for update of exam_version;

    if current_owner_user_id is null then
        raise exception 'Assessment exam version does not exist.';
    end if;
    if current_owner_user_id is distinct from (select auth.uid()) then
        raise exception
            'Only the exam owner may submit it for review.';
    end if;
    if current_status not in ('ASSEMBLED', 'PENDING_REVIEW') then
        raise exception
            'Only an assembled exam may be submitted for review.';
    end if;

    perform 1
    from public.assessment_exam_questions assignment
    where assignment.exam_version_id = target_exam_version_id
    order by assignment.display_number
    for update;

    -- CANONICAL_EVIDENCE_GATE_SUBMIT: rejects missing, stale, and FAIL;
    -- WARNING requires the exact current owner confirmation.
    select * into governance_row
    from public.assessment_exam_current_validation_governance(
        target_exam_version_id
    );

    if governance_row.validation_evidence_id is null then
        raise exception 'CURRENT_VALIDATION_GOVERNANCE_REQUIRED';
    end if;
    if not public.assessment_exam_ready_for_review(
        target_exam_version_id
    ) then
        raise exception 'Assessment exam is not ready for review.';
    end if;
    if not public.assessment_exam_content_is_publishable(
        target_exam_version_id
    ) then
        raise exception
            'Assessment exam contains unavailable content.';
    end if;

    if current_status = 'PENDING_REVIEW' then
        return;
    end if;

    update public.assessment_exam_versions
    set assembly_status = 'PENDING_REVIEW', updated_at = now()
    where exam_version_id = target_exam_version_id;
end;
$$;

revoke all on function
public.submit_assessment_exam_for_review(uuid)
from public;

grant execute on function
public.submit_assessment_exam_for_review(uuid)
to authenticated;

create or replace function
public.apply_assessment_exam_review()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_status text;
    approved_version_number integer;
    current_exam_id uuid;
    current_owner_user_id uuid;
    governance_row record;
begin
    if not public.current_user_is_portal_admin() then
        raise exception
            'Only a portal administrator may review an exam.';
    end if;
    if new.reviewer_user_id is distinct from (select auth.uid()) then
        raise exception 'Reviewer must match the authenticated user.';
    end if;

    select
        exam_version.assembly_status,
        exam_version.version_number,
        exam_version.exam_id,
        exam.owner_user_id
    into
        current_status,
        approved_version_number,
        current_exam_id,
        current_owner_user_id
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where exam_version.exam_version_id = new.exam_version_id
    for update of exam_version, exam;

    if current_status is null then
        raise exception 'Assessment exam version does not exist.';
    end if;
    if current_owner_user_id = (select auth.uid()) then
        raise exception 'A reviewer may not review their own exam.';
    end if;
    if current_status is distinct from 'PENDING_REVIEW' then
        raise exception
            'Only a pending exam version may be reviewed.';
    end if;

    perform 1
    from public.assessment_exam_questions assignment
    where assignment.exam_version_id = new.exam_version_id
    order by assignment.display_number
    for update;

    if new.decision = 'APPROVED' then
        -- CANONICAL_EVIDENCE_GATE_REVIEW: helper rejects missing,
        -- stale, FAIL, and unconfirmed WARNING evidence.
        select * into governance_row
        from public.assessment_exam_current_validation_governance(
            new.exam_version_id
        );

        if new.validation_evidence_id is distinct from
                governance_row.validation_evidence_id
           or new.validation_evidence_digest is distinct from
                governance_row.validation_evidence_digest then
            raise exception 'REVIEW_VALIDATION_EVIDENCE_MISMATCH';
        end if;

        if governance_row.validation_status = 'WARNING' then
            if governance_row.warning_confirmation_id is null
               or new.warning_acknowledged is distinct from true then
                raise exception
                    'WARNING_REVIEW_ACKNOWLEDGEMENT_REQUIRED';
            end if;
        elsif governance_row.validation_status = 'PASS' then
            if coalesce(new.warning_acknowledged, false) then
                raise exception
                    'PASS_REVIEW_CANNOT_ACKNOWLEDGE_WARNINGS';
            end if;
            new.warning_acknowledged := false;
        else
            raise exception 'FAIL_VALIDATION_CANNOT_BE_OVERRIDDEN';
        end if;

        if not public.assessment_exam_ready_for_review(
            new.exam_version_id
        ) then
            raise exception
                'Assessment exam no longer matches its blueprint.';
        end if;
        if not public.assessment_exam_content_is_publishable(
            new.exam_version_id
        ) then
            raise exception
                'Assessment exam contains unavailable content.';
        end if;

        update public.assessment_exam_versions
        set
            assembly_status = 'APPROVED',
            locked_at = now(),
            updated_at = now()
        where exam_version_id = new.exam_version_id;

        update public.assessment_exams
        set
            current_version_number = approved_version_number,
            lifecycle_status = 'ACTIVE',
            updated_at = now()
        where exam_id = current_exam_id;
    elsif new.decision = 'REVISION_REQUIRED' then
        if new.validation_evidence_id is not null
           or new.validation_evidence_digest is not null
           or coalesce(new.warning_acknowledged, false) then
            raise exception
                'NON_APPROVAL_REVIEW_CANNOT_CLAIM_VALIDATION';
        end if;
        new.warning_acknowledged := false;
        update public.assessment_exam_versions
        set
            assembly_status = 'REVISION_REQUIRED',
            locked_at = null,
            updated_at = now()
        where exam_version_id = new.exam_version_id;
    elsif new.decision = 'REJECTED' then
        if new.validation_evidence_id is not null
           or new.validation_evidence_digest is not null
           or coalesce(new.warning_acknowledged, false) then
            raise exception
                'NON_APPROVAL_REVIEW_CANNOT_CLAIM_VALIDATION';
        end if;
        new.warning_acknowledged := false;
        update public.assessment_exam_versions
        set
            assembly_status = 'REJECTED',
            locked_at = now(),
            updated_at = now()
        where exam_version_id = new.exam_version_id;
    else
        raise exception
            'Unsupported assessment exam review decision.';
    end if;

    new.reviewed_at := now();
    return new;
end;
$$;

revoke all on function
public.apply_assessment_exam_review()
from public;

create or replace function
public.publish_assessment_exam(
    target_exam_version_id uuid,
    target_publication_channel text default 'INTERNAL',
    target_publication_note text default ''
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_exam_id uuid;
    current_version_number integer;
    current_owner_user_id uuid;
    current_status text;
    new_publication_id uuid;
    governance_row record;
    approved_review_id uuid;
begin
    select
        exam_version.exam_id,
        exam_version.version_number,
        exam.owner_user_id,
        exam_version.assembly_status
    into
        current_exam_id,
        current_version_number,
        current_owner_user_id,
        current_status
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where exam_version.exam_version_id = target_exam_version_id
    for update of exam_version, exam;

    if current_exam_id is null then
        raise exception 'Assessment exam version does not exist.';
    end if;
    if current_owner_user_id is distinct from (select auth.uid()) then
        raise exception 'Only the exam owner may publish it.';
    end if;
    if current_status is distinct from 'APPROVED' then
        raise exception 'Only an approved exam may be published.';
    end if;
    if not exists (
        select 1
        from public.assessment_exams exam
        where exam.exam_id = current_exam_id
          and exam.current_version_number = current_version_number
    ) then
        raise exception
            'Only the current approved exam version may be published.';
    end if;
    if target_publication_channel not in (
        'INTERNAL', 'PRINT', 'DIGITAL', 'EXPORT'
    ) then
        raise exception 'Unsupported assessment publication channel.';
    end if;

    perform 1
    from public.assessment_exam_questions assignment
    where assignment.exam_version_id = target_exam_version_id
    order by assignment.display_number
    for update;

    -- CANONICAL_EVIDENCE_GATE_PUBLICATION: rejects missing, stale,
    -- FAIL, and unconfirmed WARNING evidence.
    select * into governance_row
    from public.assessment_exam_current_validation_governance(
        target_exam_version_id
    );

    select review.review_id
    into approved_review_id
    from public.assessment_exam_reviews review
    where
        review.exam_version_id = target_exam_version_id
        and review.decision = 'APPROVED'
        and review.validation_evidence_id =
            governance_row.validation_evidence_id
        and review.validation_evidence_digest =
            governance_row.validation_evidence_digest
        and (
            (governance_row.validation_status = 'PASS'
                and coalesce(review.warning_acknowledged, false) = false)
            or (governance_row.validation_status = 'WARNING'
                and review.warning_acknowledged = true
                and governance_row.warning_confirmation_id is not null)
        )
    order by review.reviewed_at desc
    limit 1;

    if approved_review_id is null then
        raise exception 'CURRENT_GOVERNED_APPROVED_REVIEW_REQUIRED';
    end if;
    if not public.assessment_exam_content_is_publishable(
        target_exam_version_id
    ) then
        raise exception
            'Assessment exam content is no longer publishable.';
    end if;

    insert into public.assessment_exam_publications (
        exam_version_id,
        published_by,
        publication_channel,
        publication_note
    ) values (
        target_exam_version_id,
        (select auth.uid()),
        target_publication_channel,
        coalesce(target_publication_note, '')
    )
    returning publication_id into new_publication_id;

    update public.assessment_exam_versions
    set
        assembly_status = 'PUBLISHED',
        locked_at = coalesce(locked_at, now()),
        updated_at = now()
    where exam_version_id = target_exam_version_id;

    return new_publication_id;
end;
$$;

revoke all on function
public.publish_assessment_exam(uuid, text, text)
from public;

grant execute on function
public.publish_assessment_exam(uuid, text, text)
to authenticated;

alter function
public.build_assessment_exam_snapshot_document(uuid, uuid)
rename to build_assessment_exam_snapshot_document_v2;

create or replace function
public.build_assessment_exam_snapshot_document(
    target_exam_version_id uuid,
    target_publication_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = ''
as $$
    with snapshot_governance as (
        select
            public.build_assessment_exam_snapshot_document_v2(
                target_exam_version_id,
                target_publication_id
            ) as base_document,
            publication.published_by,
            evidence.validation_status,
            evidence.errors,
            evidence.warnings,
            evidence.metrics,
            evidence.validation_evidence_id,
            evidence.validation_input_digest,
            evidence.evidence_digest,
            evidence.validated_at,
            evidence.validation_schema_version,
            confirmation.warning_confirmation_id,
            confirmation.owner_user_id as confirmation_owner_user_id,
            confirmation.validation_evidence_digest as
                confirmation_evidence_digest,
            confirmation.confirmed_warnings,
            confirmation.confirmed_at,
            review.review_id,
            review.reviewer_user_id,
            review.decision,
            review.validation_evidence_id as review_evidence_id,
            review.validation_evidence_digest as review_evidence_digest,
            review.warning_acknowledged,
            review.reviewed_at
        from public.assessment_exam_publications publication
        join public.assessment_exam_validation_evidence evidence
            on evidence.exam_version_id = publication.exam_version_id
        join public.assessment_exam_reviews review
            on review.exam_version_id = publication.exam_version_id
            and review.decision = 'APPROVED'
            and review.validation_evidence_id =
                evidence.validation_evidence_id
            and review.validation_evidence_digest =
                evidence.evidence_digest
        left join public.assessment_exam_warning_confirmations confirmation
            on confirmation.validation_evidence_id =
                evidence.validation_evidence_id
            and confirmation.validation_evidence_digest =
                evidence.evidence_digest
            and confirmation.confirmed_warnings = evidence.warnings
        where
            publication.publication_id = target_publication_id
            and publication.exam_version_id = target_exam_version_id
            and evidence.validation_revision = (
                select max(latest.validation_revision)
                from public.assessment_exam_validation_evidence latest
                where latest.exam_version_id = target_exam_version_id
            )
        order by review.reviewed_at desc
        limit 1
    )
    select case
        when base_document is null then null
        else jsonb_set(
            jsonb_set(
                jsonb_set(
                    base_document,
                    '{snapshot_schema_version}',
                    '3'::jsonb,
                    true
                ),
                '{publication}',
                coalesce(base_document -> 'publication', '{}'::jsonb)
                || jsonb_build_object('published_by', published_by),
                true
            ),
            '{governance}',
            jsonb_build_object(
                'validation', jsonb_build_object(
                    'validation_status', validation_status,
                    'errors', errors,
                    'warnings', warnings,
                    'metrics', metrics,
                    'validation_evidence_id', validation_evidence_id,
                    'validation_input_digest', validation_input_digest,
                    'evidence_digest', evidence_digest,
                    'validated_at', validated_at,
                    'validation_schema_version',
                        validation_schema_version
                ),
                'teacher_confirmation', case
                    when validation_status = 'PASS' then 'null'::jsonb
                    else jsonb_build_object(
                        'warning_confirmation_id',
                            warning_confirmation_id,
                        'owner_user_id', confirmation_owner_user_id,
                        'validation_evidence_digest',
                            confirmation_evidence_digest,
                        'confirmed_warnings', confirmed_warnings,
                        'confirmed_at', confirmed_at
                    )
                end,
                'review', jsonb_build_object(
                    'review_id', review_id,
                    'reviewer_user_id', reviewer_user_id,
                    'decision', decision,
                    'validation_evidence_id', review_evidence_id,
                    'validation_evidence_digest',
                        review_evidence_digest,
                    'warning_acknowledged', warning_acknowledged,
                    'reviewed_at', reviewed_at
                )
            ),
            true
        )
    end
    from snapshot_governance;
$$;

revoke all on function
public.build_assessment_exam_snapshot_document(uuid, uuid)
from public;

create or replace function
public.capture_assessment_exam_publication_snapshot()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_owner_user_id uuid;
    current_status text;
    governance_row record;
    snapshot_document_value jsonb;
    snapshot_hash_value text;
begin
    select
        exam.owner_user_id,
        exam_version.assembly_status
    into current_owner_user_id, current_status
    from public.assessment_exam_versions exam_version
    join public.assessment_exams exam
        on exam.exam_id = exam_version.exam_id
    where exam_version.exam_version_id = new.exam_version_id
    for update of exam_version;

    if current_owner_user_id is null then
        raise exception 'Assessment exam version does not exist.';
    end if;
    if current_status is distinct from 'APPROVED' then
        raise exception 'Only an approved exam may be snapshotted.';
    end if;
    if new.published_by is distinct from current_owner_user_id then
        raise exception 'Snapshot publisher must be the exam owner.';
    end if;

    perform 1
    from public.assessment_exam_questions assignment
    where assignment.exam_version_id = new.exam_version_id
    order by assignment.display_number
    for update;

    select * into governance_row
    from public.assessment_exam_current_validation_governance(
        new.exam_version_id
    );
    if governance_row.validation_evidence_id is null then
        raise exception 'CURRENT_VALIDATION_GOVERNANCE_REQUIRED';
    end if;
    if not public.assessment_exam_content_is_publishable(
        new.exam_version_id
    ) then
        raise exception 'Assessment exam content is not publishable.';
    end if;

    snapshot_document_value :=
        public.build_assessment_exam_snapshot_document(
            new.exam_version_id,
            new.publication_id
        );
    if snapshot_document_value is null then
        raise exception
            'Assessment exam snapshot document could not be built.';
    end if;

    snapshot_hash_value := encode(
        extensions.digest(snapshot_document_value::text, 'sha256'),
        'hex'
    );

    insert into public.assessment_exam_snapshots (
        publication_id,
        exam_version_id,
        snapshot_schema_version,
        snapshot_document,
        snapshot_hash,
        created_by
    ) values (
        new.publication_id,
        new.exam_version_id,
        3,
        snapshot_document_value,
        snapshot_hash_value,
        new.published_by
    );

    return new;
end;
$$;

revoke all on function
public.capture_assessment_exam_publication_snapshot()
from public;

alter table public.assessment_exam_validation_evidence
    enable row level security;

alter table public.assessment_exam_warning_confirmations
    enable row level security;

revoke all on table
    public.assessment_exam_validation_evidence,
    public.assessment_exam_warning_confirmations
from public, anon, authenticated;

grant select
on table
    public.assessment_exam_validation_evidence,
    public.assessment_exam_warning_confirmations
to authenticated;

create policy assessment_exam_validation_evidence_select_visible
on public.assessment_exam_validation_evidence
for select
to authenticated
using (
    public.assessment_exam_version_is_visible(exam_version_id)
);

create policy assessment_exam_warning_confirmations_select_visible
on public.assessment_exam_warning_confirmations
for select
to authenticated
using (
    public.assessment_exam_version_is_visible(exam_version_id)
);

comment on table public.assessment_exam_validation_evidence is
'Append-only canonical PASS/WARNING/FAIL validation evidence. The current producer emits PASS or FAIL only.';

comment on table public.assessment_exam_warning_confirmations is
'Append-only owner confirmation bound to exact current WARNING evidence; confirmation never changes validation status.';

comment on function
public.assessment_exam_validation_report(uuid) is
'Atomically validates and persists canonical evidence; no production WARNING rule is defined.';

comment on function
public.build_assessment_exam_snapshot_document_v2(uuid, uuid) is
'Legacy schema-2 snapshot builder retained for reproducibility.';

comment on function
public.build_assessment_exam_snapshot_document(uuid, uuid) is
'Builds schema-3 snapshots with canonical validation, confirmation, and review governance.';

commit;
