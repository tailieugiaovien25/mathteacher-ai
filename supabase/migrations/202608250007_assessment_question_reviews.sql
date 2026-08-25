-- Assessment Question Review Workflow V1
-- Readiness validation, teacher submission, administrator review,
-- approval locking, revision reopening, and immutable review history.

create table if not exists public.assessment_question_reviews (
    review_id uuid primary key default gen_random_uuid(),

    question_version_id uuid not null
        references public.assessment_question_versions(question_version_id)
        on delete restrict,

    reviewer_user_id uuid not null
        references auth.users(id)
        on delete restrict,

    decision text not null
        check (
            decision in (
                'APPROVED',
                'REVISION_REQUIRED',
                'REJECTED'
            )
        ),

    review_note text not null default '',

    checklist jsonb not null default '{}'::jsonb
        check (jsonb_typeof(checklist) = 'object'),

    reviewed_at timestamptz not null default now()
);

create index if not exists
    assessment_question_reviews_version_idx
on public.assessment_question_reviews (
    question_version_id,
    reviewed_at desc
);

create index if not exists
    assessment_question_reviews_reviewer_idx
on public.assessment_question_reviews (
    reviewer_user_id,
    reviewed_at desc
);

create or replace function
public.assessment_question_ready_for_review(
    target_question_version_id uuid
)
returns boolean
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
    question_type_code_value text;
    answer_mode_value text;
    requires_solution_value boolean;
    option_count integer;
    correct_option_count integer;
    statement_count integer;
begin
    select
        question_version.question_type_code,
        question_type.answer_mode,
        question_type.requires_solution
    into
        question_type_code_value,
        answer_mode_value,
        requires_solution_value
    from public.assessment_question_versions question_version
    join public.assessment_question_types question_type
        on question_type.question_type_code =
            question_version.question_type_code
    where
        question_version.question_version_id =
            target_question_version_id
        and question_version.locked_at is null
        and question_version.review_status in (
            'DRAFT',
            'AI_PROPOSED',
            'PENDING_REVIEW',
            'REVISION_REQUIRED'
        );

    if question_type_code_value is null then
        return false;
    end if;

    if not exists (
        select 1
        from public.assessment_question_answers answer
        where
            answer.question_version_id =
                target_question_version_id
            and answer.answer_mode =
                answer_mode_value
    ) then
        return false;
    end if;

    if not exists (
        select 1
        from public.assessment_question_requirement_links link
        where
            link.question_version_id =
                target_question_version_id
            and link.link_role = 'PRIMARY'
    ) then
        return false;
    end if;

    if not exists (
        select 1
        from public.assessment_question_competency_links link
        where
            link.question_version_id =
                target_question_version_id
            and link.link_role = 'PRIMARY'
    ) then
        return false;
    end if;

    if question_type_code_value = 'MULTIPLE_CHOICE' then
        select
            count(*),
            count(*) filter (
                where option.is_correct = true
            )
        into
            option_count,
            correct_option_count
        from public.assessment_question_options option
        where
            option.question_version_id =
                target_question_version_id;

        if option_count <> 4
           or correct_option_count <> 1
        then
            return false;
        end if;
    end if;

    if question_type_code_value = 'TRUE_FALSE' then
        select count(*)
        into statement_count
        from public.assessment_question_statements statement
        where
            statement.question_version_id =
                target_question_version_id;

        if statement_count <> 4 then
            return false;
        end if;
    end if;

    if requires_solution_value
       and not exists (
            select 1
            from public.assessment_question_solutions solution
            where
                solution.question_version_id =
                    target_question_version_id
                and solution.is_primary = true
       )
    then
        return false;
    end if;

    if question_type_code_value = 'ESSAY'
       and not exists (
            select 1
            from public.assessment_question_scoring_steps scoring_step
            where
                scoring_step.question_version_id =
                    target_question_version_id
       )
    then
        return false;
    end if;

    if not (
        select
            public.assessment_question_scoring_total_matches(
                target_question_version_id
            )
    ) then
        return false;
    end if;

    return true;
end;
$$;

revoke all on function
public.assessment_question_ready_for_review(uuid)
from public;

grant execute on function
public.assessment_question_ready_for_review(uuid)
to authenticated;

create or replace function
public.submit_assessment_question_for_review(
    target_question_version_id uuid
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
    if (select auth.uid()) is null then
        raise exception
            'Authentication is required.';
    end if;

    if not (
        select
            public.assessment_question_version_is_editable(
                target_question_version_id
            )
    ) then
        raise exception
            'Question version is not editable by current user.';
    end if;

    if not (
        select
            public.assessment_question_ready_for_review(
                target_question_version_id
            )
    ) then
        raise exception
            'Question version is incomplete and cannot be submitted.';
    end if;

    update public.assessment_question_versions
    set
        review_status = 'PENDING_REVIEW',
        updated_at = now()
    where
        question_version_id =
            target_question_version_id;
end;
$$;

revoke all on function
public.submit_assessment_question_for_review(uuid)
from public;

grant execute on function
public.submit_assessment_question_for_review(uuid)
to authenticated;

create or replace function
public.apply_assessment_question_review()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_status text;
    reviewed_question_id uuid;
    reviewed_version_number integer;
begin
    if not (
        select public.current_user_is_portal_admin()
    ) then
        raise exception
            'Only an active portal administrator may review questions.';
    end if;

    if new.reviewer_user_id <> (select auth.uid()) then
        raise exception
            'Reviewer identity must match current user.';
    end if;

    select
        question_version.review_status,
        question_version.question_id,
        question_version.version_number
    into
        current_status,
        reviewed_question_id,
        reviewed_version_number
    from public.assessment_question_versions question_version
    where
        question_version.question_version_id =
            new.question_version_id
    for update;

    if current_status is distinct from 'PENDING_REVIEW' then
        raise exception
            'Only a pending question version may be reviewed.';
    end if;

    if new.decision = 'APPROVED' then
        if not (
            select
                public.assessment_question_ready_for_review(
                    new.question_version_id
                )
        ) then
            raise exception
                'Question version no longer satisfies approval rules.';
        end if;

        update public.assessment_question_versions
        set
            review_status = 'APPROVED',
            locked_at = now(),
            updated_at = now()
        where
            question_version_id =
                new.question_version_id;

        update public.assessment_question_items
        set
            current_version_number =
                reviewed_version_number,
            lifecycle_status = 'ACTIVE',
            updated_at = now()
        where
            question_id = reviewed_question_id;

    elsif new.decision = 'REVISION_REQUIRED' then
        update public.assessment_question_versions
        set
            review_status = 'REVISION_REQUIRED',
            locked_at = null,
            updated_at = now()
        where
            question_version_id =
                new.question_version_id;

    elsif new.decision = 'REJECTED' then
        update public.assessment_question_versions
        set
            review_status = 'REJECTED',
            locked_at = now(),
            updated_at = now()
        where
            question_version_id =
                new.question_version_id;
    end if;

    return new;
end;
$$;

drop trigger if exists
    assessment_question_reviews_apply_decision
on public.assessment_question_reviews;

create trigger
    assessment_question_reviews_apply_decision
after insert
on public.assessment_question_reviews
for each row
execute function
    public.apply_assessment_question_review();

alter table public.assessment_question_reviews
    enable row level security;

revoke all on table
    public.assessment_question_reviews
from anon;

grant select, insert on table
    public.assessment_question_reviews
to authenticated;

drop policy if exists
    assessment_question_reviews_select_authorized
on public.assessment_question_reviews;

create policy
    assessment_question_reviews_select_authorized
on public.assessment_question_reviews
for select
to authenticated
using (
    (
        select
            public.assessment_question_version_is_visible(
                question_version_id
            )
    )
);

drop policy if exists
    assessment_question_reviews_insert_admin
on public.assessment_question_reviews;

create policy
    assessment_question_reviews_insert_admin
on public.assessment_question_reviews
for insert
to authenticated
with check (
    (select public.current_user_is_portal_admin())
    and reviewer_user_id = (select auth.uid())
);

comment on table public.assessment_question_reviews is
'Immutable administrator review history for submitted question versions.';

comment on function
public.assessment_question_ready_for_review(uuid) is
'Checks answer, primary requirement, primary competency, components, solution, and scoring completeness.';

comment on function
public.submit_assessment_question_for_review(uuid) is
'Allows the owning teacher to submit a complete editable version for review.';

comment on function
public.apply_assessment_question_review() is
'Applies administrator decisions and locks approved or rejected versions.';

