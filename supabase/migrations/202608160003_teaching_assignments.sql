create table if not exists public.teaching_assignments (
    assignment_id text primary key,
    owner_id uuid not null
        references auth.users(id)
        on delete cascade,

    academic_year text not null
        check (
            char_length(academic_year)
            between 1 and 30
        ),

    class_id text not null
        check (
            char_length(class_id)
            between 1 and 100
        ),

    subject_ref text null
        check (
            subject_ref is null
            or char_length(subject_ref)
            between 1 and 100
        ),

    component_ref text null
        check (
            component_ref is null
            or char_length(component_ref)
            between 1 and 100
        ),

    role text not null
        check (
            role in (
                'TEACHING',
                'HOMEROOM'
            )
        ),

    effective_from date not null,
    effective_to date not null,

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'ACTIVE',
                'INACTIVE'
            )
        ),

    created_at timestamptz
        not null default now(),

    updated_at timestamptz
        not null default now(),

    constraint teaching_assignment_date_range
        check (
            effective_from <= effective_to
        ),

    constraint teaching_assignment_subject_rule
        check (
            (
                role = 'TEACHING'
                and subject_ref is not null
            )
            or
            (
                role = 'HOMEROOM'
            )
        )
);

create index if not exists
    teaching_assignments_owner_year_idx
on public.teaching_assignments (
    owner_id,
    academic_year
);

create index if not exists
    teaching_assignments_active_idx
on public.teaching_assignments (
    owner_id,
    academic_year,
    status
);

alter table
    public.teaching_assignments
enable row level security;

revoke all
on table public.teaching_assignments
from anon;

grant
    select,
    insert,
    update,
    delete
on table public.teaching_assignments
to authenticated;

drop policy if exists
    "teachers_select_own_assignments"
on public.teaching_assignments;

create policy
    "teachers_select_own_assignments"
on public.teaching_assignments
for select
to authenticated
using (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);

drop policy if exists
    "teachers_insert_own_assignments"
on public.teaching_assignments;

create policy
    "teachers_insert_own_assignments"
on public.teaching_assignments
for insert
to authenticated
with check (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);

drop policy if exists
    "teachers_update_own_assignments"
on public.teaching_assignments;

create policy
    "teachers_update_own_assignments"
on public.teaching_assignments
for update
to authenticated
using (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
)
with check (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);

drop policy if exists
    "teachers_delete_own_assignments"
on public.teaching_assignments;

create policy
    "teachers_delete_own_assignments"
on public.teaching_assignments
for delete
to authenticated
using (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);
