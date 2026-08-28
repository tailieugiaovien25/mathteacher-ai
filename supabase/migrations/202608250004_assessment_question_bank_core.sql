-- Assessment Question Bank Core V1
-- Stable question identity, immutable version history,
-- teacher ownership, AI provenance, and review status.

create extension if not exists pgcrypto;

create table if not exists public.assessment_question_items (
    question_id uuid primary key default gen_random_uuid(),

    question_code text not null
        check (char_length(question_code) between 1 and 140),

    owner_user_id uuid not null
        references auth.users(id)
        on delete restrict,

    subject_code text not null default 'MATH'
        check (char_length(subject_code) between 1 and 100),

    education_level text not null
        check (education_level in ('THCS', 'THPT', 'PRIMARY')),

    grade_level integer not null
        check (grade_level between 1 and 12),

    current_version_number integer not null default 0
        check (current_version_number >= 0),

    lifecycle_status text not null default 'DRAFT'
        check (
            lifecycle_status in (
                'DRAFT',
                'ACTIVE',
                'ARCHIVED'
            )
        ),

    metadata jsonb not null default '{}'::jsonb,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        owner_user_id,
        question_code
    )
);

create table if not exists public.assessment_question_versions (
    question_version_id uuid primary key default gen_random_uuid(),

    question_id uuid not null
        references public.assessment_question_items(question_id)
        on delete restrict,

    version_number integer not null
        check (version_number >= 1),

    question_type_code text not null
        references public.assessment_question_types(question_type_code)
        on update cascade
        on delete restrict,

    cognitive_level_code text not null
        references public.assessment_cognitive_levels(cognitive_level_code)
        on update cascade
        on delete restrict,

    prompt_text text not null
        check (char_length(trim(prompt_text)) > 0),

    stimulus_text text not null default '',
    instruction_text text not null default '',

    estimated_minutes numeric(6,2) null
        check (
            estimated_minutes is null
            or estimated_minutes > 0
        ),

    default_score numeric(6,2) not null
        check (default_score > 0),

    origin_type text not null default 'HUMAN'
        check (
            origin_type in (
                'HUMAN',
                'AI',
                'IMPORTED'
            )
        ),

    ai_generation_reference text null,

    review_status text not null default 'DRAFT'
        check (
            review_status in (
                'DRAFT',
                'AI_PROPOSED',
                'PENDING_REVIEW',
                'REVISION_REQUIRED',
                'APPROVED',
                'REJECTED',
                'RETIRED'
            )
        ),

    content_hash text null,
    locked_at timestamptz null,

    metadata jsonb not null default '{}'::jsonb,

    created_by uuid not null
        references auth.users(id)
        on delete restrict,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    unique (
        question_id,
        version_number
    ),

    check (
        origin_type <> 'AI'
        or review_status in (
            'AI_PROPOSED',
            'PENDING_REVIEW',
            'REVISION_REQUIRED',
            'APPROVED',
            'REJECTED',
            'RETIRED'
        )
    ),

    check (
        origin_type = 'AI'
        or ai_generation_reference is null
    ),

    check (
        review_status not in (
            'APPROVED',
            'REJECTED',
            'RETIRED'
        )
        or locked_at is not null
    )
);

create index if not exists
    assessment_question_items_owner_scope_idx
on public.assessment_question_items (
    owner_user_id,
    subject_code,
    grade_level,
    lifecycle_status
);

create index if not exists
    assessment_question_versions_question_idx
on public.assessment_question_versions (
    question_id,
    version_number desc
);

create index if not exists
    assessment_question_versions_classification_idx
on public.assessment_question_versions (
    question_type_code,
    cognitive_level_code,
    review_status
);

create or replace function
public.current_user_owns_assessment_question(
    target_question_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_question_items question_item
        where
            question_item.question_id = target_question_id
            and question_item.owner_user_id = (
                select auth.uid()
            )
    );
$$;

revoke all on function
public.current_user_owns_assessment_question(uuid)
from public;

grant execute on function
public.current_user_owns_assessment_question(uuid)
to authenticated;

create or replace function
public.assessment_question_version_is_editable(
    target_question_version_id uuid
)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1
        from public.assessment_question_versions question_version
        join public.assessment_question_items question_item
            on question_item.question_id =
                question_version.question_id
        where
            question_version.question_version_id =
                target_question_version_id
            and question_item.owner_user_id = (
                select auth.uid()
            )
            and question_version.locked_at is null
            and question_version.review_status in (
                'DRAFT',
                'AI_PROPOSED',
                'REVISION_REQUIRED'
            )
    );
$$;

revoke all on function
public.assessment_question_version_is_editable(uuid)
from public;

grant execute on function
public.assessment_question_version_is_editable(uuid)
to authenticated;

alter table public.assessment_question_items
    enable row level security;

alter table public.assessment_question_versions
    enable row level security;

revoke all on table
    public.assessment_question_items,
    public.assessment_question_versions
from anon;

grant select, insert, update on table
    public.assessment_question_items,
    public.assessment_question_versions
to authenticated;

drop policy if exists
    assessment_question_items_select_authorized
on public.assessment_question_items;

create policy
    assessment_question_items_select_authorized
on public.assessment_question_items
for select
to authenticated
using (
    owner_user_id = (select auth.uid())
    or (select public.current_user_is_portal_admin())
);

drop policy if exists
    assessment_question_items_insert_own
on public.assessment_question_items;

create policy
    assessment_question_items_insert_own
on public.assessment_question_items
for insert
to authenticated
with check (
    owner_user_id = (select auth.uid())
);

drop policy if exists
    assessment_question_items_update_own
on public.assessment_question_items;

create policy
    assessment_question_items_update_own
on public.assessment_question_items
for update
to authenticated
using (
    owner_user_id = (select auth.uid())
)
with check (
    owner_user_id = (select auth.uid())
);

drop policy if exists
    assessment_question_versions_select_authorized
on public.assessment_question_versions;

create policy
    assessment_question_versions_select_authorized
on public.assessment_question_versions
for select
to authenticated
using (
    (
        select
            public.current_user_owns_assessment_question(
                question_id
            )
    )
    or (select public.current_user_is_portal_admin())
);

drop policy if exists
    assessment_question_versions_insert_own
on public.assessment_question_versions;

create policy
    assessment_question_versions_insert_own
on public.assessment_question_versions
for insert
to authenticated
with check (
    (
        select
            public.current_user_owns_assessment_question(
                question_id
            )
    )
    and created_by = (select auth.uid())
    and review_status in (
        'DRAFT',
        'AI_PROPOSED',
        'REVISION_REQUIRED'
    )
    and locked_at is null
);

drop policy if exists
    assessment_question_versions_update_editable
on public.assessment_question_versions;

create policy
    assessment_question_versions_update_editable
on public.assessment_question_versions
for update
to authenticated
using (
    (
        select
            public.assessment_question_version_is_editable(
                question_version_id
            )
    )
)
with check (
    (
        select
            public.current_user_owns_assessment_question(
                question_id
            )
    )
    and created_by = (select auth.uid())
    and review_status in (
        'DRAFT',
        'AI_PROPOSED',
        'PENDING_REVIEW',
        'REVISION_REQUIRED'
    )
    and locked_at is null
);

create or replace function
public.set_assessment_question_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists
    assessment_question_items_set_updated_at
on public.assessment_question_items;

create trigger
    assessment_question_items_set_updated_at
before update
on public.assessment_question_items
for each row
execute function
    public.set_assessment_question_updated_at();

drop trigger if exists
    assessment_question_versions_set_updated_at
on public.assessment_question_versions;

create trigger
    assessment_question_versions_set_updated_at
before update
on public.assessment_question_versions
for each row
execute function
    public.set_assessment_question_updated_at();

comment on table public.assessment_question_items is
'Stable teacher-owned question identity independent from content versions.';

comment on table public.assessment_question_versions is
'Versioned question content with AI provenance and review lifecycle.';

comment on column
public.assessment_question_versions.origin_type is
'Identifies human-authored, AI-generated, or imported content.';

comment on column
public.assessment_question_versions.review_status is
'AI content starts as AI_PROPOSED and cannot be inserted as approved.';
