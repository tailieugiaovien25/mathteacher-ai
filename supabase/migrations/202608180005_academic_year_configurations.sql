-- Canonical Academic Year / School-Year Configuration.
--
-- ADMIN owns the system-wide academic-year configuration.
-- Other authenticated users may read it.
--
-- Canonical academic_year format:
--   YYYY-YYYY
--
-- Example:
--   2026-2027
--
-- Only one configuration may be current at a time.

create table if not exists
public.academic_year_configurations (
    academic_year_id text primary key
        check (
            char_length(academic_year_id)
            between 1 and 120
        ),

    academic_year text not null unique
        check (
            academic_year ~
            '^[0-9]{4}-[0-9]{4}$'
        ),

    start_date date not null,

    end_date date not null,

    opening_ceremony_date date not null,

    semester_1_start date not null,

    semester_1_end date not null,

    semester_2_start date not null,

    semester_2_end date not null,

    status text not null
        default 'DRAFT'
        check (
            status in (
                'DRAFT',
                'ACTIVE',
                'CLOSED'
            )
        ),

    is_current boolean not null
        default false,

    created_at timestamptz not null
        default now(),

    updated_at timestamptz not null
        default now(),

    constraint academic_year_date_order_check
        check (
            start_date <= end_date
        ),

    constraint academic_year_opening_date_check
        check (
            opening_ceremony_date
            between start_date and end_date
        ),

    constraint academic_year_semester_1_check
        check (
            semester_1_start >= start_date
            and semester_1_start <= semester_1_end
            and semester_1_end <= end_date
        ),

    constraint academic_year_semester_2_check
        check (
            semester_2_start >= start_date
            and semester_2_start <= semester_2_end
            and semester_2_end <= end_date
        ),

    constraint academic_year_semester_order_check
        check (
            semester_1_end
            < semester_2_start
        ),

    constraint academic_year_current_active_check
        check (
            not is_current
            or status = 'ACTIVE'
        )
);


-- ---------------------------------------------------------
-- ONLY ONE CURRENT ACADEMIC YEAR
-- ---------------------------------------------------------

create unique index if not exists
academic_year_configurations_one_current_idx
on public.academic_year_configurations (
    is_current
)
where is_current = true;


-- ---------------------------------------------------------
-- ROW LEVEL SECURITY
-- ---------------------------------------------------------

alter table
public.academic_year_configurations
enable row level security;

revoke all
on table public.academic_year_configurations
from anon;

grant select
on table public.academic_year_configurations
to authenticated;

grant insert, update, delete
on table public.academic_year_configurations
to authenticated;


-- ---------------------------------------------------------
-- AUTHENTICATED USERS: READ
-- ---------------------------------------------------------

drop policy if exists
"authenticated_select_academic_year_configurations"
on public.academic_year_configurations;

create policy
"authenticated_select_academic_year_configurations"
on public.academic_year_configurations
for select
to authenticated
using (
    true
);


-- ---------------------------------------------------------
-- ADMIN: INSERT
-- ---------------------------------------------------------

drop policy if exists
"admins_insert_academic_year_configurations"
on public.academic_year_configurations;

create policy
"admins_insert_academic_year_configurations"
on public.academic_year_configurations
for insert
to authenticated
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: UPDATE
-- ---------------------------------------------------------

drop policy if exists
"admins_update_academic_year_configurations"
on public.academic_year_configurations;

create policy
"admins_update_academic_year_configurations"
on public.academic_year_configurations
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
"admins_delete_academic_year_configurations"
on public.academic_year_configurations;

create policy
"admins_delete_academic_year_configurations"
on public.academic_year_configurations
for delete
to authenticated
using (
    (select public.current_user_is_portal_admin())
);


comment on table
public.academic_year_configurations is
'Canonical system-wide academic-year and school-year calendar configuration managed by ADMIN.';

comment on column
public.academic_year_configurations.academic_year is
'Canonical academic year in YYYY-YYYY format, for example 2026-2027.';

comment on column
public.academic_year_configurations.is_current is
'Exactly zero or one academic year may be current. A current academic year must be ACTIVE.';
