begin;

create table if not exists public.assessment_blueprint_reviews (
    review_id uuid primary key default gen_random_uuid(),

    blueprint_version_id uuid not null
        references public.assessment_blueprint_versions(
            blueprint_version_id
        )
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
assessment_blueprint_reviews_version_idx
on public.assessment_blueprint_reviews (
    blueprint_version_id,
    reviewed_at desc
);

create or replace function
public.submit_assessment_blueprint_for_review(
    target_blueprint_version_id uuid
)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_owner_user_id uuid;
begin
    select blueprint.owner_user_id
    into current_owner_user_id
    from public.assessment_blueprint_versions blueprint_version
    join public.assessment_blueprints blueprint
        on blueprint.blueprint_id =
            blueprint_version.blueprint_id
    where
        blueprint_version.blueprint_version_id =
            target_blueprint_version_id
    for update of blueprint_version;

    if current_owner_user_id is null then
        raise exception
            'Assessment blueprint version does not exist.';
    end if;

    if current_owner_user_id is distinct from (select auth.uid()) then
        raise exception
            'Only the blueprint owner may submit it for review.';
    end if;

    if not public.assessment_blueprint_version_is_editable(
        target_blueprint_version_id
    ) then
        raise exception
            'Assessment blueprint version is not editable.';
    end if;

    if not public.assessment_blueprint_ready_for_review(
        target_blueprint_version_id
    ) then
        raise exception
            'Assessment blueprint version is incomplete.';
    end if;

    update public.assessment_blueprint_versions
    set
        review_status = 'PENDING_REVIEW',
        updated_at = now()
    where
        blueprint_version_id =
            target_blueprint_version_id;
end;
$$;

revoke all on function
public.submit_assessment_blueprint_for_review(uuid)
from public;

grant execute on function
public.submit_assessment_blueprint_for_review(uuid)
to authenticated;

create or replace function
public.apply_assessment_blueprint_review()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_status text;
    approved_version_number integer;
    current_blueprint_id uuid;
    current_owner_user_id uuid;
begin
    if not public.current_user_is_portal_admin() then
        raise exception
            'Only a portal administrator may review a blueprint.';
    end if;

    if new.reviewer_user_id is distinct from (select auth.uid()) then
        raise exception
            'Reviewer must match the authenticated user.';
    end if;

    select
        blueprint_version.review_status,
        blueprint_version.version_number,
        blueprint_version.blueprint_id,
        blueprint.owner_user_id
    into
        current_status,
        approved_version_number,
        current_blueprint_id,
        current_owner_user_id
    from public.assessment_blueprint_versions blueprint_version
    join public.assessment_blueprints blueprint
        on blueprint.blueprint_id =
            blueprint_version.blueprint_id
    where
        blueprint_version.blueprint_version_id =
            new.blueprint_version_id
    for update of blueprint_version, blueprint;

    if current_status is null then
        raise exception
            'Assessment blueprint version does not exist.';
    end if;

    if current_owner_user_id = (select auth.uid()) then
        raise exception
            'A reviewer may not review their own blueprint.';
    end if;

    if current_status is distinct from 'PENDING_REVIEW' then
        raise exception
            'Only a pending blueprint version may be reviewed.';
    end if;

    if new.decision = 'APPROVED' then
        if not public.assessment_blueprint_ready_for_review(
            new.blueprint_version_id
        ) then
            raise exception
                'Assessment blueprint is no longer ready for approval.';
        end if;

        update public.assessment_blueprint_versions
        set
            review_status = 'APPROVED',
            locked_at = now(),
            updated_at = now()
        where
            blueprint_version_id =
                new.blueprint_version_id;

        update public.assessment_blueprints
        set
            current_version_number =
                approved_version_number,
            lifecycle_status = 'ACTIVE',
            updated_at = now()
        where
            blueprint_id = current_blueprint_id;

    elsif new.decision = 'REVISION_REQUIRED' then
        update public.assessment_blueprint_versions
        set
            review_status = 'REVISION_REQUIRED',
            locked_at = null,
            updated_at = now()
        where
            blueprint_version_id =
                new.blueprint_version_id;

    elsif new.decision = 'REJECTED' then
        update public.assessment_blueprint_versions
        set
            review_status = 'REJECTED',
            locked_at = now(),
            updated_at = now()
        where
            blueprint_version_id =
                new.blueprint_version_id;
    else
        raise exception
            'Unsupported assessment blueprint review decision.';
    end if;

    new.reviewed_at := now();

    return new;
end;
$$;

revoke all on function
public.apply_assessment_blueprint_review()
from public;

drop trigger if exists
assessment_blueprint_reviews_apply
on public.assessment_blueprint_reviews;

create trigger assessment_blueprint_reviews_apply
before insert
on public.assessment_blueprint_reviews
for each row
execute function
public.apply_assessment_blueprint_review();

alter table public.assessment_blueprint_reviews
    enable row level security;

revoke all on table
public.assessment_blueprint_reviews
from anon;

grant select, insert
on table public.assessment_blueprint_reviews
to authenticated;

drop policy if exists
assessment_blueprint_reviews_select_visible
on public.assessment_blueprint_reviews;

create policy assessment_blueprint_reviews_select_visible
on public.assessment_blueprint_reviews
for select
to authenticated
using (
    public.assessment_blueprint_version_is_visible(
        blueprint_version_id
    )
);

drop policy if exists
assessment_blueprint_reviews_insert_admin
on public.assessment_blueprint_reviews;

create policy assessment_blueprint_reviews_insert_admin
on public.assessment_blueprint_reviews
for insert
to authenticated
with check (
    public.current_user_is_portal_admin()
    and reviewer_user_id = (select auth.uid())
    and exists (
        select 1
        from public.assessment_blueprint_versions blueprint_version
        join public.assessment_blueprints blueprint
            on blueprint.blueprint_id =
                blueprint_version.blueprint_id
        where
            blueprint_version.blueprint_version_id =
                assessment_blueprint_reviews.blueprint_version_id
            and blueprint.owner_user_id
                is distinct from (select auth.uid())
    )
);

comment on table public.assessment_blueprint_reviews is
'Immutable administrative review history for assessment blueprint versions.';

comment on function
public.submit_assessment_blueprint_for_review(uuid) is
'Allows the teacher owner to submit a complete editable blueprint version for review.';

comment on function
public.apply_assessment_blueprint_review() is
'Applies an administrator decision and locks approved or rejected blueprint versions.';

commit;

