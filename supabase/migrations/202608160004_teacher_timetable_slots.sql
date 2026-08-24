create table if not exists public.teacher_timetable_slots (
    slot_id text primary key,

    owner_id uuid not null
        references auth.users(id)
        on delete cascade,

    academic_year text not null
        check (
            char_length(academic_year)
            between 1 and 30
        ),

    assignment_id text not null
        references public.teaching_assignments(
            assignment_id
        )
        on delete cascade,

    weekday integer not null
        check (
            weekday between 1 and 7
        ),

    session text not null
        check (
            session in (
                'MORNING',
                'AFTERNOON'
            )
        ),

    period integer not null
        check (
            period between 1 and 5
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

    constraint teacher_timetable_date_range
        check (
            effective_from <= effective_to
        )
);

create index if not exists
    teacher_timetable_owner_year_idx
on public.teacher_timetable_slots (
    owner_id,
    academic_year
);

create index if not exists
    teacher_timetable_position_idx
on public.teacher_timetable_slots (
    owner_id,
    academic_year,
    weekday,
    session,
    period,
    status
);

alter table
    public.teacher_timetable_slots
enable row level security;

revoke all
on table public.teacher_timetable_slots
from anon;

grant
    select,
    insert,
    update,
    delete
on table public.teacher_timetable_slots
to authenticated;

drop policy if exists
    "teachers_select_own_timetable_slots"
on public.teacher_timetable_slots;

create policy
    "teachers_select_own_timetable_slots"
on public.teacher_timetable_slots
for select
to authenticated
using (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);

drop policy if exists
    "teachers_insert_own_timetable_slots"
on public.teacher_timetable_slots;

create policy
    "teachers_insert_own_timetable_slots"
on public.teacher_timetable_slots
for insert
to authenticated
with check (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);

drop policy if exists
    "teachers_update_own_timetable_slots"
on public.teacher_timetable_slots;

create policy
    "teachers_update_own_timetable_slots"
on public.teacher_timetable_slots
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
    "teachers_delete_own_timetable_slots"
on public.teacher_timetable_slots;

create policy
    "teachers_delete_own_timetable_slots"
on public.teacher_timetable_slots
for delete
to authenticated
using (
    (select auth.uid()) is not null
    and
    (select auth.uid()) = owner_id
);
