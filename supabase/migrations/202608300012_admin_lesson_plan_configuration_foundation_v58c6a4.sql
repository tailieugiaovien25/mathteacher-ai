-- V58-C6A4: ADMIN-owned canonical lesson-plan configuration foundation.
--
-- Boundary:
--   * ADMIN owns canonical configuration/template definitions.
--   * Authenticated runtime users may read ACTIVE configuration.
--   * Teacher drafts, uploaded documents, working selections and merge state
--     are intentionally outside this migration.
--   * Existing lesson_plan_grouping_policy_config is reused and is NOT duplicated.

create table if not exists public.lesson_plan_configuration_profiles (
    profile_id uuid primary key default gen_random_uuid(),

    profile_code text not null unique
        check (char_length(trim(profile_code)) between 1 and 140),

    profile_name text not null
        check (char_length(trim(profile_name)) between 1 and 240),

    subject_ref text not null default '',
    component_ref text not null default '',

    lifecycle_status text not null default 'DRAFT'
        check (
            lifecycle_status in (
                'DRAFT',
                'ACTIVE',
                'INACTIVE',
                'ARCHIVED'
            )
        ),

    current_version_id uuid null,

    created_by uuid null default auth.uid(),
    updated_by uuid null default auth.uid(),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    check (char_length(subject_ref) <= 140),
    check (char_length(component_ref) <= 140)
);

create unique index if not exists
    lesson_plan_configuration_profiles_one_active_scope
on public.lesson_plan_configuration_profiles (
    subject_ref,
    component_ref
)
where lifecycle_status = 'ACTIVE';

create index if not exists
    lesson_plan_configuration_profiles_scope_lookup
on public.lesson_plan_configuration_profiles (
    subject_ref,
    component_ref,
    lifecycle_status
);

create table if not exists public.lesson_plan_configuration_versions (
    configuration_version_id uuid primary key
        default gen_random_uuid(),

    profile_id uuid not null
        references public.lesson_plan_configuration_profiles(profile_id)
        on delete cascade,

    version_number integer not null
        check (version_number >= 1),

    version_status text not null default 'DRAFT'
        check (
            version_status in (
                'DRAFT',
                'PUBLISHED',
                'RETIRED'
            )
        ),

    -- Canonical payload intentionally stays JSONB in Migration 1 so the
    -- existing LessonPlanTemplateProfile contract can be represented
    -- without prematurely coupling PostgreSQL columns to every UI field.
    --
    -- Expected top-level domains:
    --   template_profile
    --   standardization_policy
    --   date_policy
    --   approval_policy
    --   runtime
    configuration_payload jsonb not null default '{}'::jsonb
        check (jsonb_typeof(configuration_payload) = 'object'),

    change_note text null,

    created_by uuid null default auth.uid(),
    published_by uuid null,

    created_at timestamptz not null default now(),
    published_at timestamptz null,

    unique (profile_id, version_number),

    check (
        (version_status <> 'PUBLISHED')
        or published_at is not null
    )
);

create index if not exists
    lesson_plan_configuration_versions_profile_lookup
on public.lesson_plan_configuration_versions (
    profile_id,
    version_number desc
);

alter table public.lesson_plan_configuration_profiles
    drop constraint if exists
        lesson_plan_configuration_profiles_current_version_fk;

alter table public.lesson_plan_configuration_profiles
    add constraint
        lesson_plan_configuration_profiles_current_version_fk
    foreign key (current_version_id)
    references public.lesson_plan_configuration_versions(
        configuration_version_id
    )
    on delete restrict;

create or replace function
    public.validate_lesson_plan_configuration_current_version()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
declare
    selected_version public.lesson_plan_configuration_versions%rowtype;
begin
    if new.current_version_id is null then
        if new.lifecycle_status = 'ACTIVE' then
            raise exception
                'ACTIVE lesson-plan configuration requires current_version_id.';
        end if;

        return new;
    end if;

    select *
    into selected_version
    from public.lesson_plan_configuration_versions
    where configuration_version_id = new.current_version_id;

    if not found then
        raise exception
            'Lesson-plan configuration current version does not exist.';
    end if;

    if selected_version.profile_id <> new.profile_id then
        raise exception
            'Lesson-plan configuration current version belongs to another profile.';
    end if;

    if new.lifecycle_status = 'ACTIVE'
       and selected_version.version_status <> 'PUBLISHED' then
        raise exception
            'ACTIVE lesson-plan configuration must point to a PUBLISHED version.';
    end if;

    return new;
end;
$$;

drop trigger if exists
    validate_lesson_plan_configuration_current_version_trigger
on public.lesson_plan_configuration_profiles;

create constraint trigger
    validate_lesson_plan_configuration_current_version_trigger
after insert or update of
    current_version_id,
    lifecycle_status
on public.lesson_plan_configuration_profiles
deferrable initially deferred
for each row
execute function
    public.validate_lesson_plan_configuration_current_version();

create or replace function
    public.touch_lesson_plan_configuration_profile()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
    new.updated_at = now();
    new.updated_by = auth.uid();
    return new;
end;
$$;

drop trigger if exists
    touch_lesson_plan_configuration_profile_trigger
on public.lesson_plan_configuration_profiles;

create trigger
    touch_lesson_plan_configuration_profile_trigger
before update
on public.lesson_plan_configuration_profiles
for each row
execute function
    public.touch_lesson_plan_configuration_profile();

create or replace function
    public.protect_published_lesson_plan_configuration_version()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
    if old.version_status = 'PUBLISHED'
       and (
           new.profile_id is distinct from old.profile_id
           or new.version_number is distinct from old.version_number
           or new.configuration_payload is distinct from old.configuration_payload
       ) then
        raise exception
            'Published lesson-plan configuration payload is immutable; create a new version.';
    end if;

    return new;
end;
$$;

drop trigger if exists
    protect_published_lesson_plan_configuration_version_trigger
on public.lesson_plan_configuration_versions;

create trigger
    protect_published_lesson_plan_configuration_version_trigger
before update
on public.lesson_plan_configuration_versions
for each row
execute function
    public.protect_published_lesson_plan_configuration_version();

alter table public.lesson_plan_configuration_profiles
    enable row level security;

alter table public.lesson_plan_configuration_versions
    enable row level security;

drop policy if exists
    lesson_plan_configuration_profiles_runtime_read
on public.lesson_plan_configuration_profiles;

create policy
    lesson_plan_configuration_profiles_runtime_read
on public.lesson_plan_configuration_profiles
for select
to authenticated
using (
    lifecycle_status = 'ACTIVE'
    or (select public.current_user_is_portal_admin())
);

drop policy if exists
    lesson_plan_configuration_profiles_admin_insert
on public.lesson_plan_configuration_profiles;

create policy
    lesson_plan_configuration_profiles_admin_insert
on public.lesson_plan_configuration_profiles
for insert
to authenticated
with check (
    (select public.current_user_is_portal_admin())
);

drop policy if exists
    lesson_plan_configuration_profiles_admin_update
on public.lesson_plan_configuration_profiles;

create policy
    lesson_plan_configuration_profiles_admin_update
on public.lesson_plan_configuration_profiles
for update
to authenticated
using (
    (select public.current_user_is_portal_admin())
)
with check (
    (select public.current_user_is_portal_admin())
);

drop policy if exists
    lesson_plan_configuration_profiles_admin_delete
on public.lesson_plan_configuration_profiles;

create policy
    lesson_plan_configuration_profiles_admin_delete
on public.lesson_plan_configuration_profiles
for delete
to authenticated
using (
    (select public.current_user_is_portal_admin())
);

drop policy if exists
    lesson_plan_configuration_versions_runtime_read
on public.lesson_plan_configuration_versions;

create policy
    lesson_plan_configuration_versions_runtime_read
on public.lesson_plan_configuration_versions
for select
to authenticated
using (
    (
        version_status = 'PUBLISHED'
        and exists (
            select 1
            from public.lesson_plan_configuration_profiles profile
            where profile.profile_id =
                lesson_plan_configuration_versions.profile_id
              and profile.lifecycle_status = 'ACTIVE'
              and profile.current_version_id =
                lesson_plan_configuration_versions.configuration_version_id
        )
    )
    or (select public.current_user_is_portal_admin())
);

drop policy if exists
    lesson_plan_configuration_versions_admin_insert
on public.lesson_plan_configuration_versions;

create policy
    lesson_plan_configuration_versions_admin_insert
on public.lesson_plan_configuration_versions
for insert
to authenticated
with check (
    (select public.current_user_is_portal_admin())
);

drop policy if exists
    lesson_plan_configuration_versions_admin_update
on public.lesson_plan_configuration_versions;

create policy
    lesson_plan_configuration_versions_admin_update
on public.lesson_plan_configuration_versions
for update
to authenticated
using (
    (select public.current_user_is_portal_admin())
)
with check (
    (select public.current_user_is_portal_admin())
);

drop policy if exists
    lesson_plan_configuration_versions_admin_delete
on public.lesson_plan_configuration_versions;

create policy
    lesson_plan_configuration_versions_admin_delete
on public.lesson_plan_configuration_versions
for delete
to authenticated
using (
    (select public.current_user_is_portal_admin())
);

grant select, insert, update, delete
on public.lesson_plan_configuration_profiles
to authenticated;

grant select, insert, update, delete
on public.lesson_plan_configuration_versions
to authenticated;

comment on table public.lesson_plan_configuration_profiles is
    'Canonical ADMIN-owned lesson-plan configuration profiles. Runtime teachers consume ACTIVE profiles but do not own or mutate canonical configuration.';

comment on table public.lesson_plan_configuration_versions is
    'Versioned ADMIN-owned lesson-plan configuration payloads covering template/profile, standardization, date and approval rules.';

comment on column
    public.lesson_plan_configuration_versions.configuration_payload
is
    'JSONB canonical configuration payload. Migration 1 preserves compatibility with the existing Python LessonPlanTemplateProfile rather than duplicating every UI field as SQL columns.';
