create table if not exists
    public.teacher_subject_registrations (
        registration_id text primary key,

        owner_id uuid not null
            references auth.users(id)
            on delete cascade,

        academic_year text not null
            check (
                char_length(trim(academic_year))
                between 1 and 30
            ),

        subject_id text not null
            references public.subjects(
                subject_id
            )
            on delete restrict,

        component_id text null,

        constraint
            teacher_subject_registration_component_scope_fk
        foreign key (
            subject_id,
            component_id
        )
        references public.subject_components (
            subject_id,
            component_id
        )
        on delete restrict,

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
            not null default now()
    );


create index if not exists
    teacher_subject_registration_owner_year_idx
on public.teacher_subject_registrations (
    owner_id,
    academic_year,
    status
);


create index if not exists
    teacher_subject_registration_scope_idx
on public.teacher_subject_registrations (
    owner_id,
    academic_year,
    subject_id,
    component_id,
    status
);


alter table
    public.teacher_subject_registrations
enable row level security;


revoke all
on table public.teacher_subject_registrations
from anon;


grant
    select,
    insert,
    update,
    delete
on table public.teacher_subject_registrations
to authenticated;


drop policy if exists
    "teachers_select_own_subject_registrations"
on public.teacher_subject_registrations;


create policy
    "teachers_select_own_subject_registrations"
on public.teacher_subject_registrations
for select
to authenticated
using (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);


drop policy if exists
    "teachers_insert_own_subject_registrations"
on public.teacher_subject_registrations;


create policy
    "teachers_insert_own_subject_registrations"
on public.teacher_subject_registrations
for insert
to authenticated
with check (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);


drop policy if exists
    "teachers_update_own_subject_registrations"
on public.teacher_subject_registrations;


create policy
    "teachers_update_own_subject_registrations"
on public.teacher_subject_registrations
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
    "teachers_delete_own_subject_registrations"
on public.teacher_subject_registrations;


create policy
    "teachers_delete_own_subject_registrations"
on public.teacher_subject_registrations
for delete
to authenticated
using (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);
