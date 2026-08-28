begin;

create table if not exists public.assessment_document_types (
    document_type_code text primary key
        check (
            document_type_code in (
                'MATRIX',
                'SPECIFICATION',
                'STUDENT_EXAM',
                'ANSWER_KEY',
                'SCORING_GUIDE'
            )
        ),

    display_name text not null
        check (char_length(trim(display_name)) between 1 and 150),

    source_scope text not null
        check (
            source_scope in (
                'SNAPSHOT',
                'VARIANT'
            )
        ),

    contains_protected_answers boolean not null default false,

    sort_order integer not null
        check (sort_order >= 1),

    is_active boolean not null default true,

    metadata jsonb not null default '{}'::jsonb
        check (jsonb_typeof(metadata) = 'object'),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.assessment_document_template_sets (
    template_set_id uuid primary key default gen_random_uuid(),

    template_code text not null unique
        check (
            char_length(trim(template_code))
            between 1 and 140
        ),

    template_name text not null
        check (
            char_length(trim(template_name))
            between 1 and 250
        ),

    authority_scope text not null
        check (
            authority_scope in (
                'NATIONAL',
                'PROVINCE',
                'DISTRICT',
                'SCHOOL',
                'USER'
            )
        ),

    authority_reference text null
        check (
            authority_reference is null
            or char_length(trim(authority_reference))
                between 1 and 250
        ),

    owner_user_id uuid null
        references auth.users(id)
        on delete restrict,

    lifecycle_status text not null default 'DRAFT'
        check (
            lifecycle_status in (
                'DRAFT',
                'ACTIVE',
                'RETIRED'
            )
        ),

    current_version_number integer null
        check (
            current_version_number is null
            or current_version_number >= 1
        ),

    description text null,

    metadata jsonb not null default '{}'::jsonb
        check (jsonb_typeof(metadata) = 'object'),

    created_by uuid not null
        references auth.users(id)
        on delete restrict,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    check (
        (
            authority_scope = 'USER'
            and owner_user_id is not null
        )
        or
        (
            authority_scope <> 'USER'
            and owner_user_id is null
        )
    )
);

create table if not exists public.assessment_document_template_versions (
    template_version_id uuid primary key default gen_random_uuid(),

    template_set_id uuid not null
        references public.assessment_document_template_sets(
            template_set_id
        )
        on delete restrict,

    version_number integer not null
        check (version_number >= 1),

    version_label text not null
        check (
            char_length(trim(version_label))
            between 1 and 100
        ),

    review_status text not null default 'DRAFT'
        check (
            review_status in (
                'DRAFT',
                'PENDING_REVIEW',
                'REVISION_REQUIRED',
                'APPROVED',
                'REJECTED'
            )
        ),

    compatibility_schema_version integer not null default 1
        check (compatibility_schema_version >= 1),

    global_layout_schema jsonb not null default '{}'::jsonb
        check (
            jsonb_typeof(global_layout_schema) = 'object'
        ),

    global_style_schema jsonb not null default '{}'::jsonb
        check (
            jsonb_typeof(global_style_schema) = 'object'
        ),

    required_context_schema jsonb not null default '{}'::jsonb
        check (
            jsonb_typeof(required_context_schema) = 'object'
        ),

    change_summary text null,

    submitted_at timestamptz null,
    approved_at timestamptz null,
    approved_by uuid null
        references auth.users(id)
        on delete restrict,

    created_by uuid not null
        references auth.users(id)
        on delete restrict,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        template_set_id,
        version_number
    ),

    check (
        (
            review_status = 'APPROVED'
            and approved_at is not null
            and approved_by is not null
        )
        or review_status <> 'APPROVED'
    )
);

create table if not exists public.assessment_document_template_definitions (
    template_definition_id uuid primary key
        default gen_random_uuid(),

    template_version_id uuid not null
        references public.assessment_document_template_versions(
            template_version_id
        )
        on delete restrict,

    document_type_code text not null
        references public.assessment_document_types(
            document_type_code
        )
        on delete restrict,

    renderer_code text not null default 'DOCX_JSON_V1'
        check (
            char_length(trim(renderer_code))
            between 1 and 100
        ),

    supported_formats text[] not null
        check (
            cardinality(supported_formats) >= 1
            and supported_formats
                <@ array['DOCX', 'PDF', 'JSON']::text[]
        ),

    layout_schema jsonb not null default '{}'::jsonb
        check (jsonb_typeof(layout_schema) = 'object'),

    style_schema jsonb not null default '{}'::jsonb
        check (jsonb_typeof(style_schema) = 'object'),

    binding_schema jsonb not null default '{}'::jsonb
        check (jsonb_typeof(binding_schema) = 'object'),

    section_schema jsonb not null default '[]'::jsonb
        check (jsonb_typeof(section_schema) = 'array'),

    template_asset_path text null
        check (
            template_asset_path is null
            or char_length(trim(template_asset_path))
                between 1 and 500
        ),

    template_asset_hash text null
        check (
            template_asset_hash is null
            or char_length(template_asset_hash) = 64
        ),

    sort_order integer not null
        check (sort_order >= 1),

    metadata jsonb not null default '{}'::jsonb
        check (jsonb_typeof(metadata) = 'object'),

    created_by uuid not null
        references auth.users(id)
        on delete restrict,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        template_version_id,
        document_type_code
    )
);

insert into public.assessment_document_types (
    document_type_code,
    display_name,
    source_scope,
    contains_protected_answers,
    sort_order
)
values
    (
        'MATRIX',
        'Ma trận đề kiểm tra',
        'SNAPSHOT',
        false,
        1
    ),
    (
        'SPECIFICATION',
        'Bản đặc tả đề kiểm tra',
        'SNAPSHOT',
        false,
        2
    ),
    (
        'STUDENT_EXAM',
        'Đề dành cho học sinh',
        'VARIANT',
        false,
        3
    ),
    (
        'ANSWER_KEY',
        'Đáp án',
        'VARIANT',
        true,
        4
    ),
    (
        'SCORING_GUIDE',
        'Hướng dẫn chấm',
        'VARIANT',
        true,
        5
    )
on conflict (document_type_code)
do update set
    display_name = excluded.display_name,
    source_scope = excluded.source_scope,
    contains_protected_answers =
        excluded.contains_protected_answers,
    sort_order = excluded.sort_order,
    is_active = true,
    updated_at = now();

create or replace function
public.assessment_document_template_set_is_visible(
    target_template_set_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_document_template_sets template_set
        where
            template_set.template_set_id =
                target_template_set_id
            and (
                template_set.owner_user_id =
                    (select auth.uid())
                or (
                    template_set.lifecycle_status = 'ACTIVE'
                    and exists (
                        select 1
                        from public.assessment_document_template_versions
                            template_version
                        where
                            template_version.template_set_id =
                                template_set.template_set_id
                            and template_version.version_number =
                                template_set.current_version_number
                            and template_version.review_status =
                                'APPROVED'
                    )
                )
                or (
                    select
                        public.current_user_is_portal_admin()
                )
            )
    );
$$;

revoke all on function
public.assessment_document_template_set_is_visible(uuid)
from public;

grant execute on function
public.assessment_document_template_set_is_visible(uuid)
to authenticated;

create or replace function
public.prevent_assessment_template_identity_reassignment()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    if tg_table_name =
        'assessment_document_template_sets'
    then
        if (
            new.template_code is distinct from old.template_code
            or new.authority_scope is distinct from old.authority_scope
            or new.owner_user_id is distinct from old.owner_user_id
            or new.created_by is distinct from old.created_by
        ) then
            raise exception
                'Assessment template set identity is immutable.';
        end if;
    elsif tg_table_name =
        'assessment_document_template_versions'
    then
        if (
            new.template_set_id is distinct from old.template_set_id
            or new.version_number is distinct from old.version_number
            or new.created_by is distinct from old.created_by
        ) then
            raise exception
                'Assessment template version identity is immutable.';
        end if;
    elsif tg_table_name =
        'assessment_document_template_definitions'
    then
        if (
            new.template_version_id is distinct from
                old.template_version_id
            or new.document_type_code is distinct from
                old.document_type_code
            or new.created_by is distinct from old.created_by
        ) then
            raise exception
                'Assessment template definition identity is immutable.';
        end if;
    end if;

    return new;
end;
$$;

revoke all on function
public.prevent_assessment_template_identity_reassignment()
from public;

drop trigger if exists
assessment_document_template_sets_identity_immutable
on public.assessment_document_template_sets;

create trigger
assessment_document_template_sets_identity_immutable
before update
on public.assessment_document_template_sets
for each row
execute function
public.prevent_assessment_template_identity_reassignment();

drop trigger if exists
assessment_document_template_versions_identity_immutable
on public.assessment_document_template_versions;

create trigger
assessment_document_template_versions_identity_immutable
before update
on public.assessment_document_template_versions
for each row
execute function
public.prevent_assessment_template_identity_reassignment();

drop trigger if exists
assessment_document_template_definitions_identity_immutable
on public.assessment_document_template_definitions;

create trigger
assessment_document_template_definitions_identity_immutable
before update
on public.assessment_document_template_definitions
for each row
execute function
public.prevent_assessment_template_identity_reassignment();


create or replace function
public.prevent_approved_assessment_template_mutation()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
    current_review_status text;
begin
    if tg_table_name =
        'assessment_document_template_versions'
    then
        current_review_status := old.review_status;
    else
        select template_version.review_status
        into current_review_status
        from public.assessment_document_template_versions
            template_version
        where
            template_version.template_version_id =
                old.template_version_id;
    end if;

    if current_review_status = 'APPROVED' then
        raise exception
            'Approved assessment document templates are immutable.';
    end if;

    if tg_op = 'DELETE' then
        return old;
    end if;

    return new;
end;
$$;

revoke all on function
public.prevent_approved_assessment_template_mutation()
from public;

drop trigger if exists
assessment_document_template_versions_immutable
on public.assessment_document_template_versions;

create trigger
assessment_document_template_versions_immutable
before update or delete
on public.assessment_document_template_versions
for each row
execute function
public.prevent_approved_assessment_template_mutation();

drop trigger if exists
assessment_document_template_definitions_immutable
on public.assessment_document_template_definitions;

create trigger
assessment_document_template_definitions_immutable
before update or delete
on public.assessment_document_template_definitions
for each row
execute function
public.prevent_approved_assessment_template_mutation();

alter table public.assessment_document_types
    enable row level security;

alter table public.assessment_document_template_sets
    enable row level security;

alter table public.assessment_document_template_versions
    enable row level security;

alter table public.assessment_document_template_definitions
    enable row level security;

revoke all
on table
    public.assessment_document_types,
    public.assessment_document_template_sets,
    public.assessment_document_template_versions,
    public.assessment_document_template_definitions
from anon;

grant select
on table
    public.assessment_document_types,
    public.assessment_document_template_sets,
    public.assessment_document_template_versions,
    public.assessment_document_template_definitions
to authenticated;

grant insert, update, delete
on table
    public.assessment_document_template_sets,
    public.assessment_document_template_versions,
    public.assessment_document_template_definitions
to authenticated;

drop policy if exists
assessment_document_types_select_authenticated
on public.assessment_document_types;

create policy
assessment_document_types_select_authenticated
on public.assessment_document_types
for select
to authenticated
using (is_active);

drop policy if exists
assessment_template_sets_select_visible
on public.assessment_document_template_sets;

create policy
assessment_template_sets_select_visible
on public.assessment_document_template_sets
for select
to authenticated
using (
    public.assessment_document_template_set_is_visible(
        template_set_id
    )
);

drop policy if exists
assessment_template_sets_insert_governed
on public.assessment_document_template_sets;

create policy
assessment_template_sets_insert_governed
on public.assessment_document_template_sets
for insert
to authenticated
with check (
    created_by = (select auth.uid())
    and (
        (
            authority_scope = 'USER'
            and owner_user_id = (select auth.uid())
        )
        or (
            authority_scope <> 'USER'
            and owner_user_id is null
            and (
                select
                    public.current_user_is_portal_admin()
            )
        )
    )
);

drop policy if exists
assessment_template_sets_update_governed
on public.assessment_document_template_sets;

create policy
assessment_template_sets_update_governed
on public.assessment_document_template_sets
for update
to authenticated
using (
    (
        authority_scope = 'USER'
        and owner_user_id = (select auth.uid())
    )
    or (
        authority_scope <> 'USER'
        and (
            select
                public.current_user_is_portal_admin()
        )
    )
)
with check (
    (
        authority_scope = 'USER'
        and owner_user_id = (select auth.uid())
    )
    or (
        authority_scope <> 'USER'
        and owner_user_id is null
        and (
            select
                public.current_user_is_portal_admin()
        )
    )
);

drop policy if exists
assessment_template_sets_delete_draft
on public.assessment_document_template_sets;

create policy
assessment_template_sets_delete_draft
on public.assessment_document_template_sets
for delete
to authenticated
using (
    lifecycle_status = 'DRAFT'
    and (
        (
            authority_scope = 'USER'
            and owner_user_id = (select auth.uid())
        )
        or (
            authority_scope <> 'USER'
            and (
                select
                    public.current_user_is_portal_admin()
            )
        )
    )
);

drop policy if exists
assessment_template_versions_select_visible
on public.assessment_document_template_versions;

create policy
assessment_template_versions_select_visible
on public.assessment_document_template_versions
for select
to authenticated
using (
    public.assessment_document_template_set_is_visible(
        template_set_id
    )
);

drop policy if exists
assessment_template_versions_insert_editable
on public.assessment_document_template_versions;

create policy
assessment_template_versions_insert_editable
on public.assessment_document_template_versions
for insert
to authenticated
with check (
    review_status = 'DRAFT'
    and approved_at is null
    and approved_by is null
    and created_by = (select auth.uid())
    and exists (
        select 1
        from public.assessment_document_template_sets template_set
        where
            template_set.template_set_id =
                assessment_document_template_versions.template_set_id
            and (
                (
                    template_set.authority_scope = 'USER'
                    and template_set.owner_user_id =
                        (select auth.uid())
                )
                or (
                    template_set.authority_scope <> 'USER'
                    and (
                        select
                            public.current_user_is_portal_admin()
                    )
                )
            )
    )
);

drop policy if exists
assessment_template_versions_update_editable
on public.assessment_document_template_versions;

create policy
assessment_template_versions_update_editable
on public.assessment_document_template_versions
for update
to authenticated
using (
    review_status in (
        'DRAFT',
        'REVISION_REQUIRED'
    )
    and exists (
        select 1
        from public.assessment_document_template_sets template_set
        where
            template_set.template_set_id =
                assessment_document_template_versions.template_set_id
            and (
                (
                    template_set.authority_scope = 'USER'
                    and template_set.owner_user_id =
                        (select auth.uid())
                )
                or (
                    template_set.authority_scope <> 'USER'
                    and (
                        select
                            public.current_user_is_portal_admin()
                    )
                )
            )
    )
)
with check (
    review_status in (
        'DRAFT',
        'REVISION_REQUIRED'
    )
    and approved_at is null
    and approved_by is null
    and exists (
        select 1
        from public.assessment_document_template_sets template_set
        where
            template_set.template_set_id =
                assessment_document_template_versions.template_set_id
            and (
                (
                    template_set.authority_scope = 'USER'
                    and template_set.owner_user_id =
                        (select auth.uid())
                )
                or (
                    template_set.authority_scope <> 'USER'
                    and (
                        select
                            public.current_user_is_portal_admin()
                    )
                )
            )
    )
);

drop policy if exists
assessment_template_definitions_select_visible
on public.assessment_document_template_definitions;

create policy
assessment_template_definitions_select_visible
on public.assessment_document_template_definitions
for select
to authenticated
using (
    exists (
        select 1
        from public.assessment_document_template_versions
            template_version
        where
            template_version.template_version_id =
                assessment_document_template_definitions.template_version_id
            and
                public.assessment_document_template_set_is_visible(
                    template_version.template_set_id
                )
    )
);

drop policy if exists
assessment_template_definitions_insert_editable
on public.assessment_document_template_definitions;

create policy
assessment_template_definitions_insert_editable
on public.assessment_document_template_definitions
for insert
to authenticated
with check (
    created_by = (select auth.uid())
    and exists (
        select 1
        from public.assessment_document_template_versions
            template_version
        join public.assessment_document_template_sets
            template_set
            on template_set.template_set_id =
                template_version.template_set_id
        where
            template_version.template_version_id =
                assessment_document_template_definitions.template_version_id
            and template_version.review_status in (
                'DRAFT',
                'REVISION_REQUIRED'
            )
            and (
                (
                    template_set.authority_scope = 'USER'
                    and template_set.owner_user_id =
                        (select auth.uid())
                )
                or (
                    template_set.authority_scope <> 'USER'
                    and (
                        select
                            public.current_user_is_portal_admin()
                    )
                )
            )
    )
);

drop policy if exists
assessment_template_definitions_update_editable
on public.assessment_document_template_definitions;

create policy
assessment_template_definitions_update_editable
on public.assessment_document_template_definitions
for update
to authenticated
using (
    exists (
        select 1
        from public.assessment_document_template_versions
            template_version
        join public.assessment_document_template_sets
            template_set
            on template_set.template_set_id =
                template_version.template_set_id
        where
            template_version.template_version_id =
                assessment_document_template_definitions.template_version_id
            and template_version.review_status in (
                'DRAFT',
                'REVISION_REQUIRED'
            )
            and (
                (
                    template_set.authority_scope = 'USER'
                    and template_set.owner_user_id =
                        (select auth.uid())
                )
                or (
                    template_set.authority_scope <> 'USER'
                    and (
                        select
                            public.current_user_is_portal_admin()
                    )
                )
            )
    )
);

commit;
