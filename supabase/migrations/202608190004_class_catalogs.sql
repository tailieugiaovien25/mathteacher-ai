create table if not exists public.class_catalogs (
    class_id text primary key
        check (
            char_length(class_id)
            between 1 and 120
        ),

    academic_year text not null
        check (
            char_length(academic_year)
            between 1 and 30
        ),

    grade_level text not null
        check (
            char_length(grade_level)
            between 1 and 50
        ),

    class_code text not null
        check (
            char_length(class_code)
            between 1 and 100
        ),

    class_name text not null
        check (
            char_length(class_name)
            between 1 and 200
        ),

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

    constraint class_catalog_year_code_unique
        unique (
            academic_year,
            class_code
        )
);

create index if not exists
    class_catalogs_year_idx
on public.class_catalogs (
    academic_year
);

create index if not exists
    class_catalogs_year_grade_idx
on public.class_catalogs (
    academic_year,
    grade_level
);

create index if not exists
    class_catalogs_year_status_idx
on public.class_catalogs (
    academic_year,
    status
);

alter table
    public.class_catalogs
enable row level security;

revoke all
on table public.class_catalogs
from anon;

grant
    select,
    insert,
    update,
    delete
on table public.class_catalogs
to authenticated;


-- ---------------------------------------------------------
-- AUTHENTICATED USERS: READ
-- ---------------------------------------------------------

drop policy if exists
    "authenticated_select_class_catalogs"
on public.class_catalogs;

create policy
    "authenticated_select_class_catalogs"
on public.class_catalogs
for select
to authenticated
using (
    (select auth.uid()) is not null
);


-- ---------------------------------------------------------
-- ADMIN: INSERT
-- ---------------------------------------------------------

drop policy if exists
    "admins_insert_class_catalogs"
on public.class_catalogs;

create policy
    "admins_insert_class_catalogs"
on public.class_catalogs
for insert
to authenticated
with check (
    (select public.current_user_is_portal_admin())
);


-- ---------------------------------------------------------
-- ADMIN: UPDATE
-- ---------------------------------------------------------

drop policy if exists
    "admins_update_class_catalogs"
on public.class_catalogs;

create policy
    "admins_update_class_catalogs"
on public.class_catalogs
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
    "admins_delete_class_catalogs"
on public.class_catalogs;

create policy
    "admins_delete_class_catalogs"
on public.class_catalogs
for delete
to authenticated
using (
    (select public.current_user_is_portal_admin())
);


comment on table
public.class_catalogs is
'ADMIN-managed flexible class catalog by academic year. Class count and names are data-driven and not hard-coded.';

comment on column
public.class_catalogs.class_code is
'Flexible school-defined class code, unique within one academic year.';

comment on column
public.class_catalogs.class_name is
'Flexible display name managed by ADMIN.';
