-- Academic Year Calendar Events.
--
-- ADMIN manages holidays, Tet breaks, midterm breaks,
-- makeup teaching days, school events and other breaks.
--
-- Authenticated users may read calendar events.
--
-- Calendar events belong to one canonical academic year.

create table if not exists
public.academic_year_calendar_events (
    event_id text primary key
        check (
            char_length(event_id)
            between 1 and 120
        ),

    academic_year_id text not null
        references
        public.academic_year_configurations(
            academic_year_id
        )
        on update cascade
        on delete restrict,

    event_type text not null
        check (
            event_type in (
                'HOLIDAY',
                'TET_BREAK',
                'MIDTERM_BREAK',
                'MAKEUP_DAY',
                'SCHOOL_EVENT',
                'OTHER_BREAK'
            )
        ),

    name text not null
        check (
            char_length(name)
            between 1 and 250
        ),

    start_date date not null,

    end_date date not null,

    is_teaching_day_override boolean
        not null
        default false,

    note text null
        check (
            note is null
            or char_length(note) <= 1000
        ),

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'ACTIVE',
                'INACTIVE'
            )
        ),

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint academic_year_calendar_event_date_order_check
        check (
            start_date <= end_date
        ),

    constraint academic_year_calendar_event_override_check
        check (
            (
                event_type = 'MAKEUP_DAY'
                and is_teaching_day_override = true
            )
            or
            (
                event_type <> 'MAKEUP_DAY'
                and is_teaching_day_override = false
            )
        )
);


create index if not exists
academic_year_calendar_events_year_date_idx
on public.academic_year_calendar_events (
    academic_year_id,
    start_date,
    end_date
);


create index if not exists
academic_year_calendar_events_year_type_idx
on public.academic_year_calendar_events (
    academic_year_id,
    event_type
);


alter table
public.academic_year_calendar_events
enable row level security;


revoke all
on table public.academic_year_calendar_events
from anon;


grant select
on table public.academic_year_calendar_events
to authenticated;


grant insert, update, delete
on table public.academic_year_calendar_events
to authenticated;


-- ---------------------------------------------------------
-- AUTHENTICATED USERS: READ
-- ---------------------------------------------------------

drop policy if exists
"authenticated_select_academic_year_calendar_events"
on public.academic_year_calendar_events;

create policy
"authenticated_select_academic_year_calendar_events"
on public.academic_year_calendar_events
for select
to authenticated
using (
    true
);


-- ---------------------------------------------------------
-- ADMIN: INSERT
-- ---------------------------------------------------------

drop policy if exists
"admins_insert_academic_year_calendar_events"
on public.academic_year_calendar_events;

create policy
"admins_insert_academic_year_calendar_events"
on public.academic_year_calendar_events
for insert
to authenticated
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: UPDATE
-- ---------------------------------------------------------

drop policy if exists
"admins_update_academic_year_calendar_events"
on public.academic_year_calendar_events;

create policy
"admins_update_academic_year_calendar_events"
on public.academic_year_calendar_events
for update
to authenticated
using (
    (select public.current_user_is_portal_admin())
)
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: DELETE
-- ---------------------------------------------------------

drop policy if exists
"admins_delete_academic_year_calendar_events"
on public.academic_year_calendar_events;

create policy
"admins_delete_academic_year_calendar_events"
on public.academic_year_calendar_events
for delete
to authenticated
using (
    (select public.current_user_is_portal_admin())
);


comment on table
public.academic_year_calendar_events is
'ADMIN-managed school-year calendar events including holidays, Tet breaks, midterm breaks, makeup teaching days and other scheduling exceptions.';

comment on column
public.academic_year_calendar_events.is_teaching_day_override is
'True only for MAKEUP_DAY events that explicitly turn a normally non-teaching date into a teaching day.';
