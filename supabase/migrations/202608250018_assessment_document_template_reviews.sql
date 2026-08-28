begin;

create table if not exists public.assessment_document_template_reviews (
    template_review_id uuid primary key default gen_random_uuid(),

    template_version_id uuid not null
        references public.assessment_document_template_versions(
            template_version_id
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

    review_comment text null,

    reviewed_at timestamptz not null default now(),

    metadata jsonb not null default '{}'::jsonb
        check (jsonb_typeof(metadata) = 'object')
);

create or replace function
public.assessment_document_template_ready_for_review(
    target_template_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_document_template_versions
            template_version
        join public.assessment_document_template_sets
            template_set
            on template_set.template_set_id =
                template_version.template_set_id
        where
            template_version.template_version_id =
                target_template_version_id
            and template_version.review_status in (
                'DRAFT',
                'PENDING_REVIEW',
                'REVISION_REQUIRED',
                'APPROVED'
            )
            and (
                template_set.owner_user_id =
                    (select auth.uid())
                or (
                    select
                        public.current_user_is_portal_admin()
                )
            )
            and (
                select count(*)
                from public.assessment_document_template_definitions
                    template_definition
                join public.assessment_document_types
                    document_type
                    on document_type.document_type_code =
                        template_definition.document_type_code
                where
                    template_definition.template_version_id =
                        template_version.template_version_id
                    and document_type.is_active
            ) = (
                select count(*)
                from public.assessment_document_types
                    required_document_type
                where required_document_type.is_active
            )
            and not exists (
                select 1
                from public.assessment_document_types
                    required_document_type
                where
                    required_document_type.is_active
                    and not exists (
                        select 1
                        from public.assessment_document_template_definitions
                            template_definition
                        where
                            template_definition.template_version_id =
                                template_version.template_version_id
                            and
                                template_definition.document_type_code =
                                    required_document_type.document_type_code
                    )
            )
            and not exists (
                select 1
                from public.assessment_document_template_definitions
                    template_definition
                where
                    template_definition.template_version_id =
                        template_version.template_version_id
                    and (
                        cardinality(
                            template_definition.supported_formats
                        ) = 0
                        or jsonb_typeof(
                            template_definition.layout_schema
                        ) is distinct from 'object'
                        or jsonb_typeof(
                            template_definition.style_schema
                        ) is distinct from 'object'
                        or jsonb_typeof(
                            template_definition.binding_schema
                        ) is distinct from 'object'
                        or jsonb_typeof(
                            template_definition.section_schema
                        ) is distinct from 'array'
                        or (
                            template_definition.template_asset_path
                                is not null
                            and template_definition.template_asset_hash
                                is null
                        )
                    )
            )
    );
$$;

revoke all on function
public.assessment_document_template_ready_for_review(uuid)
from public;

grant execute on function
public.assessment_document_template_ready_for_review(uuid)
to authenticated;

create or replace function
public.submit_assessment_document_template_for_review(
    target_template_version_id uuid
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_template_set_id uuid;
    current_owner_user_id uuid;
    current_authority_scope text;
    current_review_status text;
begin
    select
        template_version.template_set_id,
        template_set.owner_user_id,
        template_set.authority_scope,
        template_version.review_status
    into
        current_template_set_id,
        current_owner_user_id,
        current_authority_scope,
        current_review_status
    from public.assessment_document_template_versions
        template_version
    join public.assessment_document_template_sets
        template_set
        on template_set.template_set_id =
            template_version.template_set_id
    where
        template_version.template_version_id =
            target_template_version_id
    for update of template_version;

    if current_template_set_id is null then
        raise exception
            'Assessment document template version does not exist.';
    end if;

    if not (
        (
            current_authority_scope = 'USER'
            and current_owner_user_id =
                (select auth.uid())
        )
        or (
            current_authority_scope <> 'USER'
            and (
                select
                    public.current_user_is_portal_admin()
            )
        )
    ) then
        raise exception
            'Current user may not submit this template.';
    end if;

    if current_review_status not in (
        'DRAFT',
        'REVISION_REQUIRED'
    ) then
        raise exception
            'Only an editable template may be submitted.';
    end if;

    if not
        public.assessment_document_template_ready_for_review(
            target_template_version_id
        )
    then
        raise exception
            'Assessment document template is incomplete.';
    end if;

    update public.assessment_document_template_versions
    set
        review_status = 'PENDING_REVIEW',
        submitted_at = now(),
        approved_at = null,
        approved_by = null,
        updated_at = now()
    where
        template_version_id =
            target_template_version_id;

    return target_template_version_id;
end;
$$;

revoke all on function
public.submit_assessment_document_template_for_review(uuid)
from public;

grant execute on function
public.submit_assessment_document_template_for_review(uuid)
to authenticated;

create or replace function
public.review_assessment_document_template(
    target_template_version_id uuid,
    target_decision text,
    target_review_comment text default null
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_review_status text;
    new_template_review_id uuid;
begin
    if not (
        select public.current_user_is_portal_admin()
    ) then
        raise exception
            'Only a portal administrator may review templates.';
    end if;

    if target_decision not in (
        'APPROVED',
        'REVISION_REQUIRED',
        'REJECTED'
    ) then
        raise exception
            'Assessment template review decision is invalid.';
    end if;

    select template_version.review_status
    into current_review_status
    from public.assessment_document_template_versions
        template_version
    where
        template_version.template_version_id =
            target_template_version_id
    for update;

    if current_review_status is null then
        raise exception
            'Assessment document template version does not exist.';
    end if;

    if current_review_status is distinct from
        'PENDING_REVIEW'
    then
        raise exception
            'Only a pending template may be reviewed.';
    end if;

    if (
        target_decision = 'APPROVED'
        and not
            public.assessment_document_template_ready_for_review(
                target_template_version_id
            )
    ) then
        raise exception
            'An incomplete template may not be approved.';
    end if;

    insert into public.assessment_document_template_reviews (
        template_version_id,
        reviewer_user_id,
        decision,
        review_comment
    )
    values (
        target_template_version_id,
        (select auth.uid()),
        target_decision,
        nullif(trim(target_review_comment), '')
    )
    returning template_review_id
    into new_template_review_id;

    update public.assessment_document_template_versions
    set
        review_status = target_decision,
        approved_at = case
            when target_decision = 'APPROVED'
                then now()
            else null
        end,
        approved_by = case
            when target_decision = 'APPROVED'
                then (select auth.uid())
            else null
        end,
        updated_at = now()
    where
        template_version_id =
            target_template_version_id;

    return new_template_review_id;
end;
$$;

revoke all on function
public.review_assessment_document_template(
    uuid,
    text,
    text
)
from public;

grant execute on function
public.review_assessment_document_template(
    uuid,
    text,
    text
)
to authenticated;

create or replace function
public.activate_assessment_document_template_version(
    target_template_version_id uuid
)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_template_set_id uuid;
    approved_version_number integer;
    current_review_status text;
    current_owner_user_id uuid;
    current_authority_scope text;
begin
    select
        template_version.template_set_id,
        template_version.version_number,
        template_version.review_status,
        template_set.owner_user_id,
        template_set.authority_scope
    into
        current_template_set_id,
        approved_version_number,
        current_review_status,
        current_owner_user_id,
        current_authority_scope
    from public.assessment_document_template_versions
        template_version
    join public.assessment_document_template_sets
        template_set
        on template_set.template_set_id =
            template_version.template_set_id
    where
        template_version.template_version_id =
            target_template_version_id
    for update of template_set;

    if current_template_set_id is null then
        raise exception
            'Assessment document template version does not exist.';
    end if;

    if current_review_status is distinct from 'APPROVED' then
        raise exception
            'Only an approved template may be activated.';
    end if;

    if not (
        (
            current_authority_scope = 'USER'
            and current_owner_user_id =
                (select auth.uid())
        )
        or (
            current_authority_scope <> 'USER'
            and (
                select
                    public.current_user_is_portal_admin()
            )
        )
    ) then
        raise exception
            'Current user may not activate this template.';
    end if;

    if not
        public.assessment_document_template_ready_for_review(
            target_template_version_id
        )
    then
        raise exception
            'An incomplete template may not be activated.';
    end if;

    update public.assessment_document_template_sets
    set
        current_version_number =
            approved_version_number,
        lifecycle_status = 'ACTIVE',
        updated_at = now()
    where
        template_set_id =
            current_template_set_id;

    return current_template_set_id;
end;
$$;

revoke all on function
public.activate_assessment_document_template_version(uuid)
from public;

grant execute on function
public.activate_assessment_document_template_version(uuid)
to authenticated;

create or replace function
public.prevent_assessment_template_review_mutation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    raise exception
        'Assessment document template reviews are immutable.';
end;
$$;

revoke all on function
public.prevent_assessment_template_review_mutation()
from public;

drop trigger if exists
assessment_document_template_reviews_immutable
on public.assessment_document_template_reviews;

create trigger
assessment_document_template_reviews_immutable
before update or delete
on public.assessment_document_template_reviews
for each row
execute function
public.prevent_assessment_template_review_mutation();

alter table public.assessment_document_template_reviews
    enable row level security;

revoke all
on table public.assessment_document_template_reviews
from anon;

grant select
on table public.assessment_document_template_reviews
to authenticated;

drop policy if exists
assessment_document_template_reviews_select_visible
on public.assessment_document_template_reviews;

create policy
assessment_document_template_reviews_select_visible
on public.assessment_document_template_reviews
for select
to authenticated
using (
    exists (
        select 1
        from public.assessment_document_template_versions
            template_version
        where
            template_version.template_version_id =
                assessment_document_template_reviews.template_version_id
            and
                public.assessment_document_template_set_is_visible(
                    template_version.template_set_id
                )
    )
);

comment on table
public.assessment_document_template_reviews is
'Immutable human review history for dynamic assessment templates.';

comment on function
public.assessment_document_template_ready_for_review(uuid) is
'Checks that every active assessment document type has a valid template definition.';

comment on function
public.activate_assessment_document_template_version(uuid) is
'Activates an approved template version without changing application code.';

commit;
