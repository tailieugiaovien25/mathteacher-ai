-- Canonical Academic Weeks.
--
-- ADMIN manages the week calendar for each academic year.
-- Authenticated users may read it.
--
-- Week dates are canonical operational data used by:
--   - Teacher timetable
--   - Weekly teaching schedule / Lich bao giang
--   - PPCT period resolution
--
-- ADMIN may manually adjust a week when required by
-- the real school calendar.

create table if not exists
public.academic_weeks (
    academic_week_id text primary key
        check (
            char_length(academic_week_id)
            between 1 and 120
        ),

    academic_year_id text not null
        references
        public.academic_year_configurations(
            academic_year_id
        )
        on update cascade
        on delete restrict,

    academic_year text not null
        check (
            academic_year ~
            '^[0-9]{4}-[0-9]{4}$'
        ),

    week_number integer not null
        check (
            week_number between 1 and 40
        ),

    start_date date not null,

    end_date date not null,

    status text not null
        default 'ACTIVE'
        check (
            status in (
                'ACTIVE',
                'INACTIVE'
            )
        ),

    is_manual_override boolean
        not null
        default false,

    note text null
        check (
            note is null
            or char_length(note) <= 1000
        ),

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint academic_week_date_order_check
        check (
            start_date <= end_date
        ),

    constraint academic_week_year_number_unique
        unique (
            academic_year_id,
            week_number
        )
);


-- ---------------------------------------------------------
-- INDEXES
-- ---------------------------------------------------------

create index if not exists
academic_weeks_year_idx
on public.academic_weeks (
    academic_year_id
);


create index if not exists
academic_weeks_year_date_idx
on public.academic_weeks (
    academic_year_id,
    start_date,
    end_date
);


create index if not exists
academic_weeks_year_status_idx
on public.academic_weeks (
    academic_year_id,
    status
);


-- ---------------------------------------------------------
-- ROW LEVEL SECURITY
-- ---------------------------------------------------------

alter table
public.academic_weeks
enable row level security;


revoke all
on table public.academic_weeks
from anon;


grant select
on table public.academic_weeks
to authenticated;


grant insert, update, delete
on table public.academic_weeks
to authenticated;


-- ---------------------------------------------------------
-- AUTHENTICATED USERS: READ
-- ---------------------------------------------------------

drop policy if exists
"authenticated_select_academic_weeks"
on public.academic_weeks;


create policy
"authenticated_select_academic_weeks"
on public.academic_weeks
for select
to authenticated
using (
    true
);


-- ---------------------------------------------------------
-- ADMIN: INSERT
-- ---------------------------------------------------------

drop policy if exists
"admins_insert_academic_weeks"
on public.academic_weeks;


create policy
"admins_insert_academic_weeks"
on public.academic_weeks
for insert
to authenticated
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: UPDATE
-- ---------------------------------------------------------

drop policy if exists
"admins_update_academic_weeks"
on public.academic_weeks;


create policy
"admins_update_academic_weeks"
on public.academic_weeks
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
"admins_delete_academic_weeks"
on public.academic_weeks;


create policy
"admins_delete_academic_weeks"
on public.academic_weeks
for delete
to authenticated
using (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- COMMENTS
-- ---------------------------------------------------------

comment on table
public.academic_weeks is
'Canonical ADMIN-managed academic week calendar used by teacher timetable and weekly teaching schedule.';


comment on column
public.academic_weeks.week_number is
'Canonical week number within the academic year, from 1 to 40.';


comment on column
public.academic_weeks.is_manual_override is
'True when ADMIN manually adjusted this week from the automatically generated school-year calendar.';


comment on column
public.academic_weeks.note is
'Optional ADMIN explanation for manual week-calendar adjustments.';
